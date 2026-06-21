"""Schemas marshmallow pour le blueprint `auth`."""
from marshmallow import EXCLUDE, Schema, fields, validate


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=1))


class ChangePasswordSchema(Schema):
    """Changement de mot de passe (RF-05) - utilisateur authentifie."""

    current_password = fields.String(required=True, validate=validate.Length(min=1))
    new_password = fields.String(required=True, validate=validate.Length(min=8))


class RegisterSchema(Schema):
    """Inscription d'une nouvelle entreprise cliente (RF-01, section 27.4).

    `contact_email` est optionnel : a defaut, l'email de l'administrateur
    initial est utilise comme email de contact de l'entreprise.

    `unknown = EXCLUDE` : le champ optionnel `registration_secret` envoye par
    le client pour la verification cote route ne doit pas declencher une
    ValidationError marshmallow.
    """

    class Meta:
        unknown = EXCLUDE

    company_name = fields.String(required=True, validate=validate.Length(min=2, max=150))
    contact_email = fields.Email(required=False, allow_none=True)
    admin_full_name = fields.String(required=True, validate=validate.Length(min=2, max=120))
    admin_email = fields.Email(required=True)
    admin_password = fields.String(required=True, validate=validate.Length(min=8))


class TokenResponseSchema(Schema):
    access_token = fields.String()
    refresh_token = fields.String()
    user = fields.Raw()


class CurrentUserSchema(Schema):
    id = fields.String()
    email = fields.String()
    full_name = fields.String()
    role = fields.String()
    permissions = fields.List(fields.String())
    branch_id = fields.String(allow_none=True)
    branch_name = fields.String(allow_none=True)
