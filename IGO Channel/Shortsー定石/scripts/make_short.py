#!/usr/bin/env python3
"""縦型の Shorts（1080×1920）を spec.json から生成する。盤面・音声は make_video.py と共通。

使い方:
    python make_short.py ../videos/s01_hamete/spec.json

spec は make_video.py と同じ形式で、加えて hook（画面上部に固定する一文）を持つ。
出力（spec.json と同じディレクトリの build/）:
    frames/beat_XX.png, audio/beat_XX.wav, video.mp4, thumbnail.png
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from make_video import BOARD_SIZE, BOARD_X, BOARD_Y, GOLD, H, PANEL, W, draw_board, font, run, tts, wrap

SW, SH = 1080, 1920
BOARD_TOP = 360
SUB_TOP = BOARD_TOP + BOARD_SIZE + 30
SUB_W = 920  # 右側の高評価ボタンなどを避ける


def board_image(spec, beat):
    canvas = Image.new("RGB", (W, H), PANEL)
    draw_board(canvas, beat.get("base", spec["base"]), beat.get("moves", ""), beat.get("marks", []),
               beat.get("cross", []), beat.get("good", []))
    return canvas.crop((BOARD_X, BOARD_Y, BOARD_X + BOARD_SIZE, BOARD_Y + BOARD_SIZE))


def render_beat(spec, beat):
    img = Image.new("RGB", (SW, SH), PANEL)
    d = ImageDraw.Draw(img)
    d.text((SW // 2, 110), spec["hook"], font=font(8, 64), fill=GOLD, anchor="mm")
    y = 180
    cap_font = font(8, 66)
    for line in wrap(beat.get("caption", ""), cap_font, SW - 80):
        d.text((SW // 2, y + 40), line, font=cap_font, fill=(255, 255, 255), anchor="mm")
        y += 84
    img.paste(board_image(spec, beat), ((SW - BOARD_SIZE) // 2, BOARD_TOP))
    s_font = font(6, 46)
    lines = wrap(beat["sub"], s_font, SUB_W - 40)
    d.rounded_rectangle([40, SUB_TOP, 40 + SUB_W, SUB_TOP + 40 + 66 * len(lines)], radius=18, fill=(8, 14, 22))
    for i, line in enumerate(lines):
        d.text((60, SUB_TOP + 20 + 66 * i), line, font=s_font, fill=(255, 255, 255))
    return img


def main(spec_path):
    spec_path = Path(spec_path).resolve()
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    build = spec_path.parent / "build"
    for sub in ("frames", "audio", "segments"):
        (build / sub).mkdir(parents=True, exist_ok=True)

    voice = spec["voice"]
    t = 0.0
    seg_list = []
    for i, beat in enumerate(spec["beats"]):
        png = build / "frames" / f"beat_{i:02d}.png"
        wav = build / "audio" / f"beat_{i:02d}.wav"
        seg = build / "segments" / f"beat_{i:02d}.mp4"
        render_beat(spec, beat).save(png)
        dur = tts(beat.get("say", beat["sub"]), wav, voice["speaker"], voice["speed"])
        run(["ffmpeg", "-y", "-loop", "1", "-framerate", "30", "-i", str(png), "-i", str(wav),
             "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p", "-r", "30",
             "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-t", f"{dur:.3f}", str(seg)])
        t += dur
        seg_list.append(seg)

    concat = build / "segments" / "list.txt"
    concat.write_text("".join(f"file '{p}'\n" for p in seg_list))
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy",
         "-movflags", "+faststart", str(build / "video.mp4")])
    Image.open(build / "frames" / "beat_00.png").save(build / "thumbnail.png")
    (build / "chapters.txt").write_text("", encoding="utf-8")  # upload.py が読む。Shorts にチャプターはない
    print(f"done: {build / 'video.mp4'}  ({t:.1f}s)")


if __name__ == "__main__":
    main(sys.argv[1])
