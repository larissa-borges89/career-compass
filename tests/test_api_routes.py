"""Integration tests for FastAPI routes."""
import pytest
from fastapi.testclient import TestClient
from api_server import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_list_applications_empty():
    response = client.get("/api/applications")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_application():
    payload = {
        "company": "Test Corp",
        "role": "Software Engineer",
        "status": "saved",
        "notes": "Great company",
        "url": "https://testcorp.com/jobs/1",
        "location": "New York, NY"
    }
    response = client.post("/api/applications", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["company"] == "Test Corp"
    assert data["role"] == "Software Engineer"
    assert data["status"] == "saved"
    assert "id" in data


def test_update_application_status():
    # Create first
    create = client.post("/api/applications", json={
        "company": "Acme Inc",
        "role": "Backend Engineer",
        "status": "saved"
    })
    app_id = create.json()["id"]

    # Update status
    response = client.patch(f"/api/applications/{app_id}", json={"status": "applied"})
    assert response.status_code == 200
    assert response.json()["status"] == "applied"


def test_update_nonexistent_application():
    response = client.patch("/api/applications/99999", json={"status": "applied"})
    assert response.status_code == 404


def test_delete_application():
    create = client.post("/api/applications", json={
        "company": "Delete Me Corp",
        "role": "QA Engineer",
        "status": "saved"
    })
    app_id = create.json()["id"]

    response = client.delete(f"/api/applications/{app_id}")
    assert response.status_code == 200

    # Confirm it's gone
    apps = client.get("/api/applications").json()
    assert not any(a["id"] == app_id for a in apps)


def test_get_stats():
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "by_status" in data
    assert "response_rate" in data


def test_get_usage():
    response = client.get("/api/usage")
    assert response.status_code == 200
    data = response.json()
    assert "adzuna" in data
    assert "serpapi" in data
    assert "claude" in data
    assert data["adzuna"]["limit"] == 250
    assert data["serpapi"]["period"] == "month"


def test_apply_to_nonexistent_job():
    response = client.post("/api/jobs/99999/apply")
    assert response.status_code == 404


def test_list_jobs_empty():
    response = client.get("/api/jobs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
