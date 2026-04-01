"""Date alias resolution for the POS CLI.

Supports human-friendly aliases like 'today', 'yesterday', '7d',
'this-week', 'last-week', 'this-month', 'last-month', and raw YYYY-MM-DD.
"""

import re
from datetime import date, timedelta


def resolve_since_until(
    since_alias: str,
    until_alias: str | None = None,
) -> tuple[str, str]:
    """Resolve date aliases into (start_date, end_date) ISO strings.

    When only --since is given, bounded periods like 'last-month' resolve
    both start and end. Open periods like '7d' default end to today.
    When --until is also given, it overrides the computed end date.
    """
    today = date.today()
    start, end = _resolve_alias(since_alias, today)

    if until_alias is not None:
        _, end = _resolve_alias(until_alias, today)

    return start.isoformat(), end.isoformat()


def _resolve_alias(alias: str, today: date) -> tuple[date, date]:
    """Resolve a single alias into a (start, end) date pair."""
    alias = alias.strip().lower()

    if alias == "today":
        return today, today

    if alias == "yesterday":
        yesterday = today - timedelta(days=1)
        return yesterday, yesterday

    # Nd pattern: 7d, 30d, 90d
    nd_match = re.match(r"^(\d+)d$", alias)
    if nd_match:
        days = int(nd_match.group(1))
        return today - timedelta(days=days), today

    if alias == "this-week":
        monday = today - timedelta(days=today.weekday())
        return monday, today

    if alias == "last-week":
        this_monday = today - timedelta(days=today.weekday())
        last_monday = this_monday - timedelta(days=7)
        last_sunday = this_monday - timedelta(days=1)
        return last_monday, last_sunday

    if alias == "this-month":
        return today.replace(day=1), today

    if alias == "last-month":
        first_of_this = today.replace(day=1)
        last_of_prev = first_of_this - timedelta(days=1)
        first_of_prev = last_of_prev.replace(day=1)
        return first_of_prev, last_of_prev

    if alias == "last-same-weekday":
        same_day_last_week = today - timedelta(days=7)
        return same_day_last_week, same_day_last_week

    # Raw YYYY-MM-DD
    try:
        d = date.fromisoformat(alias)
        return d, d
    except ValueError:
        pass

    raise ValueError(
        f"Unknown date alias: '{alias}'. "
        f"Use: today, yesterday, Nd (e.g. 7d), this-week, last-week, "
        f"this-month, last-month, or YYYY-MM-DD."
    )


def bucket_by_interval(date_str: str, interval: str) -> str:
    """Assign a date string to a time bucket.

    Returns: '2026-01' for month, '2026-W13' for week, '2026-03-31' for day.
    """
    d = date.fromisoformat(date_str)
    if interval == "month":
        return d.strftime("%Y-%m")
    if interval == "week":
        iso = d.isocalendar()
        return f"{iso[0]}-W{iso[1]:02d}"
    return date_str
