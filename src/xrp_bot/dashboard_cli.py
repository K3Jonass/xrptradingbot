from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    """Launch the dashboard via Streamlit's supported CLI entrypoint."""
    from streamlit.web.cli import main as streamlit_main

    dashboard_path = Path(__file__).with_name("dashboard.py")
    sys.argv = ["streamlit", "run", str(dashboard_path)]
    raise SystemExit(streamlit_main())


if __name__ == "__main__":
    main()
