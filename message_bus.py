"""MessageBus — エージェント間通信のログ基盤。"""

from __future__ import annotations

import json
from datetime import datetime, timezone


class MessageBus:
    """全エージェント間のメッセージを記録し、ガバナンス監査に使う。"""

    def __init__(self) -> None:
        self._log: list[dict[str, str]] = []

    def send(self, from_agent: str, to_agent: str, content: str) -> None:
        self._log.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "from": from_agent,
            "to": to_agent,
            "content": content,
        })

    def get_history(self, *, agents: list[str] | None = None) -> str:
        """全やり取りを文字列で返す。agentsを指定すると絞り込み可能。"""
        lines: list[str] = []
        for msg in self._log:
            if agents and msg["from"] not in agents and msg["to"] not in agents:
                continue
            lines.append(
                f"[{msg['timestamp']}] {msg['from']} → {msg['to']}\n{msg['content']}"
            )
        return "\n\n---\n\n".join(lines)

    def get_messages_by(self, agent: str) -> list[dict[str, str]]:
        """特定エージェントが送信したメッセージを取得。"""
        return [m for m in self._log if m["from"] == agent]

    def export_json(self) -> str:
        """監査用にJSON形式でエクスポート。"""
        return json.dumps(self._log, ensure_ascii=False, indent=2)

    def __len__(self) -> int:
        return len(self._log)
