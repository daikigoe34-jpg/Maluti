"""BTC Research Corp. — 自動売買ループ（Phase 1: デモモード）。

⛔ 鉄のルール:
  - DEMO_MODE=True がデフォルト
  - 現物取引のみ
  - レバレッジ・信用取引は一切禁止
"""

from __future__ import annotations

import logging
import signal
import sys
import time

import requests

from src.api.bitbank_client import BitbankClient
from src.config import Config
from src.logger_config import setup_logger
from src.notify.line_notify import LineNotifier
from src.strategy.base import StrategyFactory

# 戦略を登録するためにインポート
import src.strategy.grid_trade  # noqa: F401
from src.trading.order import place_order
from src.trading.paper_trade import PaperTrader
from src.trading.risk_manager import RiskLimits, RiskManager

logger = logging.getLogger("btc_bot")

# グローバル停止フラグ
_running = True


def _graceful_shutdown(signum: int = 0, frame: object = None) -> None:
    """安全停止ハンドラ。"""
    global _running
    _running = False
    logger.info("[BOT] シャットダウンシグナル受信")


def run_bot(config: Config | None = None) -> None:
    """メインループ。"""
    global _running
    _running = True

    # ── 初期化 ──
    if config is None:
        config = Config.from_env()
    config.validate()

    setup_logger(config.LOG_FILE, config.LOG_LEVEL)
    logger.info("=" * 60)
    logger.info("  🏢 BTC Research Corp. — Bot起動")
    logger.info(f"  DEMO_MODE={config.DEMO_MODE}")
    logger.info(f"  ORDER_TYPE={config.ORDER_TYPE}")
    logger.info(f"  CAPITAL=¥{config.CAPITAL:,.0f}")
    logger.info(f"  STRATEGY={config.STRATEGY_NAME}")
    logger.info("=" * 60)

    client = BitbankClient(config.PAIR)
    paper_trader = PaperTrader(
        capital=config.CAPITAL,
        maker_fee=config.MAKER_FEE,
        taker_fee=config.TAKER_FEE,
    )
    risk_limits = RiskLimits(
        capital=config.CAPITAL,
        max_risk_per_trade=config.MAX_RISK_PER_TRADE,
        max_position_ratio=config.MAX_POSITION_RATIO,
        daily_loss_limit=config.DAILY_LOSS_LIMIT,
        monthly_loss_limit=config.MONTHLY_LOSS_LIMIT,
    )
    risk_manager = RiskManager(limits=risk_limits)
    strategy = StrategyFactory.create(config.STRATEGY_NAME, config)
    notifier = LineNotifier(config.LINE_NOTIFY_TOKEN)

    # Ctrl+C ハンドラ
    signal.signal(signal.SIGINT, _graceful_shutdown)
    signal.signal(signal.SIGTERM, _graceful_shutdown)

    logger.info(f"[BOT] 戦略: {strategy.describe()}")
    logger.info(f"[BOT] ループ間隔: {config.LOOP_INTERVAL_SEC}秒")
    logger.info("[BOT] 自動ループ開始")

    consecutive_errors = 0
    loop_count = 0

    # ── メインループ ──
    while _running:
        loop_count += 1
        try:
            # [STEP 1] ティッカー取得
            ticker = client.get_ticker()
            price = float(ticker["last"])
            logger.info(f"[LOOP #{loop_count}] BTC/JPY = ¥{price:,.0f}")
            consecutive_errors = 0  # 成功したらリセット

            # [STEP 2] 日次損失チェック
            if not risk_manager.check_daily_limit():
                logger.critical("[BOT] 日次損失上限超過 → 安全停止")
                notifier.notify_error("日次損失上限超過 — Bot停止")
                break

            # [STEP 3] 戦略の内部状態を更新
            strategy.update(price)

            # [STEP 4] シグナル取得
            stats = paper_trader.get_stats()
            sig = strategy.generate_signal(price, stats)

            # [STEP 5] シグナル処理
            if sig == "hold":
                logger.debug(f"[LOOP #{loop_count}] シグナル: HOLD")

            elif sig in ("buy", "sell"):
                amount = strategy.calc_amount(price, stats, risk_manager)
                amount_jpy = price * amount

                if not risk_manager.check_trade(amount_jpy, stats["position_btc"] * price):
                    logger.warning(f"[LOOP #{loop_count}] リスクチェック失敗 → スキップ")
                else:
                    result = place_order(
                        config, paper_trader, risk_manager,
                        config.PAIR, price, amount, sig,
                    )
                    pnl = result.get("pnl", 0.0)
                    notifier.notify_trade(sig, price, amount, pnl)

            # [STEP 6] 状態ログ
            stats = paper_trader.get_stats()
            logger.info(
                f"[STATUS] 残高=¥{stats['balance']:,.0f} | "
                f"BTC={stats['position_btc']:.6f} | "
                f"総PnL=¥{stats['total_pnl']:,.0f} ({stats['total_pnl_pct']:+.2f}%) | "
                f"日次PnL=¥{risk_manager.daily_pnl:,.0f}"
            )

            # [STEP 7] インターバル
            if _running:
                time.sleep(config.LOOP_INTERVAL_SEC)

        except KeyboardInterrupt:
            break

        except requests.RequestException as e:
            consecutive_errors += 1
            logger.error(f"[ERROR] API通信エラー ({consecutive_errors}/{config.MAX_CONSECUTIVE_ERRORS}): {e}")
            if consecutive_errors >= config.MAX_CONSECUTIVE_ERRORS:
                logger.critical("[BOT] 連続エラー上限 → 安全停止")
                notifier.notify_error(f"連続APIエラー{consecutive_errors}回 — Bot停止")
                break
            time.sleep(config.ERROR_RETRY_INTERVAL_SEC)

        except ValueError as e:
            # 残高不足・ポジション不足 → スキップして続行
            logger.warning(f"[LOOP #{loop_count}] {e} → スキップ")

        except Exception as e:
            logger.exception(f"[ERROR] 予期しないエラー: {e}")
            notifier.notify_error(f"予期しないエラー: {e}")
            break

    # ── シャットダウン ──
    logger.info("[BOT] シャットダウン開始")
    stats = paper_trader.get_stats()
    logger.info(
        f"[FINAL] ループ数={loop_count} | "
        f"最終残高=¥{stats['balance']:,.0f} | "
        f"総PnL=¥{stats['total_pnl']:,.0f} ({stats['total_pnl_pct']:+.2f}%)"
    )
    notifier.notify_shutdown(stats)
    paper_trader.conn.close()
    logger.info("[BOT] 正常終了")


if __name__ == "__main__":
    run_bot()
