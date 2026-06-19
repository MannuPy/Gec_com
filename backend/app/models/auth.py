"""Modeles d'authentification et de controle d'acces (RBAC)."""
import bcrypt

from datetime import datetime

from app.extensions import db
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin, generate_uuid


class Permission(db.Model, UUIDPrimaryKeyMixin):
    __tablename__ = "permissions"

    code = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=False)

    def __repr__(self) -> str:
        return "<Permission " + self.code + ">"


class RolePermission(db.Model):
    __tablename__ = "role_permissions"

    role_id = db.Column(db.String(36), db.ForeignKey("roles.id"), primary_key=True)
    permission_id = db.Column(
        db.String(36), db.ForeignKey("permissions.id"), primary_key=True
    )


class Role(db.Model, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "roles"

    name = db.Column(db.String(32), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)

    permissions = db.relationship(
        "Permission",
        secondary="role_permissions",
        backref=db.backref("roles", lazy="dynamic"),
        lazy="joined",
    )

    def permission_codes(self):
        return [p.code for p in self.permissions]

    def __repr__(self) -> str:
        return "<Role " + self.name + ">"


class User(db.Model, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)

    role_id = db.Column(db.String(36), db.ForeignKey("roles.id"), nullable=False)
    role = db.relationship("Role", lazy="joined")

    branch_id = db.Column(db.String(36), db.ForeignKey("branches.id"), nullable=True)
    branch = db.relationship("Branch", lazy="joined")

    language = db.Column(db.String(8), nullable=False, default="fr")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    must_change_password = db.Column(db.Boolean, nullable=False, default=False)

    def set_password(self, raw_password: str) -> None:
        self.password_hash = bcrypt.hashpw(
            raw_password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, raw_password: str) -> bool:
        return bcrypt.checkpw(
            raw_password.encode("utf-8"), self.password_hash.encode("utf-8")
        )

    def __repr__(self) -> str:
        return "<User " + self.email + ">"


class TokenBlocklist(db.Model, UUIDPrimaryKeyMixin):
    __tablename__ = "token_blocklist"

    jti = db.Column(db.String(36), nullable=False, index=True, unique=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
