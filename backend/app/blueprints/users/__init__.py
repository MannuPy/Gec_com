"""Blueprint de gestion des utilisateurs et rôles (RF-01 à RF-05, RG-02/RG-03)."""
from flask import Blueprint

users_bp = Blueprint("users", __name__)

from app.blueprints.users import routes  # noqa: E402,