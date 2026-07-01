"""
Tests d'intégration API — GesCom-BF.

Vérifie que les endpoints Flask répondent correctement de bout en bout :
  requête HTTP → middleware → blueprint → réponse JSON.

Infrastructure : Flask test_client + SQLite in-memory.
Aucun PostgreSQL requis — l'app est créée en mode "testing" avec SQLite.
"""
import json
import os
import sys

import pytest

# PYTHONPATH : ajouter backend/ pour permettre "from app import ..."
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("DATABASE_URL",    "sqlite:///:memory:")
os.environ.setdefault("TEST_DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY",  "test-secret-key-not-for-production-32chars")
os.environ.setdefault("SECRET_KEY",      "test-secret-key")
os.environ.setdefault("FLASK_ENV",       "testing")
os.environ.setdefault("DEFAULT_TENANT_SCHEMA", "public")


# ---------------------------------------------------------------------------
# Fixture module-level : une seule instance Flask par session de test
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def flask_client():
    """
    Crée l'application Flask en mode testing avec SQLite in-memory.
    La fixture est scoped au module pour éviter de recréer l'app à chaque test.
    """
    from app import create_app
    from app.extensions import db as _db

    flask_app = create_app("testing")
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    flask_app.config["TESTING"] = True

    with flask_app.app_context():
        _db.create_all()
        with flask_app.test_client() as c:
            yield c
        _db.session.remove()
        _db.drop_all()


# ---------------------------------------------------------------------------
# 1. Endpoint /health (public, sans authentification)
# ---------------------------------------------------------------------------

class TestHealthEndpoint:

    def test_health_retourne_200_ou_503(self, flask_client):
        """
        /health doit toujours répondre (200 OK ou 503 Degraded).
        Un 200 indique que la DB SQLite est accessible.
        Un 503 indiquerait un problème de connexion DB — acceptable en test.
        """
        resp = flask_client.get("/health")
        assert resp.status_code in (200, 503), (
            f"Status inattendu : {resp.status_code}"
        )

    def test_health_retourne_json(self, flask_client):
        """/health retourne du JSON valide."""
        resp = flask_client.get("/health")
        data = resp.get_json()
        assert data is not None, "La réponse n'est pas du JSON valide"

    def test_health_contient_champs_requis(self, flask_client):
        """/health contient les champs status, version, db, uptime_s."""
        resp = flask_client.get("/health")
        data = resp.get_json()
        for champ in ["status", "version", "db", "uptime_s"]:
            assert champ in data, f"Champ manquant dans /health : {champ}"

    def test_health_status_valeur_attendue(self, flask_client):
        """Le champ status vaut 'ok' ou 'degraded'."""
        resp = flask_client.get("/health")
        data = resp.get_json()
        assert data["status"] in ("ok", "degraded")

    def test_health_sans_token(self, flask_client):
        """/health est accessible sans token JWT (endpoint public)."""
        resp = flask_client.get("/health", headers={})
        assert resp.status_code != 401


# ---------------------------------------------------------------------------
# 2. Endpoint /api/v1/auth/login — validation d'entrée
# ---------------------------------------------------------------------------

class TestAuthLoginValidation:

    def test_login_sans_body_retourne_erreur(self, flask_client):
        """POST /auth/login sans body → erreur de validation (400 ou 422)."""
        resp = flask_client.post(
            "/api/v1/auth/login",
            content_type="application/json",
            data=json.dumps({}),
        )
        assert resp.status_code in (400, 422), (
            f"Status inattendu sur body vide : {resp.status_code}"
        )

    def test_login_email_manquant_retourne_erreur(self, flask_client):
        """POST /auth/login sans email → erreur de validation."""
        resp = flask_client.post(
            "/api/v1/auth/login",
            content_type="application/json",
            data=json.dumps({"password": "motdepasse123"}),
        )
        assert resp.status_code in (400, 422)

    def test_login_password_manquant_retourne_erreur(self, flask_client):
        """POST /auth/login sans password → erreur de validation."""
        resp = flask_client.post(
            "/api/v1/auth/login",
            content_type="application/json",
            data=json.dumps({"email": "user@test.com"}),
        )
        assert resp.status_code in (400, 422)

    def test_login_credentials_invalides(self, flask_client):
        """POST /auth/login avec credentials inexistants → erreur (pas 500)."""
        resp = flask_client.post(
            "/api/v1/auth/login",
            content_type="application/json",
            data=json.dumps({
                "email": "inexistant@gescom-bf.com",
                "password": "mauvais_motdepasse",
            }),
        )
        assert resp.status_code in (400, 401, 404, 422), (
            f"Status inattendu : {resp.status_code} (ne doit pas être 500)"
        )

    def test_login_retourne_json(self, flask_client):
        """POST /auth/login retourne toujours du JSON (même en cas d'erreur)."""
        resp = flask_client.post(
            "/api/v1/auth/login",
            content_type="application/json",
            data=json.dumps({"email": "a@b.com", "password": "x"}),
        )
        assert resp.is_json or "json" in (resp.content_type or "")


# ---------------------------------------------------------------------------
# 3. Endpoints protégés — rejet sans token JWT
# ---------------------------------------------------------------------------

PROTECTED_ENDPOINTS = [
    ("GET",  "/api/v1/users"),
    ("GET",  "/api/v1/products/categories"),
    ("GET",  "/api/v1/stock"),
    ("GET",  "/api/v1/sales"),
    ("GET",  "/api/v1/analytics/forecast"),
    ("GET",  "/api/v1/analytics/rfm-segments"),
    ("GET",  "/api/v1/analytics/anomalies"),
]


class TestEndpointsProtectedNoAuth:

    @pytest.mark.parametrize("method,endpoint", PROTECTED_ENDPOINTS)
    def test_endpoint_sans_token_retourne_401(self, flask_client, method, endpoint):
        """
        Tout endpoint protégé doit retourner 401 en l'absence de token JWT.
        Garantit que @require_permission est bien appliqué sur chaque route.
        """
        resp = flask_client.get(endpoint)
        assert resp.status_code == 401, (
            f"{method} {endpoint} → attendu 401, obtenu {resp.status_code}"
        )

    def test_token_malformed_retourne_401(self, flask_client):
        """Un token JWT malformé doit être rejeté avec 401."""
        resp = flask_client.get(
            "/api/v1/users",
            headers={"Authorization": "Bearer token_completement_invalide"},
        )
        assert resp.status_code == 401
