"""グリッドトレード戦略 — 戦略企画推奨。

レンジ相場で等間隔の指値注文を配置し、小さな利益を積み重ねる。
Maker注文（手数料 -0.02%）を活用して手数料負けを回避。

⛔ 鉄のルール: 現物のみ。レバレッジ禁止。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.strategy.base import BaseStrategy, SignalType, StrategyFactory

if TYPE_CHECKING:
    from src.config import Config
    from src.trading.risk_manager import RiskManager

logger = logging.getLogger("btc_bot.strategy.grid")


class GridTradeStrategy(BaseStrategy):
    """等間隔グリッドトレード。

    - 現在価格がグリッド下限付近 → buy
    - 現在価格がグリッド上限付近 → sell（ポジションあれば）
    - それ以外 → hold
    """

    def __init__(self, config: Config) -> None:
        super().__init__(config)
        self.grid_count: int = config.GRID_COUNT
        self.grid_range_pct: float = config.GRID_RANGE_PCT
        self.center_price: float | None = None
        self.grid_lines: list[float] = []
        self._initialized = False

    def _init_grid(self, current_price: float) -> None:
        """初回価格を基にグリッドを構築。"""
        self.center_price = current_price
        half_range = current_price * (self.grid_range_pct / 2)
        low = current_price - half_range
        high = current_price + half_range
        step = (high - low) / self.grid_count

        self.grid_lines = [low + step * i for i in range(self.grid_count + 1)]
        self._initialized = True
        logger.info(
            f"[GRID] 初期化: center=¥{current_price:,.0f} "
            f"range={self.grid_range_pct*100:.1f}% "
            f"lines={self.grid_count+1}本 "
            f"low=¥{low:,.0f} high=¥{high:,.0f}"
        )

    def generate_signal(
        self,
        current_price: float,
        portfolio_stats: dict,
    ) -> SignalType:
        if not self._initialized:
            self._init_grid(current_price)

        has_position = portfolio_stats.get("position_btc", 0) > 0
        balance = portfolio_stats.get("balance", 0)

        # 最も近い下のグリッドラインを探す
        below_lines = [g for g in self.grid_lines if g <= current_price]
        above_lines = [g for g in self.grid_lines if g > current_price]

        if not below_lines or not above_lines:
            logger.debug("[GRID] 価格がグリッド範囲外 → HOLD")
            return "hold"

        nearest_below = max(below_lines)
        nearest_above = min(above_lines)
        grid_step = nearest_above - nearest_below if nearest_above != nearest_below else 1

        # 価格がグリッド下端に近い（下25%以内）→ 買い
        dist_from_below = (current_price - nearest_below) / grid_step
        if dist_from_below < 0.25 and balance > 0:
            logger.info(f"[GRID] BUY シグナル: price=¥{current_price:,.0f} 近いライン=¥{nearest_below:,.0f}")
            return "buy"

        # 価格がグリッド上端に近い（上25%以内）→ 売り
        dist_from_above = (nearest_above - current_price) / grid_step
        if dist_from_above < 0.25 and has_position:
            logger.info(f"[GRID] SELL シグナル: price=¥{current_price:,.0f} 近いライン=¥{nearest_above:,.0f}")
            return "sell"

        logger.debug(f"[GRID] HOLD: price=¥{current_price:,.0f}")
        return "hold"

    def calc_amount(
        self,
        current_price: float,
        portfolio_stats: dict,
        risk_manager: RiskManager,
    ) -> float:
        """1グリッドあたりの注文量を計算。資本をグリッド数で等分。"""
        capital = portfolio_stats.get("capital", 30000.0)
        per_grid_jpy = capital / self.grid_count
        # CFOルール: 1トレードリスク上限
        max_risk_jpy = risk_manager.limits.max_trade_risk_jpy
        amount_jpy = min(per_grid_jpy, max_risk_jpy)
        amount_btc = amount_jpy / current_price

        # bitbank最小注文量: 0.0001 BTC
        amount_btc = max(amount_btc, 0.0001)
        logger.debug(f"[GRID] 注文量計算: ¥{amount_jpy:,.0f} → {amount_btc:.6f} BTC")
        return round(amount_btc, 8)

    def update(self, current_price: float) -> None:
        """グリッド範囲を逸脱したら再構築。"""
        if not self._initialized:
            return
        low = self.grid_lines[0]
        high = self.grid_lines[-1]
        if current_price < low * 0.97 or current_price > high * 1.03:
            logger.warning(
                f"[GRID] 価格がグリッド範囲を逸脱 → 再構築 "
                f"(price=¥{current_price:,.0f}, range=¥{low:,.0f}〜¥{high:,.0f})"
            )
            self._init_grid(current_price)

    def describe(self) -> str:
        if self._initialized:
            return (
                f"GridTrade(grids={self.grid_count}, "
                f"range={self.grid_range_pct*100:.0f}%, "
                f"center=¥{self.center_price:,.0f})"
            )
        return f"GridTrade(grids={self.grid_count}, range={self.grid_range_pct*100:.0f}%, 未初期化)"


# ファクトリに登録
StrategyFactory.register("grid_trade", GridTradeStrategy)
