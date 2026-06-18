"""
Configuration de l'application Flask.

Les valeurs sont lues depuis les variables d'environnement (voir .env.example
a la racine du projet). Cf. 09-BACKEND-FLASK.md Config pour la justification
de chaque parametre.
"""
import os
from datetime import timedelta

from dotenv import load_dotenv

# Charge le fichier .env situe a la racine du dossier backend/ (dossier parent
# de ce fichier app/config.py). On utilise __file__ pour un chemin absolu,
# independamment du repertoire de travail courant (CWD). Sans effet si les
# variables sont deja injectees par l'environnement d'execution (Docker...).
# IMPORTANT : sur PythonAnywhere, le CWD est /home/<user>/ et NON le dossier
# backend/, d'ou l'obligation d'utiliser un chemin absolu ici.
_env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
load_dotenv(_env_file)


class BaseConfig:
    """Configuration commune a tous les environnements."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")

    # Par defaut : PostgreSQL (environnement de developpement Docker Compose,
    # cf. docker-compose.yml). Pour un hebergement PythonAnywhere (MySQL),
    # definir DATABASE_URL au format
    # `mysql+pymysql://<utilisateur>:<motdepasse>@<utilisateur>.mysql.pythonanywhere-services.com/<utilisateur>$<base>?charset=utf8mb4`
    # (cf. .env.pythonanywhere.example et docs/25-DEPLOIEMENT-CICD.md §25.9).
    # Le driver `PyMySQL` (pur Python, sans dependance systeme) est inclus
    # dans requirements.txt pour ce cas.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg2://gescom:gescom_dev_password@localhost:5432/gescom_bf",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        # Verifie la connexion avant chaque utilisation : evite les erreurs
        # "MySQL server has gone away" (connexion fermee cote serveur apres
        # `wait_timeout`) ou les connexions Postgres expirees par le pooler.
        "pool_pre_ping": True,
        # Recycle les connexions au bout de 280s, en-deca du `wait_timeout`
        # par defaut de MySQL sur PythonAnywhere (defense en profondeur en
        # complement de `pool_pre_ping`). Sans impact sur PostgreSQL.
        "pool_recycle": int(os.environ.get("SQLALCHEMY_POOL_RECYCLE", "280")),
    }

    # ---- JWT (RG-36) ----
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", 15))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=int(os.environ.get("JWT_REFRESH_TOKEN_EXPIRES_DAYS", 7))
    )
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_ERROR_MESSAGE_KEY = "error"

    # ---- CORS ----
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")

    # ---- Inventaire : seuil d'ecart necessitant justification (RG-33) ----
    INVENTORY_VARIANCE_THRESHOLD_PCT = 5

    # ---- Machine Learning / MLflow / Celery (20-MACHINE-LEARNING.md, 21-PIPELINE-ETL.md) ----
    ML_ARTIFACT_DIR = os.environ.get("ML_ARTIFACT_DIR", "instance/ml_artifacts")
    MLFLOW_TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "file:./mlruns")
    MLFLOW_EXPERIMENT_NAME = os.environ.get("MLFLOW_EXPERIMENT_NAME", "gescom-bf")

    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

    # RG-38 : marge de securite appliquee a la quantite recommandee
    FORECAST_SAFETY_MARGIN = 0.10
    # Seuil de score d'anomalie (Isolation Forest, plus negatif = plus anormal)
    ANOMALY_SCORE_THRESHOLD = -0.10
    ANOMALY_CONTAMINATION = 0.02

    # ---- Documents PDF (recus de vente RF-19, exports rapports RF-29) ----
    COMPANY_NAME = os.environ.get("COMPANY_NAME", "Gescom BF")
    COMPANY_ADDRESS = os.environ.get("COMPANY_ADDRESS", "Ouagadougou, Burkina Faso")
    COMPANY_PHONE = os.environ.get("COMPANY_PHONE", "")

    # ---- Multi-tenant SaaS (RF-01, 27-MODELE-SAAS-MULTITENANT.md) ----
    # Schema PostgreSQL utilise lorsque le claim JWT `company_schema` est
    # absent (jetons emis avant l'introduction du multi-tenant) ou pour les
    # comptes de demonstration non encore indexes dans `public.user_index`.
    # `public` correspond au tenant "historique" V1 mono-tenant.
    # Sur MySQL (PythonAnywhere), ce schema logique est maintenu tel quel :
    # `set_search_path` est un no-op sur MySQL (cf. app/utils/tenant.py) et
    # `is_valid_tenant_schema` accepte la valeur "public".
    DEFAULT_TENANT_SCHEMA = os.environ.get("DEFAULT_TENANT_SCHEMA", "public")

    # ---- Dashboard temps reel (22-DASHBOARD-BI.md section 22.2, SSE) ----
    # Intervalle (secondes) entre deux evenements pousses par
    # `GET /reports/dashboard/stream`. Le flux se ferme apres
    # DASHBOARD_STREAM_MAX_EVENTS pour liberer le worker HTTP ; le client
    # (`useDashboardStream`) se reconnecte automatiquement.
    DASHBOARD_STREAM_INTERVAL_SECONDS = int(
        os.environ.get("DASHBOARD_STREAM_INTERVAL_SECONDS", "5")
    )
    DASHBOARD_STREAM_MAX_EVENTS = int(os.environ.get("DASHBOARD_STREAM_MAX_EVENTS", "60"))

    # ---- Frontend servi par Flask (hebergement mono-processus, ex. PythonAnywhere) ----
    # Si defini et pointant vers un dossier existant (typiquement
    # `frontend/dist` apres `npm run build`), Flask sert le SPA React/Vite et
    # son fallback `index.html` pour les routes client (cf. app/__init__.py
    # `register_frontend`). Laisser vide pour un frontend deploye separement
    # (Vite dev server, Nginx, Vercel/Netlify...).
    SERVE_FRONTEND_DIST = os.environ.get("SERVE_FRONTEND_DIST")


class DevConfig(BaseConfig):
    DEBUG = True


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql+psycopg2://gescom:gescom_dev_password@localhost:5432/gescom_bf_test",
    )


class ProdConfig(BaseConfig):
    DEBUG = False
    # Derriere un reverse proxy HTTPS (PythonAnywhere, Nginx...), les URLs
    # generees (ex. liens dans les PDF/emails) doivent utiliser le schema https.
    PREFERRED_URL_SCHEME = "https"


CONFIG_BY_NAME = {
    "development": DevConfig,
    "testing": TestingConfig,
    "production": ProdConfig,
}


def get_config(env_name: str | None = None):
    env_name = env_name or os.environ.get("FLASK_ENV", "development")
    return CONFIG_BY_NAME.get(env_name, DevConfig)
