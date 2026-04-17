import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from api.database import get_db
from api.models import Application, JobListing
from src.logger import get_logger
from src.rate_limiter import check_limit, increment, get_all_usage

logger = get_logger("routes")
router = APIRouter()


# ─── Schemas ────────────────────────────────────────────────────────────────

class ApplicationCreate(BaseModel):
    company: str
    role: str
    status: str = "applied"
    notes: str = ""
    url: str = ""
    location: str = ""

class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

class JobSearchRequest(BaseModel):
    location: str = "New York"
    max_days: int = 2
    min_score: int = 60


# ─── Applications ────────────────────────────────────────────────────────────

@router.get("/applications")
def list_applications(db: Session = Depends(get_db)):
    return db.query(Application).order_by(Application.created_at.desc()).all()


@router.post("/applications")
def create_application(app: ApplicationCreate, db: Session = Depends(get_db)):
    db_app = Application(**app.model_dump())
    db.add(db_app)
    db.commit()
    db.refresh(db_app)
    return db_app


@router.patch("/applications/{app_id}")
def update_application(app_id: int, update: ApplicationUpdate, db: Session = Depends(get_db)):
    db_app = db.query(Application).filter(Application.id == app_id).first()
    if not db_app:
        raise HTTPException(status_code=404, detail="Application not found")
    if update.status:
        db_app.status = update.status
    if update.notes is not None:
        db_app.notes = update.notes
    db.commit()
    db.refresh(db_app)
    return db_app


@router.delete("/applications/{app_id}")
def delete_application(app_id: int, db: Session = Depends(get_db)):
    db_app = db.query(Application).filter(Application.id == app_id).first()
    if not db_app:
        raise HTTPException(status_code=404, detail="Application not found")
    db.delete(db_app)
    db.commit()
    return {"message": "Deleted successfully"}


# ─── Job Listings ────────────────────────────────────────────────────────────

@router.get("/jobs")
def list_jobs(db: Session = Depends(get_db)):
    return db.query(JobListing).order_by(JobListing.match_score.desc()).all()


@router.post("/jobs/search")
def search_jobs(request: JobSearchRequest, db: Session = Depends(get_db)):
    import os
    from src.mock_data import MOCK_MATCH_RESULTS, MOCK_KEYWORDS

    MOCK_MODE = os.getenv("MOCK_APIS", "false").lower() == "true"

    if MOCK_MODE:
        logger.info("🧪 MOCK MODE — no real API calls will be made")
        keywords = MOCK_KEYWORDS
        matches = [j for j in MOCK_MATCH_RESULTS if j["match_score"] >= request.min_score]
        logger.info(f"Mock: {len(matches)} jobs returned")
    else:
        # ⚠️  REAL API CALLS TEMPORARILY DISABLED
        # To re-enable: set MOCK_APIS=false in .env and uncomment the block below
        raise HTTPException(
            status_code=503,
            detail="Real API calls are disabled during development. Set MOCK_APIS=true in .env."
        )

        # from src.resume_parser import parse_resume
        # from src.job_search import search_jobs as do_search, filter_ghost_jobs
        # from src.job_matcher import match_jobs, generate_search_keywords
        #
        # resume_path = "resume.pdf"
        # if not os.path.exists(resume_path):
        #     raise HTTPException(status_code=400, detail="Resume not found. Upload resume.pdf first.")
        #
        # logger.info("Parsing resume...")
        # profile = parse_resume(resume_path)
        # logger.info(f"Resume parsed: {len(profile.get('skills', []))} skills found")
        #
        # if not check_limit("claude"):
        #     raise HTTPException(status_code=429, detail="Claude API daily limit reached. Try again tomorrow.")
        # logger.info("Generating search keywords with Claude AI...")
        # keywords = generate_search_keywords(profile)
        # increment("claude")
        # logger.info(f"Keywords generated: {keywords}")
        #
        # all_jobs = []
        # seen = set()
        # for keyword in keywords[:3]:
        #     if not check_limit("adzuna") and not check_limit("serpapi"):
        #         logger.warning("Both Adzuna and SerpAPI limits reached — stopping search early")
        #         break
        #     logger.info(f"Searching jobs for: '{keyword}' in {request.location}")
        #     jobs = do_search(keyword, request.location)
        #     increment("adzuna")
        #     increment("serpapi")
        #     active = filter_ghost_jobs(jobs, max_days=request.max_days)
        #     logger.info(f"  → {len(jobs)} found, {len(active)} after ghost filter")
        #     for job in active:
        #         key = f"{job['title'].lower()}_{job['company'].lower()}"
        #         if key not in seen:
        #             seen.add(key)
        #             all_jobs.append(job)
        #
        # logger.info(f"Total unique jobs: {len(all_jobs)} — scoring with Claude AI...")
        # matches = match_jobs(profile, all_jobs, min_score=request.min_score)
        # logger.info(f"Matches above {request.min_score}% score: {len(matches)}")

    # Save to database: upsert by company+title to preserve tracked jobs
    # Step 1: delete only jobs NOT already in the tracker
    tracked_keys = {
        (app.company.lower(), app.role.lower())
        for app in db.query(Application).all()
    }
    for existing_job in db.query(JobListing).all():
        key = (existing_job.company.lower(), existing_job.title.lower())
        if key not in tracked_keys:
            db.delete(existing_job)
    db.commit()

    # Step 2: upsert new results — update if exists, insert if not
    for job in matches:
        title = job.get("title", "")
        company = job.get("company", "")
        existing = db.query(JobListing).filter(
            JobListing.company == company,
            JobListing.title == title
        ).first()
        if existing:
            existing.match_score = job.get("match_score", 0)
            existing.match_verdict = job.get("match_verdict", "")
            existing.match_reason = job.get("match_reason", "")
            existing.date_posted = str(job.get("date", ""))
            existing.days_old = job.get("days_old") or 0
        else:
            db_job = JobListing(
                title=title,
                company=company,
                location=job.get("location", ""),
                description=job.get("description", ""),
                url=job.get("url", ""),
                source=job.get("source", ""),
                date_posted=str(job.get("date", "")),
                days_old=job.get("days_old") or 0,
                match_score=job.get("match_score", 0),
                match_verdict=job.get("match_verdict", ""),
                match_reason=job.get("match_reason", ""),
                matching_skills=json.dumps(job.get("matching_skills", [])),
                missing_skills=json.dumps(job.get("missing_skills", [])),
            )
            db.add(db_job)
    db.commit()

    # Step 3: return jobs from DB (with real IDs) sorted by score
    saved_jobs = db.query(JobListing).order_by(JobListing.match_score.desc()).all()
    jobs_out = []
    for j in saved_jobs:
        jobs_out.append({
            "id": j.id,
            "title": j.title,
            "company": j.company,
            "location": j.location,
            "description": j.description,
            "url": j.url,
            "source": j.source,
            "date": j.date_posted,
            "days_old": j.days_old,
            "match_score": j.match_score,
            "match_verdict": j.match_verdict,
            "match_reason": j.match_reason,
            "matching_skills": json.loads(j.matching_skills) if j.matching_skills else [],
            "missing_skills": json.loads(j.missing_skills) if j.missing_skills else [],
        })
    logger.info("Job search complete.")
    return {"found": len(jobs_out), "keywords": keywords, "jobs": jobs_out}


@router.post("/jobs/{job_id}/apply")
def apply_to_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(JobListing).filter(JobListing.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Prevent duplicates: check if already in tracker
    existing = db.query(Application).filter(
        Application.company == job.company,
        Application.role == job.title
    ).first()
    if existing:
        return existing

    db_app = Application(
        company=job.company,
        role=job.title,
        status="saved",
        url=job.url,
        location=job.location,
        match_score=job.match_score,
        match_reason=job.match_reason,
        matching_skills=job.matching_skills,
        missing_skills=job.missing_skills,
    )
    db.add(db_app)
    db.commit()
    db.refresh(db_app)
    return db_app


# ─── Resume ──────────────────────────────────────────────────────────────────

@router.post("/resume/upload")
async def upload_resume(file: UploadFile = File(...)):
    import shutil
    allowed = [".pdf", ".docx"]
    ext = "." + file.filename.split(".")[-1].lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files allowed.")

    with open("resume.pdf" if ext == ".pdf" else "resume.docx", "wb") as f:
        shutil.copyfileobj(file.file, f)

    return {"message": "Resume uploaded successfully", "filename": file.filename}


@router.get("/resume/profile")
def get_profile():
    from src.resume_parser import parse_resume
    import os
    resume_path = "resume.pdf" if os.path.exists("resume.pdf") else "resume.docx"
    if not os.path.exists(resume_path):
        raise HTTPException(status_code=404, detail="No resume found.")
    return parse_resume(resume_path)


# ─── API Usage ───────────────────────────────────────────────────────────────

@router.get("/usage")
def api_usage():
    """Returns daily API usage for all external services."""
    return get_all_usage()


# ─── Gmail Auth ──────────────────────────────────────────────────────────────

@router.get("/gmail/status")
def gmail_status():
    """Check if Gmail is connected (token.json exists and is valid)."""
    import os
    from src.gmail_api import get_credentials
    try:
        creds = get_credentials()
        return {"connected": creds is not None}
    except Exception:
        return {"connected": False}


@router.get("/gmail/auth")
def gmail_auth():
    """Generate Google OAuth URL for Gmail authentication."""
    import os
    from src.gmail_api import get_auth_url
    if not os.path.exists("credentials.json"):
        raise HTTPException(
            status_code=400,
            detail="credentials.json not found in project root. Set up Google Cloud credentials first."
        )
    url = get_auth_url()
    return {"auth_url": url}


@router.get("/gmail/callback")
def gmail_callback(code: str):
    """Handle Google OAuth callback — exchange code for token and save."""
    from src.gmail_api import exchange_code
    from fastapi.responses import HTMLResponse
    try:
        exchange_code(code)
        logger.info("Gmail OAuth completed successfully.")
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Gmail Connected</title>
            <style>
                body { font-family: sans-serif; display: flex; align-items: center;
                       justify-content: center; height: 100vh; margin: 0; background: #f5f5f5; }
                .card { background: white; padding: 40px; border-radius: 12px;
                        text-align: center; box-shadow: 0 2px 12px rgba(0,0,0,0.1); }
                h2 { color: #2e7d32; margin-bottom: 8px; }
                p { color: #666; }
            </style>
        </head>
        <body>
            <div class="card">
                <h2>✅ Gmail Connected!</h2>
                <p>You can close this tab and return to Career Compass.</p>
                <script>setTimeout(() => window.close(), 2000);</script>
            </div>
        </body>
        </html>
        """)
    except Exception as e:
        logger.error(f"Gmail OAuth failed: {e}")
        raise HTTPException(status_code=400, detail=f"OAuth failed: {str(e)}")


# ─── Gmail Sync ──────────────────────────────────────────────────────────────

@router.post("/gmail/sync")
def gmail_sync(db: Session = Depends(get_db)):
    """Fetch and classify job emails from Gmail, save new ones to the tracker."""
    import os
    from src.mock_data import MOCK_EMAIL_CLASSIFICATIONS

    MOCK_MODE = os.getenv("MOCK_APIS", "false").lower() == "true"

    if MOCK_MODE:
        logger.info("🧪 MOCK MODE — returning mock email classifications")
        results = MOCK_EMAIL_CLASSIFICATIONS
    else:
        from src.gmail_api import process_job_emails

        if not os.path.exists("token.json"):
            raise HTTPException(
                status_code=400,
                detail="Gmail not connected. Click 'Connect Gmail' first."
            )

        if not check_limit("claude"):
            raise HTTPException(status_code=429, detail="Claude API daily limit reached. Try again tomorrow.")

        logger.info("Starting Gmail sync...")
        results = process_job_emails()
    logger.info(f"Gmail returned {len(results)} classified emails")

    added = 0
    skipped = 0

    for item in results:
        # Skip emails that don't represent a real application status
        if item["status"] in ("unknown", "newsletter", "other"):
            skipped += 1
            continue

        # Deduplicate by company + role derived from email subject
        company = item.get("from", "Unknown").split("<")[0].strip()
        role = item.get("email", "Unknown Position")[:100]

        existing = db.query(Application).filter(
            Application.company == company,
            Application.role == role
        ).first()

        if existing:
            # Update status if it has progressed
            # TODO: "rejected" has same rank as "applied", so a rejection email never
            # overwrites an "applied" status. Rejection should always win (except over "offer").
            # See PROGRESS.md → Known Issues.
            STATUS_RANK = {"saved": 0, "applied": 1, "interview_scheduled": 2, "offer": 3, "rejected": 1}
            if STATUS_RANK.get(item["status"], 0) > STATUS_RANK.get(existing.status, 0):
                existing.status = item["status"]
                logger.info(f"Updated status: {company} → {item['status']}")
            skipped += 1
        else:
            db_app = Application(
                company=company,
                role=role,
                status=item["status"],
                notes=item.get("summary", ""),
            )
            db.add(db_app)
            added += 1
            # TODO: increment("claude") runs even in MOCK mode, inflating the usage counter.
            # Move this inside the non-mock branch above. See PROGRESS.md → Known Issues.
            increment("claude")
            logger.info(f"Added: {role} at {company} [{item['status']}]")

    db.commit()
    logger.info(f"Gmail sync complete: {added} added, {skipped} skipped")

    return {
        "processed": len(results),
        "added": added,
        "skipped": skipped,
        "message": f"{added} new application{'s' if added != 1 else ''} added to your tracker."
    }


# ─── Stats ───────────────────────────────────────────────────────────────────

@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    apps = db.query(Application).all()
    total = len(apps)
    by_status = {}
    for app in apps:
        by_status[app.status] = by_status.get(app.status, 0) + 1
    return {
        "total": total,
        "by_status": by_status,
        "response_rate": round((by_status.get("interview_scheduled", 0) / total * 100), 1) if total else 0
    }
