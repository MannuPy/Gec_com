"""Calculs partages du tableau de bord etendu (RF-24)."""
from __future__ import annotations

from datetime import datetime, time, timedelta

from sqlalchemy import func

from app.extensions import db
from app.models import Branch, Product, Sale, SaleLine, SaleStatus


def compute_dashboard(branch_id=None, days: int = 30) -> dict:
    """Indicateurs etendus : marges, ventilation multi-site, consolide (RF-24)."""
    days = max(1, min(int(days), 365))
    period_start = datetime.combine((datetime.utcnow() - timedelta(days=days - 1)).date(), time.min)

    revenue_query = (
        db.session.query(
            Sale.branch_id,
            Branch.name.label("branch_name"),
            func.coalesce(func.sum(Sale.total), 0).label("revenue"),
            func.count(Sale.id).label("sales_count"),
        )
        .join(Branch, Branch.id == Sale.branch_id)
        .filter(Sale.status == SaleStatus.VALIDEE.value, Sale.created_at >= period_start)
        .group_by(Sale.branch_id, Branch.name)
    )
    if branch_id:
        revenue_query = revenue_query.filter(Sale.branch_id == branch_id)

    branch_rows = revenue_query.all()

    cost_query = (
        db.session.query(
            Sale.branch_id,
            func.coalesce(func.sum(SaleLine.quantity * Product.purchase_price), 0).label("cost"),
        )
        .join(SaleLine, SaleLine.sale_id == Sale.id)
        .join(Product, Product.id == SaleLine.product_id)
        .filter(Sale.status == SaleStatus.VALIDEE.value, Sale.created_at >= period_start)
        .group_by(Sale.branch_id)
    )
    if branch_id:
        cost_query = cost_query.filter(Sale.branch_id == branch_id)

    costs = {row.branch_id: row.cost for row in cost_query.all()}

    branches_data = []
    consolidated_revenue = 0
    consolidated_cost = 0
    consolidated_sales = 0
    for row in branch_rows:
        revenue = row.revenue or 0
        cost = costs.get(row.branch_id, 0) or 0
        margin = revenue - cost
        margin_rate = float(margin) / float(revenue) * 100 if revenue else 0
        branches_data.append(
            {
                "branch_id": row.branch_id,
                "branch_name": row.branch_name,
                "sales_count": row.sales_count,
                "revenue": str(revenue),
                "cost": str(cost),
                "margin": str(margin),
                "margin_rate_pct": round(margin_rate, 2),
            }
        )
        consolidated_revenue += revenue
        consolidated_cost += cost
        consolidated_sales += row.sales_count

    consolidated_margin = consolidated_revenue - consolidated_cost
    consolidated_margin_rate = (
        float(consolidated_margin) / float(consolidated_revenue) * 100 if consolidated_revenue else 0
    )

    return {
        "period_days": days,
        "period_start": period_start.isoformat(),
        "branches": branches_data,
        "consolidated": {
            "sales_count": consolidated_sales,
            "revenue": str(consolidated_revenue),
            "cost": str(consolidated_cost),
            "margin": str(consolidated_margin),
            "margin_rate_pct": round(consolidated_margin_rate, 2),
        },
    }


def compute_dashboard_realtime(branch_id=None) -> dict:
    """Snapshot temps reel du tableau de bord."""
    from app.ml import abc_xyz, anomaly_detection, credit_scoring, demand_forecast, rfm_segmentation

    now = datetime.utcnow()
    today_start = datetime.combine(now.date(), time.min)
    month_start = datetime.combine(now.date().replace(day=1), time.min)

    def _period_kpis(period_start: datetime):
        revenue_query = db.session.query(
            func.coalesce(func.sum(Sale.total), 0).label("revenue"),
            func.count(Sale.id).label("sales_count"),
        ).filter(Sale.status == SaleStatus.VALIDEE.value, Sale.created_at >= period_start)
        if branch_id:
            revenue_query = revenue_query.filter(Sale.branch_id == branch_id)
        revenue_row = revenue_query.one()

        cost_query = (
            db.session.query(func.coalesce(func.sum(SaleLine.quantity * Product.purchase_price), 0))
            .join(Sale, Sale.id == SaleLine.sale_id)
            .join(Product, Product.id == SaleLine.product_id)
            .filter(Sale.status == SaleStatus.VALIDEE.value, Sale.created_at >= period_start)
        )
        if branch_id:
            cost_query = cost_query.filter(Sale.branch_id == branch_id)
        cost = cost_query.scalar() or 0

        revenue = revenue_row.revenue or 0
        sales_count = revenue_row.sales_count or 0
        margin = revenue - cost
        margin_rate = float(margin) / float(revenue) * 100 if revenue else 0.0
        return revenue, sales_count, margin_rate

    ca_jour, sales_count_jour, _ = _period_kpis(today_start)
    ca_mois, _, marge_pct_mois = _period_kpis(month_start)
    panier_moyen = (ca_jour / sales_count_jour) if sales_count_jour else 0

    alerts = []

    for item in demand_forecast.latest(alerts_only=True):
        if branch_id and item.get("branch_id") != branch_id:
            continue
        stock_disponible = item.get("stock_disponible", 0)
        alerts.append(
            {
                "type": "RUPTURE_STOCK",
                "severity": "CRITICAL" if stock_disponible <= 0 else "WARNING",
                "message": "Rupture prevue : " + str(item.get("product_name")) + " (stock " + str(stock_disponible) + ", qte recommandee " + str(item.get("quantite_recommandee")) + ")",
                "entity_id": item.get("product_id"),
            }
        )

    for item in anomaly_detection.latest():
        if branch_id and item.get("branch_id") != branch_id:
            continue
        reasons = ", ".join(item.get("reasons", [])) or "Profil statistique atypique"
        alerts.append(
            {
                "type": "ANOMALIE",
                "severity": "WARNING",
                "message": "Vente atypique " + str(item.get("reference")) + " : " + reasons,
                "entity_id": item.get("sale_id"),   # sale_id exposé par anomaly_detection.latest()
            }
        )

    for item in credit_scoring.latest():
        if item.get("risk_level") != "ELEVE":
            continue
        alerts.append(
            {
                "type": "CREDIT_RISK",
                "severity": "WARNING",
                "message": "Client a risque : " + str(item.get("customer_name")) + " (score " + str(item.get("score")) + ")",
                "entity_id": item.get("customer_id"),
            }
        )

    return {
        "generated_at": now.isoformat(),
        "kpis": {
            "ca_jour": str(ca_jour),
            "ca_mois": str(ca_mois),
            "marge_pct": round(marge_pct_mois, 2),
            "panier_moyen": str(panier_moyen),
        },
        "alerts": alerts,
        "abc_xyz": abc_xyz.latest(),
        "rfm_segments": rfm_segmentation.latest(),
    }


def compute_sales_trend(branch_id=None, days: int = 30) -> list:
    """Tendance des ventes jour par jour sur la periode donnee."""
    from app.models import SaleLine as SL
    days = max(1, min(int(days), 365))
    period_start = datetime.combine((datetime.utcnow() - timedelta(days=days - 1)).date(), time.min)

    revenue_q = (
        db.session.query(
            func.date(Sale.created_at).label("day"),
            func.coalesce(func.sum(Sale.total), 0).label("revenue"),
            func.count(Sale.id).label("sales_count"),
        )
        .filter(Sale.status == SaleStatus.VALIDEE.value, Sale.created_at >= period_start)
        .group_by(func.date(Sale.created_at))
    )
    if branch_id:
        revenue_q = revenue_q.filter(Sale.branch_id == branch_id)

    revenue_rows = {str(r.day): {"revenue": float(r.revenue), "sales_count": r.sales_count}
                   for r in revenue_q.all()}

    cost_q = (
        db.session.query(
            func.date(Sale.created_at).label("day"),
            func.coalesce(func.sum(SL.quantity * Product.purchase_price), 0).label("cost"),
        )
        .join(SL, SL.sale_id == Sale.id)
        .join(Product, Product.id == SL.product_id)
        .filter(Sale.status == SaleStatus.VALIDEE.value, Sale.created_at >= period_start)
        .group_by(func.date(Sale.created_at))
    )
    if branch_id:
        cost_q = cost_q.filter(Sale.branch_id == branch_id)

    cost_rows = {str(r.day): float(r.cost) for r in cost_q.all()}

    result = []
    for i in range(days):
        day = (datetime.utcnow() - timedelta(days=days - 1 - i)).date()
        day_str = str(day)
        rev_data = revenue_rows.get(day_str, {"revenue": 0.0, "sales_count": 0})
        cost = cost_rows.get(day_str, 0.0)
        revenue = rev_data["revenue"]
        result.append({
            "date": day_str,
            "revenue": round(revenue, 2),
            "sales_count": rev_data["sales_count"],
            "margin": round(revenue - cost, 2),
        })

    return result


def top_products_for_period(branch_id=None, days: int = 30, limit: int = 10) -> list:
    """Produits les plus vendus (par quantite) sur la periode donnee."""
    days = max(1, min(int(days), 365))
    period_start = datetime.combine((datetime.utcnow() - timedelta(days=days - 1)).date(), time.min)

    query = (
        db.session.query(
            Product.id,
            Product.name,
            Product.sku,
            func.coalesce(func.sum(SaleLine.quantity), 0).label("total_quantity"),
        )
        .join(SaleLine, SaleLine.product_id == Product.id)
        .join(Sale, Sale.id == SaleLine.sale_id)
        .filter(Sale.status == SaleStatus.VALIDEE.value, Sale.created_at >= period_start)
    )
    if branch_id:
        query = query.filter(Sale.branch_id == branch_id)

    rows = (
        query.group_by(Product.id, Product.name, Product.sku)
        .order_by(db.desc("total_quantity"))
        .limit(limit)
        .all()
    )
    return [
        {"product_id": r[0], "product_name": r[1], "sku": r[2], "total_quantity": int(r[3])}
        for r in rows
    ]
