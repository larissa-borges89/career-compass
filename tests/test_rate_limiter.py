"""Tests for rate limiter module."""
import json
import os
import pytest
from unittest.mock import patch
from datetime import date


@pytest.fixture(autouse=True)
def clean_usage_file(tmp_path, monkeypatch):
    """Use a temp file for each test — no cross-test pollution."""
    usage_file = tmp_path / "api_usage.json"
    monkeypatch.setattr("src.rate_limiter.USAGE_FILE", str(usage_file))
    yield usage_file


def test_initial_usage_is_zero():
    from src.rate_limiter import get_usage
    usage = get_usage("adzuna")
    assert usage["used"] == 0
    assert usage["limit"] == 250
    assert usage["remaining"] == 250
    assert usage["period"] == "day"


def test_increment_increases_count():
    from src.rate_limiter import increment, get_usage
    increment("adzuna")
    increment("adzuna")
    assert get_usage("adzuna")["used"] == 2


def test_check_limit_allows_when_under():
    from src.rate_limiter import check_limit
    assert check_limit("adzuna") is True


def test_check_limit_blocks_when_over(monkeypatch):
    from src.rate_limiter import check_limit, increment
    monkeypatch.setitem(__import__("src.rate_limiter", fromlist=["LIMITS"]).LIMITS,
                        "adzuna", {"limit": 2, "period": "day"})
    increment("adzuna")
    increment("adzuna")
    assert check_limit("adzuna") is False


def test_serpapi_uses_monthly_period():
    from src.rate_limiter import get_usage
    usage = get_usage("serpapi")
    assert usage["period"] == "month"
    assert usage["limit"] == 100
    assert "month" in usage["resets"]


def test_increment_serpapi_uses_month_key(clean_usage_file):
    from src.rate_limiter import increment
    increment("serpapi")
    data = json.loads(clean_usage_file.read_text())
    month_key = date.today().strftime("%Y-%m")
    assert month_key in data
    assert data[month_key]["serpapi"] == 1


def test_get_all_usage_returns_all_apis():
    from src.rate_limiter import get_all_usage
    usage = get_all_usage()
    assert "adzuna" in usage
    assert "serpapi" in usage
    assert "claude" in usage


def test_multiple_apis_tracked_independently():
    from src.rate_limiter import increment, get_usage
    increment("adzuna", 5)
    increment("claude", 2)
    assert get_usage("adzuna")["used"] == 5
    assert get_usage("claude")["used"] == 2
    assert get_usage("serpapi")["used"] == 0
