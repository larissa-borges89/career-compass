import os
import json
import pytest
from src.tracker import add_application, list_applications, update_status

TEST_DATA_FILE = "data/applications.json"

def setup_function():
    """Remove test data before each test."""
    if os.path.exists(TEST_DATA_FILE):
        os.remove(TEST_DATA_FILE)

def test_add_application():
    app = add_application("Stripe", "Backend Engineer")
    assert app["company"] == "Stripe"
    assert app["role"] == "Backend Engineer"
    assert app["status"] == "applied"
    assert app["id"] == 1

def test_list_applications():
    add_application("Stripe", "Backend Engineer")
    add_application("Airbnb", "Senior Engineer")
    apps = list_applications()
    assert len(apps) == 2

def test_update_status():
    app = add_application("Stripe", "Backend Engineer")
    updated = update_status(app["id"], "interview_scheduled")
    assert updated["status"] == "interview_scheduled"

def test_update_status_not_found():
    result = update_status(999, "offer")
    assert result is None