import os
import requests
from dotenv import load_dotenv

load_dotenv()

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_API_KEY = os.getenv("ADZUNA_API_KEY")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")


def search_adzuna(keywords, location="New York", results=20):
    """Search jobs via Adzuna API."""
    url = f"https://api.adzuna.com/v1/api/jobs/us/search/1"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_API_KEY,
        "what": keywords,
        "where": location,
        "results_per_page": results,
        "content-type": "application/json"
    }
    response = requests.get(url, params=params)
    data = response.json()

    jobs = []
    for job in data.get("results", []):
        jobs.append({
            "title": job.get("title", ""),
            "company": job.get("company", {}).get("display_name", ""),
            "location": job.get("location", {}).get("display_name", ""),
            "description": job.get("description", "")[:300],
            "url": job.get("redirect_url", ""),
            "date": job.get("created", "")[:10],
            "salary_min": job.get("salary_min", "N/A"),
            "salary_max": job.get("salary_max", "N/A"),
            "source": "adzuna"
        })
    return jobs


def search_serpapi(keywords, location="New York, NY"):
    """Search jobs via SerpAPI (Google Jobs)."""
    params = {
        "engine": "google_jobs",
        "q": keywords,
        "location": location,
        "api_key": SERPAPI_KEY,
        "hl": "en",
        "gl": "us"
    }
    response = requests.get("https://serpapi.com/search", params=params)
    data = response.json()

    jobs = []
    for job in data.get("jobs_results", []):
        jobs.append({
            "title": job.get("title", ""),
            "company": job.get("company_name", ""),
            "location": job.get("location", ""),
            "description": job.get("description", "")[:300],
            "url": job.get("share_link", ""),
            "date": job.get("detected_extensions", {}).get("posted_at", ""),
            "salary_min": "N/A",
            "salary_max": "N/A",
            "source": "google_jobs"
        })
    return jobs


def search_jobs(keywords, location="New York"):
    """Search jobs from all sources and merge results."""
    print(f"Searching for: {keywords} in {location}...")

    adzuna_jobs = search_adzuna(keywords, location)
    serp_jobs = search_serpapi(keywords, location)

    all_jobs = adzuna_jobs + serp_jobs

    # Remove duplicates by title + company
    seen = set()
    unique_jobs = []
    for job in all_jobs:
        key = f"{job['title'].lower()}_{job['company'].lower()}"
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)

    print(f"Found {len(unique_jobs)} unique jobs ({len(adzuna_jobs)} Adzuna + {len(serp_jobs)} Google Jobs)")
    return unique_jobs


def filter_ghost_jobs(jobs, max_days=2):
    """Filter out ghost jobs older than max_days."""
    import re
    from datetime import datetime, timezone

    def parse_days_old(date_str):
        if not date_str:
            return None
        # ISO format: 2026-04-13
        try:
            posted = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            if posted.tzinfo is None:
                posted = posted.replace(tzinfo=timezone.utc)
            return (datetime.now(timezone.utc) - posted).days
        except:
            pass
        # Text format: "1 day ago", "3 days ago", "24 days ago"
        match = re.search(r"(\d+)\s+day", date_str.lower())
        if match:
            return int(match.group(1))
        # "just posted" or "today"
        if any(w in date_str.lower() for w in ["just", "today", "hour", "minute"]):
            return 0
        return None

    active_jobs = []
    ghost_jobs = []

    for job in jobs:
        days_old = parse_days_old(job.get("date", ""))
        job["days_old"] = days_old
        if days_old is None or days_old <= max_days:
            active_jobs.append(job)
        else:
            ghost_jobs.append(job)

    print(f"Active jobs: {len(active_jobs)} | Ghost jobs filtered: {len(ghost_jobs)}")
    return active_jobs
