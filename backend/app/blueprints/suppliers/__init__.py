"""Blueprint fournisseurs et réceptions de marchandises (RF-11, RG-13)."""
from flask import Blueprint

suppliers_bp = Blueprint("suppliers", __name__)

from app.blueprints.suppliers import routes  # noqa: E402,