"""Tests for API key authentication."""
import pytest
import os
from fastapi.testclient import TestClient


@pytest.fixture
def authenticated_client(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-secret-key")
    from importlib import reload
    import api_server
    reload(api_server)
    return TestClient(api_server.app), "test-secret-key"


def test_health_always_public():
    """Health endpoint must always be accessible — no auth required."""
    from api_server import app
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200


def test_no_api_key_set_allows_all(monkeypatch):
    """When API_KEY is not set, all requests pass (local dev mode)."""
    monkeypatch.delenv("API_KEY", raising=False)
    from api_server import app
    client = TestClient(app)
    response = client.get("/api/applications")
    assert response.status_code == 200


def test_valid_api_key_allows_request(authenticated_client):
    client, key = authenticated_client
    response = client.get("/api/applications", headers={"X-API-Key": key})
    assert response.status_code == 200


def test_invalid_api_key_returns_401(authenticated_client):
    client, _ = authenticated_client
    response = client.get("/api/applications", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 401
    assert "Invalid" in response.json()["detail"]


def test_missing_api_key_returns_401(authenticated_client):
    client, _ = authenticated_client
    response = client.get("/api/applications")
    assert response.status_code == 401
