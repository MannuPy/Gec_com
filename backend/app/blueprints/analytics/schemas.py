"""Schémas de sérialisation du blueprint `analytics` (RF-24 à RF-29)."""
from marshmallow import Schema, fields


class BranchAnalyticsSchema(Schema):
    branch_id = fields.String()
    branch_name = fields.String()
    sales_count = fields.Integer()
    revenue = fields.String()
    cost = fields.String()
    margin = fields.String()
    margin_rate_pct = fields.Float()


class ConsolidatedAnalyticsSchema(Schema):
    sales_count = fields.Integer()
    revenue = fields.String()
    cost = fields.String()
    margin = fields.String()
    margin_rate_pct = fields.Float()


class AdvancedDashboardSchema(Schema):
    period_days = fields.Integer()
    period_start = fields.String()
    branches = fields.Nested(BranchAnalyticsSchema, many=True)
    consolidated = fields.Nested(ConsolidatedAnalyticsSchema)


class MLModelSchema(Schema):
    id = fields.String()
    model_type = fields.String()
    version = fields.String()
    algorithm = fields.String()
    metrics = fields.Raw()
    mlflow_run_id = fields.String(allow_none=True)
    trained_at = fields.String(allow_none=True)
    is_active = fields.Boolean()
