from __future__ import annotations

import importlib.util
from pathlib import Path


def test_local_check_importable():
    script = Path("scripts/local_check.py")
    spec = importlib.util.spec_from_file_location("local_check", script)
    assert spec is not None and spec.loader is not None


def test_local_check_runs(monkeypatch, capsys):
    import scripts.local_check as lc

    monkeypatch.setattr(lc, "train_and_predict", lambda df: (type("P", (), {"predicted_direction": "FLAT"})(), {"metrics": {}}))
    lc.main()
    out = capsys.readouterr().out
    assert "LOCAL CHECK PASSED" in out
