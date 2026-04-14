import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from api.database import get_db
from api.models import Application, JobListing

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
    db_app = Application(**app.dict())
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
    from src.resume_parser import parse_resume
    from src.job_search import search_jobs as do_search, filter_ghost_jobs
    from src.job_matcher import match_jobs, generate_search_keywords
    import os

    resume_path = "resume.pdf"
    if not os.path.exists(resume_path):
        raise HTTPException(status_code=400, detail="Resume not found. Upload resume.pdf first.")

    profile = parse_resume(resume_path)
    keywords = generate_search_keywords(profile)

    all_jobs = []
    seen = set()
    for keyword in keywords[:3]:
        jobs = do_search(keyword, request.location)
        active = filter_ghost_jobs(jobs, max_days=request.max_days)
        for job in active:
            key = f"{job['title'].lower()}_{job['company'].lower()}"
            if key not in seen:
                seen.add(key)
                all_jobs.append(job)

    matches = match_jobs(profile, all_jobs, min_score=request.min_score)

    # Save to database
    db.query(JobListing).delete()
    for job in matches:
        db_job = JobListing(
            title=job.get("title", ""),
            company=job.get("company", ""),
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

    return {"found": len(matches), "keywords": keywords, "jobs": matches}


@router.post("/jobs/{job_id}/apply")
def apply_to_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(JobListing).filter(JobListing.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    db_app = Application(
        company=job.company,
        role=job.title,
        status="applied",
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
