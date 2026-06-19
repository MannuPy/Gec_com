"""
Application factory Flask - GesCom-BF.

Cf. 09-BACKEND-FLASK.md pour la structure generale (Blueprints, services,
modeles) et 27-MODELE-SAAS-MULTITENANT.md pour le modele multi-tenant.

Deux modes de deploiement supportes (detectes automatiquement via DATABASE_URL
et app/utils/db_dialect.py) :

- PostgreSQL (Docker Compose, VPS) : multi-tenant schema-per-tenant ; le
  middleware `set_tenant_schema` resout le schema du tenant courant (claim JWT
  `company_schema`) a chaque requete ; `public` porte le registre central
  (`Company`, `user_index`).

- MySQL (PythonAnywhere, cf. docs/32-GUIDE-DEPLOIEMENT-PYTHONANYWHERE.md) :
  mono-tenant ; `SET search_path` et `CREATE SCHEMA` sont neutralises
  (app/utils/tenant.py, app/models/company.py) ; les tables `companies` et
  `user_index` sont creees directement dans la base applicative.
"""
import os

from flask import Flask, jsonify, send_from_directory

from app.config import get_config
from app.extensions import db, migrate, jwt, cors, ma
from app.middleware.tenant import register_tenant_middleware
from app.utils.errors import register_error_handlers


def create_app(env_name: str | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config(env_name))

    # ---- Extensions ----
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    ma.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    register_error_handlers(app)
    register_jwt_callbacks(app)
    register_tenant_middleware(app)
    register_blueprints(app)
    register_cli(app)
    register_frontend(app)

    @app.get("/health")
    def health():
        """Endpoint public de supervision (cf. 28-MONITORING-OBSERVABILITE.md)."""
        return jsonify({"status": "ok"})

    return app


def register_jwt_callbacks(app: Flask) -> None:
    from app.models.auth import TokenBlocklist

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(_jwt_header, jwt_payload):
        jti = jwt_payload["jti"]
        return db.session.query(TokenBlocklist.id).filter_by(jti=jti).first() is not None

    @jwt.expired_token_loader
    def expired_token_callback(_jwt_header, _jwt_payload):
        return jsonify({"error": "TOKEN_EXPIRED", "message": "Le jeton a expire."}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(_reason):
        return jsonify({"error": "INVALID_TOKEN", "message": "Jeton invalide."}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(_reason):
        return jsonify({"error": "AUTHORIZATION_REQUIRED", "message": "Authentification requise."}), 401

    @jwt.revoked_token_loader
    def revoked_token_callback(_jwt_header, _jwt_payload):
        return jsonify({"error": "TOKEN_REVOKED", "message": "Le jeton a ete revoque."}), 401


def register_blueprints(app: Flask) -> None:
    from app.blueprints.auth import auth_bp
    from app.blueprints.users import users_bp
    from app.blueprints.products import products_bp
    from app.blueprints.stock import stock_bp
    from app.blueprints.suppliers import suppliers_bp
    from app.blueprints.transfers import transfers_bp
    from app.blueprints.sales import sales_bp
    from app.blueprints.reports import reports_bp
    from app.blueprints.inventory import inventory_bp
    from app.blueprints.analytics import analytics_bp

    api_prefix = "/api/v1"
    app.register_blueprint(auth_bp, url_prefix=f"{api_prefix}/auth")
    app.register_blueprint(users_bp, url_prefix=f"{api_prefix}/users")
    app.register_blueprint(products_bp, url_prefix=f"{api_prefix}")
    app.register_blueprint(stock_bp, url_prefix=f"{api_prefix}/stock")
    app.register_blueprint(suppliers_bp, url_prefix=f"{api_prefix}")
    app.register_blueprint(transfers_bp, url_prefix=f"{api_prefix}/transfers")
    app.register_blueprint(sales_bp, url_prefix=f"{api_prefix}/sales")
    app.register_blueprint(reports_bp, url_prefix=f"{api_prefix}/reports")
    app.register_blueprint(inventory_bp, url_prefix=f"{api_prefix}/inventory")
    app.register_blueprint(analytics_bp, url_prefix=f"{api_prefix}/analytics")


def register_cli(app: Flask) -> None:
    """Enregistre les commandes `flask <commande>` (cf. app/cli.py).

    Utilisees en remplacement de Celery beat sur les hebergements sans
    worker dedie (ex. PythonAnywhere, cf. DEPLOIEMENT-PYTHONANYWHERE.md) via
    les "Scheduled tasks" de la plateforme.
    """
    from app.cli import register_cli as _register_cli

    _register_cli(app)


def register_frontend(app: Flask) -> None:
    """Sert optionnellement le build frontend (SPA React/Vite) depuis Flask.

    Active si la variable d'environnement `SERVE_FRONTEND_DIST` pointe vers
    un dossier existant (typiquement `frontend/dist` apres `npm run build`).
    Utile sur un hebergement mono-processus (PythonAnywhere) ou frontend et
    API sont servis sous le meme nom de domaine (pas de CORS a configurer).

    Toutes les routes hors `/api/*` et `/health` renvoient `index.html`
    (fallback SPA pour le routeur cote client, cf. frontend/src/app/router.tsx),
    sauf si le chemin correspond a un fichier statique existant (JS/CSS/icones).
    """
    # Chemin vers le build Vite : priorite a SERVE_FRONTEND_DIST, sinon
    # fallback relatif au projet (utile si npm run build tourne avant flask).
    serve_dist = app.config.get("SERVE_FRONTEND_DIST")
    if serve_dist:
        dist_dir = os.path.abspath(serve_dist)
    else:
        dist_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
        )

    # N'activer le service des fichiers statiques que si le dossier existe.
    if not os.path.isdir(dist_dir):
        return

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_spa(path: str):
        """Sert les assets statiques du build Vite, ou index.html en fallback.

        Ordre de resolution :
        1. Fichier statique existant dans dist/ (JS, CSS, images, etc.).
        2. index.html (fallback SPA pour les routes geres cote client).

        Les routes /api/* et /health ne passent jamais par ce handler car
        leurs blueprints sont enregistres en premier par Flask.
        """
        if path:
            static_file = os.path.join(dist_dir, path)
            if os.path.isfile(static_file):
                return send_from_directory(dist_dir, path)
        return send_from_directory(dist_dir, "index.html")
