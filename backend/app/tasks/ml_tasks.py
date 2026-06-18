"""
Tâches Celery d'entraînement des modèles ML (cf. 20-MACHINE-LEARNING.md
§20.7, 21-PIPELINE-ETL.md). Chaque tâche appelle `train(...)` du module
`app.ml.*` correspondant, dans le contexte applicatif Flask fourni par
`ContextTask` (cf. `app.celery_app`).

Ces tâches sont également invocables de façon synchrone (hors Celery) via
l'endpoint `POST /api/v1/analytics/ml/train/<model_type>` (cf. blueprint
`analytics`), qui appelle directement `train(...)` sans passer par Celery —
utile lorsque le worker/broker n'est pas disponible (environnement de
développement sans Redis).
"""
from __future__ import annotations

import logging

from app.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.ml_tasks.train_demand_forecast_task")
def train_demand_forecast_task(months: int = 6) -> dict:
    from app.ml import demand_forecast

    result = demand_forecast.train(months=months)
    logger.info("train_demand_forecast_task: %s", result)
    return result


@celery_app.task(name="app.tasks.ml_tasks.train_credit_scoring_task")
def train_credit_scoring_task() -> dict:
    from app.ml import credit_scoring

    result = credit_scoring.train()
    logger.info("train_credit_scoring_task: %s", result)
    return result


@celery_app.task(name="app.tasks.ml_tasks.detect_anomalies_task")
def detect_anomalies_task(days: int = 90) -> dict:
    from app.ml import anomaly_detection

    result = anomaly_detection.train(days=days)
    logger.info("detect_anomalies_task: %s", result)
    return result


@celery_app.task(name="app.tasks.ml_tasks.compute_abc_xyz_task")
def compute_abc_xyz_task(months: int = 6) -> dict:
    from app.ml import abc_xyz

    result = abc_xyz.train(months=months)
    logger.info("compute_abc_xyz_task: %s", result)
    return result


@celery_app.task(name="app.tasks.ml_tasks.compute_rfm_segments_task")
def compute_rfm_segments_task(months: int = 12, n_clusters: int = 4) -> dict:
    from app.ml import rfm_segmentation

    result = rfm_segmentation.train(months=months, n_clusters=n_clusters)
    logger.info("compute_rfm_segments_task: %s", result)
    return result


# Mapping utilisé par l'endpoint POST /analytics/ml/train/<model_type>
# pour lancer un entraînement synchrone (sans Celery) ou via `.delay()`.
TRAIN_FUNCTIONS = {
    "DEMAND_FORECAST": train_demand_forecast_task,
    "CREDIT_SCORING": train_credit_scoring_task,
    "ANOMALY_DETECTION": detect_anomalies_task,
    "ABC_XYZ": compute_abc_xyz_task,
}
