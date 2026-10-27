# usage: voidset.py OUTNAME XLOCATE_DIR index.plist... -> sets/OUTNAME.txt, .sbin.txt
# xlocate (repo-default.voidlinux.org/xlocate/xlocate.git) has one file per pkgver listing its files
# (built from the x86_64 glibc repo); packages are selected by pkgname from the given repodata.
import sys, os, re, plistlib
out, xl, plists = sys.argv[1], sys.argv[2], sys.argv[3:]
base = os.path.dirname(os.path.abspath(__file__)); sets = os.path.join(base, '..', 'sets')
names = set()
for p in plists: names |= set(plistlib.load(open(p, 'rb')).keys())
BIN = re.compile(r'^(/usr)?/s?bin/([^/]+)$')
cmds, sbin, found = set(), set(), set()
for f in os.listdir(xl):
    if f.startswith('.'): continue
    n = f.rsplit('-', 1)[0]
    if n not in names: continue
    found.add(n)
    for line in open(os.path.join(xl, f), errors='replace'):
        m = BIN.match(line.split(' -> ')[0].strip())
        if m:
            cmds.add(m.group(2))
            if 'sbin' in line: sbin.add(m.group(2))
open(os.path.join(sets, out + '.txt'), 'w').write(''.join(c + '\n' for c in sorted(cmds)))
open(os.path.join(sets, out + '.sbin.txt'), 'w').write(''.join(c + '\n' for c in sorted(sbin)))
print(f'{out}\trepo_pkgs={len(names)}\twith_filelist={len(found)}\tcmds={len(cmds)}\tsbin={len(sbin)}')
