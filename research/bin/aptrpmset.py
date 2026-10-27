# usage: aptrpmset.py OUT URL_or_FILE...
# reads apt-rpm pkglist.*.{xz,bz2} (concatenated rpm headers), e.g. https://ftp.altlinux.org/pub/distributions/ALTLinux/Sisyphus/x86_64/base/pkglist.classic.xz; writes sets/OUT.txt, OUT.sbin.txt, maps/OUT.map
import sys, os, re, lzma, bz2, struct, subprocess
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETS, DL = os.path.join(R, 'sets'), os.path.join(R, 'dl')
out, srcs = sys.argv[1], sys.argv[2:]
BIN = re.compile(r'^(/usr)?/s?bin/$')
cmap, sbin, pkgs = {}, set(), set()
def hdrs(b):
    i = 0
    while i + 16 <= len(b):
        assert b[i:i+3] == b'\x8e\xad\xe8', i
        n, ds = struct.unpack('>II', b[i+8:i+16]); idx = b[i+16:i+16+16*n]; st = i + 16 + 16*n; data = b[st:st+ds]
        tags = {}
        for k in range(n):
            t, ty, off, cnt = struct.unpack('>IIII', idx[16*k:16*k+16]); tags[t] = (ty, off, cnt)
        yield tags, data; i = st + ds
def strs(data, e):
    ty, off, cnt = e; res = []
    if ty == 6: return [data[off:data.index(b'\0', off)].decode('utf-8', 'replace')]
    p = off
    for _ in range(cnt):
        q = data.index(b'\0', p); res.append(data[p:q].decode('utf-8', 'replace')); p = q + 1
    return res
def ints(data, e):
    ty, off, cnt = e; return list(struct.unpack('>%dI' % cnt, data[off:off+4*cnt]))
os.makedirs(DL, exist_ok=True)
for i, u in enumerate(srcs):
    f = u if os.path.exists(u) else os.path.join(DL, f'{out}-{i}-' + os.path.basename(u))
    if f != u: subprocess.run(['curl', '-sfL', '--retry', '5', '-A', 'Mozilla/5.0', '-o', f, u], check=True)
    b = (bz2.open if open(f, 'rb').read(3) == b'BZh' else lzma.open)(f).read()
    if f != u: os.remove(f)
    for tags, data in hdrs(b):
        pn = strs(data, tags[1000])[0]; pkgs.add(pn)
        if 1117 not in tags: continue
        #1117 basenames, 1118 dirnames, 1116 the dirname index of each basename
        bn = strs(data, tags[1117]); dn = strs(data, tags[1118]); di = ints(data, tags[1116])
        for name, d in zip(bn, di):
            if BIN.match(dn[d]):
                cmap.setdefault(name, set()).add(pn)
                if 'sbin' in dn[d]: sbin.add(name)
os.makedirs(os.path.join(SETS, 'maps'), exist_ok=True)
open(os.path.join(SETS, out + '.txt'), 'w').write(''.join(c + '\n' for c in sorted(cmap)))
open(os.path.join(SETS, out + '.sbin.txt'), 'w').write(''.join(c + '\n' for c in sorted(sbin)))
open(os.path.join(SETS, 'maps', out + '.map'), 'w').write(''.join(c + '\t' + ','.join(sorted(cmap[c])) + '\n' for c in sorted(cmap)))
print(f'{out}\tpkgs={len(pkgs)}\tcmds={len(cmap)}\tsbin={len(sbin)}')
