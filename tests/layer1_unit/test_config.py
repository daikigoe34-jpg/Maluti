"""Layer 1: Config のユニットテスト。"""

import pytest

from src.config import Config


def test_default_config_is_demo():
    config = Config()
    assert config.DEMO_MODE is True
    assert config.ORDER_TYPE == "spot"


def test_validate_passes_for_spot():
    config = Config(ORDER_TYPE="spot")
    config.validate()  # AssertionError が出なければOK


def test_validate_rejects_non_spot():
    config = Config(ORDER_TYPE="margin")
    with pytest.raises(AssertionError, match="現物以外は禁止"):
        config.validate()


def test_capital_defaults():
    config = Config()
    assert config.CAPITAL == 30000.0
    assert config.MAX_RISK_PER_TRADE == 0.02
    assert config.DAILY_LOSS_LIMIT == 0.05
