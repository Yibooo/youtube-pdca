#!/usr/bin/env python3
"""手順(GTP座標)から右上隅の盤面図(テキスト)を作る。取られた石の処理はしない（定石図の確認用）。

使い方: python3 diagram.py "B:Q16 W:R14" "B:R12 W:R17 B:R16 ..."
  第1引数 = 初期配置（番号なし）、第2引数 = 手順（1から番号付け）
"""
import sys

COLS = "ABCDEFGHJKLMNOPQRST"
SHOW_COLS = COLS[9:]          # K..T
SHOW_ROWS = range(19, 8, -1)  # 19..9


def parse(s):
    """'pass'（手抜き）も1手として番号を進める。"""
    out = []
    for tok in s.split():
        color, _, mv = tok.rpartition(":")
        if mv == "pass":
            out.append((color, None, None))
        else:
            out.append((color, mv[0], int(mv[1:])))
    return out


def render(setup, seq):
    cell = {}
    for c, col, row in parse(setup):
        cell[(col, row)] = "X" if c == "B" else "O"
    for i, (c, col, row) in enumerate(parse(seq), 1):
        if col:
            cell[(col, row)] = ("B" if c == "B" else "W") + str(i)
    lines = ["     " + " ".join(f"{c:>3}" for c in SHOW_COLS)]
    for r in SHOW_ROWS:
        lines.append(f"{r:>3}  " + " ".join(f"{cell.get((c, r), '.'):>3}" for c in SHOW_COLS))
    return "\n".join(lines)


if __name__ == "__main__":
    print(render(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else ""))
