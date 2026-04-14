import os
import json
import hashlib
import re
import pdfplumber
from docx import Document
from dotenv import load_dotenv

load_dotenv()

CACHE_FILE = "data/resume_cache.json"


def _get_file_hash(file_path):
    """Generate MD5 hash of file to detect changes."""
    with open(file_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def _load_cache():
    """Load cached resume data."""
    os.makedirs("data", exist_ok=True)
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}


def _save_cache(cache):
    """Save resume data to cache."""
    os.makedirs("data", exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def _extract_text_from_pdf(file_path):
    """Extract text from PDF using pdfplumber."""
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text


def _extract_text_from_docx(file_path):
    """Extract text from Word document."""
    doc = Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])


def _extract_text(file_path):
    """Extract text from PDF or DOCX automatically."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return _extract_text_from_pdf(file_path)
    elif ext in [".docx", ".doc"]:
        return _extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}. Use PDF or DOCX.")


def _parse_with_claude(text):
    """Use Claude AI to extract structured profile from resume text."""
    import anthropic
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    prompt = f"""Analyze this resume and extract a structured profile. Respond ONLY with a JSON object.

Resume text:
{text[:3000]}

Respond with this exact JSON format:
{{
  "name": "candidate full name",
  "title": "current or desired job title",
  "summary": "2-3 sentence professional summary",
  "skills": ["skill1", "skill2", "skill3"],
  "experience_years": 0,
  "seniority": "junior|mid|senior|staff|principal",
  "languages": ["Python", "JavaScript"],
  "industries": ["FinTech", "Healthcare"],
  "last_role": "last job title",
  "last_company": "last company name"
}}"""

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    text_response = message.content[0].text.strip()
    match = re.search(r'\{.*\}', text_response, re.DOTALL)
    if match:
        return json.loads(match.group())
    return json.loads(text_response)


def parse_resume(file_path):
    """
    Parse resume with intelligent caching.
    Only calls Claude API if file has changed since last parse.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Resume not found: {file_path}")

    file_hash = _get_file_hash(file_path)
    cache = _load_cache()

    # Return cached result if file unchanged
    if file_path in cache and cache[file_path]["hash"] == file_hash:
        print("✅ Resume loaded from cache (no API call needed)")
        return cache[file_path]["profile"]

    # File changed or first time — parse with Claude
    print("🔄 New resume detected — parsing with Claude AI...")
    text = _extract_text(file_path)
    profile = _parse_with_claude(text)

    # Save to cache
    cache[file_path] = {"hash": file_hash, "profile": profile}
    _save_cache(cache)

    print("✅ Resume parsed and cached successfully")
    return profile
