#!/usr/bin/env python3
"""
GesCom-BF — Script de réparation complète PythonAnywhere
Usage : python3 ~/gescom-bf/fix_all.py
"""
import os, sys, subprocess, secrets

HOME = os.path.expanduser("~")
PROJECT = os.path.join(HOME, "gescom-bf")
BACKEND = os.path.join(PROJECT, "backend")
FRONTEND = os.path.join(PROJECT, "frontend")
USERNAME = os.environ.get("USER", os.path.basename(HOME))

def run(cmd, cwd=None):
    print(f"  $ {cmd}")
    r = subprocess.run(cmd, shell=True, cwd=cwd or BACKEND)
    return r.returncode == 0

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        os.remove(path)
    except FileNotFoundError:
        pass
    open(path, "w").write(content)
    print(f"  OK: {os.path.relpath(path, PROJECT)}")

print("\n" + "="*60)
print(" GesCom-BF — Reparation complete PythonAnywhere")
print("="*60)

# ── 1. FICHIERS TRONQUES ────────────────────────────────────────
print("\n-- 1/6 Correction des fichiers tronques --")

write(os.path.join(BACKEND, "migrations/alembic.ini"),
"[alembic]\nscript_location = migrations\n\n"
"[loggers]\nkeys = root,sqlalchemy,alembic,flask_migrate\n\n"
"[handlers]\nkeys = console\n\n"
"[formatters]\nkeys = generic\n\n"
"[logger_root]\nlevel = WARN\nhandlers = console\nqualname =\n\n"
"[logger_sqlalchemy]\nlevel = WARN\nhandlers =\nqualname = sqlalchemy.engine\n\n"
"[logger_alembic]\nlevel = INFO\nhandlers =\nqualname = alembic\n\n"
"[logger_flask_migrate]\nlevel = INFO\nhandlers =\nqualname = flask_migrate\n\n"
"[handler_console]\nclass = StreamHandler\nargs = (sys.stderr,)\nlevel = NOTSET\nformatter = generic\n\n"
"[formatter_generic]\nformat = %%(levelname)-5.5s [%%(name)s] %%(message)s\ndatefmt = %%H:%%M:%%S\n"
)

write(os.path.join(BACKEND, "app/blueprints/auth/schemas.py"),
'"""Schemas marshmallow pour le blueprint auth."""\n'
'from marshmallow import Schema, fields, validate\n\n\n'
'class LoginSchema(Schema):\n'
'    email = fields.Email(required=True)\n'
'    password = fields.String(required=True, validate=validate.Length(min=1))\n\n\n'
'class ChangePasswordSchema(Schema):\n'
'    current_password = fields.String(required=True, validate=validate.Length(min=1))\n'
'    new_password = fields.String(required=True, validate=validate.Length(min=8))\n\n\n'
'class RegisterSchema(Schema):\n'
'    company_name = fields.String(required=True, validate=validate.Length(min=2, max=150))\n'
'    contact_email = fields.Email(required=False, allow_none=True)\n'
'    admin_full_name = fields.String(required=True, validate=validate.Length(min=2, max=120))\n'
'    admin_email = fields.Email(required=True)\n'
'    admin_password = fields.String(required=True, validate=validate.Length(min=8))\n\n\n'
'class TokenResponseSchema(Schema):\n'
'    access_token = fields.String()\n'
'    refresh_token = fields.String()\n'
'    user = fields.Raw()\n\n\n'
'class CurrentUserSchema(Schema):\n'
'    id = fields.String()\n'
'    email = fields.String()\n'
'    full_name = fields.String()\n'
'    role = fields.String()\n'
'    permissions = fields.List(fields.String())\n'
'    branch_id = fields.String(allow_none=True)\n'
'    branch_name = fields.String(allow_none=True)\n'
)

write(os.path.join(BACKEND, "app/celery_app.py"),
'"""Celery stub no-op si celery non installe."""\nfrom __future__ import annotations\n\n'
'try:\n    from celery import Celery\n    HAS_CELERY = True\nexcept ImportError:\n    HAS_CELERY = False\n'
'    class _FakeTask:\n        def __init__(self, fn):\n            self._fn = fn\n'
'            self.__name__ = getattr(fn, "__name__", "task")\n'
'            self.__module__ = getattr(fn, "__module__", "")\n'
'        def run(self, *a, **kw): return self._fn(*a, **kw)\n'
'        def delay(self, *a, **kw): raise RuntimeError("Celery non disponible.")\n'
'        def __call__(self, *a, **kw): return self._fn(*a, **kw)\n'
'    class Celery:\n        def __init__(self, *a, **kw): self.conf = self\n'
'        def task(self, *a, name=None, **kw):\n'
'            def dec(fn): return _FakeTask(fn)\n'
'            if a and callable(a[0]): return _FakeTask(a[0])\n'
'            return dec\n        def update(self, **kw): pass\n'
'    def crontab(*a, **kw): pass\n\n'
'celery_app = Celery("gescom_bf")\n\n'
'def init_celery(app):\n'
'    if not HAS_CELERY:\n'
'        app.logger.warning("Celery non installe.")\n'
'        return celery_app\n'
'    celery_app.conf.update(\n'
'        broker_url=app.config.get("CELERY_BROKER_URL",""),\n'
'        result_backend=app.config.get("CELERY_RESULT_BACKEND",""),\n'
'        timezone="UTC", enable_utc=True,\n    )\n'
'    class ContextTask(celery_app.Task):\n'
'        def __call__(self, *a, **kw):\n'
'            with app.app_context(): return self.run(*a, **kw)\n'
'    celery_app.Task = ContextTask\n    return celery_app\n'
)

write(os.path.join(BACKEND, "app/tasks/ml_tasks.py"),
'"""Taches ML."""\nfrom __future__ import annotations\nimport logging\n'
'from app.celery_app import celery_app\nlogger = logging.getLogger(__name__)\n\n'
'@celery_app.task(name="app.tasks.ml_tasks.train_demand_forecast_task")\n'
'def train_demand_forecast_task(months: int = 6) -> dict:\n'
'    from app.ml import demand_forecast\n    return demand_forecast.train(months=months)\n\n'
'@celery_app.task(name="app.tasks.ml_tasks.train_credit_scoring_task")\n'
'def train_credit_scoring_task() -> dict:\n'
'    from app.ml import credit_scoring\n    return credit_scoring.train()\n\n'
'@celery_app.task(name="app.tasks.ml_tasks.detect_anomalies_task")\n'
'def detect_anomalies_task(days: int = 90) -> dict:\n'
'    from app.ml import anomaly_detection\n    return anomaly_detection.train(days=days)\n\n'
'@celery_app.task(name="app.tasks.ml_tasks.compute_abc_xyz_task")\n'
'def compute_abc_xyz_task(months: int = 6) -> dict:\n'
'    from app.ml import abc_xyz\n    return abc_xyz.train(months=months)\n\n'
'@celery_app.task(name="app.tasks.ml_tasks.compute_rfm_segments_task")\n'
'def compute_rfm_segments_task(months: int = 12, n_clusters: int = 4) -> dict:\n'
'    from app.ml import rfm_segmentation\n'
'    return rfm_segmentation.train(months=months, n_clusters=n_clusters)\n\n'
'TRAIN_FUNCTIONS = {\n'
'    "DEMAND_FORECAST": train_demand_forecast_task,\n'
'    "CREDIT_SCORING": train_credit_scoring_task,\n'
'    "ANOMALY_DETECTION": detect_anomalies_task,\n'
'    "ABC_XYZ": compute_abc_xyz_task,\n'
'    "RFM_SEGMENTATION": compute_rfm_segments_task,\n}\n'
)

# vite.config.ts
vite = (
    'import { defineConfig } from "vite";\n'
    'import react from "@vitejs/plugin-react";\n'
    'import { VitePWA } from "vite-plugin-pwa";\n'
    'import path from "path";\n\n'
    'export default defineConfig({\n'
    '  plugins: [\n    react(),\n    VitePWA({\n'
    '      registerType: "autoUpdate",\n'
    '      includeAssets: ["icons/*.png"],\n'
    '      manifest: {\n'
    '        name: "GesCom-BF", short_name: "GesCom",\n'
    '        description: "Gestion commerciale multi-sites.",\n'
    '        start_url: "/", display: "standalone",\n'
    '        background_color: "#ffffff", theme_color: "#0f766e",\n'
    '        icons: [\n'
    '          { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },\n'
    '          { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png" },\n'
    '          { src: "/icons/maskable-icon-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },\n'
    '        ],\n      },\n'
    '      workbox: {\n        runtimeCaching: [\n'
    '          { urlPattern: /\\/api\\/v1\\/products/, handler: "NetworkFirst", options: { cacheName: "products-cache", networkTimeoutSeconds: 3, cacheableResponse: { statuses: [0, 200] } } },\n'
    '          { urlPattern: /\\/api\\/v1\\/stock/, handler: "NetworkFirst", options: { cacheName: "stock-cache", networkTimeoutSeconds: 3, cacheableResponse: { statuses: [0, 200] } } },\n'
    '          { urlPattern: /\\.(?:png|jpg|jpeg|svg|woff2?)$/, handler: "CacheFirst", options: { cacheName: "static-assets", expiration: { maxEntries: 100, maxAgeSeconds: 2592000 } } },\n'
    '        ],\n      },\n'
    '      devOptions: { enabled: false },\n    }),\n  ],\n'
    '  resolve: { alias: { "@": path.resolve(__dirname, "./src") } },\n'
    '  server: {\n    host: true, port: 5173,\n'
    '    proxy: {\n      "/api": {\n'
    '        target: process.env.VITE_API_PROXY_TARGET || "http://localhost:5000",\n'
    '        changeOrigin: true, timeout: 0,\n      },\n    },\n  },\n});\n'
)
write(os.path.join(FRONTEND, "vite.config.ts"), vite)

vendeur = (
    'export interface VendeurCashier {\n'
    '  id: string; full_name: string; branch_id: string | null; branch_name: string | null;\n}\n'
    'export interface VendeurKpisJour {\n'
    '  ca_jour: string; nb_ventes: number; panier_moyen: string;\n}\n'
    'export interface VendeurKpisMois {\n'
    '  ca_mois: string; nb_ventes: number; commission_estimee: string;\n'
    '  objectif_mensuel: string; progression_pct: number; commission_rate_pct: number;\n}\n'
    'export interface VendeurHeure { heure: number; ca: number; }\n'
    'export interface VendeurTopProduit {\n'
    '  product_id: string; name: string; sku: string; qte_vendue: number; ca: number;\n}\n'
    'export interface VendeurDerniereVente {\n'
    '  id: string; reference: string; created_at: string | null;\n'
    '  total: string; payment_type: string; customer_name: string | null; nb_lignes: number;\n}\n'
    'export interface VendeurDashboard {\n'
    '  cashier: VendeurCashier; kpis_jour: VendeurKpisJour; kpis_mois: VendeurKpisMois;\n'
    '  historique_jour: VendeurHeure[]; top_produits_mois: VendeurTopProduit[];\n'
    '  dernieres_ventes: VendeurDerniereVente[];\n}\n'
)
write(os.path.join(FRONTEND, "src/types/vendeur.ts"), vendeur)

# ── 2. .env ─────────────────────────────────────────────────────
print("\n-- 2/6 Configuration .env --")
env_path = os.path.join(BACKEND, ".env")
env_ok = False
if os.path.exists(env_path):
    c = open(env_path).read()
    if "CHANGE_ME" not in c and "<utilisateur>" not in c and "DATABASE_URL" in c:
        print("  OK: .env valide conserve")
        env_ok = True

if not env_ok:
    sk = secrets.token_urlsafe(48)
    jk = secrets.token_urlsafe(48)
    env_c = (
        f"DATABASE_URL=mysql+pymysql://{USERNAME}:VOTRE_MDP_MYSQL@"
        f"{USERNAME}.mysql.pythonanywhere-services.com/{USERNAME}$gescom_bf?charset=utf8mb4\n"
        f"FLASK_APP=app\nFLASK_ENV=production\nSECRET_KEY={sk}\nJWT_SECRET_KEY={jk}\n"
        f"JWT_ACCESS_TOKEN_EXPIRES_MINUTES=15\nJWT_REFRESH_TOKEN_EXPIRES_DAYS=7\n"
        f"CORS_ORIGINS=https://{USERNAME}.pythonanywhere.com\n"
        f"SERVE_FRONTEND_DIST=/home/{USERNAME}/gescom-bf/frontend/dist\n"
        f"SEED_ADMIN_EMAIL=admin@gescom-bf.com\nSEED_ADMIN_PASSWORD=GesComAdmin2026!\n"
        f"COMPANY_NAME=GesCom BF\nCOMPANY_ADDRESS=Ouagadougou, Burkina Faso\n"
        f"COMPANY_PHONE=+226 00 00 00 00\nCOMMISSION_RATE=0.02\n"
        f"VENDEUR_MONTHLY_TARGET=500000\nDEFAULT_TENANT_SCHEMA=public\n"
        f"DISABLE_SSE=true\nDASHBOARD_STREAM_INTERVAL_SECONDS=5\n"
        f"DASHBOARD_STREAM_MAX_EVENTS=60\n"
        f"ML_ARTIFACT_DIR=/home/{USERNAME}/gescom-bf/backend/instance/ml_artifacts\n"
        f"MLFLOW_TRACKING_URI=file:/home/{USERNAME}/gescom-bf/backend/mlruns\n"
        f"MLFLOW_EXPERIMENT_NAME=gescom-bf\n"
    )
    open(env_path, "w").write(env_c)
    os.chmod(env_path, 0o600)
    print(f"  ATTENTION: editez DATABASE_URL dans {env_path}")
    print(f"  Remplacez VOTRE_MDP_MYSQL par votre vrai mot de passe MySQL")
    print(f"  Puis relancez: python3 ~/gescom-bf/fix_all.py")
    sys.exit(1)

write(os.path.join(BACKEND, ".flaskenv"), "FLASK_APP=app\nFLASK_ENV=production\n")

# ── 3. DEPENDANCES ───────────────────────────────────────────────
print("\n-- 3/6 Dependances Python --")
req = os.path.join(BACKEND, "requirements-pythonanywhere.txt")
if os.path.exists(req):
    run(f"pip install -r {req} --break-system-packages -q")
else:
    run("pip install Flask Flask-SQLAlchemy Flask-Migrate Flask-JWT-Extended Flask-Cors "
        "flask-marshmallow marshmallow-sqlalchemy PyMySQL python-dotenv bcrypt "
        "pandas numpy scikit-learn joblib reportlab openpyxl --break-system-packages -q")

# ── 4. MIGRATIONS ────────────────────────────────────────────────
print("\n-- 4/6 Migrations base de donnees --")
os.environ["FLASK_APP"] = "app"
os.environ["FLASK_ENV"] = "production"
if not run("flask db upgrade", cwd=BACKEND):
    print("  ECHEC migrations — verifiez DATABASE_URL et relancez")
    sys.exit(1)

# ── 5. SEED ──────────────────────────────────────────────────────
print("\n-- 5/6 Donnees initiales --")
run("flask seed", cwd=BACKEND)

# ── 6. ML ────────────────────────────────────────────────────────
print("\n-- 6/6 Entrainement ML --")
run("flask ml-train-all --months 6", cwd=BACKEND)

print("\n" + "="*60)
print(" REPARATION TERMINEE")
print("="*60)
print("""
Comptes :
  ADMIN      : admin@gescom-bf.com     / GesComAdmin2026!
  VENDEUR    : vendeur@gescom-bf.bf    / Vendeur#2026
  MAGASINIER : magasinier@gescom-bf.bf / Magasinier#2026

Etapes restantes :
  cd ~/gescom-bf/frontend && npm run build
  PythonAnywhere -> Web -> Reload
""")
