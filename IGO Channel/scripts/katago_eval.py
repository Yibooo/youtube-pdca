#!/usr/bin/env python3
"""KataGo の解析エンジンで「正解の手」と「不正解の手」の目数差を出す。

使い方:
    python katago_eval.py "B:Q16 W:R14 B:R12 W:R17 B:R16 W:Q17" P16 P17
      第1引数 = 分岐の直前までの手順（空の19路盤・コミ6.5から）
      第2引数 = 正解の手、第3引数 = 不正解の手（どちらも手番側の手）

出力: 各手を打った直後の局面の scoreLead（黒から見た目数）と、その差（＝不正解の損失）。
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

VISITS = 2000


def find_engine():
    """環境変数 KATAGO_BIN / KATAGO_CONFIG / KATAGO_MODEL、次に ~/katago/（自前ビルド）、最後に brew 版を探す。"""
    env = [os.environ.get(k) for k in ("KATAGO_BIN", "KATAGO_CONFIG", "KATAGO_MODEL")]
    if all(env):
        return env[0], Path(env[1]), Path(env[2])
    home = Path.home() / "katago"
    if (home / "katago").exists() and (home / "analysis_example.cfg").exists():
        models = sorted(home.glob("*.bin.gz"))
        if models:
            return str(home / "katago"), home / "analysis_example.cfg", models[-1]
    exe = shutil.which("katago")
    if not exe:
        raise SystemExit("katago が見つかりません（brew install katago）")
    share = Path(subprocess.run(["brew", "--prefix", "katago"], capture_output=True, text=True).stdout.strip()) / "share" / "katago"
    cfg = next(iter(sorted(share.rglob("analysis_example.cfg"))), None)
    models = sorted(share.rglob("*.bin.gz"), key=lambda p: p.stat().st_size, reverse=True)
    if not cfg or not models:
        raise SystemExit(f"設定ファイルかモデルが見つかりません: {share}")
    return exe, cfg, models[0]


def parse(seq):
    return [[c, m] for c, m in (t.split(":") for t in seq.split())]


def main(prefix, good, bad):
    exe, cfg, model = find_engine()
    moves = parse(prefix)
    player = "W" if moves and moves[-1][0] == "B" else "B"
    queries = []
    for tag, mv in (("good", good), ("bad", bad)):
        queries.append({"id": tag, "moves": moves + [[player, mv]], "rules": "japanese", "komi": 6.5,
                        "boardXSize": 19, "boardYSize": 19, "maxVisits": VISITS,
                        "overrideSettings": {"reportAnalysisWinratesAs": "BLACK"}})
    proc = subprocess.run([exe, "analysis", "-config", str(cfg), "-model", str(model)],
                          input="".join(json.dumps(q) + "\n" for q in queries),
                          capture_output=True, text=True, timeout=1800)
    res = {}
    for line in proc.stdout.splitlines():
        r = json.loads(line)
        if "rootInfo" in r:
            res[r["id"]] = r["rootInfo"]
    g, b = res["good"]["scoreLead"], res["bad"]["scoreLead"]
    sign = 1 if player == "B" else -1  # 手番側から見た損失にする
    out = {"model": model.name, "visits": VISITS, "player": player, "good": good, "bad": bad,
           "scoreLead_black_after_good": round(g, 2), "scoreLead_black_after_bad": round(b, 2),
           "loss_points": round(sign * (g - b), 2)}
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main(*sys.argv[1:4])
