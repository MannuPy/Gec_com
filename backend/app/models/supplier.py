"""Modeles fournisseurs et receptions de marchandises."""
import enum

from app.extensions import db
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin


class Supplier(db.Model, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "suppliers"

    name = db.Column(db.String(120), nullable=False)
    contact_name = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(32), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)


class ReceptionStatus(str, enum.Enum):
    BROUILLON = "BROUILLON"
    VALIDEE = "VALIDEE"


class SupplierReception(db.Model, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "supplier_receptions"

    reference = db.Column(db.String(32), unique=True, nullable=False)
    supplier_id = db.Column(db.String(36), db.ForeignKey("suppliers.id"), nullable=False)
    branch_id = db.Column(db.String(36), db.ForeignKey("branches.id"), nullable=False)
    status = db.Column(db.String(16), nullable=False, default=ReceptionStatus.BROUILLON.value)
    received_at = db.Column(db.DateTime, nullable=True)
    created_by_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)

    supplier = db.relationship("Supplier", lazy="joined")
    branch = db.relationship("Branch", lazy="joined")
    lines = db.relationship(
        "SupplierReceptionLine", backref="reception", cascade="all, delete-orphan", lazy="joined"
    )


class SupplierReceptionLine(db.Model, UUIDPrimaryKeyMixin):
    __tablename__ = "supplier_reception_lines"

    reception_id = db.Column(
        db.String(36), db.ForeignKey("supplier_receptions.id"), nullable=False
    )
    product_id = db.Column(db.String(36), db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_purchase_price = db.Column(db.Numeric(12, 2), nullable=False)

    product = db.relationship("Product", lazy="joined")

    __table_args__ = (
        db.CheckConstraint("quantity > 0", name="ck_supplier_reception_line_qty_positive"),
    )
