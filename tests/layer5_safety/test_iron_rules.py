"""Layer 5: 鉄のルール — 安全装置テスト（最重要）。

⛔ このテストは全テストの中で最も重要。
   1つでも失敗したら即座にCEO + CTOに報告すること。
"""

import subprocess
from pathlib import Path

import pytest

from src.config import Config


class TestDemoModeGuard:
    """DEMO_MODEガードのテスト。"""

    def test_default_is_demo_mode(self):
        config = Config()
        assert config.DEMO_MODE is True, "デフォルトはDEMO_MODEでなければならない"

    def test_order_type_is_spot(self):
        config = Config()
        assert config.ORDER_TYPE == "spot", "デフォルトはspot（現物）でなければならない"

    def test_non_spot_order_type_rejected(self):
        config = Config(ORDER_TYPE="margin")
        with pytest.raises(AssertionError):
            config.validate()

    def test_non_spot_order_type_futures_rejected(self):
        config = Config(ORDER_TYPE="futures")
        with pytest.raises(AssertionError):
            config.validate()


class TestForbiddenWords:
    """コードベースに禁止ワードが含まれていないか確認。"""

    FORBIDDEN_PATTERNS = [
        "margin_trading",
        "leverage_trading",
        "create_margin_order",
    ]

    @pytest.mark.parametrize("pattern", FORBIDDEN_PATTERNS)
    def test_no_forbidden_api_calls(self, pattern: str):
        src_dir = Path(__file__).parent.parent.parent / "src"
        if not src_dir.exists():
            pytest.skip("src/ ディレクトリが存在しません")

        result = subprocess.run(
            ["grep", "-rn", pattern, str(src_dir)],
            capture_output=True,
            text=True,
        )
        assert result.stdout == "", (
            f"🔴 禁止API呼び出し検出: {pattern}\n{result.stdout}"
        )


class TestOrderSafety:
    """注文処理の安全装置テスト。"""

    def test_place_order_in_demo_uses_paper_trade(self, demo_config, paper_trader, risk_manager):
        from src.trading.order import place_order

        result = place_order(
            config=demo_config,
            paper_trader=paper_trader,
            risk_manager=risk_manager,
            pair="btc_jpy",
            price=10_000_000,
            amount=0.001,
            side="buy",
        )
        assert result["mode"] == "demo"

    def test_real_trade_not_implemented(self, paper_trader, risk_manager):
        from src.trading.order import place_order

        config = Config(DEMO_MODE=False, ORDER_TYPE="spot")
        with pytest.raises(NotImplementedError, match="Phase 2"):
            place_order(
                config=config,
                paper_trader=paper_trader,
                risk_manager=risk_manager,
                pair="btc_jpy",
                price=1_000_000,
                amount=0.0001,  # ¥100 — リスク上限¥600以内
                side="buy",
            )

    def test_non_spot_real_trade_asserts(self, paper_trader, risk_manager):
        from src.trading.order import place_order

        config = Config(DEMO_MODE=False, ORDER_TYPE="margin")
        with pytest.raises(AssertionError, match="現物以外"):
            place_order(
                config=config,
                paper_trader=paper_trader,
                risk_manager=risk_manager,
                pair="btc_jpy",
                price=10_000_000,
                amount=0.001,
                side="buy",
            )
