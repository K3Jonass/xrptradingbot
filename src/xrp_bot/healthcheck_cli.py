from __future__ import annotations

import json

from .healthcheck import run_healthcheck


def main() -> None:
    print(json.dumps(run_healthcheck(), indent=2))


if __name__ == "__main__":
    main()
