#!/bin/bash
# safety_check.sh — コード変更後に毎回実行する安全チェック

echo "=== 🐛 BTC Research Corp. 安全チェック ==="

FAIL=0

# 1. 鉄のルール違反チェック（禁止ワード検出）
echo "[1/3] 禁止ワード検出..."
if [ -d "src" ]; then
    # コメント行・docstring行・ルール説明行を除外して実コードのみチェック
    if grep -rn "margin\|leverage\|信用\|レバ" src/ 2>/dev/null | grep -v "^.*:#" | grep -v "^.*:.*- " | grep -v '^.*:.*"""' | grep -v "^.*:.*'''" | grep -v "^.*:.*⛔" | grep -v "^.*:.*鉄のルール" | grep -v "^.*:.*禁止" | grep -q .; then
        echo "🔴 CRITICAL: 禁止ワード検出！即座にCEO報告"
        FAIL=1
    else
        echo "✅ 禁止ワードなし"
    fi
else
    echo "⏭️  src/ ディレクトリなし（スキップ）"
fi

# 2. DEMO_MODEガード確認
echo "[2/3] DEMO_MODEガード確認..."
if [ -d "src" ]; then
    ORDER_FUNCS=$(grep -rn "def.*order\|def.*trade\|def.*execute" src/ 2>/dev/null | wc -l)
    GUARDED=$(grep -rn "DEMO_MODE" src/ 2>/dev/null | grep -c "if\|assert")
    echo "   注文系関数: ${ORDER_FUNCS}個 / ガード: ${GUARDED}個"
    if [ "$ORDER_FUNCS" -gt 0 ] && [ "$ORDER_FUNCS" -gt "$GUARDED" ]; then
        echo "🟡 WARNING: ガードされていない注文関数の可能性あり"
    else
        echo "✅ ガード確認OK"
    fi
else
    echo "⏭️  src/ ディレクトリなし（スキップ）"
fi

# 3. Python構文チェック
echo "[3/3] Python構文チェック..."
SYNTAX_FAIL=0
for f in $(find . -name "*.py" -not -path "./.git/*" -not -path "./*__pycache__*" 2>/dev/null); do
    python -m py_compile "$f" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "🔴 構文エラー: $f"
        SYNTAX_FAIL=1
    fi
done
if [ $SYNTAX_FAIL -eq 0 ]; then
    echo "✅ 構文チェックOK"
else
    FAIL=1
fi

echo ""
if [ $FAIL -ne 0 ]; then
    echo "🔴 安全チェック失敗。修正が必要です。"
    exit 1
else
    echo "🟢 全チェック通過"
fi
