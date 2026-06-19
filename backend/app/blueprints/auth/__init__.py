"""Blueprint d'authentification (login / refresh / logout / profil courant).

Cf. 17-API-REST.md §Auth et 18-SECURITE.md (politique JWT, RG-36).
"""
from flask import Blueprint

auth_bp = Blueprint("auth", __name__)

from app.blueprints.auth import routes  # noqa: E4