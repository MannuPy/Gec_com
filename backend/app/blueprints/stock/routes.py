"""Routes du blueprint `stock` : consultation et ajustements manuels."""
from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity

from app.blueprints.stock import stock_bp
from app.blueprints.stock.schemas import (
    StockAdjustmentSchema,
    StockItemSchema,
    StockMovementSchema,
)
from app.extensions import db
from app.models import Branch, Product, Stock, StockMovement, StockMovementType
from app.services.stock_service import apply_stock_movement
from app.utils.dates import parse_updated_since
from app.utils.decorators import require_permission
from app.utils.errors import not_found

stock_item_schema = StockItemSchema(many=True)
stock_movement_schema = StockMovementSchema(many=True)
stock_movement_single_schema = StockMovementSchema()


@stock_bp.get("")
@require_permission("stock:read", "products:read", "sales:create")
def list_stock():
    """Niveaux de stock, filtrables par site et par seuil minimum (RG-38)."""
    # Jointures explicites via les attributs de relation pour eviter le
    # conflit avec lazy="joined" defini sur le modele (SQLAlchemy 2.x).
    query = (
        db.session.query(Stock)
        .join(Stock.product)
        .join(Stock.branch)
    )

    branch_id = request.args.get("branch_id")
    if branch_id:
        query = query.filter(Stock.branch_id == branch_id)

    below_min = request.args.get("below_min")
    if below_min is not None and below_min.lower() in ("1", "true", "yes"):
        query = query.filter(Stock.quantity < Product.min_stock_threshold)

    updated_since = parse_updated_since(request.args.get("updated_since"))
    if updated_since is not None:
        query = query.filter(Stock.updated_at >= updated_since)

    items = query.order_by(Product.name).all()
    return jsonify(stock_item_schema.dump(items))


@stock_bp.get("/movements")
@require_permission("stock:read", "products:read")
def list_movements():
    """Historique des mouvements de stock (tracabilite, RG-17/RG-24)."""
    query = StockMovement.query

    branch_id = request.args.get("branch_id")
    if branch_id:
        query = query.filter(StockMovement.branch_id == branch_id)

    product_id = request.args.get("product_id")
    if product_id:
        query = query.filter(StockMovement.product_id == product_id)

    page = request.args.get("page", default=1, type=int)
    per_page = min(request.args.get("per_page", default=50, type=int), 200)

    pagination = query.order_by(StockMovement.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        "data": stock_movement_schema.dump(pagination.items),
        "meta": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
        },
    })


@stock_bp.post("/adjustments")
@require_permission("stock:write")
def create_adjustment():
    """Ajustement manuel de stock (inventaire, casse, perte) - RG-24."""
    payload = StockAdjustmentSchema().load(request.get_json(silent=True) or {})

    if db.session.get(Product, payload["product_id"]) is None:
        raise not_found("Produit", payload["product_id"])

    if db.session.get(Branch, payload["branch_id"]) is None:
        raise not_found("Site", payload["branch_id"])

    movement = apply_stock_movement(
        product_id=payload["product_id"],
        branch_id=payload["branch_id"],
        quantity=payload["quantity_delta"],
        movement_type=StockMovementType.AJUSTEMENT_MANUEL.value,
        reference_type="ADJUSTMENT",
        created_by_id=get_jwt_identity(),
        comment=payload["comment"],
    )
    return jsonify({"message": "Ajustement de stock effectue."})
