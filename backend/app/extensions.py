"""
Instances partagées des extensions Flask.

Déclarées ici (sans application liée) pour éviter les imports circulaires,
puis initialisées dans `app/__init__.py` via `extension.init_app(app)`.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_marshmallow import Marshmallow

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
ma = Marshmallow()

from flask_limiter import Limiter


def _get_real_ip():
    """Résolution IP réelle : Cloudflare → reverse-proxy → socket."""
    from flask import request
    return (
        request.headers.get("CF-Connecting-IP")
        or request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or request.remote_addr
    )


limiter = Limiter(
    key_func=_get_real_ip,
    default_limits=[],          # Pas de limite globale ; seulement par route
    storage_uri="memory://",    # Pas de Redis sur PythonAnywhere
)
