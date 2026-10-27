# usage: sample.py SETS NAME...
# reads SETS/reach.txt and SETS/maps/NAME.map: 30 residual names (after reach) per set, random.seed(2026), with their packages
import os, sys, random
d = sys.argv[1]
reach = set(l.strip() for l in open(os.path.join(d, 'reach.txt')) if l.strip())
for n in sys.argv[2:]:
    m = dict(l.rstrip('\n').split('\t', 1) for l in open(os.path.join(d, 'maps', n + '.map')))
    res = sorted(set(m) - reach); random.seed(2026)
    print(f'## {n} residual={len(res)}')
    for x in sorted(random.sample(res, 30)): print(f'{x}\t{m[x][:60]}')
