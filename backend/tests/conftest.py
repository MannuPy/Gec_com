"""
Configuration pytest — GesCom-BF backend.

Deux suites de tests coexistent :

1. Tests unitaires ML (fonctions pures, sans DB ni Flask context)
   → test_demand_forecast, test_credit_scoring_logic, test_anomaly_detection,
     test_rfm_segmentation, test_market_basket, test_price_elasticity
   → Tournent sans aucune fixture Flask.

2. Tests d'intégration + sécurité (Flask test_client + SQLite in-memory)
   → test_integration_api.py, test_security_rbac.py
   → Utilisent les fixtures `app` et `client` définies ici.
"""
import os
import sys

import pytest

# Ajouter le répertoire backend au PYTHONPATH pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Variables d'environnement minimales — DOIT être fait avant tout import de app.config
# TEST_DATABASE_URL est lu au niveau classe dans TestingConfig (attribut évalué à l'import).
# Il faut donc le définir ici, avant que pytest importe les fichiers de test.
os.environ.setdefault("TEST_DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production-32chars")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("FLASK_ENV", "testing")
os.environ.setdefault("DEFAULT_TENANT_SCHEMA", "public")


# ---------------------------------------------------------------------------
# Fixtures Flask pour les tests d'intégration et de sécurité
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def app():
    """
    Application Flask configurée pour les tests d'intégration.

    Utilise SQLite in-memory pour éviter toute dépendance à PostgreSQL ou MySQL.
    Le middleware tenant fonctionne en mode no-op sur SQLite (set_search_path
    n'exécute pas SET search_path sur un dialecte non-PostgreSQL).
    """
    os.environ["TEST_DATABASE_URL"] = "sqlite:///:memory:"

    from app import create_app
    from app.extensions import db as _db

    flask_app = create_app("testing")
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False

    with flask_app.app_context():
        _db.create_all()
        yield flask_app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope="session")
def client(app):
    """Client de test Flask (session-scoped)."""
    return app.test_client()


@pytest.fixture()
def db_session(app):
    """Accès db avec rollback automatique après chaque test."""
    from app.extensions import db as _db
    yield _db
    _db.session.rollback()
