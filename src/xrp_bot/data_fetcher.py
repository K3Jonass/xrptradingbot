"""Binance public market data access layer (no private keys used)."""

from __future__ import annotations

import time
from typing import Any

import pandas as pd
import requests

from .config import NETWORK, SYMBOL


class DataFetchError(RuntimeError):
    """Raised when market data cannot be fetched or validated."""


class BinanceMarketDataFetcher:
    BASE_URL = "https://api.binance.com"

    def __init__(self) -> None:
        self.timeout = NETWORK["timeout_seconds"]

    def fetch_klines(self, interval: str, limit: int, symbol: str = SYMBOL) -> pd.DataFrame:
        retries = NETWORK["retries"]
        last_exc: Exception | None = None
        url = f"{self.BASE_URL}/api/v3/klines"
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        for attempt in range(1, retries + 1):
            try:
                resp = requests.get(url, params=params, timeout=self.timeout)
                if resp.status_code == 429:
                    time.sleep(min(attempt, 3))
                    continue
                resp.raise_for_status()
                raw_klines: list[list[Any]] = resp.json()
                return self._normalize_klines(raw_klines)
            except (requests.RequestException, ValueError) as exc:
                last_exc = exc
                time.sleep(min(attempt, 3))
                continue
            except Exception as exc:  # pragma: no cover
                raise DataFetchError(f"Unexpected fetch error: {exc}") from exc
        raise DataFetchError(f"Failed after retries: {last_exc}")

    @staticmethod
    def _normalize_klines(raw_klines: list[list[Any]]) -> pd.DataFrame:
        if not raw_klines:
            raise DataFetchError("Empty candle response from Binance.")
        columns = [
            "open_time", "open", "high", "low", "close", "volume", "close_time",
            "quote_asset_volume", "number_of_trades", "taker_buy_base_asset_volume",
            "taker_buy_quote_asset_volume", "ignore",
        ]
        for row in raw_klines:
            if len(row) < 12:
                raise DataFetchError("Malformed candle row received from Binance.")
        df = pd.DataFrame(raw_klines, columns=columns)
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            if df[col].isna().any():
                raise DataFetchError(f"Malformed numeric data in '{col}'.")
        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
        df["close_time"] = pd.to_datetime(df["close_time"], unit="ms", utc=True)
        return df
