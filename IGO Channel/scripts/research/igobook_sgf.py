import re, html, json, sys, time, urllib.request
COLS="ABCDEFGHJKLMNOPQRST"
PAGES={"tsukenobi":"/2017-03-18/Hoshi_Tsukenobi.html","kosumitsuke":"/2017-03-18/Hoshi_kosumitsuke.html",
"kogeimauke_basic":"/2017-03-18/Hoshi_kogeimauke.html","tsukeosae":"/2017-03-18/Hoshi_tukeosae.html",
"hasami_sansan":"/2017-03-18/Hoshi_ikkenbasami_sansan.html","hasami_kaeshi":"/2017-03-18/Hoshi_hasami_hasami_kaeshi.html",
"ikkentakabasami":"/2017-03-18/Hoshi_ikkendakabasami.html","ikken_uke":"/books/hoshi/kogeima_gakari-ikken_uke.html",
"kogeima_uke":"/books/hoshi/kogeima_gakari-kogeima_uke.html","kogeima_uke_sansan":"/books/hoshi/kogeima_gakari-kogeima_uke-sansan_iri.html",
"nikentakabasami":"/books/hoshi/kogeima_gakari-nikendaka_basami.html","ryogakari":"/books/hoshi/kogeima_gakari-ryougakari_matome.html",
"sangenbasami":"/books/hoshi/kogeima_gakari-sangen_basami.html","sangentakabasami":"/books/hoshi/kogeima_gakari-sangendaka_basami.html"}
def tok(s):
    # tokens: '(' ')' or node string
    out=[];i=0
    while i<len(s):
        c=s[i]
        if c in '()': out.append(c); i+=1
        elif c==';':
            j=i+1; buf=''
            while j<len(s) and s[j] not in '();':
                if s[j]=='[':
                    k=j+1
                    while k<len(s) and not (s[k]==']' and s[k-1]!='\\'): k+=1
                    buf+=s[j:k+1]; j=k+1
                else: buf+=s[j]; j+=1
            out.append(';'+buf); i=j
        else: i+=1
    return out
def props(node):
    d={}
    for k,vs in re.findall(r'([A-Z]+)((?:\[(?:\\\]|[^\]])*\]\s*)+)',node):
        d.setdefault(k,[]).extend(re.findall(r'\[((?:\\\]|[^\]])*)\]',vs))
    return d
def lines(tokens):
    """all root-to-leaf paths"""
    res=[]
    def walk(i,path):
        # at '(' start
        assert tokens[i]=='('; i+=1
        while i<len(tokens) and tokens[i].startswith(';'):
            path=path+[props(tokens[i])]; i+=1
        if i<len(tokens) and tokens[i]=='(':
            while tokens[i]=='(':
                i=walk(i,path)
            assert tokens[i]==')'; return i+1
        res.append(path); return i+1
    i=0
    while i<len(tokens) and tokens[i]=='(':
        i=walk(i,[])
    return res
def xform_for(stones):
    # find transform so black star -> pd and approach -> qf (R14)
    T=[lambda x,y:(x,y),lambda x,y:(18-y,18-x),lambda x,y:(18-x,y),lambda x,y:(y,x),lambda x,y:(x,18-y),lambda x,y:(18-x,18-y),lambda x,y:(y,18-x),lambda x,y:(18-y,x)]
    for t in T:
        if ('B',(15,3)) in [(c,t(*p)) for c,p in stones] and ('W',(16,5)) in [(c,t(*p)) for c,p in stones]: return t
    return None
def g(t,c): 
    if not c: return "pass"
    x,y=t(ord(c[0])-97,ord(c[1])-97); return f"{COLS[x]}{19-y}"
out={}
for key,path in PAGES.items():
    req=urllib.request.Request("https://igobook.info"+path,headers={"User-Agent":"Mozilla/5.0"})
    t=None
    for _ in range(4):
        try: t=urllib.request.urlopen(req,timeout=30).read().decode('utf-8','replace'); break
        except Exception as e: print("retry",key,e,file=sys.stderr); time.sleep(3)
    if t is None: out[key]=[{"skip":"fetch failed"}]; continue
    txt=html.unescape(re.sub(r'<[^>]+>',' ',t))
    sgfs=[]; pos=0
    while True:
        i=txt.find("(;FF[4]",pos)
        if i<0: break
        depth=0; inb=False; j=i
        while j<len(txt):
            c=txt[j]
            if inb:
                if c==']' and txt[j-1]!='\\': inb=False
            elif c=='[': inb=True
            elif c=='(': depth+=1
            elif c==')':
                depth-=1
                if depth==0: break
            j+=1
        sgfs.append(txt[i:j+1]); pos=j+1
    sgfs=list(dict.fromkeys(sgfs))
    pv=[]
    for s in sgfs:
        s=re.sub(r'</?b>','',s)
        for L in lines(tok(s)):
            stones=[]; seq=[]; comments=[]
            for p in L:
                for c in p.get('AB',[]): stones.append(('B',(ord(c[0])-97,ord(c[1])-97)))
                for c in p.get('AW',[]): stones.append(('W',(ord(c[0])-97,ord(c[1])-97)))
                for col in 'BW':
                    if col in p: seq.append((col,p[col][0])); stones.append((col,(ord(p[col][0][0])-97,ord(p[col][0][1])-97)) if p[col][0] else (col,(-1,-1)))
                if 'C' in p: comments.append((len(seq),p['C'][0].strip()[:120]))
            tf=xform_for(stones)
            if not tf: pv.append({"skip":"orientation"}); continue
            setup=[f"{c}:{g(tf,'%c%c'%(x+97,y+97))}" for c,(x,y) in stones[:len(stones)-len(seq)]]
            pv.append({"setup":setup,"seq":" ".join(f"{c}:{g(tf,m)}" for c,m in seq),"comments":comments})
    out[key]=pv; time.sleep(0.5)
json.dump(out,open("../../sources/raw/igobook.json","w"),ensure_ascii=False,indent=1)
for k,v in out.items():
    print("=====",k)
    for p in v:
        if "skip" in p: print("  (skip: different joseki orientation)"); continue
        print("  setup:"," ".join(p["setup"]),"| seq:",p["seq"])
        for n,c in p["comments"]: print("     @",n,c)
