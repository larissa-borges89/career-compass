"""
Rate limiter for external APIs.
Tracks usage in data/api_usage.json and enforces limits
before making calls — zero waste of API quota.

Supports daily and monthly periods.
"""

import json
import os
from datetime import date
from src.logger import get_logger

logger = get_logger("rate_limiter")

USAGE_FILE = "data/api_usage.json"

# Real limits based on actual free tier plans
LIMITS = {
    "adzuna":  {"limit": 250, "period": "day"},    # Adzuna free: 250 requests/day
    "serpapi": {"limit": 100, "period": "month"},  # SerpAPI free: 100 searches/month
    "claude":  {"limit": 50,  "period": "day"},    # Conservative daily cap on Claude calls
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


def _period_key(period: str) -> str:
    today = date.today()
    if period == "month":
        return today.strftime("%Y-%m")  # e.g. "2026-04"
    return str(today)                   # e.g. "2026-04-14"


def get_usage(api: str) -> dict:
    """Returns current usage and limit for an API."""
    config = LIMITS.get(api, {"limit": 999, "period": "day"})
    period_key = _period_key(config["period"])
    data = _load()
    used = data.get(period_key, {}).get(api, 0)
    limit = config["limit"]
    return {
        "api": api,
        "used": used,
        "limit": limit,
        "remaining": limit - used,
        "period": config["period"],
        "resets": "midnight" if config["period"] == "day" else "1st of next month",
    }


def check_limit(api: str) -> bool:
    """Returns True if the API can be called, False if limit reached."""
    usage = get_usage(api)
    if usage["remaining"] <= 0:
        logger.warning(
            f"Rate limit reached for {api}: {usage['used']}/{usage['limit']} "
            f"this {usage['period']} (resets {usage['resets']})"
        )
        return False
    return True


def increment(api: str, count: int = 1):
    """Increments the call counter for an API."""
    config = LIMITS.get(api, {"limit": 999, "period": "day"})
    period_key = _period_key(config["period"])
    data = _load()
    if period_key not in data:
        data[period_key] = {}
    data[period_key][api] = data[period_key].get(api, 0) + count
    _save(data)
    usage = get_usage(api)
    logger.info(
        f"API usage [{api}]: {usage['used']}/{usage['limit']} this {usage['period']} "
        f"({usage['remaining']} remaining)"
    )


def get_all_usage() -> dict:
    """Returns usage summary for all APIs."""
    return {api: get_usage(api) for api in LIMITS}
