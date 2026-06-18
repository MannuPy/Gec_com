"""Routes du blueprint `suppliers` : fournisseurs et réceptions de marchandises.

Cf. 04-REGLES-METIER.md (RG-13 : toute réception alimente le stock du dépôt
central) et 18-SECURITE.md (permissions `suppliers:*`, `receptions:*`).
"""
from datetime import datetime

from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity

from app.blueprints.suppliers import suppliers_bp
from app.blueprints.suppliers.schemas import (
    ReceptionCreateSchema,
    ReceptionSchema,
    SupplierSchema,
    SupplierWriteSchema,
)
from app.extensions import db
from app.models import (
    AuditLog,
    Branch,
    Product,
    ReceptionStatus,
    StockMovementType,
    Supplier,
    SupplierReception,
    SupplierReceptionLine,
)
from app.services.reference_service import generate_reference
from app.services.stock_service import apply_stock_movement
from app.utils.decorators import require_permission
from app.utils.errors import ApiError, conflict, not_found, validation_error

supplier_schema = SupplierSchema()
suppliers_schema = SupplierSchema(many=True)
reception_schema = ReceptionSchema()
receptions_schema = ReceptionSchema(many=True)


# ---------------------------------------------------------------------------
# Fournisseurs
# ---------------------------------------------------------------------------

@suppliers_bp.get("/suppliers")
@require_permission("suppliers:read", "receptions:read")
def list_suppliers():
    query = Supplier.query

    is_active = request.args.get("is_active")
    if is_active is not None:
        query = query.filter(Supplier.is_active == (is_active.lower() in ("1", "true", "yes")))

    suppliers = query.order_by(Supplier.name).all()
    return jsonify(suppliers_schema.dump(suppliers))


@suppliers_bp.post("/suppliers")
@require_permission("suppliers:write")
def create_supplier():
    payload = SupplierWriteSchema().load(request.get_json(silent=True) or {})

    if Supplier.query.filter_by(name=payload["name"]).first() is not None:
        raise conflict("SUPPLIER_ALREADY_EXISTS", "Un fournisseur porte déjà ce nom.")

    supplier = Supplier(**payload)
    db.session.add(supplier)
    db.session.commit()
    return jsonify(supplier_schema.dump(supplier)), 201


@suppliers_bp.get("/suppliers/<string:supplier_id>")
@require_permission("suppliers:read", "receptions:read")
def get_supplier(supplier_id: str):
    supplier = Supplier.query.get(supplier_id)
    if supplier is None:
        raise not_found("Fournisseur", supplier_id)
    return jsonify(supplier_schema.dump(supplier))


@suppliers_bp.put("/suppliers/<string:supplier_id>")
@require_permission("suppliers:write")
def update_supplier(supplier_id: str):
    supplier = Supplier.query.get(supplier_id)
    if supplier is None:
        raise not_found("Fournisseur", supplier_id)

    payload = SupplierWriteSchema().load(request.get_json(silent=True) or {})

    for field, value in payload.items():
        setattr(supplier, field, value)

    db.session.commit()
    return jsonify(supplier_schema.dump(supplier))


# ---------------------------------------------------------------------------
# Réceptions
# ---------------------------------------------------------------------------

@suppliers_bp.get("/receptions")
@require_permission("receptions:read")
def list_receptions():
    query = SupplierReception.query

    branch_id = request.args.get("branch_id")
    if branch_id:
        query = query.filter(SupplierReception.branch_id == branch_id)

    supplier_id = request.args.get("supplier_id")
    if supplier_id:
        query = query.filter(SupplierReception.supplier_id == supplier_id)

    status = request.args.get("status")
    if status:
        query = query.filter(SupplierReception.status == status)

    receptions = query.order_by(SupplierReception.created_at.desc()).all()
    return jsonify(receptions_schema.dump(receptions))


@suppliers_bp.post("/receptions")
@require_permission("receptions:write")
def create_reception():
    """Crée une réception en BROUILLON (RF-11). La validation alimente le stock."""
    payload = ReceptionCreateSchema().load(request.get_json(silent=True) or {})

    if Supplier.query.get(payload["supplier_id"]) is None:
        raise not_found("Fournisseur", payload["supplier_id"])

    branch = Branch.query.get(payload["branch_id"])
    if branch is None:
        raise not_found("Site", payload["branch_id"])

    if not branch.is_depot:
        raise validation_error(
            "Les réceptions fournisseur ne peuvent être enregistrées que sur le dépôt central (RG-13).",
            details={"branch_id": "doit être un site marqué comme dépôt (is_depot=true)"},
        )

    reception = SupplierReception(
        reference=generate_reference("REC"),
        supplier_id=payload["supplier_id"],
        branch_id=payload["branch_id"],
        status=ReceptionStatus.BROUILLON.value,
        created_by_id=get_jwt_identity(),
    )

    for line in payload["lines"]:
        if Product.query.get(line["product_id"]) is None:
            raise not_found("Produit", line["product_id"])

        reception.lines.append(SupplierReceptionLine(
            product_id=line["product_id"],
            quantity=line["quantity"],
            unit_purchase_price=line["unit_purchase_price"],
        ))

    db.session.add(reception)
    db.session.commit()

    return jsonify(reception_schema.dump(reception)), 201


@suppliers_bp.get("/receptions/<string:reception_id>")
@require_permission("receptions:read")
def get_reception(reception_id: str):
    reception = SupplierReception.query.get(reception_id)
    if reception is None:
        raise not_found("Réception", reception_id)
    return jsonify(reception_schema.dump(reception))


@suppliers_bp.post("/receptions/<string:reception_id>/validate")
@require_permission("receptions:write")
def validate_reception(reception_id: str):
    """Valide une réception : alimente le stock du dépôt et met à jour le
    dernier prix d'achat connu de chaque produit (RG-13).
    """
    reception = SupplierReception.query.get(reception_id)
    if reception is None:
        raise not_found("Réception", reception_id)

    if reception.status != ReceptionStatus.BROUILLON.value:
        raise ApiError(
            "RECEPTION_ALREADY_VALIDATED",
            "Cette réception a déjà été validée.",
            status_code=409,
        )

    for line in reception.lines:
        apply_stock_movement(
            product_id=line.product_id,
            branch_id=reception.branch_id,
            quantity=line.quantity,
            movement_type=StockMovementType.ENTREE_RECEPTION.value,
            reference_type="RECEPTION",
            reference_id=reception.id,
            created_by_id=get_jwt_identity(),
            comment=f"Réception {reception.reference}",
        )
        line.product.purchase_price = line.unit_purchase_price

    reception.status = "VALIDE"
    AuditLog.record(
        event_type="RECEPTION_VALIDATED",
        user_id=get_jwt_identity(),
        entity_type="Reception",
        entity_id=str(reception.id),
        description=f"Reception {reception.reference} validee.",
    )
    db.session.commit()
    from app.blueprints.suppliers.schemas import ReceptionSchema
    return jsonify(ReceptionSchema().dump(reception)), 200
