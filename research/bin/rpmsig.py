# usage: rpmsig.py RPM-URL...
# reads the first 16 KB of each rpm: its signature-header tags (267 DSA, 268 RSA, 1002 PGP, 1005 GPG, 278 OPENPGP)
import sys, struct, urllib.request
for u in sys.argv[1:]:
    b = urllib.request.urlopen(urllib.request.Request(u, headers={'Range': 'bytes=0-16383', 'User-Agent': 'Mozilla/5.0'}), timeout=60).read()
    i = 96; n = struct.unpack('>I', b[i+8:i+12])[0]
    tags = [struct.unpack('>I', b[i+16+16*k:i+20+16*k])[0] for k in range(n)]
    sig = [t for t in tags if t in (267, 268, 1002, 1005, 278)]
    print('signed' if sig else 'UNSIGNED', sig, u.rsplit('/', 1)[-1])
