"""Measure commands in PPAs (noble, amd64) that the Ubuntu 24.04 archive set lacks.
usage: python3 -I ppa.py <cov_dir> <workdir> owner/name ..."""
import sys, os, re, lzma, gzip, json, subprocess, urllib.request, concurrent.futures as cf
cov, work = sys.argv[1], sys.argv[2]; ppas = sys.argv[3:]
ub = set(open(f"{cov}/sets/ubuntu-24.04.txt").read().split())
ubpk = set(open(f"{work}/noble.pkgnames").read().split())
CAP = 1_500_000_000
BIN = re.compile(r'^\./(?:usr/)?s?bin/([^/]+)$')
def get(u):
    with urllib.request.urlopen(u, timeout=120) as r: return r.read()
def packages(base):
    for ext, dec in (("xz", lzma.decompress), ("gz", gzip.decompress)):
        try: return dec(get(f"{base}/dists/noble/main/binary-amd64/Packages.{ext}")).decode()
        except Exception: pass
    return None
def listdeb(url, path):
    with urllib.request.urlopen(url, timeout=600) as r, open(path, "wb") as f:
        while (b := r.read(1 << 20)): f.write(b)
    out = subprocess.run(["dpkg-deb", "--fsys-tarfile", path], capture_output=True).stdout
    os.unlink(path)
    names = subprocess.run(["tar", "-t"], input=out, capture_output=True).stdout.decode(errors="replace").split("\n")
    return {m.group(1) for n in names if (m := BIN.match(n))}
res = {}
for p in ppas:
    owner, name = p.split("/")
    base = f"https://ppa.launchpadcontent.net/{owner}/{name}/ubuntu"
    txt = packages(base)
    if txt is None: res[p] = {"error": "no noble amd64"}; print(p, "no noble", flush=True); continue
    st = [dict(re.findall(r'^([A-Za-z-]+): (.*)$', s, re.M)) for s in txt.split("\n\n") if s.strip()]
    st = [s for s in st if not re.search(r'-dbg(sym)?$', s["Package"])]
    st.sort(key=lambda s: int(s.get("Size", 0)))
    take, tot, skipped = [], 0, []
    for s in st:
        if tot + int(s["Size"]) > CAP: skipped.append(s["Package"]); continue
        tot += int(s["Size"]); take.append(s)
    cmds = {}
    with cf.ThreadPoolExecutor(8) as ex:
        fut = {ex.submit(listdeb, f"{base}/{s['Filename']}", f"{work}/deb.{owner}.{name}.{i}.deb"): s["Package"] for i, s in enumerate(take)}
        for f in cf.as_completed(fut):
            try:
                for c in f.result(): cmds.setdefault(c, set()).add(fut[f])
            except Exception as e: skipped.append(fut[f] + ":" + str(e)[:40])
    new = sorted(c for c in cmds if c not in ub)
    res[p] = {"pkgs": len(st), "pkgs_not_in_archive": sum(s["Package"] not in ubpk for s in st), "bytes": tot,
              "cmds": len(cmds), "new": new, "new_from": {c: sorted(cmds[c]) for c in new}, "skipped": skipped}
    print(p, len(st), "pkgs", len(cmds), "cmds", len(new), "new", f"{tot/1e6:.0f}MB", "skipped", len(skipped), flush=True)
json.dump(res, open(f"{work}/ppa-result.json", "w"), indent=1)
