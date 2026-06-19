"""Taches Celery du pipeline ETL / Feature Store."""
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
