"""Schémas marshmallow pour le blueprint `stock`."""
from marshmallow import Schema, fields, validate


class StockItemSchema(Schema):
    id = fields.String()
    product_id = fields.String()
    product_sku = fields.Method("get_product_sku")
    product_name = fields.Method("get_product_name")
    branch_id = fields.String()
    branch_name = fields.Method("get_branch_name")
    quantity = fields.Integer()
    min_stock_threshold = fields.Method("get_min_stock_threshold")
    below_min = fields.Method("get_below_min")

    def get_product_sku(self, obj):
        return obj.product.sku if obj.product else ""

    def get_product_name(self, obj):
        return obj.product.name if obj.product else "Produit supprime"

    def get_branch_name(self, obj):
        return obj.branch.name if obj.branch else ""

    def get_min_stock_threshold(self, obj):
        return obj.product.min_stock_threshold if obj.product else 0

    def get_below_min(self, obj):
        return obj.quantity < obj.product.min_stock_threshold if obj.product else False


class StockMovementSchema(Schema):
    id = fields.String()
    product_id = fields.String()
    product_name = fields.Method("get_product_name")
    branch_id = fields.String()
    branch_name = fields.Method("get_branch_name")
    movement_type = fields.String()
    quantity = fields.Integer()
    reference_type = fields.String(allow_none=True)
    reference_id = fields.String(allow_none=True)
    comment = fields.String(allow_none=True)
    created_at = fields.DateTime()

    def get_product_name(self, obj):
        return obj.product.name if obj.product else "Produit supprime"

    def get_branch_name(self, obj):
        return obj.branch.name if obj.branch else ""


class StockAdjustmentSchema(Schema):
    product_id = fields.String(required=True)
    branch_id = fields.String(required=True)
    quantity_delta = fields.Integer(
        required=True,
        validate=validate.NoneOf([0], error="La quantité d'ajustement ne peut pas être nulle."),
    )
    comment = fields.String(required=True, validate=validate.Length(min=3, max=255))
