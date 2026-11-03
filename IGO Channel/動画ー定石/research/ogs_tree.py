#!/usr/bin/env python3
"""OGS の定石ツリーを調べる。

  python ogs_tree.py kids "Q16 R14" "Q16 R14 R12"   … 各局面の次の手（I=定石 G=有力 M=悪手 T=ハメ手、数字は順位）
  python ogs_tree.py line Q16,R14,R12 ...           … その局面から定石（I/G）の手順をたどり、解説と悪手を表示
"""
import re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from ogs_joseki import get


def node(path):
    n = get("root")
    for mv in path:
        m = [x for x in n["next_moves"] if x["placement"] == mv]
        if not m:
            return None
        time.sleep(0.3)
        n = get(m[0]["node_id"])
    return n


def kids(spec):
    n = node(spec.split())
    if not n:
        print(spec, "-> not found"); return
    ks = sorted(n["next_moves"], key=lambda m: (m["category"] != "IDEAL", m["variation_label"] if m["variation_label"] != "_" else "z"))
    print(f"{spec} :: " + " ".join(f"{m['placement']}({m['category'][0]}{'' if m['variation_label'] == '_' else m['variation_label']})" for m in ks))


def line(spec):
    p = spec.split(","); print("=====", spec)
    n = node(p); seq = []
    while n and len(seq) < 16:
        d = re.sub(r"\s+", " ", n["description"] or "")[:260]
        bad = [m["placement"] + "(" + m["category"][0] + ")" for m in n["next_moves"] if m["category"] in ("MISTAKE", "TRICK")]
        print(f"  {n['placement']} [{n['category']}] {d}" + (f"  !bad: {bad}" if bad else ""))
        nm = [m for m in n["next_moves"] if m["category"] in ("IDEAL", "GOOD")]
        if not nm:
            break
        time.sleep(0.3); n = get(nm[0]["node_id"])
        if n: seq.append(n["placement"])
    print("  line:", " ".join(p + seq))


if __name__ == "__main__":
    mode, args = sys.argv[1], sys.argv[2:]
    for a in args:
        (kids if mode == "kids" else line)(a)
