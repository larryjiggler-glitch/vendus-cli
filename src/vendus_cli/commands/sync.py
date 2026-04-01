"""Sync commands: export sales data."""

import argparse
import json
from datetime import datetime, timezone
from typing import Any

import requests

from vendus_cli.api import fetch_all, fetch_categories, fetch_documents
from vendus_cli.dates import resolve_since_until


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register sync subcommands."""
    parser = subparsers.add_parser("sync", help="Data export and sync")
    sub = parser.add_subparsers(dest="subcmd")

    p = sub.add_parser("sales", help="Export sales documents to JSON")
    p.add_argument("--since", required=True, help="Start: today, yesterday, 7d, YYYY-MM-DD")
    p.add_argument("--until", default=None)
    p.add_argument("--output", default=None, help="Output file (default: vendus-sales.json)")
    p.set_defaults(func=cmd_sync_sales)


def cmd_sync_sales(
    args: argparse.Namespace,
    session: requests.Session,
) -> dict[str, Any]:
    since, until = resolve_since_until(args.since, args.until)
    docs = fetch_documents(session, since, until, detailed=True)

    # Include product + category maps for offline queries
    products = fetch_all(session, "products", per_page=500)
    product_map = {
        str(p["id"]): {
            "title": p.get("title", ""),
            "category_id": p.get("category_id", 0),
        }
        for p in products
    }
    cats = fetch_categories(session)
    category_map = {str(c["id"]): c["title"] for c in cats}

    output = {
        "metadata": {
            "start_date": since,
            "end_date": until,
            "total_count": len(docs),
            "extracted_at": datetime.now(timezone.utc).isoformat(),
        },
        "products": product_map,
        "categories": category_map,
        "transactions": docs,
    }

    path = args.output or "./vendus-sales.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    return {"saved": path, "total_count": len(docs), "period": {"since": since, "until": until}}
