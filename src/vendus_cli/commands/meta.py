"""Meta commands: categories, stores, registers."""

import argparse
from typing import Any

import requests

from vendus_cli.api import fetch_categories, fetch_registers, fetch_stores

_META_COMMANDS = {
    "categories": ("Product categories", "categories", fetch_categories),
    "stores": ("Store locations", "stores", fetch_stores),
    "registers": ("POS registers", "registers", fetch_registers),
}


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register meta commands as top-level command groups."""
    for cmd_name, (help_text, key, fetcher) in _META_COMMANDS.items():
        parser = subparsers.add_parser(cmd_name, help=help_text)
        sub = parser.add_subparsers(dest="subcmd")
        p = sub.add_parser("list", help=f"List all {cmd_name}")
        p.set_defaults(func=_make_handler(key, fetcher))


def _make_handler(
    key: str,
    fetcher: Any,
) -> Any:
    """Create a command handler that fetches and wraps results."""
    def handler(_args: argparse.Namespace, session: requests.Session) -> dict[str, Any]:
        return {key: fetcher(session)}
    return handler
