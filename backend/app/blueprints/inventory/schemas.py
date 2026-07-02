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
        return obj.product.sku if obj.product else ""

    def get_product_name(self, obj):
        return obj.product.name if obj.product else "Produit supprime"

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
    cancelled_at = fields.DateTime(allow_none=True)
    created_at = fields.DateTime()
    lines_count = fields.Method("get_lines_count")
    lines_with_variance = fields.Method("get_lines_with_variance")

    def get_branch_name(self, obj):
        return obj.branch.name if obj.branch else ""

    def get_created_by_name(self, obj):
        return obj.created_by.full_name if obj.created_by else ""

    def get_validated_by_name(self, obj):
        return obj.validated_by.full_name if obj.validated_by else None

    def get_cancelled_by_name(self, obj):
        return obj.cancelled_by.full_name if obj.cancelled_by else None

    def get_lines_count(self, obj):
        # Vue liste : evite de charger toutes les lignes en memoire.
        # Si les lignes sont deja en cache SQLAlchemy (vue detail), len() suffit.
        from sqlalchemy import inspect as sa_inspect
        try:
            attr = sa_inspect(obj).attrs.get("lines")
            if attr is not None and attr.loaded_value is not None:
                return len(obj.lines)
        except Exception:
            pass
        # Fallback propre : sous-requete COUNT
        from app.extensions import db
        from app.models.inventory import StockCountLine
        return db.session.query(StockCountLine).filter_by(stock_count_id=obj.id).count()

    def get_lines_with_variance(self, obj):
        # Meme optimisation : sous-requete au lieu d un chargement complet.
        from sqlalchemy import inspect as sa_inspect
        try:
            attr = sa_inspect(obj).attrs.get("lines")
            if attr is not None and attr.loaded_value is not None:
                return sum(1 for line in obj.lines if line.variance not in (None, 0))
        except Exception:
            pass
        from app.extensions import db
        from app.models.inventory import StockCountLine
        return (
            db.session.query(StockCountLine)
            .filter(
                StockCountLine.stock_count_id == obj.id,
                StockCountLine.variance.isnot(None),
                StockCountLine.variance != 0,
            )
            .count()
        )


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
