#!/usr/bin/env python3
"""KataGo で、ある局面の候補手をまとめて比べる（~/katago の CPU 版を使う）。

  python kg_multi.py "B:Q16 W:R14" O17,R12,D4            … 手番側の候補手ごとの損と、その後の読み筋
  KG_SETUP="B:Q10" python kg_multi.py "B:Q16 W:R17" R16,Q17  … 置き石（周りの石）つき

手抜きは pass ではなく、他の大場（D4 など）に打った手として比べる（pass は相手に1手与えるため約12目多く出る）。
"""
import json, os, subprocess, sys, pathlib
H = pathlib.Path.home() / "katago"
prefix = [t.split(":") for t in sys.argv[1].split()]
player = "W" if prefix and prefix[-1][0] == "B" else "B"
cands = sys.argv[2].split(",")
setup = [t.split(":") for t in os.environ.get("KG_SETUP", "").split()]
base = {"initialStones": setup, "rules": "japanese", "komi": 6.5, "boardXSize": 19, "boardYSize": 19,
        "overrideSettings": {"reportAnalysisWinratesAs": "BLACK"}}
qs = [dict(base, id="root", moves=prefix, maxVisits=3000)]
qs += [dict(base, id=c, moves=prefix + [[player, c]], maxVisits=2000) for c in cands]
p = subprocess.run([str(H / "katago"), "analysis", "-config", str(H / "analysis_example.cfg"), "-model", str(H / "kata1-b18.bin.gz")],
                   input="".join(json.dumps(q) + "\n" for q in qs), capture_output=True, text=True, timeout=3600)
res = {json.loads(l)["id"]: json.loads(l) for l in p.stdout.splitlines() if l.startswith("{") and "rootInfo" in l}
r = res["root"]; best = r["rootInfo"]["scoreLead"]; sign = 1 if player == "B" else -1
print("root scoreLead(B):", round(best, 2))
print("top moves:", [(m["move"], round(m["scoreLead"], 2), m["visits"]) for m in r["moveInfos"][:6]])
for c in cands:
    x = res[c]; s = x["rootInfo"]["scoreLead"]
    print(f"{c}: scoreLead(B) {s:.2f} loss {sign*(best-s):.2f}  PV: {' '.join(x['moveInfos'][0]['pv'][:12])}")
