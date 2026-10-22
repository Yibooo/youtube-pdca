#!/bin/bash
# ============================================================
# YouTube PDCA - VOICEVOXエンジン起動 + 日次サイクル実行
# launchd の ProgramArguments から呼び出される
# ============================================================
set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_PYTHON="$PROJECT_DIR/venv/bin/python3"
VOICEVOX_ENGINE="$HOME/voicevox/macos-arm64/run"
VOICEVOX_LOG="/tmp/voicevox.log"

echo "🚀 YouTube PDCA 起動: $(date)"

# ── Step 1: VOICEVOXエンジンが起動していなければ起動 ──
if curl -s --max-time 3 http://127.0.0.1:50021/version > /dev/null 2>&1; then
    echo "✅ VOICEVOXエンジン起動済み"
else
    echo "🔊 VOICEVOXエンジンを起動中..."
    if [ -f "$VOICEVOX_ENGINE" ]; then
        "$VOICEVOX_ENGINE" --host 127.0.0.1 --port 50021 >> "$VOICEVOX_LOG" 2>&1 &
        VOICEVOX_PID=$!
        echo "$VOICEVOX_PID" > /tmp/voicevox.pid

        # 最大60秒待機
        for i in $(seq 1 60); do
            sleep 1
            if curl -s --max-time 2 http://127.0.0.1:50021/version > /dev/null 2>&1; then
                echo "✅ VOICEVOXエンジン起動完了 (${i}秒)"
                break
            fi
            if [ "$i" -eq 60 ]; then
                echo "⚠️  VOICEVOXエンジンの起動タイムアウト。macOS TTS にフォールバックします。"
            fi
        done
    else
        echo "⚠️  VOICEVOXエンジンが見つかりません: $VOICEVOX_ENGINE"
        echo "     macOS TTS にフォールバックします。"
    fi
fi

# ── Step 2: 日次サイクルを実行 ──
echo "📅 日次サイクル開始..."
"$VENV_PYTHON" "$PROJECT_DIR/scripts/daily_cycle.py"

echo "✅ 完了: $(date)"
