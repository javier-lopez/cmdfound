# usage: brewset.py formula.x86_64_linux.jws.json OUT.txt
# reads https://formulae.brew.sh/api/internal/formula.x86_64_linux.jws.json: executables of formulae with a Linux bottle
import json,sys
p=json.loads(json.load(open(sys.argv[1]))['payload'])['formulae']
names=set(); nb=nexe=0
for k,v in p.items():
    if not v.get('bottle_checksum'): continue
    nb+=1
    ex=v.get('executables') or []
    if ex: nexe+=1
    names.update(e for e in ex if e and '/' not in e)
open(sys.argv[2],'w').write(''.join(n+'\n' for n in sorted(names)))
print(f"formulae={len(p)} linux_bottled={nb} with_executables={nexe} commands={len(names)}")
