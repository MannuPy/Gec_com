"""Schemas marshmallow pour le blueprint inventory (RF-21 a RF-23)."""
from marshmallow import Schema, fields, validate


class StockCountLineSchema(Schema):
    id = fields.String()
    product_id = fields.String()
    product_sku = fields.Method("get_product_sku")
    product_name = fields.Method("get_product_name")
    theoretical_quantity = fields.Integer()
    counted_quantity = fields.Integer(allow_none=True)
    variance = fields.Integer(allow_none=True)
    variance_pct = fields.Method("get_variance_pct")
    comment = fields.String(allow_none=True)

    def get_product_sku(self, obj):
        return obj.product.sku

    def get_product_name(self, obj):
        return obj.product.name

    def get_variance_pct(self, obj):
        if obj.variance is None:
            return None
        base = obj.theoretical_quantity or 1
        return round(abs(obj.variance) / base * 100, 2)


class StockCountSchema(Schema):
    id = fields.String()
    reference = fields.String()
    branch_id = fields.String()
    branch_name = fields.Method("get_branch_name")
    status = fields.String()
    created_by_id = fields.String()
    created_by_name = fields.Method("get_created_by_name")
    validated_by_id = fields.String(allow_none=True)
    validated_by_name = fields.Method("get_validated_by_name")
    validated_at = fields.DateTime(allow_none=True)
    cancelled_by_id = fields.String(allow_none=True)
    cancelled_by_name = fields.Method("get_cancelled_by_name")
    created_at = fields.DateTime()
    lines_count = fields.Method("get_lines_count")
    lines_with_variance = fields.Method("get_lines_with_variance")

    def get_branch_name(self, obj):
        return obj.branch.name

    def get_created_by_name(self, obj):
        return obj.created_by.full_name

    def get_validated_by_name(self, obj):
        return obj.validated_by.full_name if obj.validated_by else None

    def get_cancelled_by_name(self, obj):
        return obj.cancelled_by.full_name if obj.cancelled_by else None

    def get_lines_count(self, obj):
        return len(obj.lines)

    def get_lines_with_variance(self, obj):
        return sum(1 for line in obj.lines if line.variance not in (None, 0))


class StockCountDetailSchema(StockCountSchema):
    lines = fields.Nested(StockCountLineSchema, many=True)


class StockCountCreateSchema(Schema):
    branch_id = fields.String(required=True)


class StockCountLineUpdateSchema(Schema):
    product_id = fields.String(required=True)
    counted_quantity = fields.Integer(required=True, validate=validate.Range(min=0))
    comment = fields.String(allow_none=True, validate=validate.Length(max=255))


class StockCountLinesUpdateSchema(Schema):
    lines = fields.List(fields.Nested(StockCountLineUpdateSchema))
