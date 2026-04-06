from __future__ import annotations

import anthropic

from message_bus import MessageBus

DEFAULT_MODEL = "claude-sonnet-4-20250514"


class BaseAgent:
    """全エージェントの基底クラス。"""

    role: str = "agent"
    system_prompt: str = "You are a helpful assistant."

    def __init__(self, client: anthropic.Anthropic, bus: MessageBus) -> None:
        self.client = client
        self.bus = bus

    def run(self, message: str, *, sender: str = "system") -> str:
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
