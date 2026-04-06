"""Layer 1: グリッドトレード戦略のユニットテスト。"""

import pytest

from src.config import Config
from src.strategy.grid_trade import GridTradeStrategy
from src.trading.risk_manager import RiskLimits, RiskManager


@pytest.fixture
def config() -> Config:
    return Config(GRID_COUNT=5, GRID_RANGE_PCT=0.10)


@pytest.fixture
def strategy(config: Config) -> GridTradeStrategy:
    return GridTradeStrategy(config)


@pytest.fixture
def risk_manager() -> RiskManager:
    return RiskManager(limits=RiskLimits(capital=30000.0))


class TestGridInit:
    def test_grid_initializes_on_first_signal(self, strategy: GridTradeStrategy):
        stats = {"balance": 30000, "position_btc": 0, "capital": 30000}
        strategy.generate_signal(10_000_000, stats)
        assert strategy._initialized
        assert len(strategy.grid_lines) == 6  # 5 grids = 6 lines

    def test_grid_center_is_first_price(self, strategy: GridTradeStrategy):
        stats = {"balance": 30000, "position_btc": 0, "capital": 30000}
        strategy.generate_signal(10_000_000, stats)
        assert strategy.center_price == 10_000_000


class TestSignals:
    def test_hold_in_middle(self, strategy: GridTradeStrategy):
        stats = {"balance": 30000, "position_btc": 0, "capital": 30000}
        sig = strategy.generate_signal(10_000_000, stats)
        # 中央付近なのでhold
        assert sig == "hold"

    def test_buy_near_grid_bottom(self, strategy: GridTradeStrategy):
        stats = {"balance": 30000, "position_btc": 0, "capital": 30000}
        # まず初期化
        strategy.generate_signal(10_000_000, stats)
        # グリッド下限付近の価格
        low = strategy.grid_lines[0]
        sig = strategy.generate_signal(low + 1, stats)
        assert sig == "buy"

    def test_sell_near_grid_top_with_position(self, strategy: GridTradeStrategy):
        stats = {"balance": 20000, "position_btc": 0.001, "capital": 30000}
        # 初期化
        strategy.generate_signal(10_000_000, stats)
        # グリッド上限付近の価格
        high = strategy.grid_lines[-1]
        sig = strategy.generate_signal(high - 1, stats)
        assert sig == "sell"

    def test_no_sell_without_position(self, strategy: GridTradeStrategy):
        stats = {"balance": 30000, "position_btc": 0, "capital": 30000}
        strategy.generate_signal(10_000_000, stats)
        high = strategy.grid_lines[-1]
        sig = strategy.generate_signal(high - 1, stats)
        assert sig == "hold"  # ポジションなし → sellしない


class TestCalcAmount:
    def test_amount_respects_risk_limit(self, strategy: GridTradeStrategy, risk_manager: RiskManager):
        stats = {"capital": 30000, "balance": 30000, "position_btc": 0}
        strategy.generate_signal(10_000_000, stats)  # init
        amount = strategy.calc_amount(10_000_000, stats, risk_manager)
        # 1グリッドあたり ¥6,000 だがリスク上限 ¥600 → ¥600/10M = 0.00006
        # 最小注文量0.0001で切り上げ
        assert amount >= 0.0001

    def test_amount_minimum_btc(self, strategy: GridTradeStrategy, risk_manager: RiskManager):
        stats = {"capital": 30000, "balance": 30000, "position_btc": 0}
        strategy.generate_signal(100_000_000, stats)
        amount = strategy.calc_amount(100_000_000, stats, risk_manager)
        assert amount >= 0.0001


class TestGridUpdate:
    def test_grid_rebuilds_on_breakout(self, strategy: GridTradeStrategy):
        stats = {"balance": 30000, "position_btc": 0, "capital": 30000}
        strategy.generate_signal(10_000_000, stats)
        old_center = strategy.center_price
        # 大きく上抜け
        strategy.update(12_000_000)
        assert strategy.center_price != old_center

    def test_describe(self, strategy: GridTradeStrategy):
        stats = {"balance": 30000, "position_btc": 0, "capital": 30000}
        strategy.generate_signal(10_000_000, stats)
        desc = strategy.describe()
        assert "GridTrade" in desc
        assert "grids=5" in desc
