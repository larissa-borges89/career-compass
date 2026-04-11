import json
import os
from datetime import datetime

DATA_FILE = "data/applications.json"

def load_applications():
    """Load all job applications from file."""
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_applications(applications):
    """Save all job applications to file."""
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(applications, f, indent=2)

def add_application(company, role, status="applied", notes=""):
    """Add a new job application."""
    applications = load_applications()
    application = {
        "id": len(applications) + 1,
        "company": company,
        "role": role,
        "status": status,
        "notes": notes,
        "created_at": datetime.now().isoformat()
    }
    applications.append(application)
    save_applications(applications)
    return application

def list_applications():
    """Return all job applications."""
    return load_applications()

def update_status(app_id, new_status):
    """Update the status of an application."""
    applications = load_applications()
    for app in applications:
        if app["id"] == app_id:
            app["status"] = new_status
            app["updated_at"] = datetime.now().isoformat()
            save_applications(applications)
            return app
    return None