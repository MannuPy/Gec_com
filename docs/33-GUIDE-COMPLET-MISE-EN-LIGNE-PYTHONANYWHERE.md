# 33. Guide complet de mise en ligne sur PythonAnywhere
## De la création de compte à l'envoi du lien à vos amis

> **Niveau :** débutant à intermédiaire  
> **Durée estimée :** 2 à 3 heures (première fois)  
> **Ce guide suppose :** que le code du projet GesCom-BF est sur GitHub (ou GitLab)

---

## Table des matières

- [ÉTAPE 0 — Préparer le dépôt GitHub](#étape-0--préparer-le-dépôt-github)
- [ÉTAPE 1 — Créer un compte PythonAnywhere](#étape-1--créer-un-compte-pythonanywhere)
- [ÉTAPE 2 — Passer au plan Developer (MySQL requis)](#étape-2--passer-au-plan-developer)
- [ÉTAPE 3 — Créer la base de données MySQL](#étape-3--créer-la-base-de-données-mysql)
- [ÉTAPE 4 — Ouvrir une console Bash](#étape-4--ouvrir-une-console-bash)
- [ÉTAPE 5 — Cloner le projet depuis GitHub](#étape-5--cloner-le-projet-depuis-github)
- [ÉTAPE 6 — Créer l'environnement Python virtuel](#étape-6--créer-lenvironnement-python-virtuel)
- [ÉTAPE 7 — Installer les dépendances](#étape-7--installer-les-dépendances)
- [ÉTAPE 8 — Configurer les variables d'environnement (.env)](#étape-8--configurer-les-variables-denvironnement)
- [ÉTAPE 9 — Appliquer les migrations (créer les tables)](#étape-9--appliquer-les-migrations)
- [ÉTAPE 10 — Initialiser les données de base (seed)](#étape-10--initialiser-les-données-de-base)
- [ÉTAPE 11 — Construire le frontend React](#étape-11--construire-le-frontend-react)
- [ÉTAPE 12 — Créer l'application web (WSGI)](#étape-12--créer-lapplication-web-wsgi)
- [ÉTAPE 13 — Configurer le fichier WSGI](#étape-13--configurer-le-fichier-wsgi)
- [ÉTAPE 14 — Configurer le virtualenv dans l'onglet Web](#étape-14--configurer-le-virtualenv)
- [ÉTAPE 15 — Recharger et tester](#étape-15--recharger-et-tester)
- [ÉTAPE 16 — Partager le lien avec vos amis](#étape-16--partager-le-lien)
- [ÉTAPE 17 — Planifier les tâches automatiques](#étape-17--planifier-les-tâches-automatiques)
- [ANNEXE A — Dépannage rapide](#annexe-a--dépannage-rapide)
- [ANNEXE B — Mettre à jour le site après modification du code](#annexe-b--mettre-à-jour-le-site)

---

## ÉTAPE 0 — Préparer le dépôt GitHub

Avant de toucher à PythonAnywhere, assurez-vous que votre code est **sur GitHub** (ou GitLab).

### 0.1 Vérifier que le projet est bien sur GitHub

Allez sur [https://github.com](https://github.com) et vérifiez que votre dépôt `gescom-bf` existe et contient les dossiers `backend/` et `frontend/`.

### 0.2 Copier l'URL du dépôt

Sur la page de votre dépôt GitHub :
1. Cliquer le bouton vert **`< > Code`**
2. Choisir l'onglet **HTTPS**
3. Copier l'URL — elle ressemble à : `https://github.com/votre-nom/gescom-bf.git`

> Gardez cette URL sous la main — vous en aurez besoin à l'étape 5.

---

## ÉTAPE 1 — Créer un compte PythonAnywhere

### 1.1 Aller sur le site

Ouvrez votre navigateur et allez sur : **[https://www.pythonanywhere.com](https://www.pythonanywhere.com)**

### 1.2 Créer un compte

1. Cliquer sur **"Pricing & signup"** dans le menu en haut
2. Cliquer sur **"Create a Beginner account"** (gratuit, pour commencer)  
   *(Vous passerez au plan payant à l'étape 2)*
3. Remplir le formulaire :
   - **Username** : choisissez un nom simple, sans espace, en minuscules (ex. `gescombf` ou `mannu`). **Ce nom deviendra une partie de votre URL** : `https://mannu.pythonanywhere.com`
   - **Email** : votre adresse email
   - **Password** : un mot de passe fort
4. Cocher la case d'acceptation des conditions
5. Cliquer **"Register"**
6. Vérifier votre email et cliquer le lien de confirmation

> **Important :** le nom d'utilisateur est permanent. Choisissez quelque chose de professionnel.

### 1.3 Se connecter

Après confirmation, connectez-vous sur [https://www.pythonanywhere.com/login](https://www.pythonanywhere.com/login).

Vous arrivez sur le **Dashboard** (tableau de bord) de PythonAnywhere.

---

## ÉTAPE 2 — Passer au plan Developer

Le plan gratuit ne permet pas d'utiliser MySQL. Vous devez passer au plan **Developer (10 $/mois)**.

### 2.1 Accéder à la page de compte

1. En haut à droite, cliquer sur votre **nom d'utilisateur**
2. Cliquer **"Account"** dans le menu déroulant

### 2.2 Changer de plan

1. Onglet **"Account type"** (ou "Plan")
2. Cliquer **"Upgrade"** en face du plan **Developer** (10 $/mois)
3. Renseigner les informations de paiement (carte bancaire)
4. Confirmer l'abonnement

> **Ce que vous obtenez avec Developer :**
> - MySQL managé inclus
> - 1 application web active (votre URL `<username>.pythonanywhere.com`)
> - 3 consoles simultanées
> - SSH activé
> - 20 tâches planifiées
> - 5 Go de stockage
> - 5000 secondes CPU/jour

---

## ÉTAPE 3 — Créer la base de données MySQL

### 3.1 Aller dans l'onglet Databases

Dans le menu en haut du Dashboard de PythonAnywhere, cliquer sur **"Databases"**.

### 3.2 Initialiser MySQL

Sur la page Databases, vous voyez une section **MySQL** :

1. Dans le champ **"MySQL password"**, tapez un mot de passe fort pour MySQL  
   *(Ce mot de passe est **différent** de votre mot de passe PythonAnywhere)*  
   Exemple : `GesComMySQL2026!`
2. Cliquer **"Initialize MySQL"**
3. Attendre quelques secondes — PythonAnywhere crée votre serveur MySQL personnel

### 3.3 Créer la base de données

Après initialisation, vous voyez :
- Un champ **"Create a database"**
- Le texte `<username>$` déjà pré-rempli à gauche

1. Dans le champ, taper : `gescom_bf`
2. Cliquer **"Create"**

PythonAnywhere crée la base `<username>$gescom_bf`.

### 3.4 Noter vos informations de connexion

Sur la page Databases, repérez et **notez précieusement** :

```
Hôte MySQL     : <username>.mysql.pythonanywhere-services.com
Utilisateur    : <username>
Mot de passe   : [celui que vous avez défini à l'étape 3.2]
Base de données: <username>$gescom_bf
```

> Exemple concret si votre username est `mannu` :
> ```
> Hôte      : mannu.mysql.pythonanywhere-services.com
> Utilisateur: mannu
> Base      : mannu$gescom_bf
> ```

---

## ÉTAPE 4 — Ouvrir une console Bash

Toutes les commandes du projet se tapent dans une console **Bash** sur PythonAnywhere.

### 4.1 Ouvrir une console

1. Cliquer sur **"Consoles"** dans le menu du haut
2. Dans la section **"Start a new console"**, cliquer sur **"Bash"**

Une console Linux s'ouvre dans votre navigateur. Vous voyez quelque chose comme :

```
15:32 ~ $
```

> Toutes les commandes qui suivent dans ce guide sont à taper dans **cette console Bash**.

---

## ÉTAPE 5 — Cloner le projet depuis GitHub

Dans la console Bash :

```bash
cd ~
git clone https://github.com/votre-nom/gescom-bf.git gescom-bf
```

> Remplacer `https://github.com/votre-nom/gescom-bf.git` par l'URL copiée à l'étape 0.2.

Résultat attendu :
```
Cloning into 'gescom-bf'...
remote: Enumerating objects: 1247, done.
remote: Counting objects: 100% (1247/1247), done.
...
Resolving deltas: 100% (423/423), done.
```

### 5.1 Vérifier que le clonage a réussi

```bash
ls ~/gescom-bf
```

Vous devez voir : `backend/  frontend/  docs/  docker-compose.yml  .env.example  README.md`

---

## ÉTAPE 6 — Créer l'environnement Python virtuel

Python a besoin d'un environnement isolé pour les dépendances du projet.

```bash
cd ~/gescom-bf/backend
python3.12 -m venv .venv
```

> Si vous obtenez `python3.12: command not found`, essayez `python3.10` ou `python3.11` (selon ce que PythonAnywhere propose).

### 6.1 Activer le virtualenv

```bash
source .venv/bin/activate
```

Votre prompt change et affiche maintenant `(.venv)` au début :
```
(.venv) 15:35 ~/gescom-bf/backend $
```

> **Important :** à chaque fois que vous ouvrez une **nouvelle** console Bash et que vous voulez lancer des commandes Flask, vous devez relancer `source .venv/bin/activate`.

### 6.2 Vérifier la version de Python

```bash
python --version
```

Doit afficher `Python 3.12.x` (ou la version choisie).

---

## ÉTAPE 7 — Installer les dépendances

```bash
# Toujours dans ~/gescom-bf/backend, avec (.venv) actif
pip install --upgrade pip
pip install -r requirements.txt
```

Cette commande installe Flask, SQLAlchemy, PyMySQL, JWT, Marshmallow, scikit-learn, etc.

Durée : environ **3 à 5 minutes** (les bibliothèques ML prennent du temps).

Résultat final attendu :
```
Successfully installed Flask-3.x.x SQLAlchemy-2.x.x PyMySQL-1.1.1 ...
```

### 7.1 Vérifier l'installation

```bash
python -c "import pymysql; print('PyMySQL OK')"
python -c "import flask; print('Flask OK')"
```

Les deux doivent afficher `... OK`.

---

## ÉTAPE 8 — Configurer les variables d'environnement

Le fichier `.env` contient tous les paramètres secrets du projet (mot de passe DB, clés JWT, etc.).

### 8.1 Créer le fichier .env à partir du modèle

```bash
cd ~/gescom-bf/backend
cp .env.pythonanywhere.example .env
```

### 8.2 Ouvrir le fichier pour l'éditer

```bash
nano .env
```

L'éditeur `nano` s'ouvre dans la console. Utilisez les **touches fléchées** pour naviguer.

### 8.3 Remplir chaque valeur — ligne par ligne

**a) DATABASE_URL** — la connexion MySQL (la plus importante)

Trouvez la ligne :
```
DATABASE_URL=mysql+pymysql://<utilisateur>:CHANGE_ME@<utilisateur>.mysql.pythonanywhere-services.com/<utilisateur>$gescom_bf?charset=utf8mb4
```

Remplacez **les 3 occurrences de `<utilisateur>`** par votre username PythonAnywhere, et `CHANGE_ME` par votre mot de passe MySQL de l'étape 3.2.

Exemple final (si username = `mannu`, mot de passe MySQL = `GesComMySQL2026!`) :
```
DATABASE_URL=mysql+pymysql://mannu:GesComMySQL2026!@mannu.mysql.pythonanywhere-services.com/mannu$gescom_bf?charset=utf8mb4
```

**b) SECRET_KEY** — clé secrète Flask

Ouvrez un **deuxième onglet** dans la console (ou notez de côté) et générez une clé :

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copiez la valeur (ex. `a3f1c9d7e2b4...`) et collez-la dans le `.env` :
```
SECRET_KEY=a3f1c9d7e2b4...
```

**c) JWT_SECRET_KEY** — clé secrète JWT (différente de SECRET_KEY)

Regénérer une autre valeur :
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

```
JWT_SECRET_KEY=f8b2e6a1d4c9...   (valeur différente de SECRET_KEY)
```

**d) CORS_ORIGINS** — domaine autorisé

```
CORS_ORIGINS=https://mannu.pythonanywhere.com
```
*(Remplacer `mannu` par votre username)*

**e) SERVE_FRONTEND_DIST** — chemin du build React

```
SERVE_FRONTEND_DIST=/home/mannu/gescom-bf/frontend/dist
```
*(Remplacer `mannu` par votre username)*

**f) SEED_ADMIN_EMAIL / SEED_ADMIN_PASSWORD** — compte administrateur

```
SEED_ADMIN_EMAIL=admin@votre-quincaillerie.bf
SEED_ADMIN_PASSWORD=MonMotDePasseAdmin2026!
```

> Ce sont les identifiants que vous utiliserez pour vous connecter à GesCom-BF. Notez-les bien.

**g) COMPANY_NAME / COMPANY_ADDRESS / COMPANY_PHONE** — informations de votre entreprise

```
COMPANY_NAME=Quincaillerie Mannu
COMPANY_ADDRESS=Ouagadougou, Secteur 22, Burkina Faso
COMPANY_PHONE=+226 70 00 00 00
```

**h) ML_ARTIFACT_DIR / MLFLOW_TRACKING_URI** — dossiers ML

```
ML_ARTIFACT_DIR=/home/mannu/gescom-bf/backend/instance/ml_artifacts
MLFLOW_TRACKING_URI=file:/home/mannu/gescom-bf/backend/mlruns
```

### 8.4 Sauvegarder et quitter nano

1. Appuyer sur **Ctrl + X** (quitter)
2. Appuyer sur **Y** (oui, sauvegarder)
3. Appuyer sur **Entrée** (confirmer le nom de fichier)

### 8.5 Sécuriser le fichier

```bash
chmod 600 ~/gescom-bf/backend/.env
```

Cela empêche d'autres utilisateurs système de lire votre mot de passe.

### 8.6 Vérifier le contenu (optionnel)

```bash
grep "DATABASE_URL\|SECRET_KEY\|COMPANY_NAME\|SERVE_FRONTEND" ~/gescom-bf/backend/.env
```

Vérifiez visuellement que les valeurs sont correctes (pas de `<utilisateur>` ni de `CHANGE_ME` restants).

---

## ÉTAPE 9 — Appliquer les migrations (créer les tables)

Cette étape crée toutes les tables dans votre base MySQL.

```bash
cd ~/gescom-bf/backend
source .venv/bin/activate   # si pas déjà activé
export FLASK_APP=wsgi.py
flask db upgrade
```

Vous devez voir une longue liste de migrations s'exécuter :
```
INFO  [alembic.runtime.migration] Running upgrade  -> 1a2b3c4d5e6f, initial schema
INFO  [alembic.runtime.migration] Running upgrade 1a2b3c4d5e6f -> 2b3c4d..., roles and permissions
INFO  [alembic.runtime.migration] Running upgrade ...
...
INFO  [alembic.runtime.migration] Running upgrade ... -> latest revision
```

### 9.1 Vérifier que les tables ont été créées

```bash
python3 -c "
import pymysql, os
from dotenv import load_dotenv
load_dotenv()
import re
url = os.environ['DATABASE_URL']
m = re.match(r'mysql\+pymysql://([^:]+):([^@]+)@([^/]+)/(.+)\?', url)
user, pwd, host, db = m.groups()
conn = pymysql.connect(host=host, user=user, password=pwd, database=db)
cur = conn.cursor()
cur.execute('SHOW TABLES')
tables = cur.fetchall()
print(f'Nombre de tables créées : {len(tables)}')
for t in tables: print(' -', t[0])
conn.close()
"
```

Vous devez voir **32 tables** listées (branches, users, products, sales, stock, etc.).

---

## ÉTAPE 10 — Initialiser les données de base

Cette étape crée les rôles, permissions, et le premier compte administrateur.

```bash
cd ~/gescom-bf/backend
source .venv/bin/activate
export FLASK_APP=wsgi.py
python -m app.seed
```

Résultat attendu :
```
[seed] Création des rôles et permissions...
[seed] Création des sites par défaut...
[seed] Compte admin créé : admin@votre-quincaillerie.bf
[seed] Terminé.
```

### 10.1 (Optionnel) Ajouter des données de démonstration

Si vous voulez montrer le site avec des données réalistes (produits, ventes, stock) :

```bash
python -m app.seed_demo
```

Cela ajoute un catalogue complet de quincaillerie, des clients, des fournisseurs, et 6 mois d'historique de ventes.

---

## ÉTAPE 11 — Construire le frontend React

> ⚠️ **PythonAnywhere ne fournit pas Node.js par défaut.**  
> Cette étape nécessite d'abord d'installer Node.js via `nvm`, ou de builder en local puis d'uploader.  
> **Guide dédié : [`docs/34-SOLUTION-NODEJS-PYTHONANYWHERE.md`](34-SOLUTION-NODEJS-PYTHONANYWHERE.md)**

### 11.A — Solution rapide : nvm sur PythonAnywhere (à essayer en premier)

Dans la console **Bash PythonAnywhere** :

```bash
# 1. Installer nvm (gestionnaire Node.js, ne nécessite pas les droits admin)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# 2. Recharger le shell
source ~/.bashrc

# 3. Installer Node.js LTS
nvm install --lts

# 4. Vérifier
node --version   # → v20.x.x
npm --version    # → 10.x.x

# 5. Builder le frontend
cd ~/gescom-bf/frontend
npm install
npm run build
```

### 11.B — Si nvm ne fonctionne pas : build en local + upload SSH

Sur **votre ordinateur** (terminal local, pas PythonAnywhere) :

```bash
# Prérequis : Node.js installé sur votre ordinateur (https://nodejs.org)
cd votre-dossier/gescom-bf

# Build + upload en une commande (script fourni dans le projet)
chmod +x scripts/deploy-frontend-ssh.sh
./scripts/deploy-frontend-ssh.sh mannu   # remplacer mannu par votre username
```

Le script build le frontend et copie automatiquement les fichiers sur PythonAnywhere via SSH.

**Alternative manuelle :**

```bash
cd frontend
npm install && npm run build
scp -r dist/ mannu@ssh.pythonanywhere.com:/home/mannu/gescom-bf/frontend/
```

### 11.C — Solution automatique : GitHub Actions (pour la suite)

Le fichier `.github/workflows/deploy-pythonanywhere.yml` inclus dans le projet automatise le build et le déploiement à chaque `git push`. Voir `docs/34-SOLUTION-NODEJS-PYTHONANYWHERE.md §Solution C`.

### 11.D — Vérifier que le build existe (quelle que soit la solution choisie)

Dans la console **Bash PythonAnywhere** :

```bash
ls ~/gescom-bf/frontend/dist/
```

Vous devez voir : `index.html  assets/`

Si ce fichier existe → **continuer à l'étape 12.**

---

## ÉTAPE 12 — Créer l'application web (WSGI)

### 12.1 Aller dans l'onglet Web

Dans le menu du haut de PythonAnywhere, cliquer sur **"Web"**.

### 12.2 Ajouter une nouvelle application

1. Cliquer le bouton bleu **"Add a new web app"**
2. Cliquer **"Next"** (votre domaine `<username>.pythonanywhere.com` est déjà sélectionné)
3. Sur l'écran "Select a Python Web framework" : choisir **"Manual configuration"** *(pas "Flask" — ce mode nous donne plus de contrôle)*
4. Sur l'écran "Select a Python version" : choisir **"Python 3.12"**
5. Cliquer **"Next"**

Vous arrivez sur la page de configuration de votre application web.

---

## ÉTAPE 13 — Configurer le fichier WSGI

Le fichier WSGI est le point d'entrée que PythonAnywhere utilise pour démarrer Flask.

### 13.1 Ouvrir le fichier WSGI

Sur la page **Web**, repérez la section **"Code"**. Vous voyez :

```
WSGI configuration file: /var/www/<username>_pythonanywhere_com_wsgi.py
```

Cliquer sur ce lien (c'est un lien cliquable).

Un éditeur de texte s'ouvre dans le navigateur, avec du contenu par défaut.

### 13.2 Effacer tout le contenu

Sélectionner tout le texte (Ctrl+A) et le supprimer.

### 13.3 Coller le contenu correct

Coller exactement ce texte (en remplaçant `mannu` par votre username) :

```python
"""
Fichier WSGI — GesCom-BF sur PythonAnywhere.
PythonAnywhere charge ce fichier pour démarrer l'application Flask via uWSGI.
"""
import sys
import os

# ------------------------------------------------------------------
# 1. Ajouter le répertoire backend au PYTHONPATH
# ------------------------------------------------------------------
project_home = "/home/mannu/gescom-bf/backend"   # <-- REMPLACER mannu
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# ------------------------------------------------------------------
# 2. Activer l'environnement virtuel Python
# ------------------------------------------------------------------
activate_env = os.path.join(project_home, ".venv", "bin", "activate_this.py")
with open(activate_env) as f:
    exec(f.read(), {"__file__": activate_env})

# ------------------------------------------------------------------
# 3. Définir l'environnement de production
# ------------------------------------------------------------------
os.environ.setdefault("FLASK_ENV", "production")

# ------------------------------------------------------------------
# 4. Importer et exposer l'application Flask
# ------------------------------------------------------------------
from app import create_app   # noqa: E402

application = create_app("production")
```

### 13.4 Sauvegarder

Cliquer le bouton **"Save"** en haut à droite de l'éditeur.

---

## ÉTAPE 14 — Configurer le virtualenv

Retourner sur la page **Web** (cliquer l'onglet Web dans le menu).

### 14.1 Configurer le chemin du virtualenv

Dans la section **"Virtualenv"** :

1. Cliquer dans le champ vide (ou cliquer "Enter path to a virtualenv")
2. Taper : `/home/mannu/gescom-bf/backend/.venv`  
   *(Remplacer `mannu` par votre username)*
3. Cliquer **"OK"** ou appuyer sur **Entrée**

PythonAnywhere va afficher la version Python de ce virtualenv.

### 14.2 Configurer les fichiers statiques (optionnel mais recommandé)

Dans la section **"Static files"**, cliquer **"Enter URL"** :

| URL | Directory |
|---|---|
| `/static/` | `/home/mannu/gescom-bf/backend/app/static/` |

Cela permet à PythonAnywhere de servir directement les fichiers statiques sans passer par Flask (plus rapide).

---

## ÉTAPE 15 — Recharger et tester

### 15.1 Recharger l'application

Sur la page **Web**, cliquer le grand bouton vert :

**"Reload mannu.pythonanywhere.com"**

PythonAnywhere redémarre votre application Flask. Cela prend 5 à 15 secondes.

### 15.2 Tester le health check

Dans votre navigateur (sur votre ordinateur), ouvrez :

```
https://mannu.pythonanywhere.com/health
```

*(Remplacer `mannu` par votre username)*

Vous devez voir :
```json
{"status": "ok"}
```

Si vous voyez `{"status": "ok"}` → **l'API Flask fonctionne !** ✅

### 15.3 Tester le frontend

```
https://mannu.pythonanywhere.com/
```

Vous devez voir la **page de connexion de GesCom-BF** avec les champs email et mot de passe.

### 15.4 Se connecter

Utiliser les identifiants définis à l'étape 8.3 (f) :
- **Email :** `admin@gescom-bf.bf`
- **Mot de passe :** `admin@gescom-bf.bf`

Si la connexion réussit et que vous accédez au tableau de bord → **le site est opérationnel !** 🎉

### 15.5 En cas d'erreur — consulter les logs

Sur la page **Web**, section **"Log files"** :

- **Error log** → cliquer pour voir les erreurs Python (très utile pour déboguer)
- **Access log** → voir toutes les requêtes HTTP

---

## ÉTAPE 16 — Partager le lien avec vos amis

### 16.1 Votre URL publique

L'URL de votre site est simplement :

```
https://mannu.pythonanywhere.com
```

*(Avec votre vrai username à la place de `mannu`)*

### 16.2 Créer des comptes pour vos amis

Vos amis ne peuvent pas créer de compte eux-mêmes (le self-service multi-tenant est désactivé sur MySQL). Vous devez créer leurs comptes depuis l'interface admin.

**Option A — Via l'interface web (recommandée) :**

1. Connectez-vous avec votre compte admin
2. Menu **"Utilisateurs"** → **"Ajouter un utilisateur"**
3. Remplir : nom, email, mot de passe temporaire, rôle (`VENDEUR` ou `MAGASINIER`)
4. Envoyer les identifiants à votre ami par message privé

**Option B — Via la commande seed_demo :**

Si vous avez lancé `python -m app.seed_demo` à l'étape 10, des comptes de démonstration sont déjà créés :

| Rôle | Email | Mot de passe |
|---|---|---|
| ADMIN | `admin@gescom-bf.bf` | `Admin#2026` |
| MAGASINIER | `magasinier@gescom-bf.bf` | `Magasinier#2026` |
| VENDEUR | `vendeur@gescom-bf.bf` | `Vendeur#2026` |

> **⚠️ Changez ces mots de passe immédiatement** si vous utilisez ces comptes de démo en production.

### 16.3 Envoyer le lien

Message type à envoyer à vos amis :

```
Bonjour !

Le site GesCom-BF est en ligne 🎉

Lien d'accès : https://mannu.pythonanywhere.com

Identifiants de connexion :
  Email    : ton_email@example.com
  Mot de passe : [mot de passe temporaire]

Je te conseille de changer ton mot de passe dès la première connexion.

À bientôt !
```

### 16.4 Ce que vos amis peuvent faire

Selon le rôle attribué :

**VENDEUR** :
- Consulter le catalogue produits
- Effectuer des ventes (caisse)
- Voir son historique de ventes
- Accéder au tableau de bord (KPIs du jour)

**MAGASINIER** :
- Tout ce que fait le VENDEUR
- Gérer les stocks (entrées/sorties)
- Effectuer des transferts inter-sites
- Faire des inventaires

**ADMIN** :
- Tout ce que fait le MAGASINIER
- Gérer les utilisateurs
- Voir tous les rapports
- Accéder aux analyses et prévisions ML
- Configurer l'application

---

## ÉTAPE 17 — Planifier les tâches automatiques

Ces tâches font tourner le module IA et l'ETL pendant la nuit, sans intervention manuelle.

### 17.1 Aller dans l'onglet Tasks

Menu du haut → **"Tasks"**

### 17.2 Créer un script helper

Dans la console Bash :

```bash
cat > ~/run_task.sh << 'EOF'
#!/bin/bash
cd /home/mannu/gescom-bf/backend
source .venv/bin/activate
export FLASK_APP=wsgi.py
python -m flask "$@" >> /home/mannu/gescom-bf/logs/tasks.log 2>&1
EOF

chmod +x ~/run_task.sh
mkdir -p ~/gescom-bf/logs
```

*(Remplacer `mannu` par votre username)*

### 17.3 Ajouter les tâches planifiées

Dans l'onglet **Tasks** → **"Add a new scheduled task"** → remplir :

| Heure (UTC+0 = heure BF) | Fréquence | Commande |
|---|---|---|
| 02:00 | Daily | `/home/mannu/run_task.sh etl-daily` |
| 03:00 | Daily | `/home/mannu/run_task.sh ml-train-all` |
| 03:30 | Daily | `/home/mannu/run_task.sh db-backup` |

Cliquer **"Create"** pour chaque tâche.

---

## ANNEXE A — Dépannage rapide

### Le site affiche "502 Bad Gateway" ou une page d'erreur PythonAnywhere

**Causes les plus fréquentes :**

1. **Erreur dans le fichier WSGI** → Vérifier l'Error log (page Web → Log files)
2. **Chemin mal orthographié** dans le fichier WSGI (`/home/mannu/gescom-bf/backend` avec votre username)
3. **Virtualenv non configuré** → Vérifier section Virtualenv dans l'onglet Web

**Comment lire l'error log :**

Page Web → section "Log files" → cliquer sur le lien Error log. Chercher les lignes `Traceback` ou `Error`.

---

### Erreur "OperationalError: Can't connect to MySQL"

Votre `DATABASE_URL` dans `.env` est probablement incorrecte.

```bash
# Vérifier la valeur actuelle
grep DATABASE_URL ~/gescom-bf/backend/.env

# Tester la connexion manuellement
cd ~/gescom-bf/backend && source .venv/bin/activate
python3 -c "
import pymysql
conn = pymysql.connect(
    host='mannu.mysql.pythonanywhere-services.com',
    user='mannu',
    password='VOTRE_MOT_DE_PASSE_MYSQL',
    database='mannu\$gescom_bf'
)
print('Connexion OK !')
conn.close()
"
```

Si l'erreur persiste : vérifier le mot de passe dans l'onglet **Databases** et le réinitialiser si nécessaire.

---

### Le frontend affiche une page blanche

**Cause :** le build React n'existe pas, ou `SERVE_FRONTEND_DIST` pointe vers le mauvais chemin.

```bash
# Vérifier que le build existe
ls ~/gescom-bf/frontend/dist/index.html
# Doit afficher le chemin sans erreur

# Vérifier la variable dans .env
grep SERVE_FRONTEND_DIST ~/gescom-bf/backend/.env
# Doit afficher : SERVE_FRONTEND_DIST=/home/mannu/gescom-bf/frontend/dist

# Si le build est absent, le recréer :
cd ~/gescom-bf/frontend
npm install && npm run build
```

Puis recharger l'application (onglet Web → bouton Reload).

---

### Erreur "flask: command not found"

Le virtualenv n'est pas activé.

```bash
cd ~/gescom-bf/backend
source .venv/bin/activate
# Maintenant taper vos commandes flask
```

---

### "MySQL server has gone away" dans les logs

Connexion MySQL coupée après inactivité. C'est géré automatiquement par `pool_pre_ping=True` et `pool_recycle=280` dans la config. Si l'erreur persiste :

```bash
# Ajouter cette ligne dans .env
echo "SQLALCHEMY_POOL_RECYCLE=280" >> ~/gescom-bf/backend/.env
```

Puis recharger l'application.

---

### Les tables n'ont pas été créées (0 tables dans MySQL)

Relancer les migrations :

```bash
cd ~/gescom-bf/backend
source .venv/bin/activate
export FLASK_APP=wsgi.py
flask db upgrade
```

---

## ANNEXE B — Mettre à jour le site

Quand vous modifiez le code sur votre ordinateur et poussez sur GitHub, voici comment mettre à jour le site :

```bash
# 1. Ouvrir une console Bash sur PythonAnywhere

# 2. Récupérer le nouveau code
cd ~/gescom-bf
git pull origin main

# 3. Si requirements.txt a changé
cd backend
source .venv/bin/activate
pip install -r requirements.txt

# 4. Si des migrations ont été ajoutées
export FLASK_APP=wsgi.py
flask db upgrade

# 5. Si le frontend a changé
cd ../frontend
npm install
npm run build

# 6. Recharger l'application
# → Aller sur l'onglet Web → cliquer "Reload mannu.pythonanywhere.com"
```

---

## Récapitulatif des étapes

| # | Étape | Durée estimée |
|---|---|---|
| 0 | Préparer GitHub | 5 min |
| 1 | Créer compte PythonAnywhere | 5 min |
| 2 | Passer au plan Developer | 5 min |
| 3 | Créer base MySQL | 5 min |
| 4 | Ouvrir console Bash | 1 min |
| 5 | Cloner le projet | 2 min |
| 6 | Créer virtualenv Python | 2 min |
| 7 | Installer dépendances | 5 min |
| 8 | Configurer .env | 15 min |
| 9 | Appliquer migrations | 3 min |
| 10 | Seed des données | 2 min |
| 11 | Builder le frontend | 5 min |
| 12 | Créer l'app web | 3 min |
| 13 | Configurer le WSGI | 5 min |
| 14 | Configurer virtualenv | 2 min |
| 15 | Recharger et tester | 5 min |
| 16 | Partager le lien | 5 min |
| 17 | Planifier les tâches | 5 min |
| **Total** | | **~75 minutes** |

---

## Votre URL finale

```
https://<votre-username>.pythonanywhere.com
```

**C'est cette URL que vous partagez avec vos amis.**  
Elle est disponible 24h/24, 7j/7, sans que votre ordinateur soit allumé.
