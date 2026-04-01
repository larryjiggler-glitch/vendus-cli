"""Query commands: offline analysis of synced sales data."""

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from vendus_cli.api import doc_gross, doc_net, item_gross, line_items, safe_float
from vendus_cli.dates import bucket_by_interval

DEFAULT_FILE = "./vendus-sales.json"


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register query subcommands."""
    parser = subparsers.add_parser(
        "query", help="Query synced local data (no API calls)",
    )
    sub = parser.add_subparsers(dest="subcmd")

    for name, help_text, func, extra_args in [
        ("summary", "Sales summary", cmd_summary, []),
        ("by-category", "Sales by category", cmd_by_category, [
            ("--category", {"default": None, "help": "Filter by category name"}),
        ]),
        ("by-product", "Sales by product", cmd_by_product, [
            ("--product", {"default": None, "help": "Filter by product name"}),
            ("--top", {"type": int, "default": None, "help": "Limit to top N"}),
        ]),
    ]:
        p = sub.add_parser(name, help=help_text)
        p.add_argument("--file", default=DEFAULT_FILE, help="Synced JSON file")
        p.add_argument(
            "--interval", default=None, choices=["day", "week", "month"],
            help="Bucket results by time interval for trends",
        )
        for arg_name, kwargs in extra_args:
            p.add_argument(arg_name, **kwargs)
        p.set_defaults(func=func)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def _load(path: str) -> dict[str, Any]:
    """Load synced JSON file."""
    p = Path(path)
    if not p.is_file():
        raise ValueError(
            f"Sync file not found: {path}\n"
            f"Run: vendus-pos sync sales --since <date>"
        )
    return json.loads(p.read_text(encoding="utf-8"))


def _product_cat_map(data: dict[str, Any]) -> dict[int, int]:
    """product_id → category_id from synced products."""
    products = data.get("products") or {}
    return {int(k): v.get("category_id", 0) for k, v in products.items()}


def _cat_titles(data: dict[str, Any]) -> dict[int, str]:
    """category_id → title from synced categories."""
    cats = data.get("categories") or {}
    return {int(k): v for k, v in cats.items()}


def _resolve_cat_id(data: dict[str, Any], name: str) -> int | None:
    """Fuzzy-match a category name."""
    needle = name.lower()
    for cid_str, title in (data.get("categories") or {}).items():
        if needle in title.lower():
            return int(cid_str)
    return None


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_summary(
    args: argparse.Namespace,
    _session: Any,
) -> dict[str, Any]:
    data = _load(args.file)
    docs = data.get("transactions") or []

    if not args.interval:
        return {
            "document_count": len(docs),
            "total_gross": round(sum(doc_gross(d) for d in docs), 2),
            "total_net": round(sum(doc_net(d) for d in docs), 2),
        }

    buckets: dict[str, dict[str, float | int]] = defaultdict(
        lambda: {"gross": 0.0, "net": 0.0, "count": 0}
    )
    for d in docs:
        dt = d.get("date", "")
        if dt:
            b = buckets[bucket_by_interval(dt, args.interval)]
            b["gross"] += doc_gross(d)
            b["net"] += doc_net(d)
            b["count"] += 1

    return {
        "interval": args.interval,
        "data": [
            {"period": k, "gross": round(v["gross"], 2), "net": round(v["net"], 2),
             "transactions": v["count"]}
            for k, v in sorted(buckets.items())
        ],
    }


def cmd_by_category(
    args: argparse.Namespace,
    _session: Any,
) -> dict[str, Any]:
    data = _load(args.file)
    docs = data.get("transactions") or []
    pcm = _product_cat_map(data)
    cat_names = _cat_titles(data)

    target = None
    if args.category:
        target = _resolve_cat_id(data, args.category)
        if target is None:
            return {
                "error": f"Category '{args.category}' not found.",
                "available": list(cat_names.values()),
            }

    if args.interval:
        buckets: dict[str, dict[str, float]] = defaultdict(
            lambda: {"qty": 0.0, "gross": 0.0}
        )
        for d in docs:
            dt = d.get("date", "")
            if not dt:
                continue
            label = bucket_by_interval(dt, args.interval)
            for item in line_items(d):
                cat_id = pcm.get(item.get("id") or 0, 0)
                if target and cat_id != target:
                    continue
                if not target and args.category:
                    continue
                buckets[label]["qty"] += safe_float(item.get("qty", 0))
                buckets[label]["gross"] += item_gross(item)

        result: dict[str, Any] = {
            "interval": args.interval,
            "data": [
                {"period": k, "qty": round(v["qty"], 2), "gross": round(v["gross"], 2)}
                for k, v in sorted(buckets.items())
            ],
        }
        if args.category:
            result["filter"] = args.category
        return result

    # No interval — aggregate totals
    totals: dict[int, dict[str, float]] = defaultdict(lambda: {"qty": 0.0, "gross": 0.0})
    for d in docs:
        for item in line_items(d):
            cat_id = pcm.get(item.get("id") or 0, 0)
            if target and cat_id != target:
                continue
            totals[cat_id]["qty"] += safe_float(item.get("qty", 0))
            totals[cat_id]["gross"] += item_gross(item)

    return {
        "categories": sorted(
            [
                {
                    "category_id": cid,
                    "category": cat_names.get(cid, f"Unknown ({cid})"),
                    "qty": round(v["qty"], 2),
                    "gross": round(v["gross"], 2),
                }
                for cid, v in totals.items()
            ],
            key=lambda x: -x["gross"],
        ),
    }


def cmd_by_product(
    args: argparse.Namespace,
    _session: Any,
) -> dict[str, Any]:
    data = _load(args.file)
    docs = data.get("transactions") or []
    needle = args.product.lower() if args.product else None

    if args.interval:
        buckets: dict[str, dict[int, dict[str, Any]]] = defaultdict(
            lambda: defaultdict(lambda: {"title": "", "qty": 0.0, "gross": 0.0})
        )
        for d in docs:
            dt = d.get("date", "")
            if not dt:
                continue
            label = bucket_by_interval(dt, args.interval)
            for item in line_items(d):
                pid = item.get("id") or 0
                title = item.get("title", "")
                if needle and needle not in title.lower():
                    continue
                b = buckets[label][pid]
                b["title"] = title
                b["qty"] += safe_float(item.get("qty", 0))
                b["gross"] += item_gross(item)

        if needle:
            return {
                "interval": args.interval,
                "filter": args.product,
                "data": [
                    {
                        "period": label,
                        "qty": round(sum(p["qty"] for p in prods.values()), 2),
                        "gross": round(sum(p["gross"] for p in prods.values()), 2),
                    }
                    for label, prods in sorted(buckets.items())
                ],
            }

        rows = []
        for label in sorted(buckets):
            ranked = sorted(buckets[label].items(), key=lambda x: -x[1]["qty"])
            if args.top:
                ranked = ranked[:args.top]
            for pid, v in ranked:
                rows.append({
                    "period": label, "product_id": pid, "title": v["title"],
                    "qty": round(v["qty"], 2), "gross": round(v["gross"], 2),
                })
        return {"interval": args.interval, "data": rows}

    # No interval
    totals: dict[int, dict[str, Any]] = defaultdict(
        lambda: {"title": "", "qty": 0.0, "gross": 0.0}
    )
    for d in docs:
        for item in line_items(d):
            pid = item.get("id") or 0
            title = item.get("title", "")
            if needle and needle not in title.lower():
                continue
            if not totals[pid]["title"]:
                totals[pid]["title"] = title
            totals[pid]["qty"] += safe_float(item.get("qty", 0))
            totals[pid]["gross"] += item_gross(item)

    ranked = sorted(totals.items(), key=lambda x: -x[1]["qty"])
    if args.top:
        ranked = ranked[:args.top]

    return {
        "products": [
            {"product_id": pid, "title": v["title"],
             "qty": round(v["qty"], 2), "gross": round(v["gross"], 2)}
            for pid, v in ranked
        ],
    }
