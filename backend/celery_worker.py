"""
Point d'entrée Celery (worker et beat).

Usage :
    celery -A celery_worker.celery worker --loglevel=info -Q ml
    celery -A celery_worker.celery beat --loglevel=info

Cf. 21-PIPELINE-ETL.md, 20-MACHINE-LEARNING.md §20.7 et
`docker-compose.yml` (services `worker` / `beat`).
"""
from app import create_app
from app.celery_app import init_celery

flask_app = create_app()
celery = init_celery(flask_app)

# Importé après `init_celery` pour enregistrer les tâches auprès de
# l'instance Celery configurée.
from app.tasks import ml_tasks  # noqa: E402,F401
from app.tasks import etl_tasks 