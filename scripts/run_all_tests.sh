#!/bin/bash
# run_all_tests.sh — 5層テスト一括実行

echo "🐛 BTC Research Corp. — 全層テスト実行"
echo "========================================="

FAIL=0

echo ""
echo "--- Layer 1: ユニットテスト ---"
pytest tests/layer1_unit/ -v --tb=short 2>/dev/null || FAIL=1

echo ""
echo "--- Layer 2: 統合テスト ---"
pytest tests/layer2_integration/ -v --tb=short 2>/dev/null || FAIL=1

echo ""
echo "--- Layer 3: API統合テスト ---"
pytest tests/layer3_api/ -v --tb=short 2>/dev/null || FAIL=1

echo ""
echo "--- Layer 4: 財務整合性テスト ---"
pytest tests/layer4_financial/ -v --tb=short 2>/dev/null || FAIL=1

echo ""
echo "--- Layer 5: 安全装置テスト（最重要） ---"
pytest tests/layer5_safety/ -v --tb=long 2>/dev/null || FAIL=1

echo ""
echo "--- 安全装置グレップ ---"
if [ -d "src" ]; then
    if grep -rn "margin\|leverage\|信用\|レバ" src/; then
        echo "🔴 CRITICAL: 禁止ワード検出！"
        FAIL=1
    else
        echo "✅ 禁止ワードなし"
    fi
fi

echo ""
if [ -d "src" ]; then
    echo "--- カバレッジ ---"
    pytest --cov=src --cov-report=term-missing -q 2>/dev/null
fi

echo ""
if [ $FAIL -ne 0 ]; then
    echo "🔴 テスト失敗あり。デバッガーレポートを作成してください。"
    exit 1
else
    echo "🟢 全層テスト通過！"
fi
