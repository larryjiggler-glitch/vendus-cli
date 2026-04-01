---
description: Query Vendus POS data — sales, payments, catalog, receipts
---

Run `vendus-pos` CLI commands to answer POS questions. See SKILL.md for the full command reference.

Quick examples:
- `vendus-pos sales summary --since today`
- `vendus-pos sales by-hour --date yesterday`
- `vendus-pos catalog find "cappuccino"`
- `vendus-pos payments mix --since this-week`
- `vendus-pos --format table sales by-product --since 7d --top 5`
