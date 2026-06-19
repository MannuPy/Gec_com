"""
Utilitaires de resolution et d'application du schema PostgreSQL d'un tenant.

Cf. docs/27-MODELE-SAAS-MULTITENANT.md (§27.2 - schema-per-tenant, §27.7 -
resolution du tenant, table d'index `public.user_index`).
"""
import re
import unicodedata

from flask import current_app
from sqlalchemy import text

from app.extensions import db
from app.models.company import UserIndex
from app.utils.db_dialect import is_postgres_engine
from app.utils.errors import ApiError

TENANT_SCHEMA_PREFIX = "tenant_"

# "public" (tenant par defaut / V1 mono-tenant) ou "tenant_<slug>".
_SCHEMA_NAME_RE = re.compile(r"^(public|tenant_[a-z0-9_]+)$")


def slugify_company_name(name: str) -> str:
    """Convertit un nom d'entreprise en slug ascii utilisable dans un nom de
    schema PostgreSQL (RF-01) : minuscules, chiffres et underscores uniquement.
    """
    normalized = unicodedata.normalize("NFKD", name or "")
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "_", ascii_only.lower()).strip("_")
    return slug or "entreprise"


def schema_name_for_company(name: str) -> str:
    """Genere le nom de schema PostgreSQL dedie d'une nouvelle entreprise."""
    return f"{TENANT_SCHEMA_PREFIX}{slugify_company_name(name)}"


def is_valid_tenant_schema(schema_name: str) -> bool:
    return bool(schema_name) and bool(_SCHEMA_NAME_RE.match(schema_name))


def set_search_path(schema_name: str) -> None:
    """Positionne le `search_path` PostgreSQL de la session courante (§27.7).

    Le schema `public` reste toujours accessible en second afin que les
    tables du registre central (`companies`, `user_index`) restent
    consultables quel que soit le tenant courant.

    Leve `INVALID_TENANT_CONTEXT` (403) si `schema_name` ne respecte pas le
    format attendu (`public` ou `tenant_<slug>`), ce qui empeche toute
    injection SQL via cette valeur (issue d'un claim JWT).

    Sur MySQL (deploiement mono-tenant, ex. PythonAnywhere : une seule base
    de donnees, pas de notion de schema equivalente a PostgreSQL), la
    commande `SET search_path` n'existe pas et n'est donc pas executee :
    cette fonction ne fait alors que valider `schema_name`.
    """
    if not is_valid_tenant_schema(schema_name):
        raise ApiError(
            "INVALID_TENANT_CONTEXT",
            "Contexte d'entreprise invalide ou manquant.",
            status_code=403,
        )

    if not is_postgres_engine(db.session.get_bind()):
        # MySQL / PythonAnywhere : no-op, validation suffit.
        return

    if schema_name == "public":
        db.session.execute(text("SET search_path TO public"))
    else:
        # `schema_name` est garanti conforme a `_SCHEMA_NAME_RE` ci-dessus
        # (caracteres [a-z0-9_] uniquement) : l'interpolation est sure.
        db.session.execute(text(f'SET search_path TO "{schema_name}", public'))


def get_schema_for_email(email: str) -> str:
    """Retrouve le schema tenant associe a un email via `public.user_index`
    (§27.7). Retombe sur le tenant par defaut (`DEFAULT_TENANT_SCHEMA`,
    schema `public` en V1 mono-tenant) si l'email n'est pas encore indexe -
    ce qui couvre les comptes de demonstration crees avant l'introduction
    du multi-tenant.
    """
    entry = UserIndex.query.filter_by(email=email.lower()).first()
    if entry is not None:
        return entry.schema_name
    return current_app.config["DEFAULT_TENANT_SCHEMA"]


def register_user_index(email: str, schema_name: str) -> None:
    """Cree ou met a jour l'entree `public.user_index` pour cet email."""
    email = email.lower()
    entry = UserIndex.query.filter_by(email=email).first()
    if entry is None:
        db.session.add(UserIndex(email=email, schema_name=schema_name))
    else:
        entry.schema_name = schema_name


def remove_user_index(email: str) -> None:
    """Supprime l'entree `public.user_index` pour cet email (desactivation utilisateur)."""
    email = email.lower()
    entry = UserIndex.query.filter_by(email=email).first()
    if entry is not None:
        db.session.delete(entry)
