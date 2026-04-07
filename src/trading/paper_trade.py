"""紙取引シミュレーター — Phase 1 のコア。

⛔ DEMO_MODEガード: このモジュールはデモモード専用。
   実取引APIは一切呼ばない。
"""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("btc_bot.paper_trade")

DB_PATH = Path("logs/paper_trades.db")


@dataclass
class PaperOrder:
    """紙取引の注文レコード。"""

    timestamp: str
    side: str       # "buy" or "sell"
    pair: str
    price: float
    amount: float
    fee: float
    pnl: float = 0.0


class PaperTrader:
    """紙取引の実行と記録。SQLiteに全注文を保存。"""

    def __init__(
        self,
        capital: float = 30000.0,
        maker_fee: float = -0.0002,
        taker_fee: float = 0.0012,
        db_path: Path = DB_PATH,
    ) -> None:
        self.capital = capital
        self.balance = capital
        self.maker_fee = maker_fee
        self.taker_fee = taker_fee
        self.position: float = 0.0  # BTC保有量
        self.avg_buy_price: float = 0.0
        self.db_path = db_path
        self._init_db()
        logger.info(
            f"[DEMO] PaperTrader 初期化: 資本=¥{capital:,.0f}, DEMO_MODE=True"
        )

    def _init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS paper_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                side TEXT NOT NULL,
                pair TEXT NOT NULL,
                price REAL NOT NULL,
                amount REAL NOT NULL,
                fee REAL NOT NULL,
                pnl REAL DEFAULT 0,
                balance_after REAL NOT NULL
            )
        """)
        self.conn.commit()

    def simulate_order(
        self,
        pair: str,
        price: float,
        amount: float,
        side: str,
        is_maker: bool = True,
    ) -> PaperOrder:
        """紙注文を実行し、記録する。"""
        fee_rate = self.maker_fee if is_maker else self.taker_fee
        cost = price * amount
        fee = cost * fee_rate
        pnl = 0.0

        if side == "buy":
            total_cost = cost + fee
            if total_cost > self.balance:
                logger.warning(f"[DEMO] 残高不足: 必要=¥{total_cost:,.0f}, 残高=¥{self.balance:,.0f}")
                raise ValueError("残高不足")
            self.balance -= total_cost
            self.avg_buy_price = (
                (self.avg_buy_price * self.position + price * amount)
                / (self.position + amount)
                if self.position > 0
                else price
            )
            self.position += amount

        elif side == "sell":
            if amount > self.position:
                logger.warning(f"[DEMO] ポジション不足: 売却量={amount}, 保有量={self.position}")
                raise ValueError("ポジション不足")
            pnl = (price - self.avg_buy_price) * amount - abs(fee)
            self.balance += cost - abs(fee)
            self.position -= amount

        order = PaperOrder(
            timestamp=datetime.now(timezone.utc).isoformat(),
            side=side,
            pair=pair,
            price=price,
            amount=amount,
            fee=fee,
            pnl=pnl,
        )

        self._save_order(order)
        logger.info(
            f"[DEMO] {side.upper()} {amount} {pair} @ ¥{price:,.0f} "
            f"| 手数料=¥{fee:,.0f} | PnL=¥{pnl:,.0f} | 残高=¥{self.balance:,.0f}"
        )
        return order

    def _save_order(self, order: PaperOrder) -> None:
        self.conn.execute(
            """INSERT INTO paper_orders
               (timestamp, side, pair, price, amount, fee, pnl, balance_after)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                order.timestamp,
                order.side,
                order.pair,
                order.price,
                order.amount,
                order.fee,
                order.pnl,
                self.balance,
            ),
        )
        self.conn.commit()

    def get_stats(self) -> dict:
        """現在のポートフォリオ状況を返す。"""
        return {
            "balance": self.balance,
            "position_btc": self.position,
            "avg_buy_price": self.avg_buy_price,
            "total_pnl": self.balance - self.capital,
            "total_pnl_pct": (self.balance - self.capital) / self.capital * 100,
            "capital": self.capital,
        }
