"""Routes du blueprint `users` : gestion des comptes et consultation des roles.

Cf. 17-API-REST.md section Utilisateurs et 18-SECURITE.md (matrice des permissions :
`users:read`, `users:write`, reservees au role ADMIN).
"""
from flask import current_app, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from app.blueprints.users import users_bp
from app.blueprints.users.schemas import (
    AuditLogSchema,
    RoleSchema,
    UserCreateSchema,
    UserSchema,
    UserUpdateSchema,
)
from app.extensions import db
from app.models import AuditLog, Role, User
from app.utils.decorators import require_permission
from app.utils.errors import conflict, not_found, validation_error
from app.utils.tenant import register_user_index

user_schema = UserSchema()
users_schema = UserSchema(many=True)
role_schema = RoleSchema(many=True)
audit_log_schema = AuditLogSchema(many=True)


@users_bp.get("/roles")
@require_permission("users:read")
def list_roles():
    """Liste les roles disponibles (pour les formulaires de creation d'utilisateur)."""
    roles = Role.query.order_by(Role.name).all()
    return jsonify(role_schema.dump(roles))


@users_bp.get("")
@require_permission("users:read")
def list_users():
    """Liste les utilisateurs, avec filtres optionnels `branch_id` et `role_id`."""
    query = User.query

    branch_id = request.args.get("branch_id")
    if branch_id:
        query = query.filter(User.branch_id == branch_id)

    role_id = request.args.get("role_id")
    if role_id:
        query = query.filter(User.role_id == role_id)

    users = query.order_by(User.full_name).all()
    return jsonify(users_schema.dump(users))


@users_bp.post("")
@require_permission("users:write")
def create_user():
    """Cree un nouvel utilisateur (RF-01)."""
    payload = UserCreateSchema().load(request.get_json(silent=True) or {})

    email = payload["email"].lower()
    if User.query.filter_by(email=email).first() is not None:
        raise conflict("EMAIL_ALREADY_USED", "Un utilisateur existe deja avec cet email.")

    role = Role.query.get(payload["role_id"])
    if role is None:
        raise not_found("Role", payload["role_id"])

    user = User(
        email=email,
        full_name=payload["full_name"],
        role_id=role.id,
        branch_id=payload.get("branch_id"),
        language=payload.get("language", "fr"),
        # RF-05 : mot de passe attribue par un administrateur -> changement
        # obligatoire a la 1re connexion.
        must_change_password=True,
    )
    user.set_password(payload["password"])
    db.session.add(user)

    # Index global email -> schema (section 27.7) : le nouvel utilisateur appartient
    # au tenant courant (schema resolu par le middleware `set_tenant_schema`
    # a partir du claim JWT `company_schema` de l'appelant).
    company_schema = get_jwt().get("company_schema", current_app.config["DEFAULT_TENANT_SCHEMA"])
    register_user_index(email, company_schema)

    AuditLog.record(
        event_type="USER_CREATED",
        user_id=get_jwt_identity(),
        entity_type="User",
        description=f"Creation de l'utilisateur {user.email}",
    )
    db.session.commit()

    return jsonify(user_schema.dump(user)), 201


@users_bp.get("/<string:user_id>")
@require_permission("users:read")
def get_user(user_id: str):
    user = User.query.get(user_id)
    if user is None:
        raise not_found("Utilisateur", user_id)
    return jsonify(user_schema.dump(user))


@users_bp.put("/<string:user_id>")
@require_permission("users:write")
def update_user(user_id: str):
    """Met a jour un utilisateur (role, site, statut, mot de passe...)."""
    user = User.query.get(user_id)
    if user is None:
        raise not_found("Utilisateur", user_id)

    payload = UserUpdateSchema().load(request.get_json(silent=True) or {})

    if "role_id" in payload:
        role = Role.query.get(payload["role_id"])
        if role is None:
            raise validation_error("Role inconnu.", details={"role_id": payload["role_id"]})
        user.role_id = role.id

    for field in ("full_name", "branch_id", "language", "is_active"):
        if field in payload:
            setattr(user, field, payload[field])

    if "password" in payload:
        user.set_password(payload["password"])
        # RF-05 : un mot de passe reinitialise par un administrateur doit
        # etre change par l'utilisateur a sa prochaine connexion.
        user.must_change_password = True

    AuditLog.record(
        event_type="USER_UPDATED",
        user_id=get_jwt_identity(),
        entity_type="User",
        entity_id=user.id,
        description=f"Mise a jour de l'utilisateur {user.email}",
    )
    db.session.commit()

    return jsonify(user_schema.dump(user))


@users_bp.get("/audit-logs")
@require_permission("users:read")
def list_audit_logs():
    """Journal d'audit applicatif (RF-26), pagine et filtrable par type d'evenement."""
    query = AuditLog.query

    event_type = request.args.get("event_type")
    if event_type:
        query = query.filter(AuditLog.event_type == event_type)

    user_id = request.args.get("user_id")
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)

    page = request.args.get("page", default=1, type=int)
    per_page = min(request.args.get("per_page", default=50, type=int), 200)

    pagination = query.order_by(AuditLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        "data": audit_log_schema.dump(pagination.items),
        "meta": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
        },
    })
