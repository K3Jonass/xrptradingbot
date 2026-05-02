from __future__ import annotations

import argparse
import json

from .journal import load_journal, weekly_summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize paper-trade journal activity")
    parser.add_argument("--json", action="store_true", help="Print weekly summary as JSON")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    journal_df = load_journal()
    summary = weekly_summary(journal_df)
    if args.json:
        print(json.dumps(summary, indent=2))
        return
    print(f"Journal entries: {len(journal_df)}")
    print(f"Average decision score: {summary['avg_decision_score']}")


if __name__ == "__main__":
    main()
