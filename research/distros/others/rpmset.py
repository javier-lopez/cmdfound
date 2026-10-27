# usage: rpmset.py OUTNAME KIND(primary|filelists) REPOURL...  -> sets/OUTNAME.txt, .sbin.txt; prints stats
import sys, re, subprocess, urllib.request, xml.etree.ElementTree as ET, os
out, kind, repos = sys.argv[1], sys.argv[2], sys.argv[3:]
base = os.path.dirname(os.path.abspath(__file__))
sets = os.path.join(base, '..', 'sets'); dl = os.path.join(base, 'dl')
BIN = re.compile(r'^(/usr)?/s?bin/([^/]+)$')
cmds, sbin, pkgs, size = set(), set(), set(), 0
for r in repos:
    r = r.rstrip('/') + '/'
    md = urllib.request.urlopen(r + 'repodata/repomd.xml').read().decode()
    m = re.search(r'<data type="%s">.*?<location href="([^"]+)"/>.*?<size>(\d+)</size>' % kind, md, re.S)
    href, sz = m.group(1), int(m.group(2)); size += sz
    f = os.path.join(dl, out + '-' + os.path.basename(href))
    subprocess.run(['curl', '-sfL', '-o', f, r + href], check=True)
    dec = {'zst': ['zstd', '-dc'], '.gz': ['gzip', '-dc'], '.xz': ['xz', '-dc']}[href[-3:]]
    p = subprocess.Popen(dec + [f], stdout=subprocess.PIPE)
    for ev, el in ET.iterparse(p.stdout):
        t = el.tag.split('}')[1]
        if t == 'package':
            a = el.get('arch') or el.find('{*}arch').text
            if a not in ('x86_64', 'noarch'): el.clear(); continue
            n = el.get('name') or el.find('{*}name').text; pkgs.add(n)
            for fe in el.iter():
                if fe.tag.endswith('}file') and fe.get('type') != 'dir' and fe.text:
                    mm = BIN.match(fe.text)
                    if mm:
                        cmds.add(mm.group(2))
                        if 'sbin' in fe.text: sbin.add(mm.group(2))
            el.clear()
    p.wait(); os.remove(f)
open(os.path.join(sets, out + '.txt'), 'w').write(''.join(c + '\n' for c in sorted(cmds)))
open(os.path.join(sets, out + '.sbin.txt'), 'w').write(''.join(c + '\n' for c in sorted(sbin)))
print(f'{out}\t{kind}\tindex_bytes={size}\tpkgs={len(pkgs)}\tcmds={len(cmds)}\tsbin={len(sbin)}')
