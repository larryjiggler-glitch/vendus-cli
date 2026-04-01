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
vendus-pos sales by-hour --date yesterday
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

### Sync & Inspect

```bash
vendus-pos sync sales --since yesterday --output sales.json
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
vendus-pos --format table sales by-hour --date today
```

### "Payment split this week?"

```bash
vendus-pos --format table payments mix --since this-week
```

### "What's our ATV?"

```bash
vendus-pos sales stats --since this-week
```

## Response Style

Always convert output into a clear conversational answer with actual numbers. Never dump raw JSON to the user.

## Technical Notes

- Sales queries filter to `FT`/`FS`/`FR` documents only (excludes receipts, credit notes).
- `status=N` excludes cancelled documents.
- Line-item queries (by-product, by-category, stats, payments) fetch each document individually.
- All monetary values are EUR.
- Auth: API key as query parameter.
