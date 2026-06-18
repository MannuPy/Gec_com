"""Routes du blueprint `inventory` : inventaire physique (RF-21 à RF-23).

Cycle de vie d'une session d'inventaire :
1. `POST /inventory/counts` — ouverture d'une session (EN_COURS), une ligne
   `stock_count_lines` est créée par produit actif présent en stock sur le
   site, avec `theoretical_quantity` figée au moment de l'ouverture.
2. `PATCH /inventory/counts/<id>/lines` — saisie des quantités comptées
   (RF-22). Tout écart dont la valeur absolue dépasse
   `INVENTORY_VARIANCE_THRESHOLD_PCT` (RG-33) nécessite un commentaire de
   justification.
3. `POST /inventory/counts/<id>/validate` — validation (RF-23) : la session
   passe à VALIDE et un mouvement `AJUSTEMENT_INVENTAIRE` est généré pour
   chaque ligne dont l'écart est non nul, alignant le stock théorique sur le
   stock compté.
"""
from datetime import datetime

from flask import current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity

from app.blueprints.inventory import inventory_bp
from app.blueprints.inventory.schemas import (
    StockCountCreateSchema,
    StockCountDetailSchema,
    StockCountLinesUpdateSchema,
    StockCountSchema,
)
from app.extensions import db
from app.models import (
    Branch,
    Product,
    Stock,
    StockCount,
    StockCountLine,
    StockCountStatus,
    StockMovementType,
)
from app.services.reference_service import generate_reference
from app.services.stock_service import apply_stock_movement
from app.utils.decorators import require_permission
from app.utils.errors import conflict, not_found, validation_error

stock_count_list_schema = StockCountSchema(many=True)
stock_count_detail_schema = StockCountDetailSchema()


@inventory_bp.get("/counts")
@require_permission("inventory:read")
def list_stock_counts():
    """Liste des sessions d'inventaire, filtrables par site et statut."""
    query = StockCount.query

    branch_id = request.args.get("branch_id")
    if branch_id:
        query = query.filter(StockCount.branch_id == branch_id)

    status = request.args.get("status")
    if status:
        query = query.filter(StockCount.status == status)

    page = request.args.get("page", default=1, type=int)
    per_page = min(request.args.get("per_page", default=20, type=int), 100)

    pagination = query.order_by(StockCount.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify(
        {
            "data": stock_count_list_schema.dump(pagination.items),
            "meta": {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total": pagination.total,
            },
        }
    )


@inventory_bp.get("/counts/<string:count_id>")
@require_permission("inventory:read")
def get_stock_count(count_id: str):
    """Détail d'une session d'inventaire avec ses lignes."""
    stock_count = StockCount.query.get(count_id)
    if stock_count is None:
        raise not_found("Session d'inventaire", count_id)
    return jsonify(stock_count_detail_schema.dump(stock_count))


@inventory_bp.post("/counts")
@require_permission("inventory:write")
def create_stock_count():
    """Ouvre une nouvelle session d'inventaire (RF-21).

    Une ligne est créée pour chaque produit actif disposant d'une ligne de
    stock sur le site (y compris à 0), avec `theoretical_quantity` figée au
    moment de l'ouverture.
    """
    payload = StockCountCreateSchema().load(request.get_json(silent=True) or {})

    branch = Branch.query.get(payload["branch_id"])
    if branch is None:
        raise not_found("Site", payload["branch_id"])

    existing = StockCount.query.filter_by(
        branch_id=branch.id, status=StockCountStatus.EN_COURS.value
    ).first()
    if existing is not None:
        raise conflict(
            "STOCK_COUNT_IN_PROGRESS",
            "Une session d'inventaire est déjà en cours pour ce site.",
            details={"stock_count_id": existing.id, "reference": existing.reference},
        )

    stock_count = StockCount(
        reference=generate_reference("INV"),
        branch_id=branch.id,
        status=StockCountStatus.EN_COURS.value,
        created_by_id=get_jwt_identity(),
    )
    db.session.add(stock_count)
    db.session.flush()

    stock_rows = (
        Stock.query.join(Product)
        .filter(Stock.branch_id == branch.id, Product.is_active.is_(True))
        .all()
    )
    for stock in stock_rows:
        db.session.add(
            StockCountLine(
                stock_count_id=stock_count.id,
                product_id=stock.product_id,
                theoretical_quantity=stock.quantity,
            )
        )

    db.session.commit()
    return jsonify(stock_count_detail_schema.dump(stock_count)), 201


@inventory_bp.patch("/counts/<string:count_id>/lines")
@require_permission("inventory:write")
def update_stock_count_lines(count_id: str):
    """Saisit les quantités comptées (RF-22) et calcule les écarts.

    RG-33 : tout écart dont la valeur absolue (en %) dépasse
    `INVENTORY_VARIANCE_THRESHOLD_PCT` doit être accompagné d'un commentaire
    de justification.
    """
    stock_count = StockCount.query.get(count_id)
    if stock_count is None:
        raise not_found("Session d'inventaire", count_id)

    if stock_count.status != StockCountStatus.EN_COURS.value:
        raise conflict(
            "STOCK_COUNT_NOT_EDITABLE",
            "Cette session d'inventaire n'est plus modifiable (déjà validée).",
        )

    payload = StockCountLinesUpdateSchema().load(request.get_json(silent=True) or {})
    threshold_pct = current_app.config.get("INVENTORY_VARIANCE_THRESHOLD_PCT", 5)

    lines_by_product = {line.product_id: line for line in stock_count.lines}

    for entry in payload["lines"]:
        line = lines_by_product.get(entry["product_id"])
        if line is None:
            raise not_found("Ligne d'inventaire pour le produit", entry["product_id"])

        counted = entry["counted_quantity"]
        variance = counted - line.theoretical_quantity
        base = line.theoretical_quantity or 1
        variance_pct = abs(variance) / base * 100

        comment = entry.get("comment")
        if variance != 0 and variance_pct > threshold_pct and not comment:
            raise validation_error(
                f"Un écart de {variance:+d} ({variance_pct:.1f}%) sur le produit "
                f"'{line.product.name}' dépasse le seuil de {threshold_pct}% et "
                f"doit être justifié (champ 'comment').",
                details={"product_id": entry["product_id"], "variance": variance, "variance_pct": round(variance_pct, 2)},
            )

        line.counted_quantity = counted
        line.variance = variance
        if comment:
            line.comment = comment

    db.session.commit()
    return jsonify(stock_count_detail_schema.dump(stock_count))


@inventory_bp.post("/counts/<string:count_id>/validate")
@require_permission("inventory:write")
def validate_stock_count(count_id: str):
    """Valide la session d'inventaire (RF-23).

    Pour chaque ligne ayant une quantité comptée et un écart non nul, génère
    un mouvement `AJUSTEMENT_INVENTAIRE` alignant le stock théorique sur le
    stock compté. Les lignes non comptées sont ignorées (laissées au stock
    théorique).
    """
    stock_count = StockCount.query.get(count_id)
    if stock_count is None:
        raise not_found("Session d'inventaire", count_id)

    if stock_count.status != StockCountStatus.EN_COURS.value:
        raise conflict(
            "STOCK_COUNT_ALREADY_VALIDATED",
            "Cette session d'inventaire a déjà été validée.",
        )

    uncounted = [line for line in stock_count.lines if line.counted_quantity is None]
    if uncounted:
        raise validation_error(
            f"{len(uncounted)} produit(s) n'ont pas encore été comptés.",
            details={"product_ids": [line.product_id for line in uncounted]},
        )

    user_id = get_jwt_identity()
    adjustments = 0
    for line in stock_count.lines:
        if line.variance:
            apply_stock_movement(
                product_id=line.product_id,
                branch_id=stock_count.branch_id,
                quantity=line.variance,
                movement_type=StockMovementType.AJUSTEMENT_INVENTAIRE.value,
                reference_type="STOCK_COUNT",
                reference_id=stock_count.id,
                created_by_id=user_id,
                comment=line.comment or f"Régularisation inventaire {stock_count.reference}",
                allow_negative=True,
            )
            adjustments += 1

    stock_count.status = StockCountStatus.VALIDE.value
    db.session.commit()
    return jsonify(stock_count_detail_schema.dump(stock_count))
