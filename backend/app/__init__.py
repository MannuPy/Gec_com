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
import time as _time
from datetime import datetime as _dt

from flask import Flask, jsonify, send_from_directory

from app.config import get_config
from app.extensions import db, migrate, jwt, cors, ma, limiter
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
    # ── Flask-Limiter (rate limiting) — toujours initialisé ─────────────────
    limiter.init_app(app)

    # ── Sentry : monitoring erreurs (optionnel) ──────────────────────────────
    _sentry_dsn = app.config.get("SENTRY_DSN") or os.environ.get("SENTRY_DSN")
    if _sentry_dsn:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.flask import FlaskIntegration
            sentry_sdk.init(
                dsn=_sentry_dsn,
                integrations=[FlaskIntegration()],
                traces_sample_rate=0.1,          # 10 % des requêtes tracées
                environment=os.environ.get("FLASK_ENV", "production"),
                release=os.environ.get("APP_VERSION", "dev"),
            )
            app.logger.info("Sentry initialisé (DSN configuré)")
        except ImportError:
            app.logger.warning("sentry-sdk non installé — monitoring Sentry désactivé")

    register_error_handlers(app)
    register_jwt_callbacks(app)
    register_tenant_middleware(app)
    register_blueprints(app)
    register_cli(app)
    register_frontend(app)

    _start_time = _time.monotonic()

    @app.get("/health")
    def health():
        """Endpoint public de supervision enrichi (cf. 28-MONITORING-OBSERVABILITE.md).

        Retourne :
          - status        : "ok" ou "degraded"
          - version       : version de l'app (APP_VERSION dans .env ou "dev")
          - uptime_s      : secondes depuis le démarrage du processus Flask
          - db            : "ok" ou message d'erreur (ping SELECT 1)
          - ml_models     : nombre de modèles actifs dans ml_models
          - timestamp_utc : horodatage de la réponse
        """
        from sqlalchemy import text

        # Ping base de données
        try:
            db.session.execute(text("SELECT 1"))
            db_status = "ok"
        except Exception as exc:
            db_status = f"error: {exc}"

        # Nombre de modèles ML actifs
        try:
            from app.models.ml import MLModel
            ml_active = db.session.query(MLModel).filter_by(is_active=True).count()
        except Exception:
            ml_active = -1

        overall = "ok" if db_status == "ok" else "degraded"

        return jsonify({
            "status":        overall,
            "version":       os.environ.get("APP_VERSION", "dev"),
            "uptime_s":      round(_time.monotonic() - _start_time, 1),
            "db":            db_status,
            "ml_models_actifs": ml_active,
            "timestamp_utc": _dt.utcnow().isoformat() + "Z",
        }), 200 if overall == "ok" else 503

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

        Cache-Control :
        - assets/ (JS/CSS hasches par Vite) : immutable, 1 an — le hash garantit
          l'invalidation automatique a chaque nouveau build.
        - index.html (et toutes les routes SPA) : no-cache — le navigateur doit
          toujours revalider pour obtenir les references de chunks a jour.
          Sans cela, un rechargement apres deploiement peut tenter de charger
          d'anciens chunks (supprimes) : "Failed to fetch dynamically imported module".
        """
        if path:
            static_file = os.path.join(dist_dir, path)
            if os.path.isfile(static_file):
                response = send_from_directory(dist_dir, path)
                # Assets haches (Vite met un hash de contenu dans le nom de fichier)
                # → peuvent etre caches indefiniment.
                if path.startswith("assets/") or path.endswith((".js", ".css", ".woff2", ".woff")):
                    response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
                return response
        # index.html — JAMAIS mis en cache : doit toujours refleter le dernier build.
        response = send_from_directory(dist_dir, "index.html")
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
