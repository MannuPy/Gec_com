"""
Routes du blueprint `analytics` : tableau de bord avance et endpoints IA/ML
(RF-24 a RF-29, cf. 03-ANALYSE-DES-BESOINS.md et 20-MACHINE-LEARNING.md).

- `GET /dashboard`        : indicateurs etendus (marges, multi-site, consolide) - RF-24
- `GET /forecast`         : previsions de demande / alertes de rupture - RF-25, RG-38
- `GET /credit-scores`    : scoring credit clients - RF-27
- `GET /anomalies`        : detection d'anomalies sur les ventes - RF-28
- `GET /abc-xyz`          : classification ABC/XYZ des produits - RF-26
- `GET /rfm-segments`     : segmentation RFM des clients - RF-26
- `GET /ml/models`        : registre des modeles entraines (tracabilite RNF-17)
- `POST /ml/train/<type>` : declenche l'entrainement d'un modele - RF-29
"""
from __future__ import annotations

from flask import current_app, jsonify, request

from app.blueprints.analytics import analytics_bp
from app.models import MLModel
from app.services.analytics_service import compute_dashboard
from app.utils.decorators import require_permission


@analytics_bp.get("/dashboard")
@require_permission("analytics:read")
def advanced_dashboard():
    """Tableau de bord etendu : marges, ventilation multi-site, consolide (RF-24)."""
    branch_id = request.args.get("branch_id")
    try:
        days = int(request.args.get("days", 30))
    except ValueError:
        days = 30

    return jsonify(compute_dashboard(branch_id=branch_id, days=days))


@analytics_bp.get("/forecast")
@require_permission("analytics:read")
def demand_forecast_view():
    """Previsions de demande et alertes de rupture de stock (RF-25, RG-38)."""
    from app.ml import demand_forecast

    alerts_only = request.args.get("alerts_only", "false").lower() in ("1", "true", "yes")
    branch_id = request.args.get("branch_id")
    product_id = request.args.get("product_id")

    results = demand_forecast.latest(alerts_only=alerts_only)
    if branch_id:
        results = [r for r in results if r.get("branch_id") == branch_id]
    if product_id:
        results = [r for r in results if r.get("product_id") == product_id]

    return jsonify({"items": results, "count": len(results)})


@analytics_bp.get("/forecast/<product_id>/<branch_id>")
@require_permission("analytics:read")
def demand_forecast_detail(product_id: str, branch_id: str):
    """Prevision de demande pour un couple produit/site donne (RF-25)."""
    from app.ml import demand_forecast

    results = demand_forecast.latest()
    for r in results:
        if r.get("product_id") == product_id and r.get("branch_id") == branch_id:
            return jsonify(r)

    return jsonify({"error": "NOT_FOUND", "message": "Aucune prevision disponible pour ce produit/site."}), 404


@analytics_bp.get("/credit-scores")
@require_permission("analytics:read")
def credit_scores_view():
    """Scoring credit des clients (RF-27)."""
    from app.ml import credit_scoring

    risk_level = request.args.get("risk_level")
    customer_id = request.args.get("customer_id")

    results = credit_scoring.latest()
    if risk_level:
        results = [r for r in results if r.get("risk_level") == risk_level.upper()]
    if customer_id:
        results = [r for r in results if r.get("customer_id") == customer_id]

    return jsonify({"items": results, "count": len(results)})


@analytics_bp.get("/anomalies")
@require_permission("analytics:read")
def anomalies_view():
    """Ventes signalees comme anomalies (RF-28)."""
    from app.ml import anomaly_detection

    branch_id = request.args.get("branch_id")

    results = anomaly_detection.latest()
    if branch_id:
        results = [r for r in results if r.get("branch_id") == branch_id]

    return jsonify({"items": results, "count": len(results)})


@analytics_bp.get("/abc-xyz")
@require_permission("analytics:read")
def abc_xyz_view():
    """Classification ABC/XYZ des produits (RF-26)."""
    from app.ml import abc_xyz

    abc_class = request.args.get("abc_class")
    xyz_class = request.args.get("xyz_class")

    results = abc_xyz.latest()
    if abc_class:
        results = [r for r in results if r.get("abc_class") == abc_class.upper()]
    if xyz_class:
        results = [r for r in results if r.get("xyz_class") == xyz_class.upper()]

    return jsonify({"items": results, "count": len(results)})


@analytics_bp.get("/rfm-segments")
@require_permission("analytics:read")
def rfm_segments_view():
    """Segmentation RFM des clients (RF-26)."""
    from app.ml import rfm_segmentation

    segment = request.args.get("segment")

    results = rfm_segmentation.latest()
    if segment:
        results = [r for r in results if r.get("segment") == segment.upper()]

    return jsonify({"items": results, "count": len(results)})


@analytics_bp.get("/ml/models")
@require_permission("analytics:read")
def ml_models_view():
    """Registre des modeles entraines, pour tracabilite (RNF-17, RG-40)."""
    models = MLModel.query.order_by(MLModel.model_type, MLModel.trained_at.desc()).all()

    return jsonify(
        {
            "items": [
                {
                    "id": m.id,
                    "model_type": m.model_type,
                    "version": m.version,
                    "algorithm": m.algorithm,
                    "metrics": m.metrics_json,
                    "mlflow_run_id": m.mlflow_run_id,
                    "trained_at": m.trained_at.isoformat(),
                    "is_active": m.is_active,
                }
                for m in models
            ]
        }
    )


@analytics_bp.post("/ml/train/<model_type>")
@require_permission("ml:train")
def trigger_training(model_type: str):
    """
    Declenche l'entrainement d'un modele ML (RF-29).

    Par defaut, execution synchrone (utile en environnement de developpement
    sans worker Celery/Redis). Avec `?async=true`, tente de planifier la
    tache via Celery (`.delay()`) et bascule en synchrone si le broker est
    indisponible.
    """
    from app.tasks.ml_tasks import TRAIN_FUNCTIONS

    model_type_normalized = model_type.upper()
    if model_type_normalized not in TRAIN_FUNCTIONS:
        return (
            jsonify(
                {
                    "error": "VALIDATION_ERROR",
                    "message": f"Type de modele inconnu. Valeurs possibles : {', '.join(sorted(TRAIN_FUNCTIONS))}",
                }
            ),
            400,
        )

    task = TRAIN_FUNCTIONS[model_type_normalized]
    use_async = request.args.get("async", "false").lower() in ("1", "true", "yes")

    if use_async:
        try:
            async_result = task.delay()
            return (
                jsonify({"status": "queued", "task_id": async_result.id, "model_type": model_type_normalized}),
                202,
            )
        except Exception as exc:  # broker indisponible -> repli synchrone
            current_app.logger.warning(
                "Celery/Redis indisponible (%s) ; execution synchrone de l'entrainement %s.",
                exc,
                model_type_normalized,
            )
            result = task.run()
            return jsonify({"status": "ok", "model_type": model_type_normalized, "result": result})

    result = task.run()
    return jsonify({"status": "ok", "model_type": model_type_normalized, "result": result})
