"""
Journal d'audit applicatif.

Cf. 16-CONTRAINTES-SQL.md (table `audit_logs`, partitionnement par mois en
production) et 18-SECURITE.md (table des types d'événements de sécurité).
En V1 mono-tenant, la table n'est pas partitionnée ; le partitionnement par
mois pourra être ajouté via une migration dédiée avant la mise en
production (cf. 25-DEPLOIEMENT-CICD.md).
"""
from app.extensions import db
from app.models.base import UUIDPrimaryKeyMixin


class AuditLog(db.Model, UUIDPrimaryKeyMixin):
    __tablename__ = "audit_logs"

    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)
    event_type = db.Column(db.String(64), nullable=False, index=True)
    entity_type = db.Column(db.String(64), nullable=True)
    entity_id = db.Column(db.String(36), nullable=True)
    description = db.Column(db.String(500), nullable=True)
    metadata_json = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), index=True)

    user = db.relationship("User", lazy="joined")

    @staticmethod
    def record(event_type: str, user_id: str | None = None, entity_type: str | None = None,
               entity_id: str | None = None, description: str | None = None,
               metadata: dict | None = None) -> "AuditLog":
        """Crée (sans committer) une entrée d'audit — appelé par les services métier."""
        entry = AuditLog(
            user_id=user_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            metadata_json=metadata,
        )
        db.session.add(entry)
        return entry
