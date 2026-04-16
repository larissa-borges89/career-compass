"""
Smoke test for Gmail sync endpoints in MOCK mode.

Usage:
    # Terminal 1: start backend
    source venv/bin/activate
    uvicorn api_server:app --reload --port 8000

    # Terminal 2: run this script
    python test_mock_gmail.py

Expects MOCK_APIS=true in .env. Does NOT consume any external API credits.
"""
import sys
import requests

BASE = "http://localhost:8000"
API_KEY = "career-compass-dev-key"
HEADERS = {"X-API-Key": API_KEY}

PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
DIM = "\033[90m"
RST = "\033[0m"

failures = []


def check(label, cond, detail=""):
    mark = PASS if cond else FAIL
    print(f"  {mark} {label}" + (f" {DIM}({detail}){RST}" if detail else ""))
    if not cond:
        failures.append(label)


def section(title):
    print(f"\n\033[1m{title}\033[0m")


# ─── 1. Health check (no auth) ────────────────────────────────────────────────
section("1. GET /health (no auth)")
try:
    r = requests.get(f"{BASE}/health", timeout=5)
    check("responds 200", r.status_code == 200, f"got {r.status_code}")
    check("returns status=ok", r.json().get("status") == "ok", str(r.json()))
except Exception as e:
    print(f"  {FAIL} could not reach backend: {e}")
    print("\n  Is uvicorn running on port 8000?")
    sys.exit(1)


# ─── 2. Auth middleware still protects other endpoints ────────────────────────
section("2. Auth middleware (no API key → 401)")
r = requests.get(f"{BASE}/api/applications", timeout=5)
check("rejects without X-API-Key", r.status_code == 401, f"got {r.status_code}")


# ─── 3. Gmail status ──────────────────────────────────────────────────────────
section("3. GET /api/gmail/status")
r = requests.get(f"{BASE}/api/gmail/status", headers=HEADERS, timeout=5)
check("responds 200", r.status_code == 200, f"got {r.status_code}")
body = r.json() if r.ok else {}
check("has 'connected' field", "connected" in body, str(body))
print(f"    {DIM}→ Gmail connected: {body.get('connected')}{RST}")


# ─── 4. Gmail auth URL generation ─────────────────────────────────────────────
section("4. GET /api/gmail/auth (generate OAuth URL)")
r = requests.get(f"{BASE}/api/gmail/auth", headers=HEADERS, timeout=5)
check("responds 200", r.status_code == 200, f"got {r.status_code}")
if r.ok:
    body = r.json()
    url = body.get("auth_url", "")
    check("returns auth_url field", bool(url))
    check("URL points to accounts.google.com", "accounts.google.com" in url)
    check("URL includes redirect_uri", "redirect_uri=" in url)
    check("URL includes our callback path", "gmail%2Fcallback" in url or "gmail/callback" in url)


# ─── 5. Snapshot applications before sync ─────────────────────────────────────
section("5. GET /api/applications (before sync)")
r = requests.get(f"{BASE}/api/applications", headers=HEADERS, timeout=5)
check("responds 200", r.status_code == 200, f"got {r.status_code}")
before = r.json() if r.ok else []
print(f"    {DIM}→ {len(before)} applications before sync{RST}")


# ─── 6. Gmail sync in MOCK mode ───────────────────────────────────────────────
section("6. POST /api/gmail/sync (MOCK mode)")
r = requests.post(f"{BASE}/api/gmail/sync", headers=HEADERS, timeout=30)
check("responds 200 (not 503)", r.status_code == 200,
      f"got {r.status_code} → {r.text[:200]}")
if r.ok:
    body = r.json()
    check("processed == 3", body.get("processed") == 3, f"got {body.get('processed')}")
    check("has 'added' field", "added" in body)
    check("has 'skipped' field", "skipped" in body)
    check("added + skipped == 3", body.get("added", 0) + body.get("skipped", 0) == 3)
    print(f"    {DIM}→ processed=3, added={body.get('added')}, skipped={body.get('skipped')}{RST}")
    print(f"    {DIM}→ message: {body.get('message')}{RST}")


# ─── 7. Verify applications appeared in DB ────────────────────────────────────
section("7. GET /api/applications (after sync)")
r = requests.get(f"{BASE}/api/applications", headers=HEADERS, timeout=5)
check("responds 200", r.status_code == 200)
after = r.json() if r.ok else []
print(f"    {DIM}→ {len(after)} applications after sync{RST}")

# Find mock-sourced apps
mock_companies = {"recruiting@techcorp.com", "hr@fintechsolutions.com", "noreply@startuphub.com"}
mock_apps = [a for a in after if a.get("company") in mock_companies]
check(f"found {len(mock_apps)}/3 mock-sourced apps in DB",
      len(mock_apps) == 3,
      f"companies: {[a.get('company') for a in mock_apps]}")

statuses = {a.get("status") for a in mock_apps}
check("status 'applied' present", "applied" in statuses, str(statuses))
check("status 'interview_scheduled' present", "interview_scheduled" in statuses)
check("status 'rejected' present", "rejected" in statuses)


# ─── 8. Idempotency — second sync should not create duplicates ────────────────
section("8. POST /api/gmail/sync again (dedup)")
r = requests.post(f"{BASE}/api/gmail/sync", headers=HEADERS, timeout=30)
if r.ok:
    body = r.json()
    check("added == 0 (dedup works)", body.get("added") == 0,
          f"got added={body.get('added')}, skipped={body.get('skipped')}")


# ─── Summary ──────────────────────────────────────────────────────────────────
print()
if failures:
    print(f"\033[91m\033[1m{len(failures)} failure(s):\033[0m")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
else:
    print(f"\033[92m\033[1mAll checks passed. Mock Gmail sync is working end-to-end.\033[0m")
