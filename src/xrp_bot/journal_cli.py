from __future__ import annotations

import argparse
import json

from .journal import load_journal, weekly_summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Trading journal and decision intelligence CLI (paper-only).")
    parser.add_argument("--json", action="store_true", help="Output summary as JSON")
    parser.add_argument("--journal-path", default="data/trade_journal.jsonl")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = weekly_summary(load_journal(args.journal_path))
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print("Weekly Journal Summary")
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
