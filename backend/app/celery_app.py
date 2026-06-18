"""
Integration Celery (cf. 21-PIPELINE-ETL.md, 20-MACHINE-LEARNING.md section 20.7).

L'instance Celery est creee sans application Flask liee (pour eviter les
imports circulaires) puis configuree via `init_celery(app)`, appele depuis
`celery_worker.py`. Chaque tache s'execute dans un contexte applicatif Flask
(`ContextTask`) afin d'acceder a la base de donnees et a la configuration.

Planification (beat) :
- `etl_extract_and_clean`       : quotidienne (02h00) - section 21.3 (ETL)
- `etl_validate`                : quotidienne (02h10), apres l'extraction - section 21.3/21.4
- `etl_build_features`          : quotidienne (02h20), avant les taches ML - section 21.3/21.6
- `train_demand_forecast_task`  : hebdomadaire (lundi 02h00) - RF-25/RG-38
- `train_credit_scoring_task`   : quotidienne (02h30) - RF-27
- `detect_anomalies_task`       : horaire - RF-28
- `compute_abc_xyz_task`        : hebdomadaire (lundi 03h00) - RF-26
- `compute_rfm_segments_task`   : mensuelle (1er du mois, 04h00) - RF-26
"""
from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

celery_app = Celery("gescom_bf")


def init_celery(app) -> Celery:
    """Configure l'instance Celery globale a partir de l'app Flask."""
    celery_app.conf.update(
        broker_url=app.config["CELERY_BROKER_URL"],
        result_backend=app.config["CELERY_RESULT_BACKEND"],
        timezone="UTC",
        enable_utc=True,
        task_default_queue="ml",
        beat_schedule={
            "etl-extract-and-clean-daily": {
                "task": "app.tasks.etl_tasks.etl_extract_and_clean",
                "schedule": crontab(hour=2, minute=0),
            },
            "etl-validate-daily": {
                "task": "app.tasks.etl_tasks.etl_validate",
                "schedule": crontab(hour=2, minute=10),
            },
            "etl-build-features-daily": {
                "task": "app.tasks.etl_tasks.etl_build_features",
                "schedule": crontab(hour=2, minute=20),
            },
            "train-demand-forecast-weekly": {
                "task": "app.tasks.ml_tasks.train_demand_forecast_task",
                "schedule": crontab(day_of_week="monday", hour=2, minute=0),
            },
            "train-credit-scoring-nightly": {
                "task": "app.tasks.ml_tasks.train_credit_scoring_task",
                "schedule": crontab(hour=2, minute=30),
            },
            "detect-anomalies-hourly": {
                "task": "app.tasks.ml_tasks.detect_anomalies_task",
                "schedule": crontab(minute=0),
            },
            "compute-abc-xyz-weekly": {
                "task": "app.tasks.ml_tasks.compute_abc_xyz_task",
                "schedule": crontab(day_of_week="monday", hour=3, minute=0),
            },
            "compute-rfm-segments-monthly": {
                "task": "app.tasks.ml_tasks.compute_rfm_segments_task",
                "schedule": crontab(day_of_month=1, hour=4, minute=0),
            },
        },
    )

    class ContextTask(celery_app.Task):
        """Execute chaque tache dans le contexte applicatif Flask."""

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    celery_app.Task = ContextTask
    return celery_app
