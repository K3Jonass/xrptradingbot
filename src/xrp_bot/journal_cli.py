from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    path = Path("data/paper_trades.jsonl")
    count = len(path.read_text().splitlines()) if path.exists() else 0
    print(json.dumps({"journal_entries": count, "paper_trading_only": True, "advisory_only": True}, indent=2))


if __name__ == "__main__":
    main()
