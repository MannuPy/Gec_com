"""Routes du blueprint `inventory` : inventaire physique (RF-21 a RF-23)."""
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
    AuditLog,
    Branch,
    Product,
    Stock,
    StockCount,
    StockCountLine,
    StockCountStatus,
    StockMovementType,
)
from app.services.reference_service import generate_reference
from app.services.stock_service import apply_stock_movement, get_or_create_stock_row
from app.utils.decorators import require_permission
from app.utils.errors import conflict, not_found, validation_error

stock_count_list_schema = StockCountSchema(many=True)
stock_count_detail_schema = StockCountDetailSchema()


@inventory_bp.get("/counts")
@require_permission("inventory:read")
def list_stock_counts():
    """Liste des sessions d inventaire, filtrables par site et statut.

    Optimisation MySQL/PythonAnywhere : les lignes (stock_count_lines) ne sont
    PAS chargees en liste — elles sont agregees via sous-requetes SQL pour
    calculer lines_count et lines_with_variance sans faire exploser les JOIN.
    """
    from sqlalchemy import func, case
    from sqlalchemy.orm import joinedload, load_only

    query = (
        db.session.query(StockCount)
        .options(
            # Charger seulement les relations legeres (branch, created_by, etc.)
            joinedload(StockCount.branch).load_only("id", "name"),
            joinedload(StockCount.created_by).load_only("id", "full_name"),
            joinedload(StockCount.validated_by).load_only("id", "full_name"),
            joinedload(StockCount.cancelled_by).load_only("id", "full_name"),
            # NE PAS charger les lignes en liste (trop lourd) — calcul via schema
        )
    )

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

    return jsonify({
        "data": stock_count_list_schema.dump(pagination.items),
        "meta": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
        },
    })


@inventory_bp.get("/counts/<string:count_id>")
@require_permission("inventory:read")
def get_stock_count(count_id: str):
    """Detail d une session d inventaire avec ses lignes."""
    stock_count = db.session.get(StockCount, count_id)
    if stock_count is None:
        raise not_found("Session d inventaire", count_id)
    return jsonify(stock_count_detail_schema.dump(stock_count))


@inventory_bp.post("/counts")
@require_permission("inventory:write")
def create_stock_count():
    """Ouvre une nouvelle session d inventaire (RF-21)."""
    payload = StockCountCreateSchema().load(request.get_json(silent=True) or {})

    branch = db.session.get(Branch, payload["branch_id"])
    if branch is None:
        raise not_found("Site", payload["branch_id"])

    existing = StockCount.query.filter_by(
        branch_id=branch.id, status=StockCountStatus.EN_COURS.value
    ).first()
    if existing is not None:
        raise conflict(
            "STOCK_COUNT_IN_PROGRESS",
            "Une session d inventaire est deja en cours pour ce site.",
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

    # Fix Bug #1 : utiliser des jointures explicites pour eviter le double-JOIN
    # genere par lazy="joined" + Stock.query.join(Product) (SQLAlchemy 2.x).
    stock_rows = (
        db.session.query(Stock)
        .join(Stock.product)
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
    """Saisit les quantites comptees (RF-22) et calcule les ecarts."""
    stock_count = db.session.get(StockCount, count_id)
    if stock_count is None:
        raise not_found("Session d inventaire", count_id)

    if stock_count.status != StockCountStatus.EN_COURS.value:
        raise conflict(
            "STOCK_COUNT_NOT_EDITABLE",
            "Cette session d inventaire n est plus modifiable "
            "(statut actuel : " + stock_count.status + ").",
        )

    payload = StockCountLinesUpdateSchema().load(request.get_json(silent=True) or {})
    threshold_pct = current_app.config.get("INVENTORY_VARIANCE_THRESHOLD_PCT", 5)

    lines_by_product = {line.product_id: line for line in stock_count.lines}

    for entry in payload["lines"]:
        line = lines_by_product.get(entry["product_id"])
        if line is None:
            raise not_found("Ligne d inventaire pour le produit", entry["product_id"])

        counted = entry["counted_quantity"]
        variance = counted - line.theoretical_quantity
        base = line.theoretical_quantity or 1
        variance_pct = abs(variance) / base * 100

        comment = entry.get("comment")
        if variance != 0 and variance_pct > threshold_pct and not comment:
            raise validation_error(
                "Ecart de " + str(variance) + " (" + str(round(variance_pct, 1)) + "%) "
                "sur le produit '" + line.product.name + "' : "
                "depasse le seuil de " + str(threshold_pct) + "%, justification requise.",
                details={"product_id": entry["product_id"], "variance": variance,
                         "variance_pct": round(variance_pct, 2)},
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
    """Valide la session d inventaire et ajuste le stock (RF-23).

    Fix Bug #2 : recalcule le delta reel au moment de la validation
    (counted_quantity - stock_actuel) plutot que d utiliser line.variance
    (counted - stock_theorique_au_moment_de_la_creation).

    Cela garantit que le stock final = counted_quantity >= 0,
    ce qui ne peut jamais violer la contrainte CHECK (quantity >= 0).
    Des ventes ou transferts peuvent avoir eu lieu pendant la saisie
    de l inventaire ; le delta reel tient compte de ces mouvements.
    """
    stock_count = db.session.get(StockCount, count_id)
    if stock_count is None:
        raise not_found("Session d inventaire", count_id)

    if stock_count.status != StockCountStatus.EN_COURS.value:
        raise conflict(
            "STOCK_COUNT_NOT_VALIDATABLE",
            "Seule une session EN_COURS peut etre validee "
            "(statut actuel : " + stock_count.status + ").",
        )

    uncounted = [line for line in stock_count.lines if line.counted_quantity is None]
    if uncounted:
        raise validation_error(
            str(len(uncounted)) + " produit(s) n ont pas encore ete comptes.",
            details={"product_ids": [line.product_id for line in uncounted]},
        )

    user_id = get_jwt_identity()
    for line in stock_count.lines:
        # Recalcul du delta reel : stock actuel en base peut differ du stock
        # theorique si des mouvements ont eu lieu pendant la saisie.
        # delta_reel = counted - stock_actuel
        # stock_final = stock_actuel + delta_reel = counted >= 0
        # => jamais de violation de la contrainte CHECK (quantity >= 0).
        current_stock = get_or_create_stock_row(line.product_id, stock_count.branch_id)
        actual_delta = line.counted_quantity - current_stock.quantity

        if actual_delta != 0:
            apply_stock_movement(
                product_id=line.product_id,
                branch_id=stock_count.branch_id,
                quantity=actual_delta,
                movement_type=StockMovementType.AJUSTEMENT_INVENTAIRE.value,
                reference_type="STOCK_COUNT",
                reference_id=stock_count.id,
                created_by_id=user_id,
                comment="Regularisation inventaire " + stock_count.reference
                    + " (theorique=" + str(line.theoretical_quantity)
                    + ", compte=" + str(line.counted_quantity) + ")",
                allow_negative=False,
            )

    stock_count.status = StockCountStatus.VALIDE.value
    stock_count.validated_by_id = user_id
    stock_count.validated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(stock_count_detail_schema.dump(stock_count))


@inventory_bp.post("/counts/<string:count_id>/cancel")
@require_permission("inventory:write")
def cancel_stock_count(count_id: str):
    """Annule (abandonne) une session EN_COURS sans ajustement de stock (RF-21)."""
    stock_count = db.session.get(StockCount, count_id)
    if stock_count is None:
        raise not_found("Session d inventaire", count_id)

    if stock_count.status != StockCountStatus.EN_COURS.value:
        raise conflict(
            "STOCK_COUNT_NOT_CANCELLABLE",
            "Seule une session EN_COURS peut etre annulee "
            "(statut actuel : " + stock_count.status + ").",
        )

    user_id = get_jwt_identity()
    stock_count.status = StockCountStatus.ANNULE.value
    stock_count.cancelled_by_id = user_id
    stock_count.cancelled_at = datetime.utcnow()

    AuditLog.record(
        event_type="STOCK_COUNT_CANCELLED",
        user_id=user_id,
        entity_type="StockCount",
        entity_id=stock_count.id,
        description="Session d inventaire " + stock_count.reference + " annulee.",
    )

    db.session.commit()
    return jsonify(stock_count_detail_schema.dump(stock_count))
