import json, sys, urllib.request, time
def get(nid):
    for _ in range(3):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(f"https://online-go.com/oje/position?id={nid}",headers={"User-Agent":"Mozilla/5.0 igo-research"}), timeout=20))
        except Exception as e: time.sleep(2)
def child(node, mv):
    for m in node["next_moves"]:
        if m["placement"]==mv: return get(m["node_id"])
    raise SystemExit(f"no {mv} in {[m['placement'] for m in node['next_moves']]}")
if __name__=="__main__":
    n=get("root")
    for mv in sys.argv[1:]: n=child(n,mv)
    print("play:",n["play"],"| cat:",n["category"],"| src:",n.get("joseki_source"))
    print("desc:",(n["description"] or "")[:400].replace("\n"," "))
    for m in n["next_moves"]: print("  ",m["placement"],m["category"],m["variation_label"])
