"""
Utilitaires partages par les modules `app.ml.*` : persistance des artefacts,
suivi MLflow (optionnel) et enregistrement dans le registre `ml_models` /
`predictions` (cf. 20-MACHINE-LEARNING.md).
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Iterable

from flask import current_app

from app.extensions import db
from app.models.ml import MLModel, Prediction

try:
    import joblib
    HAS_JOBLIB = True
except ImportError:
    HAS_JOBLIB = False

try:
    import mlflow
    HAS_MLFLOW = True
except ImportError:
    HAS_MLFLOW = False


def artifact_dir(model_type: str) -> str:
    base = current_app.config.get("ML_ARTIFACT_DIR", "instance/ml_artifacts")
    path = os.path.join(base, model_type.lower())
    os.makedirs(path, exist_ok=True)
    return path


def save_artifact(obj: Any, model_type: str, version: str) -> str | None:
    if not HAS_JOBLIB:
        return None
    path = os.path.join(artifact_dir(model_type), f"{version}.joblib")
    joblib.dump(obj, path)
    return path


def load_artifact(path: str | None) -> Any | None:
    if not path or not HAS_JOBLIB or not os.path.exists(path):
        return None
    return joblib.load(path)


class MLflowRun:
    """Context manager no-op si MLflow est indisponible."""

    def __init__(self, model_type: str):
        self.model_type = model_type
        self.run_id: str | None = None
        self._active = False

    def __enter__(self) -> "MLflowRun":
        if not HAS_MLFLOW:
            return self
        try:
            tracking_uri = current_app.config.get("MLFLOW_TRACKING_URI", "file:./mlruns")
            experiment = current_app.config.get("MLFLOW_EXPERIMENT_NAME", "gescom-bf")
            mlflow.set_tracking_uri(tracking_uri)
            mlflow.set_experiment(experiment)
            run = mlflow.start_run(
                run_name=model_type + "-" + datetime.utcnow().strftime("%Y%m%d%H%M%S")
            )
            self.run_id = run.info.run_id
            self._active = True
        except Exception:
            self.run_id = None
            self._active = False
        return self

    def log_params(self, params: dict) -> None:
        if not self._active:
            return
        try:
            mlflow.log_params(params)
        except Exception:
            pass

    def log_metrics(self, metrics: dict) -> None:
        if not self._active:
            return
        try:
            mlflow.log_metrics({k: float(v) for k, v in metrics.items() if v is not None})
        except Exception:
            pass

    def log_artifact(self, path: str | None) -> None:
        if not self._active or not path:
            return
        try:
            mlflow.log_artifact(path)
        except Exception:
            pass

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._active:
            try:
                mlflow.end_run()
            except Exception:
                pass


def next_version(model_type: str) -> str:
    return model_type.lower() + "_" + datetime.utcnow().strftime("%Y%m%d_%H%M%S")


def register_model(
    model_type: str,
    algorithm: str,
    metrics: dict | None = None,
    artifact_path: str | None = None,
    mlflow_run_id: str | None = None,
    version: str | None = None,
    deactivate_previous: bool = True,
    keep_versions: int = 3,
) -> MLModel:
    """Enregistre un nouveau modele et desactive/purge les anciennes versions.

    `keep_versions` : nombre de versions inactives a conserver (defaut 3).
    Les versions plus anciennes sont supprimees pour eviter une croissance
    indefinie de la table `ml_models` (voir 20-MACHINE-LEARNING.md).
    """
    if deactivate_previous:
        MLModel.query.filter_by(model_type=model_type, is_active=True).update({"is_active": False})

    # Purger les anciennes versions inactives au-dela de keep_versions
    old_models = (
        MLModel.query
        .filter_by(model_type=model_type, is_active=False)
        .order_by(MLModel.trained_at.desc())
        .offset(keep_versions)
        .all()
    )
    for old_model in old_models:
        if old_model.artifact_path:
            try:
                import os as _os
                if _os.path.exists(old_model.artifact_path):
                    _os.remove(old_model.artifact_path)
            except Exception:
                pass
        db.session.delete(old_model)

    model = MLModel(
        model_type=model_type,
        version=version or next_version(model_type),
        algorithm=algorithm,
        metrics_json=metrics or {},
        artifact_path=artifact_path,
        mlflow_run_id=mlflow_run_id,
        trained_at=datetime.utcnow(),
        is_active=True,
    )
    db.session.add(model)
    db.session.flush()
    return model


def record_predictions(
    model: MLModel,
    prediction_type: str,
    entries: Iterable[dict],
    clear_previous: bool = True,
) -> int:
    if clear_previous:
        Prediction.query.filter_by(prediction_type=prediction_type).delete()

    count = 0
    for entry in entries:
        db.session.add(
            Prediction(
                model_id=model.id,
                prediction_type=prediction_type,
                entity_type=entry["entity_type"],
                entity_id=entry.get("entity_id"),
                payload_json=entry["payload"],
                created_at=datetime.utcnow(),
            )
        )
        count += 1

    db.session.flush()
    return count


def get_active_model(model_type: str) -> MLModel | None:
    return (
        MLModel.query.filter_by(model_type=model_type, is_active=True)
        .order_by(MLModel.trained_at.desc())
        .first()
    )


def latest_predictions(prediction_type: str) -> list:
    from app.models.ml import Prediction
    subq = (
        db.session.query(
            Prediction.entity_id,
            db.func.max(Prediction.created_at).label("max_created_at"),
        )
        .filter(Prediction.prediction_type == prediction_type)
        .group_by(Prediction.entity_id)
        .subquery()
    )
    return (
        db.session.query(Prediction)
        .join(
            subq,
            (Prediction.entity_id == subq.c.entity_id)
            & (Prediction.created_at == subq.c.max_created_at),
        )
        .filter(Prediction.prediction_type == prediction_type)
        .all()
    )
