import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

def get_gmail_service():
    """Authenticate and return Gmail API service."""
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)

def fetch_job_emails(max_results=20):
    """Fetch real job-related emails, excluding newsletters and marketing."""
    service = get_gmail_service()

    query = (
        "("
        "subject:(application OR interview OR offer OR hiring OR "
        "\"thank you for applying\" OR \"next steps\" OR "
        "\"we received\" OR \"unfortunately\" OR \"moving forward\") "
        "OR from:(recruit OR talent OR hiring OR hr) "
        ") "
        "-from:(interviewkickstart.com OR editors-noreply@linkedin.com OR "
        "jobalerts-noreply@linkedin.com OR ziprecruiter.com) "
        "-category:promotions "
        "-category:social "
        "-subject:(unsubscribe OR newsletter)"
    )
    
    results = service.users().messages().list(
        userId="me", q=query, maxResults=max_results
    ).execute()

    messages = results.get("messages", [])
    emails = []

    for msg in messages:
        full_msg = service.users().messages().get(
            userId="me", id=msg["id"], format="metadata",
            metadataHeaders=["Subject", "From", "Date"]
        ).execute()

        headers = {h["name"]: h["value"] for h in full_msg["payload"]["headers"]}
        emails.append({
            "id": msg["id"],
            "subject": headers.get("Subject", ""),
            "from": headers.get("From", ""),
            "date": headers.get("Date", ""),
            "snippet": full_msg.get("snippet", "")
        })

    return emails


def process_job_emails():
    """Fetch emails and classify them using Claude AI."""
    from src.claude_ai import classify_email
    from src.tracker import list_applications, update_status

    emails = fetch_job_emails()
    results = []

    for email in emails:
        classification = classify_email(
            subject=email["subject"],
            body=email["snippet"]
        )

        results.append({
            "email": email["subject"],
            "from": email["from"],
            "date": email["date"],
            "status": classification["status"],
            "summary": classification["summary"]
        })

    return results