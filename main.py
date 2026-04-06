"""マルチエージェント会社シミュレーター

ユーザーのリクエストを「会社」のように複数エージェントが協力して処理する。

フロー: ユーザー → CEO → PM → Engineer → Reviewer → (修正) → Reporter → ユーザー
"""

from __future__ import annotations

import sys

import anthropic

from agents import CEOAgent, PMAgent, EngineerAgent, ReviewerAgent, ReporterAgent
from message_bus import MessageBus


def run_company(request: str) -> str:
    """会社全体でリクエストを処理し、最終レポートを返す。"""
    client = anthropic.Anthropic()
    bus = MessageBus()

    ceo = CEOAgent(client, bus)
    pm = PMAgent(client, bus)
    engineer = EngineerAgent(client, bus)
    reviewer = ReviewerAgent(client, bus)
    reporter = ReporterAgent(client, bus)

    # 1. CEO: 戦略を立てる
    print("🏢 CEO が計画を策定中...")
    plan = ceo.run(request, sender="user")

    # 2. PM: タスクに分解
    print("📋 PM がタスクを分解中...")
    tasks = pm.run(plan, sender="CEO")

    # 3. Engineer: 実装
    print("💻 Engineer が実装中...")
    output = engineer.run(tasks, sender="PM")

    # 4. Reviewer: レビュー
    print("🔍 Reviewer がレビュー中...")
    review = reviewer.run(output, sender="Engineer")

    # 5. 要修正の場合、1回だけリトライ
    if "要修正" in review:
        print("🔧 Engineer が修正中...")
        revision_prompt = f"以下のレビュー指摘に基づいて修正してください:\n\n{review}\n\n元の成果物:\n{output}"
        output = engineer.run(revision_prompt, sender="Reviewer")

        print("🔍 Reviewer が再レビュー中...")
        review = reviewer.run(output, sender="Engineer")

    # 6. Reporter: 最終報告
    print("📝 Reporter がレポート作成中...")
    history = bus.get_history()
    report = reporter.run(
        f"以下が社内の全やり取りです。ユーザーへの最終レポートを作成してください:\n\n{history}",
        sender="system",
    )

    return report


def main() -> None:
    if len(sys.argv) > 1:
        request = " ".join(sys.argv[1:])
    else:
        print("=" * 50)
        print("  🏢 マルチエージェント会社シミュレーター")
        print("=" * 50)
        print()
        request = input("依頼内容を入力してください: ")

    if not request.strip():
        print("依頼内容が空です。終了します。")
        return

    print()
    report = run_company(request)
    print()
    print("=" * 50)
    print("  📊 最終レポート")
    print("=" * 50)
    print()
    print(report)


if __name__ == "__main__":
    main()
