"""Schémas marshmallow pour le blueprint `transfers`."""
from marshmallow import Schema, fields, validate


class TransferLineWriteSchema(Schema):
    product_id = fields.String(required=True)
    quantity_sent = fields.Integer(required=True, validate=validate.Range(min=1))


class TransferCreateSchema(Schema):
    source_branch_id = fields.String(required=True)
    destination_branch_id = fields.String(required=True)
    lines = fields.List(
        fields.Nested(TransferLineWriteSchema), required=True, validate=validate.Length(min=1)
    )


class ReceiveLineSchema(Schema):
    line_id = fields.String(required=True)
    quantity_received = fields.Integer(required=True, validate=validate.Range(min=0))
    variance_comment = fields.String(allow_none=True, load_default=None)


class TransferReceiveSchema(Schema):
    lines = fields.List(
        fields.Nested(ReceiveLineSchema), required=True, validate=validate.Length(min=1)
    )


class TransferLineSchema(Schema):
    id = fields.String()
    product_id = fields.String()
    product_sku = fields.Method("get_product_sku")
    product_name = fields.Method("get_product_name")
    quantity_sent = fields.Integer()
    quantity_received = fields.Integer(allow_none=True)
    variance_comment = fields.String(allow_none=True)

    def get_product_sku(self, obj):
        return obj.product.sku

    def get_product_name(self, obj):
        return obj.product.name


class TransferSchema(Schema):
    id = fields.String()
    reference = fields.String()
    source_branch_id = fields.String()
    source_branch_name = fields.Method("get_source_branch_name")
    destination_branch_id = fields.String()
    destination_branch_name = fields.Method("get_destination_branch_name")
    status = fields.String()
    created_at = fields.DateTime()
    sent_at = fields.DateTime(allow_none=True)
    received_at = fields.DateTime(allow_none=True)
    lines = fields.List(fields.Nested(TransferLineSchema))

    def get_source_branch_name(self, obj):
        return obj.source_branch.name

    def get_destination_branch_name(self, obj):
        return obj.destination_branch.name if obj.destination_branch else None
