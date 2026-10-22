#!/usr/bin/env python3
"""
動画生成モジュール
各スライド画像 + 音声の尺に合わせてスライドショー動画を生成する。
既存 youtube-automation の 3_build_video.py をベースに拡張。
"""
import subprocess, sys, os, tempfile
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).parent.parent
OUTPUT_DIR = ROOT_DIR / "output" / "video"


def _build_slide_segment(img_path: str, duration: float, seg_path: str) -> bool:
    """
    1枚のスライド画像 + 指定秒数で動画セグメントを生成する。
    duration秒間の静止画動画（音声なし）を作成する。
    """
    cmd = [
        "ffmpeg",
        "-loop", "1", "-i", img_path,
        "-t", str(duration),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-vf", "scale=1920:1080:flags=lanczos",
        "-r", "1",   # 1fps で容量節約
        "-crf", "28", "-preset", "fast",
        seg_path, "-y", "-v", "quiet"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def _concat_segments(seg_paths: list, audio_path: str, output_path: str) -> bool:
    """
    複数の映像セグメントを結合し、音声を乗せる。
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False
    ) as tf:
        for p in seg_paths:
            tf.write(f"file '{p}'\n")
        concat_file = tf.name

    try:
        # ① 映像を連結
        tmp_video = output_path.replace(".mp4", "_novid.mp4")
        cmd_concat = [
            "ffmpeg",
            "-f", "concat", "-safe", "0",
            "-i", concat_file,
            "-c", "copy",
            tmp_video, "-y", "-v", "quiet"
        ]
        r = subprocess.run(cmd_concat, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"❌ 映像結合エラー: {r.stderr}")
            return False

        # ② 映像 + 音声を合わせる
        cmd_av = [
            "ffmpeg",
            "-i", tmp_video,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            "-movflags", "+faststart",
            output_path, "-y", "-v", "quiet", "-stats"
        ]
        r2 = subprocess.run(cmd_av, capture_output=True, text=True)
        if r2.returncode != 0:
            print(f"❌ 音声合成エラー: {r2.stderr}")
            return False

        # 中間ファイルを削除
        if os.path.exists(tmp_video):
            os.remove(tmp_video)

        return True
    finally:
        os.unlink(concat_file)


def build(image_paths: list, audio_path: str, durations: list, theme_id: str) -> str:
    """
    スライド画像リスト + 音声 + 尺リストからMP4を生成する。
    Args:
        image_paths: 各スライドPNGのパスリスト
        audio_path: 結合済みWAVのパス
        durations: 各スライドの音声長（秒）のリスト
        theme_id: テーマID（ファイル名に使用）
    Returns:
        str: 生成されたMP4のパス
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = OUTPUT_DIR / f"{theme_id}_{ts}.mp4"

    # スライド数と尺の調整
    n = min(len(image_paths), len(durations))
    image_paths = image_paths[:n]
    durations   = durations[:n]

    total_sec = sum(durations)
    print(f"🎬 動画生成中... ({n}スライド / 合計{total_sec/60:.1f}分)")

    tmp_dir = OUTPUT_DIR / f"tmp_{theme_id}_{ts}"
    tmp_dir.mkdir(exist_ok=True)

    # 各スライドのセグメント映像を生成
    seg_paths = []
    for i, (img, dur) in enumerate(zip(image_paths, durations)):
        seg = str(tmp_dir / f"seg{i+1:02d}.mp4")
        ok = _build_slide_segment(img, dur, seg)
        if ok:
            seg_paths.append(seg)
            print(f"   📹 Slide {i+1}/{n} ({dur:.1f}秒)", end="\r")
        else:
            print(f"   ⚠️  Slide {i+1}: セグメント生成失敗、スキップ")

    print()

    # 全セグメントを結合 + 音声を合わせる
    ok = _concat_segments(seg_paths, audio_path, str(out))

    # 一時ファイルを削除
    import shutil
    shutil.rmtree(str(tmp_dir))

    if not ok:
        raise RuntimeError("動画生成に失敗しました")

    size_mb = out.stat().st_size // 1024 // 1024
    print(f"✅ 動画完了: {out.name} ({size_mb}MB)")
    return str(out)


if __name__ == "__main__":
    # 単体テスト用（既存スクリプトが存在する場合に実行）
    import sys, json
    sys.path.insert(0, str(ROOT_DIR / "scripts"))
    from generate_script import generate as gen_script
    from generate_slides  import generate as gen_slides
    from generate_tts     import generate as gen_tts

    theme = sys.argv[1] if len(sys.argv) > 1 else "nisa_basics"
    script = gen_script(theme)
    imgs   = gen_slides(script["slides"], theme)
    audio, durs = gen_tts(script["slides"], theme)
    mp4    = build(imgs, audio, durs, theme)
    print(f"出力: {mp4}")
