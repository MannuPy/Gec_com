"""Blueprint de consultation et ajustement du stock (RF-13 à RF-17)."""
from flask import Blueprint

stock_bp = Blueprint("stock", __name__)

from app.blueprints.stock import routes  # noqa: E402,F401
