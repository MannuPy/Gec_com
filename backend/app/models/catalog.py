"""Modeles du catalogue produit, des sites et du stock."""
import enum

from sqlalchemy import event

from app.extensions import db
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin
from app.utils.phonetic import phonetic_code


class Branch(db.Model, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "branches"

    name = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(16), unique=True, nullable=False)
    is_depot = db.Column(db.Boolean, nullable=False, default=False)
    address = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(32), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return "<Branch " + self.code + " - " + self.name + ">"


class Category(db.Model, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "categories"

    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)


class Brand(db.Model, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "brands"

    name = db.Column(db.String(120), unique=True, nullable=False)


class ProductUnit(str, enum.Enum):
    UNITE = "UNITE"
    BOITE = "BOITE"
    SAC = "SAC"
    LITRE = "LITRE"
    METRE = "METRE"
    KG = "KG"


class Product(db.Model, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "products"

    sku = db.Column(db.String(32), unique=True, nullable=False, index=True)
    barcode = db.Column(db.String(64), unique=True, nullable=True, index=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    name_moore = db.Column(db.String(255), nullable=True)
    name_phonetic = db.Column(db.String(255), nullable=True, index=True)
    description = db.Column(db.Text, nullable=True)

    category_id = db.Column(db.String(36), db.ForeignKey("categories.id"), nullable=True)
    brand_id = db.Column(db.String(36), db.ForeignKey("brands.id"), nullable=True)

    category = db.relationship("Category", lazy="joined")
    brand = db.relationship("Brand", lazy="joined")

    unit = db.Column(db.String(16), nullable=False, default=ProductUnit.UNITE.value)

    simple_price = db.Column(db.Numeric(12, 2), nullable=False)
    technician_price = db.Column(db.Numeric(12, 2), nullable=False)
    purchase_price = db.Column(db.Numeric(12, 2), nullable=False, default=0)

    min_stock_threshold = db.Column(db.Integer, nullable=False, default=0)

    is_active = db.Column(db.Boolean, nullable=False, default=True)

    __table_args__ = (
        db.CheckConstraint("simple_price >= 0", name="ck_products_simple_price_positive"),
        db.CheckConstraint("technician_price >= 0", name="ck_products_technician_price_positive"),
        db.CheckConstraint("technician_price <= simple_price", name="ck_products_technician_le_simple"),
    )

    def price_for(self, customer_type: str):
        return self.technician_price if customer_type == "TECHNICIEN" else self.simple_price

    def __repr__(self) -> str:
        return "<Product " + self.sku + " - " + self.name + ">"


@event.listens_for(Product, "before_insert")
@event.listens_for(Product, "before_update")
def _product_compute_name_phonetic(mapper, connection, target):
    target.name_phonetic = phonetic_code(target.name)


class Stock(db.Model, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "stock"

    product_id = db.Column(db.String(36), db.ForeignKey("products.id"), nullable=False)
    branch_id = db.Column(db.String(36), db.ForeignKey("branches.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)

    product = db.relationship("Product", lazy="joined")
    branch = db.relationship("Branch", lazy="joined")

    __table_args__ = (
        db.UniqueConstraint("product_id", "branch_id", name="uq_stock_product_branch"),
    )


class StockMovementType(str, enum.Enum):
    ENTREE_RECEPTION = "ENTREE_RECEPTION"
    SORTIE_TRANSFERT = "SORTIE_TRANSFERT"
    ENTREE_TRANSFERT = "ENTREE_TRANSFERT"
    SORTIE_VENTE = "SORTIE_VENTE"
    ENTREE_RETOUR_VENTE = "ENTREE_RETOUR_VENTE"
    AJUSTEMENT_INVENTAIRE = "AJUSTEMENT_INVENTAIRE"
    AJUSTEMENT_MANUEL = "AJUSTEMENT_MANUEL"


class StockMovement(db.Model, UUIDPrimaryKeyMixin):
    __tablename__ = "stock_movements"

    product_id = db.Column(db.String(36), db.ForeignKey("products.id"), nullable=False)
    branch_id = db.Column(db.String(36), db.ForeignKey("branches.id"), nullable=False)
    movement_type = db.Column(db.String(32), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    reference_type = db.Column(db.String(32), nullable=True)
    reference_id = db.Column(db.String(36), nullable=True)

    created_by_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    comment = db.Column(db.String(255), nullable=True)
