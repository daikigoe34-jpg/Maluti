"""Layer 1: RiskManager のユニットテスト。"""

from src.trading.risk_manager import RiskLimits, RiskManager


def test_trade_within_limit(risk_manager: RiskManager):
    assert risk_manager.check_trade(500.0, 0.0) is True


def test_trade_exceeds_per_trade_limit(risk_manager: RiskManager):
    # 上限は ¥600（資本3万 × 2%）
    assert risk_manager.check_trade(700.0, 0.0) is False


def test_position_limit(risk_manager: RiskManager):
    # 最大ポジション ¥9,000（資本3万 × 30%）
    assert risk_manager.check_trade(500.0, 8600.0) is False


def test_daily_loss_limit(risk_manager: RiskManager):
    risk_manager.record_pnl(-1600.0)  # ¥1,500超え
    assert risk_manager.check_daily_limit() is False


def test_daily_loss_within_limit(risk_manager: RiskManager):
    risk_manager.record_pnl(-1000.0)
    assert risk_manager.check_daily_limit() is True


def test_monthly_loss_limit(risk_manager: RiskManager):
    risk_manager.record_pnl(-5000.0)  # ¥4,500超え
    assert risk_manager.check_monthly_limit() is False


def test_reset_daily(risk_manager: RiskManager):
    risk_manager.record_pnl(-1600.0)
    risk_manager.reset_daily()
    assert risk_manager.check_daily_limit() is True
