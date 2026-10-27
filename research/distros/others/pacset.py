# usage: pacset.py OUTNAME URL.files... -> sets/OUTNAME.txt, .sbin.txt
import sys, re, subprocess, os, tarfile, io
out, urls = sys.argv[1], sys.argv[2:]
base = os.path.dirname(os.path.abspath(__file__)); sets = os.path.join(base, '..', 'sets')
BIN = re.compile(r'^(usr/)?s?bin/([^/]+)$')
cmds, sbin, pkgs, size = set(), set(), set(), 0
for u in urls:
    data = subprocess.run(['curl', '-sfL', u], check=True, capture_output=True).stdout; size += len(data)
    if data[:4] == b'\x28\xb5\x2f\xfd': data = subprocess.run(['zstd', '-dc'], input=data, capture_output=True, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(data)) as t:
        for m in t:
            if m.name.endswith('/files'):
                pkgs.add(m.name.split('/')[0])
                for line in t.extractfile(m).read().decode().splitlines():
                    mm = BIN.match(line)
                    if mm:
                        cmds.add(mm.group(2))
                        if 'sbin' in line: sbin.add(mm.group(2))
open(os.path.join(sets, out + '.txt'), 'w').write(''.join(c + '\n' for c in sorted(cmds)))
open(os.path.join(sets, out + '.sbin.txt'), 'w').write(''.join(c + '\n' for c in sorted(sbin)))
print(f'{out}\tindex_bytes={size}\tpkgs={len(pkgs)}\tcmds={len(cmds)}\tsbin={len(sbin)}')
