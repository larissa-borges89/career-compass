"""Tests for API key authentication."""
import os
import pytest
from fastapi.testclient import TestClient
from api_server import app

client = TestClient(app)


def test_health_always_public():
    """Health endpoint must always be accessible — no auth required."""
    response = client.get("/health")
    assert response.status_code == 200


def test_no_api_key_set_allows_all(monkeypatch):
    """When API_KEY is not set, all requests pass (local dev mode)."""
    monkeypatch.delenv("API_KEY", raising=False)
    response = client.get("/api/applications")
    assert response.status_code == 200


def test_valid_api_key_allows_request(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-secret-key")
    response = client.get("/api/applications", headers={"X-API-Key": "test-secret-key"})
    assert response.status_code == 200


def test_invalid_api_key_returns_401(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-secret-key")
    response = client.get("/api/applications", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 401
    assert "Invalid" in response.json()["detail"]


def test_missing_api_key_returns_401(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-secret-key")
    response = client.get("/api/applications")
    assert response.status_code == 401
