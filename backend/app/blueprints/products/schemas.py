"""Schemas marshmallow pour le blueprint products (catalogue)."""
from marshmallow import Schema, fields, validate


class BranchSchema(Schema):
    id = fields.String()
    name = fields.String()
    code = fields.String()
    is_depot = fields.Boolean()
    address = fields.String(allow_none=True)
    phone = fields.String(allow_none=True)
    is_active = fields.Boolean()


class CategorySchema(Schema):
    id = fields.String()
    name = fields.String()
    description = fields.String(allow_none=True)


class CategoryWriteSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=2, max=120))
    description = fields.String(allow_none=True, load_default=None)


class BrandSchema(Schema):
    id = fields.String()
    name = fields.String()


class BrandWriteSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=120))


PRODUCT_UNITS = ["UNITE", "BOITE", "SAC", "LITRE", "METRE", "KG"]


class ProductSchema(Schema):
    id = fields.String()
    sku = fields.String()
    barcode = fields.String(allow_none=True)
    name = fields.String()
    name_moore = fields.String(allow_none=True)
    description = fields.String(allow_none=True)
    category_id = fields.String(allow_none=True)
    category_name = fields.Method("get_category_name")
    brand_id = fields.String(allow_none=True)
    brand_name = fields.Method("get_brand_name")
    unit = fields.String()
    simple_price = fields.Decimal(as_string=True)
    technician_price = fields.Decimal(as_string=True)
    purchase_price = fields.Decimal(as_string=True)
    min_stock_threshold = fields.Integer()
    is_active = fields.Boolean()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None

    def get_brand_name(self, obj):
        return obj.brand.name if obj.brand else None


class ProductCreateSchema(Schema):
    sku = fields.String(required=True, validate=validate.Length(min=1, max=32))
    barcode = fields.String(allow_none=True, load_default=None, validate=validate.Length(max=64))
    name = fields.String(required=True, validate=validate.Length(min=2, max=255))
    name_moore = fields.String(allow_none=True, load_default=None, validate=validate.Length(max=255))
    description = fields.String(allow_none=True, load_default=None)
    category_id = fields.String(allow_none=True, load_default=None)
    brand_id = fields.String(allow_none=True, load_default=None)
    unit = fields.String(load_default="UNITE", validate=validate.OneOf(PRODUCT_UNITS))
    simple_price = fields.Decimal(required=True, places=2, as_string=True)
    technician_price = fields.Decimal(required=True, places=2, as_string=True)
    purchase_price = fields.Decimal(load_default="0", places=2, as_string=True)
    min_stock_threshold = fields.Integer(load_default=0, validate=validate.Range(min=0))


class ProductUpdateSchema(Schema):
    barcode = fields.String(allow_none=True, validate=validate.Length(max=64))
    name = fields.String(validate=validate.Length(min=2, max=255))
    name_moore = fields.String(allow_none=True, validate=validate.Length(max=255))
    description = fields.String(allow_none=True)
    category_id = fields.String(allow_none=True)
    brand_id = fields.String(allow_none=True)
    unit = fields.String(validate=validate.OneOf(PRODUCT_UNITS))
    simple_price = fields.Decimal(places=2, as_string=True)
    technician_price = fields.Decimal(places=2, as_string=True)
    purchase_price = fields.Decimal(places=2, as_string=True)
    min_stock_threshold = fields.Integer(validate=validate.Range(min=0))
    is_active = fields.Boolean()


__all__ = [
    "BranchSchema",
    "CategorySchema",
    "CategoryWriteSchema",
    "BrandSchema",
    "BrandWriteSchema",
    "ProductSchema",
    "ProductCreateSchema",
    "ProductUpdateSchema",
]
