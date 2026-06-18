"""
Registre central des tenants (entreprises clientes) du SaaS GesCom-BF.

Cf. docs/27-MODELE-SAAS-MULTITENANT.md (section 27.2 a 27.8) et docs/14-MPD.md
section 14.2 - la table `public.companies` vit dans le schema PostgreSQL `public`,
partage par tous les tenants, et sert de point d'entree pour resoudre le
schema dedie (`schema_name`, ex. `tenant_quincaillerie_ouaga`) a associer a
chaque requete (middleware `set_tenant_schema`, cf. app/middleware/tenant.py).
"""
import enum

from app.extensions import db
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin
from app.utils.db_dialect import is_postgres

# Sur PostgreSQL, `companies`/`user_index` vivent dans le schema `public`,
# partage par tous les tenants (schema-per-tenant, §27.2). Sur MySQL
# (deploiement mono-tenant, ex. PythonAnywhere - une seule base de donnees,
# pas de notion de schema equivalente), ces tables restent simplement dans la
# base applicative : on n'ajoute donc pas de `schema` aux `__table_args__`.
_PUBLIC_SCHEMA_ARGS: dict = {"schema": "public"} if is_postgres() else {}


class SubscriptionPlan(str, enum.Enum):
    """Plans d'abonnement proposes (section 27.5)."""

    TRIAL = "TRIAL"
    STANDARD = "STANDARD"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"


class SubscriptionStatus(str, enum.Enum):
    """Etats du cycle de vie d'un tenant (section 27.8)."""

    TRIAL = "TRIAL"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    CANCELLED = "CANCELLED"


class Company(db.Model, UUIDPrimaryKeyMixin, TimestampMixin):
    """Entreprise cliente (tenant) - une ligne par quincaillerie inscrite (RF-01).

    Cette table reside dans le schema `public`, distinct des schemas
    `tenant_<slug>` qui contiennent les donnees metier de chaque entreprise
    (cf. section 27.2 - strategie schema-per-tenant).
    """

    __tablename__ = "companies"
    __table_args__ = (
        db.CheckConstraint(
            "subscription_plan IN ('TRIAL','STANDARD','PRO','ENTERPRISE')",
            name="ck_companies_subscription_plan",
        ),
        db.CheckConstraint(
            "subscription_status IN ('TRIAL','ACTIVE','SUSPENDED','CANCELLED')",
            name="ck_companies_subscription_status",
        ),
        _PUBLIC_SCHEMA_ARGS,
    )

    name = db.Column(db.String(150), nullable=False)

    # Nom du schema PostgreSQL dedie (ex. "tenant_quincaillerie_ouaga"),
    # genere a l'inscription (RF-01) par slugification de `name` - cf.
    # scripts/provision_tenant.py et app/utils/tenant.py.
    schema_name = db.Column(db.String(63), nullable=False, unique=True, index=True)

    # Adresse e-mail de contact / administrateur initial (RF-01) - hors
    # perimetre strict du MPD section 14.2 mais necessaire pour l'inscription en
    # ligne (creation du compte ADMIN initial, communications d'abonnement).
    contact_email = db.Column(db.String(255), nullable=False)

    subscription_plan = db.Column(
        db.String(20), nullable=False, default=SubscriptionPlan.TRIAL.value
    )
    subscription_status = db.Column(
        db.String(20), nullable=False, default=SubscriptionStatus.TRIAL.value
    )
    subscription_expires_at = db.Column(db.DateTime, nullable=True)

    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<Company {self.schema_name} - {self.name}>"


class UserIndex(db.Model):
    """Index global `email -> schema_name` (schema `public`, section 27.7).

    Permet a `/auth/login` de localiser le tenant d'un utilisateur sans
    parcourir tous les schemas. Maintenu par l'application a la creation,
    mise a jour (changement d'email) et suppression d'un utilisateur - cf.
    app/utils/tenant.py.
    """

    __tablename__ = "user_index"
    __table_args__ = _PUBLIC_SCHEMA_ARGS

    email = db.Column(db.String(120), primary_key=True)
    schema_name = db.Column(db.String(63), nullable=False, index=True)
