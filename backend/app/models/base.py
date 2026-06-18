"""
Classes et mixins de base partagés par tous les modèles.

Convention (cf. 14-MPD.md) : toutes les tables utilisent une clé primaire
UUID et portent les colonnes `created_at` / `updated_at`.
"""
import uuid
from datetime import datetime

from app.extensions import db


def generate_uuid() -> str:
    return str(uuid.uuid4())


class TimestampMixin:
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class UUIDPrimaryKeyMixin:
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
