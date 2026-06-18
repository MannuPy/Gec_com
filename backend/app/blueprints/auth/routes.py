"""Routes du blueprint `auth` : login, refresh, logout, profil courant.

Cf. 17-API-REST.md (POST /auth/login, POST /auth/refresh, POST /auth/logout,
GET /auth/me) et 18-SECURITE.md (RG-36 : access token courte duree + refresh
token, blocklist en base pour la revocation).
"""
from datetime import datetime, timezone

from flask import current_app, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)

from app.blueprints.auth import auth_bp
from app.blueprints.auth.schemas import ChangePasswordSchema, LoginSchema, RegisterSchema
from app.extensions import db
from app.models import AuditLog, TokenBlocklist, User
from app.services.tenant_provisioning import provision_tenant
from app.utils.errors import ApiError
from app.utils.tenant import get_schema_for_email, set_search_path


def _build_additional_claims(user: User, company_schema: str) -> dict:
    """Construit les claims JWT additionnels (role, permissions, site, tenant).

    Le claim `company_schema` (RF-01, section 27.7) permet au middleware
    `set_tenant_schema` de positionner le `search_path` PostgreSQL sur le
    schema de l'entreprise cliente lors des requetes suivantes.
    """
    return {
        "role": user.role.name,
        "permissions": user.role.permission_codes(),
        "branch_id": user.branch_id,
        "company_schema": company_schema,
    }


def _serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.name,
        "permissions": user.role.permission_codes(),
        "branch_id": user.branch_id,
        "branch_name": user.branch.name if user.branch else None,
        "language": user.language,
        "must_change_password": user.must_change_password,
    }


@auth_bp.post("/login")
def login():
    """Authentifie un utilisateur et renvoie une paire access/refresh token."""
    payload = LoginSchema().load(request.get_json(silent=True) or {})
    email = payload["email"].lower()

    # Resolution du tenant (section 27.7) : `public.user_index` indique le schema
    # PostgreSQL dans lequel chercher cet utilisateur. A defaut d'entree
    # (compte cree avant le multi-tenant), on retombe sur le tenant par
    # defaut (V1 mono-tenant, schema `public`).
    company_schema = get_schema_for_email(email)
    set_search_path(company_schema)

    user = User.query.filter_by(email=email).first()

    if user is None or not user.check_password(payload["password"]):
        AuditLog.record(
            event_type="AUTH_LOGIN_FAILED",
            description=f"Tentative de connexion echouee pour {email}",
            metadata={"email": email},
        )
        db.session.commit()
        raise ApiError("INVALID_CREDENTIALS", "Email ou mot de passe incorrect.", status_code=401)

    if not user.is_active:
        raise ApiError("ACCOUNT_DISABLED", "Ce compte a ete desactive.", status_code=403)

    claims = _build_additional_claims(user, company_schema)
    access_token = create_access_token(identity=user.id, additional_claims=claims)
    refresh_token = create_refresh_token(identity=user.id, additional_claims=claims)

    AuditLog.record(
        event_type="AUTH_LOGIN_SUCCESS",
        user_id=user.id,
        entity_type="User",
        entity_id=user.id,
        description=f"Connexion reussie de {user.email}",
    )
    db.session.commit()

    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": _serialize_user(user),
    })


@auth_bp.post("/register")
def register():
    """Inscription d'une nouvelle entreprise cliente (RF-01).

    Provisionne un schema PostgreSQL dedie (section 27.4) avec son RBAC par defaut,
    un site "Depot Central" et un compte ADMIN initial, puis connecte
    automatiquement cet administrateur (reponse identique a `/auth/login`).
    """
    payload = RegisterSchema().load(request.get_json(silent=True) or {})

    admin_email = payload["admin_email"].lower()
    contact_email = payload.get("contact_email") or admin_email

    company, admin_user = provision_tenant(
        company_name=payload["company_name"],
        contact_email=contact_email,
        admin_full_name=payload["admin_full_name"],
        admin_email=admin_email,
        admin_password=payload["admin_password"],
    )

    claims = _build_additional_claims(admin_user, company.schema_name)
    access_token = create_access_token(identity=admin_user.id, additional_claims=claims)
    refresh_token = create_refresh_token(identity=admin_user.id, additional_claims=claims)

    AuditLog.record(
        event_type="COMPANY_REGISTERED",
        user_id=admin_user.id,
        entity_type="Company",
        entity_id=company.id,
        description=f"Inscription de l'entreprise \"{company.name}\" (schema {company.schema_name})",
    )
    db.session.commit()

    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": _serialize_user(admin_user),
        "company": {
            "id": company.id,
            "name": company.name,
            "schema_name": company.schema_name,
            "subscription_plan": company.subscription_plan,
            "subscription_status": company.subscription_status,
        },
    }), 201


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    """Emet un nouveau access token a partir d'un refresh token valide."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if user is None or not user.is_active:
        raise ApiError("ACCOUNT_DISABLED", "Ce compte a ete desactive.", status_code=403)

    # Le middleware `set_tenant_schema` a deja positionne `search_path`
    # d'apres le claim `company_schema` du refresh token ci-dessus.
    company_schema = get_jwt().get("company_schema", current_app.config["DEFAULT_TENANT_SCHEMA"])
    claims = _build_additional_claims(user, company_schema)
    access_token = create_access_token(identity=user.id, additional_claims=claims)
    return jsonify({"access_token": access_token})


@auth_bp.post("/logout")
@jwt_required(verify_type=False)
def logout():
    """Revoque le jeton courant (access ou refresh) via la blocklist (RG-36)."""
    jwt_payload = get_jwt()
    jti = jwt_payload["jti"]

    db.session.add(TokenBlocklist(jti=jti, created_at=datetime.now(timezone.utc)))

    AuditLog.record(
        event_type="AUTH_LOGOUT",
        user_id=get_jwt_identity(),
        description="Deconnexion / revocation de jeton",
    )
    db.session.commit()

    return jsonify({"message": "Deconnexion reussie."})


@auth_bp.get("/me")
@jwt_required()
def me():
    """Retourne le profil de l'utilisateur authentifie."""
    user = User.query.get(get_jwt_identity())
    if user is None:
        raise ApiError("NOT_FOUND", "Utilisateur introuvable.", status_code=404)
    return jsonify(_serialize_user(user))


@auth_bp.post("/change-password")
@jwt_required()
def change_password():
    """Change le mot de passe de l'utilisateur authentifie (RF-05).

    Leve `must_change_password` a `False` : utilise aussi bien pour le
    changement volontaire que pour le changement force a la 1re connexion
    (compte cree par un administrateur, cf. blueprints/users/routes.py).
    """
    user = User.query.get(get_jwt_identity())
    if user is None:
        raise ApiError("NOT_FOUND", "Utilisateur introuvable.", status_code=404)

    payload = ChangePasswordSchema().load(request.get_json(silent=True) or {})

    if not user.check_password(payload["current_password"]):
        raise ApiError("INVALID_CREDENTIALS", "Mot de passe actuel incorrect.", status_code=401)

    user.set_password(payload["new_password"])
    user.must_change_password = False

    AuditLog.record(
        event_type="PASSWORD_CHANGED",
        user_id=user.id,
        entity_type="User",
        entity_id=user.id,
        description="Mot de passe modifie.",
    )
    db.session.commit()
    return jsonify({"message": "Mot de passe modifie avec succes."}), 200
