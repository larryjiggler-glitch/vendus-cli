#!/usr/bin/env python3
"""vendus-pos — task-oriented CLI for Cegid Vendus POS operations.

Usage:
    vendus-pos sales summary --since today
    vendus-pos sales by-hour --date yesterday
    vendus-pos catalog find "cappuccino"
    vendus-pos payments mix --since this-week
    vendus-pos inspect auth
"""

import argparse
import json
import logging
import sys
from typing import Any

from vendus_cli.api import get_credentials, make_session
from vendus_cli.commands import (
    catalog,
    inspect_cmd,
    meta,
    payments,
    receipts,
    sales,
    sync,
)
from vendus_cli.format import output


def _extract_format(argv: list[str]) -> tuple[str, list[str]]:
    """Extract --format flag from argv (supports any position).

    Handles both ``--format json`` and ``--format=json`` syntax.
    Returns (format_value, remaining_argv).
    """
    fmt = "json"
    remaining = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg.startswith("--format="):
            val = arg.split("=", 1)[1]
            if val in ("json", "table", "md"):
                fmt = val
            i += 1
        elif arg == "--format" and i + 1 < len(argv):
            val = argv[i + 1]
            if val in ("json", "table", "md"):
                fmt = val
                i += 2
            else:
                remaining.append(arg)
                i += 1
        else:
            remaining.append(arg)
            i += 1
    return fmt, remaining


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    out_fmt, argv = _extract_format(sys.argv[1:])

    parser = argparse.ArgumentParser(
        prog="vendus-pos",
        description=(
            "Vendus POS CLI — sales, payments, catalog, receipts\n\n"
            "Global: --format json|table|md (anywhere in command)"
        ),
    )

    subparsers = parser.add_subparsers(dest="group")

    sales.register(subparsers)
    receipts.register(subparsers)
    catalog.register(subparsers)
    payments.register(subparsers)
    meta.register(subparsers)
    sync.register(subparsers)
    inspect_cmd.register(subparsers)

    args = parser.parse_args(argv)
    args.format = out_fmt

    if not args.group:
        parser.print_help()
        sys.exit(1)

    if not hasattr(args, "func"):
        parser.parse_args([args.group, "--help"])
        sys.exit(1)

    username, api_key = get_credentials()
    session = make_session(username, api_key)

    try:
        result: Any = args.func(args, session)
        print(output(result, fmt=args.format))
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
