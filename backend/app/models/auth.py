"""
Modeles d'authentification et de controle d'acces (RBAC).

Cf. 12-MCD.md / 13-MLD.md (entites UTILISATEUR, ROLE, PERMISSION,
ROLE_PERMISSION) et 18-SECURITE.md (matrice des permissions).
"""
import bcrypt

from datetime import datetime

from app.extensions import db
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin, generate_uuid


class Permission(db.Model, UUIDPrimaryKeyMixin):
    """Permission atomique au format `<ressource>:<action>` (ex. 'sales:create')."""

    __tablename__ = "permissions"

    code = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=False)

    def __repr__(self) -> str:
        return f"<Permission {self.code}>"


class RolePermission(db.Model):
    """Table d'association N:N entre roles et permissions (cf. 13-MLD.md)."""

    __tablename__ = "role_permissions"

    role_id = db.Column(db.String(36), db.ForeignKey("roles.id"), primary_key=True)
    permission_id = db.Column(
        db.String(36), db.ForeignKey("permissions.id"), primary_key=True
    )


class Role(db.Model, UUIDPrimaryKeyMixin, TimestampMixin):
    """Role applicatif : ADMIN, MAGASINIER, VENDEUR (RG-02, RG-03)."""

    __tablename__ = "roles"

    name = db.Column(db.String(32), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)

    permissions = db.relationship(
        "Permission",
        secondary="role_permissions",
        backref=db.backref("roles", lazy="dynamic"),
        lazy="joined",
    )

    def permission_codes(self) -> list[str]:
        return [p.code for p in self.permissions]

    def __repr__(self) -> str:
        return f"<Role {self.name}>"


class User(db.Model, UUIDPrimaryKeyMixin, TimestampMixin):
    """Utilisateur de l'application (RF-01 a RF-05)."""

    __tablename__ = "users"

    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)

    role_id = db.Column(db.String(36), db.ForeignKey("roles.id"), nullable=False)
    role = db.relationship("Role", lazy="joined")

    # Site de rattachement (nullable pour ADMIN, qui voit tous les sites)
    branch_id = db.Column(db.String(36), db.ForeignKey("branches.id"), nullable=True)
    branch = db.relationship("Branch", lazy="joined")

    # Preference de langue d'interface (RF-32) : 'fr' ou 'mos'
    language = db.Column(db.String(8), nullable=False, default="fr")

    is_active = db.Column(db.Boolean, nullable=False, default=True)

    # RF-05 : force le changement de mot de passe a la prochaine connexion.
    # Par defaut False (l'administrateur auto-inscrit via /auth/register
    # choisit son propre mot de passe) ; mis a True explicitement par
    # `create_user()` et lors d'une reinitialisation de mot de passe par un
    # administrateur (cf. blueprints/users/routes.py).
    must_change_password = db.Column(db.Boolean, nullable=False, default=False)

    # ---- Gestion du mot de passe ----
    def set_password(self, raw_password: str) -> None:
        self.password_hash = bcrypt.hashpw(
            raw_password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, raw_password: str) -> bool:
        return bcrypt.checkpw(
            raw_password.encode("utf-8"), self.password_hash.encode("utf-8")
        )

    def __repr__(self) -> str:
        return f"<User {self.email}>"


class TokenBlocklist(db.Model, UUIDPrimaryKeyMixin):
    """Liste de revocation des jetons JWT (logout - RG-36).

    En V2, cette table peut etre remplacee par un stockage Redis avec TTL
    (cf. 18-SECURITE.md), mais une table SQL suffit pour le volume V1.
    """

    __tablename__ = "token_blocklist"

    jti = db.Column(db.String(36), nullable=False, index=True, unique=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
