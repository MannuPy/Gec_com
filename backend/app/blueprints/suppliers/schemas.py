"""Schémas marshmallow pour le blueprint `suppliers` (fournisseurs, réceptions)."""
from marshmallow import Schema, fields, validate


class SupplierSchema(Schema):
    id = fields.String()
    name = fields.String()
    contact_name = fields.String(allow_none=True)
    phone = fields.String(allow_none=True)
    email = fields.String(allow_none=True)
    address = fields.String(allow_none=True)
    is_active = fields.Boolean()


class SupplierWriteSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=2, max=120))
    contact_name = fields.String(allow_none=True, load_default=None)
    phone = fields.String(allow_none=True, load_default=None, validate=validate.Length(max=32))
    email = fields.Email(allow_none=True, load_default=None)
    address = fields.String(allow_none=True, load_default=None)
    is_active = fields.Boolean(load_default=True)


class ReceptionLineWriteSchema(Schema):
    product_id = fields.String(required=True)
    quantity = fields.Integer(required=True, validate=validate.Range(min=1))
    unit_purchase_price = fields.Decimal(required=True, places=2, as_string=True)


class ReceptionCreateSchema(Schema):
    supplier_id = fields.String(required=True)
    branch_id = fields.String(required=True)
    lines = fields.List(
        fields.Nested(ReceptionLineWriteSchema), required=True, validate=validate.Length(min=1)
    )


class ReceptionLineSchema(Schema):
    id = fields.String()
    product_id = fields.String()
    product_sku = fields.Method("get_product_sku")
    product_name = fields.Method("get_product_name")
    quantity = fields.Integer()
    unit_purchase_price = fields.Decimal(as_string=True)

    def get_product_sku(self, obj):
        return obj.product.sku

    def get_product_name(self, obj):
        return obj.product.name


class ReceptionSchema(Schema):
    id = fields.String()
    reference = fields.String()
    supplier_id = fields.String()
    supplier_name = fields.Method("get_supplier_name")
    branch_id = fields.String()
    branch_name = fields.Method("get_branch_name")
    status = fields.String()
    received_at = fields.DateTime(allow_none=True)
    created_at = fields.DateTime()
    lines = fields.List(fields.Nested(ReceptionLineSchema))
    total_amount = fields.Method("get_total_amount")

    def get_supplier_name(self, obj):
        return obj.supplier.name

    def get_branch_name(self, obj):
        return obj.branch.name

    def get_total_amount(self, obj):
        return str(sum((line.quantity * line.unit_purchase_price) for line in obj.lines))
