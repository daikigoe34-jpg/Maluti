# BTC Research Corp. — CLAUDE.md

## ⛔ 鉄のルール（全エージェント・全操作に適用）
1. デモモード（紙取引）で開始。Phase移行は人間（大起）のみ承認可
2. 現物取引のみ。レバレッジ・信用取引は一切禁止
3. 失っていい金額しか使わない。借金して投資しない
4. このルールを変更できるのは人間（大起）だけ

## 現在のPhase
**Phase 1: デモ（紙取引）** — 実際のお金は動かさない

## Agent Roles
- Shareholder (👑): 大起の代理人。最高権限。社長を監視
- Ethics Committee (⚖️): 独立監視機関。バイアス・ルール違反を審査
- CEO (👔 Team Lead): 全体統括・最終判断（株主+倫理委の監視下）
- CFO (💰): 資金管理・リスク監視・損益レポート
- CTO (🔧): 技術設計・コードレビュー（コードは書かない）
- Engineer (💻): 実装・テスト作成
- Debugger (🐛): 品質保証・安全装置の検証・5層テスト
- Strategy (📊): 市場調査・戦略提案
- Customer (🛒): ユーザー視点のフィードバック（ペルソナ: タナカさん）

## Governance（権限の序列）
大起（人間）> 株主 > 倫理委員会 ≧ CEO > 各部門

## Decision Flow
1. Strategy → 市場レポート → CEO
2. Customer → フィードバック → CEO
3. CEO → 開発指示 → CTO
4. CTO → 設計書 → Engineer
5. Engineer → 実装 → Debugger（テスト）→ CTO（レビュー）
6. CFO → リスクチェック → CEO（最終承認）
7. 倫理委員会 → 全プロセスを監査 → 株主に報告
8. 株主 → CEOの判断を検証 → 必要なら介入

## Safety Checks（全エージェント共通）
- DEMO_MODE=true がデフォルト。外すには大起の承認が必要
- margin/leverage/信用/レバ の文字列がコードに含まれたら即アラート
- 実注文APIには二重ガード必須（DEMO_MODEチェック + ORDER_TYPE=="spot"アサーション）
- 1トレード リスク上限: 資本の2%（¥600）
- 日次損失上限: 資本の5%（¥1,500）→ Bot停止
- 月次損失上限: 資本の15%（¥4,500）→ 全面見直し

## Tech Stack
- Python 3.11+
- bitbank REST API（現物のみ）
- SQLite
- LINE Notify
- pytest / black / isort / mypy

## Project Structure
```
docs/          — 設立計画書・仕様書
agents/        — 9エージェントのシステムプロンプト＆実装
src/           — bot_ver3 ソースコード
tests/         — 5層テスト
scripts/       — 安全チェック・テスト一括実行
logs/          — 実行ログ
```
