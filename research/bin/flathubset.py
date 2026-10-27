# usage: flathubset.py appstream.json OUT.txt [ROWS.json]
# reads https://flathub.org/api/v2/appstream (app ids), then /api/v2/summary/ID of each: the x86_64 apps' declared command
import json,sys,urllib.request,concurrent.futures as cf
ids=json.load(open(sys.argv[1])); out=sys.argv[2]
def get(i):
    for _ in range(3):
        try:
            with urllib.request.urlopen(f"https://flathub.org/api/v2/summary/{i}",timeout=30) as r:
                d=json.load(r); m=d.get('metadata') or {}
                return i,m.get('command'),'x86_64' in (d.get('arches') or [])
        except Exception as e: err=e
    return i,None,None
rows=list(cf.ThreadPoolExecutor(16).map(get,ids))
json.dump(rows,open(sys.argv[3],'w')) if len(sys.argv)>3 else None
cmds={c.rsplit('/',1)[-1] for i,c,x in rows if c and x}
open(out,'w').write(''.join(c+'\n' for c in sorted(cmds)))
print(f"apps={len(ids)} answered={sum(1 for r in rows if r[2] is not None)} x86_64_with_command={sum(1 for i,c,x in rows if c and x)} commands={len(cmds)}")
