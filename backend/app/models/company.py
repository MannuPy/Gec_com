"""Registre central des tenants (entreprises clientes) du SaaS GesCom-BF."""
import enum

from app.extensions import db
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin
from app.utils.db_dialect import is_postgres

_PUBLIC_SCHEMA_ARGS: dict = {"schema": "public"} if is_postgres() else {}


class SubscriptionPlan(str, enum.Enum):
    TRIAL = "TRIAL"
    STANDARD = "STANDARD"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"


class SubscriptionStatus(str, enum.Enum):
    TRIAL = "TRIAL"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    CANCELLED = "CANCELLED"


class Company(db.Model, UUIDPrimaryKeyMixin, TimestampMixin):
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
    schema_name = db.Column(db.String(63), nullable=False, unique=True, index=True)
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
        return "<Company " + self.schema_name + " - " + self.name + ">"


class UserIndex(db.Model):
    __tablename__ = "user_index"
    __table_args__ = _PUBLIC_SCHEMA_ARGS

    email = db.Column(db.String(120), primary_key=True)
    schema_name = db.Column(db.String(63), nullable=False, index=True)
