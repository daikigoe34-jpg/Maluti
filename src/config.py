"""BTC Research Corp. — 設定管理。

⛔ 鉄のルール:
  - DEMO_MODE=True がデフォルト。変更は大起の承認が必要
  - ORDER_TYPE="spot" 以外は禁止
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class Config:
    """Bot設定。環境変数または config.yaml から読み込む。"""

    # ── 鉄のルール関連 ──
    DEMO_MODE: bool = True
    ORDER_TYPE: str = "spot"  # "spot" 以外は AssertionError

    # ── bitbank API ──
    BITBANK_API_KEY: str = ""
    BITBANK_API_SECRET: str = ""
    PAIR: str = "btc_jpy"

    # ── 資金管理（CFOルール） ──
    CAPITAL: float = 30000.0
    MAX_RISK_PER_TRADE: float = 0.02      # 資本の2%（¥600）
    MAX_POSITION_RATIO: float = 0.30       # 資本の30%（¥9,000）
    DAILY_LOSS_LIMIT: float = 0.05         # 資本の5%（¥1,500）→ Bot停止
    MONTHLY_LOSS_LIMIT: float = 0.15       # 資本の15%（¥4,500）→ 全面見直し

    # ── bitbank 手数料 ──
    MAKER_FEE: float = -0.0002  # -0.02% (リベート)
    TAKER_FEE: float = 0.0012   # 0.12%

    # ── LINE Notify ──
    LINE_NOTIFY_TOKEN: str = ""

    # ── ログ ──
    LOG_LEVEL: str = "DEBUG"
    LOG_FILE: str = "logs/bot.log"

    @classmethod
    def from_env(cls) -> Config:
        """環境変数から設定を読み込む。"""
        return cls(
            DEMO_MODE=os.getenv("DEMO_MODE", "true").lower() == "true",
            ORDER_TYPE=os.getenv("ORDER_TYPE", "spot"),
            BITBANK_API_KEY=os.getenv("BITBANK_API_KEY", ""),
            BITBANK_API_SECRET=os.getenv("BITBANK_API_SECRET", ""),
            LINE_NOTIFY_TOKEN=os.getenv("LINE_NOTIFY_TOKEN", ""),
            LOG_LEVEL=os.getenv("LOG_LEVEL", "DEBUG"),
        )

    def validate(self) -> None:
        """鉄のルールの設定レベルでの検証。"""
        assert self.ORDER_TYPE == "spot", (
            f"🔴 鉄のルール違反: ORDER_TYPE='{self.ORDER_TYPE}' — 現物以外は禁止"
        )
        if not self.DEMO_MODE:
            import logging
            logging.getLogger("btc_bot").warning(
                "⚠️ DEMO_MODE=False — 実取引モードです。大起の承認は得ていますか？"
            )
