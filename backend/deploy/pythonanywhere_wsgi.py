"""
Modèle de fichier de configuration WSGI pour PythonAnywhere.

PythonAnywhere ne permet pas d'utiliser `backend/wsgi.py` directement : le
contenu ci-dessous doit être COPIÉ dans le fichier généré automatiquement par
l'onglet "Web" -> "Code" -> "WSGI configuration file"
(`/var/www/<utilisateur>_pythonanywhere_com_wsgi.py`).

Cf. docs/25-DEPLOIEMENT-CICD.md §25.9 pour la procédure complète.

Étapes :
  1. Adapter PROJECT_HOME ci-dessous (chemin absolu du dépôt sur PythonAnywhere,
     ex. /home/<utilisateur>/gescom-bf).
  2. Coller ce fichier (en remplaçant tout le contenu existant) dans le
     fichier WSGI de l'onglet "Web".
  3. Vérifier que l'onglet "Web" -> "Virtualenv" pointe vers le virtualenv
     créé pour le projet (cf. §25.9.2).
  4. Recharger l'application web ("Reload").
"""
import sys
import os

# ---- 1. Rendre le code de l'application importable ----
# Chemin absolu vers le dossier `backend/` du dépôt cloné sur PythonAnywhere.
PROJECT_HOME = "/home/<utilisateur>/gescom-bf/backend"
if PROJECT_HOME not in sys.path:
    sys.path.insert(0, PROJECT_HOME)

# ---- 2. Charger les variables d'environnement (.env) ----
# `app.config` appelle déjà `load_dotenv()`, mais celle-ci recherche le
# fichier `.env` relativement au répertoire courant du process, qui peut
# différer sous uWSGI. On force ici le chemin explicite vers le `.env`
# de production (cf. backend/.env.pythonanywhere.example).
from dotenv import load_dotenv

load_dotenv(os.path.join(PROJECT_HOME, ".env"))

# ---- 3. Créer l'application Flask ----
from app import create_app  # noqa: E402
