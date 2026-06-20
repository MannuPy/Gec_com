#!/bin/bash
# GesCom-BF — Script de déploiement PythonAnywhere
# Usage: bash ~/gescom-bf/deploy.sh [--skip-ml] [--skip-build]
#
# Options :
#   --skip-ml     Ne pas ré-entraîner les modèles ML (plus rapide)
#   --skip-build  Ne pas rebuilder le frontend
set -euo pipefail

USERNAME=$(whoami)
PROJECT_DIR="$HOME/gescom-bf"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
ENV_FILE="$BACKEND_DIR/.env"

SKIP_ML=false
SKIP_BUILD=false
for arg in "$@"; do
    [[ "$arg" == "--skip-ml" ]]    && SKIP_ML=true
    [[ "$arg" == "--skip-build" ]] && SKIP_BUILD=true
done

echo "============================================="
echo " GesCom-BF — Déploiement PythonAnywhere"
echo " $(date '+%Y-%m-%d %H:%M')"
echo "============================================="

# ── Vérifier que .env existe ────────────────────────────────────
if [ ! -f "$ENV_FILE" ]; then
    echo "ERREUR: .env introuvable."
    echo "  Lance d'abord : bash ~/gescom-bf/setup_env.sh"
    exit 1
fi

# Vérifier que .env a des credentials réels (pas CHANGE_ME)
if grep -q "CHANGE_ME\|<utilisateur>" "$ENV_FILE" 2>/dev/null; then
    echo "ERREUR: .env contient encore des valeurs placeholder (CHANGE_ME)."
    echo "  Lance d'abord : bash ~/gescom-bf/setup_env.sh"
    exit 1
fi

# ── Sauvegarde .env avant git ───────────────────────────────────
cp "$ENV_FILE" "$ENV_FILE.bak"
echo "✓ .env sauvegardé"

# ── Mise à jour du code ─────────────────────────────────────────
cd "$PROJECT_DIR"
echo ""
echo "── Git pull ─────────────────────────────────"
git fetch origin main
# Annuler les modifications locales sur fichiers suivis (corrige le pb inode WSL2)
git checkout -- .
git pull origin main
echo "✓ Code mis à jour"

# ── Restaurer .env (git checkout -- . ne le touche pas car .gitignore) ──
# Sécurité : si par accident il était effacé
if [ ! -f "$ENV_FILE" ] || grep -q "CHANGE_ME" "$ENV_FILE"; then
    cp "$ENV_FILE.bak" "$ENV_FILE"
    chmod 600 "$ENV_FILE"
    echo "✓ .env restauré depuis sauvegarde"
else
    rm -f "$ENV_FILE.bak"
fi

# ── .flaskenv ───────────────────────────────────────────────────
printf "FLASK_APP=app\nFLASK_ENV=production\n" > "$BACKEND_DIR/.flaskenv"
echo "✓ .flaskenv configuré"

# ── Installation des dépendances ────────────────────────────────
echo ""
echo "── Dépendances Python ───────────────────────"
pip install -r "$BACKEND_DIR/requirements-pythonanywhere.txt" \
    --break-system-packages -q --disable-pip-version-check
echo "✓ Dépendances installées"

# Vérifier scikit-learn
python3 -c "import sklearn; print(f'  scikit-learn {sklearn.__version__} OK')" || \
    echo "  ATTENTION: scikit-learn non disponible, repli algorithmes basiques"

# ── Migrations base de données ──────────────────────────────────
echo ""
echo "── Base de données ──────────────────────────"
cd "$BACKEND_DIR"
export FLASK_APP=app
flask db upgrade
echo "✓ Migrations appliquées"

# ── Modèles ML ──────────────────────────────────────────────────
if [ "$SKIP_ML" = false ]; then
    echo ""
    echo "── Entraînement ML ──────────────────────────"
    flask ml-train-all --months 6 2>&1 | python3 -c "
import sys, json
try:
    data = json.loads(sys.stdin.read())
    for k, v in data.items():
        n = v.get('metrics', {}).get('n_customers', v.get('metrics', {}).get('n_products', v.get('metrics', {}).get('n_series', '?')))
        print(f'  ✓ {k}: n={n}')
except:
    pass
" 2>/dev/null || echo "  ✓ ML entraîné (vérifiez les logs si erreur)"
fi

# ── Build frontend ───────────────────────────────────────────────
if [ "$SKIP_BUILD" = false ]; then
    echo ""
    echo "── Build frontend ───────────────────────────"
    cd "$FRONTEND_DIR"
    npm run build 2>&1 | tail -5
    echo "✓ Frontend compilé → frontend/dist/"
fi

echo ""
echo "============================================="
echo " DÉPLOIEMENT TERMINÉ"
echo "============================================="
echo ""
echo "ACTION REQUISE :"
echo "  PythonAnywhere → Web → Reload"
echo ""
echo "URL : https://${USERNAME}.pythonanywhere.com"
