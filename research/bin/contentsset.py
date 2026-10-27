# usage: contentsset.py OUT URL_or_FILE...   (env BINRE: path regex, its last group is the command)
# reads apt Contents-amd64.{gz,bz2,xz,zst} (path, then pkg list), e.g. http://deb.debian.org/debian/dists/sid/main/Contents-amd64.gz; writes sets/OUT.txt, OUT.sbin.txt, maps/OUT.map
import sys, os, re, subprocess
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETS, DL = os.path.join(R, 'sets'), os.path.join(R, 'dl')
out, srcs = sys.argv[1], sys.argv[2:]
BIN = re.compile(os.environ.get('BINRE', r'^/?(usr/)?(local/)?s?bin/([^/]+)$'))
cmap, sbin, size = {}, set(), 0
def unpack(f):
    m = open(f, 'rb').read(6)
    for magic, dec in ((b'\x1f\x8b', 'gzip'), (b'BZh', 'bzip2'), (b'\xfd7zXZ', 'xz'), (b'\x28\xb5\x2f\xfd', 'zstd')):
        if m.startswith(magic): return subprocess.Popen([dec, '-dc', f], stdout=subprocess.PIPE, text=True, errors='replace')
    return subprocess.Popen(['cat', f], stdout=subprocess.PIPE, text=True, errors='replace')
os.makedirs(DL, exist_ok=True)
for i, u in enumerate(srcs):
    f = u if os.path.exists(u) else os.path.join(DL, f'{out}-{i}-' + os.path.basename(u))
    if f != u:
        r = subprocess.run(['curl', '-sfL', '--retry', '5', '--retry-all-errors', '-A', 'Mozilla/5.0', '-o', f, u])
        if r.returncode: print(f'WARN {u} failed', file=sys.stderr); continue
    size += os.path.getsize(f)
    p = unpack(f)
    for l in p.stdout:
        #the package list is the last field; the path is the rest
        sp = l.rstrip('\n').rsplit(None, 1)
        if len(sp) != 2: continue
        path, loc = sp[0].rstrip(), sp[1]
        m = BIN.match(path)
        if m:
            c = m.group(m.re.groups); cmap.setdefault(c, set()).update(x.split('/')[-1] for x in loc.split(','))
            if 'sbin/' in path: sbin.add(c)
    p.wait()
    if f != u: os.remove(f)
os.makedirs(os.path.join(SETS, 'maps'), exist_ok=True)
open(os.path.join(SETS, out + '.txt'), 'w').write(''.join(c + '\n' for c in sorted(cmap)))
open(os.path.join(SETS, out + '.sbin.txt'), 'w').write(''.join(c + '\n' for c in sorted(sbin)))
open(os.path.join(SETS, 'maps', out + '.map'), 'w').write(''.join(c + '\t' + ','.join(sorted(cmap[c])) + '\n' for c in sorted(cmap)))
print(f'{out}\tcontents_bytes={size}\tpkgs_with_cmds={len(set().union(*cmap.values()))}\tcmds={len(cmap)}\tsbin={len(sbin)}')
