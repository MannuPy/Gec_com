"""Schémas marshmallow pour le blueprint `users`."""
from marshmallow import Schema, fields, validate


class RoleSchema(Schema):
    id = fields.String()
    name = fields.String()
    description = fields.String(allow_none=True)
    permissions = fields.Method("get_permission_codes")

    def get_permission_codes(self, obj):
        return obj.permission_codes()


class UserSchema(Schema):
    id = fields.String()
    email = fields.String()
    full_name = fields.String()
    role_id = fields.String()
    role_name = fields.Method("get_role_name")
    branch_id = fields.String(allow_none=True)
    branch_name = fields.Method("get_branch_name")
    language = fields.String()
    is_active = fields.Boolean()
    created_at = fields.DateTime()

    def get_role_name(self, obj):
        return obj.role.name if obj.role else None

    def get_branch_name(self, obj):
        return obj.branch.name if obj.branch else None


class UserCreateSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=8))
    full_name = fields.String(required=True, validate=validate.Length(min=2, max=120))
    role_id = fields.String(required=True)
    branch_id = fields.String(allow_none=True, load_default=None)
    language = fields.String(load_default="fr", validate=validate.OneOf(["fr", "mos"]))


class UserUpdateSchema(Schema):
    full_name = fields.String(validate=validate.Length(min=2, max=120))
    role_id = fields.String()
    branch_id = fields.String(allow_none=True)
    language = fields.String(validate=validate.OneOf(["fr", "mos"]))
    is_active = fields.Boolean()
    password = fields.String(validate=validate.Length(min=8), load_only=True)


class AuditLogSchema(Schema):
    id = fields.String()
    user_id = fields.String(allow_none=True)
    user_name = fields.Method("get_user_name")
    event_type = fields.String()
    entity_type = fields.String(allow_none=True)
    entity_id = fields.String(allow_none=True)
    description = fields.String(allow_none=True)
    metadata_json = fields.Raw(allow_none=True)
    created_at = fields.DateTime()

    def get_user_name(self, obj):
        return obj.user.full_name if obj.user else None
