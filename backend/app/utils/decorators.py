"""
Décorateurs transverses : contrôle d'accès basé sur les rôles (RBAC).

Cf. 18-SECURITE.md (matrice des permissions par endpoint). Chaque permission
est une chaîne `<ressource>:<action>` (ex. "products:write", "sales:create",
"audit:read"). Les permissions de l'utilisateur sont injectées dans le JWT
au moment du login (claim "permissions"), ce qui évite une requête en base
à chaque appel protégé.
"""
from functools import wraps

from flask_jwt_extended import verify_jwt_in_request, get_jwt

from app.utils.errors import forbidden


def require_permission(*required_permissions: str):
    """Exige que l'utilisateur authentifié possède AU MOINS UNE des permissions listées.

    Exemple:
        @require_permission("products:write")
        def create_product(): ...
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_permissions = set(claims.get("permissions", []))

            if "*" in user_permissions:  # Super-Admin
                return fn(*args, **kwargs)

            if not user_permissions.intersection(required_permissions):
                raise forbidden(
                    f"Cette action nécessite l'une des permissions suivantes : "
                    f"{', '.join(required_permissions)}."
                )
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def require_role(*roles: str):
    """Exige que l'utilisateur authentifié possède l'un des rôles listés."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") not in roles:
                raise forbidden(
                    f"Cette action est réservée aux rôles : {', '.join(roles)}."
                )
            return fn(*args, **kwargs)
        return wrapper
    return decorator
