"""
Username search demo for Maigret.

Searches for a username across the top-ranked sites in Maigret's bundled
database and prints any accounts that were found, along with profile data
extracted via socid_extractor when available.

Usage:
    python examples/username_search_demo.py <username> [--top N] [--timeout S]
                                                       [--tags tag1,tag2]
                                                       [--no-parse]

Examples:
    python examples/username_search_demo.py soxoj
    python examples/username_search_demo.py soxoj --top 100 --tags coding
"""

import argparse
import asyncio
import logging
import os
import sys

from maigret import search as maigret_search
from maigret.sites import MaigretDatabase
from maigret.notify import QueryNotifyPrint


DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "maigret",
    "resources",
    "data.json",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Maigret username search demo")
    parser.add_argument("username", help="Username to search for")
    parser.add_argument(
        "--top",
        type=int,
        default=500,
        help="Number of top-ranked sites to scan (default: 500)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Per-request timeout in seconds (default: 30)",
    )
    parser.add_argument(
        "--tags",
        default="",
        help="Comma-separated tag filter (e.g. 'coding,gaming')",
    )
    parser.add_argument(
        "--no-parse",
        action="store_true",
        help="Disable profile parsing via socid_extractor",
    )
    parser.add_argument(
        "--db",
        default=DEFAULT_DB_PATH,
        help=f"Path to data.json (default: {DEFAULT_DB_PATH})",
    )
    return parser.parse_args()


async def run(args: argparse.Namespace) -> int:
    logger = logging.getLogger("maigret-demo")
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

    db = MaigretDatabase().load_from_path(args.db)
    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    sites = db.ranked_sites_dict(top=args.top, tags=tags) if tags else db.ranked_sites_dict(top=args.top)

    print(f"Scanning {len(sites)} sites for username '{args.username}'...\n")

    results = await maigret_search(
        username=args.username,
        site_dict=sites,
        logger=logger,
        query_notify=QueryNotifyPrint(verbose=False, print_found_only=True),
        timeout=args.timeout,
        is_parsing_enabled=not args.no_parse,
    )

    found = {name: r for name, r in results.items() if r["status"].is_found()}

    print(f"\nFound {len(found)} account(s) out of {len(results)} sites checked.\n")
    for site_name, result in sorted(found.items()):
        print(f"[+] {site_name}: {result['url_user']}")
        ids_data = result.get("ids_data") or {}
        for key, value in ids_data.items():
            print(f"      {key}: {value}")

    return 0 if found else 1


def main() -> int:
    args = parse_args()
    try:
        return asyncio.run(run(args))
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
