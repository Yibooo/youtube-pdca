#!/usr/bin/env python3
"""
TTS音声生成モジュール（VOICEVOX版）
VOICEVOX Engine (localhost:50021) を使って各スライドのナレーションを生成し、
FFmpegで1つのWAVファイルに結合する。

VOICEVOX Engine を事前に起動しておく必要があります：
  ~/voicevox/macos-arm64/run --host 127.0.0.1 --port 50021 &
"""
import subprocess, sys, os, json, tempfile, time, urllib.request, urllib.parse, urllib.error
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).parent.parent
OUTPUT_DIR = ROOT_DIR / "output" / "audio"

VOICEVOX_HOST = "http://127.0.0.1:50021"
VOICEVOX_ENGINE_PATH = Path.home() / "voicevox" / "macos-arm64" / "run"


def _load_config():
    with open(ROOT_DIR / "config.json", encoding="utf-8") as f:
        return json.load(f)


def _is_voicevox_running() -> bool:
    """VOICEVOXエンジンが起動済みか確認する。"""
    try:
        req = urllib.request.urlopen(f"{VOICEVOX_HOST}/version", timeout=3)
        return req.status == 200
    except Exception:
        return False


def _start_voicevox():
    """VOICEVOXエンジンをバックグラウンドで起動し、Ready になるまで待つ。"""
    if not VOICEVOX_ENGINE_PATH.exists():
        raise FileNotFoundError(
            f"VOICEVOXエンジンが見つかりません: {VOICEVOX_ENGINE_PATH}\n"
            "  インストール手順: ~/voicevox/ に macos-arm64 ディレクトリを配置してください"
        )

    print("🚀 VOICEVOXエンジンを起動中...")
    log_path = Path("/tmp/voicevox.log")
    with open(log_path, "a") as logf:
        subprocess.Popen(
            [str(VOICEVOX_ENGINE_PATH), "--host", "127.0.0.1", "--port", "50021"],
            stdout=logf, stderr=logf,
            cwd=str(VOICEVOX_ENGINE_PATH.parent),
        )

    for i in range(60):
        time.sleep(1)
        if _is_voicevox_running():
            print(f"✅ VOICEVOXエンジン起動完了 ({i+1}秒)")
            return
    raise TimeoutError("VOICEVOXエンジンの起動がタイムアウトしました (60秒)")


def _ensure_voicevox():
    """VOICEVOXが起動していなければ自動起動する。"""
    if not _is_voicevox_running():
        _start_voicevox()


def _narration_to_wav(text: str, speaker: int, speed: float, out_path: str) -> bool:
    """
    1つのナレーションテキストをWAVに変換する（VOICEVOX API使用）。

    Args:
        text: ナレーションテキスト
        speaker: VOICEVOXスピーカーID (例: 30 = No.7 アナウンス)
        speed: 読み上げ速度 (例: 1.1 = 少し速め)
        out_path: 出力WAVファイルパス
    Returns:
        bool: 成功したかどうか
    """
    try:
        # Step1: audio_query を取得
        encoded_text = urllib.parse.quote(text)
        query_url = f"{VOICEVOX_HOST}/audio_query?speaker={speaker}&text={encoded_text}"
        req = urllib.request.Request(query_url, method="POST")
        req.add_header("Content-Type", "application/json")

        with urllib.request.urlopen(req, timeout=30) as resp:
            query_data = json.loads(resp.read().decode("utf-8"))

        # 速度調整
        query_data["speedScale"] = speed
        # 音量調整（少し大きめ）
        query_data["volumeScale"] = 1.1
        # 無音部分を少し短く
        query_data["prePhonemeLength"] = 0.05
        query_data["postPhonemeLength"] = 0.1

        # Step2: 音声合成
        synthesis_url = f"{VOICEVOX_HOST}/synthesis?speaker={speaker}"
        body = json.dumps(query_data).encode("utf-8")
        req2 = urllib.request.Request(synthesis_url, data=body, method="POST")
        req2.add_header("Content-Type", "application/json")

        with urllib.request.urlopen(req2, timeout=60) as resp:
            wav_data = resp.read()

        with open(out_path, "wb") as f:
            f.write(wav_data)

        return True

    except urllib.error.URLError as e:
        print(f"❌ VOICEVOX APIエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False


def _concat_wavs(wav_paths: list, output_path: str) -> bool:
    """複数のWAVファイルを1つに連結する（FFmpeg使用）。"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as tf:
        for p in wav_paths:
            tf.write(f"file '{p}'\n")
        concat_file = tf.name

    try:
        cmd = [
            "ffmpeg", "-f", "concat", "-safe", "0",
            "-i", concat_file,
            "-ar", "44100", "-ac", "2",  # 44100Hz ステレオ
            output_path, "-y", "-v", "quiet"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ FFmpeg concat エラー: {result.stderr}")
            return False
        return True
    finally:
        os.unlink(concat_file)


def _get_audio_duration(wav_path: str) -> float:
    """WAVファイルの長さ（秒）を取得する。"""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_streams", wav_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return 5.0  # フォールバック値
    data = json.loads(result.stdout)
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "audio":
            dur = float(stream.get("duration", 5.0))
            return max(dur, 1.0)  # 最低1秒
    return 5.0


def generate(slides_data: list, theme_id: str) -> tuple:
    """
    各スライドのナレーションからTTS音声を生成し、結合したWAVを返す。

    Args:
        slides_data: generate_script.pyのslides配列（各要素に 'narration' キー）
        theme_id: テーマID（ファイル名に使用）
    Returns:
        tuple: (結合WAVパス, 各スライドの音声長さリスト[秒])
    """
    config = _load_config()
    tts_cfg = config.get("tts", {})

    # VOICEVOXスピーカー設定（config.json の voicevox_speaker または デフォルト30）
    speaker = tts_cfg.get("voicevox_speaker", 30)  # 30 = No.7 アナウンス
    speed   = tts_cfg.get("voicevox_speed", 1.15)  # 少し速め（YouTube向け）

    # VOICEVOXエンジンを確認・起動
    _ensure_voicevox()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    tmp_dir = OUTPUT_DIR / f"tmp_{theme_id}_{ts}"
    tmp_dir.mkdir(exist_ok=True)

    segment_wavs = []
    durations = []

    print(f"🎤 VOICEVOX TTS生成中 (speaker={speaker}, speed={speed})...")

    for i, slide in enumerate(slides_data):
        narration = slide.get("narration", "")
        if not narration:
            narration = slide.get("heading", "スライド")

        wav_path = str(tmp_dir / f"slide{i+1:02d}.wav")

        print(f"   🔊 Slide {i+1}/{len(slides_data)}: {len(narration)}文字", end=" ... ", flush=True)

        ok = _narration_to_wav(narration, speaker, speed, wav_path)
        if not ok:
            print("❌ 生成失敗 → ダミー音声で続行")
            # ダミー音声（0.5秒の無音）を生成してスキップしない
            subprocess.run([
                "ffmpeg", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                "-t", "3", wav_path, "-y", "-v", "quiet"
            ])

        dur = _get_audio_duration(wav_path)
        durations.append(dur)
        segment_wavs.append(wav_path)
        print(f"✅ ({dur:.1f}秒)")

    # 全スライドを1つのWAVに結合
    final_wav = str(OUTPUT_DIR / f"{theme_id}_narration_{ts}.wav")
    if not _concat_wavs(segment_wavs, final_wav):
        raise RuntimeError("WAV結合に失敗しました")

    total_dur = sum(durations)
    print(f"✅ VOICEVOX音声生成完了: {final_wav}")
    print(f"   合計尺: {total_dur/60:.1f}分 ({total_dur:.0f}秒)")

    # 一時ファイルを削除
    import shutil
    shutil.rmtree(str(tmp_dir))

    return final_wav, durations


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT_DIR / "scripts"))
    from generate_script import generate as gen_script

    theme = sys.argv[1] if len(sys.argv) > 1 else "nisa_basics"
    script = gen_script(theme)
    wav_path, durs = generate(script["slides"], theme)
    print(f"出力: {wav_path}")
    print(f"尺: {[f'{d:.1f}s' for d in durs]}")
