"""Tâches Celery du pipeline ETL / Feature Store (cf. 21-PIPELINE-ETL.md
§21.3, §21.6). Chaque tâche délègue à `app.services.etl_service`, dans le
contexte applicatif Flask fourni par `ContextTask` (cf. `app.celery_app`).

Orchestration (§21.3) :
- `etl_extract_and_clean` : extraction + nettoyage, quotidienne (02h00) ;
- `etl_validate`          : validation qualité (§21.4), après l'extraction ;
- `etl_build_features`    : feature engineering (§21.6), avant les tâches
  d'entraînement ML qui consomment la Feature Store
  (`train_credit_scoring_task`, `detect_anomalies_task`, etc.).

Si `etl_validate` échoue (`EtlValidationError`), `etl_build_features` ne
modifie aucune table `fs_*` et renvoie `{"success": False, ...}` — l'étape
suivante est ainsi bloquée, conformément à §21.4.
"""
from __future__ import annotations

import logging

from app.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.etl_tasks.etl_extract_and_clean")
def etl_extract_and_clean(days: int = 180) -> dict:
    from app.services import etl_service

    data = etl_service.extract_and_clean(days=days)
    result = {key: int(len(df)) for key, df in data.items()}
    logger.info("etl_extract_and_clean: %s", result)
    return result


@celery_app.task(name="app.tasks.etl_tasks.etl_validate")
def etl_validate(days: int = 180) -> dict:
    from app.services import etl_service

    data = etl_service.extract_and_clean(days=days)
    try:
        result = etl_service.validate(data)
    except etl_service.EtlValidationError as exc:
        logger.error("etl_validate: validation en echec - %s", exc)
        return {"success": False, "error": str(exc)}

    logger.info("etl_validate: %s", result)
    return result


@celery_app.task(name="app.tasks.etl_tasks.etl_build_features")
def etl_build_features(days: int = 180) -> dict:
    from app.services import etl_service

    try:
        result = etl_service.build_features(days=days)
    except etl_service.EtlValidationError as exc:
        logger.error("etl_build_features: validation en echec, etape bloquee - %s", exc)
        return {"success": False, "error": str(exc)}

    summary = {k: v for k, v in result.items() if k != "validation"}
    summary["validation"] = result["validation"]
    summary["success"] = True
    logger.info("etl_build_features: %s", {k: v for k, v in summary.items()})
    return summary
