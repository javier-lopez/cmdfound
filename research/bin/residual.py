# usage: residual.py SETS table [NAME...] | residual.py SETS new [--lists DIR] NAME... | residual.py SETS overlap A B [A B ...]
# reads SETS/*.txt and SETS/reach.txt (baseline plus the branch's rows)
#   table: per NAME, the residual after reach, what is left after every other set, its biggest absorber; greedy over NAMEs; family overlaps
#   new: per NAME, new vs the bare baseline, vs planned, vs reach, vs reach once toolchain/versioned/script names are dropped, vs every other set
#   overlap: sizes and differences of each pair
import sys, os, re
d, mode, args = sys.argv[1], sys.argv[2], sys.argv[3:]
rd = lambda n: set(l.strip() for l in open(os.path.join(d, n + '.txt')) if l.strip())
alls = sorted(f[:-4] for f in os.listdir(d) if f.endswith('.txt') and not f.endswith('.sbin.txt'))
if mode == 'overlap':
    for x, y in zip(args[::2], args[1::2]):
        A, B = rd(x), rd(y); print(f'{x}|{y}| A={len(A)} B={len(B)} A-B={len(A-B)} B-A={len(B-A)} AnB={len(A&B)}')
    sys.exit()
reach = rd('reach')
others = [n for n in alls if n != 'reach']
sets = {n: rd(n) for n in others}
if mode == 'new':
    lists = None
    if args[:1] == ['--lists']: lists, args = args[1], args[2:]
    bare = sets['current-union-bare']
    planned = bare | sets['ubuntu-26.04'] | sets['fedora-44'] | sets['opensuse-tumbleweed'] | sets['wolfi']
    X = re.compile(r'(-linux-|-w64-|mingw|-elf-|-none-|-cros-|-chimera-)|(-?[0-9]+(\.[0-9]+)+)$|-[0-9]+$|\.(sh|py|pl|R|rb|jl|txt|md|json|yaml|so[.0-9]*|Rmd|DAT)$')
    for n in args:
        s = sets[n]; o = set().union(*(sets[k] for k in others if k != n and not k.startswith(n + '.')))
        new = s - reach; new2 = sorted(new - o); clean = {x for x in new if not X.search(x)}
        print(f'{n}\tcmds={len(s)}\tnew_vs_bare={len(s - bare)}\tnew_vs_planned={len(s - planned)}\tnew_vs_reach={len(new)}\tclean_new={len(clean)}'
              f'\tnew_vs_all_sets={len(new2)}\tin_nixpkgs={len(s & sets["nixpkgs"])}\tsample={new2[:: max(1, len(new2)//10)][:10]}')
        if lists:
            open(os.path.join(lists, n + '.new-vs-planned.txt'), 'w').write(''.join(x + '\n' for x in sorted(s - planned)))
            open(os.path.join(lists, n + '.new-vs-all.txt'), 'w').write(''.join(x + '\n' for x in new2))
    sys.exit()
C = args or ['rosa-13', 'pld-th', 'aosc', 'deepin-25', 'openkylin-nile', 'pclinuxos', 'julia-jll', 'terra-44', 'chimera', 'oneapi-opt']
res = {n: sets[n] - reach for n in C}
print('| candidate | (a) after reach | (b) unique: after reach + every other set | biggest absorber of (a) |')
for n in C:
    o = set().union(*(sets[k] for k in others if k != n and not k.startswith(n)))
    absorb = max((k for k in others if k != n), key=lambda k: len(res[n] & sets[k]))
    print(f'| {n} | {len(res[n]):,} | {len(res[n] - o):,} | {absorb} ({len(res[n] & sets[absorb]):,}) |')
print('\n(c) greedy over these candidates only, on top of reach')
s = set(reach); left = list(C)
while left:
    b = max(left, key=lambda n: len(sets[n] - s)); a = len(sets[b] - s); s |= sets[b]; left.remove(b); print(f'| {b} | +{a:,} | {len(s):,} |')
print('\nfamily overlaps of residuals after reach (row ∩ col)')
for fam in (['rosa-13', 'pclinuxos', 'openmandriva-rolling', 'mageia-cauldron', 'alt-sisyphus'], ['deepin-25', 'openkylin-nile', 'debian-sid', 'kali-rolling']):
    r = {n: sets[n] - reach for n in fam}
    print('| | ' + ' | '.join(fam) + ' |')
    for a in fam: print(f'| {a} ({len(r[a]):,}) | ' + ' | '.join(f'{len(r[a] & r[b]):,}' for b in fam) + ' |')
    for a in fam[:2]:
        rest = set().union(*(r[b] for b in fam if b != a)); print(f'{a}: {len(r[a] - rest):,} of {len(r[a]):,} outside the rest of its family')
