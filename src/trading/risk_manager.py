"""リスク管理 — CFOルールの実装。

⛔ 鉄のルール:
  - 1トレード リスク上限: 資本の2%
  - 日次損失上限: 資本の5% → Bot停止
  - 月次損失上限: 資本の15% → 全面見直し
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger("btc_bot.risk")


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
    """取引前のリスクチェックを実行する。"""

    def __init__(self, limits: RiskLimits | None = None) -> None:
        self.limits = limits or RiskLimits()
        self.daily_pnl: float = 0.0
        self.monthly_pnl: float = 0.0

    def check_trade(self, amount_jpy: float, current_position_jpy: float) -> bool:
        """取引前チェック。問題があればFalseを返す。"""
        # 1トレードのリスク上限
        if amount_jpy > self.limits.max_trade_risk_jpy:
            logger.warning(
                f"🔴 リスク超過: 取引額=¥{amount_jpy:,.0f} > "
                f"上限=¥{self.limits.max_trade_risk_jpy:,.0f}"
            )
            return False

        # 最大ポジション
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
        """損益を記録。"""
        self.daily_pnl += pnl
        self.monthly_pnl += pnl

    def reset_daily(self) -> None:
        self.daily_pnl = 0.0

    def reset_monthly(self) -> None:
        self.monthly_pnl = 0.0
