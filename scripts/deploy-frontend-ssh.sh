#!/bin/bash
# ============================================================
# GesCom-BF — Script de déploiement frontend (Solution 2 : SSH local)
# ============================================================
#
# PRÉREQUIS : Node.js installé sur VOTRE ORDINATEUR (pas PythonAnywhere)
#
# USAGE :
#   chmod +x scripts/deploy-frontend-ssh.sh
#   ./scripts/deploy-frontend-ssh.sh <votre-username-pythonanywhere>
#
# EXEMPLE :
#   ./scripts/deploy-frontend-ssh.sh mannu
#
# Ce script :
#   1. Build le frontend React en local
#   2. Copie le dossier dist/ sur PythonAnywhere via SCP (SSH)
#   3. Recharge l'application web via l'API PythonAnywhere
#
# Cf. docs/33-GUIDE-COMPLET-MISE-EN-LIGNE-PYTHONANYWHERE.md §Solution 2
# ============================================================

set -e   # arrêter le script si une commande échoue

# ---- Paramètres ----
PA_USERNAME="${1:-}"

if [ -z "$PA_USERNAME" ]; then
    echo "❌ Erreur : fournir votre username PythonAnywhere en argument."
    echo "   Usage : ./scripts/deploy-frontend-ssh.sh <username>"
    exit 1
fi

PA_HOST="ssh.pythonanywhere.com"
PA_REMOTE_PATH="/home/$PA_USERNAME/gescom-bf/frontend/dist"

echo "============================================"
echo "  GesCom-BF — Déploiement frontend"
echo "  Destination : $PA_USERNAME@$PA_HOST"
echo "============================================"
echo ""

# ---- Se placer à la racine du projet ----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# ---- Étape 1 : Vérifier Node.js ----
echo "📋 Vérification Node.js..."
if ! command -v node &>/dev/null; then
    echo "❌ Node.js n'est pas installé sur votre ordinateur."
    echo "   Télécharger depuis : https://nodejs.org"
    exit 1
fi
echo "   Node.js $(node --version) ✅"
echo "   npm $(npm --version) ✅"
echo ""

# ---- Étape 2 : Installer les dépendances frontend ----
echo "📦 Installation des dépendances frontend..."
cd frontend
npm install
echo "   Dépendances installées ✅"
echo ""

# ---- Étape 3 : Build du frontend ----
echo "🔨 Build du frontend React (Vite)..."
npm run build
echo ""

if [ ! -f "dist/index.html" ]; then
    echo "❌ Le build a échoué : dist/index.html introuvable."
    exit 1
fi

FILE_COUNT=$(find dist -type f | wc -l)
echo "   Build terminé : $FILE_COUNT fichiers dans dist/ ✅"
echo ""

# ---- Étape 4 : Copier vers PythonAnywhere ----
echo "📤 Copie vers PythonAnywhere (SCP)..."
echo "   (Votre mot de passe PythonAnywhere vous sera demandé)"
echo ""

# Créer le dossier de destination si nécessaire
ssh "$PA_USERNAME@$PA_HOST" "mkdir -p $PA_REMOTE_PATH"

# Copier le contenu de dist/ (pas le dossier lui-même)
scp -r dist/* "$PA_USERNAME@$PA_HOST:$PA_REMOTE_PATH/"

echo ""
echo "   Fichiers copiés sur PythonAnywhere ✅"
echo ""

# ---- Étape 5 : Recharger l'application (optionnel, nécessite API token) ----
cd "$PROJECT_ROOT"

if [ -n "$PA_API_TOKEN" ]; then
    echo "🔄 Rechargement de l'application web..."
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST \
        -H "Authorization: Token $PA_API_TOKEN" \
        "https://www.pythonanywhere.com/api/v0/user/$PA_USERNAME/webapps/$PA_USERNAME.pythonanywhere.com/reload/")

    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "   Application rechargée ✅"
    else
        echo "   ⚠️  Recharger manuellement dans l'onglet Web de PythonAnywhere (HTTP: $HTTP_STATUS)"
    fi
else
    echo "ℹ️  Recharger manuellement dans l'onglet Web de PythonAnywhere"
    echo "   (Ou définir PA_API_TOKEN=xxx avant d'appeler ce script)"
fi

echo ""
echo "============================================"
echo "  ✅ Déploiement terminé !"
echo "  🌐 https://$PA_USERNAME.pythonanywhere.com"
echo "============================================"
