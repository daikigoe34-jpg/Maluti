# Maluti - マルチエージェント会社シミュレーター

複数のAIエージェントが「会社」のように協力してタスクを遂行するシステムです。

## 組織構成

```
ユーザー
  │
  ▼
CEO（社長）── 戦略立案・全体指揮
  │
  ▼
PM（マネージャー）── タスク分解・管理
  │
  ▼
Engineer（エンジニア）── 技術的な実装
  │
  ▼
Reviewer（レビュアー）── 品質チェック
  │          │
  │        要修正 → Engineerに差し戻し（1回）
  ▼
Reporter（広報）── 最終レポート作成
  │
  ▼
ユーザー
```

## セットアップ

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-api-key"
```

## 使い方

```bash
# 対話モード
python main.py

# コマンドライン引数で指定
python main.py "Todoアプリを設計してください"
```

## 仕組み

1. **CEO** がユーザーの依頼を分析し、高レベルな計画を立てる
2. **PM** が計画を具体的なタスクリストに分解
3. **Engineer** がタスクを実装
4. **Reviewer** が成果物をレビュー（問題があれば1回差し戻し）
5. **Reporter** が全体のやり取りをもとにユーザー向けレポートを作成
