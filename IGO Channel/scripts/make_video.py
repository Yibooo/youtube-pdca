#!/usr/bin/env python3
"""定石動画を spec.json から生成する（盤面描画 → VOICEVOX 音声 → ffmpeg 結合）。

使い方:
    python make_video.py ../videos/ep01_ikken_takabasami/spec.json

出力（spec.json と同じディレクトリの build/）:
    frames/beat_XX.png, audio/beat_XX.wav, video.mp4, thumbnail.png, chapters.txt

前提: VOICEVOX Engine が http://127.0.0.1:50021 で起動していること、ffmpeg が入っていること。
"""
import json
import subprocess
import sys
import unicodedata
import urllib.parse
import urllib.request
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
COLS = "ABCDEFGHJKLMNOPQRST"
VIEW_COLS = COLS[8:]            # J..T（右端が盤端）
VIEW_ROWS = list(range(19, 8, -1))  # 19..9（上端が盤端）
STAR_POINTS = {"K16", "Q10", "K10", "Q16", "K4", "Q4"}

BOARD_X, BOARD_Y, BOARD_SIZE = 40, 40, 1000
GRID = 88
WOOD = (222, 180, 110)
LINE = (40, 30, 20)
PANEL = (24, 36, 52)
GOLD = (236, 190, 80)
RED = (220, 40, 40)
BLUE = (30, 110, 230)

VOICEVOX = "http://127.0.0.1:50021"
PAUSE_SEC = 0.5


def font(weight, size):
    """ヒラギノ角ゴシック（macOS 標準。ファイル名が NFD なので正規化して探す）"""
    for f in Path("/System/Library/Fonts").iterdir():
        if unicodedata.normalize("NFC", f.name) == f"ヒラギノ角ゴシック W{weight}.ttc":
            return ImageFont.truetype(str(f), size)
    raise FileNotFoundError("ヒラギノ角ゴシックが見つかりません")


def point_xy(pt):
    col, row = pt[0], int(pt[1:])
    ci = VIEW_COLS.index(col)
    ri = VIEW_ROWS.index(row)
    right = BOARD_X + BOARD_SIZE - 70
    top = BOARD_Y + 70
    return right - (len(VIEW_COLS) - 1 - ci) * GRID, top + ri * GRID


def parse_moves(s):
    out = []
    for tok in s.split():
        color, _, mv = tok.rpartition(":")
        out.append((color, mv))
    return out


def neighbors(pt):
    ci, r = COLS.index(pt[0]), int(pt[1:])
    out = []
    for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        c2, r2 = ci + dc, r + dr
        if 0 <= c2 < 19 and 1 <= r2 <= 19:
            out.append(f"{COLS[c2]}{r2}")
    return out


def remove_captured(board, pt):
    """pt に打った直後、呼吸点のなくなった相手の石を取る。"""
    enemy = "W" if board[pt] == "B" else "B"
    for n in neighbors(pt):
        if board.get(n) != enemy:
            continue
        group, stack, libs = {n}, [n], False
        while stack:
            for m in neighbors(stack.pop()):
                if m not in board:
                    libs = True
                elif board[m] == enemy and m not in group:
                    group.add(m)
                    stack.append(m)
        if not libs:
            for g in group:
                del board[g]


def draw_board(img, setup, moves, marks=(), cross=(), good=()):
    d = ImageDraw.Draw(img)
    d.rectangle([BOARD_X, BOARD_Y, BOARD_X + BOARD_SIZE, BOARD_Y + BOARD_SIZE], fill=WOOD)
    x_left, y_top = point_xy(VIEW_COLS[0] + "19")
    x_right, y_bottom = point_xy("T" + str(VIEW_ROWS[-1]))
    # 盤端（上・右）は太線、続いている側（左・下）は枠まで線を伸ばす
    for c in VIEW_COLS:
        x, _ = point_xy(c + "19")
        d.line([x, y_top, x, BOARD_Y + BOARD_SIZE], fill=LINE, width=5 if c == "T" else 2)
    for r in VIEW_ROWS:
        _, y = point_xy("T" + str(r))
        d.line([BOARD_X, y, x_right, y], fill=LINE, width=5 if r == 19 else 2)
    for sp in STAR_POINTS:
        if sp[0] in VIEW_COLS and int(sp[1:]) in VIEW_ROWS:
            x, y = point_xy(sp)
            d.ellipse([x - 8, y - 8, x + 8, y + 8], fill=LINE)

    r = 41
    num_font = font(6, 34)
    board, number = {}, {}
    for c, mv in parse_moves(setup):
        board[mv] = c
    last = None
    for i, (c, mv) in enumerate(parse_moves(moves), 1):
        if mv == "pass":
            continue
        board[mv] = c
        number[mv] = i
        remove_captured(board, mv)
        last = mv
    stones = [(c, mv, number.get(mv)) for mv, c in board.items()]
    for color, mv, n in stones:
        if mv[0] not in VIEW_COLS or int(mv[1:]) not in VIEW_ROWS:
            continue
        x, y = point_xy(mv)
        fill, text = ((15, 15, 15), (255, 255, 255)) if color == "B" else ((250, 250, 250), (15, 15, 15))
        d.ellipse([x - r + 3, y - r + 5, x + r + 3, y + r + 5], fill=(150, 110, 60))  # 影
        d.ellipse([x - r, y - r, x + r, y + r], fill=fill, outline=(0, 0, 0), width=2)
        if n is not None:
            d.text((x, y), str(n), font=num_font, fill=RED if mv == last else text, anchor="mm")

    mark_font = font(8, 52)
    for pt, label in marks:
        x, y = point_xy(pt)
        d.ellipse([x - 34, y - 34, x + 34, y + 34], fill=WOOD)
        d.text((x, y), label, font=mark_font, fill=BLUE, anchor="mm")
    for pt in cross:
        x, y = point_xy(pt)
        d.line([x - 48, y - 48, x + 48, y + 48], fill=RED, width=12)
        d.line([x - 48, y + 48, x + 48, y - 48], fill=RED, width=12)
    for pt in good:
        x, y = point_xy(pt)
        d.ellipse([x - 56, y - 56, x + 56, y + 56], outline=BLUE, width=10)


def wrap(text, fnt, width):
    lines, cur = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(cur)
            cur = ""
        elif fnt.getlength(cur + ch) > width and ch not in "、。，．！？」）ー":  # 行頭禁則：句読点は前の行に残す
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def render_beat(spec, beat):
    img = Image.new("RGB", (W, H), PANEL)
    draw_board(img, beat.get("base", spec["base"]), beat.get("moves", ""), beat.get("marks", []),
               beat.get("cross", []), beat.get("good", []))
    d = ImageDraw.Draw(img)
    px, pw = 1100, 760
    d.text((px, 60), spec["series"], font=font(6, 36), fill=GOLD)
    y = 130
    cap_font = font(8, 64)
    for line in wrap(beat.get("caption", ""), cap_font, pw):
        d.text((px, y), line, font=cap_font, fill=(255, 255, 255))
        y += 84
    y += 30
    b_font = font(6, 40)
    for b in beat.get("bullets", []):
        for i, line in enumerate(wrap(b, b_font, pw - 50)):
            d.text((px + (0 if i == 0 else 50), y), ("● " if i == 0 else "") + line, font=b_font, fill=(230, 235, 245))
            y += 58
        y += 12
    # 字幕
    s_font = font(6, 40)
    sub_lines = wrap(beat["sub"], s_font, pw - 40)
    box_h = 40 + 60 * len(sub_lines)
    top = BOARD_Y + BOARD_SIZE - box_h
    d.rounded_rectangle([px - 20, top, px + pw, BOARD_Y + BOARD_SIZE], radius=18, fill=(8, 14, 22))
    for i, line in enumerate(sub_lines):
        d.text((px, top + 22 + 60 * i), line, font=s_font, fill=(255, 255, 255))
    return img


def render_thumbnail(spec):
    t = spec["thumbnail"]
    img = Image.new("RGB", (W, H), PANEL)
    draw_board(img, spec["base"], t["moves"], t.get("marks", []))
    d = ImageDraw.Draw(img)
    big = font(9, 150)
    lines = wrap(t["headline"], big, 820)
    y = 200
    for line in lines:
        d.text((1080, y), line, font=big, fill=RED, stroke_width=10, stroke_fill=(255, 255, 255))
        y += 190
    d.text((1080, y + 40), t["sub"], font=font(8, 90), fill=(255, 255, 255), stroke_width=6, stroke_fill=BLUE)
    d.text((1080, 940), "囲碁定石", font=font(7, 60), fill=GOLD)
    return img


def tts(text, out_path, speaker, speed):
    q = urllib.parse.urlencode({"text": text, "speaker": speaker})
    req = urllib.request.Request(f"{VOICEVOX}/audio_query?{q}", method="POST")
    query = json.load(urllib.request.urlopen(req, timeout=60))
    query["speedScale"] = speed
    query["postPhonemeLength"] = PAUSE_SEC
    req = urllib.request.Request(f"{VOICEVOX}/synthesis?speaker={speaker}",
                                 data=json.dumps(query).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    out_path.write_bytes(urllib.request.urlopen(req, timeout=120).read())
    with wave.open(str(out_path)) as w:
        return w.getnframes() / w.getframerate()


def run(cmd):
    subprocess.run(cmd, check=True, capture_output=True)


def main(spec_path):
    spec_path = Path(spec_path).resolve()
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    build = spec_path.parent / "build"
    for sub in ("frames", "audio", "segments"):
        (build / sub).mkdir(parents=True, exist_ok=True)

    voice = spec["voice"]
    chapters, t = [], 0.0
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
        if beat.get("chapter"):
            mm, ss = divmod(int(t), 60)
            chapters.append(f"{mm:02d}:{ss:02d} {beat['chapter']}")
        t += dur
        seg_list.append(seg)
        print(f"beat {i:02d}: {dur:5.1f}s  {beat['sub'][:30]}")

    concat = build / "segments" / "list.txt"
    concat.write_text("".join(f"file '{p}'\n" for p in seg_list))
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy",
         "-movflags", "+faststart", str(build / "video.mp4")])
    render_thumbnail(spec).resize((1280, 720)).save(build / "thumbnail.png")
    (build / "chapters.txt").write_text("\n".join(chapters) + "\n", encoding="utf-8")
    print(f"done: {build / 'video.mp4'}  ({t:.1f}s)")
    print("\n".join(chapters))


if __name__ == "__main__":
    main(sys.argv[1])
