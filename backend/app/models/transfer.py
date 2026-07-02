"""Modeles de transferts inter-sites."""
import enum

from app.extensions import db
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin


class TransferStatus(str, enum.Enum):
    BROUILLON = "BROUILLON"
    EN_TRANSIT = "EN_TRANSIT"
    RECU = "RECU"
    ANNULE = "ANNULE"


class Transfer(db.Model, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "transfers"

    reference = db.Column(db.String(32), unique=True, nullable=False)
    source_branch_id = db.Column(db.String(36), db.ForeignKey("branches.id"), nullable=False)
    destination_branch_id = db.Column(
        db.String(36), db.ForeignKey("branches.id"), nullable=False
    )
    status = db.Column(db.String(16), nullable=False, default=TransferStatus.BROUILLON.value)

    created_by_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    sent_at = db.Column(db.DateTime, nullable=True)
    received_by_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)
    received_at = db.Column(db.DateTime, nullable=True)

    source_branch = db.relationship("Branch", foreign_keys=[source_branch_id], lazy="joined")
    destination_branch = db.relationship(
        "Branch", foreign_keys=[destination_branch_id], lazy="joined"
    )
    created_by = db.relationship("User", foreign_keys=[created_by_id], lazy="joined")
    received_by = db.relationship("User", foreign_keys=[received_by_id], lazy="joined")
    lines = db.relationship(
        "TransferLine", backref="transfer", cascade="all, delete-orphan", lazy="joined"
    )

    __table_args__ = (
        db.CheckConstraint(
            "source_branch_id != destination_branch_id",
            name="ck_transfer_source_destination_distinct",
        ),
    )


class TransferLine(db.Model, UUIDPrimaryKeyMixin):
    __tablename__ = "transfer_lines"

    transfer_id = db.Column(db.String(36), db.ForeignKey("transfers.id"), nullable=False)
    product_id = db.Column(db.String(36), db.ForeignKey("products.id"), nullable=False)

    quantity_sent = db.Column(db.Integer, nullable=False)
    quantity_received = db.Column(db.Integer, nullable=True)
    variance_comment = db.Column(db.String(255), nullable=True)

    product = db.relationship("Product", lazy="joined")

    __table_args__ = (
        db.CheckConstraint("quantity_sent > 0", name="ck_transfer_line_qty_positive"),
    )
