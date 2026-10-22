import re, html, json, time, sys, urllib.request
BASE="https://gojoseki.shogidb2.com"
def fetch(path):
    req=urllib.request.Request(BASE+path,headers={"User-Agent":"Mozilla/5.0 igo-research"})
    return urllib.request.urlopen(req,timeout=20).read().decode()
def parse(t):
    title=re.search(r'<title>(.*?)</title>',t,re.S).group(1).split('|')[0].strip()
    wgo=[html.unescape(w) for w in re.findall(r'data-wgo="([^"]+)"',t)]
    body=re.sub(r'<script.*?</script>|<style.*?</style>|<nav.*?</nav>','',t,flags=re.S)
    body=re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',body)))
    links=sorted(set(re.findall(r'href="([a-z_]+/)"',t)))
    return title,wgo,body,links
seen={}; queue=[("/hoshi/kogeimagakari/",0)]
while queue:
    p,d=queue.pop(0)
    if p in seen: continue
    try: t=fetch(p)
    except Exception as e: print("ERR",p,e,file=sys.stderr); continue
    title,wgo,body,links=parse(t); seen[p]={"title":title,"wgo":wgo,"body":body[:3000],"depth":d}
    if d<3:
        for l in links:
            queue.append((p+l,d+1))
    time.sleep(0.5)
json.dump(seen,open("../../sources/raw/gojoseki.json","w"),ensure_ascii=False,indent=1)
print(len(seen))
for p,v in seen.items(): print(v["depth"],p,v["title"],len(v["wgo"]))
