# usage: pypiset.py top-pypi-packages.min.json OUT.txt ROWS.json
# reads https://hugovk.github.io/top-pypi-packages/ and, per project, the latest wheel's entry_points.txt by HTTP range: console_scripts
import json,sys,io,zipfile,urllib.request,configparser,concurrent.futures as cf
top=[r['project'] for r in json.load(open(sys.argv[1]))['rows']]; out=sys.argv[2]
class RF(io.RawIOBase):
    def __init__(s,u,n): s.u,s.n,s.p=u,n,0
    def seekable(s): return True
    def readable(s): return True
    def tell(s): return s.p
    def seek(s,o,w=0): s.p={0:o,1:s.p+o,2:s.n+o}[w]; return s.p
    def readinto(s,b):
        k=len(b)
        if k==0 or s.p>=s.n: return 0
        r=urllib.request.Request(s.u,headers={'Range':f'bytes={s.p}-{min(s.n,s.p+k)-1}'})
        d=urllib.request.urlopen(r,timeout=60).read(); b[:len(d)]=d; s.p+=len(d); return len(d)
def pick(urls):
    w=[u for u in urls if u['packagetype']=='bdist_wheel' and not u.get('yanked')]
    def score(u):
        f=u['filename']; return (0 if 'none-any' in f else 1 if 'manylinux' in f and 'x86_64' in f else 2)
    w.sort(key=score); return w[0] if w and score(w[0])<2 else None
def one(p):
    try:
        d=json.load(urllib.request.urlopen(f"https://pypi.org/pypi/{p}/json",timeout=60))
        w=pick(d['urls'])
        if not w: return p,'nowheel',[]
        z=zipfile.ZipFile(io.BufferedReader(RF(w['url'],w['size']),buffer_size=1<<16))
        e=[n for n in z.namelist() if n.endswith('.dist-info/entry_points.txt') and n.count('/')==1]
        if not e: return p,'ok',[]
        c=configparser.ConfigParser(delimiters=('=',),interpolation=None); c.optionxform=str
        c.read_string(z.read(e[0]).decode('utf-8','replace'))
        return p,'ok',sorted(c['console_scripts'].keys()) if c.has_section('console_scripts') else []
    except Exception as ex: return p,'error:'+type(ex).__name__,[]
rows=list(cf.ThreadPoolExecutor(32).map(one,top))
json.dump(rows,open(sys.argv[3],'w'))
cmds={c.strip() for _,_,cs in rows for c in cs if c.strip()}
open(out,'w').write(''.join(c+'\n' for c in sorted(cmds)))
from collections import Counter
print(Counter(s.split(':')[0] for _,s,_ in rows), 'with_scripts=',sum(1 for r in rows if r[2]),'commands=',len(cmds))
