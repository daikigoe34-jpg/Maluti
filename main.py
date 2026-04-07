"""BTC Research Corp. — マルチエージェント会社シミュレーター

9人のAIエージェントが「会社」のように協力してタスクを遂行する。

フロー:
  サイクル1: 戦略企画 → CEO判断
  サイクル2: CTO設計 → Engineer実装 → Debugger検証
  サイクル3: CFO評価 + 顧客FB → CEOレビュー
  サイクル4: 倫理委員会監査 → 株主レビュー
"""

from __future__ import annotations

import argparse
import sys

import anthropic

from agents import (
    CEOAgent,
    CFOAgent,
    CTOAgent,
    CustomerAgent,
    DebuggerAgent,
    EngineerAgent,
    EthicsAgent,
    ShareholderAgent,
    StrategyAgent,
)
from message_bus import MessageBus


def run_full_cycle(request: str) -> str:
    """9人フルサイクルでリクエストを処理する。"""
    client = anthropic.Anthropic()
    bus = MessageBus()

    # エージェント初期化
    ceo = CEOAgent(client, bus)
    cfo = CFOAgent(client, bus)
    cto = CTOAgent(client, bus)
    engineer = EngineerAgent(client, bus)
    debugger = DebuggerAgent(client, bus)
    strategy = StrategyAgent(client, bus)
    customer = CustomerAgent(client, bus)
    ethics = EthicsAgent(client, bus)
    shareholder = ShareholderAgent(client, bus)

    # ── サイクル1: 調査・方針 ──
    print("📊 [サイクル1] 戦略企画が市場調査中...")
    market_report = strategy.run(request, sender="CEO")

    print("🛒 [サイクル1] 顧客がフィードバック作成中...")
    customer_fb = customer.run(request, sender="CEO")

    print("👔 [サイクル1] CEO が方針を決定中...")
    ceo_plan = ceo.run(
        f"以下の情報を基に方針を決定してください:\n\n"
        f"【ユーザーの依頼】\n{request}\n\n"
        f"【戦略企画レポート】\n{market_report}\n\n"
        f"【顧客フィードバック】\n{customer_fb}",
        sender="user",
    )

    # ── サイクル2: 開発 ──
    print("🔧 [サイクル2] CTO が設計中...")
    cto_design = cto.run(ceo_plan, sender="CEO")

    print("💻 [サイクル2] エンジニアが実装中...")
    eng_output = engineer.run(cto_design, sender="CTO")

    print("🐛 [サイクル2] デバッガーが検証中...")
    debug_report = debugger.run(eng_output, sender="Engineer")

    # バグ発見時: 1回だけ修正ループ
    if "FAIL" in debug_report.upper() or "失敗" in debug_report or "NG" in debug_report:
        print("🔧 [サイクル2] バグ検出 → エンジニアが修正中...")
        eng_output = engineer.run(
            f"デバッガーから以下の指摘がありました。修正してください:\n\n{debug_report}\n\n元の成果物:\n{eng_output}",
            sender="Debugger",
        )
        print("🐛 [サイクル2] デバッガーが再検証中...")
        debug_report = debugger.run(eng_output, sender="Engineer")

    # CTO レビュー
    print("🔧 [サイクル2] CTO がコードレビュー中...")
    cto_review = cto.run(
        f"エンジニアの成果物をレビューしてください:\n\n{eng_output}\n\nデバッガーの検証結果:\n{debug_report}",
        sender="Engineer",
    )

    # ── サイクル3: 評価 ──
    print("💰 [サイクル3] CFO がリスク評価中...")
    cfo_report = cfo.run(
        f"以下の開発成果に対してリスク・財務評価を行ってください:\n\n"
        f"【CEO方針】\n{ceo_plan}\n\n【CTO設計】\n{cto_design}\n\n【実装結果】\n{eng_output}",
        sender="CEO",
    )

    print("👔 [サイクル3] CEO が最終レビュー中...")
    ceo_review = ceo.run(
        f"全部門の報告を統合し、最終レビューを行ってください:\n\n"
        f"【CTO レビュー】\n{cto_review}\n\n"
        f"【デバッガーレポート】\n{debug_report}\n\n"
        f"【CFO レポート】\n{cfo_report}\n\n"
        f"【顧客FB】\n{customer_fb}",
        sender="system",
    )

    # ── サイクル4: ガバナンス ──
    print("⚖️ [サイクル4] 倫理委員会が監査中...")
    ethics_report = ethics.run(
        f"以下の全プロセスを監査してください:\n\n{bus.get_history()}",
        sender="system",
    )

    print("👑 [サイクル4] 株主がレビュー中...")
    shareholder_review = shareholder.run(
        f"社長の判断をレビューしてください:\n\n"
        f"【CEO最終レビュー】\n{ceo_review}\n\n"
        f"【倫理委員会レポート】\n{ethics_report}",
        sender="system",
    )

    # ── 最終レポート ──
    final_report = (
        "=" * 60 + "\n"
        "  🏢 BTC Research Corp. — 全社レポート\n"
        + "=" * 60 + "\n\n"
        f"{ceo_review}\n\n"
        "---\n\n"
        f"{cfo_report}\n\n"
        "---\n\n"
        f"{ethics_report}\n\n"
        "---\n\n"
        f"{shareholder_review}\n"
    )

    return final_report


def run_lite(request: str) -> str:
    """3人体制（CEO + CTO + Engineer）の軽量モード。"""
    client = anthropic.Anthropic()
    bus = MessageBus()

    ceo = CEOAgent(client, bus)
    cto = CTOAgent(client, bus)
    engineer = EngineerAgent(client, bus)

    print("👔 CEO が方針を決定中...")
    plan = ceo.run(request, sender="user")

    print("🔧 CTO が設計中...")
    design = cto.run(plan, sender="CEO")

    print("💻 エンジニアが実装中...")
    output = engineer.run(design, sender="CTO")

    return f"👔 CEO方針:\n{plan}\n\n🔧 CTO設計:\n{design}\n\n💻 実装結果:\n{output}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="BTC Research Corp. マルチエージェント会社シミュレーター"
    )
    parser.add_argument("request", nargs="*", help="依頼内容")
    parser.add_argument(
        "--mode",
        choices=["full", "lite"],
        default="full",
        help="full: 9人フル / lite: 3人体制 (default: full)",
    )
    args = parser.parse_args()

    if args.request:
        request = " ".join(args.request)
    else:
        print("=" * 50)
        print("  🏢 BTC Research Corp.")
        print("  マルチエージェント会社シミュレーター")
        print("=" * 50)
        print(f"  モード: {args.mode}")
        print()
        request = input("依頼内容を入力してください: ")

    if not request.strip():
        print("依頼内容が空です。終了します。")
        return

    print()
    if args.mode == "full":
        report = run_full_cycle(request)
    else:
        report = run_lite(request)

    print()
    print(report)


if __name__ == "__main__":
    main()
