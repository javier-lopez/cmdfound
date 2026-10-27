# usage: appimageset.py feed.json OUT.txt
# reads https://appimage.github.io/feed.json: app names, lowercased (AM's convention for its launcher names)
import json,sys
it=json.load(open(sys.argv[1]))['items']
n={i['name'].lower() for i in it if i.get('name')}
open(sys.argv[2],'w').write(''.join(x+'\n' for x in sorted(n)))
print(f"items={len(it)} names={len(n)}")
