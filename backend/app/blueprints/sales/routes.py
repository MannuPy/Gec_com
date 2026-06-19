"""Routes du blueprint `sales` : ventes (caisse), avoirs et clients.

Cf. 17-API-REST.md section Sales et 04-REGLES-METIER.md (RG-20 a RG-27). La
logique metier est deleguee a `app.services.sale_service`.
"""
from datetime import date
from decimal import Decimal

from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity
from sqlalchemy import or_

from app.blueprints.sales import sales_bp
from app.blueprints.sales.schemas import (
    CustomerPaymentCreateSchema,
    CustomerPaymentSchema,
    CustomerPaymentUpdateSchema,
    CustomerSchema,
    CustomerWriteSchema,
    RefundCreateSchema,
    SaleCreateSchema,
    SaleSchema,
    SaleSyncBatchSchema,
    SaleSyncResultSchema,
)
from app.extensions import db
from app.models import AuditLog, Customer, CustomerPayment, CustomerPaymentStatus, Product, Sale, SaleLine
from app.services.sale_service import (
    approve_refund,
    create_refund,
    create_sale,
    reject_refund,
    sync_offline_sales,
)
from app.utils.decorators import require_permission
from app.utils.errors import conflict, not_found
from app.utils.pdf import build_sale_receipt_pdf, pdf_response

sale_schema = SaleSchema()
sales_schema = SaleSchema(many=True)
customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)
customer_payment_schema = CustomerPaymentSchema()
customer_payments_schema = CustomerPaymentSchema(many=True)


# ---------------------------------------------------------------------------
# Ventes
# ---------------------------------------------------------------------------

@sales_bp.get("")
@require_permission("sales:read")
def list_sales():
    """Liste paginee des ventes, filtrable par site, statut, client, vendeur."""
    query = Sale.query

    branch_id = request.args.get("branch_id")
    if branch_id:
        query = query.filter(Sale.branch_id == branch_id)

    status = request.args.get("status")
    if status:
        query = query.filter(Sale.status == status)

    customer_id = request.args.get("customer_id")
    if customer_id:
        query = query.filter(Sale.customer_id == customer_id)

    cashier_id = request.args.get("cashier_id")
    if cashier_id:
        query = query.filter(Sale.cashier_id == cashier_id)

    page = request.args.get("page", default=1, type=int)
    per_page = min(request.args.get("per_page", default=20, type=int), 100)

    pagination = query.order_by(Sale.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        "data": sales_schema.dump(pagination.items),
        "meta": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
        },
    })


@sales_bp.post("")
@require_permission("sales:create")
def create_sale_route():
    """Enregistre une vente caisse (UC-11/UC-12) - cf. `sale_service.create_sale`."""
    payload = SaleCreateSchema().load(request.get_json(silent=True) or {})
    sale = create_sale(payload, cashier_id=get_jwt_identity())
    return jsonify(sale_schema.dump(sale)), 201


@sales_bp.post("/sync")
@require_permission("sales:create")
def sync_sales_route():
    """Synchronise un lot de ventes saisies hors-ligne (RF-20, RG-28 a RG-30).

    Reponse 200 avec un statut metier par vente (cf. 17-API-REST.md,
    code `SYNC_CONFLICT`) : `VALIDEE`, `EN_CONFLIT`, `EN_ATTENTE_APPROBATION`,
    `DEJA_SYNCHRONISE` ou `ERREUR`. Aucune vente n'est rejetee silencieusement.
    """
    payload = SaleSyncBatchSchema().load(request.get_json(silent=True) or {})
    results = sync_offline_sales(payload["sales"], cashier_id=get_jwt_identity())
    return jsonify({"results": SaleSyncResultSchema(many=True).dump(results)}), 200



@sales_bp.get("/<string:sale_id>")
@require_permission("sales:read")
def get_sale(sale_id: str):
    sale = Sale.query.get(sale_id)
    if sale is None:
        raise not_found("Vente", sale_id)
    return jsonify(sale_schema.dump(sale))


@sales_bp.get("/<string:sale_id>/receipt")
@require_permission("sales:read")
def sale_receipt(sale_id: str):
    """Genere le recu de vente au format PDF (RF-19)."""
    sale = Sale.query.get(sale_id)
    if sale is None:
        raise not_found("Vente", sale_id)

    buffer = build_sale_receipt_pdf(sale)
    return pdf_response(buffer, filename=f"recu-{sale.reference}.pdf")


@sales_bp.post("/<string:sale_id>/refund")
@require_permission("sales:refund")
def refund_sale(sale_id: str):
    """Emet un avoir sur une vente validee (RG-27)."""
    sale = Sale.query.get(sale_id)
    if sale is None:
        raise not_found("Vente", sale_id)

    payload = RefundCreateSchema().load(request.get_json(silent=True) or {})
    refund = create_refund(sale, payload, user_id=get_jwt_identity())
    return jsonify(sale_schema.dump(refund)), 201


# ---------------------------------------------------------------------------
# Clients
# ---------------------------------------------------------------------------

@sales_bp.get("/customers")
@require_permission("customers:read", "sales:create")
def list_customers():
    """Liste les clients, avec recherche optionnelle par nom/telephone."""
    query = Customer.query

    search = (request.args.get("search") or "").strip()
    if search:
        like = f"%{search}%"
        query = query.filter(or_(Customer.full_name.ilike(like), Customer.phone.ilike(like)))

    customers = query.order_by(Customer.full_name).all()
    return jsonify(customers_schema.dump(customers))


@sales_bp.post("/customers")
@require_permission("customers:write")
def create_customer():
    """Cree un client (requis pour toute vente a credit - RG-26)."""
    payload = CustomerWriteSchema().load(request.get_json(silent=True) or {})

    if payload.get("phone") and Customer.query.filter_by(phone=payload["phone"]).first():
        raise conflict("PHONE_ALREADY_USED", "Un client existe deja avec ce numero de telephone.")

    customer = Customer(**payload)
    db.session.add(customer)
    db.session.commit()

    return jsonify(customer_schema.dump(customer)), 201


@sales_bp.get("/customers/<string:customer_id>")
@require_permission("customers:read", "sales:create")
def get_customer(customer_id: str):
    customer = Customer.query.get(customer_id)
    if customer is None:
        raise not_found("Client", customer_id)
    return jsonify(customer_schema.dump(customer))


@sales_bp.put("/customers/<string:customer_id>")
@require_permission("customers:write")
def update_customer(customer_id: str):
    customer = Customer.query.get(customer_id)
    if customer is None:
        raise not_found("Client", customer_id)

    payload = CustomerWriteSchema().load(request.get_json(silent=True) or {})

    if payload.get("phone") and payload["phone"] != customer.phone:
        if Customer.query.filter_by(phone=payload["phone"]).first():
            raise conflict("PHONE_ALREADY_USED", "Un client existe deja avec ce numero de telephone.")

    for field, value in payload.items():
        setattr(customer, field, value)

    db.session.commit()
    return jsonify(customer_schema.dump(customer))


# ---------------------------------------------------------------------------
# Echeances de remboursement a credit (RF-26, section 20.6.2)
# ---------------------------------------------------------------------------

@sales_bp.get("/customers/<string:customer_id>/payments")
@require_permission("customers:read", "sales:create")
def list_customer_payments(customer_id: str):
    """Liste les echeances de remboursement (passees et a venir) d'un client."""
    customer = Customer.query.get(customer_id)
    if customer is None:
        raise not_found("Client", customer_id)

    payments = (
        CustomerPayment.query.filter_by(customer_id=customer_id)
        .order_by(CustomerPayment.due_date.desc())
        .all()
    )
    return jsonify(customer_payments_schema.dump(payments))


@sales_bp.post("/customers/<string:customer_id>/payments")
@require_permission("customers:write")
def create_customer_payment(customer_id: str):
    """Enregistre une echeance de remboursement a credit (RF-26).

    Alimente le suivi reel des remboursements utilise par le scoring de
    solvabilite (`app/ml/credit_scoring.py`), en remplacement de la
    simulation deterministe documentee en section 20.6.2.
    """
    customer = Customer.query.get(customer_id)
    if customer is None:
        raise not_found("Client", customer_id)

    payload = CustomerPaymentCreateSchema().load(request.get_json(silent=True) or {})

    sale = None
    if payload.get("sale_id"):
        sale = Sale.query.get(payload["sale_id"])
        if sale is None:
            raise not_found("Vente", payload["sale_id"])

    payment = CustomerPayment(
        customer_id=customer.id,
        sale_id=sale.id if sale else None,
        amount=payload["amount"],
        due_date=payload["due_date"],
        status=CustomerPaymentStatus.PENDING.value,
        note=payload.get("note"),
        recorded_by_id=get_jwt_identity(),
    )
    db.session.add(payment)

    AuditLog.record(
        event_type="CUSTOMER_PAYMENT_CREATED",
        user_id=get_jwt_identity(),
        entity_type="CustomerPayment",
        description=f"Echeance de remboursement de {payment.amount} creee pour {customer.full_name}",
    )
    db.session.commit()

    return jsonify(customer_payment_schema.dump(payment)), 201


@sales_bp.put("/customers/<string:customer_id>/payments/<string:payment_id>")
@require_permission("customers:write")
def update_customer_payment(customer_id: str, payment_id: str):
    """Enregistre le reglement (ou le retard/annulation) d'une echeance (RF-26).

    Lorsqu'une echeance passe a `PAID`, l'encours du client
    (`customer.credit_balance`) est diminue du montant regle (et reajuste en
    cas d'annulation d'un reglement deja enregistre).
    """
    payment = CustomerPayment.query.filter_by(id=payment_id, customer_id=customer_id).first()
    if payment is None:
        raise not_found("Echeance de remboursement", payment_id)

    payload = CustomerPaymentUpdateSchema().load(request.get_json(silent=True) or {})

    was_paid = payment.status == CustomerPaymentStatus.PAID.value
    payment.status = payload["status"]
    now_paid = payment.status == CustomerPaymentStatus.PAID.value

    if now_paid:
        payment.paid_date = payload.get("paid_date") or date.today()
        if not was_paid:
            payment.customer.credit_balance = max(
                Decimal("0"), payment.customer.credit_balance - payment.amount
            )
    else:
        if payload.get("paid_date"):
            payment.paid_date = payload["paid_date"]
        if was_paid:
            # Annulation d'un reglement deja comptabilise -> on reajuste l'encours.
            payment.customer.credit_balance = payment.customer.credit_balance + payment.amount

    AuditLog.record(
        event_type="CUSTOMER_PAYMENT_UPDATED",
        user_id=get_jwt_identity(),
        entity_type="CustomerPayment",
        entity_id=str(payment.id),
        description=f"Reglement {payment.id} mis a jour.",
    )
    db.session.commit()
    return jsonify(CustomerPaymentSchema().dump(payment)), 200


# ---------------------------------------------------------------------------
# Avoirs (retours) — gestion admin
# ---------------------------------------------------------------------------

@sales_bp.get('/refunds/pending')
@require_permission('sales:refund')
def list_pending_refunds():
    """Liste les avoirs en attente d'approbation (admin)."""
    from app.models import SaleStatus as _SS
    sales = (
        Sale.query.filter(Sale.status == _SS.EN_ATTENTE_APPROBATION.value)
        .order_by(Sale.created_at.desc())
        .all()
    )
    return jsonify(sales_schema.dump(sales))


@sales_bp.patch('/<string:sale_id>/refund/approve')
@require_permission('sales:refund')
def approve_refund_route(sale_id: str):
    """Approuve un avoir en attente et reintegre le stock (RG-27)."""
    refund = Sale.query.get(sale_id)
    if refund is None:
        raise not_found('Avoir', sale_id)
    updated = approve_refund(refund, admin_id=get_jwt_identity())
    return jsonify(sale_schema.dump(updated))


@sales_bp.patch('/<string:sale_id>/refund/reject')
@require_permission('sales:refund')
def reject_refund_route(sale_id: str):
    """Rejette un avoir en attente."""
    refund = Sale.query.get(sale_id)
    if refund is None:
        raise not_found('Avoir', sale_id)
    payload = request.get_json(silent=True) or {}
    reason = payload.get('reason', '')
    updated = reject_refund(refund, admin_id=get_jwt_identity(), reason=reason)
    return jsonify(sale_schema.dump(updated))


# ---------------------------------------------------------------------------
# Encours clients (credits)
# ---------------------------------------------------------------------------

@sales_bp.get('/credits')
@require_permission('customers:read', 'sales:read')
def list_credits():
    """Liste les clients ayant un encours de credit non nul (credit_balance > 0)."""
    from decimal import Decimal as _D
    query = Customer.query

    branch_id = request.args.get('branch_id')
    if branch_id:
        # Filtrer par site via les ventes a credit de ce client
        query = query.filter(Customer.credit_balance > _D('0'))
    else:
        query = query.filter(Customer.credit_balance > _D('0'))

    customer_type = request.args.get('customer_type')
    if customer_type:
        query = query.filter(Customer.customer_type == customer_type)

    customers = query.order_by(Customer.credit_balance.desc()).all()
    return jsonify(customers_schema.dump(customers))


@sales_bp.post('/customers/<string:customer_id>/settle')
@require_permission('customers:write', 'sales:create')
def settle_credit(customer_id: str):
    """Enregistre un remboursement partiel ou total de l'encours d'un client (RF-26).

    Payload : { amount: string (Decimal), note?: string }
    """
    from decimal import Decimal as _D, InvalidOperation
    customer = Customer.query.get(customer_id)
    if customer is None:
        raise not_found('Client', customer_id)

    payload = request.get_json(silent=True) or {}
    try:
        amount = _D(str(payload.get('amount', '0')))
    except InvalidOperation:
        from app.utils.errors import validation_error
        raise validation_error('Montant invalide.', details={'amount': payload.get('amount')})

    if amount <= 0:
        from app.utils.errors import validation_error
        raise validation_error('Le montant doit etre positif.', details={'amount': str(amount)})

    if amount > customer.credit_balance:
        amount = customer.credit_balance

    customer.credit_balance = max(_D('0'), customer.credit_balance - amount)

    AuditLog.record(
        event_type='CREDIT_SETTLED',
        user_id=get_jwt_identity(),
        entity_type='Customer',
        entity_id=customer.id,
        description=f"Reglement de {amount} FCFA sur l'encours de {customer.full_name}. Nouvel encours : {customer.credit_balance} FCFA.",
        metadata={'amount': str(amount), 'note': payload.get('note', '')},
    )
    db.session.commit()

    return jsonify({
        'customer_id': customer.id,
        'amount_settled': str(amount),
        'new_credit_balance': str(customer.credit_balance),
    })
