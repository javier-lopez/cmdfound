# usage: ratio.py SETS CHANNELS_DIR
# what each channel costs in bytes against the commands only it brings: the
# unique ones, greedy (each after the ones above it), per MB its index downloads
# and per MB of index plus its image, downloaded once. Markdown, by ratio.
# Index bytes are cmdfound's own (index bytes, nothing fetched); an image is
# its amd64 manifest's compressed size; homebrew is a candidate, not a channel
import sys, os, subprocess, json, urllib.request, tempfile, re
SETS, CH = sys.argv[1], sys.argv[2]
IN = os.path.join(os.path.dirname(CH), 'cmdfound.in')
# channel, set, and for a candidate its index url, image, and bytes once on top of the image
ROWS = [('am', 'am'), ('aqua', 'aqua'), ('pkgx', 'pkgx'), ('nix-portable', 'nixpkgs'),
        ('alpine', 'alpine-3.22'), ('wolfi', 'wolfi'), ('ubuntu', 'ubuntu-26.04'), ('alt', 'alt-p11'),
        ('fedora', 'fedora-44'), ('opensuse', 'opensuse-tumbleweed'), ('epel', 'epel-10+alma-10'),
        ('rosa', 'rosa-13'), ('arch', 'arch'), ('blackarch', 'blackarch'), ('chaotic-aur', 'chaotic-aur')]
CANDS = {'homebrew': ('homebrew-linux', 'https://formulae.brew.sh/api/internal/formula.x86_64_linux.jws.json',
                      'docker.io/library/ubuntu:26.04', 52_000_000)}

def names(s):
    p = os.path.join(SETS, s + '.txt')
    return set(l.split('\t')[0].strip() for l in open(p) if l.strip()) if os.path.exists(p) else None

def run(*a):
    env = dict(os.environ, CMDFOUND_CHANNELS=CH, CMDFOUND_HOME=tempfile.mkdtemp())
    try: return subprocess.run(['sh', IN] + list(a), env=env, capture_output=True, text=True, timeout=600).stdout
    except Exception: return ''

def index_bytes(ch):
    m = re.search(r'^bytes=(\d+)$', run('--channel', ch, 'index', 'bytes'), re.M)
    return int(m.group(1)) if m else None

def head(url):
    r = urllib.request.Request(url, method='HEAD', headers={'Accept-Encoding': 'gzip'})
    with urllib.request.urlopen(r, timeout=60) as f: return int(f.headers.get('Content-Length') or 0) or None

def image_of(ch):
    for f in [os.path.join(d, ch) for d, _, fs in os.walk(CH) if ch in fs]:
        m = re.search(r'^REPOSITORY="([^"]+)"\s*$.*?^TAG="([^"]+)"', open(f).read(), re.M | re.S)
        if m:
            tag = m.group(2)
            if '${RELEASE}' in tag: tag = re.search(r'^RELEASE="([^"]+)"', open(f).read(), re.M).group(1)
            return 'docker.io/%s:%s' % (m.group(1), tag)
    return None

def image_bytes(ref):
    repo, tag = ref.split('/', 1)[1].rsplit(':', 1)
    tok = json.load(urllib.request.urlopen('https://auth.docker.io/token?service=registry.docker.io&scope=repository:%s:pull' % repo, timeout=60))['token']
    acc = ','.join(['application/vnd.oci.image.index.v1+json', 'application/vnd.docker.distribution.manifest.list.v2+json',
                    'application/vnd.oci.image.manifest.v1+json', 'application/vnd.docker.distribution.manifest.v2+json'])
    def get(ref2):
        r = urllib.request.Request('https://registry-1.docker.io/v2/%s/manifests/%s' % (repo, ref2), headers={'Authorization': 'Bearer ' + tok, 'Accept': acc})
        return json.load(urllib.request.urlopen(r, timeout=60))
    m = get(tag)
    if 'manifests' in m:
        m = get(next(x['digest'] for x in m['manifests'] if x.get('platform', {}).get('architecture') == 'amd64' and x['platform'].get('os') == 'linux'))
    return m['config']['size'] + sum(l['size'] for l in m['layers'])

sets = {}
for ch, s in ROWS:
    n = names(s)
    if n is not None: sets[ch] = n
for c, (s, *_ ) in CANDS.items():
    n = names(s)
    if n is not None: sets[c] = n
# greedy over the channels; a candidate is measured after all of them
have, uniq, left = set(), {}, {c: sets[c] for c, _ in ROWS if c in sets}
while left:
    c = max(left, key=lambda k: len(left[k] - have)); uniq[c] = len(left[c] - have); have |= left.pop(c)
for c in CANDS:
    if c in sets: uniq[c] = len(sets[c] - have)

rows = []
for ch, _ in ROWS + [(c, None) for c in CANDS]:
    if ch not in uniq: continue
    if ch in CANDS:
        _, url, img, once = CANDS[ch]
        ib = head(url); imb = image_bytes(img) + once
    else:
        ib = index_bytes(ch); img = image_of(ch); imb = image_bytes(img) if img else 0
    rows.append((ch, ib, imb, len(sets[ch]), uniq[ch]))

mb = lambda b: b / 1e6
def ratio(u, b): return u / mb(b) if b else None
out = sorted(rows, key=lambda r: -(ratio(r[4], r[1]) or 0))
print('| channel | index MB | image MB | commands | unique | unique/MB index | unique/MB index+image |')
print('|---|---:|---:|---:|---:|---:|---:|')
fmt = lambda v, d=0: '-' if v is None else f'{v:,.{d}f}'
for ch, ib, imb, n, u in out:
    name = ch + (' (candidate)' if ch in CANDS else '')
    print(f'| {name} | {fmt(ib and mb(ib), 1)} | {fmt(mb(imb), 0) if imb else "-"} | {n:,} | {u:,} | {fmt(ratio(u, ib))} | {fmt(ratio(u, (ib or 0) + imb))} |')
