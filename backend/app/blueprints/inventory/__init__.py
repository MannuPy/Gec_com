"""Blueprint inventaire physique (RF-21 à RF-23)."""
from flask import Blueprint

inventory_bp = Blueprint("inventory", __name__)

from app.blueprints.inventory import routes  # noqa: E402,F401
