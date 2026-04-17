"""
Gmail OAuth integration for Career Compass.

Flow:
1. get_auth_url()  → returns Google OAuth URL
2. User authenticates in browser → Google redirects to /api/gmail/callback?code=...
3. exchange_code(code) → saves token.json
4. process_job_emails() → fetches + classifies emails with Claude
"""

import os
import json
import base64
import re
from src.logger import get_logger

logger = get_logger("gmail_api")

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"
REDIRECT_URI = "http://localhost:8000/api/gmail/callback"


# ─── Auth ────────────────────────────────────────────────────────────────────

def get_credentials():
    """Load credentials from token.json, refreshing if expired."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    if not os.path.exists(TOKEN_FILE):
        return None

    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if creds and creds.expired and creds.refresh_token:
        logger.info("Refreshing expired Gmail token...")
        creds.refresh(Request())
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
        logger.info("Token refreshed and saved.")

    return creds if creds and creds.valid else None


def get_auth_url() -> str:
    """Generate Google OAuth authorization URL."""
    from google_auth_oauthlib.flow import Flow

    if not os.path.exists(CREDENTIALS_FILE):
        raise FileNotFoundError("credentials.json not found in project root.")

    flow = Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )
    logger.info("Gmail auth URL generated.")
    return auth_url


def exchange_code(code: str):
    """Exchange OAuth code for credentials and save to token.json."""
    from google_auth_oauthlib.flow import Flow

    flow = Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    flow.fetch_token(code=code)
    creds = flow.credentials

    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())

    logger.info("Gmail token saved — authentication complete.")
    return creds


# ─── Gmail Service ────────────────────────────────────────────────────────────

def get_gmail_service():
    """Return authenticated Gmail API service."""
    from googleapiclient.discovery import build

    creds = get_credentials()
    if not creds:
        raise ValueError("Gmail not authenticated. Connect Gmail first.")

    return build("gmail", "v1", credentials=creds)


# ─── Email Fetching ───────────────────────────────────────────────────────────

def fetch_job_emails(max_results: int = 20) -> list:
    """Fetch real job-related emails, excluding newsletters and marketing."""
    service = get_gmail_service()

    # Precise query: job-related subjects/senders, excludes digests and newsletters
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

    logger.info(f"Fetching up to {max_results} job emails from Gmail...")
    results = service.users().messages().list(
        userId="me", q=query, maxResults=max_results
    ).execute()

    messages = results.get("messages", [])
    logger.info(f"Found {len(messages)} matching emails.")

    emails = []
    for msg in messages:
        try:
            full_msg = service.users().messages().get(
                userId="me",
                id=msg["id"],
                format="metadata",
                metadataHeaders=["Subject", "From", "Date"]
            ).execute()

            headers = {h["name"]: h["value"] for h in full_msg["payload"]["headers"]}
            emails.append({
                "id": msg["id"],
                "subject": headers.get("Subject", "(no subject)"),
                "from": headers.get("From", ""),
                "date": headers.get("Date", ""),
                # internalDate = ms since epoch (UTC), assigned by Gmail on receipt.
                # Always present and reliable — prefer over the RFC 2822 "Date" header,
                # which can be malformed or spoofed by the sender.
                "internal_date": full_msg.get("internalDate"),
                "snippet": full_msg.get("snippet", "")
            })
        except Exception as e:
            logger.warning(f"Failed to fetch email {msg['id']}: {e}")
            continue

    return emails


# ─── Classification ───────────────────────────────────────────────────────────

def classify_email(subject: str, body: str) -> dict:
    """Use Claude Haiku to classify a job-related email."""
    import anthropic

    client = anthropic.Anthropic()

    prompt = f"""Classify this job application email. Respond with JSON only.

Subject: {subject}
Body: {body[:500]}

JSON format:
{{
    "status": "applied|interview_scheduled|offer|rejected|unknown",
    "company": "company name",
    "role": "job title",
    "summary": "one sentence summary"
}}

Rules:
- applied = application received confirmation
- interview_scheduled = interview invitation or confirmation
- offer = job offer
- rejected = application declined
- unknown = newsletter, digest, or unrelated"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        text = message.content[0].text
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        logger.warning(f"Failed to parse Claude response: {e}")

    return {
        "status": "unknown",
        "company": subject,
        "role": subject,
        "summary": "Could not classify email."
    }


# ─── Main Entry Point ─────────────────────────────────────────────────────────

def process_job_emails(max_emails: int = 20) -> list:
    """Fetch and classify job emails from Gmail. Called by /api/gmail/sync."""
    emails = fetch_job_emails(max_results=max_emails)

    results = []
    for email in emails:
        logger.info(f"Classifying: {email['subject'][:60]}...")
        classification = classify_email(
            subject=email["subject"],
            body=email["snippet"]
        )
        results.append({
            "email": classification.get("role", email["subject"]),
            "from": classification.get("company", email["from"].split("<")[0].strip()),
            "status": classification.get("status", "unknown"),
            "summary": classification.get("summary", ""),
            "date": email["date"],
            "internal_date": email.get("internal_date"),
        })

    logger.info(f"Gmail processing complete: {len(results)} emails classified.")
    return results
