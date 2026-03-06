#!/bin/bash
# ============================================================
# YouTube PDCA 自動運用 - launchd セットアップスクリプト
# 実行方法: bash setup/setup_launchd.sh
# ============================================================
set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLIST_SRC="$PROJECT_DIR/setup/com.youtube-pdca.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.youtube-pdca.plist"
VENV_DIR="$PROJECT_DIR/venv"
VENV_PYTHON="$VENV_DIR/bin/python3"

echo "============================================================"
echo "  YouTube PDCA 自動運用 セットアップ"
echo "============================================================"
echo "  プロジェクトディレクトリ: $PROJECT_DIR"
echo ""

# ── Step 1: venv の作成 ──
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 仮想環境を作成中..."
    python3 -m venv "$VENV_DIR"
    echo "✅ 仮想環境作成完了"
else
    echo "✅ 仮想環境は既に存在します"
fi

# ── Step 2: 依存パッケージのインストール ──
echo ""
echo "📥 依存パッケージをインストール中..."
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet -r "$PROJECT_DIR/requirements.txt"
echo "✅ パッケージインストール完了"

# ── Step 3: credentials.json の確認 ──
echo ""
if [ ! -f "$PROJECT_DIR/credentials.json" ]; then
    echo "⚠️  credentials.json が見つかりません"
    echo ""
    echo "   以下の手順で取得してください:"
    echo "   1. https://console.cloud.google.com/apis/credentials にアクセス"
    echo "   2. プロジェクトを作成（または既存を選択）"
    echo "   3. YouTube Data API v3 を有効化"
    echo "   4. OAuth 2.0 クライアントID を作成（アプリの種類: デスクトップ）"
    echo "   5. JSONをダウンロードして $PROJECT_DIR/credentials.json に配置"
    echo ""
    echo "   ⚠️  セットアップを続けますが、credentials.json がないと動画アップロードができません"
else
    echo "✅ credentials.json 確認済み"
fi

# ── Step 4: output/ logs/ ディレクトリの作成 ──
echo ""
mkdir -p "$PROJECT_DIR/output/audio" \
         "$PROJECT_DIR/output/images" \
         "$PROJECT_DIR/output/video" \
         "$PROJECT_DIR/logs"
echo "✅ ディレクトリ作成完了"

# ── Step 5: plistファイルのパス置換 ──
echo ""
echo "⚙️  launchd plist を設定中..."

TMP_PLIST=$(mktemp /tmp/com.youtube-pdca.XXXXXX.plist)
sed \
    -e "s|VENV_PYTHON_PATH|$VENV_PYTHON|g" \
    -e "s|PROJECT_DIR|$PROJECT_DIR|g" \
    -e "s|HOME_DIR|$HOME|g" \
    "$PLIST_SRC" > "$TMP_PLIST"

# ── Step 6: LaunchAgents にコピー ──
mkdir -p "$HOME/Library/LaunchAgents"
cp "$TMP_PLIST" "$PLIST_DST"
rm "$TMP_PLIST"
echo "✅ plist コピー完了: $PLIST_DST"

# ── Step 7: launchd に登録 ──
echo ""
echo "🚀 launchd に登録中..."

# 既に登録されている場合はアンロード
launchctl unload "$PLIST_DST" 2>/dev/null || true
launchctl load -w "$PLIST_DST"

echo "✅ launchd 登録完了"

# ── Step 8: 動作確認 ──
echo ""
echo "============================================================"
echo "  ✅ セットアップ完了！"
echo "============================================================"
echo ""
echo "  📅 毎日09:00に自動実行されます"
echo "  📝 ログ: $PROJECT_DIR/logs/"
echo ""
echo "  手動で今すぐ実行する場合:"
echo "  $ $VENV_PYTHON $PROJECT_DIR/scripts/daily_cycle.py"
echo ""
echo "  停止する場合:"
echo "  $ launchctl unload $PLIST_DST"
echo ""
echo "  再開する場合:"
echo "  $ launchctl load -w $PLIST_DST"
echo "============================================================"

# ── 初回認証の案内 ──
if [ ! -f "$PROJECT_DIR/token.json" ]; then
    echo ""
    echo "  ⚠️  初回実行時にブラウザが起動してGoogle認証が必要です"
    echo "  手動で一度実行して認証を完了させてください:"
    echo ""
    echo "  $ $VENV_PYTHON $PROJECT_DIR/scripts/daily_cycle.py"
    echo ""
fi
