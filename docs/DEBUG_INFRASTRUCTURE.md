# デバッグインフラ（全社共通基盤）

## 1. Hooks（自動防御壁）

Claude Codeがファイルを編集するたびに自動でチェックが走る。

```json
// .claude/settings.json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "command": "bash scripts/safety_check.sh",
            "timeout": 30000
          }
        ]
      }
    ]
  }
}
```

## 2. ログ設計

```python
# src/logger_config.py
import logging

def setup_logger():
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s'
    )
    file_handler = logging.FileHandler('logs/bot.log')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    logger = logging.getLogger('btc_bot')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger
```

**ログで記録すべき項目:**
- すべてのAPI呼び出し（リクエスト/レスポンス/応答時間）
- すべての売買シグナル（指標値 + 判定理由）
- すべての注文（デモ/実 + 金額 + 結果）
- すべてのエラー（スタックトレース付き）
- DEMO_MODEの状態（起動時に必ずログ出力）

## 3. パイプデバッグ

```bash
# エラーをClaude Codeに直接分析させる
python main.py 2>&1 | tee log.txt | claude

# テスト失敗を分析
pytest --tb=long -v 2>&1 | claude "このテスト失敗の原因を分析して"

# エラーだけ抽出して分析
grep "ERROR\|CRITICAL" logs/bot.log | tail -50 | claude
```

## 4. ディレクトリ構成

```
bot_ver3/
├── .claude/settings.json       ← Hooks設定
├── scripts/
│   ├── safety_check.sh         ← 自動安全チェック
│   └── run_all_tests.sh        ← 全層テスト一括実行
├── src/
│   ├── config.py               ← DEMO_MODE, 各種設定
│   ├── logger_config.py        ← ログ設定
│   ├── api/bitbank_client.py   ← API通信
│   ├── strategy/               ← 戦略実装
│   ├── trading/
│   │   ├── order.py            ← 注文処理（DEMO_MODEガード必須）
│   │   ├── risk_manager.py     ← CFOルールの実装
│   │   └── paper_trade.py      ← 紙取引シミュレーター
│   └── notify/line_notify.py   ← LINE通知
├── tests/
│   ├── layer1_unit/            ← ユニットテスト
│   ├── layer2_integration/     ← 統合テスト
│   ├── layer3_api/             ← APIテスト（モック）
│   ├── layer4_financial/       ← 財務整合性テスト
│   └── layer5_safety/          ← 安全装置テスト（最重要）
├── logs/bot.log
├── docs/
├── CLAUDE.md
└── .env                        ← API鍵（gitignore必須）
```
