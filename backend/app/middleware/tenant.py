"""
Middleware multi-tenant : resolution du schema PostgreSQL courant.
"""
from flask import Flask, current_app, request
from flask_jwt_extended import get_jwt, verify_jwt_in_request

from app.utils.tenant import set_search_path

PUBLIC_ENDPOINTS = {
    "health",
    "auth.login",
    "auth.register",
}


def register_tenant_middleware(app: Flask) -> None:
    """Enregistre les hooks before_request / teardown_request."""

    @app.before_request
    def set_tenant_schema():
        if request.endpoint is None or request.endpoint in PUBLIC_ENDPOINTS:
            return

        verify_jwt_in_request(optional=True)

        claims = get_jwt()
        schema = (claims or {}).get("company_schema") or current_app.config[
            "DEFAULT_TENANT_SCHEMA"
        ]
        set_search_path(schema)

    @app.teardown_request
    def reset_tenant_schema(_exception):
        try:
            set_search_path("public")
        except Exception:
            pass
