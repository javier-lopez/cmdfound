# usage: xcmdset.py PKG_DIR OUT.txt
# reads the x-cmd pkg catalog (https://raw.githubusercontent.com/x-cmd/pkg/main/dist/vX.tar.gz): packages with linux/x64, plus binmod.txt aliases
import os,sys,re
root=sys.argv[1]; pk={}; lin=set()
for cat in os.listdir(root):
    p=os.path.join(root,cat)
    if not os.path.isdir(p): continue
    for n in os.listdir(p):
        v=os.path.join(p,n,'version.tt.json')
        if os.path.isfile(v):
            pk[n]=cat
            if '"linux/x64"' in open(v).read(): lin.add(n)
cmds=set(lin)
for l in open(os.path.join(root,'binmod.txt')):
    m=l.strip().split(':')
    if len(m)==3 and m[2] in lin: cmds.add(m[1])
open(sys.argv[2],'w').write(''.join(c+'\n' for c in sorted(cmds)))
print(f"packages={len(pk)} linux_x64={len(lin)} commands={len(cmds)}")
