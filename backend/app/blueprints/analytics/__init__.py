"""Blueprint analytics / IA : dashboard avancé, prévisions, ML (RF-24 à RF-29)."""
from flask import Blueprint

analytics_bp = Blueprint("analytics", __name__)

from app.blueprints.analytics import routes  # noqa: E402,F401
