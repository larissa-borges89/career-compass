"""
Global pytest configuration.
Uses StaticPool to ensure all connections share the same in-memory database.
Production database is never touched during test runs.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.database import Base, get_db
from api_server import app

# StaticPool ensures all connections share the same in-memory instance
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Apply override globally for all tests
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create all tables once before the test session starts."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def disable_auth_by_default(monkeypatch):
    """Unset API_KEY for all tests by default, so integration tests don't
    need to send the X-API-Key header on every request. Tests in
    test_auth.py that specifically exercise the auth middleware override
    this via their own monkeypatch.setenv() calls."""
    monkeypatch.delenv("API_KEY", raising=False)
