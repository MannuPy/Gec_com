"""Point d'entree WSGI (Gunicorn / uWSGI / `flask run`).

PythonAnywhere : copier `backend/deploy/pythonanywhere_wsgi.py` dans le
fichier WSGI genere par l'onglet "Web" (cf. docs/32-GUIDE-DEPLOIEMENT-PYTHONANYWHERE.md).
Ce fichier wsgi.py est le point d'entree pour Gunicorn (Docker Compose /
VPS) et pour `flask run` en developpement.
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
