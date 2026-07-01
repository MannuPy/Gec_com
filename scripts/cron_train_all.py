#!/usr/bin/env python3
"""
Script d'entraînement ML nocturne — GesCom-BF.

Usage sur PythonAnywhere (Scheduled Tasks, 02h00 UTC) :
    /home/<username>/.virtualenvs/gescom-bf/bin/python \
        /home/<username>/gescom-bf/scripts/cron_train_all.py

Ce script est l'alternative au worker Celery/Redis (non disponible sur
PythonAnywhere). Il appelle directement les tâches ML via `flask ml-train-all`
en invoquant la CLI Flask, ou — alternative — en créant le contexte
applicatif directement.

Cf. docs/32-GUIDE-DEPLOIEMENT-PYTHONANYWHERE.md §9.
"""
from __future__ import annotations

import os
import sys
import time
import logging
from datetime import datetime

# ── Configuration du chemin ───────────────────────────────────────────────────
# Ce script peut être lancé depuis n'importe où sur PythonAnywhere.
# On calcule le chemin du projet à partir de l'emplacement du script.
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)           # racine du repo
BACKEND_DIR = os.path.join(PROJECT_DIR, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_FILE = os.path.join(PROJECT_DIR, "logs", "cron_train_all.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

# ── Variables d'environnement ─────────────────────────────────────────────────
# S'assurer que les vars sont chargées si ce script est lancé hors Flask.
env_file = os.path.join(BACKEND_DIR, ".env")
if os.path.isfile(env_file):
    from dotenv import load_dotenv
    load_dotenv(env_file)


def run_all() -> dict:
    """Exécute ETL + tous les modèles ML dans le contexte Flask.

    Retourne un dict de résultats par tâche avec succès/erreur.
    """
    from app import create_app
    from app.tasks.etl_tasks import etl_build_features, etl_extract_and_clean, etl_validate
    from app.tasks.ml_tasks import (
        compute_demand_forecast_task,
        compute_rfm_segmentation_task,
        compute_anomaly_detection_task,
        compute_credit_scoring_task,
        compute_abc_xyz_task,
        compute_market_basket_task,
    )

    flask_app = create_app("production")
    results: dict = {}
    start_global = time.monotonic()

    with flask_app.app_context():
        # ── 1. ETL Pipeline ───────────────────────────────────────────────
        log.info("=== ETL Pipeline ===")

        for task_fn, label in [
            (etl_extract_and_clean, "etl_extract_and_clean"),
            (etl_validate,          "etl_validate"),
            (etl_build_features,    "etl_build_features"),
        ]:
            t0 = time.monotonic()
            try:
                res = task_fn.run()
                elapsed = round(time.monotonic() - t0, 1)
                log.info("  ✅ %s — %.1fs : %s", label, elapsed, res)
                results[label] = {"ok": True, "elapsed_s": elapsed, "result": res}
                if res.get("success") is False:
                    log.warning("  ⚠️ %s a indiqué un échec — arrêt de l'ETL.", label)
                    break
            except Exception as exc:
                elapsed = round(time.monotonic() - t0, 1)
                log.error("  ❌ %s — %.1fs : %s", label, elapsed, exc, exc_info=True)
                results[label] = {"ok": False, "elapsed_s": elapsed, "error": str(exc)}
                # On continue les autres tâches ETL même en cas d'erreur partielle.

        # ── 2. Modèles ML ─────────────────────────────────────────────────
        log.info("=== Entraînement ML ===")

        ml_tasks = [
            (compute_demand_forecast_task, "demand_forecast",     {}),
            (compute_rfm_segmentation_task,"rfm_segmentation",    {}),
            (compute_anomaly_detection_task,"anomaly_detection",   {}),
            (compute_credit_scoring_task,  "credit_scoring",      {}),
            (compute_abc_xyz_task,         "abc_xyz",             {}),
            (compute_market_basket_task,   "market_basket",       {"months": 6}),
        ]

        for task_fn, label, kwargs in ml_tasks:
            t0 = time.monotonic()
            try:
                res = task_fn.run(**kwargs)
                elapsed = round(time.monotonic() - t0, 1)
                log.info("  ✅ %s — %.1fs", label, elapsed)
                results[label] = {"ok": True, "elapsed_s": elapsed}
            except Exception as exc:
                elapsed = round(time.monotonic() - t0, 1)
                log.error("  ❌ %s — %.1fs : %s", label, elapsed, exc, exc_info=True)
                results[label] = {"ok": False, "elapsed_s": elapsed, "error": str(exc)}
                # On ne stoppe pas : une tâche en erreur ne bloque pas les suivantes.

    total = round(time.monotonic() - start_global, 1)
    nb_ok  = sum(1 for v in results.values() if v.get("ok"))
    nb_err = len(results) - nb_ok

    log.info(
        "=== Terminé en %.1fs — %d OK / %d ERREUR ===",
        total, nb_ok, nb_err,
    )
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "total_elapsed_s": total,
        "nb_ok": nb_ok,
        "nb_errors": nb_err,
        "tasks": results,
    }


if __name__ == "__main__":
    log.info("Démarrage cron_train_all.py — %s UTC", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
    try:
        summary = run_all()
        if summary["nb_errors"] > 0:
            log.warning("Terminé avec %d erreur(s).", summary["nb_errors"])
            sys.exit(1)       # code de sortie non-0 → PythonAnywhere logge l'échec
        sys.exit(0)
    except Exception as exc:
        log.critical("Erreur critique non récupérée : %s", exc, exc_info=True)
        sys.exit(2)
