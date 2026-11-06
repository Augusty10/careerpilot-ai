import os
import sys
from pathlib import Path
import pytest
import mongomock

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app import create_app
from backend.config import Config
from backend.database import get_db, close_db


class TestConfig(Config):
    TESTING = True
    RATELIMIT_ENABLED = False
    JWT_SECRET = "super-test-jwt-secret-key-for-careerpilot"
    JWT_EXPIRY_MINUTES = 60
    FRONTEND_URL = "http://localhost:5173"


@pytest.fixture(autouse=True)
def clean_db():
    """Provides a fresh isolated in-memory mongomock database for each test."""
    mock_client = mongomock.MongoClient()
    db = get_db(client_override=mock_client, db_name_override="careerpilot_test_db")
    db.users.drop()
    yield db
    mock_client.close()
    close_db()


@pytest.fixture
def app(clean_db):
    """Creates a test Flask application configured with the mock database."""
    test_app = create_app(
        config_class=TestConfig,
        client_override=clean_db.client,
        db_name_override="careerpilot_test_db"
    )
    test_app.config["TESTING"] = True
    test_app.config["RATELIMIT_ENABLED"] = False
    return test_app


@pytest.fixture
def client(app):
    """Flask test client fixture."""
    return app.test_client()

