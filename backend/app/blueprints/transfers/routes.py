"""Routes du blueprint `transfers` : cycle de vie BROUILLON -> EN_TRANSIT -> RECU."""
from datetime import datetime

from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity

from app.blueprints.transfers import transfers_bp
from app.blueprints.transfers.schemas import (
    TransferCreateSchema,
    TransferReceiveSchema,
    TransferSchema,
)
from app.extensions import db
from app.models import AuditLog, Branch, Product, StockMovementType, Transfer, TransferLine, TransferStatus
from app.services.reference_service import generate_reference
from app.services.stock_service import apply_stock_movement
from app.utils.decorators import require_permission
from app.utils.errors import ApiError, not_found, validation_error

transfer_schema = TransferSchema()
transfers_schema = TransferSchema(many=True)


@transfers_bp.get("")
@require_permission("transfers:read")
def list_transfers():
    query = Transfer.query

    branch_id = request.args.get("branch_id")
    if branch_id:
        query = query.filter(
            (Transfer.source_branch_id == branch_id) | (Transfer.destination_branch_id == branch_id)
        )

    status = request.args.get("status")
    if status:
        query = query.filter(Transfer.status == status)

    transfers = query.order_by(Transfer.created_at.desc()).all()
    return jsonify(transfers_schema.dump(transfers))


@transfers_bp.post("")
@require_permission("transfers:write")
def create_transfer():
    """Cree un transfert en BROUILLON (RF-12)."""
    payload = TransferCreateSchema().load(request.get_json(silent=True) or {})

    if payload["source_branch_id"] == payload["destination_branch_id"]:
        raise validation_error(
            "Le site source et le site destination doivent etre differents.",
            details={"destination_branch_id": "doit etre different de source_branch_id"},
        )

    if Branch.query.get(payload["source_branch_id"]) is None:
        raise not_found("Site source", payload["source_branch_id"])

    if Branch.query.get(payload["destination_branch_id"]) is None:
        raise not_found("Site destination", payload["destination_branch_id"])

    transfer = Transfer(
        reference=generate_reference("TRF"),
        source_branch_id=payload["source_branch_id"],
        destination_branch_id=payload["destination_branch_id"],
        status=TransferStatus.BROUILLON.value,
        created_by_id=get_jwt_identity(),
    )

    for line in payload["lines"]:
        if Product.query.get(line["product_id"]) is None:
            raise not_found("Produit", line["product_id"])

        transfer.lines.append(TransferLine(
            product_id=line["product_id"],
            quantity_sent=line["quantity_sent"],
        ))

    db.session.add(transfer)
    db.session.commit()

    return jsonify(transfer_schema.dump(transfer)), 201


@transfers_bp.get("/<string:transfer_id>")
@require_permission("transfers:read")
def get_transfer(transfer_id: str):
    transfer = Transfer.query.get(transfer_id)
    if transfer is None:
        raise not_found("Transfert", transfer_id)
    return jsonify(transfer_schema.dump(transfer))


@transfers_bp.post("/<string:transfer_id>/send")
@require_permission("transfers:write")
def send_transfer(transfer_id: str):
    """Expedie un transfert BROUILLON : sortie de stock du site source (RG-17)."""
    transfer = Transfer.query.get(transfer_id)
    if transfer is None:
        raise not_found("Transfert", transfer_id)

    if transfer.status != TransferStatus.BROUILLON.value:
        raise ApiError(
            "TRANSFER_NOT_DRAFT",
            "Seul un transfert en brouillon peut etre expedie.",
            status_code=409,
        )

    for line in transfer.lines:
        apply_stock_movement(
            product_id=line.product_id,
            branch_id=transfer.source_branch_id,
            quantity=-line.quantity_sent,
            movement_type=StockMovementType.SORTIE_TRANSFERT.value,
            reference_type="TRANSFER",
            reference_id=transfer.id,
            created_by_id=get_jwt_identity(),
            comment="Expedition transfert " + transfer.reference,
        )

    transfer.status = TransferStatus.EN_TRANSIT.value
    transfer.sent_at = datetime.utcnow()

    db.session.commit()

    return jsonify(transfer_schema.dump(transfer))


@transfers_bp.post("/<string:transfer_id>/receive")
@require_permission("transfers:write")
def receive_transfer(transfer_id: str):
    """Receptionne un transfert EN_TRANSIT (RG-17/RG-18)."""
    transfer = Transfer.query.get(transfer_id)
    if transfer is None:
        raise not_found("Transfert", transfer_id)

    if transfer.status != TransferStatus.EN_TRANSIT.value:
        raise ApiError(
            "TRANSFER_NOT_IN_TRANSIT",
            "Seul un transfert en transit peut etre receptionne.",
            status_code=409,
        )

    payload = TransferReceiveSchema().load(request.get_json(silent=True) or {})
    lines_by_id = {line.id: line for line in transfer.lines}

    for received_line in payload["lines"]:
        line = lines_by_id.get(received_line["line_id"])
        if line is None:
            raise not_found("Ligne de transfert", received_line["line_id"])

        quantity_received = received_line["quantity_received"]
        if quantity_received != line.quantity_sent and not received_line.get("variance_comment"):
            raise validation_error(
                "Un ecart entre la quantite expediee et recue doit etre motive (RG-18).",
                details={"line_id": line.id, "variance_comment": "requis en cas d'ecart"},
            )

        line.quantity_received = quantity_received
        line.variance_comment = received_line.get("variance_comment")

        if quantity_received > 0:
            apply_stock_movement(
                product_id=line.product_id,
                branch_id=transfer.destination_branch_id,
                quantity=quantity_received,
                movement_type=StockMovementType.ENTREE_TRANSFERT.value,
                reference_type="TRANSFER",
                reference_id=transfer.id,
                created_by_id=get_jwt_identity(),
                comment="Reception transfert " + transfer.reference,
            )

    transfer.status = TransferStatus.RECU.value
    transfer.received_by_id = get_jwt_identity()
    transfer.received_at = datetime.utcnow()

    db.session.commit()

    return jsonify(transfer_schema.dump(transfer))


@transfers_bp.post("/<string:transfer_id>/cancel")
@require_permission("transfers:write")
def cancel_transfer(transfer_id: str):
    """Annule un transfert encore en BROUILLON."""
    transfer = Transfer.query.get(transfer_id)
    if transfer is None:
        raise not_found("Transfert", transfer_id)

    if transfer.status != TransferStatus.BROUILLON.value:
        raise ApiError(
            "TRANSFER_NOT_DRAFT",
            "Seul un transfert en brouillon peut etre annule.",
            status_code=409,
        )

    transfer.status = TransferStatus.ANNULE.value
    AuditLog.record(
        event_type="TRANSFER_CANCELLED",
        user_id=get_jwt_identity(),
        entity_type="Transfer",
        entity_id=str(transfer.id),
        description="Transfert " + transfer.reference + " annule.",
    )
    db.session.commit()
    return jsonify(transfer_schema.dump(transfer))
