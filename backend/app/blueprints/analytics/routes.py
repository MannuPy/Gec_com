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

from datetime import datetime, date, time, timedelta
from collections import defaultdict

from flask import current_app, jsonify, request

from app.blueprints.analytics import analytics_bp
from app.extensions import db
from app.models import MLModel, Sale, SaleStatus, SaleLine, Customer
from app.services.analytics_service import compute_dashboard, compute_sales_trend
from app.utils.decorators import require_permission


@analytics_bp.get("/sales-trend")
@require_permission("analytics:read")
def sales_trend_view():
    """Serie temporelle des ventes jour par jour (graphiques tendance RF-24)."""
    branch_id = request.args.get("branch_id")
    try:
        days = int(request.args.get("days", 30))
    except ValueError:
        days = 30
    data = compute_sales_trend(branch_id=branch_id, days=days)
    return jsonify({"items": data, "count": len(data)})


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
@require_permission("analytics:read", "ml:train")
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
                    "message": "Type de modele inconnu. Valeurs possibles : " + ", ".join(sorted(TRAIN_FUNCTIONS)),
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
    return jsonify({"status": "completed", "model_type": model_type_normalized, "result": result})


@analytics_bp.post('/ml/train')
@require_permission('ml:train')
def trigger_training_body():
    """
    Variante de trigger_training acceptant le type de modele dans le corps JSON.

    Payload : { model_type: str, async?: bool }

    Alias pour compatibilite avec le client frontend qui envoie le type dans
    le corps de la requete plutot qu'en parametre d'URL.
    """
    from app.tasks.ml_tasks import TRAIN_FUNCTIONS

    payload = request.get_json(silent=True) or {}
    model_type = payload.get('model_type', '')
    model_type_normalized = model_type.upper()

    if not model_type_normalized or model_type_normalized not in TRAIN_FUNCTIONS:
        return (
            jsonify({
                'error': 'VALIDATION_ERROR',
                'message': 'Type de modele manquant ou inconnu. Valeurs possibles : ' + ', '.join(sorted(TRAIN_FUNCTIONS)),
            }),
            400,
        )

    task = TRAIN_FUNCTIONS[model_type_normalized]
    use_async = payload.get('async', False) or request.args.get('async', 'false').lower() in ('1', 'true', 'yes')

    if use_async:
        try:
            async_result = task.delay()
            return (
                jsonify({'status': 'queued', 'task_id': async_result.id, 'model_type': model_type_normalized}),
                202,
            )
        except Exception as exc:
            current_app.logger.warning(
                "Celery/Redis indisponible (%s) ; execution synchrone de l'entrainement %s.",
                exc,
                model_type_normalized,
            )
            result = task.run()
            return jsonify({'status': 'ok', 'model_type': model_type_normalized, 'result': result})

    result = task.run()
    return jsonify({'status': 'completed', 'model_type': model_type_normalized, 'result': result})


# ---------------------------------------------------------------------------
# Analyse de cohortes clients — Feature E
# ---------------------------------------------------------------------------

@analytics_bp.get("/cohorts")
@require_permission("analytics:read")
def cohort_analysis():
    """Matrice de retention clients par cohorte d'acquisition.

    Groupe les clients par mois du premier achat, puis calcule le taux de retention
    (% de clients de la cohorte ayant rachete) pour chaque mois suivant (M+0, M+1, ...).

    Retourne une liste de cohortes :
      - cohort       : mois YYYY-MM
      - size         : nombre de clients dans la cohorte
      - retention    : liste [{"month": 0, "count": n, "rate": 100.0}, ...]

    Parametres GET :
        months : nombre de mois a analyser (defaut 12)
    """
    try:
        nb_months = max(1, min(int(request.args.get("months", 12)), 24))
    except ValueError:
        nb_months = 12

    today = datetime.utcnow().date()
    start_date = date(today.year, today.month, 1) - timedelta(days=nb_months * 31)

    sales = (
        db.session.query(Sale.customer_id, Sale.created_at)
        .filter(
            Sale.status == SaleStatus.VALIDEE.value,
            Sale.customer_id.isnot(None),
            Sale.created_at >= datetime.combine(start_date, time.min),
        )
        .order_by(Sale.created_at)
        .all()
    )

    if not sales:
        return jsonify({"cohorts": [], "max_months": 0})

    first_purchase = {}
    for cid, created_at in sales:
        mois = created_at.strftime("%Y-%m")
        if cid not in first_purchase or mois < first_purchase[cid]:
            first_purchase[cid] = mois

    customer_months = defaultdict(set)
    for cid, created_at in sales:
        customer_months[cid].add(created_at.strftime("%Y-%m"))

    cohort_customers = defaultdict(list)
    for cid, cohort_mois in first_purchase.items():
        cohort_customers[cohort_mois].append(cid)

    cohorts_sorted = sorted(cohort_customers.keys())

    result_cohorts = []
    max_months_seen = 0
    for cohort_mois in cohorts_sorted:
        members = cohort_customers[cohort_mois]
        size = len(members)
        if size == 0:
            continue

        cy, cm = int(cohort_mois[:4]), int(cohort_mois[5:7])

        retention = []
        for delta in range(nb_months + 1):
            target_total = cy * 12 + cm - 1 + delta
            ty, tm = divmod(target_total, 12)
            tm += 1
            target_mois = f"{ty:04d}-{tm:02d}"

            count = sum(1 for cid in members if target_mois in customer_months[cid])
            rate = round(count / size * 100, 1)
            retention.append({"month": delta, "month_label": target_mois, "count": count, "rate": rate})
            if count > 0:
                max_months_seen = max(max_months_seen, delta)

        result_cohorts.append({
            "cohort": cohort_mois,
            "size": size,
            "retention": retention,
        })

    return jsonify({
        "cohorts": result_cohorts,
        "max_months": max_months_seen,
    })


# ---------------------------------------------------------------------------
# Customer Lifetime Value (CLV) — Feature F
# ---------------------------------------------------------------------------

@analytics_bp.get("/clv")
@require_permission("analytics:read")
def clv_view():
    """Valeur vie client (CLV) estimee.

    CLV = panier_moyen x frequence_achats_mensuelle x duree_vie_estimee_mois

    Parametres GET :
        limit   : nombre max de clients (defaut 50, max 200)
        min_clv : CLV minimum pour filtrer (defaut 0)
    """
    try:
        limit = max(1, min(int(request.args.get("limit", 50)), 200))
    except ValueError:
        limit = 50
    try:
        min_clv = float(request.args.get("min_clv", 0))
    except ValueError:
        min_clv = 0.0

    rows = (
        db.session.query(
            Sale.customer_id,
            db.func.count(Sale.id).label("nb_commandes"),
            db.func.sum(Sale.total).label("ca_total"),
            db.func.min(Sale.created_at).label("premier_achat"),
            db.func.max(Sale.created_at).label("dernier_achat"),
        )
        .filter(
            Sale.status == SaleStatus.VALIDEE.value,
            Sale.customer_id.isnot(None),
        )
        .group_by(Sale.customer_id)
        .having(db.func.count(Sale.id) >= 1)
        .all()
    )

    if not rows:
        return jsonify({"items": [], "count": 0, "stats": {"clv_moyen": 0, "clv_median": 0, "clv_max": 0, "clv_min": 0}})

    customer_ids = [r.customer_id for r in rows]
    customers = {c.id: c for c in Customer.query.filter(Customer.id.in_(customer_ids)).all()}

    clv_list = []
    for row in rows:
        customer = customers.get(row.customer_id)
        if not customer:
            continue

        ca_total = float(row.ca_total or 0)
        nb = row.nb_commandes
        panier_moyen = ca_total / nb if nb else 0

        premier = row.premier_achat
        dernier = row.dernier_achat
        if premier and dernier and premier != dernier:
            delta = (dernier.year - premier.year) * 12 + (dernier.month - premier.month)
            duree_mois = max(1, delta)
        else:
            duree_mois = 1

        frequence_mensuelle = nb / duree_mois

        # Durée de vie estimée plafonnée par le nombre d'achats pour éviter
        # des CLV irréalistes sur les clients à achat unique.
        # 1 achat  → max  6 mois (confiance faible)
        # 2 achats → max 12 mois
        # 4 achats → max 24 mois (confiance pleine)
        # Extrapolation : duree_mois * 2, plafonné à 36 mois globalement.
        duree_vie_par_nb = nb * 6          # 6 mois de crédit par achat
        duree_vie_historique = duree_mois * 2
        duree_vie_estimee_mois = max(3, min(36, duree_vie_par_nb, duree_vie_historique))
        # Au moins 3 mois pour ne pas générer un CLV nul sur de très petits paniers
        if nb >= 4:
            # Client bien établi : on accepte l'extrapolation historique jusqu'à 36 mois
            duree_vie_estimee_mois = max(6, min(36, duree_vie_historique))

        # Indice de confiance dans l'estimation (0-1)
        data_confidence = round(min(1.0, nb / 5), 2)

        clv = panier_moyen * frequence_mensuelle * duree_vie_estimee_mois

        if clv < min_clv:
            continue

        clv_list.append({
            "customer_id": row.customer_id,
            "name": customer.full_name,
            "customer_type": customer.customer_type if hasattr(customer, "customer_type") else "",
            "nb_commandes": nb,
            "ca_total": round(ca_total, 2),
            "panier_moyen": round(panier_moyen, 2),
            "premier_achat": premier.date().isoformat() if premier else None,
            "dernier_achat": dernier.date().isoformat() if dernier else None,
            "duree_mois": duree_mois,
            "frequence_mensuelle": round(frequence_mensuelle, 3),
            "clv_estime": round(clv, 2),
            "duree_vie_estimee_mois": duree_vie_estimee_mois,
            "data_confidence": data_confidence,
        })

    clv_list.sort(key=lambda x: x["clv_estime"], reverse=True)
    clv_list = clv_list[:limit]

    if clv_list:
        clv_values = [c["clv_estime"] for c in clv_list]
        stats = {
            "clv_moyen": round(sum(clv_values) / len(clv_values), 2),
            "clv_median": round(sorted(clv_values)[len(clv_values) // 2], 2),
            "clv_max": round(max(clv_values), 2),
            "clv_min": round(min(clv_values), 2),
        }
    else:
        stats = {"clv_moyen": 0, "clv_median": 0, "clv_max": 0, "clv_min": 0}

    return jsonify({
        "items": clv_list,
        "count": len(clv_list),
        "stats": stats,
    })
