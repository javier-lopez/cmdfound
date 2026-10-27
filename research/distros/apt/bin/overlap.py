"""Set overlaps for the apt family. usage: python3 -I overlap.py <cov_dir> A B [A B ...]"""
import sys, random
cov = sys.argv[1]; pairs = sys.argv[2:]
L = lambda n: set(open(f"{cov}/sets/{n}.txt").read().split())
for a, b in zip(pairs[::2], pairs[1::2]):
    A, B = L(a), L(b)
    print(f"{a}|{b}| A={len(A)} B={len(B)} A-B={len(A-B)} B-A={len(B-A)} AnB={len(A&B)}")
