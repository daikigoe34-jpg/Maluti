"""Layer 1: bot.py メインループのユニットテスト（モックAPI使用）。"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.config import Config


@pytest.fixture
def demo_config() -> Config:
    return Config(
        DEMO_MODE=True,
        ORDER_TYPE="spot",
        LOOP_INTERVAL_SEC=0,
        STRATEGY_NAME="grid_trade",
        GRID_COUNT=5,
        GRID_RANGE_PCT=0.10,
        LOG_FILE="/tmp/test_bot.log",
    )


class TestBotImport:
    def test_bot_module_imports(self):
        import src.bot
        assert hasattr(src.bot, "run_bot")

    def test_strategy_factory_has_grid_trade(self):
        import src.strategy.grid_trade  # noqa: F401
        from src.strategy.base import StrategyFactory
        assert "grid_trade" in StrategyFactory.available()


class TestBotSafetyGuards:
    def test_bot_refuses_non_spot(self):
        config = Config(DEMO_MODE=True, ORDER_TYPE="margin")
        with pytest.raises(AssertionError, match="現物以外は禁止"):
            config.validate()

    def test_config_defaults_are_safe(self):
        config = Config()
        assert config.DEMO_MODE is True
        assert config.ORDER_TYPE == "spot"
        assert config.STRATEGY_NAME == "grid_trade"
        assert config.LOOP_INTERVAL_SEC == 60
