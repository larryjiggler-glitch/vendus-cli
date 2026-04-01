"""Payments commands: summary and mix by payment method."""

import argparse
from collections import defaultdict
from typing import Any

import requests

from vendus_cli.api import fetch_documents, safe_float
from vendus_cli.dates import resolve_since_until


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register payments subcommands."""
    parser = subparsers.add_parser("payments", help="Payment analytics")
    sub = parser.add_subparsers(dest="subcmd")

    p = sub.add_parser("summary", help="Payment totals by method")
    p.add_argument("--since", required=True, help="Start: today, yesterday, 7d, YYYY-MM-DD")
    p.add_argument("--until", default=None)
    p.add_argument("--store", type=int, default=None)
    p.set_defaults(func=cmd_summary)

    p = sub.add_parser("mix", help="Payment method distribution (%)")
    p.add_argument("--since", required=True, help="Start: today, yesterday, 7d, YYYY-MM-DD")
    p.add_argument("--until", default=None)
    p.add_argument("--store", type=int, default=None)
    p.set_defaults(func=cmd_mix)


def _aggregate_payments(
    docs: list[dict[str, Any]],
) -> dict[str, float]:
    """Aggregate payment amounts by method title."""
    by_method: dict[str, float] = defaultdict(float)
    for d in docs:
        payments = d.get("payments") or []
        for p in payments:
            title = p.get("title", "Unknown")
            amount = safe_float(p.get("amount", 0))
            by_method[title] += amount
    return dict(by_method)


def cmd_summary(
    args: argparse.Namespace,
    session: requests.Session,
) -> dict[str, Any]:
    since, until = resolve_since_until(args.since, args.until)
    # Payments are in the detailed view (list endpoint with view=detailed includes them)
    docs = fetch_documents(session, since, until, detailed=True, store_id=args.store)

    by_method = _aggregate_payments(docs)
    total = sum(by_method.values())

    methods = sorted(
        [{"method": k, "total": round(v, 2)} for k, v in by_method.items()],
        key=lambda x: -x["total"],
    )

    return {
        "period": {"since": since, "until": until},
        "total": round(total, 2),
        "methods": methods,
    }


def cmd_mix(
    args: argparse.Namespace,
    session: requests.Session,
) -> dict[str, Any]:
    since, until = resolve_since_until(args.since, args.until)
    docs = fetch_documents(session, since, until, detailed=True, store_id=args.store)

    by_method = _aggregate_payments(docs)
    total = sum(by_method.values())

    methods = sorted(
        [
            {
                "method": k,
                "total": round(v, 2),
                "pct": round((v / total) * 100, 1) if total else 0,
            }
            for k, v in by_method.items()
        ],
        key=lambda x: -x["total"],
    )

    return {
        "period": {"since": since, "until": until},
        "total": round(total, 2),
        "methods": methods,
    }
