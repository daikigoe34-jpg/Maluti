"""リスク管理 — CFOルールの実装。

⛔ 鉄のルール:
  - 1トレード リスク上限: 資本の2%
  - 日次損失上限: 資本の5% → Bot停止
  - 月次損失上限: 資本の15% → 全面見直し
"""

from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

logger = logging.getLogger("btc_bot.risk")

RISK_DB_PATH = Path("logs/risk_state.db")


@dataclass
class RiskLimits:
    """CFOが定めたリスク上限値。"""

    capital: float = 30000.0
    max_risk_per_trade: float = 0.02
    max_position_ratio: float = 0.30
    daily_loss_limit: float = 0.05
    monthly_loss_limit: float = 0.15

    @property
    def max_trade_risk_jpy(self) -> float:
        return self.capital * self.max_risk_per_trade

    @property
    def max_position_jpy(self) -> float:
        return self.capital * self.max_position_ratio

    @property
    def daily_loss_limit_jpy(self) -> float:
        return self.capital * self.daily_loss_limit

    @property
    def monthly_loss_limit_jpy(self) -> float:
        return self.capital * self.monthly_loss_limit


class RiskManager:
    """取引前のリスクチェックを実行する。日次/月次PnLをSQLiteに永続化。"""

    def __init__(
        self,
        limits: RiskLimits | None = None,
        db_path: Path = RISK_DB_PATH,
    ) -> None:
        self.limits = limits or RiskLimits()
        self.db_path = db_path
        self.daily_pnl: float = 0.0
        self.monthly_pnl: float = 0.0
        self._init_db()
        self._load_state()

    def _init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS risk_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                daily_pnl REAL NOT NULL DEFAULT 0,
                monthly_pnl REAL NOT NULL DEFAULT 0,
                last_daily_reset TEXT NOT NULL,
                last_monthly_reset TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def _load_state(self) -> None:
        """DB から日次/月次PnLを復元。日付が変わっていたらリセット。"""
        row = self.conn.execute("SELECT * FROM risk_state WHERE id = 1").fetchone()
        today = date.today().isoformat()
        this_month = date.today().strftime("%Y-%m")

        if row is None:
            self.conn.execute(
                "INSERT INTO risk_state (id, daily_pnl, monthly_pnl, last_daily_reset, last_monthly_reset) "
                "VALUES (1, 0, 0, ?, ?)",
                (today, this_month),
            )
            self.conn.commit()
            return

        _, daily_pnl, monthly_pnl, last_daily, last_monthly = row

        # 日付が変わっていたら日次リセット
        if last_daily != today:
            daily_pnl = 0.0
            logger.info(f"[RISK] 日次PnLリセット（前日: {last_daily}）")

        # 月が変わっていたら月次リセット
        if last_monthly != this_month:
            monthly_pnl = 0.0
            logger.info(f"[RISK] 月次PnLリセット（前月: {last_monthly}）")

        self.daily_pnl = daily_pnl
        self.monthly_pnl = monthly_pnl
        self._save_state()
        logger.info(f"[RISK] 状態復元: 日次PnL=¥{self.daily_pnl:,.0f}, 月次PnL=¥{self.monthly_pnl:,.0f}")

    def _save_state(self) -> None:
        """現在の状態をDBに保存。"""
        today = date.today().isoformat()
        this_month = date.today().strftime("%Y-%m")
        self.conn.execute(
            "UPDATE risk_state SET daily_pnl=?, monthly_pnl=?, last_daily_reset=?, last_monthly_reset=? WHERE id=1",
            (self.daily_pnl, self.monthly_pnl, today, this_month),
        )
        self.conn.commit()

    def check_trade(self, amount_jpy: float, current_position_jpy: float) -> bool:
        """取引前チェック。問題があればFalseを返す。"""
        if amount_jpy > self.limits.max_trade_risk_jpy:
            logger.warning(
                f"🔴 リスク超過: 取引額=¥{amount_jpy:,.0f} > "
                f"上限=¥{self.limits.max_trade_risk_jpy:,.0f}"
            )
            return False

        if current_position_jpy + amount_jpy > self.limits.max_position_jpy:
            logger.warning(
                f"🔴 ポジション超過: 合計=¥{current_position_jpy + amount_jpy:,.0f} > "
                f"上限=¥{self.limits.max_position_jpy:,.0f}"
            )
            return False

        return True

    def check_daily_limit(self) -> bool:
        """日次損失上限チェック。超過ならBot停止が必要。"""
        if abs(self.daily_pnl) > self.limits.daily_loss_limit_jpy and self.daily_pnl < 0:
            logger.critical(
                f"🔴 日次損失上限超過: ¥{self.daily_pnl:,.0f} — Bot停止が必要"
            )
            return False
        return True

    def check_monthly_limit(self) -> bool:
        """月次損失上限チェック。超過なら全面見直し。"""
        if abs(self.monthly_pnl) > self.limits.monthly_loss_limit_jpy and self.monthly_pnl < 0:
            logger.critical(
                f"🔴 月次損失上限超過: ¥{self.monthly_pnl:,.0f} — 全面見直しが必要"
            )
            return False
        return True

    def record_pnl(self, pnl: float) -> None:
        """損益を記録し、永続化する。"""
        self.daily_pnl += pnl
        self.monthly_pnl += pnl
        self._save_state()

    def reset_daily(self) -> None:
        self.daily_pnl = 0.0
        self._save_state()

    def reset_monthly(self) -> None:
        self.monthly_pnl = 0.0
        self._save_state()
