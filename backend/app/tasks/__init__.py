"""
Tâches asynchrones Celery (cf. 21-PIPELINE-ETL.md).

`ml_tasks` regroupe les tâches d'entraînement / d'inférence des modules
`app.ml.*`. Importé par `celery_worker.py` pour enregistrer les tâches
auprès de l'instance Celery (`app.celery_app.celery_app`).
"""
