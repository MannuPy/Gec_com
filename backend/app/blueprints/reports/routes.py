"""Routes du blueprint `reports` : indicateurs synthetiques pour le tableau de bord."""
import json
import time as time_module
from datetime import datetime, time

from flask import current_app, jsonify, request, stream_with_context, Response
from sqlalchemy import func

from app.extensions import db
from app.blueprints.reports import reports_bp
from app.models import Product, Sale, SaleStatus, Stock
from app.services.analytics_service import compute_dashboard, compute_dashboard_realtime, top_products_for_period
from app.utils.decorators import require_permission
from app.utils.pdf import build_dashboard_report_pdf, pdf_response


@reports_bp.get("/dashboard")
@require_permission("reports:read")
def dashboard_summary():
    """Indicateurs cles du jour : ventes, panier moyen, alertes de stock (RF-23)."""
    branch_id = request.args.get("branch_id")

    today_start = datetime.combine(datetime.utcnow().date(), time.min)

    sales_query = Sale.query.filter(
        Sale.status == SaleStatus.VALIDEE.value, Sale.created_at >= today_start
    )
    if branch_id:
        sales_query = sales_query.filter(Sale.branch_id == branch_id)

    sales_today = sales_query.all()
    sales_count = len(sales_today)
    sales_total = sum((sale.total for sale in sales_today), start=0)
    average_basket = (sales_total / sales_count) if sales_count else 0

    stock_query = db.session.query(Stock).join(Product)
    if branch_id:
        stock_query = stock_query.filter(Stock.branch_id == branch_id)

    low_stock_count = stock_query.filter(Stock.quantity < Product.min_stock_threshold).count()

    # Top produits vendus aujourd'hui (par quantite)
    from app.models import SaleLine  # import local pour eviter un cycle au chargement du module

    top_products = (
        db.session.query(
            Product.id,
            Product.name,
            Product.sku,
            func.coalesce(func.sum(SaleLine.quantity), 0).label("total_quantity"),
        )
        .join(SaleLine, SaleLine.product_id == Product.id)
        .join(Sale, Sale.id == SaleLine.sale_id)
        .filter(Sale.status == SaleStatus.VALIDEE.value, Sale.created_at >= today_start)
    )
    if branch_id:
        top_products = top_products.filter(Sale.branch_id == branch_id)

    top_products = (
        top_products.group_by(Product.id, Product.name, Product.sku)
        .order_by(func.sum(SaleLine.quantity).desc())
        .limit(5)
        .all()
    )

    return jsonify({
        "sales_today_total": str(sales_total),
        "sales_today_count": sales_count,
        "average_basket": str(average_basket),
        "low_stock_count": low_stock_count,
        "top_products_today": [
            {"product_id": p.id, "name": p.name, "sku": p.sku, "quantity_sold": int(p.total_quantity)}
            for p in top_products
        ],
    })


@reports_bp.get("/dashboard/realtime")
@require_permission("reports:read")
def dashboard_realtime():
    """Snapshot temps reel du tableau de bord (section 22.2/22.5) : KPIs (CA jour/mois,
    marge, panier moyen), alertes IA (rupture de stock, anomalies, clients a
    risque), ABC/XYZ et segmentation RFM.

    Utilise pour le chargement initial et comme repli "polling" par le hook
    frontend `useDashboardStream` lorsque le flux SSE (`/dashboard/stream`)
    est indisponible.
    """
    branch_id = request.args.get("branch_id")
    return jsonify(compute_dashboard_realtime(branch_id=branch_id))


@reports_bp.get("/dashboard/stream")
@require_permission("reports:read")
def dashboard_stream():
    """Flux temps reel (Server-Sent Events) du tableau de bord (section 22.2, adapte
    en SSE/polling - cf. decision projet : pas de WebSocket/Redis pub-sub).

    Pousse periodiquement (`DASHBOARD_STREAM_INTERVAL_SECONDS`) le meme
    payload que `GET /reports/dashboard/realtime`, sous forme d'evenements
    `event: dashboard`. Le flux se referme apres
    `DASHBOARD_STREAM_MAX_EVENTS` iterations afin de liberer le worker HTTP ;
    `useDashboardStream` (frontend) se reconnecte alors automatiquement.

    `stream_with_context` conserve le contexte de requete (et donc le
    `search_path` PostgreSQL du tenant courant, cf. `app/middleware/tenant.py`)
    pendant toute la duree du flux.
    """
    branch_id = request.args.get("branch_id")
    interval = current_app.config.get("DASHBOARD_STREAM_INTERVAL_SECONDS", 5)
    max_events = current_app.config.get("DASHBOARD_STREAM_MAX_EVENTS", 60)

    @stream_with_context
    def event_stream():
        yield ": connected\n\n"
        for _ in range(max_events):
            try:
                payload = compute_dashboard_realtime(branch_id=branch_id)
                yield f"event: dashboard\ndata: {json.dumps(payload, default=str)}\n\n"
            except Exception as exc:  # ne jamais casser le flux SSE
                current_app.logger.exception("dashboard_stream: erreur de calcul du snapshot")
                yield f"event: error\ndata: {json.dumps({'message': str(exc)})}\n\n"
            time_module.sleep(interval)
        yield ": closing\n\n"

    return Response(
        event_stream(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@reports_bp.get("/export")
@require_permission("reports:read")
def export_report_pdf():
    """Export PDF du tableau de bord etendu : marges, multi-site, consolide (RF-29)."""
    branch_id = request.args.get("branch_id")
    try:
        days = int(request.args.get("days", 30))
    except ValueError:
        days = 30

    dashboard_data = compute_dashboard(branch_id=branch_id, days=days)
    products = top_products_for_period(branch_id=branch_id, days=days)

    buffer = build_dashboard_report_pdf(dashboard_data, top_products=products)
    return pdf_response(buffer, filename=f"rapport-ventes-{days}j.pdf")
