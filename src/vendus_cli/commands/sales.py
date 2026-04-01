"""Sales commands: summary, by-hour, by-product, by-category, compare, stats."""

import argparse
from collections import defaultdict
from typing import Any

import requests

from vendus_cli.api import (
    build_product_category_map,
    doc_gross,
    doc_net,
    fetch_categories,
    fetch_documents,
    item_gross,
    line_items,
    safe_float,
)
from vendus_cli.dates import resolve_since_until


def _add_date_args(parser: argparse.ArgumentParser) -> None:
    """Add common --since/--until/--store/--register args."""
    parser.add_argument("--since", required=True, help="Start: today, yesterday, 7d, YYYY-MM-DD")
    parser.add_argument("--until", default=None, help="End: today, YYYY-MM-DD (default: auto)")
    parser.add_argument("--store", type=int, default=None, help="Filter by store ID")
    parser.add_argument("--register", type=int, default=None, help="Filter by register ID")


def _resolve_dates(args: argparse.Namespace) -> tuple[str, str]:
    return resolve_since_until(args.since, args.until)


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register sales subcommands."""
    parser = subparsers.add_parser("sales", help="Sales data and analytics")
    sub = parser.add_subparsers(dest="subcmd")

    p = sub.add_parser("summary", help="Sales totals for a period")
    _add_date_args(p)
    p.set_defaults(func=cmd_summary)

    p = sub.add_parser("by-hour", help="Hourly sales breakdown")
    p.add_argument("--date", required=True, help="Date: today, yesterday, YYYY-MM-DD")
    p.add_argument("--store", type=int, default=None)
    p.add_argument("--register", type=int, default=None)
    p.set_defaults(func=cmd_by_hour)

    p = sub.add_parser("by-product", help="Sales by product")
    _add_date_args(p)
    p.add_argument("--product", default=None, help="Filter by product name (fuzzy)")
    p.add_argument("--top", type=int, default=None, help="Limit to top N")
    p.set_defaults(func=cmd_by_product)

    p = sub.add_parser("by-category", help="Sales by category")
    _add_date_args(p)
    p.add_argument("--category", default=None, help="Filter by category name")
    p.set_defaults(func=cmd_by_category)

    p = sub.add_parser("compare", help="Compare two periods")
    p.add_argument("--a", required=True, dest="period_a", help="Period A (e.g. yesterday)")
    p.add_argument("--b", required=True, dest="period_b", help="Period B (e.g. last-same-weekday)")
    p.add_argument("--store", type=int, default=None)
    p.set_defaults(func=cmd_compare)

    p = sub.add_parser("stats", help="ATV and items-per-ticket")
    _add_date_args(p)
    p.set_defaults(func=cmd_stats)


# ---------------------------------------------------------------------------
# Aggregation helpers
# ---------------------------------------------------------------------------


def _aggregate_summary(docs: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate documents into a sales summary."""
    total_gross = 0.0
    total_net = 0.0
    by_type: dict[str, dict[str, Any]] = defaultdict(lambda: {"count": 0, "gross": 0.0})

    for d in docs:
        gross = doc_gross(d)
        net = doc_net(d)
        total_gross += gross
        total_net += net
        dtype = d.get("type", "??")
        by_type[dtype]["count"] += 1
        by_type[dtype]["gross"] += gross

    return {
        "document_count": len(docs),
        "total_gross": round(total_gross, 2),
        "total_net": round(total_net, 2),
        "by_type": {
            k: {"count": v["count"], "gross": round(v["gross"], 2)}
            for k, v in by_type.items()
        },
    }


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


def cmd_summary(
    args: argparse.Namespace,
    session: requests.Session,
) -> dict[str, Any]:
    since, until = _resolve_dates(args)
    docs = fetch_documents(session, since, until, detailed=False,
                           store_id=args.store, register_id=args.register)
    result = _aggregate_summary(docs)
    result["period"] = {"since": since, "until": until}
    return result


def cmd_by_hour(
    args: argparse.Namespace,
    session: requests.Session,
) -> dict[str, Any]:
    since, until = resolve_since_until(args.date)
    docs = fetch_documents(session, since, until, detailed=False,
                           store_id=args.store, register_id=args.register)

    by_hour: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"count": 0, "gross": 0.0}
    )
    for d in docs:
        # local_time format: "2026-03-30 15:54:23"
        lt = d.get("local_time") or d.get("system_time") or ""
        hour = lt[11:13] if len(lt) >= 13 else "??"
        by_hour[hour]["count"] += 1
        by_hour[hour]["gross"] += doc_gross(d)

    hours = []
    for h in sorted(by_hour.keys()):
        hours.append({
            "hour": f"{h}:00",
            "transactions": by_hour[h]["count"],
            "gross": round(by_hour[h]["gross"], 2),
        })

    return {"date": since, "hours": hours}


def cmd_by_product(
    args: argparse.Namespace,
    session: requests.Session,
) -> dict[str, Any]:
    since, until = _resolve_dates(args)
    docs = fetch_documents(session, since, until, detailed=True,
                           store_id=args.store, register_id=args.register)

    product_totals: dict[Any, dict[str, Any]] = defaultdict(
        lambda: {"title": "", "reference": "", "qty": 0.0, "gross": 0.0}
    )

    needle = args.product.lower() if args.product else None

    for d in docs:
        for item in line_items(d):
            pid = item.get("id") or item.get("product_id") or 0
            title = item.get("title", f"Product {pid}")
            ref = item.get("reference", "")

            if needle:
                if needle not in title.lower() and needle not in ref.lower():
                    continue

            qty = safe_float(item.get("qty", 0))
            gross = item_gross(item)
            if not product_totals[pid]["title"]:
                product_totals[pid]["title"] = title
                product_totals[pid]["reference"] = ref
            product_totals[pid]["qty"] += qty
            product_totals[pid]["gross"] += gross

    ranked = sorted(product_totals.items(), key=lambda x: -x[1]["qty"])
    if args.top:
        ranked = ranked[:args.top]

    products = [
        {
            "product_id": pid,
            "title": data["title"],
            "reference": data["reference"],
            "total_qty": round(data["qty"], 2),
            "total_gross": round(data["gross"], 2),
        }
        for pid, data in ranked
    ]

    result: dict[str, Any] = {
        "period": {"since": since, "until": until},
        "products": products,
    }
    if args.product:
        result["filter"] = args.product
    return result


def cmd_by_category(
    args: argparse.Namespace,
    session: requests.Session,
) -> dict[str, Any]:
    since, until = _resolve_dates(args)
    cats = fetch_categories(session)
    cat_map = {c["id"]: c["title"] for c in cats}
    product_cat_map = build_product_category_map(session)
    docs = fetch_documents(session, since, until, detailed=True,
                           store_id=args.store, register_id=args.register)

    # Optionally filter by category
    target_cat_id = None
    if args.category:
        needle = args.category.lower()
        for c in cats:
            if needle in c.get("title", "").lower():
                target_cat_id = c["id"]
                break
        if target_cat_id is None:
            return {
                "error": f"Category '{args.category}' not found.",
                "available": [c["title"] for c in cats],
            }

    cat_totals: dict[int, dict[str, Any]] = defaultdict(
        lambda: {"title": "", "qty": 0.0, "gross": 0.0}
    )
    for d in docs:
        for item in line_items(d):
            pid = item.get("id") or 0
            cat_id = product_cat_map.get(pid, 0)
            if target_cat_id and cat_id != target_cat_id:
                continue
            cat_totals[cat_id]["title"] = cat_map.get(cat_id, f"Unknown ({cat_id})")
            cat_totals[cat_id]["qty"] += safe_float(item.get("qty", 0))
            cat_totals[cat_id]["gross"] += item_gross(item)

    categories = sorted(
        [
            {
                "category_id": cid,
                "category": data["title"],
                "total_qty": round(data["qty"], 2),
                "total_gross": round(data["gross"], 2),
            }
            for cid, data in cat_totals.items()
        ],
        key=lambda x: -x["total_gross"],
    )

    return {
        "period": {"since": since, "until": until},
        "categories": categories,
    }


def cmd_compare(
    args: argparse.Namespace,
    session: requests.Session,
) -> dict[str, Any]:
    since_a, until_a = resolve_since_until(args.period_a)
    since_b, until_b = resolve_since_until(args.period_b)

    docs_a = fetch_documents(session, since_a, until_a, detailed=False,
                             store_id=args.store)
    docs_b = fetch_documents(session, since_b, until_b, detailed=False,
                             store_id=args.store)

    summary_a = _aggregate_summary(docs_a)
    summary_b = _aggregate_summary(docs_b)

    gross_a = summary_a["total_gross"]
    gross_b = summary_b["total_gross"]
    delta = round(gross_a - gross_b, 2)
    pct = round((delta / gross_b) * 100, 1) if gross_b else 0

    return {
        "period_a": {"since": since_a, "until": until_a, **summary_a},
        "period_b": {"since": since_b, "until": until_b, **summary_b},
        "delta_gross": delta,
        "delta_pct": pct,
    }


def cmd_stats(
    args: argparse.Namespace,
    session: requests.Session,
) -> dict[str, Any]:
    since, until = _resolve_dates(args)
    docs = fetch_documents(session, since, until, detailed=True,
                           store_id=args.store, register_id=args.register)
    doc_count = len(docs)
    total_gross = sum(doc_gross(d) for d in docs)
    total_items = sum(
        safe_float(item.get("qty", 0))
        for d in docs for item in line_items(d)
    )

    return {
        "document_count": doc_count,
        "total_gross": round(total_gross, 2),
        "total_items": round(total_items, 2),
        "avg_transaction_value": round(total_gross / doc_count, 2) if doc_count else 0,
        "avg_items_per_ticket": round(total_items / doc_count, 2) if doc_count else 0,
        "period": {"since": since, "until": until},
    }
