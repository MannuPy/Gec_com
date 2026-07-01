"""
Tests RBAC multi-roles — verification des 403 par role (Admin/Magasinier/Vendeur).

Permissions reelles par role (app/seed.py) :
  ADMIN      : ["*"]  => acces total
  MAGASINIER : products:read, stock:*, suppliers:*, transfers:*, analytics:read
               SANS users:read / sales:create
  VENDEUR    : products:read, stock:read, sales:*, customers:*, analytics:read
               SANS users:read / products:write / suppliers:*
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("TEST_DATABASE_URL",     "sqlite:///:memory:")
os.environ.setdefault("DATABASE_URL",          "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY",        "test-secret-key-not-for-production-32chars")
os.environ.setdefault("SECRET_KEY",            "test-secret-key")
os.environ.setdefault("FLASK_ENV",             "testing")
os.environ.setdefault("DEFAULT_TENANT_SCHEMA", "public")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def flask_app_rbac():
    from app import create_app
    from app.extensions import db as _db
    flask_app = create_app("testing")
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    flask_app.config["TESTING"] = True
    with flask_app.app_context():
        _db.create_all()
        yield flask_app
        _db.session.remove()
        _db.drop_all()


def _make_token(flask_app, permissions):
    from flask_jwt_extended import create_access_token
    with flask_app.app_context():
        return create_access_token(
            identity="test-user-rbac",
            additional_claims={"permissions": permissions, "role": "TEST"},
        )


@pytest.fixture(scope="module")
def admin_token(flask_app_rbac):
    return _make_token(flask_app_rbac, ["*"])


@pytest.fixture(scope="module")
def magasinier_token(flask_app_rbac):
    return _make_token(flask_app_rbac, [
        "products:read", "stock:read", "stock:write",
        "suppliers:read", "suppliers:write",
        "receptions:read", "receptions:write",
        "transfers:read", "transfers:write",
        "customers:read", "reports:read",
        "analytics:read", "inventory:read", "inventory:write",
    ])


@pytest.fixture(scope="module")
def vendeur_token(flask_app_rbac):
    return _make_token(flask_app_rbac, [
        "products:read", "stock:read",
        "sales:read", "sales:create",
        "customers:read", "customers:write",
        "transfers:read", "transfers:write",
        "reports:read", "analytics:read",
    ])


@pytest.fixture(scope="module")
def client_rbac(flask_app_rbac):
    return flask_app_rbac.test_client()


def auth(token):
    return {"Authorization": "Bearer " + token}


# ---------------------------------------------------------------------------
# 1. Admin acces total
# ---------------------------------------------------------------------------

class TestAdminAccesTotal:

    def test_admin_peut_lire_utilisateurs(self, client_rbac, admin_token):
        resp = client_rbac.get("/api/v1/users", headers=auth(admin_token))
        assert resp.status_code != 403, "Admin ne devrait jamais avoir 403"
        assert resp.status_code != 401

    def test_admin_peut_lire_analytics(self, client_rbac, admin_token):
        resp = client_rbac.get("/api/v1/analytics/rfm-segments", headers=auth(admin_token))
        assert resp.status_code != 403

    def test_admin_peut_lire_stock(self, client_rbac, admin_token):
        resp = client_rbac.get("/api/v1/stock", headers=auth(admin_token))
        assert resp.status_code != 403


# ---------------------------------------------------------------------------
# 2. Magasinier : interdit sur users:read
# ---------------------------------------------------------------------------

class TestMagasinierPermissions:

    def test_magasinier_interdit_liste_utilisateurs(self, client_rbac, magasinier_token):
        """GET /users/ exige users:read — Magasinier n'a pas -> 403."""
        resp = client_rbac.get("/api/v1/users", headers=auth(magasinier_token))
        assert resp.status_code == 403, (
            "Magasinier sur GET /users/ attendu 403 obtenu " + str(resp.status_code)
        )

    def test_magasinier_peut_lire_stock(self, client_rbac, magasinier_token):
        """Magasinier a stock:read -> pas de 403."""
        resp = client_rbac.get("/api/v1/stock", headers=auth(magasinier_token))
        assert resp.status_code not in (401, 403)

    def test_magasinier_peut_lire_analytics(self, client_rbac, magasinier_token):
        """Magasinier a analytics:read -> acces rfm-segments."""
        resp = client_rbac.get("/api/v1/analytics/rfm-segments", headers=auth(magasinier_token))
        assert resp.status_code not in (401, 403)


# ---------------------------------------------------------------------------
# 3. Vendeur : interdit sur users:read et products:write
# ---------------------------------------------------------------------------

class TestVendeurPermissions:

    def test_vendeur_interdit_liste_utilisateurs(self, client_rbac, vendeur_token):
        """GET /users/ exige users:read — Vendeur n'a pas -> 403."""
        resp = client_rbac.get("/api/v1/users", headers=auth(vendeur_token))
        assert resp.status_code == 403, (
            "Vendeur sur GET /users/ attendu 403 obtenu " + str(resp.status_code)
        )

    def test_vendeur_interdit_creation_produit(self, client_rbac, vendeur_token):
        """POST /products exige products:write — Vendeur n'a pas -> 403."""
        resp = client_rbac.post(
            "/api/v1/products",
            json={"name": "test", "sku": "TST-001", "price": 1000},
            headers=auth(vendeur_token),
        )
        assert resp.status_code == 403, (
            "Vendeur sur POST /api/v1/products attendu 403 obtenu " + str(resp.status_code)
        )

    def test_vendeur_peut_lire_analytics(self, client_rbac, vendeur_token):
        """Vendeur a analytics:read -> acces endpoints analytiques."""
        resp = client_rbac.get("/api/v1/analytics/rfm-segments", headers=auth(vendeur_token))
        assert resp.status_code not in (401, 403)

    def test_vendeur_peut_creer_vente(self, client_rbac, vendeur_token):
        """Vendeur a sales:create -> POST /sales ne doit pas retourner 403."""
        resp = client_rbac.post(
            "/api/v1/sales",
            json={"lines": [], "boutique_id": 1},
            headers=auth(vendeur_token),
        )
        assert resp.status_code != 403, (
            "Vendeur sur POST /sales attendu pas de 403 obtenu " + str(resp.status_code)
        )
        assert resp.status_code != 401


# ---------------------------------------------------------------------------
# 4. Format de la reponse 403
# ---------------------------------------------------------------------------

class TestFormat403:

    def test_403_est_json(self, client_rbac, vendeur_token):
        """Un 403 retourne du JSON."""
        resp = client_rbac.get("/api/v1/users", headers=auth(vendeur_token))
        assert resp.status_code == 403
        data = resp.get_json()
        assert data is not None, "La reponse 403 devrait etre du JSON"

    def test_403_contient_champ_erreur(self, client_rbac, vendeur_token):
        """Le JSON 403 contient 'error' ou 'message'."""
        resp = client_rbac.get("/api/v1/users", headers=auth(vendeur_token))
        data = resp.get_json()
        if data:
            has_field = ("error" in data) or ("message" in data)
            assert has_field, "Reponse 403 sans champ error/message : " + str(data)
