# usage: apkset.py [--newest] OUT URL_or_FILE...   (--newest: only the newest build of each package, as wolfi keeps every version)
# reads APKINDEX.tar.gz (p: cmd: provides), e.g. https://dl-cdn.alpinelinux.org/alpine/v3.22/main/x86_64/APKINDEX.tar.gz; writes sets/OUT.txt, maps/OUT.map
import sys, os, io, tarfile, subprocess, time
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETS, DL = os.path.join(R, 'sets'), os.path.join(R, 'dl')
args = sys.argv[1:]
newest_only = args[0] == '--newest'
if newest_only: args = args[1:]
out, srcs = args[0], args[1:]
size, newest, signed, nblk, best, allc = 0, 0, set(), 0, {}, set()
os.makedirs(DL, exist_ok=True)
for i, u in enumerate(srcs):
    f = u if os.path.exists(u) else os.path.join(DL, f'{out}-{i}-APKINDEX.tar.gz')
    if f != u: subprocess.run(['curl', '-sfL', '--retry', '5', '-A', 'Mozilla/5.0', '-o', f, u], check=True)
    b = open(f, 'rb').read(); size += len(b)
    if f != u: os.remove(f)
    tf = tarfile.open(fileobj=io.BytesIO(b))
    signed |= {m.name for m in tf.getmembers() if m.name.startswith('.SIGN')}
    for blk in tf.extractfile('APKINDEX').read().decode(errors='replace').split('\n\n'):
        d = dict(l.split(':', 1) for l in blk.splitlines() if len(l) > 1 and l[1] == ':')
        if 'P' not in d: continue
        nblk += 1; t = int(d.get('t', 0)); newest = max(newest, t)
        c = {x[4:].split('=')[0] for x in d.get('p', '').split() if x.startswith('cmd:')}
        allc |= c; pkg = d.get('o', d['P'])
        #one key per build unless --newest, so every build's commands count
        key = d['P'] if newest_only else (d['P'], d.get('V'), i)
        if key not in best or t > best[key][0]: best[key] = (t, c, pkg)
cmap = {}
for t, c, pkg in best.values():
    for x in c: cmap.setdefault(x, set()).add(pkg)
os.makedirs(os.path.join(SETS, 'maps'), exist_ok=True)
open(os.path.join(SETS, out + '.txt'), 'w').write(''.join(c + '\n' for c in sorted(cmap)))
open(os.path.join(SETS, 'maps', out + '.map'), 'w').write(''.join(c + '\t' + ','.join(sorted(cmap[c])) + '\n' for c in sorted(cmap)))
print(f'{out}\tindex_bytes={size}\tpkgs={nblk}\tnames={len({k[0] if isinstance(k, tuple) else k for k in best})}\tcmds={len(cmap)}'
      f'\tcmds_any_version={len(allc)}\tnewest={time.strftime("%Y-%m-%d", time.gmtime(newest))}\tsig={",".join(sorted(signed)) or "none"}')
