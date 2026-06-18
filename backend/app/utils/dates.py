"""Utilitaires de parsing de dates pour les API REST.

Utilisé notamment pour la synchronisation incrémentale du catalogue/stock en
mode hors-ligne (`updated_since`, cf. 26-GESTION-OFFLINE-PWA.md §26.7).
"""
from datetime import datetime


def parse_updated_since(raw_value: str | None) -> datetime | None:
    """Parse le paramètre `updated_since` (ISO 8601).

    Une valeur absente ou invalide est ignorée silencieusement (retourne
    `None`, donc pas de filtre appliqué) : la synchro incrémentale dégrade
    alors gracieusement vers une synchro complète.
    """
    if not raw_value:
        return None
    try:
        value = raw_value.strip()
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except ValueError:
        return None
