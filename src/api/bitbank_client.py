"""bitbank REST APIクライアント（現物のみ）。

⛔ 鉄のルール:
  - 現物取引のAPIのみ使用
  - margin / leverage 系エンドポイントは一切呼ばない
"""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

logger = logging.getLogger("btc_bot.api")

BASE_URL = "https://public.bitbank.cc"


class BitbankClient:
    """bitbank公開APIのラッパー（認証不要の公開エンドポイントのみ）。"""

    def __init__(self, pair: str = "btc_jpy") -> None:
        self.pair = pair
        self.session = requests.Session()

    def get_ticker(self) -> dict[str, Any]:
        """現在のティッカー情報を取得。"""
        url = f"{BASE_URL}/{self.pair}/ticker"
        logger.debug(f"API GET {url}")
        start = time.monotonic()
        resp = self.session.get(url, timeout=10)
        elapsed = time.monotonic() - start
        logger.debug(f"API応答: {resp.status_code} ({elapsed:.2f}s)")
        resp.raise_for_status()
        data = resp.json()
        if data.get("success") != 1:
            raise RuntimeError(f"bitbank APIエラー: {data}")
        return data["data"]

    def get_depth(self) -> dict[str, Any]:
        """板情報を取得。"""
        url = f"{BASE_URL}/{self.pair}/depth"
        logger.debug(f"API GET {url}")
        resp = self.session.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("success") != 1:
            raise RuntimeError(f"bitbank APIエラー: {data}")
        return data["data"]

    def get_candlestick(
        self, candle_type: str = "1hour", yyyymmdd: str = "20260406"
    ) -> dict[str, Any]:
        """ローソク足データを取得。"""
        url = f"{BASE_URL}/{self.pair}/candlestick/{candle_type}/{yyyymmdd}"
        logger.debug(f"API GET {url}")
        resp = self.session.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("success") != 1:
            raise RuntimeError(f"bitbank APIエラー: {data}")
        return data["data"]
