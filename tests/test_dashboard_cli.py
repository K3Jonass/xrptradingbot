from __future__ import annotations

import importlib
import sys
from types import SimpleNamespace
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python <3.11
    import tomli as tomllib


class _BlockStreamlitImports:
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith("streamlit"):
            raise ModuleNotFoundError("streamlit blocked by test")
        return None


def test_dashboard_helpers_import_without_streamlit_runtime(monkeypatch):
    blocker = _BlockStreamlitImports()
    monkeypatch.syspath_prepend("src")
    monkeypatch.setattr(sys, "meta_path", [blocker, *sys.meta_path])

    mod = importlib.import_module("xrp_bot.dashboard")

    assert callable(mod.load_paper_state)
    assert callable(mod.calculate_dashboard_metrics)


def test_dashboard_cli_import_does_not_execute_ui(monkeypatch):
    monkeypatch.syspath_prepend("src")
    mod = importlib.import_module("xrp_bot.dashboard_cli")

    assert callable(mod.main)


def test_xrp_dashboard_script_target_is_valid():
    pyproject = Path("pyproject.toml")
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))

    target = data["project"]["scripts"]["xrp-dashboard"]
    assert ":" in target

    module_name, func_name = target.split(":", 1)
    module = importlib.import_module(module_name)

    assert hasattr(module, func_name)


def test_xrp_dashboard_cli_runs_dashboard_py(monkeypatch):
    monkeypatch.syspath_prepend("src")
    mod = importlib.import_module("xrp_bot.dashboard_cli")

    calls = {}

    def fake_streamlit_main():
        calls["argv"] = list(sys.argv)
        return 0

    monkeypatch.setitem(sys.modules, "streamlit.web.cli", SimpleNamespace(main=fake_streamlit_main))

    try:
        mod.main()
    except SystemExit:
        pass

    assert calls["argv"][0:2] == ["streamlit", "run"]
    assert calls["argv"][2].endswith("src/xrp_bot/dashboard.py")
