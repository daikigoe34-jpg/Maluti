"""注文処理 — DEMO_MODEガード付き。

⛔ 鉄のルール:
  - DEMO_MODE=True → 紙取引シミュレーター経由
  - DEMO_MODE=False → 二重ガード（ORDER_TYPE + CFOリスクチェック）
  - 現物のみ。レバレッジ・信用取引のコードは書かない
"""

from __future__ import annotations

import logging
from typing import Any

from src.config import Config
from src.trading.paper_trade import PaperTrader
from src.trading.risk_manager import RiskManager

logger = logging.getLogger("btc_bot.order")


def place_order(
    config: Config,
    paper_trader: PaperTrader,
    risk_manager: RiskManager,
    pair: str,
    price: float,
    amount: float,
    side: str,
) -> dict[str, Any]:
    """注文を実行する。DEMO_MODEに応じて紙取引 or 実取引。"""

    # ── DEMO_MODE ガード ──
    if config.DEMO_MODE:
        logger.info(f"[DEMO] {side} {amount} {pair} @ ¥{price:,.0f}")
        order = paper_trader.simulate_order(pair, price, amount, side)
        risk_manager.record_pnl(order.pnl)
        return {
            "mode": "demo",
            "side": side,
            "price": price,
            "amount": amount,
            "pnl": order.pnl,
        }

    # ── 実取引ガード（二重チェック） ──
    assert config.ORDER_TYPE == "spot", "🔴 鉄のルール違反: 現物以外の取引は禁止です"

    amount_jpy = price * amount
    if not risk_manager.check_trade(amount_jpy, 0.0):
        logger.warning(f"🔴 CFOリスクチェック失敗: 取引を拒否")
        return {"mode": "blocked", "reason": "risk_limit_exceeded"}

    if not risk_manager.check_daily_limit():
        logger.critical(f"🔴 日次損失上限超過: Bot停止")
        return {"mode": "stopped", "reason": "daily_loss_limit"}

    # TODO: 実取引の実装は Phase 2 以降（大起の承認後）
    logger.error("実取引は未実装です。Phase 2 で大起の承認後に実装します。")
    raise NotImplementedError("実取引は Phase 2 以降で実装。大起の承認が必要です。")
