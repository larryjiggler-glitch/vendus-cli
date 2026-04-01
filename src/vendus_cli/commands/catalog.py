"""Catalog commands: product lookup, search, browse by category."""

import argparse
from typing import Any

import requests

from vendus_cli.api import (
    fetch_categories,
    fetch_product_detail,
    fetch_products,
    resolve_category,
)


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register catalog subcommands."""
    parser = subparsers.add_parser("catalog", help="Product catalog")
    sub = parser.add_subparsers(dest="subcmd")

    p = sub.add_parser("list", help="List all products")
    p.add_argument("--category", default=None, help="Filter by category name")
    p.add_argument("--status", default=None, choices=["on", "off", "all"],
                   help="Filter by status")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("find", help="Search products by name/reference/barcode")
    p.add_argument("query", help="Search query")
    p.set_defaults(func=cmd_find)

    p = sub.add_parser("show", help="Show product detail")
    p.add_argument("id", type=int, help="Product ID")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("by-category", help="List products in a category")
    p.add_argument("name", help="Category name (fuzzy match)")
    p.set_defaults(func=cmd_by_category)


def _category_not_found(name: str, cats: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "error": f"Category '{name}' not found.",
        "available": [c["title"] for c in cats],
    }


def cmd_list(
    args: argparse.Namespace,
    session: requests.Session,
) -> dict[str, Any]:
    category_id = None
    if args.category:
        cats = fetch_categories(session)
        category_id = resolve_category(cats, args.category)
        if category_id is None:
            return _category_not_found(args.category, cats)
    products = fetch_products(session, category_id=category_id)
    return {"product_count": len(products), "products": products}


def cmd_find(
    args: argparse.Namespace,
    session: requests.Session,
) -> dict[str, Any]:
    products = fetch_products(session, query=args.query)
    return {"query": args.query, "product_count": len(products), "products": products}


def cmd_show(
    args: argparse.Namespace,
    session: requests.Session,
) -> dict[str, Any]:
    product = fetch_product_detail(session, args.id)
    if product is None:
        return {"error": f"Product {args.id} not found."}
    return product


def cmd_by_category(
    args: argparse.Namespace,
    session: requests.Session,
) -> dict[str, Any]:
    cats = fetch_categories(session)
    category_id = resolve_category(cats, args.name)
    if category_id is None:
        return _category_not_found(args.name, cats)
    products = fetch_products(session, category_id=category_id)
    return {
        "category": args.name,
        "category_id": category_id,
        "product_count": len(products),
        "products": products,
    }
