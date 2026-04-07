"""Layer 1: PaperTrader のユニットテスト。"""

import pytest

from src.trading.paper_trade import PaperTrader


def test_buy_order(paper_trader: PaperTrader):
    order = paper_trader.simulate_order("btc_jpy", 10_000_000, 0.001, "buy")
    assert order.side == "buy"
    assert order.price == 10_000_000
    assert paper_trader.position == 0.001


def test_sell_order_after_buy(paper_trader: PaperTrader):
    paper_trader.simulate_order("btc_jpy", 10_000_000, 0.001, "buy")
    order = paper_trader.simulate_order("btc_jpy", 10_100_000, 0.001, "sell")
    assert order.side == "sell"
    assert paper_trader.position == 0.0
    assert order.pnl > 0  # 値上がりしたのでプラス


def test_sell_without_position_raises(paper_trader: PaperTrader):
    with pytest.raises(ValueError, match="ポジション不足"):
        paper_trader.simulate_order("btc_jpy", 10_000_000, 0.001, "sell")


def test_buy_exceeding_balance_raises(paper_trader: PaperTrader):
    with pytest.raises(ValueError, match="残高不足"):
        paper_trader.simulate_order("btc_jpy", 10_000_000, 1.0, "buy")  # 1千万円分


def test_stats(paper_trader: PaperTrader):
    stats = paper_trader.get_stats()
    assert stats["balance"] == 30000.0
    assert stats["capital"] == 30000.0
    assert stats["total_pnl"] == 0.0
