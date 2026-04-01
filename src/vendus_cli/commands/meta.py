"""Meta commands: categories, stores, registers."""

import argparse
from typing import Any

import requests

from vendus_cli.api import fetch_categories, fetch_registers, fetch_stores


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register meta commands as top-level command groups."""
    # pos categories list
    cat_parser = subparsers.add_parser("categories", help="Product categories")
    cat_sub = cat_parser.add_subparsers(dest="subcmd")
    p = cat_sub.add_parser("list", help="List all categories")
    p.set_defaults(func=cmd_categories_list)

    # pos stores list
    store_parser = subparsers.add_parser("stores", help="Store locations")
    store_sub = store_parser.add_subparsers(dest="subcmd")
    p = store_sub.add_parser("list", help="List all stores")
    p.set_defaults(func=cmd_stores_list)

    # pos registers list
    reg_parser = subparsers.add_parser("registers", help="POS registers")
    reg_sub = reg_parser.add_subparsers(dest="subcmd")
    p = reg_sub.add_parser("list", help="List all registers")
    p.set_defaults(func=cmd_registers_list)


def cmd_categories_list(
    args: argparse.Namespace,
    session: requests.Session,
) -> dict[str, Any]:
    cats = fetch_categories(session)
    return {"categories": cats}


def cmd_stores_list(
    args: argparse.Namespace,
    session: requests.Session,
) -> dict[str, Any]:
    stores = fetch_stores(session)
    return {"stores": stores}


def cmd_registers_list(
    args: argparse.Namespace,
    session: requests.Session,
) -> dict[str, Any]:
    registers = fetch_registers(session)
    return {"registers": registers}
