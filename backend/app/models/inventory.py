"""Inventaire physique (RF-21 a RF-23)."""
import enum

from app.extensions import db
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin


class StockCountStatus(str, enum.Enum):
    EN_COURS = "EN_COURS"
    VALIDE = "VALIDE"
    ANNULE = "ANNULE"   # Session abandonnée sans ajustement de stock


class StockCount(db.Model, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "stock_counts"

    reference = db.Column(db.String(32), unique=True, nullable=False)
    branch_id = db.Column(db.String(36), db.ForeignKey("branches.id"), nullable=False)
    status = db.Column(db.String(16), nullable=False, default=StockCountStatus.EN_COURS.value)

    created_by_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    validated_by_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)
    validated_at = db.Column(db.DateTime, nullable=True)
    cancelled_by_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)

    branch = db.relationship("Branch", lazy="joined")
    created_by = db.relationship("User", foreign_keys=[created_by_id], lazy="joined")
    validated_by = db.relationship("User", foreign_keys=[validated_by_id], lazy="joined")
    cancelled_by = db.relationship("User", foreign_keys=[cancelled_by_id], lazy="joined")
    lines = db.relationship(
        "StockCountLine", backref="stock_count", cascade="all, delete-orphan", lazy="joined"
    )

    def __repr__(self) -> str:
        return "<StockCount " + self.reference + " (" + self.status + ")>"


class StockCountLine(db.Model, UUIDPrimaryKeyMixin):
    __tablename__ = "stock_count_lines"

    stock_count_id = db.Column(db.String(36), db.ForeignKey("stock_counts.id"), nullable=False)
    product_id = db.Column(db.String(36), db.ForeignKey("products.id"), nullable=False)

    theoretical_quantity = db.Column(db.Integer, nullable=False, default=0)
    counted_quantity = db.Column(db.Integer, nullable=True)
    variance = db.Column(db.Integer, nullable=True)
    comment = db.Column(db.String(255), nullable=True)

    product = db.relationship("Product", lazy="joined")

    __table_args__ = (
        db.UniqueConstraint(
            "stock_count_id", "product_id",
            name="uq_stock_count_line_product",
        ),
    )
