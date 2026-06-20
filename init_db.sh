#!/bin/bash
# GesCom-BF — Initialisation complète de la base de données
# Exécuter UNE SEULE FOIS après setup_env.sh, sur une base vide.
# Usage: bash ~/gescom-bf/init_db.sh
set -euo pipefail

BACKEND_DIR="$HOME/gescom-bf/backend"
cd "$BACKEND_DIR"
export FLASK_APP=app

echo "=== GesCom-BF — Initialisation base de données ==="

echo "── 1/4 Migrations ────────────────────────────"
flask db upgrade
echo "✓ Tables créées"

echo "── 2/4 Données de référence (RBAC, sites) ───"
flask seed
echo "✓ Seed de base"

echo "── 3/4 Données de démo (6 mois historique) ──"
read -rp "  Générer des données de démo ? (O/n) : " demo
if [[ "${demo:-O}" != "n" && "${demo:-O}" != "N" ]]; then
    flask seed-demo --months 6
    echo "✓ Données démo générées"
    echo "── ETL + Feature Store ─────────────────────"
    flask etl-daily --days 180
    echo "✓ ETL terminé"
fi

echo "── 4/4 Entraînement modèles ML ──────────────"
flask ml-train-all --months 6
echo "✓ Modèles ML entraînés"

echo ""
echo "=== INITIALISATION TERMINÉE ==="
echo "→ Rechargez l'app : PythonAnywhere > Web > Reload"
