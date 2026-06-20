#!/bin/bash
# GesCom-BF — Configuration initiale de l'environnement PythonAnywhere
# Exécuter UNE SEULE FOIS lors de la première installation.
# Usage: bash ~/gescom-bf/setup_env.sh
set -euo pipefail

USERNAME=$(whoami)
PROJECT_DIR="$HOME/gescom-bf"
ENV_FILE="$PROJECT_DIR/backend/.env"

echo "=== GesCom-BF — setup_env.sh ==="
echo "Utilisateur : $USERNAME"

# ── Si .env existe et est valide, proposer de le conserver ──────
if [ -f "$ENV_FILE" ]; then
    DB=$(grep "^DATABASE_URL" "$ENV_FILE" 2>/dev/null | cut -d= -f2-)
    if [[ "$DB" != *"CHANGE_ME"* && -n "$DB" ]]; then
        echo "✓ .env existant avec une DATABASE_URL valide détectée."
        read -rp "  Conserver ce fichier ? (O/n) : " keep
        [[ "${keep:-O}" != "n" && "${keep:-O}" != "N" ]] && echo "Rien à faire." && exit 0
    fi
fi

# ── Saisie des informations ──────────────────────────────────────
echo ""
echo "Entrez vos informations PythonAnywhere :"
read -rsp "  Mot de passe MySQL : " DB_PASS; echo
read -rsp "  Mot de passe admin (flask seed) : " ADMIN_PASS; echo
read -rp  "  Nom entreprise [GesCom BF] : " COMPANY_NAME
COMPANY_NAME="${COMPANY_NAME:-GesCom BF}"

# ── Génération des clés secrètes ────────────────────────────────
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(48))")
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(48))")

# ── Écriture du .env ────────────────────────────────────────────
cat > "$ENV_FILE" << ENV
# GesCom-BF — Environnement PythonAnywhere
# Généré le $(date "+%Y-%m-%d %H:%M")
# NE PAS COMMITTER CE FICHIER

# ── Base de données MySQL ──────────────────────────────────────
DATABASE_URL=mysql+pymysql://${USERNAME}:${DB_PASS}@${USERNAME}.mysql.pythonanywhere-services.com/${USERNAME}\$gescom_bf?charset=utf8mb4

# ── Flask ─────────────────────────────────────────────────────
FLASK_APP=app
FLASK_ENV=production
SECRET_KEY=${SECRET_KEY}

# ── JWT ───────────────────────────────────────────────────────
JWT_SECRET_KEY=${JWT_SECRET_KEY}
JWT_ACCESS_TOKEN_EXPIRES_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRES_DAYS=7

# ── CORS + Frontend ───────────────────────────────────────────
CORS_ORIGINS=https://${USERNAME}.pythonanywhere.com
SERVE_FRONTEND_DIST=/home/${USERNAME}/gescom-bf/frontend/dist

# ── Compte admin initial (flask seed) ─────────────────────────
SEED_ADMIN_EMAIL=admin@gescom-bf.com
SEED_ADMIN_PASSWORD=${ADMIN_PASS}

# ── Informations entreprise (PDF, exports) ────────────────────
COMPANY_NAME=${COMPANY_NAME}
COMPANY_ADDRESS=Ouagadougou, Burkina Faso
COMPANY_PHONE=+226 00 00 00 00

# ── Dashboard vendeur ─────────────────────────────────────────
COMMISSION_RATE=0.02
VENDEUR_MONTHLY_TARGET=500000

# ── Multi-tenant (ne pas modifier) ───────────────────────────
DEFAULT_TENANT_SCHEMA=public

# ── SSE désactivé (PythonAnywhere mono-worker) ───────────────
DISABLE_SSE=true
DASHBOARD_STREAM_INTERVAL_SECONDS=5
DASHBOARD_STREAM_MAX_EVENTS=60

# ── ML / Artefacts ────────────────────────────────────────────
ML_ARTIFACT_DIR=/home/${USERNAME}/gescom-bf/backend/instance/ml_artifacts
MLFLOW_TRACKING_URI=file:/home/${USERNAME}/gescom-bf/backend/mlruns
MLFLOW_EXPERIMENT_NAME=gescom-bf
ENV

chmod 600 "$ENV_FILE"
echo ""
echo "✓ .env créé → $ENV_FILE"
echo "✓ Permissions : 600 (lecture propriétaire uniquement)"
echo ""
echo "Étape suivante :"
echo "  bash ~/gescom-bf/deploy.sh"
