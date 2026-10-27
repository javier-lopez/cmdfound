# usage: pacset.py OUT URL_or_FILE...
# reads pacman's REPO.files (tar, gz or zstd), e.g. https://geo.mirror.pkgbuild.com/core/os/x86_64/core.files; writes sets/OUT.txt, OUT.sbin.txt, maps/OUT.map
import sys, os, re, io, subprocess, tarfile
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETS, DL = os.path.join(R, 'sets'), os.path.join(R, 'dl')
out, srcs = sys.argv[1], sys.argv[2:]
BIN = re.compile(r'^(usr/)?s?bin/([^/]+)$')
cmap, sbin, pkgs, size = {}, set(), set(), 0
os.makedirs(DL, exist_ok=True)
for i, u in enumerate(srcs):
    f = u if os.path.exists(u) else os.path.join(DL, f'{out}-{i}.files')
    if f != u: subprocess.run(['curl', '-sfL', '--retry', '5', '-A', 'Mozilla/5.0', '-o', f, u], check=True)
    data = open(f, 'rb').read(); size += len(data)
    if f != u: os.remove(f)
    if data[:4] == b'\x28\xb5\x2f\xfd': data = subprocess.run(['zstd', '-dc'], input=data, capture_output=True, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(data)) as t:
        for m in t:
            if not m.name.endswith('/files'): continue
            #the member is NAME-VERSION-RELEASE/files
            pkgs.add(m.name.split('/')[0]); pn = m.name.split('/')[0].rsplit('-', 2)[0]
            for line in t.extractfile(m).read().decode(errors='replace').splitlines():
                mm = BIN.match(line)
                if mm:
                    cmap.setdefault(mm.group(2), set()).add(pn)
                    if 'sbin' in line: sbin.add(mm.group(2))
os.makedirs(os.path.join(SETS, 'maps'), exist_ok=True)
open(os.path.join(SETS, out + '.txt'), 'w').write(''.join(c + '\n' for c in sorted(cmap)))
open(os.path.join(SETS, out + '.sbin.txt'), 'w').write(''.join(c + '\n' for c in sorted(sbin)))
open(os.path.join(SETS, 'maps', out + '.map'), 'w').write(''.join(c + '\t' + ','.join(sorted(cmap[c])) + '\n' for c in sorted(cmap)))
print(f'{out}\tindex_bytes={size}\tpkgs={len(pkgs)}\tcmds={len(cmap)}\tsbin={len(sbin)}')
