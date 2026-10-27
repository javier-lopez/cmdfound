# usage: condapaths.py REPODATA(.json|.json.zst) CHANNEL_URL MAPFILE REACH.txt PKG...
# reads the newest .conda of each PKG (info/paths.json by HTTP range): its bin/ commands, and how many residual MAPFILE names they hold
import json, subprocess, sys, io, zipfile, tarfile, urllib.request
src, chan, mapf, reachf, names = sys.argv[1], sys.argv[2].rstrip('/'), sys.argv[3], sys.argv[4], sys.argv[5:]
raw = subprocess.run(['zstd', '-dc', src], capture_output=True).stdout if src.endswith('.zst') else open(src, 'rb').read()
d = json.loads(raw); reach = set(l.strip() for l in open(reachf))
res = {l.split('\t')[0] for l in open(mapf)} - reach
class R(io.RawIOBase):
    def __init__(s, u):
        s.u = u; s.p = 0; s.n = int(urllib.request.urlopen(urllib.request.Request(u, method='HEAD')).headers['Content-Length'])
    def seekable(s): return True
    def readable(s): return True
    def seek(s, o, w=0): s.p = {0: o, 1: s.p + o, 2: s.n + o}[w]; return s.p
    def tell(s): return s.p
    def readinto(s, b):
        if s.p >= s.n: return 0
        e = min(s.n, s.p + len(b)) - 1
        x = urllib.request.urlopen(urllib.request.Request(s.u, headers={'Range': f'bytes={s.p}-{e}'})).read(); b[:len(x)] = x; s.p += len(x); return len(x)
hit = set()
for n in names:
    c = [(p.get('timestamp', 0), f) for f, p in d.get('packages.conda', {}).items() if p['name'] == n]
    if not c: print(n, 'no .conda'); continue
    f = max(c)[1]
    z = zipfile.ZipFile(io.BufferedReader(R(f'{chan}/linux-64/{f}'), 1 << 16))
    info = [i for i in z.namelist() if i.startswith('info-')][0]
    pj = json.load(tarfile.open(fileobj=io.BytesIO(subprocess.run(['zstd', '-dc'], input=z.read(info), capture_output=True).stdout)).extractfile('info/paths.json'))
    b = {p['_path'].split('/')[-1] for p in pj['paths'] if '/bin/' in '/' + p['_path'] and p['_path'].count('/') <= 3}
    h = b & res; hit |= h; print(n, f, f'bin={len(b)} residual_hits={len(h)}')
print(f'residual={len(res)} found_in_these_packages={len(hit)}')
