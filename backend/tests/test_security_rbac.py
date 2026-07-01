"""
Tests de securite — RBAC et protection des endpoints (GesCom-BF).

Verifie que :
  1. Tous les endpoints sensibles exigent un token JWT valide (401 sans token).
  2. Les tokens malformes sont rejetes avec 401 et une reponse JSON.
  3. Le rate limiting est configure sans erreur serveur (pas de 500).
  4. L'endpoint /health est public.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("DATABASE_URL",        "sqlite:///:memory:")
os.environ.setdefault("TEST_DATABASE_URL",   "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY",      "test-secret-key-not-for-production-32chars")
os.environ.setdefault("SECRET_KEY",          "test-secret-key")
os.environ.setdefault("FLASK_ENV",           "testing")
os.environ.setdefault("DEFAULT_TENANT_SCHEMA", "public")


@pytest.fixture(scope="module")
def flask_client():
    """Flask test_client avec SQLite in-memory (module-scoped)."""
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
# Matrice des endpoints proteges
# ---------------------------------------------------------------------------

ENDPOINTS_AUTH_REQUIS = [
    ("GET", "/api/v1/users",                      "Liste utilisateurs"),
    ("GET", "/api/v1/products/categories",         "Categories produits"),
    ("GET", "/api/v1/stock",                       "Stock global"),
    ("GET", "/api/v1/transfers",                   "Transferts"),
    ("GET", "/api/v1/sales",                       "Ventes"),
    ("GET", "/api/v1/analytics/forecast",           "Prevision demande"),
    ("GET", "/api/v1/analytics/rfm-segments",      "Segmentation RFM"),
    ("GET", "/api/v1/analytics/anomalies",         "Anomalies"),
    ("GET", "/api/v1/analytics/credit-scores",     "Scoring credit"),
]


# ---------------------------------------------------------------------------
# 1. Endpoint public /health
# ---------------------------------------------------------------------------

class TestEndpointPublic:

    def test_health_sans_token_pas_401(self, flask_client):
        """/health est public — ne doit pas retourner 401."""
        resp = flask_client.get("/health")
        assert resp.status_code != 401, (
            "/health ne devrait pas exiger d'authentification"
        )


# ---------------------------------------------------------------------------
# 2. Rejet sans token JWT
# ---------------------------------------------------------------------------

class TestRejetSansToken:

    @pytest.mark.parametrize("method,endpoint,desc", ENDPOINTS_AUTH_REQUIS)
    def test_sans_token_retourne_401(self, flask_client, method, endpoint, desc):
        """Tout endpoint protege retourne 401 sans token JWT."""
        resp = flask_client.get(endpoint)
        assert resp.status_code == 401, (
            f"[{desc}] {method} {endpoint} -> attendu 401, obtenu {resp.status_code}"
        )


# ---------------------------------------------------------------------------
# 3. Tokens invalides — rejet 401 en JSON
# ---------------------------------------------------------------------------

INVALID_TOKENS = [
    ("token_completement_invalide",             "Token aleatoire"),
    ("eyJhbGciOiJIUzI1NiJ9.invalide.invalide", "JWT malformed"),
]


class TestTokensInvalides:

    @pytest.mark.parametrize("token,desc", INVALID_TOKENS)
    def test_token_invalide_retourne_401(self, flask_client, token, desc):
        """Un token invalide est rejete avec 401 — jamais 500."""
        resp = flask_client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401, (
            f"[{desc}] attendu 401, obtenu {resp.status_code}"
        )

    def test_reponse_401_est_json(self, flask_client):
        """La reponse 401 est du JSON, pas une page HTML d'erreur Flask."""
        resp = flask_client.get(
            "/api/v1/users",
            headers={"Authorization": "Bearer token_invalide"},
        )
        assert resp.status_code == 401
        data = resp.get_json()
        assert data is not None, (
            "La reponse 401 n'est pas du JSON — verifier register_jwt_callbacks()"
        )

    def test_reponse_401_contient_champ_erreur(self, flask_client):
        """La reponse 401 contient 'error' ou 'message' pour le frontend."""
        resp = flask_client.get(
            "/api/v1/users",
            headers={"Authorization": "Bearer token_invalide"},
        )
        data = resp.get_json()
        if data:
            assert "error" in data or "message" in data, (
                f"Reponse 401 sans champ error/message : {data}"
            )


# ---------------------------------------------------------------------------
# 4. Rate limiting — pas d'erreur serveur (500)
# ---------------------------------------------------------------------------

class TestRateLimiting:

    def test_appels_repetitifs_login_pas_500(self, flask_client):
        """
        5 appels rapides sur /auth/login ne doivent pas provoquer de 500.
        Le rate limiter (memory://) peut retourner 429 apres le seuil,
        mais jamais une erreur serveur.
        """
        payload = json.dumps({"email": "test@rate.com", "password": "wrong"})
        statuts_attendus = {400, 401, 404, 422, 429}

        for i in range(5):
            resp = flask_client.post(
                "/api/v1/auth/login",
                content_type="application/json",
                data=payload,
            )
            assert resp.status_code != 500, (
                f"Erreur serveur 500 a l'appel #{i+1} sur /auth/login"
            )
            assert resp.status_code in statuts_attendus, (
                f"Status inattendu {resp.status_code} a l'appel #{i+1}"
            )
