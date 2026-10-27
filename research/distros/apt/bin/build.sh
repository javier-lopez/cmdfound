#!/bin/sh
# Rebuild apt-family command sets from official Contents indexes (no package installs).
# usage: build.sh [name ...]   names: debian-trixie debian-sid ubuntu-22.04 ubuntu-24.04 ubuntu-26.04 ubuntu-26.10 kali-rolling
set -eu
COV=$(cd "$(dirname "$0")/../.." && pwd)
SETS=$COV/sets; MAPS=$COV/apt/maps; mkdir -p "$SETS" "$MAPS"
D=http://deb.debian.org/debian/dists; U=http://archive.ubuntu.com/ubuntu/dists; K=http://http.kali.org/kali/dists

urls() {
  case $1 in
    debian-trixie|debian-sid)
      s=${1#debian-}; suites=$s; [ "$s" = trixie ] && suites="trixie trixie-updates"
      for su in $suites; do for c in main contrib non-free non-free-firmware; do for a in amd64 all; do
        echo "$D/$su/$c/Contents-$a.gz"; done; done; done ;;
    ubuntu-*)
      case $1 in ubuntu-22.04) s=jammy;; ubuntu-24.04) s=noble;; ubuntu-26.04) s=resolute;; ubuntu-26.10) s=stonking;; esac
      echo "$U/$s/Contents-amd64.gz"; echo "$U/$s-updates/Contents-amd64.gz" ;;
    kali-rolling)
      for c in main contrib non-free non-free-firmware; do echo "$K/kali-rolling/$c/Contents-amd64.gz"; done ;;
  esac
}

for n in "$@"; do
  : > "$MAPS/$n.map.tmp"
  for u in $(urls "$n"); do
    curl -fsSL "$u" | zcat | awk '
      { line=$0; loc=$NF; path=substr(line,1,length(line)-length(loc)); sub(/[ \t]+$/,"",path)
        if (path ~ /^(usr\/)?s?bin\/[^\/]+$/) { b=path; sub(/.*\//,"",b); sbin=(path ~ /sbin\//)?1:0
          n=split(loc,p,","); for(i=1;i<=n;i++){q=p[i]; sub(/.*\//,"",q); print b "\t" q "\t" sbin} } }' >> "$MAPS/$n.map.tmp" \
      || echo "WARN $u failed" >&2
  done
  sort -u "$MAPS/$n.map.tmp" > "$MAPS/$n.map"; rm -f "$MAPS/$n.map.tmp"
  cut -f1 "$MAPS/$n.map" | sort -u > "$SETS/$n.txt"
  awk -F'\t' '$3==1{print $1}' "$MAPS/$n.map" | sort -u > "$SETS/$n.sbin.txt"
  echo "$n: $(wc -l < "$SETS/$n.txt") commands, $(wc -l < "$SETS/$n.sbin.txt") sbin, $(cut -f2 "$MAPS/$n.map" | sort -u | wc -l) packages shipping commands"
done
