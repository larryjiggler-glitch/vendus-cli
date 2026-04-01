"""Vendus API client — credentials, session, pagination, field helpers."""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = "https://www.vendus.pt/ws/v1.1"
DEFAULT_PER_PAGE = 100
SALES_DOC_TYPES = "FT,FS,FR"

log = logging.getLogger("pos")

# ---------------------------------------------------------------------------
# Credentials
# ---------------------------------------------------------------------------


def _load_secrets_file() -> dict[str, str]:
    """Parse KEY=VALUE lines from first .env or .secrets file found.

    Handles both ``KEY=value`` and ``export KEY=value`` formats.
    """
    secrets: dict[str, str] = {}
    candidates = [
        Path(".env"),
        Path(".secrets"),
        Path.home() / ".env",
        Path.home() / ".secrets",
    ]
    for p in candidates:
        if p.is_file():
            for line in p.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, value = line.partition("=")
                    key = key.strip()
                    if key.startswith("export "):
                        key = key[7:].strip()
                    secrets[key] = value.strip().strip("'\"")
            break
    return secrets


def get_credentials() -> tuple[str, str]:
    """Return (username, api_key). Tries env vars, then .secrets."""
    username = os.environ.get("VENDUS_USERNAME")
    api_key = os.environ.get("VENDUS_API_KEY")

    if not api_key:
        secrets = _load_secrets_file()
        api_key = secrets.get("VENDUS_API_KEY", "")
        username = username or secrets.get("VENDUS_USERNAME", "admin")

    if not api_key:
        print(json.dumps({
            "error": "VENDUS_API_KEY not found. "
                     "Set it in environment or ~/.secrets file:\n"
                     "  VENDUS_API_KEY=your_key\n"
                     "  VENDUS_USERNAME=admin  (optional, defaults to 'admin')"
        }))
        sys.exit(1)

    return (username or "admin", api_key)


def make_session(username: str, api_key: str) -> requests.Session:
    """Create a session with the API key as a default query parameter."""
    session = requests.Session()
    session.params = {"api_key": api_key}  # type: ignore[assignment]
    session.headers.update({"Accept": "application/json"})
    return session


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


def _fetch_page(
    session: requests.Session,
    url: str,
    params: dict[str, Any],
) -> list[dict[str, Any]] | None:
    """Fetch one page. Retries once on 5xx. Returns None on failure."""
    for attempt in range(2):
        try:
            resp = session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict):
                return [data]
            return data
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else 0
            if status >= 500 and attempt == 0:
                log.warning("HTTP %s on page %s — retrying", status, params.get("page"))
                continue
            log.error("HTTP %s on page %s — giving up", status, params.get("page"))
            return None
        except requests.RequestException as exc:
            log.error("Request error: %s", exc)
            return None
    return None


def fetch_all(
    session: requests.Session,
    endpoint: str,
    params: dict[str, Any] | None = None,
    per_page: int = DEFAULT_PER_PAGE,
) -> list[dict[str, Any]]:
    """Paginate through all pages. Stops when page returns < per_page items."""
    url = f"{BASE_URL}/{endpoint.strip('/')}/"
    params = dict(params or {})
    results: list[dict[str, Any]] = []
    page = 1

    while True:
        params["page"] = page
        params["per_page"] = per_page

        items = _fetch_page(session, url, params)
        if items is None:
            if results:
                log.warning(
                    "Partial fetch: %d items before page %d failed.",
                    len(results), page,
                )
            break

        results.extend(items)
        if len(items) < per_page:
            break
        page += 1

    return results


def deduplicate(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove duplicate IDs, keep first occurrence."""
    seen: set[Any] = set()
    result: list[dict[str, Any]] = []
    for item in items:
        item_id = item.get("id")
        if item_id not in seen:
            seen.add(item_id)
            result.append(item)
        else:
            log.warning("Duplicate ID %s dropped", item_id)
    return result


# ---------------------------------------------------------------------------
# Data fetchers
# ---------------------------------------------------------------------------


def fetch_categories(session: requests.Session) -> list[dict[str, Any]]:
    """Fetch all product categories."""
    cats = fetch_all(session, "products/categories", per_page=500)
    return [{"id": c["id"], "title": c.get("title", "")} for c in cats]


def fetch_products(
    session: requests.Session,
    category_id: int | None = None,
    query: str | None = None,
) -> list[dict[str, Any]]:
    """Fetch products, optionally filtered by category or search query."""
    params: dict[str, Any] = {}
    if category_id:
        params["category_id"] = category_id
    if query:
        params["q"] = query
    return fetch_all(session, "products", params)


def fetch_product_detail(
    session: requests.Session,
    product_id: int,
) -> dict[str, Any] | None:
    """Fetch a single product by ID."""
    url = f"{BASE_URL}/products/{product_id}/"
    try:
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        log.warning("Failed to fetch product %s: %s", product_id, exc)
        return None


def fetch_document_detail(
    session: requests.Session,
    doc_id: int,
) -> dict[str, Any] | None:
    """Fetch a single document by ID (includes line items)."""
    url = f"{BASE_URL}/documents/{doc_id}/"
    try:
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        log.warning("Failed to fetch document %s: %s", doc_id, exc)
        return None


def fetch_documents(
    session: requests.Session,
    since: str,
    until: str,
    doc_types: str = SALES_DOC_TYPES,
    detailed: bool = False,
    store_id: int | None = None,
    register_id: int | None = None,
    status: str = "N",
) -> list[dict[str, Any]]:
    """Fetch documents for a date range.

    When detailed=True, fetches each document individually to include
    line items (the list endpoint does not return them).
    """
    params: dict[str, Any] = {
        "type": doc_types,
        "since": since,
        "until": until,
        "status": status,
    }
    if store_id:
        params["store_id"] = store_id
    if register_id:
        params["register_id"] = register_id

    docs = fetch_all(session, "documents", params)
    docs = deduplicate(docs)

    if not detailed or not docs:
        return docs

    log.info("Fetching line items for %d documents...", len(docs))
    detailed_docs: list[dict[str, Any]] = []
    for doc in docs:
        detail = fetch_document_detail(session, doc["id"])
        if detail:
            detailed_docs.append(detail)
    return detailed_docs


def fetch_stores(session: requests.Session) -> list[dict[str, Any]]:
    """Fetch all stores."""
    return fetch_all(session, "stores", per_page=500)


def fetch_registers(session: requests.Session) -> list[dict[str, Any]]:
    """Fetch all registers."""
    return fetch_all(session, "registers", per_page=500)


def fetch_payment_methods(session: requests.Session) -> list[dict[str, Any]]:
    """Fetch all payment methods."""
    return fetch_all(session, "documents/paymentmethods", per_page=500)


def fetch_clients(
    session: requests.Session,
    query: str | None = None,
) -> list[dict[str, Any]]:
    """Fetch clients, optionally filtered by search query."""
    params: dict[str, Any] = {}
    if query:
        params["q"] = query
    return fetch_all(session, "clients", params)


def fetch_rate_limit(session: requests.Session) -> dict[str, Any]:
    """Check current rate limit status via a lightweight request."""
    url = f"{BASE_URL}/products/categories/"
    resp = session.get(url, params={"per_page": 1, "page": 1}, timeout=30)
    return {
        "status_code": resp.status_code,
        "rate_limit_limit": resp.headers.get("Rate-Limit-Limit", "unknown"),
        "rate_limit_remaining": resp.headers.get("Rate-Limit-Remaining", "unknown"),
        "rate_limit_used": resp.headers.get("Rate-Limit-Used", "unknown"),
        "rate_limit_reset": resp.headers.get("Rate-Limit-Reset", "unknown"),
    }


# ---------------------------------------------------------------------------
# Field-access helpers
# ---------------------------------------------------------------------------


def safe_float(val: Any) -> float:
    """Safely convert a value to float, defaulting to 0.0."""
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


def doc_gross(doc: dict[str, Any]) -> float:
    """Extract gross amount from a document."""
    return safe_float(doc.get("amount_gross") or doc.get("total") or 0)


def doc_net(doc: dict[str, Any]) -> float:
    """Extract net amount from a document."""
    return safe_float(doc.get("amount_net") or 0)


def line_items(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract line items from a document."""
    return doc.get("items") or doc.get("lines") or []


def item_gross(item: dict[str, Any]) -> float:
    """Extract gross total from a line item."""
    amounts = item.get("amounts")
    if amounts:
        return safe_float(amounts.get("gross_total", 0))
    return safe_float(item.get("total") or item.get("price", 0))


def build_product_category_map(
    session: requests.Session,
) -> dict[int, int]:
    """Build product_id → category_id mapping from the products endpoint."""
    products = fetch_all(session, "products", per_page=500)
    return {p["id"]: p.get("category_id", 0) for p in products}
