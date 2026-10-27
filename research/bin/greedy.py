# usage: greedy.py SETS [CAND...] [--alone] [--sample NAME...] | greedy.py SETS --base reach|all NAME...
# reads every SETS/*.txt: coverage of the branch's channels, then CANDs greedily by marginal gain (default: every set not excluded below)
# --alone: each candidate's size and its gain alone after the branch; --sample: 8 seeded new names of each NAME after the branch
# --base: greedy order of NAMEs on top of reach.txt alone (reach) or of reach plus every set not in NAMEs (all)
import sys, os, re, random, argparse
ap = argparse.ArgumentParser()
ap.add_argument('sets'); ap.add_argument('cands', nargs='*')
ap.add_argument('--alone', action='store_true'); ap.add_argument('--sample', nargs='+', default=[]); ap.add_argument('--base', choices=['reach', 'all'])
a = ap.parse_intermixed_args(); d = a.sets
load = lambda n: set(open(os.path.join(d, n + '.txt')).read().split())
if a.base:
    #a line per name here; the coverage below splits on whitespace, as final.out was made
    load = lambda n: set(l.strip() for l in open(os.path.join(d, n + '.txt')) if l.strip())
    s = load('reach')
    if a.base == 'all':
        for f in os.listdir(d):
            b = f[:-4]
            if f.endswith('.txt') and b.split('.')[0] not in a.cands and b != 'reach': s |= load(b)
    sets = {n: load(n) for n in a.cands}; print(f'base={a.base} {len(s):,}')
    while sets:
        b = max(sets, key=lambda n: len(sets[n] - s)); add = len(sets[b] - s); s |= sets.pop(b)
        print(f'| {b} | +{add:,} | {len(s):,} |')
    sys.exit()
names = sorted(f[:-4] for f in os.listdir(d) if f.endswith('.txt') and not f.endswith('.sbin.txt') and not f.startswith('current-union'))
sets = {n: load(n) for n in names}
U = set().union(*sets.values())
#a name is sbin-only when it is in some sbin/ and no path-aware set has it outside sbin/
sbin_any = set().union(*(set(open(os.path.join(d, f)).read().split()) for f in os.listdir(d) if f.endswith('.sbin.txt')))
pathaware = [n for n in names if os.path.exists(os.path.join(d, n + '.sbin.txt'))]
nonsbin = set().union(*(sets[n] - set(open(os.path.join(d, n + '.sbin.txt')).read().split()) for n in pathaware))
sbinonly = sbin_any - nonsbin
ver = re.compile(r'^(.+?)(-\d[\d.]*|\d+\.\d+)$')
versioned = {c for c in U if (m := ver.match(c)) and m.group(1) in U}
U1, U2 = U - sbinonly, U - sbinonly - versioned
pct = lambda r: f"{100*len(r & U)/len(U):.1f}% | {100*len(r & U1)/len(U1):.1f}% | {100*len(r & U2)/len(U2):.1f}%"
print(f"universe {len(U):,} names from {len(names)} sets; sbin-only {len(sbinonly):,}; versioned {len(versioned):,}")
today = load('current-union-bare')
print(f"| today (bare) | {len(today):,} | {pct(today)} |")
branch = ['ubuntu-26.04', 'fedora-44', 'opensuse-tumbleweed', 'epel-10+alma-10', 'wolfi', 'arch', 'blackarch']
r = set(today)
for n in branch:
    add = len(sets[n] - r); r |= sets[n]; print(f"| +{n} | +{add:,} | {len(r):,} | {pct(r)} |")
cp = set(r)
#the baseline's parts, the branch, and the sets another one stands for (debian in ubuntu, rocky/rhel in alma+epel, ...)
EXCL = re.compile(r'current-union.*|reach|nixpkgs|alpine-3\.22|alpine-edge|aqua|pkgx|am|binstall|ubuntu-2[24]\.04|ubuntu-26\.10|debian-.*'
                  r'|fedora-43|fedora-rawhide|void-.*|epel-10|alma-10|oneapi|pclinuxos|kali-rolling')
cands = a.cands or [n for n in names if n not in branch and not EXCL.fullmatch(n)]
left = list(cands)
while left:
    best = max(left, key=lambda n: len(sets[n] - r)); add = len(sets[best] - r); r |= sets[best]; left.remove(best)
    print(f"| +{best} | +{add:,} | {len(r):,} | {pct(r)} |")
if a.alone:
    print("\n| Candidate | Commands | New after the branch (alone) |\n|---|---:|---:|")
    for n in sorted(cands, key=lambda n: -len(sets[n] - cp)): print(f"| {n} | {len(sets[n]):,} | {len(sets[n] - cp):,} |")
for n in a.sample:
    new = sorted(sets[n] - cp); random.seed(1)
    print(n, len(new), random.sample(new, min(8, len(new))))
