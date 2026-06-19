"""
Detection du dialecte de base de donnees configure (PostgreSQL vs MySQL).
"""
import os

_DEFAULT_DATABASE_URL = "postgresql+psycopg2://gescom:gescom_dev_password@localhost:5432/gescom_bf"


def is_postgres(database_url=None) -> bool:
    """True si database_url (ou DATABASE_URL) designe une base PostgreSQL."""
    url = database_url if database_url is not None else os.environ.get("DATABASE_URL", _DEFAULT_DATABASE_URL)
    return url.startswith("postgresql")


def is_postgres_engine(bind) -> bool:
    """True si le moteur/connexion SQLAlchemy bind est PostgreSQL."""
    try:
        return bind.dialect.name == "postgresql"
    except AttributeError:
        return False
