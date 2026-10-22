import sys, time, json, re
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from ogs_joseki import get
root=get("root")
def descend(n, path):
    for mv in path:
        m=[x for x in n["next_moves"] if x["placement"]==mv]
        if not m: return None
        time.sleep(0.3); n=get(m[0]["node_id"])
    return n
def clean(d): return re.sub(r'\s+',' ',(d or '')).strip()[:350]
base=descend(root,["Q16","R14"])
res={}
for spec in sys.argv[1:]:
    path=spec.split(",")
    n=descend(base,path)
    if not n: res[spec]={"error":"path not found"}; continue
    line=list(path); notes=[]; mistakes=[]
    notes.append((path[-1],clean(n["description"])))
    while True:
        for m in n["next_moves"]:
            if m["category"] in ("MISTAKE","TRICK","QUESTION"):
                mistakes.append({"after":" ".join(line),"move":m["placement"],"cat":m["category"]})
        ideal=[m for m in n["next_moves"] if m["category"]=="IDEAL" and m["placement"]!="pass"] or [m for m in n["next_moves"] if m["category"]=="IDEAL"]
        if not ideal or len(line)>=18: break
        time.sleep(0.3); n=get(ideal[0]["node_id"]); line.append(n["placement"])
        if clean(n["description"]): notes.append((n["placement"],clean(n["description"])))
    src=n.get("joseki_source") or {}
    res[spec]={"line":line,"notes":notes,"mistakes":mistakes,"end_src":src.get("description")}
    print(spec, "=>", " ".join(line), file=sys.stderr)
json.dump(res,open("../../sources/raw/ogs_lines.json","w"),ensure_ascii=False,indent=1)
