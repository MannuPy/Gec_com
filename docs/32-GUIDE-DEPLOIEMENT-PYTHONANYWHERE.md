# 32. Guide de déploiement — PythonAnywhere (MySQL, mono-tenant)

> **Environnement cible :** PythonAnywhere plan Developer (10 $/mois)  
> **Base de données :** MySQL 8.0 managé (inclus dans le plan)  
> **Mode applicatif :** mono-tenant V1 (multi-tenant PostgreSQL désactivé)  
> **Prérequis :** compte PythonAnywhere actif, dépôt Git accessible (GitHub/GitLab)

---

## Sommaire

1. [Vue d'ensemble de l'architecture sur PythonAnywhere](#1-vue-densemble)
2. [Créer et configurer la base MySQL](#2-base-mysql)
3. [Cloner le dépôt et créer l'environnement Python](#3-environnement-python)
4. [Installer les dépendances](#4-dependances)
5. [Configurer les variables d'environnement](#5-variables-denvironnement)
6. [Appliquer les migrations et initialiser les données](#6-migrations-et-seed)
7. [Configurer l'application web (WSGI)](#7-configuration-wsgi)
8. [Construire et servir le frontend React](#8-frontend)
9. [Planifier les tâches périodiques (Scheduled Tasks)](#9-taches-planifiees)
10. [Vérification et tests de fumée](#10-verification)
11. [Gestion des mises à jour (déploiement continu)](#11-mises-a-jour)
12. [Sauvegarde MySQL](#12-sauvegarde)
13. [Dépannage (Troubleshooting)](#13-depannage)

---

## 1. Vue d'ensemble

```
Internet (HTTPS)
    │
    ▼
PythonAnywhere — proxy uWSGI
    │
    ├── /api/v1/*  →  Flask (backend/wsgi.py)
    │                     │
    │                     └── MySQL managé (<user>$gescom_bf)
    │
    └── /*         →  Fichiers statiques frontend (frontend/dist/)
                       servis par Flask (SERVE_FRONTEND_DIST)
```

**Points clés :**
- PythonAnywhere fournit MySQL uniquement — PostgreSQL n'est pas disponible.
- Le mode multi-tenant (schema-per-tenant PostgreSQL) est automatiquement désactivé — détecté via `DATABASE_URL` dans `app/utils/db_dialect.py`.
- Celery et Redis ne sont pas requis : les tâches planifiées sont exécutées via les **Scheduled Tasks** de PythonAnywhere (`flask etl-daily`, `flask ml-train-all`, etc.).
- Le frontend React est buildé en local puis servi directement par Flask via `SERVE_FRONTEND_DIST`.

---

## 2. Base MySQL

### 2.1 Créer la base de données

1. Connectez-vous à [https://www.pythonanywhere.com](https://www.pythonanywhere.com).
2. Onglet **Databases** (menu principal).
3. Section **MySQL** → saisir un mot de passe MySQL fort → cliquer **Initialize MySQL**.
4. Dans le champ **Create a database**, saisir : `gescom_bf` → **Create**.

> PythonAnywhere nomme automatiquement la base `<username>$gescom_bf`.  
> Le nom complet visible dans l'onglet est par exemple `mannu$gescom_bf`.

### 2.2 Relever les informations de connexion

Dans l'onglet **Databases**, noter :

| Paramètre | Valeur |
|---|---|
| Host | `<username>.mysql.pythonanywhere-services.com` |
| Username | `<username>` (votre login PythonAnywhere) |
| Password | Le mot de passe MySQL défini à l'étape 2.1 |
| Database | `<username>$gescom_bf` |
| Port | `3306` |

### 2.3 Tester la connexion (optionnel)

Dans un **Bash console** :

```bash
mysql -u <username> -h <username>.mysql.pythonanywhere-services.com -p
# Saisir le mot de passe MySQL
mysql> SHOW DATABASES;
# Doit lister : <username>$gescom_bf
mysql> EXIT;
```

---

## 3. Environnement Python

### 3.1 Ouvrir une console Bash

Onglet **Consoles** → **New console** → **Bash**.

### 3.2 Cloner le dépôt

```bash
cd ~
git clone https://github.com/<organisation>/gescom-bf.git gescom-bf
# Ou avec SSH si vos clés sont configurées :
# git clone git@github.com:<organisation>/gescom-bf.git gescom-bf
```

### 3.3 Créer un environnement virtuel Python 3.12

```bash
cd ~/gescom-bf/backend
python3.12 -m venv .venv
source .venv/bin/activate
python --version   # doit afficher Python 3.12.x
```

> PythonAnywhere met à disposition Python 3.12 par défaut sur les plans récents.  
> Si `python3.12` n'est pas trouvé : `ls /usr/bin/python3*` pour vérifier les versions disponibles.

---

## 4. Dépendances

```bash
# Toujours dans le venv activé
pip install --upgrade pip
pip install -r requirements.txt
```

Le fichier `requirements.txt` inclut :
- `PyMySQL==1.1.1` — driver MySQL pur Python (pas de compilation système requise)
- `Flask`, `Flask-SQLAlchemy`, `Flask-Migrate`, `Flask-JWT-Extended`, `Marshmallow`
- `scikit-learn`, `Prophet`, `XGBoost` (ML — installés mais non requis au boot)

> **Note :** `psycopg2-binary` (driver PostgreSQL) est également présent dans `requirements.txt` pour la compatibilité dev — il s'installe sans erreur sur PythonAnywhere (version pre-compilée) mais n'est jamais utilisé si `DATABASE_URL` pointe vers MySQL.

---

## 5. Variables d'environnement

### 5.1 Créer le fichier `.env`

```bash
cd ~/gescom-bf/backend
cp .env.pythonanywhere.example .env
nano .env    # ou vim .env
```

### 5.2 Contenu minimal à configurer

```bash
# ============================================================
# GesCom-BF — Configuration PythonAnywhere (MySQL, mono-tenant)
# ============================================================

# ---- Base de données MySQL ----
# Format : mysql+pymysql://<user>:<password>@<user>.mysql.pythonanywhere-services.com/<user>$<base>?charset=utf8mb4
DATABASE_URL=mysql+pymysql://<username>:<mysql_password>@<username>.mysql.pythonanywhere-services.com/<username>$gescom_bf?charset=utf8mb4

# ---- Flask ----
FLASK_APP=wsgi.py
FLASK_ENV=production
SECRET_KEY=<générer avec : python3 -c "import secrets; print(secrets.token_hex(32))">

# ---- JWT ----
# token_hex(32) = 64 caractères hex = 256 bits (minimum requis : 32 octets / 64 car. hex)
# Une clé < 32 octets déclenche un InsecureKeyLengthWarning au démarrage.
JWT_SECRET_KEY=<générer avec : python3 -c "import secrets; print(secrets.token_hex(32))">
JWT_ACCESS_TOKEN_EXPIRES_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRES_DAYS=7

# ---- CORS : remplacer par votre domaine PythonAnywhere ----
CORS_ORIGINS=https://<username>.pythonanywhere.com

# ---- Frontend servi par Flask (après npm run build) ----
SERVE_FRONTEND_DIST=/home/<username>/gescom-bf/frontend/dist

# ---- Compte admin initial (seed) ----
SEED_ADMIN_EMAIL=admin@votre-quincaillerie.bf
SEED_ADMIN_PASSWORD=<mot_de_passe_fort_16_car_min>

# ---- Documents (PDF, exports) ----
COMPANY_NAME=Votre Quincaillerie
COMPANY_ADDRESS=Ouagadougou, Burkina Faso
COMPANY_PHONE=+226 XX XX XX XX

# ---- Multi-tenant (laisser tel quel) ----
DEFAULT_TENANT_SCHEMA=public

# ---- ML / ETL ----
ML_ARTIFACT_DIR=/home/<username>/gescom-bf/backend/instance/ml_artifacts
MLFLOW_TRACKING_URI=file:/home/<username>/gescom-bf/backend/mlruns
MLFLOW_EXPERIMENT_NAME=gescom-bf

# ---- Connection pool (MySQL PythonAnywhere) ----
# 280s < wait_timeout MySQL (évite "MySQL server has gone away")
SQLALCHEMY_POOL_RECYCLE=280
```

**Générer les clés secrètes :**

```bash
# SECRET_KEY (Flask sessions)
python3 -c "import secrets; print(secrets.token_urlsafe(48))"

# JWT_SECRET_KEY — 256 bits (64 caractères hex) — exécuter séparément
python3 -c "import secrets; print(secrets.token_hex(32))"
```

> `token_hex(32)` produit 64 caractères hexadécimaux = 256 bits. Flask-JWT-Extended émet un `InsecureKeyLengthWarning` si la clé fait moins de 32 octets — ce qui se produirait avec `token_hex(16)` (32 car. = 128 bits = 16 octets, limite basse) ou des valeurs par défaut de développement.

### 5.3 Sécuriser le fichier `.env`

```bash
chmod 600 ~/gescom-bf/backend/.env
```

---

## 6. Migrations et seed

### 6.1 Appliquer les migrations Alembic

```bash
cd ~/gescom-bf/backend
source .venv/bin/activate
export FLASK_APP=wsgi.py

flask db upgrade
```

Résultat attendu : création des 32 tables en DDL MySQL pur (pas de `CREATE SCHEMA`, pas de `uuid-ossp`). Exemple de sortie :

```
INFO  [alembic.runtime.migration] Running upgrade  -> 1a2b3c4d5e6f, initial schema
INFO  [alembic.runtime.migration] Running upgrade 1a2b3c4d5e6f -> 2b3c4d5e6f7a, roles and permissions
...
INFO  [alembic.runtime.migration] Running upgrade ... -> latest, feature store fs_*
```

**Vérification :**

```bash
mysql -u <username> -h <username>.mysql.pythonanywhere-services.com -p<mysql_password> <username>\$gescom_bf \
  -e "SHOW TABLES;" | wc -l
# Doit afficher 33 (32 tables + 1 ligne d'en-tête)
```

### 6.2 Initialiser les données de base (seed)

```bash
python -m app.seed
```

Crée :
- Les rôles : `ADMIN`, `MAGASINIER`, `VENDEUR`
- Les permissions RBAC
- Le site par défaut (dépôt central)
- Le compte administrateur (`SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD`)

### 6.3 (Optionnel) Seed de démonstration

```bash
python -m app.seed_demo
```

Ajoute un catalogue de produits de quincaillerie, des clients, des fournisseurs, et 6 mois d'historique de ventes — utile pour les démonstrations.

---

## 7. Configuration WSGI

### 7.1 Créer l'application web

1. Onglet **Web** → **Add a new web app**.
2. Choisir **Manual configuration** (PAS "Flask" — pour avoir le contrôle du chemin).
3. Python version : **3.12**.

### 7.2 Configurer le fichier WSGI

Dans l'onglet **Web**, cliquer sur le lien du **WSGI configuration file** (ex. `/var/www/<username>_pythonanywhere_com_wsgi.py`).

Remplacer intégralement son contenu par :

```python
"""
Fichier WSGI — GesCom-BF sur PythonAnywhere (MySQL, mono-tenant).

PythonAnywhere charge ce fichier pour servir l'application Flask via uWSGI.
Le fichier .env est chargé automatiquement par load_dotenv() dans config.py.
"""
import sys
import os

# Ajouter le répertoire backend au PYTHONPATH
project_home = "/home/<username>/gescom-bf/backend"
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Activer l'environnement virtuel
activate_env = f"{project_home}/.venv/bin/activate_this.py"
with open(activate_env) as f:
    exec(f.read(), {"__file__": activate_env})

# Charger l'application Flask
os.environ.setdefault("FLASK_ENV", "production")

from app import create_app  # noqa: E402

application = create_app("production")
```

> Remplacer `<username>` par votre login PythonAnywhere dans les deux chemins.

### 7.3 Configurer le répertoire virtuel

Dans l'onglet **Web** → section **Virtualenv** :

```
/home/<username>/gescom-bf/backend/.venv
```

### 7.4 Configurer les fichiers statiques

Dans l'onglet **Web** → section **Static files** :

| URL | Directory |
|---|---|
| `/static/` | `/home/<username>/gescom-bf/backend/app/static/` |

> Le frontend (React/Vite) est servi par Flask directement via `SERVE_FRONTEND_DIST` — pas besoin d'une entrée statique séparée pour les assets React.

### 7.5 Recharger l'application

Cliquer le bouton vert **Reload** dans l'onglet Web.

Tester : `https://<username>.pythonanywhere.com/health` doit retourner `{"status": "ok"}`.

---

## 8. Frontend React

### 8.1 Installer Node.js (si nécessaire)

PythonAnywhere fournit Node.js en console Bash :

```bash
node --version   # vérifier la version disponible
npm --version
```

### 8.2 Construire le frontend

```bash
cd ~/gescom-bf/frontend
npm install
npm run build
```

Le build est généré dans `frontend/dist/`. Flask le sert automatiquement grâce à `SERVE_FRONTEND_DIST=/home/<username>/gescom-bf/frontend/dist` dans `.env`.

### 8.3 Vérifier que le frontend est servi

```
GET https://<username>.pythonanywhere.com/
→ Doit retourner la page d'accueil React (formulaire de connexion)
```

---

## 9. Tâches planifiées (Scheduled Tasks)

Sur PythonAnywhere, les tâches Celery Beat sont remplacées par des **Scheduled Tasks** (onglet **Tasks**). Chaque tâche exécute une commande CLI Flask.

### 9.1 Script d'activation du venv

Créer un script helper pour toutes les tâches :

```bash
cat > ~/gescom-bf/run_task.sh << 'EOF'
#!/bin/bash
# Helper : active le venv et exécute une commande Flask
cd /home/<username>/gescom-bf/backend
source .venv/bin/activate
export FLASK_APP=wsgi.py
python -m flask "$@"
EOF
chmod +x ~/gescom-bf/run_task.sh
```

### 9.2 Configurer les tâches dans l'onglet Tasks

Onglet **Tasks** → **Add a new scheduled task** :

| Heure (UTC) | Fréquence | Commande |
|---|---|---|
| 02:00 | Daily | `/home/<username>/gescom-bf/run_task.sh etl-daily` |
| 03:00 | Daily | `/home/<username>/gescom-bf/run_task.sh ml-train-all` |
| 03:30 | Daily | `/home/<username>/gescom-bf/run_task.sh db-backup` |
| 04:00 | Daily | `/home/<username>/gescom-bf/run_task.sh anomaly-detect` |

> L'heure est en **UTC**. Burkina Faso = UTC+0 (pas de changement d'heure), donc UTC = heure locale.

### 9.3 (Optionnel) Always-on task pour le dashboard SSE

Si le plan Developer inclut 1 always-on task et que vous souhaitez garder les connexions SSE actives :

```bash
# Toujours-actif (Always-on task) — optionnel
/home/<username>/gescom-bf/run_task.sh run --host=0.0.0.0 --port=5001
```

> Cela n'est généralement pas nécessaire : uWSGI gère les requêtes SSE directement.

---

## 10. Vérification et tests de fumée

Exécuter depuis une console Bash ou via `curl` :

```bash
BASE="https://<username>.pythonanywhere.com/api/v1"

# 1. Health check
curl "$BASE/../health"
# → {"status": "ok"}

# 2. Login admin
TOKEN=$(curl -s -X POST "$BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@votre-quincaillerie.bf","password":"<mot_de_passe>"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "Token: $TOKEN"

# 3. Produits
curl -H "Authorization: Bearer $TOKEN" "$BASE/products?page=1&per_page=5"

# 4. Stock
curl -H "Authorization: Bearer $TOKEN" "$BASE/stock"

# 5. Dashboard
curl -H "Authorization: Bearer $TOKEN" "$BASE/reports/dashboard"
```

Résultats attendus : codes HTTP 200 pour tous les appels, données JSON cohérentes.

---

## 11. Mises à jour (déploiement continu)

Procédure standard pour déployer une nouvelle version :

```bash
# 1. Récupérer le code
cd ~/gescom-bf
git pull origin main

# 2. Mettre à jour les dépendances (si requirements.txt a changé)
cd backend
source .venv/bin/activate
pip install -r requirements.txt

# 3. Appliquer les nouvelles migrations
flask db upgrade

# 4. Rebuilder le frontend (si le code frontend a changé)
cd ../frontend
npm install
npm run build

# 5. Recharger l'application web
# Via l'onglet Web → bouton "Reload"
# Ou via l'API PythonAnywhere :
curl -X POST https://www.pythonanywhere.com/api/v0/user/<username>/webapps/<username>.pythonanywhere.com/reload/ \
  -H "Authorization: Token <api_token>"
```

> Générer un token API : **Account** → **API token** → **Create a new API token**.

---

## 12. Sauvegarde MySQL

### 12.1 Sauvegarde manuelle

```bash
cd ~
mysqldump -u <username> -h <username>.mysql.pythonanywhere-services.com -p<mysql_password> \
  <username>\$gescom_bf > backup_gescom_$(date +%Y%m%d).sql

# Compresser
gzip backup_gescom_$(date +%Y%m%d).sql
```

### 12.2 Sauvegarde automatique via Scheduled Task

La commande CLI `flask db-backup` (dans `backend/app/cli.py`) exécute mysqldump et stocke le fichier dans `instance/backups/`.

Tâche planifiée déjà configurée en §9.2 (`03:30 Daily`).

### 12.3 Sauvegarde PythonAnywhere (Files)

PythonAnywhere propose une fonctionnalité de backup des fichiers de votre home dans les paramètres **Account** → **Files**. Activer cette option pour une protection supplémentaire.

---

## 13. Dépannage (Troubleshooting)

### 13.1 Consulter les logs d'erreur

Dans l'onglet **Web** → section **Log files** :

- **Error log** : erreurs Python / Flask (traceback complet)
- **Access log** : toutes les requêtes HTTP reçues
- **Server log** : logs uWSGI (démarrage, rechargement)

```bash
# En console Bash, pour suivre en temps réel :
tail -f /var/log/<username>.pythonanywhere.com.error.log
```

### 13.2 Erreurs fréquentes

| Erreur | Cause probable | Solution |
|---|---|---|
| `ModuleNotFoundError: No module named 'app'` | `project_home` mal configuré dans le fichier WSGI | Vérifier le chemin dans `wsgi.py` (`/home/<username>/gescom-bf/backend`) |
| `OperationalError: (2003) Can't connect to MySQL server` | `DATABASE_URL` incorrect | Vérifier host, username, mot de passe et nom de base dans `.env` |
| `MySQL server has gone away` | Connexion idle expirée | Vérifier que `SQLALCHEMY_POOL_RECYCLE=280` est bien dans `.env` |
| `(1045) Access denied for user` | Mot de passe MySQL incorrect | Réinitialiser depuis l'onglet Databases |
| `(1049) Unknown database` | Base non créée | Créer la base dans l'onglet Databases avant `flask db upgrade` |
| `500 Internal Server Error` sur toutes les routes | Erreur au boot Flask | Consulter l'error log ; souvent un `.env` manquant ou une variable mal formatée |
| `CORS error` côté navigateur | `CORS_ORIGINS` ne correspond pas au domaine | Mettre `https://<username>.pythonanywhere.com` sans slash final |
| `flask: command not found` | Venv non activé | `source ~/gescom-bf/backend/.venv/bin/activate` puis `python -m flask ...` |
| Frontend affiche une page blanche | `SERVE_FRONTEND_DIST` incorrect ou `npm run build` non exécuté | Vérifier que `frontend/dist/index.html` existe |
| `CHECK constraint` ignorée | MySQL < 8.0.16 | Les validations sont assurées au niveau applicatif — pas de risque de corruption |

### 13.3 Tester la connexion MySQL depuis Python

```bash
cd ~/gescom-bf/backend
source .venv/bin/activate
python3 - << 'EOF'
import pymysql, os
from dotenv import load_dotenv
load_dotenv()
url = os.environ["DATABASE_URL"]
# Extraire les paramètres
import re
m = re.match(r"mysql\+pymysql://([^:]+):([^@]+)@([^/]+)/(.+)\?", url)
user, pwd, host, db = m.groups()
conn = pymysql.connect(host=host, user=user, password=pwd, database=db)
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE()")
print(f"Tables dans la base : {cursor.fetchone()[0]}")
conn.close()
print("Connexion MySQL OK")
EOF
```

### 13.4 Recréer l'environnement virtuel

En cas de corruption du venv :

```bash
cd ~/gescom-bf/backend
rm -rf .venv
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 13.5 Réinitialiser la base de données

> ⚠️ Destructif — supprime toutes les données.

```bash
# Supprimer toutes les tables
mysql -u <username> -h <username>.mysql.pythonanywhere-services.com -p<password> \
  -e "DROP DATABASE \`<username>\$gescom_bf\`; CREATE DA