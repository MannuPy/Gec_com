"""
Modeles du coeur metier : clients et ventes.

Cf. 12-MCD.md (CLIENT, VENTE, LIGNE_VENTE) et 04-REGLES-METIER.md
(RG-21 a RG-30). La logique de validation est implementee dans
`app/services/sale_service.py` - ces modeles restent volontairement
"passifs" (pas de logique metier dans les modeles, cf. 09-BACKEND-FLASK.md
section couches routes -> schemas -> services -> models).
"""
import enum

from app.extensions import db
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin


class CustomerType(str, enum.Enum):
    SIMPLE = "SIMPLE"
    TECHNICIEN = "TECHNICIEN"


class Customer(db.Model, UUIDPrimaryKeyMixin, TimestampMixin):
    """Client (RG-26 : requis pour toute vente a credit)."""

    __tablename__ = "customers"

    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(32), nullable=True, unique=True)
    customer_type = db.Column(db.String(16), nullable=False, default=CustomerType.SIMPLE.value)

    credit_balance = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    credit_limit = db.Column(db.Numeric(12, 2), nullable=False, default=0)

    __table_args__ = (
        db.CheckConstraint("credit_balance >= 0", name="ck_customer_credit_balance_non_negative"),
    )


class PaymentType(str, enum.Enum):
    CASH = "CASH"
    CREDIT = "CREDIT"


class SaleStatus(str, enum.Enum):
    VALIDEE = "VALIDEE"
    ANNULEE = "ANNULEE"
    AVOIR_EMIS = "AVOIR_EMIS"
    EN_ATTENTE_SYNC = "EN_ATTENTE_SYNC"
    EN_CONFLIT = "EN_CONFLIT"
    EN_ATTENTE_APPROBATION = "EN_ATTENTE_APPROBATION"


class SaleChannel(str, enum.Enum):
    """Canal d'origine de la vente (RF-20, RG-28 a RG-30)."""

    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"


class Sale(db.Model, UUIDPrimaryKeyMixin):
    """Vente (UC-11 a UC-13).

    Une vente VALIDEE est **immuable** (RG-27) : toute correction passe par
    un avoir (statut AVOIR_EMIS referencant la vente d'origine), jamais par
    une modification directe.
    """

    __tablename__ = "sales"

    reference = db.Column(db.String(32), unique=True, nullable=False)

    branch_id = db.Column(db.String(36), db.ForeignKey("branches.id"), nullable=False)
    cashier_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    customer_id = db.Column(db.String(36), db.ForeignKey("customers.id"), nullable=True)

    subtotal = db.Column(db.Numeric(12, 2), nullable=False)
    discount_rate = db.Column(db.Integer, nullable=False, default=0)
    discount_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    total = db.Column(db.Numeric(12, 2), nullable=False)

    payment_type = db.Column(db.String(16), nullable=False, default=PaymentType.CASH.value)
    status = db.Column(db.String(32), nullable=False, default=SaleStatus.VALIDEE.value)

    # RG-23 : remise >= seuil necessite l'identifiant de l'approbateur
    approved_by_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)

    # RG-28 : idempotence de la synchronisation hors-ligne
    offline_uuid = db.Column(db.String(36), unique=True, nullable=True, index=True)

    # RF-20 : canal d'origine (caisse en ligne ou vente saisie hors-ligne puis synchronisee)
    channel = db.Column(db.String(10), nullable=False, default=SaleChannel.ONLINE.value)

    # Reference a la vente d'origine en cas d'avoir
    refund_of_sale_id = db.Column(db.String(36), db.ForeignKey("sales.id"), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now()
    )

    branch = db.relationship("Branch", lazy="joined")
    cashier = db.relationship("User", foreign_keys=[cashier_id], lazy="joined")
    customer = db.relationship("Customer", lazy="joined")
    approved_by = db.relationship("User", foreign_keys=[approved_by_id], lazy="joined")
    lines = db.relationship(
        "SaleLine", backref="sale", cascade="all, delete-orphan", lazy="joined"
    )

    __table_args__ = (
        db.CheckConstraint("subtotal >= 0", name="ck_sale_subtotal_non_negative"),
        db.CheckConstraint("total >= 0", name="ck_sale_total_non_negative"),
        db.CheckConstraint(
            "discount_rate IN (0, 5, 10, 15, 20)", name="ck_sale_discount_rate_allowed"
        ),
        db.CheckConstraint("channel IN ('ONLINE', 'OFFLINE')", name="ck_sale_channel_allowed"),
    )


class CustomerPaymentStatus(str, enum.Enum):
    """Statut d'une echeance de remboursement a credit (RF-26)."""

    PENDING = "PENDING"
    PAID = "PAID"
    LATE = "LATE"
    CANCELLED = "CANCELLED"


class CustomerPayment(db.Model, UUIDPrimaryKeyMixin, TimestampMixin):
    """Echeance / reglement de remboursement de credit client (RF-26).

    Remplace la simulation deterministe documentee en section 20.6.2 :
    `taux_retard` et `delai_moyen_remboursement_jours` (cf.
    `app/ml/credit_scoring.py`) sont desormais calculables a partir de
    l'historique reel des echeances (echeance `due_date` vs reglement
    effectif `paid_date`).
    """

    __tablename__ = "customer_payments"

    customer_id = db.Column(db.String(36), db.ForeignKey("customers.id"), nullable=False, index=True)
    # Vente a credit a l'origine de cette echeance (nullable : une echeance
    # peut aussi correspondre a un reglement global de l'encours).
    sale_id = db.Column(db.String(36), db.ForeignKey("sales.id"), nullable=True)

    amount = db.Column(db.Numeric(12, 2), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    paid_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(16), nullable=False, default=CustomerPaymentStatus.PENDING.value)

    recorded_by_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)
    note = db.Column(db.String(255), nullable=True)

    customer = db.relationship("Customer", lazy="joined")
    sale = db.relationship("Sale", lazy="joined")
    recorded_by = db.relationship("User", lazy="joined")

    __table_args__ = (
        db.CheckConstraint("amount > 0", name="ck_customer_payment_amount_positive"),
        db.CheckConstraint(
            "status IN ('PENDING', 'PAID', 'LATE', 'CANCELLED')",
            name="ck_customer_payment_status_allowed",
        ),
    )


class SaleLine(db.Model, UUIDPrimaryKeyMixin):
    __tablename__ = "sale_lines"

    sale_id = db.Column(db.String(36), db.ForeignKey("sales.id"), nullable=False)
    product_id = db.Column(db.String(36), db.ForeignKey("products.id"), nullable=False)

    quantity = db.Column(db.Integer, nullable=False)
    # RG-21 : prix fige au moment de la vente (immutabilite, independant des
    # evolutions futures du tarif catalogue)
    unit_price_applied = db.Column(db.Numeric(12, 2), nullable=False)
    price_type = db.Column(db.String(16), nullable=False, default=CustomerType.SIMPLE.value)
    line_total = db.Column(db.Numeric(12, 2), nullable=False)

    product = db.relationship("Product", lazy="joined")

    __table_args__ = (
        db.CheckConstraint("quantity > 0", name="ck_sale_line_quantity_positive"),
        db.CheckConstraint("unit_price_applied >= 0", name="ck_sale_line_price_non_negative"),
    )
