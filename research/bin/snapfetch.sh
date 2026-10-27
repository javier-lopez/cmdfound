#!/bin/sh
# usage: snapfetch.sh DIR [strict|classic]
# pages https://api.snapcraft.io/api/v1/snaps/search (amd64, wide scope) into DIR/page-CONFINEMENT-N.json
set -e; D=$1; C=${2:-strict}; mkdir -p "$D"; n=1
while :; do
  curl -sf -H 'X-Ubuntu-Series: 16' -H 'X-Ubuntu-Architecture: amd64' \
    "https://api.snapcraft.io/api/v1/snaps/search?scope=wide&confinement=$C&size=500&page=$n&fields=package_name,apps,confinement,architecture" > "$D/page-$C-$n.json"
  grep -q '"next"' "$D/page-$C-$n.json" || break; n=$((n+1)); sleep 1
done; echo pages=$n
