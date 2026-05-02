from __future__ import annotations


def test_journal_cli_main_importable() -> None:
    from xrp_bot.journal_cli import main

    assert callable(main)
