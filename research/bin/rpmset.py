# usage: rpmset.py [--compare] OUT primary|filelists REPOURL...   (env BINRE: path regex, its last group is the command)
# reads REPOURL/repodata/repomd.xml and its primary or filelists; writes sets/OUT.txt, OUT.sbin.txt, maps/OUT.map
# --compare: reads the index, writes nothing, and reports the names of sets/OUT.txt it lacks (primary vs filelists)
import sys, os, re, subprocess, urllib.request, xml.etree.ElementTree as ET, time
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETS, DL = os.path.join(R, 'sets'), os.path.join(R, 'dl')
args = sys.argv[1:]
compare = args[0] == '--compare'
if compare: args = args[1:]
out, kind, repos = args[0], args[1], args[2:]
assert kind in ('primary', 'filelists'), kind
BIN = re.compile(os.environ.get('BINRE', r'^(/usr)?(/local)?/s?bin/([^/]+)$'))
cmap, sbin, pkgs, size, newest, signed = {}, set(), set(), 0, 0, set()
def get(u): return urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60).read()
def unpack(f):
    m = open(f, 'rb').read(6)
    for magic, dec in ((b'\x1f\x8b', 'gzip'), (b'BZh', 'bzip2'), (b'\xfd7zXZ', 'xz'), (b'\x28\xb5\x2f\xfd', 'zstd')):
        if m.startswith(magic): return subprocess.Popen([dec, '-dc', f], stdout=subprocess.PIPE)
    return subprocess.Popen(['cat', f], stdout=subprocess.PIPE)
os.makedirs(DL, exist_ok=True)
for r in repos:
    r = r.rstrip('/') + '/'
    md = get(r + 'repodata/repomd.xml').decode()
    try: get(r + 'repodata/repomd.xml.asc'); signed.add('asc')
    except Exception: signed.add('no-asc')
    newest = max([newest] + [int(x) for x in re.findall(r'<timestamp>(\d+)</timestamp>', md)])
    blk = re.search(r'<data type="%s">(.*?)</data>' % kind, md, re.S).group(1)
    href = re.search(r'<location href="([^"]+)"', blk).group(1)
    sz = re.search(r'<size>(\d+)</size>', blk); size += int(sz.group(1)) if sz else 0
    f = os.path.join(DL, out + '-' + os.path.basename(href))
    subprocess.run(['curl', '-sfL', '--retry', '5', '--retry-all-errors', '-C', '-', '-A', 'Mozilla/5.0', '-o', f, r + href], check=True)
    p = unpack(f)
    for ev, el in ET.iterparse(p.stdout):
        if el.tag.split('}')[-1] != 'package': continue
        #filelists carries arch and name as attributes, primary as children
        a = el.get('arch') or el.findtext('{*}arch') or ''
        if a in ('x86_64', 'noarch', ''):
            pn = el.get('name') or el.findtext('{*}name'); pkgs.add(pn)
            for fe in el.iter():
                if fe.tag.split('}')[-1] == 'file' and fe.get('type') != 'dir' and fe.text:
                    m = BIN.match(fe.text)
                    if m:
                        c = m.group(m.re.groups); cmap.setdefault(c, set()).add(pn)
                        if 'sbin' in fe.text: sbin.add(c)
        el.clear()
    p.wait(); os.remove(f)
stats = f'{out}\t{kind}\tindex_bytes={size}\tnewest={time.strftime("%Y-%m-%d", time.gmtime(newest))}\tsig={",".join(sorted(signed))}\tpkgs={len(pkgs)}\tcmds={len(cmap)}'
if compare:
    full = set(open(os.path.join(SETS, out + '.txt')).read().split())
    print(f'{stats}\tin_sets={len(full)}\tmissing_from_{kind}={len(full - set(cmap))}'); sys.exit()
os.makedirs(os.path.join(SETS, 'maps'), exist_ok=True)
open(os.path.join(SETS, out + '.txt'), 'w').write(''.join(c + '\n' for c in sorted(cmap)))
open(os.path.join(SETS, out + '.sbin.txt'), 'w').write(''.join(c + '\n' for c in sorted(sbin)))
open(os.path.join(SETS, 'maps', out + '.map'), 'w').write(''.join(c + '\t' + ','.join(sorted(cmap[c])) + '\n' for c in sorted(cmap)))
print(f'{stats}\tsbin={len(sbin)}')
