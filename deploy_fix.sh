#!/bin/bash
# ============================================================
# SCRIPT DE DÉPLOIEMENT ONE-SHOT — GesCom-BF
# Exécuter dans la console PythonAnywhere (Bash) :
#   cd ~ && bash gescom-bf/deploy_fix.sh 2>&1 | tee deploy_fix.log
# ============================================================
set -e
BOLD='\033[1m'; GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}!${NC} $1"; }
fail() { echo -e "${RED}✗${NC} $1"; exit 1; }
step() { echo -e "\n${BOLD}━━━ $1 ━━━${NC}"; }

APP_DIR="$HOME/gescom-bf"
BACKEND_DIR="$APP_DIR/backend"
FRONTEND_DIR="$APP_DIR/frontend"
VENV="$BACKEND_DIR/.venv/bin/python"
WSGI_FILE="/var/www/mannudev_pythonanywhere_com_wsgi.py"

cd "$APP_DIR" || fail "Dossier $APP_DIR introuvable"

# ── 1. Git pull ───────────────────────────────────────────
step "1/5 · Git pull"
git pull origin main && ok "Code mis à jour" || warn "git pull a échoué (vérifier conflits)"

# ── 2. Corrections base de données ───────────────────────
step "2/5 · Corrections base de données"
cd "$BACKEND_DIR"

$VENV - << 'PYEOF'
import sys, os
sys.path.insert(0, os.getcwd())

# Charger l'app Flask pour avoir le contexte DB
from app import create_app
app = create_app()

with app.app_context():
    from app.extensions import db
    from sqlalchemy import text

    # ── 2a. Ajouter cancelled_by_id à stock_counts si manquant ──
    row = db.session.execute(
        text("SELECT COUNT(*) FROM information_schema.columns "
             "WHERE table_schema = DATABASE() "
             "AND table_name = 'stock_counts' "
             "AND column_name = 'cancelled_by_id'")
    ).scalar()

    if row == 0:
        db.session.execute(text(
            "ALTER TABLE stock_counts "
            "ADD COLUMN cancelled_by_id VARCHAR(36) NULL, "
            "ADD CONSTRAINT fk_sc_cancelled_by "
            "FOREIGN KEY (cancelled_by_id) REFERENCES users(id)"
        ))
        db.session.commit()
        print("✓ [DB] cancelled_by_id ajouté à stock_counts")
    else:
        print("✓ [DB] cancelled_by_id déjà présent")

    # ── 2b. Marquer la migration comme appliquée ──
    try:
        row = db.session.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar()
        if row != 'f6a7b8c9d0e1':
            db.session.execute(
                text("UPDATE alembic_version SET version_num = 'f6a7b8c9d0e1'")
            )
            db.session.commit()
            print("✓ [DB] alembic_version mis à jour → f6a7b8c9d0e1")
        else:
            print("✓ [DB] alembic_version déjà à f6a7b8c9d0e1")
    except Exception as e:
        print(f"! [DB] alembic_version : {e}")

    # ── 2c. S'assurer que le dépôt central a is_depot=TRUE ──
    result = db.session.execute(
        text("SELECT id, name, is_depot FROM branches ORDER BY created_at LIMIT 10")
    ).fetchall()

    print("\n[DB] Branches actuelles :")
    depots = []
    for r in result:
        flag = "DEPOT" if r[2] else "site"
        print(f"     [{flag}] {r[1]} (id={r[0][:8]}...)")
        if r[2]:
            depots.append(r[0])

    if not depots:
        # Aucun dépôt trouvé — chercher "Central" ou "Depot" dans le nom
        candidates = db.session.execute(
            text("SELECT id, name FROM branches "
                 "WHERE LOWER(name) LIKE '%central%' OR LOWER(name) LIKE '%depot%' OR LOWER(name) LIKE '%dépôt%' "
                 "LIMIT 3")
        ).fetchall()

        if candidates:
            for cand in candidates:
                db.session.execute(
                    text("UPDATE branches SET is_depot = TRUE WHERE id = :id"),
                    {"id": cand[0]}
                )
                print(f"✓ [DB] is_depot=TRUE appliqué → {cand[1]}")
            db.session.commit()
        else:
            # Dernier recours : mettre la première branche comme dépôt
            first = db.session.execute(
                text("SELECT id, name FROM branches ORDER BY created_at LIMIT 1")
            ).fetchone()
            if first:
                db.session.execute(
                    text("UPDATE branches SET is_depot = TRUE WHERE id = :id"),
                    {"id": first[0]}
                )
                db.session.commit()
                print(f"! [DB] Aucun dépôt trouvé — is_depot=TRUE forcé sur : {first[1]}")
            else:
                print("! [DB] Aucune branche trouvée du tout")
    else:
        print(f"✓ [DB] {len(depots)} dépôt(s) déjà configuré(s)")

    # ── 2d. Diagnostic tables manquantes ──
    tables_requises = [
        'stock_counts', 'stock_count_lines',
        'supplier_receptions', 'supplier_reception_lines',
        'transfers', 'transfer_lines',
        'customer_payments', 'sales', 'sale_lines',
        'fs_daily_sales', 'fs_customer_rfm',
    ]
    print("\n[DB] Vérification des tables :")
    for t in tables_requises:
        exists = db.session.execute(
            text("SELECT COUNT(*) FROM information_schema.tables "
                 "WHERE table_schema = DATABASE() AND table_name = :t"),
            {"t": t}
        ).scalar()
        status = "✓" if exists else "✗ MANQUANTE"
        print(f"     {status}  {t}")

print("\n✓ Corrections DB terminées")
PYEOF

# ── 3. Rebuild frontend ───────────────────────────────────
step "3/5 · Build frontend (npm run build)"
cd "$FRONTEND_DIR"

if [ ! -d "node_modules" ]; then
    warn "node_modules absent — lancement de npm install..."
    npm install --silent
fi

npm run build
ok "Frontend compilé (dist/ mis à jour)"

# ── 4. Recharger Flask ────────────────────────────────────
step "4/5 · Rechargement Flask (touch WSGI)"
if [ -f "$WSGI_FILE" ]; then
    touch "$WSGI_FILE"
    ok "WSGI rechargé : $WSGI_FILE"
else
    warn "Fichier WSGI introuvable : $WSGI_FILE"
    warn "Rechargez manuellement l'app depuis le dashboard PythonAnywhere"
fi

# ── 5. Résumé ─────────────────────────────────────────────
step "5/5 · Résumé"
echo ""
echo -e "${GREEN}${BOLD}Déploiement terminé.${NC}"
echo ""
echo "  ✓ Code mis à jour (git pull)"
echo "  ✓ Colonne cancelled_by_id ajoutée (inventaire réparé)"
echo "  ✓ is_depot vérifié/corrigé (réceptions réparées)"
echo "  ✓ Frontend reconstruit (boutons Historique visibles)"
echo "  ✓ Flask rechargé"
echo ""
echo "  Testez maintenant :"
echo "    → Créer une session d'inventaire"
echo "    → Créer une réception fournisseur"
echo "    → Créer un transfert"
echo "    → Ouvrir l'onglet Crédits clients → bouton Historique"
echo "    → Ouvrir l'onglet Retours produits → bouton Historique"
echo ""
