import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

SIMULATE = not os.getenv("ANTHROPIC_API_KEY")


def classify_email(subject: str, body: str) -> dict:
    """Classify a job-related email and return status and summary."""
    if SIMULATE:
        return _simulate_classify(subject, body)
    return _claude_classify(subject, body)


def _simulate_classify(subject: str, body: str) -> dict:
    """Simulated classification for development without API key."""
    subject_lower = subject.lower()
    if any(word in subject_lower for word in ["interview", "schedule", "call"]):
        status = "interview_scheduled"
        summary = "Recruiter is inviting you for an interview."
    elif any(word in subject_lower for word in ["offer", "congratulations"]):
        status = "offer"
        summary = "You received a job offer!"
    elif any(word in subject_lower for word in ["unfortunately", "not moving", "other candidates"]):
        status = "rejected"
        summary = "Application was not selected."
    else:
        status = "applied"
        summary = "Application received or under review."
    return {"status": status, "summary": summary, "simulated": True}


def _claude_classify(subject: str, body: str) -> dict:
    """Real classification using Claude AI API."""
    import anthropic

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    prompt = f"""Classify this job application email. Respond with ONLY a JSON object, no extra text.

Email subject: {subject}
Email body: {body}

Valid statuses: applied, interview_scheduled, offer, rejected

Respond ONLY with this JSON format:
{{"status": "<status>", "summary": "<one sentence summary>"}}"""

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}]
    )

    text = message.content[0].text.strip()
    match = re.search(r'\{.*?\}', text, re.DOTALL)
    if match:
        return json.loads(match.group())
    return json.loads(text)