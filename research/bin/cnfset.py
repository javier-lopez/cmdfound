# usage: cnfset.py OUT URL_or_FILE...
# reads Ubuntu's command-not-found index, e.g. http://archive.ubuntu.com/ubuntu/dists/resolute/main/cnf/Commands-amd64.xz; writes sets/OUT.txt, maps/OUT.map
import sys, os, lzma, subprocess
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETS, DL = os.path.join(R, 'sets'), os.path.join(R, 'dl')
out, srcs = sys.argv[1], sys.argv[2:]
cmap = {}
os.makedirs(DL, exist_ok=True)
for i, u in enumerate(srcs):
    f = u if os.path.exists(u) else os.path.join(DL, f'{out}-{i}-Commands.xz')
    if f != u:
        if subprocess.run(['curl', '-sfL', '--retry', '5', '-o', f, u]).returncode: print(f'WARN {u} failed', file=sys.stderr); continue
    pkg = None
    for line in lzma.open(f, 'rt'):
        if line.startswith('name: '): pkg = line[6:].strip()
        elif line.startswith('commands: '):
            for c in line[10:].strip().split(','): cmap.setdefault(c, set()).add(pkg)
    if f != u: os.remove(f)
os.makedirs(os.path.join(SETS, 'maps'), exist_ok=True)
open(os.path.join(SETS, out + '.txt'), 'w').write(''.join(c + '\n' for c in sorted(cmap)))
open(os.path.join(SETS, 'maps', out + '.map'), 'w').write(''.join(c + '\t' + ','.join(sorted(cmap[c])) + '\n' for c in sorted(cmap)))
print(f'{out}\tpkgs={len(set().union(*cmap.values()))}\tcmds={len(cmap)}')
