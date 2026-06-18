"""
Middleware multi-tenant : résolution du schéma PostgreSQL courant.

Cf. docs/27-MODELE-SAAS-MULTITENANT.md §27.7. À chaque requête (hors
endpoints publics), le claim JWT `company_schema` est lu et appliqué via
`SET search_path` (RG-41 : isolation stricte des données entre entreprises
clientes). En fin de requête, `search_path` est réinitialisé à `public`
avant que la connexion ne retourne au pool, afin d'éviter toute fuite de
contexte tenant entre requêtes (§27.9).
"""
from flask import Flask, current_app, request
from flask_jwt_extended import get_jwt, verify_jwt_in_request

from app.utils.tenant import set_search_path

# Endpoints opérant sur le schéma `public` uniquement (registre des tenants)
# ou ne nécessitant aucun contexte tenant : aucune résolution de schéma n'est
# effectuée pour ces routes (§27.7).
PUBLIC_ENDPOINTS = {
    "health",
    "auth.login",
    "auth.register",
}


def register_tenant_middleware(app: Flask) -> None:
    """Enregistre les hooks `before_request` / `teardown_request` qui
    appliquent le schéma tenant courant à la session SQLAlchemy.
    """

    @app.before_request
    def set_tenant_schema():  # noqa: WPS430 - hook nommé pour la lisibilité
        if request.endpoint is None or request.endpoint in PUBLIC_ENDPOINTS:
            return

        # `optional=True` : si aucun jeton n'est fourni ou s'il est invalide,
        # on laisse `@jwt_required()` (sur la vue) produire l'erreur 401
        # standard plutôt que de lever une erreur ici.
        verify_jwt_in_request(optional=True)

        claims = get_jwt()
        schema = (claims or {}).get("company_schema") or current_app.config[
            "DEFAULT_TENANT_SCHEMA"
        ]
        set_search_path(schema)

    @app.teardown_request
    def reset_tenant_schema(_exception):  # noqa: WPS430
        try:
            set_search_path("public")
        except Exception:  # pragma: no cover - connexion deja fermee/invalide
            pass
