from __future__ import annotations


class MessageBus:
    """エージェント間のメッセージを記録するシンプルなログ。"""

    def __init__(self) -> None:
        self._log: list[dict[str, str]] = []

    def send(self, from_agent: str, to_agent: str, content: str) -> None:
        self._log.append({"from": from_agent, "to": to_agent, "content": content})

    def get_history(self) -> str:
        lines: list[str] = []
        for msg in self._log:
            lines.append(f"[{msg['from']} → {msg['to']}]\n{msg['content']}")
        return "\n\n---\n\n".join(lines)

    def __len__(self) -> int:
        return len(self._log)
