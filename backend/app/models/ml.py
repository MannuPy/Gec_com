"""
Registre des modèles de Machine Learning et traçabilité des prédictions.

Cf. 20-MACHINE-LEARNING.md §20.7 et 21-PIPELINE-ETL.md : chaque exécution
d'entraînement crée une entrée dans `ml_models` (type, version, algorithme,
métriques, chemin d'artefact MLflow) référencée par chaque `predictions.model_id`
— garantissant que toute prédiction est traçable jusqu'au modèle et aux
données qui l'ont produite (RNF-17, RG-40).
"""
import enum

from app.extensions import db
from app.models.base import UUIDPrimaryKeyMixin
from datetime import datetime


class MLModelType(str, enum.Enum):
    DEMAND_FORECAST = "DEMAND_FORECAST"
    CREDIT_SCORING = "CREDIT_SCORING"
    ANOMALY_DETECTION = "ANOMALY_DETECTION"
    ABC_XYZ = "ABC_XYZ"
    RFM_SEGMENTATION = "RFM_SEGMENTATION"
    MARKET_BASKET = "MARKET_BASKET"  # Fix : manquait dans l'enum


class MLModel(db.Model, UUIDPrimaryKeyMixin):
    """Entrée du registre des modèles entraînés (cf. 20.7)."""

    __tablename__ = "ml_models"

    model_type = db.Column(db.String(32), nullable=False, index=True)
    version = db.Column(db.String(64), nullable=False)
    algorithm = db.Column(db.String(64), nullable=False)
    metrics_json = db.Column(db.JSON, nullable=True)
    artifact_path = db.Column(db.String(500), nullable=True)
    mlflow_run_id = db.Column(db.String(64), nullable=True)
    trained_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    predictions = db.relationship("Prediction", backref="model", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<MLModel {self.model_type} v{self.version} ({self.algorithm})>"


class Prediction(db.Model, UUIDPrimaryKeyMixin):
    """Sortie d'un modèle ML, tracée jusqu'à son modèle d'origine."""

    __tablename__ = "predictions"

    model_id = db.Column(db.String(36), db.ForeignKey("ml_models.id"), nullable=False)
    prediction_type = db.Column(db.String(32), nullable=False, index=True)
    entity_type = db.Column(db.String(32), nullable=False)
    entity_id = db.Column(db.String(36), nullable=True, index=True)
    payload_json = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    def __repr__(self) -> str:
        return f"<Prediction {self.prediction_type} entity={self.entity_id}>"
