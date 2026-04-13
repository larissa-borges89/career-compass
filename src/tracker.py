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

def sync_emails_to_tracker():
    """Fetch job emails, classify with Claude AI, and sync to tracker."""
    from src.gmail_api import process_job_emails

    print("\n🔄 Syncing emails to tracker...\n")
    results = process_job_emails()

    if not results:
        print("No job-related emails found.")
        return

    applications = load_applications()
    synced = 0

    for result in results:
        company = result["from"].split("<")[0].strip().strip('"')
        subject = result["email"]
        status = result["status"]
        summary = result["summary"]

        # Check if application already exists
        existing = next((a for a in applications if
                        subject.lower() in a.get("notes", "").lower() or
                        company.lower() in a.get("company", "").lower()), None)

        if existing:
            existing["status"] = status
            existing["updated_at"] = datetime.now().isoformat()
            print(f"✅ Updated: {existing['company']} → {status}")
        else:
            new_app = {
                "id": len(applications) + 1,
                "company": company,
                "role": subject,
                "status": status,
                "notes": summary,
                "created_at": datetime.now().isoformat()
            }
            applications.append(new_app)
            print(f"➕ Added: {company} → {status}")

        synced += 1

    save_applications(applications)
    print(f"\n✅ Synced {synced} emails to tracker.")