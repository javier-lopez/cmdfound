# usage: voidset.py OUT XLOCATE_DIR index.plist...
# reads an xlocate clone (https://repo-default.voidlinux.org/xlocate/xlocate.git, a file list per pkgver of the x86_64 glibc repo),
# keeping the packages named in the repodata index.plist files; writes sets/OUT.txt, OUT.sbin.txt, maps/OUT.map
import sys, os, re, plistlib
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETS = os.path.join(R, 'sets')
out, xl, plists = sys.argv[1], sys.argv[2], sys.argv[3:]
names = set()
for p in plists: names |= set(plistlib.load(open(p, 'rb')).keys())
BIN = re.compile(r'^(/usr)?/s?bin/([^/]+)$')
cmap, sbin, found = {}, set(), set()
for f in os.listdir(xl):
    if f.startswith('.'): continue
    n = f.rsplit('-', 1)[0]
    if n not in names: continue
    found.add(n)
    for line in open(os.path.join(xl, f), errors='replace'):
        m = BIN.match(line.split(' -> ')[0].strip())
        if m:
            cmap.setdefault(m.group(2), set()).add(n)
            if 'sbin' in line: sbin.add(m.group(2))
os.makedirs(os.path.join(SETS, 'maps'), exist_ok=True)
open(os.path.join(SETS, out + '.txt'), 'w').write(''.join(c + '\n' for c in sorted(cmap)))
open(os.path.join(SETS, out + '.sbin.txt'), 'w').write(''.join(c + '\n' for c in sorted(sbin)))
open(os.path.join(SETS, 'maps', out + '.map'), 'w').write(''.join(c + '\t' + ','.join(sorted(cmap[c])) + '\n' for c in sorted(cmap)))
print(f'{out}\trepo_pkgs={len(names)}\twith_filelist={len(found)}\tcmds={len(cmap)}\tsbin={len(sbin)}')
