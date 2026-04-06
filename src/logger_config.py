"""ログ設定 — デバッガーの命綱。"""

from __future__ import annotations

import logging
import os


def setup_logger(log_file: str = "logs/bot.log", level: str = "DEBUG") -> logging.Logger:
    """全モジュール共通のログ設定。"""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
    )

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(getattr(logging, level))
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger = logging.getLogger("btc_bot")
    logger.setLevel(getattr(logging, level))
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
