#!/usr/bin/env python3
"""
Script d'entraînement nocturne des modèles ML — GesCom-BF.

À configurer comme tâche planifiée sur PythonAnywhere :
  Section "Tasks" → "Add a new scheduled task"
  Heure    : 02:00
  Commande : /home/<username>/.virtualenvs/<venv>/bin/python \
             /home/<username>/gescom/backend/scripts/cron_train_all.py

Remplacer <username> et <venv> par les valeurs réelles du compte PythonAnywhere.

Journaux : /tmp/gescom_ml_training.log (écrasé à chaque exécution)
"""
import sys
import os
import logging

# Rendre le package `app` importable depuis n'importe quel répertoire courant.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("/tmp/gescom_ml_training.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("cron_train_all")


def run_all() -> dict:
    """Lance l'entraînement de tous les modèles ML dans un contexte Flask."""
    from app import create_app

    app = create_app()
    results: dict = {}

    with app.app_context():

        # 1. Prévision de demande (LinearRegression + Prophet si dispo)
        try:
            from app.ml import demand_forecast
            results["demand_forecast"] = demand_forecast.train(months=6)
            logger.info("demand_forecast OK : %s", results["demand_forecast"])
        except Exception as exc:
            logger.error("demand_forecast FAILED : %s", exc, exc_info=True)
            results["demand_forecast"] = {"status": "error", "error": str(exc)}

        # 2. Scoring crédit (RandomForest + LogisticRegression ou règles)
        try:
            from app.ml import credit_scoring
            results["credit_scoring"] = credit_scoring.train()
            logger.info("credit_scoring OK : %s", results["credit_scoring"])
        except Exception as exc:
            logger.error("credit_scoring FAILED : %s", exc, exc_info=True)
            results["credit_scoring"] = {"status": "error", "error": str(exc)}

        # 3. Détection d'anomalies (IsolationForest + Z-Score)
        try:
            from app.ml import anomaly_detection
            results["anomaly_detection"] = anomaly_detection.train(days=90)
            logger.info("anomaly_detection OK : %s", results["anomaly_detection"])
        except Exception as exc:
            logger.error("anomaly_detection FAILED : %s", exc, exc_info=True)
            results["anomaly_detection"] = {"status": "error", "error": str(exc)}

        # 4. Classification ABC/XYZ produits
        try:
            from app.ml import abc_xyz
            results["abc_xyz"] = abc_xyz.train(months=6)
            logger.info("abc_xyz OK : %s", results["abc_xyz"])
        except Exception as exc:
            logger.error("abc_xyz FAILED : %s", exc, exc_info=True)
            results["abc_xyz"] = {"status": "error", "error": str(exc)}

        # 5. Segmentation RFM clients (KMeans)
        try:
            from app.ml import rfm_segmentation
            results["rfm_segmentation"] = rfm_segmentation.train(months=12)
            logger.info("rfm_segmentation OK : %s", results["rfm_segmentation"])
        except Exception as exc:
            logger.error("rfm_segmentation FAILED : %s", exc, exc_info=True)
            results["rfm_segmentation"] = {"status": "error", "error": str(exc)}

        # 6. Market Basket Analysis (module optionnel — Phase 2.1)
        try:
            from app.ml import market_basket
            results["market_basket"] = market_basket.train(months=6)
            logger.info("market_basket OK : %s", results["market_basket"])
        except ImportError:
            logger.info("market_basket : module non encore déployé, ignoré.")
            results["market_basket"] = {"status": "skipped", "reason": "module absent"}
        except Exception as exc:
            logger.error("market_basket FAILED : %s", exc, exc_info=True)
            results["market_basket"] = {"status": "error", "error": str(exc)}

        logger.info("=== ENTRAÎNEMENT TERMINÉ === %s", results)

    return results


if __name__ == "__main__":
    run_all()
