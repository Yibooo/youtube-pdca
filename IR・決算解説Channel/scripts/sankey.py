#!/usr/bin/env python3
"""決算の数字から「売上 → 費用・利益」の流れ図（サンキー図）を描く。

使い方:
    python sankey.py <data.json> <out.png> [--thumb]

- data.json の nodes / links は決算短信の数字（百万円）をそのまま書く。表示は億円に丸める。
- --thumb を付けると、1280×720 のサムネ用に、図を右寄せにして見出しを左に大きく載せる。
"""
import json
import sys
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_DIR = Path("/System/Library/Fonts")
SS = 2  # 2倍で描いて縮小し、線をなめらかにする

COLORS = {
    "revenue": (52, 64, 84),
    "segment": (96, 112, 136),
    "cost": (226, 92, 84),
    "profit": (34, 150, 110),
    "plus": (64, 132, 210),
    "highlight": (240, 140, 30),
}


def font(weight, size):
    for f in FONT_DIR.iterdir():
        if unicodedata.normalize("NFC", f.name) == f"ヒラギノ角ゴシック W{weight}.ttc":
            return ImageFont.truetype(str(f), size * SS)
    raise SystemExit("ヒラギノ角ゴシックが見つかりません")


def oku(v, data=None):
    """百万円 → 「1兆848億」のような表記。会社の資料に合わせて、data の rounding（floor＝切り捨て／round＝四捨五入）と
    decimals（億未満の桁数。小さい会社は1にする）で丸める"""
    data = data or {}
    dec = data.get("decimals", 0)
    x = v / 100
    o = (int(x * 10 ** dec) / 10 ** dec) if data.get("rounding", "floor") == "floor" else round(x, dec)
    if dec:
        return f"{o:,.{dec}f}億"
    o = int(o)
    if o >= 10000:
        return f"{o // 10000}兆{o % 10000:,}億" if o % 10000 else f"{o // 10000}兆"
    return f"{o:,}億"


def bezier_band(x0, y0a, y0b, x1, y1a, y1b, n=40):
    """左端 (y0a〜y0b) から右端 (y1a〜y1b) へ流れる帯の多角形"""
    def curve(ya, yb):
        pts = []
        for i in range(n + 1):
            t = i / n
            x = (1 - t) ** 3 * x0 + 3 * (1 - t) ** 2 * t * (x0 + (x1 - x0) / 2) + 3 * (1 - t) * t ** 2 * (x0 + (x1 - x0) / 2) + t ** 3 * x1
            y = (1 - t) ** 3 * ya + 3 * (1 - t) ** 2 * t * ya + 3 * (1 - t) * t ** 2 * yb + t ** 3 * yb
            pts.append((x, y))
        return pts
    return curve(y0a, y1a) + curve(y0b, y1b)[::-1]


def layout(data, box):
    """各ノードの位置（x, 上端 y, 高さ）を決める"""
    x0, y0, x1, y1 = box
    nodes = {n["id"]: dict(n) for n in data["nodes"]}
    cols = sorted({n["col"] for n in nodes.values()})
    gap = data.get("gap", 26) * SS
    node_w = data.get("node_w", 22) * SS
    # 1列の合計が一番大きい列が、枠の高さに収まる倍率にする
    tallest = max(sum(n["value"] for n in nodes.values() if n["col"] == c) +
                  gap * 0 for c in cols)
    ngaps = max(sum(1 for n in nodes.values() if n["col"] == c) - 1 for c in cols)
    k = (y1 - y0 - gap * ngaps) / tallest
    step = (x1 - x0 - node_w) / (len(cols) - 1)
    for c in cols:
        y = y0
        for n in [n for n in data["nodes"] if n["col"] == c]:
            nd = nodes[n["id"]]
            nd["x"] = x0 + step * cols.index(c)
            nd["h"] = n["value"] * k
            nd["y"] = y0 + n["y"] * (y1 - y0) if "y" in n else y
            nd["in"] = nd["out"] = 0
            y = nd["y"] + nd["h"] + gap
    return nodes, k, node_w


def draw(data, size, box, label_scale=1.0, show=None, highlight=None, short=False, upto=None):
    """show：ラベルを出すノードの id（None ならすべて）。highlight：目立たせるノードの id（1つかリスト）。
    short：ノードの short 名を使う。upto：この列までだけ描く（動画で1段ずつ見せるとき）"""
    W, H = size
    if isinstance(highlight, str):
        highlight = [highlight]
    highlight = set(highlight or [])
    img = Image.new("RGB", (W * SS, H * SS), tuple(data.get("bg", (246, 246, 243))))
    d = ImageDraw.Draw(img, "RGBA")
    box = [v * SS for v in box]
    nodes, k, node_w = layout(data, box)
    total = data["base"]

    for ln in data["links"]:
        a, b = nodes[ln["from"]], nodes[ln["to"]]
        h = ln["value"] * k
        ya, yb = a["y"] + a["out"], b["y"] + b["in"]
        a["out"] += h
        b["in"] += h
        if upto is not None and b["col"] > upto:
            continue
        color = COLORS[b["kind"] if b["kind"] in ("cost",) else (a["kind"] if b["kind"] == "revenue" else b["kind"])]
        alpha = 70
        if highlight & {ln["from"], ln["to"]}:
            color, alpha = COLORS["highlight"], 120
        d.polygon(bezier_band(a["x"] + node_w, ya, ya + h, b["x"], yb, yb + h), fill=color + (alpha,))

    f_name = font(7, int(22 * label_scale))
    f_val = font(6, int(20 * label_scale))
    f_pct = font(5, int(16 * label_scale))
    for n in nodes.values():
        if upto is not None and n["col"] > upto:
            continue
        color = COLORS["highlight"] if n["id"] in highlight else COLORS[n["kind"]]
        d.rectangle([n["x"], n["y"], n["x"] + node_w, n["y"] + max(n["h"], 2 * SS)], fill=color)
        if show is not None and n["id"] not in show:
            continue
        lines = [(n.get("short", n["label"]) if short else n["label"], f_name), (oku(n["value"], data), f_val)]
        if n.get("pct", True):
            lines.append((f"{n['value'] / total * 100:.1f}%", f_pct))
        side = n.get("label_side", "right")
        th = sum(fn.getbbox(t)[3] + 6 * SS for t, fn in lines)
        ty = n["y"] - th - 4 * SS if side == "above" else n["y"] + max(n["h"], 2 * SS) / 2 - th / 2
        for t, fn in lines:
            tw = fn.getlength(t)
            tx = n["x"] + node_w + 10 * SS if side == "right" else n["x"] - 10 * SS - tw
            if side == "above":
                tx = n["x"] + node_w / 2 - tw / 2
            d.text((tx, ty), t, font=fn, fill=color if n["kind"] not in ("segment", "revenue") or n["id"] in highlight else (60, 60, 60))
            ty += fn.getbbox(t)[3] + 6 * SS
    return img, d


def render(data_path, out_path, thumb=False):
    data = json.loads(Path(data_path).read_text(encoding="utf-8"))
    if thumb:
        t = data["thumbnail"]
        img, d = draw(data, (1280, 720), (600, 110, 1090, 690), label_scale=1.25,
                      show=set(t.get("show", [])), highlight=t.get("highlight"), short=True)
        f1, f2, f3 = font(8, t.get("size", 78)), font(7, 34), font(6, 26)
        y = 60 * SS
        d.text((40 * SS, y), t["company"], font=f2, fill=(52, 64, 84))
        y += 64 * SS
        for line in t["lines"]:
            d.text((40 * SS, y), line, font=f1, fill=(226, 92, 84) if line in t.get("accent", []) else (30, 30, 30),
                   stroke_width=3 * SS, stroke_fill=(255, 255, 255))
            y += (t.get("size", 78) + 22) * SS
        d.text((40 * SS, 640 * SS), t["period"], font=f3, fill=(110, 110, 110))
        size = (1280, 720)
    else:
        img, d = draw(data, (1920, 1080), (300, 200, 1640, 1000))
        d.text((60 * SS, 40 * SS), data["title"], font=font(8, 44), fill=(30, 30, 30))
        d.text((60 * SS, 100 * SS), data["subtitle"], font=font(5, 24), fill=(110, 110, 110))
        d.text((60 * SS, 1030 * SS), data["source"], font=font(4, 18), fill=(130, 130, 130))
        size = (1920, 1080)
    img.resize(size, Image.LANCZOS).save(out_path)
    print("saved", out_path)


if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2], thumb="--thumb" in sys.argv)
