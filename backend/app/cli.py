"""
Commandes Flask CLI - exécution synchrone des tâches ETL/ML sans Celery/Redis.

Cf. 21-PIPELINE-ETL.md §21.3 (orchestration) et 25-DEPLOIEMENT-CICD.md. Sur un
hébergement sans worker Celery dédié (ex. PythonAnywhere), ces commandes sont
appelées par les "Scheduled tasks" de la plateforme à la place de Celery beat :

    # quotidien (02h00)
    flask etl-daily

    # quotidien (02h30) ou hebdomadaire selon le plan disponible
    flask ml-train-all

    # horaire (si le plan le permet), sinon inclus dans ml-train-all
    flask ml-detect-anomalies

    # amorçage initial des données de référence (idempotent)
    flask seed

Chaque tâche Celery (`app.tasks.*`) reste un objet `Task` ; `.run(...)`
exécute la fonction sous-jacente directement, sans broker ni worker.
"""
from __future__ import annotations

import json

import click
from flask import Flask


def register_cli(app: Flask) -> None:
    @app.cli.command("seed")
    def seed_command() -> None:
        """Amorce les données de référence (RBAC, sites, catalogue, démo)."""
        from app import seed as seed_module

        seed_module.run()

    @app.cli.command("seed-demo")
    @click.option("--months", default=6, show_default=True, help="Profondeur d'historique a generer (mois).")
    @click.option("--seed", default=42, show_default=True, help="Graine du generateur aleatoire (reproductibilite).")
    def seed_demo_command(months: int, seed: int) -> None:
        """Genere un jeu de donnees commerciales de demonstration (catalogue
        etendu, clients, fournisseurs, ventes/POS, stock, credit, anomalies).

        A executer UNE FOIS apres 'flask seed', sur une base fraichement
        amorcee. Ordre recommande :

            flask seed
            flask seed-demo --months 6
            flask etl-daily --days 180
            flask ml-train-all --months 6
        """
        from app import seed_demo as seed_demo_module

        seed_demo_module.run(months=months, seed=seed)

    @app.cli.command("etl-daily")
    @click.option("--days", default=180, show_default=True, help="Fenetre d'historique (jours).")
    def etl_daily_command(days: int) -> None:
        """Pipeline ETL quotidien : extraction -> validation -> feature store (§21.3)."""
        from app.tasks.etl_tasks import etl_build_features, etl_extract_and_clean, etl_validate

        extract_result = etl_extract_and_clean.run(days=days)
        click.echo(f"etl_extract_and_clean: {json.dumps(extract_result, default=str)}")

        validate_result = etl_validate.run(days=days)
        click.echo(f"etl_validate: {json.dumps(validate_result, default=str)}")
        if validate_result.get("success") is False:
            click.echo("Validation en echec : etl_build_features ne sera pas execute.", err=True)
            raise SystemExit(1)

        features_result = etl_build_features.run(days=days)
        click.echo(
            "etl_build_features: "
            f"{json.dumps({k: v for k, v in features_result.items() if k != 'validation'}, default=str)}"
        )
        if features_result.get("success") is False:
            raise SystemExit(1)

    @app.cli.command("ml-train-all")
    @click.option("--months", default=6, show_default=True, help="Fenetre d'historique (mois) pour la demande/ABC-XYZ.")
    @click.option("--anomaly-days", default=90, show_default=True, help="Fenetre d'historique (jours) pour les anomalies.")
    @click.option("--rfm-months", default=12, show_default=True, help="Fenetre d'historique (mois) pour la segmentation RFM.")
    def ml_train_all_command(months: int, anomaly_days: int, rfm_months: int) -> None:
        """Entraine/recalcule l'ensemble des modeles ML (RF-25 a RF-28)."""
        from app.tasks.ml_tasks import (
            compute_abc_xyz_task,
            compute_market_basket_task,
            compute_rfm_segments_task,
            detect_anomalies_task,
            train_credit_scoring_task,
            train_demand_forecast_task,
        )

        results = {
            "demand_forecast": train_demand_forecast_task.run(months=months),
            "credit_scoring": train_credit_scoring_task.run(),
            "anomaly_detection": detect_anomalies_task.run(days=anomaly_days),
            "abc_xyz": compute_abc_xyz_task.run(months=months),
            "rfm_segmentation": compute_rfm_segments_task.run(months=rfm_months),
            "market_basket": compute_market_basket_task.run(months=months),  # Fix : manquait
        }
        click.echo(json.dumps(results, default=str, ensure_ascii=False))

    @app.cli.command("ml-detect-anomalies")
    @click.option("--days", default=90, show_default=True, help="Fenetre d'historique (jours).")
    def ml_detect_anomalies_command(days: int) -> None:
        """Detection d'anomalies sur les ventes recentes (RF-28), executable horairement."""
        from app.tasks.ml_tasks import detect_anomalies_task

        result = detect_anomalies_task.run(days=days)
        click.echo(f"Detection anomalies complete : {result}")
