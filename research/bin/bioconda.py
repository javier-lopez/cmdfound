# usage: bioconda.py DLDIR REACH.txt N
# reads DLDIR/{linux-64,noarch}.json.zst (https://conda.anaconda.org/bioconda/SUBDIR/repodata.json.zst), then info/paths.json of N sampled tool packages by HTTP range: an estimate of new bin/ commands
import json, subprocess, sys, random, urllib.request, zipfile, io, tarfile, os
dl, reach, N = sys.argv[1], set(l.strip() for l in open(sys.argv[2])), int(sys.argv[3])
best = {}
for s in ('linux-64', 'noarch'):
    d = json.loads(subprocess.run(['zstd', '-dc', os.path.join(dl, s + '.json.zst')], capture_output=True).stdout)
    for f, p in d.get('packages.conda', {}).items():
        if p['name'].startswith(('r-', 'bioconductor-', 'perl-', 'python-', 'py-', 'lib')): continue
        if p['name'] not in best or p.get('timestamp', 0) > best[p['name']][2]: best[p['name']] = (s, f, p.get('timestamp', 0))
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
        d = urllib.request.urlopen(urllib.request.Request(s.u, headers={'Range': f'bytes={s.p}-{e}'})).read()
        b[:len(d)] = d; s.p += len(d); return len(d)
random.seed(7); names = random.sample(sorted(best), N)
allc, newc, ok, withbin = set(), set(), 0, 0
for n in names:
    s, f, _ = best[n]
    try:
        z = zipfile.ZipFile(io.BufferedReader(R(f'https://conda.anaconda.org/bioconda/{s}/{f}'), 1 << 16))
        info = [i for i in z.namelist() if i.startswith('info-')][0]
        raw = subprocess.run(['zstd', '-dc'], input=z.read(info), capture_output=True).stdout
        pj = json.load(tarfile.open(fileobj=io.BytesIO(raw)).extractfile('info/paths.json'))
        cm = {p['_path'][4:] for p in pj['paths'] if p['_path'].startswith('bin/') and '/' not in p['_path'][4:]}
        ok += 1; withbin += bool(cm); allc |= cm; newc |= cm - reach
    except Exception as e: print('skip', n, type(e).__name__, file=sys.stderr)
print(f'tool_packages={len(best)} sampled={ok} with_bin={withbin} cmds={len(allc)} new={len(newc)} new_per_pkg={len(newc)/max(ok,1):.2f} est_new_total={int(len(newc)/max(ok,1)*len(best))}')
print(sorted(newc)[:25])
