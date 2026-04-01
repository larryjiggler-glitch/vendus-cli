"""Tests for date alias resolution."""

from datetime import date, timedelta
from unittest.mock import patch

import pytest

from vendus_cli.dates import resolve_since_until


@pytest.fixture
def fixed_today():
    """Fix 'today' to 2026-03-31 (Tuesday) for deterministic tests."""
    with patch("vendus_cli.dates.date") as mock_date:
        mock_date.today.return_value = date(2026, 3, 31)
        mock_date.fromisoformat = date.fromisoformat
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
        yield date(2026, 3, 31)


def test_today(fixed_today):
    assert resolve_since_until("today") == ("2026-03-31", "2026-03-31")


def test_yesterday(fixed_today):
    assert resolve_since_until("yesterday") == ("2026-03-30", "2026-03-30")


def test_nd_7d(fixed_today):
    since, until = resolve_since_until("7d")
    assert since == "2026-03-24"
    assert until == "2026-03-31"


def test_nd_30d(fixed_today):
    since, until = resolve_since_until("30d")
    assert since == "2026-03-01"
    assert until == "2026-03-31"


def test_this_week(fixed_today):
    # 2026-03-31 is Tuesday, Monday is 2026-03-30
    since, until = resolve_since_until("this-week")
    assert since == "2026-03-30"
    assert until == "2026-03-31"


def test_last_week(fixed_today):
    since, until = resolve_since_until("last-week")
    assert since == "2026-03-23"  # Monday
    assert until == "2026-03-29"  # Sunday


def test_this_month(fixed_today):
    since, until = resolve_since_until("this-month")
    assert since == "2026-03-01"
    assert until == "2026-03-31"


def test_last_month(fixed_today):
    since, until = resolve_since_until("last-month")
    assert since == "2026-02-01"
    assert until == "2026-02-28"


def test_last_same_weekday(fixed_today):
    # Tuesday 2026-03-31 → Tuesday 2026-03-24
    since, until = resolve_since_until("last-same-weekday")
    assert since == "2026-03-24"
    assert until == "2026-03-24"


def test_raw_date():
    since, until = resolve_since_until("2026-01-15")
    assert since == "2026-01-15"
    assert until == "2026-01-15"


def test_since_with_until():
    since, until = resolve_since_until("2026-01-01", "2026-01-31")
    assert since == "2026-01-01"
    assert until == "2026-01-31"


def test_invalid_alias():
    with pytest.raises(ValueError, match="Unknown date alias"):
        resolve_since_until("next-century")
