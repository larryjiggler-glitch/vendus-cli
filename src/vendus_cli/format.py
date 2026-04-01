"""Output formatting for the POS CLI: json, table, md."""

import json
from typing import Any


def output(data: Any, fmt: str = "json") -> str:
    """Format data for display. Returns a string."""
    if fmt == "json":
        return json.dumps(data, indent=2, ensure_ascii=False)
    rows, columns = _extract_rows(data)
    if fmt == "table":
        return _render_table(rows, columns)
    if fmt == "md":
        return _render_markdown(rows, columns)
    return json.dumps(data, indent=2, ensure_ascii=False)


def _extract_rows(data: Any) -> tuple[list[dict[str, Any]], list[str]]:
    """Normalize various data shapes into a list of row dicts + column names."""
    # Empty list
    if isinstance(data, list) and not data:
        return [], []

    # List of dicts → direct table (derive columns from all rows)
    if isinstance(data, list) and data and isinstance(data[0], dict):
        seen: dict[str, None] = {}
        for row in data:
            for k in row:
                seen.setdefault(k, None)
        return data, list(seen)

    # Dict with a single list-valued key → extract the list
    if isinstance(data, dict):
        list_keys = [k for k, v in data.items() if isinstance(v, list) and v]
        if len(list_keys) == 1:
            rows = data[list_keys[0]]
            if rows and isinstance(rows[0], dict):
                seen_cols: dict[str, None] = {}
                for row in rows:
                    for k in row:
                        seen_cols.setdefault(k, None)
                return rows, list(seen_cols)

        # Flat dict → key/value table
        rows = [{"field": k, "value": v} for k, v in data.items()
                if not isinstance(v, (dict, list))]
        if rows:
            return rows, ["field", "value"]

    # Fallback
    return [{"data": str(data)}], ["data"]


def _render_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    """Render an ASCII table with auto-sized columns."""
    if not rows:
        return "(no data)"

    # Compute column widths
    widths: dict[str, int] = {}
    for col in columns:
        widths[col] = len(col)
        for row in rows:
            val = str(row.get(col, ""))
            widths[col] = max(widths[col], len(val))

    # Header
    header = "  ".join(col.ljust(widths[col]) for col in columns)
    separator = "  ".join("-" * widths[col] for col in columns)

    # Rows
    lines = [header, separator]
    for row in rows:
        line = "  ".join(str(row.get(col, "")).ljust(widths[col]) for col in columns)
        lines.append(line)

    return "\n".join(lines)


def _render_markdown(rows: list[dict[str, Any]], columns: list[str]) -> str:
    """Render a Markdown table."""
    if not rows:
        return "(no data)"

    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"

    lines = [header, separator]
    for row in rows:
        line = "| " + " | ".join(str(row.get(col, "")) for col in columns) + " |"
        lines.append(line)

    return "\n".join(lines)
