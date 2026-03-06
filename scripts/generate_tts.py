#!/usr/bin/env python3
"""
TTS音声生成モジュール
macOS の say コマンドを使って各スライドのナレーションを生成し、
FFmpegで1つのWAVファイルに結合する。
"""
import subprocess, sys, os, tempfile
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).parent.parent
OUTPUT_DIR = ROOT_DIR / "output" / "audio"


def _load_config():
    import json
    with open(ROOT_DIR / "config.json", encoding="utf-8") as f:
        return json.load(f)


def _check_voice(voice: str) -> str:
    """指定ボイスが使えるか確認。使えない場合はフォールバック。"""
    result = subprocess.run(
        ["say", "-v", "?"], capture_output=True, text=True
    )
    voices = result.stdout
    if voice in voices:
        return voice
    # フォールバック（日本語ボイス候補）
    for fallback in ["Kyoko", "O-ren", "Otoya"]:
        if fallback in voices:
            print(f"⚠️  ボイス '{voice}' が見つからないため '{fallback}' を使用します")
            return fallback
    # 最終フォールバック
    print("⚠️  日本語ボイスが見つかりません。デフォルトボイスを使用します")
    return None


def _narration_to_aiff(text: str, voice: str, rate: int, out_path: str) -> bool:
    """1つのナレーションテキストをAIFFに変換する。"""
    # 長いテキストは一時ファイル経由で渡す
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", encoding="utf-8", delete=False
    ) as tf:
        tf.write(text)
        tmp_txt = tf.name

    try:
        cmd = ["say", "-r", str(rate), "-o", out_path]
        if voice:
            cmd += ["-v", voice]
        cmd += ["-f", tmp_txt]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            print(f"❌ sayコマンドエラー: {result.stderr}")
            return False
        return True
    finally:
        os.unlink(tmp_txt)


def _aiff_to_wav(aiff_path: str, wav_path: str) -> bool:
    """AIFFをWAV（44100Hz, ステレオ）に変換する。"""
    cmd = [
        "ffmpeg", "-i", aiff_path,
        "-ar", "44100", "-ac", "2",
        wav_path, "-y", "-v", "quiet"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def _concat_wavs(wav_paths: list, output_path: str) -> bool:
    """複数のWAVファイルを1つに連結する。"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False
    ) as tf:
        for p in wav_paths:
            tf.write(f"file '{p}'\n")
        concat_file = tf.name

    try:
        cmd = [
            "ffmpeg", "-f", "concat", "-safe", "0",
            "-i", concat_file,
            "-c", "copy", output_path,
            "-y", "-v", "quiet"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
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
        return 0.0
    import json
    data = json.loads(result.stdout)
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "audio":
            return float(stream.get("duration", 0))
    return 0.0


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
    voice = _check_voice(tts_cfg.get("voice", "Kyoko"))
    rate = tts_cfg.get("rate", 175)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    tmp_dir = OUTPUT_DIR / f"tmp_{theme_id}_{ts}"
    tmp_dir.mkdir(exist_ok=True)

    segment_wavs = []
    durations = []

    print(f"🎤 TTS生成中 (voice={voice}, rate={rate})...")

    for i, slide in enumerate(slides_data):
        narration = slide.get("narration", "")
        if not narration:
            narration = slide.get("heading", "スライド")

        aiff_path = str(tmp_dir / f"slide{i+1:02d}.aiff")
        wav_path  = str(tmp_dir / f"slide{i+1:02d}.wav")

        print(f"   🔊 Slide {i+1}/{len(slides_data)}: {len(narration)}文字", end=" ... ")

        ok = _narration_to_aiff(narration, voice, rate, aiff_path)
        if not ok:
            print("❌ AIFF生成失敗")
            continue

        ok = _aiff_to_wav(aiff_path, wav_path)
        if not ok:
            print("❌ WAV変換失敗")
            continue

        dur = _get_audio_duration(wav_path)
        durations.append(dur)
        segment_wavs.append(wav_path)
        print(f"✅ ({dur:.1f}秒)")

    # 全スライドを1つのWAVに結合
    final_wav = str(OUTPUT_DIR / f"{theme_id}_narration_{ts}.wav")
    if not _concat_wavs(segment_wavs, final_wav):
        raise RuntimeError("WAV結合に失敗しました")

    total_dur = sum(durations)
    print(f"✅ 音声生成完了: {final_wav}")
    print(f"   合計尺: {total_dur/60:.1f}分 ({total_dur:.0f}秒)")

    # 一時ファイルを削除
    import shutil
    shutil.rmtree(str(tmp_dir))

    return final_wav, durations


if __name__ == "__main__":
    import json, sys
    sys.path.insert(0, str(ROOT_DIR / "scripts"))
    from generate_script import generate as gen_script

    theme = sys.argv[1] if len(sys.argv) > 1 else "nisa_basics"
    script = gen_script(theme)
    wav_path, durs = generate(script["slides"], theme)
    print(f"出力: {wav_path}")
    print(f"尺: {durs}")
