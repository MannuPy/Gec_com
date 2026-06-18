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
