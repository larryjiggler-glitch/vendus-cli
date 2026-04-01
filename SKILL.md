---
name: vendus-cli
description: "Query Cegid Vendus POS data — sales, payments, catalog, receipts. Use when the user asks about sales figures, revenue, bestsellers, product performance, sales comparisons, hourly breakdown, payment methods, ATV, items per ticket, or invoicing data. Triggers on: Vendus, invoices, fatura, POS, sales questions, cafe/store analytics, payment mix."
---

# Vendus POS CLI

Task-oriented CLI for Cegid Vendus POS operations.

## Setup

```bash
pip install vendus-cli   # or: uv pip install vendus-cli
```

If running from the skill directory venv (OpenClaw/Manus):

```bash
VENDUS="$HOME/.openclaw/workspace/skills/vendus-cli/.venv/bin/vendus-pos"
```

Set credentials in environment or `.env` file:

```
VENDUS_API_KEY=your_key
VENDUS_USERNAME=admin
```

## Date Aliases (built-in)

All `--since` / `--until` args accept:

`today`, `yesterday`, `7d`, `30d`, `90d`, `this-week`, `last-week`, `this-month`, `last-month`, `last-same-weekday`, `YYYY-MM-DD`

## Output Formats

All commands accept `--format json|table|md` (default: json). Flag works in any position.

## Command Reference

### Sales

```bash
vendus-pos sales summary --since today
vendus-pos sales by-hour --since yesterday
vendus-pos sales by-product --since 7d --top 5
vendus-pos sales by-product --since 7d --product "egg"
vendus-pos sales by-category --since this-month
vendus-pos sales by-category --since 30d --category Matcha
vendus-pos sales compare --a yesterday --b last-same-weekday
vendus-pos sales stats --since today
```

### Receipts

```bash
vendus-pos receipts list --since today
vendus-pos receipts list --since this-week --type FT
vendus-pos receipts show 326732206
vendus-pos receipts search --client "Maria" --since 30d
```

### Catalog

```bash
vendus-pos catalog list
vendus-pos catalog find "cappuccino"
vendus-pos catalog show 295673194
vendus-pos catalog by-category "Matcha"
```

### Payments

```bash
vendus-pos payments summary --since today
vendus-pos payments mix --since this-week
```

### Meta

```bash
vendus-pos categories list
vendus-pos stores list
vendus-pos registers list
```

### Sync & Query (offline — for trends and large date ranges)

```bash
# Step 1: Sync data locally (one-time, ~3min for 3 months)
vendus-pos sync sales --since 2026-01-01 --until today --output sales.json

# Step 2: Query instantly from the local file (no API calls)
vendus-pos query summary --file sales.json --interval month
vendus-pos query by-category --file sales.json --category Beans --interval month
vendus-pos query by-product --file sales.json --product "Cappuccino" --interval week
vendus-pos query by-product --file sales.json --top 5 --interval month
```

**IMPORTANT:** For any query spanning >1 month with category/product filters, always use sync→query instead of the live `sales by-category` command. The live command fetches every document individually (~60s per month). The query command reads a local file (~0.15s).

### Inspect

```bash
vendus-pos inspect auth
vendus-pos inspect rate-limit
```

## Answering Common Questions

### "How much did we sell yesterday?"

```bash
vendus-pos sales summary --since yesterday
```

### "Compare this Sunday to last Sunday"

```bash
vendus-pos sales compare --a yesterday --b last-same-weekday
```

### "Top 3 bestsellers this week?"

```bash
vendus-pos sales by-product --since this-week --top 3
```

### "Hourly breakdown today?"

```bash
vendus-pos --format table sales by-hour --since today
```

### "Payment split this week?"

```bash
vendus-pos --format table payments mix --since this-week
```

### "What's our ATV?"

```bash
vendus-pos sales stats --since this-week
```

### "Show me beans sales trend this year" (or any category/product trend)

Use sync→query (NOT the live `sales by-category` which is too slow for multi-month):

```bash
vendus-pos sync sales --since 2026-01-01 --until today --output /tmp/vendus-sales.json
vendus-pos --format table query by-category --file /tmp/vendus-sales.json --category Beans --interval month
```

For product trends:

```bash
vendus-pos query by-product --file /tmp/vendus-sales.json --product "Cappuccino" --interval month
```

## Response Style

Always convert output into a clear conversational answer with actual numbers. Never dump raw JSON to the user.

## Technical Notes

- Sales queries filter to `FT`/`FS`/`FR` documents only (excludes receipts, credit notes).
- `status=N` excludes cancelled documents.
- Line-item queries (by-product, by-category, stats, payments) fetch each document individually — ~60s per month.
- For queries spanning >1 month with filters, use `sync` + `query` instead (sync once, query instant).
- All monetary values are EUR.
- Auth: API key as query parameter.
