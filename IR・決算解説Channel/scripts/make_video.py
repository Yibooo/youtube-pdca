#!/usr/bin/env python3
"""決算解説の動画を spec.json から作る（画面の描画 → VOICEVOX の音声 → ffmpeg でつなぐ）。

使い方:
    python make_video.py ../episodes/ep01_fastretailing_fy2026/spec.json

- spec.json の scenes は、章（chapter）ごとにセリフ（lines）を並べたもの。
  セリフごとに音声を作り、字幕付きの画面を表示する。画面（v）は、次に v が出てくるまで同じものを出し続ける。
- 出力は <エピソード>/build/ に video.mp4、chapters.txt、thumbnail.png を作る。
前提: VOICEVOX Engine が http://127.0.0.1:50021 で起動していること、ffmpeg と pdftoppm が入っていること。
"""
import json
import subprocess
import sys
import urllib.parse
import urllib.request
import wave
from pathlib import Path

from PIL import Image, ImageDraw

import sankey
from sankey import COLORS, font

VOICEVOX = "http://127.0.0.1:50021"
W, H = 1920, 1080
BG = (246, 246, 243)
INK = (30, 30, 30)
SUB = (110, 110, 110)
MAIN = (60, 110, 1860, 900)  # 図を置く範囲（上は見出し、下は字幕）
PAUSE_LINE, PAUSE_SCENE = 0.25, 0.7


# ---------- 画面 ----------

def text_w(fn, t):
    return fn.getlength(t) / sankey.SS


def wrap(fn, t, width):
    lines, cur = [], ""
    for ch in t:
        if text_w(fn, cur + ch) > width and ch not in "、。）」":  # 句読点は行頭に置かない
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    return lines + [cur] if cur else lines


class Canvas:
    """sankey.font は2倍の大きさで作るので、2倍の画像に描いて最後に縮小する"""

    def __init__(self, img=None):
        self.img = img or Image.new("RGB", (W * sankey.SS, H * sankey.SS), BG)
        self.d = ImageDraw.Draw(self.img, "RGBA")

    def text(self, xy, t, fn, fill=INK, anchor="la", **kw):
        self.d.text((xy[0] * sankey.SS, xy[1] * sankey.SS), t, font=fn, fill=fill, anchor=anchor, **kw)

    def rect(self, box, **kw):
        self.d.rectangle([v * sankey.SS for v in box], **kw)

    def rrect(self, box, r=16, **kw):
        self.d.rounded_rectangle([v * sankey.SS for v in box], radius=r * sankey.SS, **kw)

    def done(self):
        return self.img.resize((W, H), Image.LANCZOS)


def v_title(c, v, ctx):
    y = 260
    for line in v["lines"]:
        size = v.get("size", 96)
        color = COLORS["cost"] if line in v.get("accent", []) else INK
        c.text((W / 2, y), line, font(8, size), fill=color, anchor="ma")
        y += size + 36
    if v.get("sub"):
        c.text((W / 2, y + 30), v["sub"], font(5, 36), fill=SUB, anchor="ma")


def v_points(c, v, ctx):
    c.text((160, 150), v["title"], font(8, 56))
    y = 270
    step = min(130, 620 / len(v["items"]))
    for i, item in enumerate(v["items"], 1):
        on = i - 1 in v.get("highlight", range(len(v["items"])))
        col = COLORS["profit"] if on else (190, 190, 190)
        c.rrect((160, y, 236, y + 76), r=38, fill=col)
        c.text((198, y + 38), str(i), font(8, 40), fill=(255, 255, 255), anchor="mm")
        c.text((270, y + 8), item, font(7, 44), fill=INK if on else (170, 170, 170))
        y += step


def v_sankey(c, v, ctx):
    data = ctx["data"][v.get("data", "data")]
    img, _ = sankey.draw(data, (W, H), (330, 150, 1560, 870), label_scale=1.2,
                         highlight=v.get("highlight"), upto=v.get("upto"))
    c.img.paste(img, (0, 0))
    if v.get("title"):
        c.text((60, 110), v["title"], font(7, 34), fill=SUB)


def v_bars(c, v, ctx):
    c.text((120, 110), v["title"], font(8, 48))
    if v.get("legend", True) and any("prev" in it for it in v["items"]):
        fl_ = font(5, 26)
        x = 1800
        for label, col in ((v.get("cur_label", "今期"), COLORS["revenue"]), (v.get("prev_label", "前期"), (205, 205, 205))):
            x -= text_w(fl_, label)
            c.text((x, 124), label, fl_, fill=SUB)
            c.rect((x - 40, 130, x - 10, 150), fill=col)
            x -= 80
    items = v["items"]
    vmax = max(max(it["value"], it.get("prev", 0)) for it in items)
    x0, x1 = 520, 1560
    top, bottom = 200, 860
    row = (bottom - top) / len(items)
    fl, fv, fc = font(7, 36), font(6, 30), font(6, 28)
    for i, it in enumerate(items):
        y = top + row * i
        hl = it["label"] in v.get("highlight", [])
        col = COLORS["highlight"] if hl else COLORS.get(it.get("kind", "revenue"))
        c.text((x0 - 30, y + row / 2), it["label"], fl, fill=INK, anchor="rm")
        bh = min(row * 0.32, 44)
        if "prev" in it:
            c.rect((x0, y + row / 2 - bh - 4, x0 + (x1 - x0) * it["prev"] / vmax, y + row / 2 - 4), fill=(205, 205, 205))
            c.text((x0 + (x1 - x0) * it["prev"] / vmax + 12, y + row / 2 - bh / 2 - 4), it.get("prev_text", f"{it['prev']:,}"),
                   fc, fill=SUB, anchor="lm")
            yb = y + row / 2 + 4
        else:
            yb = y + row / 2 - bh / 2
        xe = x0 + (x1 - x0) * it["value"] / vmax
        c.rect((x0, yb, xe, yb + bh), fill=col)
        label = it.get("text", f"{it['value']:,}")
        if it.get("change"):
            label += f"（{it['change']}）"
        c.text((xe + 12, yb + bh / 2), label, fv, fill=col, anchor="lm")
        if it.get("sub"):  # 売上の棒の下に、事業利益と利益率を併記する
            c.text((x0, yb + bh + 8), it["sub"], font(6, 27), fill=COLORS["profit"])
    if v.get("note"):
        c.text((120, 880), v["note"], font(5, 26), fill=SUB)


def v_table(c, v, ctx):
    c.text((120, 110), v["title"], font(8, 48))
    cols = v["headers"]
    widths = v.get("widths") or [1 / len(cols)] * len(cols)
    x0, x1, y = 160, 1760, 210
    rh = min(92, 640 / (len(v["rows"]) + 1))
    xs = [x0]
    for w_ in widths:
        xs.append(xs[-1] + (x1 - x0) * w_)
    fh, fb = font(7, 32), font(6, 36)
    c.rect((x0, y, x1, y + rh), fill=COLORS["revenue"])
    for j, h in enumerate(cols):
        c.text(((xs[j] + xs[j + 1]) / 2, y + rh / 2), h, fh, fill=(255, 255, 255), anchor="mm")
    for i, r in enumerate(v["rows"]):
        yy = y + rh * (i + 1)
        hl = i in v.get("highlight", [])
        c.rect((x0, yy, x1, yy + rh), fill=(255, 236, 214) if hl else ((255, 255, 255) if i % 2 == 0 else (238, 238, 234)))
        for j, cell in enumerate(r):
            anchor = "lm" if j == 0 else "mm"
            x = xs[j] + 24 if j == 0 else (xs[j] + xs[j + 1]) / 2
            c.text((x, yy + rh / 2), str(cell), fb, fill=INK, anchor=anchor)
    if v.get("note"):
        c.text((120, 880), v["note"], font(5, 26), fill=SUB)


def v_cards(c, v, ctx):
    c.text((120, 110), v["title"], font(8, 48))
    items = v["items"]
    n = len(items)
    cols = 1 if n <= 3 else 2  # 3つまでは横いっぱいの段にする
    rows = (n + cols - 1) // cols
    gw, gh = (1680 - 40 * (cols - 1)) / cols, (680 - 40 * (rows - 1)) / rows
    for i, it in enumerate(items):
        x = 120 + (i % cols) * (gw + 40)
        y = 200 + (i // cols) * (gh + 40)
        on = i in v.get("highlight", range(n))
        c.rrect((x, y, x + gw, y + gh), r=20, fill=(255, 255, 255), outline=COLORS[it.get("kind", "cost")] if on else (220, 220, 220), width=4 * sankey.SS)
        c.text((x + 36, y + 30), it["h"], font(8, 40), fill=COLORS[it.get("kind", "cost")] if on else (180, 180, 180))
        fb = font(5, 32)
        yy = y + 100
        for line in wrap(fb, it["b"], gw - 72):
            c.text((x + 36, yy), line, fb, fill=INK if on else (180, 180, 180))
            yy += 46


def v_slide(c, v, ctx):
    ep = ctx["ep"]
    png = ep / "build" / "slides" / f"{Path(v['pdf']).stem}-{v['page']}.png"
    if not png.exists():
        png.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["pdftoppm", "-r", "200", "-png", "-singlefile", "-f", str(v["page"]), "-l", str(v["page"]),
                        str(ep / v["pdf"]), str(png.with_suffix(""))], check=True)
    sl = Image.open(png).convert("RGB")
    # 説明会資料は「スライド＋話す原稿」の縦長ページなので、上の枠で囲まれたスライド部分だけを切り出す
    if sl.height > sl.width:
        g = sl.crop((0, 0, sl.width, int(sl.height * 0.5))).convert("L")
        px = g.load()
        rows = [y for y in range(g.height) if sum(px[x, y] < 120 for x in range(0, g.width, 4)) > g.width / 4 * 0.6]
        if rows:  # スライドの外枠（黒い横線）の上端と下端で切る
            y0, y1 = min(rows), max(rows)
            cols = [x for x in range(g.width) if sum(px[x, y] < 120 for y in range(y0, y1, 4)) > (y1 - y0) / 4 * 0.6]
            sl = sl.crop((min(cols), y0, max(cols) + 1, y1 + 1))
    bw, bh = 1640, 690
    s = min(bw / sl.width, bh / sl.height)
    sl = sl.resize((int(sl.width * s * sankey.SS), int(sl.height * s * sankey.SS)), Image.LANCZOS)
    x = int((W * sankey.SS - sl.width) / 2)
    y = int(120 * sankey.SS)
    c.d.rectangle([x - 8 * sankey.SS, y - 8 * sankey.SS, x + sl.width + 8 * sankey.SS, y + sl.height + 8 * sankey.SS],
                  fill=(255, 255, 255), outline=(150, 150, 150), width=3 * sankey.SS)
    c.img.paste(sl, (x, y))
    c.rrect((x / sankey.SS - 8, y / sankey.SS - 52, x / sankey.SS + 110, y / sankey.SS - 10), r=8, fill=(90, 90, 90))
    c.text((x / sankey.SS + 51, y / sankey.SS - 31), "引用", font(7, 26), fill=(255, 255, 255), anchor="mm")
    c.text((W / 2, y / sankey.SS + sl.height / sankey.SS + 22), "出典：" + v["source"], font(5, 24), fill=SUB, anchor="ma")


def arrow(c, cx, cy, w=34, h=44, fill=(150, 150, 150)):
    """右向きの三角の矢印（フォントに▶がないため図形で描く）"""
    c.d.polygon([((cx - w / 2) * sankey.SS, (cy - h / 2) * sankey.SS), ((cx + w / 2) * sankey.SS, cy * sankey.SS),
                 ((cx - w / 2) * sankey.SS, (cy + h / 2) * sankey.SS)], fill=fill)


def v_pillars(c, v, ctx):
    """戦略の柱：列ごとに見出しと中身を並べる。hl：強調する列、hl_items：強調する [列, 行]"""
    c.text((120, 110), v["title"], font(8, 48))
    if v.get("lead"):
        c.text((120, 178), v["lead"], font(6, 30), fill=SUB)
    cols = v["cols"]
    n = len(cols)
    top = 240 if v.get("lead") else 200
    gw = (1680 - 40 * (n - 1)) / n
    hl = v.get("hl", list(range(n)))
    hli = [tuple(x) for x in v.get("hl_items", [])]
    for i, col in enumerate(cols):
        x = 120 + i * (gw + 40)
        on = i in hl
        kind = COLORS[col.get("kind", "profit")]
        c.rrect((x, top, x + gw, top + 86), r=14, fill=kind if on else (205, 205, 205))
        c.text((x + gw / 2, top + 43), col["h"], font(8, 38), fill=(255, 255, 255), anchor="mm")
        y = top + 110
        ih = min(190, (880 - y) / max(1, len(col["items"])) - 18)
        for j, it in enumerate(col["items"]):
            ion = on and (not hli or (i, j) in hli)
            c.rrect((x, y, x + gw, y + ih), r=12, fill=(255, 255, 255), outline=kind if ion else (220, 220, 220), width=3 * sankey.SS)
            head, _, body = it.partition("｜")
            fh = font(8, 38)
            c.text((x + 30, y + 20), head, fh, fill=INK if ion else (175, 175, 175))
            if body:
                fb = font(5, 31)
                yy = y + 76
                for line in wrap(fb, body, gw - 60)[:max(1, int((ih - 80) // 42))]:
                    c.text((x + 30, yy), line, fb, fill=INK if ion else (185, 185, 185))
                    yy += 42
            y += ih + 18


def v_flow(c, v, ctx):
    """矢印でつないだ流れ。steps：[{h, b}]、hl：強調する段"""
    c.text((120, 110), v["title"], font(8, 48))
    if v.get("lead"):
        c.text((120, 178), v["lead"], font(6, 30), fill=SUB)
    steps = v["steps"]
    n = len(steps)
    aw = 70
    gw = (1680 - aw * (n - 1)) / n
    top, h = 250, v.get("height", 600)
    hl = v.get("hl", list(range(n)))
    for i, st in enumerate(steps):
        x = 120 + i * (gw + aw)
        on = i in hl
        kind = COLORS[st.get("kind", "profit")]
        c.rrect((x, top, x + gw, top + h), r=18, fill=(255, 255, 255), outline=kind if on else (220, 220, 220), width=4 * sankey.SS)
        c.rrect((x, top, x + gw, top + 96), r=18, fill=kind if on else (215, 215, 215))
        c.text((x + gw / 2, top + 48), st["h"], font(8, 40 if n <= 3 else 34), fill=(255, 255, 255), anchor="mm")
        fb = font(6 if on else 5, 37 if n <= 3 else 32)
        yy = top + 130
        for line in wrap(fb, st.get("b", ""), gw - 56)[:9]:
            c.text((x + 28, yy), line, fb, fill=INK if on else (185, 185, 185))
            yy += 56 if n <= 3 else 48
        if i < n - 1:
            arrow(c, x + gw + aw / 2, top + h / 2)
    if v.get("note"):
        c.text((120, 880), v["note"], font(5, 26), fill=SUB)


def v_kpi(c, v, ctx):
    """大きな数字の推移。items：[{label, value, sub}]、hl：強調する項目"""
    c.text((120, 110), v["title"], font(8, 48))
    items = v["items"]
    n = len(items)
    aw = 90
    gw = (1680 - aw * (n - 1)) / n
    hl = v.get("hl", list(range(n)))
    for i, it in enumerate(items):
        x = 120 + i * (gw + aw)
        on = i in hl
        col = COLORS[it.get("kind", "profit")] if on else (190, 190, 190)
        c.text((x + gw / 2, 300), it["label"], font(7, 46), fill=INK if on else (170, 170, 170), anchor="ma")
        c.text((x + gw / 2, 380), it["value"], font(8, 120), fill=col, anchor="ma")
        fs = font(5, 34)
        yy = 560
        for line in wrap(fs, it.get("sub", ""), gw - 20)[:3]:
            c.text((x + gw / 2, yy), line, fs, fill=SUB, anchor="ma")
            yy += 48
        if i < n - 1:
            arrow(c, x + gw + aw / 2, 450, 40, 54)
    if v.get("note"):
        c.text((120, 880), v["note"], font(5, 26), fill=SUB)


VISUALS = {"title": v_title, "points": v_points, "sankey": v_sankey, "bars": v_bars,
           "table": v_table, "cards": v_cards, "slide": v_slide, "pillars": v_pillars, "flow": v_flow, "kpi": v_kpi}


def frame(v, chapter, caption, ctx):
    c = Canvas()
    VISUALS[v["type"]](c, v, ctx)
    # 見出し
    c.rect((0, 0, W, 64), fill=COLORS["revenue"])
    c.text((40, 32), chapter, font(7, 30), fill=(255, 255, 255), anchor="lm")
    c.text((W - 40, 32), ctx["header"], font(5, 26), fill=(220, 225, 232), anchor="rm")
    # 字幕
    if caption:
        fc = font(6, 40)
        lines = wrap(fc, caption, 1700)[:3]
        top = 1060 - 58 * len(lines) - 24
        c.rrect((90, top, W - 90, 1060), r=14, fill=(255, 255, 255, 235))
        for i, line in enumerate(lines):
            c.text((W / 2, top + 16 + 58 * i), line, fc, fill=INK, anchor="ma")
    return c.done()


# ---------- 音声 ----------

def tts(text, path, voice, readings):
    for k, r in readings.items():
        text = text.replace(k, r)
    q = urllib.parse.urlencode({"text": text, "speaker": voice["speaker"]})
    aq = json.load(urllib.request.urlopen(urllib.request.Request(f"{VOICEVOX}/audio_query?{q}", method="POST")))
    aq["speedScale"] = voice.get("speed", 1.1)
    aq["postPhonemeLength"] = 0.1
    req = urllib.request.Request(f"{VOICEVOX}/synthesis?speaker={voice['speaker']}", data=json.dumps(aq).encode(),
                                 headers={"Content-Type": "application/json"})
    path.write_bytes(urllib.request.urlopen(req).read())
    with wave.open(str(path)) as w:
        return w.getnframes() / w.getframerate(), aq["kana"]


def main(spec_path):
    spec_path = Path(spec_path).resolve()
    ep = spec_path.parent
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    out = ep / "build"
    for sub in ("frames", "audio", "segments"):
        (out / sub).mkdir(parents=True, exist_ok=True)
    ctx = {"ep": ep, "header": spec["header"],
           "data": {k: json.loads((ep / f).read_text(encoding="utf-8")) for k, f in spec["data"].items()}}
    readings = spec.get("readings", {})
    segs, chapters, kana_log, t = [], [], [], 0.0
    n = 0
    for si, scene in enumerate(spec["scenes"]):
        chapters.append((t, scene["chapter"]))
        v = None
        for li, line in enumerate(scene["lines"]):
            v = line.get("v", v)
            n += 1
            wav = out / "audio" / f"{n:03d}.wav"
            dur, kana = tts(line.get("r", line["t"]), wav, spec["voice"], readings)
            kana_log.append(f"{n:03d} {line['t']}\n    {kana}")
            img = out / "frames" / f"{n:03d}.png"
            frame(v, scene["chapter"], line["t"], ctx).save(img)
            pad = PAUSE_SCENE if li == len(scene["lines"]) - 1 else PAUSE_LINE
            seg = out / "segments" / f"{n:03d}.mp4"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", "30", "-i", str(img),
                            "-i", str(wav), "-af", f"apad=pad_dur={pad},aresample=48000", "-t", f"{dur + pad:.3f}",
                            "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p", "-r", "30",
                            "-c:a", "aac", "-b:a", "160k", "-ac", "2", str(seg)], check=True)
            segs.append(seg)
            t += dur + pad
            print(f"{n:03d} {t:7.1f}s {line['t'][:30]}", flush=True)
    (out / "concat.txt").write_text("".join(f"file '{s}'\n" for s in segs))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(out / "concat.txt"),
                    "-c", "copy", "-movflags", "+faststart", str(out / "video.mp4")], check=True)
    (out / "chapters.txt").write_text("\n".join(f"{int(s // 60)}:{int(s % 60):02d} {name}" for s, name in chapters))
    (out / "kana.txt").write_text("\n".join(kana_log))
    sankey.render(ep / spec["data"]["data"], out / "thumbnail.png", thumb=True)
    print(f"video: {out / 'video.mp4'}  ({t / 60:.1f} min)")


if __name__ == "__main__":
    main(sys.argv[1])
