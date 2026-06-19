"""Blueprint de transferts inter-sites (RF-12, RG-17/RG-18)."""
from flask import Blueprint

transfers_bp = Blueprint("transfers", __name__)

from app.blueprints.transfers import routes  # noqa: E402,