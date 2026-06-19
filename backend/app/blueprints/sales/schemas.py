"""Schemas marshmallow pour le blueprint sales (ventes et clients)."""
from marshmallow import Schema, fields, validate


class CustomerSchema(Schema):
    id = fields.String()
    full_name = fields.String()
    phone = fields.String(allow_none=True)
    customer_type = fields.String()
    credit_balance = fields.Decimal(as_string=True)
    credit_limit = fields.Decimal(as_string=True)
    created_at = fields.DateTime()


class CustomerWriteSchema(Schema):
    full_name = fields.String(required=True, validate=validate.Length(min=2, max=120))
    phone = fields.String(allow_none=True, load_default=None, validate=validate.Length(max=32))
    customer_type = fields.String(load_default="SIMPLE", validate=validate.OneOf(["SIMPLE", "TECHNICIEN"]))
    credit_limit = fields.Decimal(load_default="0", places=2, as_string=True, validate=validate.Range(min=0))


class CustomerPaymentSchema(Schema):
    id = fields.String()
    customer_id = fields.String()
    sale_id = fields.String(allow_none=True)
    sale_reference = fields.Method("get_sale_reference")
    amount = fields.Decimal(as_string=True)
    due_date = fields.Date()
    paid_date = fields.Date(allow_none=True)
    status = fields.String()
    note = fields.String(allow_none=True)
    created_at = fields.DateTime()

    def get_sale_reference(self, obj):
        return obj.sale.reference if obj.sale else None


class CustomerPaymentCreateSchema(Schema):
    sale_id = fields.String(allow_none=True, load_default=None)
    amount = fields.Decimal(required=True, places=2, as_string=True, validate=validate.Range(min=0.01))
    due_date = fields.Date(required=True)
    note = fields.String(allow_none=True, load_default=None, validate=validate.Length(max=255))


class CustomerPaymentUpdateSchema(Schema):
    status = fields.String(
        required=True, validate=validate.OneOf(["PENDING", "PAID", "LATE", "CANCELLED"])
    )
    paid_date = fields.Date(allow_none=True, load_default=None)


class SaleLineCreateSchema(Schema):
    product_id = fields.String(required=True)
    quantity = fields.Integer(required=True, validate=validate.Range(min=1))


class SaleCreateSchema(Schema):
    branch_id = fields.String(required=True)
    customer_id = fields.String(allow_none=True, load_default=None)
    payment_type = fields.String(load_default="CASH", validate=validate.OneOf(["CASH", "CREDIT"]))
    discount_rate = fields.Integer(load_default=0, validate=validate.Range(min=0, max=100))
    lines = fields.List(
        fields.Nested(SaleLineCreateSchema), required=True, validate=validate.Length(min=1)
    )


class SaleSyncLineSchema(Schema):
    product_id = fields.String(required=True)
    quantity = fields.Integer(required=True, validate=validate.Range(min=1))


class SaleSyncItemSchema(Schema):
    offline_uuid = fields.String(required=True, validate=validate.Length(min=1, max=36))
    branch_id = fields.String(required=True)
    customer_id = fields.String(allow_none=True, load_default=None)
    payment_type = fields.String(load_default="CASH", validate=validate.OneOf(["CASH", "CREDIT"]))
    discount_rate = fields.Integer(load_default=0, validate=validate.Range(min=0, max=100))
    created_at_local = fields.DateTime(allow_none=True, load_default=None)
    lines = fields.List(
        fields.Nested(SaleSyncLineSchema), required=True, validate=validate.Length(min=1)
    )


class SaleSyncBatchSchema(Schema):
    sales = fields.List(
        fields.Nested(SaleSyncItemSchema), required=True, validate=validate.Length(min=1)
    )


class SaleSyncResultSchema(Schema):
    offline_uuid = fields.String()
    status = fields.String()
    sale_id = fields.String(allow_none=True)
    message = fields.String(allow_none=True)


class RefundLineSchema(Schema):
    product_id = fields.String(required=True)
    quantity = fields.Integer(required=True, validate=validate.Range(min=1))


class RefundCreateSchema(Schema):
    lines = fields.List(
        fields.Nested(RefundLineSchema), required=True, validate=validate.Length(min=1)
    )
    reason = fields.String(required=True, validate=validate.Length(min=3, max=255))


class SaleLineSchema(Schema):
    id = fields.String()
    product_id = fields.String()
    product_sku = fields.Method("get_product_sku")
    product_name = fields.Method("get_product_name")
    quantity = fields.Integer()
    unit_price_applied = fields.Decimal(as_string=True)
    price_type = fields.String()
    line_total = fields.Decimal(as_string=True)

    def get_product_sku(self, obj):
        return obj.product.sku

    def get_product_name(self, obj):
        return obj.product.name


class SaleSchema(Schema):
    id = fields.String()
    reference = fields.String()
    branch_id = fields.String()
    branch_name = fields.Method("get_branch_name")
    cashier_id = fields.String()
    cashier_name = fields.Method("get_cashier_name")
    customer_id = fields.String(allow_none=True)
    customer_name = fields.Method("get_customer_name")
    subtotal = fields.Decimal(as_string=True)
    discount_rate = fields.Integer()
    discount_amount = fields.Decimal(as_string=True)
    total = fields.Decimal(as_string=True)
    payment_type = fields.String()
    status = fields.String()
    channel = fields.String()
    offline_uuid = fields.String(allow_none=True)
    refund_of_sale_id = fields.String(allow_none=True)
    created_at = fields.DateTime()
    lines = fields.List(fields.Nested(SaleLineSchema))

    def get_branch_name(self, obj):
        return obj.branch.name

    def get_cashier_name(self, obj):
        return obj.cashier.full_name

    def get_customer_name(self, obj):
        return obj.customer.full_name if obj.customer else None
