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


def _payment_breakdown(
    args: argparse.Namespace,
    session: requests.Session,
    include_pct: bool = False,
) -> dict[str, Any]:
    """Shared logic for summary and mix commands."""
    since, until = resolve_since_until(args.since, args.until)
    docs = fetch_documents(session, since, until, detailed=True, store_id=args.store)

    by_method: dict[str, float] = defaultdict(float)
    for d in docs:
        for p in d.get("payments") or []:
            by_method[p.get("title", "Unknown")] += safe_float(p.get("amount", 0))

    total = sum(by_method.values())
    methods = sorted(
        [
            {
                "method": k,
                "total": round(v, 2),
                **({"pct": round((v / total) * 100, 1) if total else 0} if include_pct else {}),
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


def cmd_summary(
    args: argparse.Namespace,
    session: requests.Session,
) -> dict[str, Any]:
    return _payment_breakdown(args, session, include_pct=False)


def cmd_mix(
    args: argparse.Namespace,
    session: requests.Session,
) -> dict[str, Any]:
    return _payment_breakdown(args, session, include_pct=True)
