import json
from pathlib import Path

import pytest
from xrp_bot.data_fetcher import BinanceMarketDataFetcher, DataFetchError


def test_normalize_klines_success_from_fixture():
    fixture = Path(__file__).parent / "fixtures" / "xrpusdt_1h_sample.json"
    raw = json.loads(fixture.read_text(encoding="utf-8"))
    df = BinanceMarketDataFetcher._normalize_klines(raw)
    assert len(df) > 50
    assert "close" in df.columns


def test_normalize_klines_empty():
    with pytest.raises(DataFetchError):
        BinanceMarketDataFetcher._normalize_klines([])
