"""
Decorateurs transverses : controle d'acces base sur les roles (RBAC).
"""
from functools import wraps

from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt

from app.utils.errors import forbidden


def require_permission(*required_permissions: str):
    """Exige que l'utilisateur authentifie possede AU MOINS UNE des permissions listees.

    RF-05 : si le claim `must_change_password` est True, toutes les routes
    protegees retournent 403 PASSWORD_CHANGE_REQUIRED pour forcer le
    changement avant toute action metier.  Seul `/api/v1/auth/change-password`
    est exempt (il ne passe pas par ce decorateur).
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()

            # RF-05 : blocage si premier changement de mot de passe non effectue.
            if claims.get("must_change_password"):
                return jsonify({
                    "error": "PASSWORD_CHANGE_REQUIRED",
                    "message": (
                        "Vous devez changer votre mot de passe avant d'utiliser l'application. "
                        "Appelez POST /api/v1/auth/change-password."
                    ),
                }), 403

            user_permissions = set(claims.get("permissions", []))

            if "*" in user_permissions:  # Super-Admin
                return fn(*args, **kwargs)

            if not user_permissions.intersection(required_permissions):
                raise forbidden(
                    "Cette action necessite l'une des permissions suivantes : "
                    + ", ".join(required_permissions) + "."
                )
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def require_role(*roles: str):
    """Exige que l'utilisateur authentifie possede l'un des roles listes."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") not in roles:
                raise forbidden(
                    "Cette action est reservee aux roles : " + ", ".join(roles) + "."
                )
            return fn(*args, **kwargs)
        return wrapper
    return decorator
