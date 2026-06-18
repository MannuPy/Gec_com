"""
Détection du dialecte de base de données configuré (PostgreSQL vs MySQL).

Le modèle multi-tenant "schema-per-tenant" (cf. docs/27-MODELE-SAAS-MULTITENANT.md)
repose sur des fonctionnalités spécifiques à PostgreSQL (schémas, `SET
search_path`, `CREATE SCHEMA`). Pour un déploiement mono-tenant sur MySQL
(ex. PythonAnywhere, cf. docs/25-DEPLOIEMENT-CICD.md §25.9), ces
fonctionnalités sont neutralisées sans casser le code Postgres existant.

`is_postgres()` est utilisé à deux niveaux :
  - à l'import des modèles (`app/models/company.py`), où aucun contexte
    applicatif n'existe encore : on lit directement `DATABASE_URL` (même
    variable d'environnement que `app/config.py`) ;
  - à l'exécution, dans `app/utils/tenant.py`, où la session SQLAlchemy est
    disponible : `is_postgres_engine(bind)` interroge le dialecte réel du
    moteur connecté (plus fiable que l'URL si celle-ci a été modifiée après
    coup par `SQLALCHEMY_ENGINE_OPTIONS`).
"""
import os

# Valeur par défaut alignée sur `app/config.py` (BaseConfig.SQLALCHEMY_DATABASE_URI).
_DEFAULT_DATABASE_URL = "postgresql+psycopg2://gescom:gescom_dev_password@localhost:5432/gescom_bf"


def is_postgres(database_url: str | None = None) -> bool:
    """True si `database_url` (ou `DATABASE_URL`) désigne une base PostgreSQL."""
    url = database_url if database_url is not None else os.environ.get("DATABASE_URL", _DEFAULT_DATABASE_URL)
    return url.startswith("postgresql")


def is_postgres_engine(bind) -> bool:
    """True si le moteur/connexion SQLAlchemy `bind` est PostgreSQL."""
    try:
        return bind.dialect.name == "postgresql"
    except AttributeError:  # pragma: no cover - bind invalide
        return False
