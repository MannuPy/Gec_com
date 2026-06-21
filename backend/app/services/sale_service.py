"""Service metier des ventes (caisse) - RG-20 a RG-27."""
from collections import defaultdict
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from app.extensions import db
from app.models import (
    AuditLog,
    Customer,
    CustomerType,
    PaymentType,
    Product,
    Sale,
    SaleChannel,
    SaleLine,
    SaleStatus,
    Stock,
    StockMovementType,
)
from app.services.reference_service import generate_reference
from app.services.stock_service import apply_stock_movement
from app.utils.errors import ApiError, not_found, validation_error

TWO_PLACES = Decimal("0.01")


def _round_money(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def create_sale(payload: dict, cashier_id: str) -> Sale:
    """Cree et valide une vente (UC-11/UC-12)."""
    discount_rate = payload["discount_rate"]
    if not (0 <= discount_rate <= 100):
        raise validation_error(
            "Le taux de remise doit etre compris entre 0 et 100.",
            details={"discount_rate": discount_rate},
        )

    branch_id = payload["branch_id"]
    payment_type = payload["payment_type"]

    customer = None
    if payload.get("customer_id"):
        customer = Customer.query.get(payload["customer_id"])
        if customer is None:
            raise not_found("Client", payload["customer_id"])

    if payment_type == PaymentType.CREDIT.value and customer is None:
        raise validation_error(
            "Une vente a credit necessite un client identifie (RG-26).",
            details={"customer_id": "requis lorsque payment_type = CREDIT"},
        )

    price_type = customer.customer_type if customer else CustomerType.SIMPLE.value

    sale_lines = []
    subtotal = Decimal("0")

    for line in payload["lines"]:
        product = Product.query.get(line["product_id"])
        if product is None:
            raise not_found("Produit", line["product_id"])
        if not product.is_active:
            raise validation_error(
                "Le produit '" + product.name + "' est desactive et ne peut pas etre vendu.",
                details={"product_id": product.id},
            )

        quantity = line["quantity"]
        unit_price = Decimal(product.price_for(price_type))
        line_total = _round_money(unit_price * quantity)

        sale_lines.append(SaleLine(
            product_id=product.id,
            quantity=quantity,
            unit_price_applied=unit_price,
            price_type=price_type,
            line_total=line_total,
        ))
        subtotal += line_total

    discount_amount = _round_money(subtotal * Decimal(discount_rate) / Decimal(100))
    total = subtotal - discount_amount

    if payment_type == PaymentType.CREDIT.value:
        new_balance = customer.credit_balance + total
        if customer.credit_limit > 0 and new_balance > customer.credit_limit:
            raise ApiError(
                "CREDIT_LIMIT_EXCEEDED",
                "Cette vente porterait l'encours du client a " + str(new_balance) + " FCFA, "
                "au-dela de sa limite autorisee (" + str(customer.credit_limit) + " FCFA).",
                status_code=409,
                details={
                    "customer_id": customer.id,
                    "current_balance": str(customer.credit_balance),
                    "credit_limit": str(customer.credit_limit),
                    "sale_total": str(total),
                },
            )

    sale = Sale(
        reference=generate_reference("VTE"),
        branch_id=branch_id,
        cashier_id=cashier_id,
        customer_id=customer.id if customer else None,
        subtotal=subtotal,
        discount_rate=discount_rate,
        discount_amount=discount_amount,
        total=total,
        payment_type=payment_type,
        status=SaleStatus.VALIDEE.value,
    )
    sale.lines = sale_lines
    db.session.add(sale)
    db.session.flush()

    for sale_line in sale_lines:
        apply_stock_movement(
            product_id=sale_line.product_id,
            branch_id=branch_id,
            quantity=-sale_line.quantity,
            movement_type=StockMovementType.SORTIE_VENTE.value,
            reference_type="SALE",
            reference_id=sale.id,
            created_by_id=cashier_id,
            comment="Vente " + sale.reference,
        )

    if payment_type == PaymentType.CREDIT.value:
        customer.credit_balance = customer.credit_balance + total

    AuditLog.record(
        event_type="SALE_CREATED",
        user_id=cashier_id,
        entity_type="Sale",
        entity_id=sale.id,
        description="Vente " + sale.reference + " (" + str(total) + " FCFA, remise " + str(discount_rate) + "%)",
        metadata={
            "branch_id": branch_id,
            "discount_rate": discount_rate,
            "payment_type": payment_type,
        },
    )

    db.session.commit()
    return sale


def create_refund(sale: Sale, payload: dict, user_id: str) -> Sale:
    """Cree un avoir EN ATTENTE D'APPROBATION (RG-27)."""
    if sale.status != SaleStatus.VALIDEE.value:
        raise ApiError(
            "SALE_NOT_REFUNDABLE",
            "Seule une vente validee peut faire l'objet d'un avoir.",
            status_code=409,
        )

    existing_pending = Sale.query.filter_by(
        refund_of_sale_id=sale.id,
        status=SaleStatus.EN_ATTENTE_APPROBATION.value,
    ).first()
    if existing_pending is not None:
        raise ApiError(
            "REFUND_ALREADY_PENDING",
            "Un retour est deja en attente d'approbation pour cette vente.",
            status_code=409,
        )

    lines_by_product = {line.product_id: line for line in sale.lines}

    refund_lines = []
    subtotal = Decimal("0")

    for refund_line in payload["lines"]:
        original_line = lines_by_product.get(refund_line["product_id"])
        if original_line is None:
            raise validation_error(
                "Ce produit ne fait pas partie de la vente d'origine.",
                details={"product_id": refund_line["product_id"]},
            )

        if refund_line["quantity"] > original_line.quantity:
            raise validation_error(
                "La quantite retournee depasse la quantite vendue.",
                details={
                    "product_id": refund_line["product_id"],
                    "sold_quantity": original_line.quantity,
                    "requested_quantity": refund_line["quantity"],
                },
            )

        unit_price = original_line.unit_price_applied
        line_total = _round_money(unit_price * refund_line["quantity"])

        refund_lines.append(SaleLine(
            product_id=original_line.product_id,
            quantity=refund_line["quantity"],
            unit_price_applied=unit_price,
            price_type=original_line.price_type,
            line_total=line_total,
        ))
        subtotal += line_total

    discount_amount = _round_money(subtotal * Decimal(sale.discount_rate) / Decimal(100))
    total = subtotal - discount_amount

    refund = Sale(
        reference=generate_reference("RET"),
        branch_id=sale.branch_id,
        cashier_id=user_id,
        customer_id=sale.customer_id,
        subtotal=subtotal,
        discount_rate=sale.discount_rate,
        discount_amount=discount_amount,
        total=total,
        payment_type=sale.payment_type,
        status=SaleStatus.EN_ATTENTE_APPROBATION.value,
        refund_of_sale_id=sale.id,
    )
    refund.lines = refund_lines
    db.session.add(refund)

    AuditLog.record(
        event_type="REFUND_INITIATED",
        user_id=user_id,
        entity_type="Sale",
        entity_id=sale.id,
        description="Retour produit initie par le vendeur sur la vente " + sale.reference + " ("
            + str(total) + " FCFA) - en attente d'approbation admin. Motif : " + payload.get("reason", ""),
        metadata={"sale_id": sale.id, "total": str(total), "reason": payload.get("reason", "")},
    )

    db.session.commit()
    return refund


def approve_refund(refund: Sale, admin_id: str) -> Sale:
    """Approuve un retour en attente (admin uniquement)."""
    if refund.status != SaleStatus.EN_ATTENTE_APPROBATION.value:
        raise ApiError(
            "REFUND_NOT_PENDING",
            "Ce retour n'est pas en attente d'approbation.",
            status_code=409,
        )

    original_sale = Sale.query.get(refund.refund_of_sale_id)

    for refund_line in refund.lines:
        apply_stock_movement(
            product_id=refund_line.product_id,
            branch_id=refund.branch_id,
            quantity=refund_line.quantity,
            movement_type=StockMovementType.ENTREE_RETOUR_VENTE.value,
            reference_type="SALE_REFUND",
            reference_id=refund.id,
            created_by_id=admin_id,
            comment="Retour approuve " + refund.reference + " (vente " + (original_sale.reference if original_sale else "?") + ")",
        )

    if refund.payment_type == PaymentType.CREDIT.value and refund.customer is not None:
        refund.customer.credit_balance = max(
            Decimal("0"), refund.customer.credit_balance - refund.total
        )

    refund.status = SaleStatus.AVOIR_EMIS.value
    refund.approved_by_id = admin_id

    if original_sale:
        original_sale.status = SaleStatus.AVOIR_EMIS.value

    AuditLog.record(
        event_type="REFUND_APPROVED",
        user_id=admin_id,
        entity_type="Sale",
        entity_id=refund.id,
        description="Retour " + refund.reference + " approuve par l'admin. Stock reintegre, encours mis a jour (" + str(refund.total) + " FCFA).",
        metadata={"refund_id": refund.id, "original_sale_id": str(refund.refund_of_sale_id)},
    )

    db.session.commit()
    return refund


def reject_refund(refund: Sale, admin_id: str, reason: str = "") -> Sale:
    """Rejette un retour en attente (admin uniquement)."""
    if refund.status != SaleStatus.EN_ATTENTE_APPROBATION.value:
        raise ApiError(
            "REFUND_NOT_PENDING",
            "Ce retour n'est pas en attente d'approbation.",
            status_code=409,
        )

    refund.status = SaleStatus.ANNULEE.value
    refund.approved_by_id = admin_id

    AuditLog.record(
        event_type="REFUND_REJECTED",
        user_id=admin_id,
        entity_type="Sale",
        entity_id=refund.id,
        description="Retour " + refund.reference + " rejete par l'admin. Motif : " + reason,
        metadata={"refund_id": refund.id, "reason": reason},
    )

    db.session.commit()
    return refund


def sync_offline_sale(item: dict, cashier_id: str) -> dict:
    """Synchronise une vente saisie hors-ligne (cf. 26-GESTION-OFFLINE-PWA.md)."""
    offline_uuid = item["offline_uuid"]

    existing = Sale.query.filter_by(offline_uuid=offline_uuid).first()
    if existing is not None:
        return {
            "offline_uuid": offline_uuid,
            "status": "DEJA_SYNCHRONISE",
            "sale_id": existing.id,
            "message": "Cette vente a deja ete synchronisee precedemment (idempotence RG-28).",
        }

    branch_id = item["branch_id"]
    payment_type = item["payment_type"]
    discount_rate = item["discount_rate"]
    notes = []

    if not (0 <= discount_rate <= 100):
        notes.append("Taux de remise " + str(discount_rate) + "% hors plage, ramene a 0%.")
        discount_rate = 0

    customer = None
    if item.get("customer_id"):
        customer = Customer.query.get(item["customer_id"])
        if customer is None:
            notes.append("Client introuvable cote serveur, vente traitee sans client.")

    if payment_type == PaymentType.CREDIT.value and customer is None:
        notes.append("Vente a credit sans client identifie (RG-26), repassee en CASH.")
        payment_type = PaymentType.CASH.value

    price_type = customer.customer_type if customer else CustomerType.SIMPLE.value

    sale_lines = []
    subtotal = Decimal("0")
    for line in item["lines"]:
        product = Product.query.get(line["product_id"])
        if product is None or not product.is_active:
            notes.append("Produit " + str(line["product_id"]) + " introuvable ou desactive, ligne ignoree.")
            continue

        quantity = line["quantity"]
        unit_price = Decimal(product.price_for(price_type))
        line_total = _round_money(unit_price * quantity)

        sale_lines.append(SaleLine(
            product_id=product.id,
            quantity=quantity,
            unit_price_applied=unit_price,
            price_type=price_type,
            line_total=line_total,
        ))
        subtotal += line_total

    if not sale_lines:
        return {
            "offline_uuid": offline_uuid,
            "status": "ERREUR",
            "sale_id": None,
            "message": " ".join(notes) or "Aucun produit valide dans cette vente.",
        }

    discount_amount = _round_money(subtotal * Decimal(discount_rate) / Decimal(100))
    total = subtotal - discount_amount

    needed_by_product = defaultdict(int)
    for sale_line in sale_lines:
        needed_by_product[sale_line.product_id] += sale_line.quantity

    has_stock_conflict = False
    for product_id, needed_qty in needed_by_product.items():
        stock_row = Stock.query.filter_by(product_id=product_id, branch_id=branch_id).first()
        available = stock_row.quantity if stock_row is not None else 0
        if available < needed_qty:
            has_stock_conflict = True
            break

    if has_stock_conflict:
        status = SaleStatus.EN_CONFLIT.value
        notes.append(
            "Stock insuffisant au moment de la synchronisation (RG-29) : vente "
            "enregistree en conflit, stock mis en negatif controle (RG-30)."
        )
    else:
        status = SaleStatus.VALIDEE.value

    created_at = item.get("created_at_local") or datetime.utcnow()

    sale = Sale(
        reference=generate_reference("VTE"),
        branch_id=branch_id,
        cashier_id=cashier_id,
        customer_id=customer.id if customer else None,
        subtotal=subtotal,
        discount_rate=discount_rate,
        discount_amount=discount_amount,
        total=total,
        payment_type=payment_type,
        status=status,
        offline_uuid=offline_uuid,
        channel=SaleChannel.OFFLINE.value,
        created_at=created_at,
    )
    sale.lines = sale_lines
    db.session.add(sale)
    db.session.flush()

    for sale_line in sale_lines:
        apply_stock_movement(
            product_id=sale_line.product_id,
            branch_id=branch_id,
            quantity=-sale_line.quantity,
            movement_type=StockMovementType.SORTIE_VENTE.value,
            reference_type="SALE",
            reference_id=sale.id,
            created_by_id=cashier_id,
            comment="Vente hors-ligne " + sale.reference + " (synchronisation)",
            allow_negative=True,
        )

    if payment_type == PaymentType.CREDIT.value and customer is not None:
        customer.credit_balance = customer.credit_balance + total

    AuditLog.record(
        event_type="SALE_SYNCED",
        user_id=cashier_id,
        entity_type="Sale",
        entity_id=sale.id,
        description="Vente hors-ligne " + sale.reference + " synchronisee (" + str(total) + " FCFA, statut " + status + ")",
        metadata={
            "offline_uuid": offline_uuid,
            "branch_id": branch_id,
            "status": status,
            "notes": notes,
        },
    )

    if status == SaleStatus.EN_CONFLIT.value:
        AuditLog.record(
            event_type="SALE_SYNC_CONFLICT",
            user_id=cashier_id,
            entity_type="Sale",
            entity_id=sale.id,
            description="Conflit de stock a la synchronisation de la vente " + sale.reference + " (RG-29) : regularisation manuelle requise.",
            metadata={"offline_uuid": offline_uuid, "branch_id": branch_id},
        )

    db.session.commit()

    return {
        "offline_uuid": offline_uuid,
        "status": status,
        "sale_id": sale.id,
        "message": " ".join(notes) if notes else None,
    }


def sync_offline_sales(items: list, cashier_id: str) -> list:
    """Synchronise un lot de ventes hors-ligne (POST /sales/sync)."""
    results = []
    for item in items:
        try:
            result = sync_offline_sale(item, cashier_id)
            results.append(result)
        except Exception as exc:
            results.append({
                "offline_uuid": item.get("offline_uuid"),
                "status": "ERREUR",
                "sale_id": None,
                "message": str(exc),
            })
    return results
