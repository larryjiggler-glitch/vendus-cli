# vendus-cli

Task-oriented CLI for [Cegid Vendus](https://www.vendus.pt/) POS systems. Query sales, payments, catalog, and receipts from the command line or through AI agent platforms.

Built for operators, not API wrappers. Ask *what sold*, *when*, *how paid* — not "GET /documents".

## Install

```bash
pip install vendus-cli
# or
uv pip install vendus-cli
```

## Quick Start

1. Get your API key from your Vendus account settings.

2. Set credentials (choose one):

```bash
# Option A: .env file in your project
echo "VENDUS_API_KEY=your_key" > .env

# Option B: environment variable
export VENDUS_API_KEY=your_key
```

3. Run:

```bash
vendus-pos sales summary --since today
vendus-pos sales by-hour --date yesterday
vendus-pos catalog find "cappuccino"
vendus-pos payments mix --since this-week
```

## Commands

### Sales

```bash
vendus-pos sales summary --since today              # Total gross, net, doc count
vendus-pos sales by-hour --date yesterday            # Hourly breakdown
vendus-pos sales by-product --since 7d --top 5       # Top products by qty
vendus-pos sales by-product --since 7d --product egg # Single product
vendus-pos sales by-category --since this-month      # All categories ranked
vendus-pos sales compare --a yesterday --b last-same-weekday
vendus-pos sales stats --since today                 # ATV + items/ticket
```

### Receipts

```bash
vendus-pos receipts list --since today               # Today's invoices
vendus-pos receipts show 326732206                   # Single receipt detail
vendus-pos receipts search --client "Maria" --since 30d
```

### Catalog

```bash
vendus-pos catalog list                              # All products
vendus-pos catalog find "flat white"                 # Search
vendus-pos catalog show 295673194                    # Product detail
vendus-pos catalog by-category "Matcha"              # By category
```

### Payments

```bash
vendus-pos payments summary --since today            # Totals by method
vendus-pos payments mix --since this-week            # % distribution
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

## Date Aliases

All `--since` / `--until` arguments accept:

| Alias | Resolves to |
|-------|-------------|
| `today` | Today |
| `yesterday` | Yesterday |
| `7d`, `30d`, `90d` | N days ago to today |
| `this-week` | Monday to today |
| `last-week` | Last Monday to last Sunday |
| `this-month` | 1st of month to today |
| `last-month` | Full previous month |
| `last-same-weekday` | Same weekday last week |
| `YYYY-MM-DD` | Specific date |

## Output Formats

```bash
vendus-pos --format json sales summary --since today   # JSON (default)
vendus-pos --format table sales by-hour --date today   # ASCII table
vendus-pos --format md categories list                 # Markdown table
```

`--format` works in any position in the command.

## Credentials

The CLI looks for credentials in this order:

1. Environment variables: `VENDUS_API_KEY`, `VENDUS_USERNAME`
2. `.env` file (current directory, then home directory)
3. `.secrets` file (current directory, then home directory)

`VENDUS_USERNAME` defaults to `admin` if not set.

## Agent Platform Installation

### Claude Code

```bash
# Clone into your project or globally
git clone https://github.com/larryjiggler-glitch/vendus-cli
cd vendus-cli && pip install -e .
```

Claude Code reads the `SKILL.md` and `CLAUDE.md` files for context. The `/vendus-pos` slash command is available when the repo is in your project.

### OpenClaw

```bash
git clone https://github.com/larryjiggler-glitch/vendus-cli ~/.openclaw/workspace/skills/vendus-cli
cd ~/.openclaw/workspace/skills/vendus-cli && pip install -e .
```

The `SKILL.md` is auto-discovered by OpenClaw's skill registry.

### Manus

```bash
git clone https://github.com/larryjiggler-glitch/vendus-cli /mnt/skills/vendus-cli
cd /mnt/skills/vendus-cli && pip install -e .
```

Manus reads the `SKILL.md` for command reference.

## Development

```bash
git clone https://github.com/larryjiggler-glitch/vendus-cli
cd vendus-cli
uv venv && uv pip install -e ".[dev]"
pytest
ruff check src/
```

## License

MIT — see [LICENSE](LICENSE).
