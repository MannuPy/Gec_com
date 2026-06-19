# Guide de déploiement — GitHub + PythonAnywhere

> **Version :** V1 (juin 2026) — à jour avec Tableau de bord vendeur, Module comptabilité  
> **Repo :** `https://github.com/MannuPy/Gec_com`  
> **URL de production :** `https://mannu.pythonanywhere.com`  
> **Stack :** Flask 3 · MySQL 8 (PythonAnywhere) · React 18/Vite

---

## Architecture de déploiement

```
GitHub (source) ──── git pull ──── PythonAnywhere
                                        │
                                   Bash console
                                        │
                   ┌────────────────────┴──────────────────────┐
                   │                                           │
             Backend Flask                              Frontend React
         ~/gescom-bf/backend/                       ~/gescom-bf/frontend/
              wsgi.py                                   npm run build
                   │                                       dist/
            MySQL managé                                    │
       <user>$gescom_bf                    servi par Flask (SERVE_FRONTEND_DIST)
```

**Règles de base :**
- PythonAnywhere = MySQL uniquement (pas PostgreSQL)
- Pas de Celery/Redis → tâches planifiées via l'onglet **Scheduled Tasks**
- Le frontend buildé est servi directement par Flask (`SERVE_FRONTEND_DIST`)
- SSE désactivé sur PythonAnywhere (`DISABLE_SSE=true`) → polling automatique

---

## 1. Workflow GitHub (pousser du code)

### 1.1 Push initial ou après modifications

```bash
# Depuis votre machine locale
cd /chemin/vers/Gec_com

git add -A
git commit -m "feat: tableau de bord vendeur + module comptabilité"
git push origin main
```

### 1.2 Fichiers à NE JAMAIS committer

Le `.gitignore` à la racine doit exclure :

```gitignore
# Secrets
backend/.env
frontend/.env.local

# Build frontend
frontend/dist/
frontend/node_modules/

# Python
__pycache__/
*.pyc
backend/.venv/
backend/instance/
backend/mlruns/
backend/ml/

# Divers
*.DS_Store
~$*
```

> ⚠️ Si un `.env` a déjà été commité par erreur :
> ```bash
> git rm --cached backend/.env
> git commit -m "fix: retirer .env du tracking"
> git push origin main
> ```

---

## 2. Déploiement initial sur PythonAnywhere

### 2.1 Prérequis

- Compte PythonAnywhere **plan Developer** (10 $/mois — MySQL requis)
- Base MySQL créée dans l'onglet **Databases** → nommer `gescom_bf`
- Python **3.12** sélectionnable dans les consoles

### 2.2 Cloner et préparer l'environnement

```bash
# Console Bash PythonAnywhere
cd ~
git clone https://github.com/MannuPy/Gec_com.git gescom-bf

# Virtualenv Python 3.12
cd ~/gescom-bf/backend
python3.12 -m venv .venv
source .venv/bin/activate

# Dépendances
pip install --upgrade pip
pip install -r requirements.txt
```

### 2.3 Variables d'environnement (`.env`)

```bash
cp .env.pythonanywhere.example .env
nano .env   # ou vi .env
```

Remplir **toutes** les valeurs marquées `CHANGE_ME` :

```dotenv
# ── Base de données MySQL ──────────────────────────────────────────
DATABASE_URL=mysql+pymysql://mannu:VOTRE_MDP@mannu.mysql.pythonanywhere-services.com/mannu$gescom_bf?charset=utf8mb4

# ── Flask / JWT ────────────────────────────────────────────────────
FLASK_APP=wsgi.py
FLASK_ENV=production
SECRET_KEY=<générer avec : python -c "import secrets; print(secrets.token_urlsafe(48))">
JWT_SECRET_KEY=<générer avec : python -c "import secrets; print(secrets.token_urlsafe(48))">
JWT_ACCESS_TOKEN_EXPIRES_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRES_DAYS=7

# ── Frontend (SPA servi par Flask) ────────────────────────────────
SERVE_FRONTEND_DIST=/home/mannu/gescom-bf/frontend/dist

# ── CORS (inutile si même domaine) ────────────────────────────────
CORS_ORIGINS=https://mannu.pythonanywhere.com

# ── Dashboard temps réel (SSE désactivé sur PythonAnywhere) ────────
DISABLE_SSE=true
DASHBOARD_STREAM_INTERVAL_SECONDS=5
DASHBOARD_STREAM_MAX_EVENTS=60

# ── Tableau de bord vendeur ────────────────────────────────────────
COMMISSION_RATE=0.02
VENDEUR_MONTHLY_TARGET=500000

# ── Machine Learning / ETL ────────────────────────────────────────
ML_ARTIFACT_DIR=/home/mannu/gescom-bf/backend/instance/ml_artifacts
MLFLOW_TRACKING_URI=file:/home/mannu/gescom-bf/backend/mlruns
MLFLOW_EXPERIMENT_NAME=gescom-bf

# ── Compte admin initial ──────────────────────────────────────────
SEED_ADMIN_EMAIL=admin@votre-entreprise.bf
SEED_ADMIN_PASSWORD=MotDePasse_TresSecurise_2026

# ── Informations entreprise (PDF) ─────────────────────────────────
COMPANY_NAME=Votre Quincaillerie
COMPANY_ADDRESS=Ouagadougou, Burkina Faso
COMPANY_PHONE=+226 00 00 00 00

# ── Multi-tenant (ne pas modifier) ────────────────────────────────
DEFAULT_TENANT_SCHEMA=public
```

### 2.4 Migrations et données initiales

```bash
cd ~/gescom-bf/backend
source .venv/bin/activate
export FLASK_APP=wsgi.py

# Créer toutes les tables
flask db upgrade

# Injecter les rôles, permissions, succursales, admin, catalogue
python -m app.seed

# (Optionnel) Données de démonstration
# python -m app.seed_demo
```

### 2.5 Build du frontend React

```bash
# Node.js disponible sur PythonAnywhere via nvm ou node système
cd ~/gescom-bf/frontend

# Vérifier Node
node --version   # 18+ requis

# Si Node absent → utiliser nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.bashrc
nvm install 20
nvm use 20

# Créer le fichier .env de production
echo 'VITE_API_URL=/api/v1' > .env.production

# Installer et builder
npm install
npm run build
# → génère frontend/dist/
```

### 2.6 Configuration WSGI

Dans l'onglet **Web** → **WSGI configuration file**, remplacer **tout** le contenu par :

```python
import sys
import os
from dotenv import load_dotenv

PROJECT_HOME = "/home/mannu/gescom-bf/backend"
if PROJECT_HOME not in sys.path:
    sys.path.insert(0, PROJECT_HOME)

load_dotenv(os.path.join(PROJECT_HOME, ".env"))

from app import create_app
application = create_app()
```

### 2.7 Virtualenv dans l'onglet Web

- **Web** → **Virtualenv** → saisir :  
  `/home/mannu/gescom-bf/backend/.venv`

### 2.8 Premier chargement

- Cliquer **Reload** dans l'onglet Web
- Ouvrir `https://mannu.pythonanywhere.com`
- Se connecter avec `admin@votre-entreprise.bf` / mot de passe configuré

---

## 3. Workflow de mise à jour (après chaque commit)

### 3.1 Séquence standard

```bash
# 1. Sur votre machine — pousser le code
git add -A && git commit -m "..." && git push origin main

# 2. Sur PythonAnywhere (console Bash)
cd ~/gescom-bf
git pull origin main

# 3. Backend : nouvelles dépendances ?
cd backend
source .venv/bin/activate
pip install -r requirements.txt   # idempotent, sans risque

# 4. Backend : nouvelles migrations ?
export FLASK_APP=wsgi.py
flask db upgrade                   # no-op si rien de nouveau

# 5. Frontend : fichiers modifiés ?
cd ../frontend
npm install                        # si package.json a changé
npm run build                      # toujours rebuilder

# 6. Recharger l'application
# → Onglet Web → bouton "Reload"
```

### 3.2 Quand rebuilder le frontend ?

| Changement | npm install | npm run build | Reload |
|---|---|---|---|
| Backend uniquement | ✗ | ✗ | ✓ |
| Fichier `.tsx` / `.ts` | ✗ | ✓ | ✓ |
| `package.json` modifié | ✓ | ✓ | ✓ |
| Variable `VITE_*` dans `.env.production` | ✗ | ✓ | ✓ |

### 3.3 Vérifier l'état des migrations

```bash
# Liste les migrations appliquées vs en attente
flask db current
flask db history --verbose
```

---

## 4. Tâches planifiées (Scheduled Tasks)

Onglet **Tasks** → ajouter les tâches suivantes :

| Heure UTC | Commande | Description |
|---|---|---|
| `01:00` | `/home/mannu/gescom-bf/backend/.venv/bin/flask --app /home/mannu/gescom-bf/backend/wsgi.py etl-daily` | Pipeline ETL quotidien |
| `02:00` | `/home/mannu/gescom-bf/backend/.venv/bin/flask --app /home/mannu/gescom-bf/backend/wsgi.py ml-train-all` | Entraînement modèles ML |
| `03:00` | `/home/mannu/gescom-bf/backend/.venv/bin/flask --app /home/mannu/gescom-bf/backend/wsgi.py ml-detect-anomalies` | Détection anomalies |

> **Note :** Adapter l'heure UTC selon le fuseau horaire de Ouagadougou (UTC+0 = même heure, UTC+0 toute l'année).

Exécution manuelle depuis la console Bash :
```bash
cd ~/gescom-bf/backend
source .venv/bin/activate
export FLASK_APP=wsgi.py
flask etl-daily
flask ml-train-all
```

---

## 5. Nouvelles routes à vérifier après déploiement

Après la mise à jour V1 (juin 2026), tester ces endpoints :

| URL | Description | Permission requise |
|---|---|---|
| `GET /api/v1/reports/vendeur/dashboard` | Tableau de bord vendeur | `sales:create` (JWT) |
| `GET /api/v1/reports/compta/summary` | Bilan comptable simplifié | `reports:read` |
| `GET /api/v1/reports/compta/summary?branch_id=X&date_debut=2026-06-01&date_fin=2026-06-30` | Bilan filtré | `reports:read` |

Navigation frontend (sidebar) :
- `/mon-tableau-de-bord` → Ma performance (rôle Vendeur/Caissier)
- `/comptabilite` → Comptabilité (rôle Admin/Manager)

---

## 6. Dépannage rapide

### Erreur 500 au chargement

```bash
# Lire les logs d'erreur
cat /var/log/mannu.pythonanywhere.com.error.log | tail -50
```

Causes fréquentes :

| Symptôme | Cause | Solution |
|---|---|---|
| `ImportError: No module named 'app'` | `sys.path` incorrect dans WSGI | Vérifier `PROJECT_HOME` dans le fichier WSGI |
| `OperationalError: (2003)` | MySQL inaccessible | Vérifier `DATABASE_URL` dans `.env` |
| `flask db upgrade` échoue | Conflit de migration | `flask db stamp head` puis relancer |
| Page blanche (SPA) | `dist/` absent ou mauvais chemin | Relancer `npm run build`, vérifier `SERVE_FRONTEND_DIST` |
| `ValueError: COMMISSION_RATE` | Variable manquante dans `.env` | Ajouter `COMMISSION_RATE=0.02` dans `.env` |
| SSE bloque les requêtes | uWSGI synchrone | Vérifier `DISABLE_SSE=true` dans `.env` |

### Vérifier la configuration chargée

```bash
cd ~/gescom-bf/backend
source .venv/bin/activate
python -c "
from app import create_app
app = create_app()
with app.app_context():
    from flask import current_app
    print('DB:', current_app.config.get('SQLALCHEMY_DATABASE_URI', '')[:40], '...')
    print('SSE disabled:', current_app.config.get('DISABLE_SSE'))
    print('Frontend dist:', current_app.config.get('SERVE_FRONTEND_DIST'))
    print('Commission rate:', current_app.config.get('COMMISSION_RATE'))
"
```

### Reset complet (si base corrompue)

```bash
# ⚠️ Détruit toutes les données
flask db downgrade base
flask db upgrade
python -m app.seed
```

---

## 7. Checklist de déploiement (à imprimer)

```
PRE-PUSH (machine locale)
  ☐ Tests passent (backend: py_compile, frontend: tsc --noEmit)
  ☐ .env absent du commit (git status | grep .env)
  ☐ frontend/dist/ absent du commit

DÉPLOIEMENT (PythonAnywhere)
  ☐ git pull origin main
  ☐ pip install -r requirements.txt
  ☐ flask db upgrade (vérifier "Running upgrade...")
  ☐ npm install (si package.json changé)
  ☐ npm run build (vérifier "dist/ built in X ms")
  ☐ Reload dans l'onglet Web

VÉRIFICATION
  ☐ Page d'accueil charge (/)
  ☐ Login fonctionne
  ☐ /api/v1/health retourne 200
  ☐ /mon-tableau-de-bord accessible (vendeur)
  ☐ /comptabilite accessible (admin)
  ☐ Logs d'erreur vides (error.log)
```

---

## Références

| Document | Contenu |
|---|---|
| `docs/32-GUIDE-DEPLOIEMENT-PYTHONANYWHERE.md` | Guide technique détaillé (WSGI, MySQL, variables) |
| `docs/33-GUIDE-COMPLET-MISE-EN-LIGNE-PYTHONANYWHERE.md` | Guide pas-à-pas complet (niveau débutant) |
| `backend/.env.pythonanywhere.example` | Modèle de fichier `.env` commenté |
| `backend/deploy/pythonanywhere_wsgi.py` | Template WSGI prêt à copier-coller |
| `docs/25-DEPLOIEMENT-CICD.md` | Architecture CI/CD et stratégie de déploiement |
