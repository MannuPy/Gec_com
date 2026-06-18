"""Blueprint catalogue : produits, catégories, marques, sites (RF-06 à RF-10)."""
from flask import Blueprint

products_bp = Blueprint("products", __name__)

from app.blueprints.products import routes  # noqa: E402,F401
