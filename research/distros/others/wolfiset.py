# usage: wolfiset.py APKINDEX -> sets/wolfi.txt (cmd: provides of the newest build of each package)
import sys, os
base = os.path.dirname(os.path.abspath(__file__)); sets = os.path.join(base, '..', 'sets')
best, allc = {}, set()
for blk in open(sys.argv[1]).read().split('\n\n'):
    f = dict(l.split(':', 1) for l in blk.splitlines() if len(l) > 1 and l[1] == ':')
    if 'P' not in f: continue
    c = {x[4:].split('=')[0] for x in f.get('p', '').split() if x.startswith('cmd:')}
    allc |= c
    t = int(f.get('t', 0))
    if f['P'] not in best or t > best[f['P']][0]: best[f['P']] = (t, c)
cur = set().union(*(c for t, c in best.values()))
open(os.path.join(sets, 'wolfi.txt'), 'w').write(''.join(x + '\n' for x in sorted(cur)))
print(f"wolfi\tpkgs={len(best)}\tcmds_newest={len(cur)}\tcmds_any_version={len(allc)}")
