"""
Rate limiter for external APIs.
Tracks daily usage in data/api_usage.json and enforces limits
before making calls — zero waste of API quota.
"""

import json
import os
from datetime import date
from src.logger import get_logger

logger = get_logger("rate_limiter")

USAGE_FILE = "data/api_usage.json"

# Daily limits (adjust based on your plan)
LIMITS = {
    "adzuna":  250,   # Adzuna free: 250/day
    "serpapi": 100,   # SerpAPI free: 100/month (~3/day safe buffer)
    "claude":  50,    # Claude API calls per day (conservative)
}


def _load() -> dict:
    if not os.path.exists(USAGE_FILE):
        return {}
    try:
        with open(USAGE_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data: dict):
    os.makedirs("data", exist_ok=True)
    with open(USAGE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _today() -> str:
    return str(date.today())


def get_usage(api: str) -> dict:
    """Returns current usage and limit for an API."""
    data = _load()
    today = _today()
    count = data.get(today, {}).get(api, 0)
    limit = LIMITS.get(api, 999)
    return {"api": api, "used": count, "limit": limit, "remaining": limit - count}


def check_limit(api: str) -> bool:
    """Returns True if the API can be called, False if limit reached."""
    usage = get_usage(api)
    if usage["remaining"] <= 0:
        logger.warning(
            f"Rate limit reached for {api}: {usage['used']}/{usage['limit']} calls today"
        )
        return False
    return True


def increment(api: str, count: int = 1):
    """Increments the call counter for an API."""
    data = _load()
    today = _today()
    if today not in data:
        data[today] = {}
    data[today][api] = data[today].get(api, 0) + count
    _save(data)
    usage = get_usage(api)
    logger.info(f"API usage [{api}]: {usage['used']}/{usage['limit']} today")


def get_all_usage() -> dict:
    """Returns usage summary for all APIs today."""
    return {api: get_usage(api) for api in LIMITS}
