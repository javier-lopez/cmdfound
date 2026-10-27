# usage: npmset.py npm-high-impact/lib/top.js OUT.txt ROWS.jsonl   (a rerun skips the rows already in ROWS.jsonl)
# reads the npm-high-impact top list, then https://registry.npmjs.org/PKG/latest of each: its bin names
import json,sys,re,http.client,threading,concurrent.futures as cf
# One keep-alive connection per thread: a fresh urlopen per package resolves DNS each time, and a
# getaddrinfo that hangs has no timeout (that stalled the first run).
T=threading.local()
def conn():
    if not hasattr(T,'c'): T.c=http.client.HTTPSConnection('registry.npmjs.org',timeout=60)
    return T.c
names=re.findall(r"^\s*'([^']+)',?$",open(sys.argv[1]).read(),re.M)
def one(p):
    for _ in range(3):
        try:
            c=conn(); c.request('GET','/'+p.replace('/','%2f')+'/latest'); r=c.getresponse(); body=r.read()
            if r.status==404: return p,[]
            if r.status!=200: raise OSError(r.status)
            d=json.loads(body)
            b=d.get('bin')
            if isinstance(b,str): return p,[p.split('/')[-1]]
            if isinstance(b,dict): return p,list(b.keys())
            return p,[]
        except Exception:
            if hasattr(T,'c'): T.c.close(); del T.c
    return p,None
# Rows go to a jsonl as they arrive, and a rerun skips the answered ones (a run can be cut short).
import os
done={}
if os.path.exists(sys.argv[3]):
    for l in open(sys.argv[3]):
        r=json.loads(l)
        if r[1] is not None: done[r[0]]=r
lk=threading.Lock(); out=open(sys.argv[3],'a')
def rec(p):
    r=one(p)
    with lk: out.write(json.dumps(r)+'\n'); out.flush()
    return r
todo=[n for n in names if n not in done]
new={r[0]:r for r in cf.ThreadPoolExecutor(8).map(rec,todo)}
rows=[done.get(n) or new[n] for n in names]
cmds={c.split('/')[-1] for _,cs in rows if cs for c in cs if c}
open(sys.argv[2],'w').write(''.join(c+'\n' for c in sorted(cmds)))
print(f"packages={len(names)} answered={sum(1 for r in rows if r[1] is not None)} with_bin={sum(1 for r in rows if r[1])} commands={len(cmds)}")
