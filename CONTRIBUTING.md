# Contributing to vendus-cli

## Development Setup

```bash
git clone https://github.com/larryjiggler-glitch/vendus-cli
cd vendus-cli
uv venv
uv pip install -e ".[dev]"
```

## Code Style

This project uses [ruff](https://docs.astral.sh/ruff/) for linting and formatting:

```bash
ruff check src/           # lint
ruff check src/ --fix     # auto-fix
ruff format src/          # format
```

Configuration is in `pyproject.toml`. Key rules: line length 100, Python 3.10+ target.

## Testing

```bash
pytest                    # run all tests
pytest -v                 # verbose output
pytest tests/test_dates.py  # specific test file
```

Tests should not require API access. Use pure logic tests for date parsing, formatting, etc.

## Pull Request Process

1. Fork the repo and create a feature branch from `main`.
2. Make your changes. Add tests if applicable.
3. Run `ruff check src/` and `pytest` — both must pass.
4. Open a PR with a clear description of what changed and why.
5. One approval required before merge.

## Adding a New Command

1. Create or edit a file in `src/vendus_cli/commands/`.
2. Add a `register(subparsers)` function that sets up argparse and `set_defaults(func=...)`.
3. Command functions take `(args, session)` and **return a dict** (never print directly).
4. Register the module in `src/vendus_cli/cli.py`.
5. Add tests if the command has non-trivial logic.
6. Document in `SKILL.md` and `README.md`.

## Reporting Issues

Use [GitHub Issues](https://github.com/larryjiggler-glitch/vendus-cli/issues). Include:

- What you ran (exact command)
- What you expected
- What happened (error message, unexpected output)
- Your Python version and OS
