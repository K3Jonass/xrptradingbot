from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Paper trading CLI placeholder (simulation-only).")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--state-path", default="data/paper_state.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = {
        "mode": "paper",
        "paper_trading_only": True,
        "state_path": str(Path(args.state_path)),
        "once": bool(args.once),
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
