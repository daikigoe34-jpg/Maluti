"""テスト共通設定。"""

import sys
from pathlib import Path

import pytest

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.trading.paper_trade import PaperTrader
from src.trading.risk_manager import RiskLimits, RiskManager


@pytest.fixture
def demo_config() -> Config:
    """DEMO_MODE=True の設定。"""
    config = Config(DEMO_MODE=True, ORDER_TYPE="spot")
    config.validate()
    return config


@pytest.fixture
def risk_limits() -> RiskLimits:
    return RiskLimits(capital=30000.0)


@pytest.fixture
def risk_manager(risk_limits: RiskLimits) -> RiskManager:
    return RiskManager(limits=risk_limits)


@pytest.fixture
def paper_trader(tmp_path: Path) -> PaperTrader:
    """一時DBを使う紙取引シミュレーター。"""
    return PaperTrader(
        capital=30000.0,
        db_path=tmp_path / "test_trades.db",
    )
