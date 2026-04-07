"""戦略の基底クラスとファクトリ。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from src.config import Config
    from src.trading.risk_manager import RiskManager

SignalType = Literal["buy", "sell", "hold"]


class BaseStrategy(ABC):
    """全戦略が継承する基底クラス。"""

    def __init__(self, config: Config) -> None:
        self.config = config

    @abstractmethod
    def generate_signal(
        self,
        current_price: float,
        portfolio_stats: dict,
    ) -> SignalType:
        """現在価格とポートフォリオからシグナルを返す。"""
        ...

    @abstractmethod
    def calc_amount(
        self,
        current_price: float,
        portfolio_stats: dict,
        risk_manager: RiskManager,
    ) -> float:
        """注文量（BTC単位）を計算する。"""
        ...

    def update(self, current_price: float) -> None:
        """ループごとの内部状態更新フック。"""
        pass

    @abstractmethod
    def describe(self) -> str:
        """戦略名と主要パラメータを1行で返す。"""
        ...


class StrategyFactory:
    """戦略名からインスタンスを生成するファクトリ。"""

    _registry: dict[str, type[BaseStrategy]] = {}

    @classmethod
    def register(cls, name: str, strategy_cls: type[BaseStrategy]) -> None:
        cls._registry[name] = strategy_cls

    @classmethod
    def create(cls, name: str, config: Config) -> BaseStrategy:
        if name not in cls._registry:
            available = list(cls._registry.keys())
            raise ValueError(f"未登録の戦略: '{name}' — 登録済み: {available}")
        return cls._registry[name](config)

    @classmethod
    def available(cls) -> list[str]:
        return list(cls._registry.keys())
