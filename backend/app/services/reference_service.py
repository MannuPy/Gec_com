"""Génération des références lisibles (réceptions, transferts, ventes).

Format : `<PREFIXE>-<AAAAMMJJ>-<SUFFIXE ALEATOIRE>` — court, lisible, et sans
dépendance à un compteur séquentiel partagé (donc compatible avec une
création hors-ligne future, cf. 26-GESTION-OFFLINE-PWA.md).
"""
import uuid
from datetime import datetime


def generate_reference(prefix: str) -> str:
    return f"{prefix}-{datetime.utcnow():%Y%m%d}-{uuid.uuid4().hex[:6].upper()}"
