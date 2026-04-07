"""BaseAgent — 全エージェントの基底クラス。"""

from __future__ import annotations

from typing import TYPE_CHECKING

import anthropic

if TYPE_CHECKING:
    from message_bus import MessageBus

DEFAULT_MODEL = "claude-sonnet-4-20250514"


class BaseAgent:
    """各エージェントはこのクラスを継承し、role と system_prompt を定義する。"""

    role: str = "agent"
    system_prompt: str = "You are a helpful assistant."

    def __init__(self, client: anthropic.Anthropic, bus: MessageBus) -> None:
        self.client = client
        self.bus = bus

    def run(self, message: str, *, sender: str = "system") -> str:
        """メッセージを受け取り、LLMで処理して結果を返す。"""
        self.bus.send(sender, self.role, message)

        response = self.client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=4096,
            system=self.system_prompt,
            messages=[{"role": "user", "content": message}],
        )

        result = response.content[0].text
        self.bus.send(self.role, sender, result)
        return result
