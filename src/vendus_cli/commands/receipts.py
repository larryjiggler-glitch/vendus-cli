"""Receipts commands: list, show, search."""

import argparse
from typing import Any

import requests

from vendus_cli.api import doc_gross, fetch_document_detail, fetch_documents
from vendus_cli.dates import resolve_since_until


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register receipts subcommands."""
    parser = subparsers.add_parser("receipts", help="Document receipts")
    sub = parser.add_subparsers(dest="subcmd")

    p = sub.add_parser("list", help="List receipts/invoices")
    p.add_argument("--since", required=True, help="Start: today, yesterday, 7d, YYYY-MM-DD")
    p.add_argument("--until", default=None, help="End date")
    p.add_argument("--type", default=None, dest="doc_type",
                   help="Document type filter (FT, FS, FR, etc.)")
    p.add_argument("--store", type=int, default=None)
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("show", help="Show receipt detail")
    p.add_argument("id", type=int, help="Document ID")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("search", help="Search receipts by client name")
    p.add_argument("--client", required=True, help="Client name to search")
    p.add_argument("--since", default="30d", help="Start (default: 30d)")
    p.add_argument("--until", default=None)
    p.set_defaults(func=cmd_search)


def cmd_list(
    args: argparse.Namespace,
    session: requests.Session,
) -> dict[str, Any]:
    since, until = resolve_since_until(args.since, args.until)
    doc_types = args.doc_type or "FT,FS,FR"
    docs = fetch_documents(session, since, until, doc_types=doc_types,
                           store_id=args.store)

    receipts = [
        {
            "id": d["id"],
            "number": d.get("number", ""),
            "date": d.get("date", ""),
            "time": (d.get("local_time") or "")[11:16],
            "type": d.get("type", ""),
            "gross": doc_gross(d),
            "status": d.get("payment_status", d.get("status", "")),
        }
        for d in docs
    ]

    return {
        "period": {"since": since, "until": until},
        "count": len(receipts),
        "receipts": receipts,
    }


def cmd_show(
    args: argparse.Namespace,
    session: requests.Session,
) -> dict[str, Any]:
    doc = fetch_document_detail(session, args.id)
    if doc is None:
        return {"error": f"Document {args.id} not found."}
    return doc


def cmd_search(
    args: argparse.Namespace,
    session: requests.Session,
) -> dict[str, Any]:
    since, until = resolve_since_until(args.since, args.until)

    # Fetch all docs in range, then filter by client name
    docs = fetch_documents(session, since, until, detailed=False)
    needle = args.client.lower()

    matches = []
    for d in docs:
        client = d.get("client") or {}
        client_name = client.get("name", "") if isinstance(client, dict) else ""
        if needle in client_name.lower():
            matches.append({
                "id": d["id"],
                "number": d.get("number", ""),
                "date": d.get("date", ""),
                "client": client_name,
                "gross": doc_gross(d),
            })

    return {
        "query": args.client,
        "period": {"since": since, "until": until},
        "count": len(matches),
        "receipts": matches,
    }
