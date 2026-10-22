#!/usr/bin/env python3
"""
スライド画像生成モジュール
Pillowを使って8枚のスライド画像（1920x1080）を生成する。
既存youtube-automationのサムネイル生成コードをベースに拡張。
"""
import sys, random
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

ROOT_DIR = Path(__file__).parent.parent
OUTPUT_DIR = ROOT_DIR / "output" / "images"

W, H = 1920, 1080

# ── カラーパレット（金融・プロフェッショナル系ダークテーマ）──
COLOR = {
    "bg_top":    (10, 20, 40),      # ダークネイビー
    "bg_bot":    (20, 40, 80),      # やや明るいネイビー
    "gold":      (212, 170, 50),    # ゴールド（アクセント）
    "white":     (255, 255, 255),
    "light":     (210, 225, 245),   # 本文テキスト（薄い青白）
    "gray":      (140, 155, 175),   # フッター・補足
    "success":   (80, 210, 140),    # 緑（ポジティブ）
    "warning":   (240, 120, 80),    # オレンジ赤（警告・NG）
    "accent":    (80, 150, 255),    # 青（セクション見出し）
    "bar":       (212, 170, 50),    # アクセントバー（ゴールド）
}

# ── フォント読み込み ──
def _load_fonts():
    paths = {
        "bold":   "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
        "medium": "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
        "light":  "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
    }
    fonts = {}
    try:
        fonts["xl"]    = ImageFont.truetype(paths["bold"],   120)
        fonts["lg"]    = ImageFont.truetype(paths["bold"],   80)
        fonts["md"]    = ImageFont.truetype(paths["bold"],   58)
        fonts["sm"]    = ImageFont.truetype(paths["medium"], 44)
        fonts["xs"]    = ImageFont.truetype(paths["medium"], 34)
        fonts["tiny"]  = ImageFont.truetype(paths["light"],  26)
    except Exception:
        default = ImageFont.load_default()
        fonts = {k: default for k in ["xl","lg","md","sm","xs","tiny"]}
    return fonts


# ── サムネスタイル別カラーパレット ──
THUMB_PALETTES = {
    "dark_navy":     {"top": (10, 20, 40),   "bot": (20, 40, 80),   "text": (255,255,255), "accent": (212,170,50),  "bar": (212,170,50)},
    "bright_red":    {"top": (180, 10, 20),  "bot": (220, 40, 50),  "text": (255,255,255), "accent": (255,220,0),   "bar": (255,220,0)},
    "bright_yellow": {"top": (230, 200, 0),  "bot": (255, 230, 0),  "text": (20, 20, 20),  "accent": (180, 0, 0),   "bar": (180, 0, 0)},
    "gradient_blue": {"top": (5, 50, 120),   "bot": (10, 90, 200),  "text": (255,255,255), "accent": (100,220,255), "bar": (100,220,255)},
    "split_dark":    {"top": (10, 20, 40),   "bot": (20, 40, 80),   "text": (255,255,255), "accent": (212,170,50),  "bar": (212,170,50)},
    "minimal_white": {"top": (245, 245, 250),"bot": (230, 235, 245),"text": (20, 20, 40),  "accent": (60, 100, 200),"bar": (60, 100, 200)},
}

_current_palette: dict = THUMB_PALETTES["dark_navy"]


def _make_canvas(thumbnail_style: str = "dark_navy"):
    """グラデーション背景のキャンバスを作成（スタイル切り替え対応）"""
    global _current_palette
    palette = THUMB_PALETTES.get(thumbnail_style, THUMB_PALETTES["dark_navy"])
    _current_palette = palette

    # カラーをパレットで上書き
    COLOR["bar"]   = palette["bar"]
    COLOR["white"] = palette["text"]
    COLOR["gold"]  = palette["accent"]

    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    t, b = palette["top"], palette["bot"]
    for y in range(H):
        rv = int(t[0] + (b[0] - t[0]) * y / H)
        gv = int(t[1] + (b[1] - t[1]) * y / H)
        bv = int(t[2] + (b[2] - t[2]) * y / H)
        draw.line([(0, y), (W, y)], fill=(rv, gv, bv))

    # split_dark スタイルは左1/3を明るくする（大数字エリア）
    if thumbnail_style == "split_dark":
        for y in range(H):
            for x in range(0, W // 3):
                draw.point((x, y), fill=(30, 60, 120))
        draw.line([(W // 3, 0), (W // 3, H)], fill=(212, 170, 50), width=6)

    # ノイズテクスチャ
    if thumbnail_style not in ("minimal_white", "bright_yellow"):
        for _ in range(1500):
            x, y = random.randint(0, W-1), random.randint(0, H-1)
            v = random.randint(0, 12)
            draw.point((x, y), fill=(v, v, v + 5))
    return img, draw


def _draw_header(draw, fonts, channel_name, slide_num, total):
    """ヘッダー：チャンネル名（左）＋スライド番号（右）"""
    pad = 50
    draw.text((pad, 30), channel_name, font=fonts["tiny"], fill=COLOR["gray"])
    num_text = f"{slide_num} / {total}"
    bb = draw.textbbox((0, 0), num_text, font=fonts["tiny"])
    tw = bb[2] - bb[0]
    draw.text((W - tw - pad, 30), num_text, font=fonts["tiny"], fill=COLOR["gray"])
    # ヘッダーライン
    draw.line([(pad, 70), (W - pad, 70)], fill=COLOR["bar"], width=2)


def _draw_footer(draw, fonts):
    """フッター：ゴールドライン"""
    draw.line([(50, H - 60), (W - 50, H - 60)], fill=COLOR["bar"], width=2)


def _centered_text(draw, text, y, font, color, shadow=True):
    """中央揃えテキスト（シャドウ付き）"""
    bb = draw.textbbox((0, 0), text, font=font)
    tw = bb[2] - bb[0]
    x = (W - tw) // 2
    if shadow:
        draw.text((x + 3, y + 3), text, font=font, fill=(0, 0, 0, 180))
    draw.text((x, y), text, font=font, fill=color)
    return bb[3] - bb[1]  # テキスト高さを返す


def _left_text(draw, text, x, y, font, color, max_width=None):
    """左揃えテキスト（長文折り返し対応）"""
    if max_width is None:
        draw.text((x, y), text, font=font, fill=color)
        bb = draw.textbbox((0, 0), text, font=font)
        return bb[3] - bb[1]

    # 折り返し処理
    words = list(text)
    line, lines = "", []
    for ch in words:
        test = line + ch
        bb = draw.textbbox((0, 0), test, font=font)
        if bb[2] - bb[0] > max_width:
            lines.append(line)
            line = ch
        else:
            line = test
    if line:
        lines.append(line)

    total_h = 0
    for i, ln in enumerate(lines):
        lh = draw.textbbox((0, 0), ln, font=font)[3]
        draw.text((x, y + total_h), ln, font=font, fill=color)
        total_h += lh + 6
    return total_h


# ── スライドタイプ別描画関数 ──

def _slide_title(draw, fonts, data, channel_name, slide_num, total):
    """タイトルスライド"""
    _draw_header(draw, fonts, channel_name, slide_num, total)
    _draw_footer(draw, fonts)

    # チャンネルロゴ風テキスト
    logo = f"▶ {channel_name}"
    _centered_text(draw, logo, 120, fonts["xs"], COLOR["gold"])

    # メインタイトル
    title = data.get("heading", "")
    _centered_text(draw, title, 320, fonts["lg"], COLOR["white"])

    # サブタイトル
    subtitle = data.get("subtitle", "")
    if subtitle:
        _centered_text(draw, subtitle, 440, fonts["md"], COLOR["gold"])

    # 装飾ライン
    draw.line([(W//2 - 200, 560), (W//2 + 200, 560)], fill=COLOR["bar"], width=3)

    # 下部のCTA
    _centered_text(draw, "チャンネル登録＆いいねよろしくお願いします", 630, fonts["xs"], COLOR["gray"])


def _slide_intro(draw, fonts, data, channel_name, slide_num, total):
    """イントロスライド（この動画で学べること）"""
    _draw_header(draw, fonts, channel_name, slide_num, total)
    _draw_footer(draw, fonts)

    heading = data.get("heading", "この動画で学べること")

    # 左アクセントバー ＋ 見出し
    draw.rectangle([(18, 100), (50, 240)], fill=COLOR["gold"])
    draw.text((80, 110), heading, font=fonts["md"], fill=COLOR["gold"])

    points = data.get("points", [])
    y = 270
    icons = ["①", "②", "③", "④"]
    for i, pt in enumerate(points[:4]):
        icon = icons[i] if i < len(icons) else "▶"
        draw.text((80, y), icon, font=fonts["sm"], fill=COLOR["gold"])
        _left_text(draw, pt, 160, y + 4, fonts["sm"], COLOR["white"], max_width=1600)
        y += 120


def _slide_problem(draw, fonts, data, channel_name, slide_num, total):
    """問題提起スライド"""
    _draw_header(draw, fonts, channel_name, slide_num, total)
    _draw_footer(draw, fonts)

    heading = data.get("heading", "")

    # 赤みがかったアクセントバー
    draw.rectangle([(18, 100), (50, 220)], fill=COLOR["warning"])
    draw.text((80, 110), heading, font=fonts["sm"], fill=COLOR["warning"])

    points = data.get("points", [])
    y = 280
    for pt in points[:4]:
        draw.text((80, y), "⚠", font=fonts["sm"], fill=COLOR["warning"])
        _left_text(draw, pt, 150, y + 4, fonts["sm"], COLOR["light"], max_width=1600)
        y += 130


def _slide_section(draw, fonts, data, channel_name, slide_num, total):
    """コンテンツセクションスライド"""
    _draw_header(draw, fonts, channel_name, slide_num, total)
    _draw_footer(draw, fonts)

    heading = data.get("heading", "")

    # 青アクセントバー ＋ 見出し
    draw.rectangle([(18, 100), (50, 240)], fill=COLOR["accent"])
    draw.text((80, 110), heading, font=fonts["md"], fill=COLOR["white"])
    draw.line([(80, 240), (1840, 240)], fill=COLOR["accent"], width=2)

    points = data.get("points", [])
    y = 280
    for i, pt in enumerate(points[:4]):
        draw.text((80, y), f"▶", font=fonts["sm"], fill=COLOR["accent"])
        _left_text(draw, pt, 140, y + 4, fonts["sm"], COLOR["light"], max_width=1640)
        y += 130


def _slide_mistakes(draw, fonts, data, channel_name, slide_num, total):
    """失敗・注意点スライド"""
    _draw_header(draw, fonts, channel_name, slide_num, total)
    _draw_footer(draw, fonts)

    heading = data.get("heading", "よくある失敗")

    draw.rectangle([(18, 100), (50, 240)], fill=COLOR["warning"])
    draw.text((80, 110), heading, font=fonts["md"], fill=COLOR["warning"])
    draw.line([(80, 240), (1840, 240)], fill=COLOR["warning"], width=2)

    points = data.get("points", [])
    y = 280
    for pt in points[:4]:
        # ✅ or ❌ の色判定
        color = COLOR["success"] if pt.startswith("✅") else COLOR["warning"]
        _left_text(draw, pt, 80, y, fonts["sm"], color, max_width=1750)
        y += 130


def _slide_cta(draw, fonts, data, channel_name, slide_num, total):
    """まとめ＆CTAスライド"""
    _draw_header(draw, fonts, channel_name, slide_num, total)
    _draw_footer(draw, fonts)

    heading = data.get("heading", "まとめ")

    # ゴールドアクセント
    draw.rectangle([(18, 100), (50, 240)], fill=COLOR["gold"])
    draw.text((80, 110), heading, font=fonts["md"], fill=COLOR["gold"])
    draw.line([(80, 240), (1840, 240)], fill=COLOR["gold"], width=2)

    points = data.get("points", [])
    y = 280
    checks = ["✅", "✅", "✅", "✅"]
    for i, pt in enumerate(points[:4]):
        icon = checks[i] if i < len(checks) else "▶"
        draw.text((80, y), icon, font=fonts["sm"], fill=COLOR["success"])
        _left_text(draw, pt, 160, y + 4, fonts["sm"], COLOR["white"], max_width=1600)
        y += 130

    # CTAボックス
    box_y = H - 200
    draw.rectangle([(80, box_y), (W - 80, box_y + 90)], outline=COLOR["gold"], width=3)
    cta = "👍 いいね・チャンネル登録・コメントよろしくお願いします！"
    _centered_text(draw, cta, box_y + 20, fonts["sm"], COLOR["gold"], shadow=False)


# スライドタイプ→描画関数マッピング
SLIDE_RENDERERS = {
    "title":    _slide_title,
    "intro":    _slide_intro,
    "problem":  _slide_problem,
    "section":  _slide_section,
    "mistakes": _slide_mistakes,
    "cta":      _slide_cta,
}


def generate(slides_data: list, theme_id: str, channel_name: str = "マネー研究所",
             thumbnail_style: str = "dark_navy") -> list:
    """
    スライドデータから画像リストを生成。
    Args:
        slides_data: generate_script.pyのslides配列
        theme_id: テーマID（ファイル名に使用）
        channel_name: チャンネル名
        thumbnail_style: サムネスタイル（dark_navy/bright_red/bright_yellow/
                         gradient_blue/split_dark/minimal_white）
    Returns:
        list of str: 生成した画像ファイルパスのリスト
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fonts = _load_fonts()
    total = len(slides_data)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    paths = []

    for i, slide in enumerate(slides_data):
        # スライド1（タイトル）だけスタイル適用、残りはdark_navyに戻す
        style = thumbnail_style if i == 0 else "dark_navy"
        img, draw = _make_canvas(style)
        slide_type = slide.get("type", "section")
        renderer = SLIDE_RENDERERS.get(slide_type, _slide_section)
        renderer(draw, fonts, slide, channel_name, i + 1, total)

        out = OUTPUT_DIR / f"{theme_id}_slide{i+1:02d}_{ts}.png"
        img.save(str(out), "PNG")
        paths.append(str(out))
        print(f"   🖼  Slide {i+1}/{total}: {out.name}")

    print(f"✅ スライド生成完了: {len(paths)}枚")
    return paths


if __name__ == "__main__":
    import json, sys
    sys.path.insert(0, str(ROOT_DIR / "scripts"))
    from generate_script import generate as gen_script

    theme = sys.argv[1] if len(sys.argv) > 1 else "nisa_basics"
    script = gen_script(theme)
    paths = generate(script["slides"], theme)
    for p in paths:
        print(p)
