"""Blueprint ventes (caisse) et clients (RF-18 à RF-22, RG-20 à RG-27)."""
from flask import Blueprint

sales_bp = Blueprint("sales", __name__)

from app.blueprints.sales import routes  # noqa: E402,