"""Service métier des ventes (caisse) — RG-20 à RG-27.

Toute la logique de tarification, de remise, de vérification de stock et de
crédit client est centralisée ici afin que le blueprint `sales` reste une
simple couche HTTP (cf. 09-BACKEND-FLASK.md).
"""
from collections import defaultdict
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from flask import current_app

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
    User,
)
from app.services.reference_service import generate_reference
from app.services.stock_service import apply_stock_movement
from app.utils.errors import ApiError, forbidden, not_found, validation_error

TWO_PLACES = Decimal("0.01")


def _round_money(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def create_sale(payload: dict, cashier_id: str) -> Sale:
    """Crée et valide une vente (UC-11/UC-12).

    Étapes : tarification (RG-21), contrôle de la remise (RG-22/RG-23),
    vérification du stock (RG-24), calcul du total (RG-25), gestion du
    crédit client (RG-26). La vente créée a le statut `VALIDEE` et est
    immuable (RG-27) : seul un avoir (cf. `create_refund`) peut la corriger.
    """
    allowed_rates = current_app.config["ALLOWED_DISCOUNT_RATES"]
    approval_threshold = current_app.config["DISCOUNT_APPROVAL_THRESHOLD"]

    discount_rate = payload["discount_rate"]
    if discount_rate not in allowed_rates:
        raise validation_error(
            f"Le taux de remise doit être l'un des suivants : {allowed_rates} (RG-22).",
            details={"discount_rate": payload["discount_rate"]},
        )

    branch_id = payload["branch_id"]
    payment_type = payload["payment_type"]

    # ---- RG-26 : vente à crédit -> client obligatoire ----
    customer = None
    if payload.get("customer_id"):
        customer = Customer.query.get(payload["customer_id"])
        if customer is None:
            raise not_found("Client", payload["customer_id"])

    if payment_type == PaymentType.CREDIT.value and customer is None:
        raise validation_error(
            "Une vente à crédit nécessite un client identifié (RG-26).",
            details={"customer_id": "requis lorsque payment_type = CREDIT"},
        )

    # ---- RG-23 : remise >= seuil -> approbation obligatoire ----
    approved_by = None
    if discount_rate >= approval_threshold:
        if not payload.get("approved_by_id"):
            raise validation_error(
                f"Une remise >= {approval_threshold}% nécessite l'accord d'un administrateur (RG-23).",
                details={"approved_by_id": "requis pour ce taux de remise"},
            )
        approved_by = User.query.get(payload["approved_by_id"])
        if approved_by is None:
            raise not_found("Approbateur", payload["approved_by_id"])
        if approved_by.role.name != "ADMIN" and "sales:approve_discount" not in approved_by.role.permission_codes():
            raise forbidden(
                "L'utilisateur référencé comme approbateur n'a pas les droits suffisants (RG-23)."
            )
    elif discount_rate > 0 and payload.get("approved_by_id"):
        # Une remise plus faible peut tout de même être tracée si un accord est renseigné.
        approved_by = User.query.get(payload["approved_by_id"])

    # ---- RG-21 : tarification selon le type de client ----
    price_type = customer.customer_type if customer else CustomerType.SIMPLE.value

    sale_lines: list[SaleLine] = []
    subtotal = Decimal("0")

    for line in payload["lines"]:
        product = Product.query.get(line["product_id"])
        if product is None:
            raise not_found("Produit", line["product_id"])
        if not product.is_active:
            raise validation_error(
                f"Le produit '{product.name}' est désactivé et ne peut pas être vendu.",
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

    # ---- RG-25 : calcul du total ----
    discount_amount = _round_money(subtotal * Decimal(discount_rate) / Decimal(100))
    total = subtotal - discount_amount

    # ---- RG-26 : vérification du plafond de crédit ----
    if payment_type == PaymentType.CREDIT.value:
        new_balance = customer.credit_balance + total
        if customer.credit_limit > 0 and new_balance > customer.credit_limit:
            raise ApiError(
                "CREDIT_LIMIT_EXCEEDED",
                f"Cette vente porterait l'encours du client à {new_balance} FCFA, "
                f"au-delà de sa limite autorisée ({customer.credit_limit} FCFA).",
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
        approved_by_id=approved_by.id if approved_by else None,
    )
    sale.lines = sale_lines
    db.session.add(sale)
    db.session.flush()  # assigne sale.id, nécessaire pour les mouvements de stock

    # ---- RG-24 : vérification et décrément du stock ----
    for sale_line in sale_lines:
        apply_stock_movement(
            product_id=sale_line.product_id,
            branch_id=branch_id,
            quantity=-sale_line.quantity,
            movement_type=StockMovementType.SORTIE_VENTE.value,
            reference_type="SALE",
            reference_id=sale.id,
            created_by_id=cashier_id,
            comment=f"Vente {sale.reference}",
        )

    # ---- RG-26 : mise à jour du solde client ----
    if payment_type == PaymentType.CREDIT.value:
        customer.credit_balance = customer.credit_balance + total

    AuditLog.record(
        event_type="SALE_CREATED",
        user_id=cashier_id,
        entity_type="Sale",
        entity_id=sale.id,
        description=f"Vente {sale.reference} ({total} FCFA, remise {discount_rate}%)",
        metadata={
            "branch_id": branch_id,
            "discount_rate": discount_rate,
            "approved_by_id": approved_by.id if approved_by else None,
            "payment_type": payment_type,
        },
    )

    if discount_rate >= approval_threshold:
        AuditLog.record(
            event_type="SALE_DISCOUNT_APPROVED",
            user_id=cashier_id,
            entity_type="Sale",
            entity_id=sale.id,
            description=(
                f"Remise de {discount_rate}% appliquée sur la vente {sale.reference}, "
                f"approuvée par {approved_by.full_name}"
            ),
            metadata={"approved_by_id": approved_by.id, "discount_rate": discount_rate},
        )

    db.session.commit()
    return sale


def create_refund(sale: Sale, payload: dict, user_id: str) -> Sale:
    """Émet un avoir (RG-27) : seule voie de correction d'une vente VALIDEE.

    Restocke les quantités retournées (`ENTREE_RETOUR_VENTE`), réduit
    l'encours du client si la vente d'origine était à crédit, et journalise
    l'opération. La vente d'origine n'est jamais modifiée.
    """
    if sale.status != SaleStatus.VALIDEE.value:
        raise ApiError(
            "SALE_NOT_REFUNDABLE",
            "Seule une vente validée peut faire l'objet d'un avoir.",
            status_code=409,
        )

    lines_by_product = {line.product_id: line for line in sale.lines}

    refund_lines: list[SaleLine] = []
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
                "La quantité retournée dépasse la quantité vendue.",
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
        reference=generate_reference("AVR"),
        branch_id=sale.branch_id,
        cashier_id=user_id,
        customer_id=sale.customer_id,
        subtotal=subtotal,
        discount_rate=sale.discount_rate,
        discount_amount=discount_amount,
        total=total,
        payment_type=sale.payment_type,
        status=SaleStatus.AVOIR_EMIS.value,
        refund_of_sale_id=sale.id,
    )
    refund.lines = refund_lines
    db.session.add(refund)
    db.session.flush()

    for refund_line in refund_lines:
        apply_stock_movement(
            product_id=refund_line.product_id,
            branch_id=sale.branch_id,
            quantity=refund_line.quantity,
            movement_type=StockMovementType.ENTREE_RETOUR_VENTE.value,
            reference_type="SALE_REFUND",
            reference_id=refund.id,
            created_by_id=user_id,
            comment=f"Avoir {refund.reference} (vente {sale.reference})",
        )

    if sale.payment_type == PaymentType.CREDIT.value and sale.customer is not None:
        sale.customer.credit_balance = max(Decimal("0"), sale.customer.credit_balance - total)

    AuditLog.record(
        event_type="SALE_REFUNDED",
        user_id=user_id,
        entity_type="Sale",
        entity_id=refund.id,
        description=f"Avoir {refund.reference} émis pour la vente {sale.reference} : {payload['reason']}",
        metadata={"refund_of_sale_id": sale.id, "total": str(total), "reason": payload["reason"]},
    )

    db.session.commit()
    return refund


# ---------------------------------------------------------------------------
# Synchronisation des ventes hors-ligne (RF-20, RG-28 à RG-30)
# ---------------------------------------------------------------------------

def sync_offline_sale(item: dict, cashier_id: str) -> dict:
    """Synchronise une vente saisie hors-ligne (cf. 26-GESTION-OFFLINE-PWA.md).

    - RG-28 : idempotence via `offline_uuid` -> `DEJA_SYNCHRONISE` sans nouvelle
      écriture si la vente est déjà connue côté serveur (rejeu réseau).
    - Sécurité (18-SECURITE.md) : le client n'envoie jamais de prix, le serveur
      revalide systématiquement la tarification (RG-21) et le stock (RG-24).
    - RG-29/RG-30 : si le stock réel est insuffisant, la vente est tout de même
      enregistrée avec le statut `EN_CONFLIT` et le stock est mis en négatif
      contrôlé, pour régularisation manuelle ultérieure par l'admin. Aucune
      vente n'est rejetée silencieusement.
    - Si une remise >= seuil (RG-23) ne peut être validée (approbateur absent
      ou invalide au moment de la synchronisation), la vente est enregistrée
      avec le statut `EN_ATTENTE_APPROBATION` pour validation a posteriori.
    """
    offline_uuid = item["offline_uuid"]

    # ---- RG-28 : idempotence ----
    existing = Sale.query.filter_by(offline_uuid=offline_uuid).first()
    if existing is not None:
        return {
            "offline_uuid": offline_uuid,
            "status": "DEJA_SYNCHRONISE",
            "sale_id": existing.id,
            "message": "Cette vente a déjà été synchronisée précédemment (idempotence RG-28).",
        }

    allowed_rates = current_app.config["ALLOWED_DISCOUNT_RATES"]
    approval_threshold = current_app.config["DISCOUNT_APPROVAL_THRESHOLD"]

    branch_id = item["branch_id"]
    payment_type = item["payment_type"]
    discount_rate = item["discount_rate"]
    notes: list[str] = []

    # ---- RG-22 : taux de remise autorisé (revalidation serveur) ----
    if discount_rate not in allowed_rates:
        notes.append(
            f"Taux de remise {discount_rate}% non autorisé (RG-22), ramené à 0%."
        )
        discount_rate = 0

    # ---- RG-26 : client requis pour une vente à crédit ----
    customer = None
    if item.get("customer_id"):
        customer = Customer.query.get(item["customer_id"])
        if customer is None:
            notes.append("Client introuvable côté serveur, vente traitée sans client.")

    if payment_type == PaymentType.CREDIT.value and customer is None:
        notes.append("Vente à crédit sans client identifié (RG-26), repassée en CASH.")
        payment_type = PaymentType.CASH.value

    # ---- RG-23 : remise >= seuil -> approbation obligatoire ----
    approved_by = None
    needs_approval = False
    if discount_rate >= approval_threshold:
        approved_by_id = item.get("approved_by_id")
        candidate = User.query.get(approved_by_id) if approved_by_id else None
        if candidate is not None and (
            candidate.role.name == "ADMIN"
            or "sales:approve_discount" in candidate.role.permission_codes()
        ):
            approved_by = candidate
        else:
            needs_approval = True
            notes.append(
                f"Remise de {discount_rate}% sans approbateur valide (RG-23) : "
                "vente en attente d'approbation."
            )

    # ---- RG-21 : tarification serveur (le client n'envoie jamais de prix) ----
    price_type = customer.customer_type if customer else CustomerType.SIMPLE.value

    sale_lines: list[SaleLine] = []
    subtotal = Decimal("0")
    for line in item["lines"]:
        product = Product.query.get(line["product_id"])
        if product is None or not product.is_active:
            notes.append(
                f"Produit {line['product_id']} introuvable ou désactivé, ligne ignorée."
            )
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

    # ---- RG-25 : calcul du total ----
    discount_amount = _round_money(subtotal * Decimal(discount_rate) / Decimal(100))
    total = subtotal - discount_amount

    # ---- RG-29 : vérification du stock réel à la synchronisation ----
    needed_by_product: dict[str, int] = defaultdict(int)
    for sale_line in sale_lines:
        needed_by_product[sale_line.product_id] += sale_line.quantity

    has_stock_conflict = False
    for product_id, needed_qty in needed_by_product.items():
        stock_row = Stock.query.filter_by(product_id=product_id, branch_id=branch_id).first()
        available = stock_row.quantity if stock_row is not None else 0
        if available < needed_qty:
            has_stock_conflict = True
            break

    # ---- Détermination du statut final ----
    if has_stock_conflict:
        status = SaleStatus.EN_CONFLIT.value
        notes.append(
            "Stock insuffisant au moment de la synchronisation (RG-29) : vente "
            "enregistrée en conflit, stock mis en négatif contrôlé (RG-30)."
        )
    elif needs_approval:
        status = SaleStatus.EN_ATTENTE_APPROBATION.value
    else:
        status = SaleStatus.VALIDEE.value

    # RG-28/RG-30 : conserver l'horodatage du poste de caisse pour l'ordre chronologique
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
        approved_by_id=approved_by.id if approved_by else None,
        offline_uuid=offline_uuid,
        channel=SaleChannel.OFFLINE.value,
        created_at=created_at,
    )
    sale.lines = sale_lines
    db.session.add(sale)
    db.session.flush()

    # ---- RG-24/RG-29/RG-30 : mouvements de stock (négatif contrôlé autorisé) ----
    for sale_line in sale_lines:
        apply_stock_movement(
            product_id=sale_line.product_id,
            branch_id=branch_id,
            quantity=-sale_line.quantity,
            movement_type=StockMovementType.SORTIE_VENTE.value,
            reference_type="SALE",
            reference_id=sale.id,
            created_by_id=cashier_id,
            comment=f"Vente hors-ligne {sale.reference} (synchronisation)",
            allow_negative=True,
        )

    # ---- RG-26 : mise à jour du solde client ----
    if payment_type == PaymentType.CREDIT.value and customer is not None:
        customer.credit_balance = customer.credit_balance + total

    AuditLog.record(
        event_type="SALE_SYNCED",
        user_id=cashier_id,
        entity_type="Sale",
        entity_id=sale.id,
        description=(
            f"Vente hors-ligne {sale.reference} synchronisée "
            f"({total} FCFA, statut {status})"
        ),
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
            description=(
                f"Conflit de stock à la synchronisation de la vente {sale.reference} "
                "(RG-29) : régularisation manuelle requise."
            ),
            metadata={"offline_uuid": offline_uuid, "branch_id": branch_id},
        )
    elif status == SaleStatus.EN_ATTENTE_APPROBATION.value:
        AuditLog.record(
            event_type="SALE_SYNC_PENDING_APPROVAL",
            user_id=cashier_id,
            entity_type="Sale",
            entity_id=sale.id,
            description=(
                f"Vente hors-ligne {sale.reference} en attente d'approbation "
                f"de remise (RG-23)."
            ),
            metadata={"offline_uuid": offline_uuid, "discount_rate": discount_rate},
        )

    db.session.commit()

    return {
        "offline_uuid": offline_uuid,
        "status": status,
        "sale_id": sale.id,
        "message": " ".join(notes) if notes else None,
    }


def sync_offline_sales(items: list[dict], cashier_id: str) -> list[dict]:
    """Synchronise un lot de ventes hors-ligne (POST /sales/sync).

    Chaque vente est traitee independamment : un echec inattendu sur l'une
    n'empeche pas le traitement des suivantes.
    """
    results = []
    for item in items:
        try:
            result = sync_offline_sale(item, cashier_id)
            results.append({"offline_uuid": item.get("offline_uuid"), "status": "ok", **result})
        except Exception as exc:  # noqa: BLE001
            results.append({"offline_uuid": item.get("offline_uuid"), "status": "error", "error": str(exc)})
    return results
