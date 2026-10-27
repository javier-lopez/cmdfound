# usage: snapset.py PAGES_DIR OUT.txt
# reads the Snap Store search pages snapfetch.sh saved: /snap/bin names whose app is named like its snap (snap.app names are counted, not written)
import json,sys,glob,os
snaps={}; 
for f in glob.glob(os.path.join(sys.argv[1],'page-*.json')):
    for p in json.load(open(f))['_embedded']['clickindex:package']:
        snaps[p['package_name']]=p
cmds=set(); conf={}
for n,p in snaps.items():
    conf[p.get('confinement')]=conf.get(p.get('confinement'),0)+1
    for a in p.get('apps') or []:
        cmds.add(n if a==n else f"{n}.{a}")
bare={c for c in cmds if '.' not in c}
open(sys.argv[2],'w').write(''.join(c+'\n' for c in sorted(bare)))
print(f"snaps={len(snaps)} with_apps={sum(1 for p in snaps.values() if p.get('apps'))} commands={len(cmds)} undotted={len(bare)} confinement={conf}")
