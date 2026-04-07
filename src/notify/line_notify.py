"""LINE通知（スタブ）。Phase 2 で実装予定。"""

from __future__ import annotations

import logging

logger = logging.getLogger("btc_bot.notify")


class LineNotifier:
    """LINE Notify のスタブ実装。現在はログ出力のみ。"""

    def __init__(self, token: str = "") -> None:
        self.token = token
        if token:
            logger.info("[NOTIFY] LINE Notify トークン設定済み")
        else:
            logger.info("[NOTIFY] LINE Notify トークン未設定（スタブモード）")

    def notify_trade(self, side: str, price: float, amount: float, pnl: float) -> None:
        """売買実行時の通知。"""
        msg = f"[{side.upper()}] ¥{price:,.0f} × {amount:.6f} BTC | PnL=¥{pnl:,.0f}"
        logger.info(f"[NOTIFY] {msg}")
        # TODO: Phase 2 で requests.post(LINE_NOTIFY_URL, ...) を実装

    def notify_shutdown(self, stats: dict) -> None:
        """Bot停止時の通知。"""
        logger.info(
            f"[NOTIFY] Bot停止 | 残高=¥{stats.get('balance', 0):,.0f} "
            f"| 総PnL=¥{stats.get('total_pnl', 0):,.0f}"
        )

    def notify_error(self, message: str) -> None:
        """エラー通知。"""
        logger.warning(f"[NOTIFY] ERROR: {message}")

    def notify_daily_report(self, stats: dict, daily_pnl: float) -> None:
        """日次レポート通知。"""
        logger.info(
            f"[NOTIFY] 日次レポート | 残高=¥{stats.get('balance', 0):,.0f} "
            f"| 日次PnL=¥{daily_pnl:,.0f}"
        )
