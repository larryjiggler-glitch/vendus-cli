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


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    # Extract --format from argv before argparse (works in any position)
    argv = sys.argv[1:]
    out_fmt = "json"
    if "--format" in argv:
        idx = argv.index("--format")
        if idx + 1 < len(argv) and argv[idx + 1] in ("json", "table", "md"):
            out_fmt = argv[idx + 1]
            argv = argv[:idx] + argv[idx + 2:]

    parser = argparse.ArgumentParser(
        prog="vendus-pos",
        description=(
            "Vendus POS CLI — sales, payments, catalog, receipts\n\n"
            "Global: --format json|table|md (anywhere in command)"
        ),
    )

    subparsers = parser.add_subparsers(dest="group")

    # Register all command families
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
    except ValueError as e:
        print(json.dumps({"error": str(e)}, indent=2))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
