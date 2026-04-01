"""Inspect commands: rate-limit, auth verification."""

import argparse
from typing import Any

import requests

from vendus_cli.api import fetch_categories, fetch_rate_limit


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register inspect subcommands."""
    parser = subparsers.add_parser("inspect", help="API diagnostics")
    sub = parser.add_subparsers(dest="subcmd")

    p = sub.add_parser("rate-limit", help="Check API rate limit status")
    p.set_defaults(func=cmd_rate_limit)

    p = sub.add_parser("auth", help="Verify API credentials")
    p.set_defaults(func=cmd_auth)


def cmd_rate_limit(
    args: argparse.Namespace,
    session: requests.Session,
) -> dict[str, Any]:
    return fetch_rate_limit(session)


def cmd_auth(
    args: argparse.Namespace,
    session: requests.Session,
) -> dict[str, Any]:
    try:
        cats = fetch_categories(session)
        return {
            "status": "ok",
            "message": f"Authenticated. {len(cats)} categories accessible.",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }
