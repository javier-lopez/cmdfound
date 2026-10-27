#!/bin/sh
# Per suite: total compressed bytes of Contents-amd64(+all) and Packages.xz (amd64[+all]), and unique binary package count.
D=http://deb.debian.org/debian/dists; U=http://archive.ubuntu.com/ubuntu/dists; K=http://http.kali.org/kali/dists
row() { # name base suite comps
  n=$1; b=$2; s=$3; shift 3
  rel=$(curl -fsSL "$b/$s/Release" | awk '/^ [0-9a-f]+ +[0-9]+ /{if(!seen[$3]++)print $2, $3}')
  cs=$(echo "$rel" | awk '$2 ~ /^([a-z-]+\/)?Contents-(amd64|all)\.gz$/{t+=$1} END{print t+0}')
  ext=xz; echo "$rel" | grep -q 'binary-amd64/Packages\.xz$' || ext=gz
  ps=$(echo "$rel" | awk -v e=$ext '$2 ~ "^[a-z-]+/binary-(amd64|all)/Packages\\." e "$"{t+=$1} END{print t+0}')
  pk=$(for f in $(echo "$rel" | awk -v e=$ext '$2 ~ "^[a-z-]+/binary-(amd64|all)/Packages\\." e "$"{print $2}'); do curl -fsSL "$b/$s/$f" | (if [ $ext = xz ]; then xz -dc; else zcat; fi) | sed -n 's/^Package: //p'; done | sort -u | wc -l)
  echo "$n $s ($ext)"; 
  echo "$n $s contents_gz=$cs packages_xz=$ps pkgs=$pk"
}
row debian-trixie $D trixie; row debian-trixie $D trixie-updates; row debian-sid $D sid
for p in jammy:22.04 noble:24.04 resolute:26.04 stonking:26.10; do s=${p%%:*}; v=${p#*:}; row ubuntu-$v $U $s; row ubuntu-$v $U $s-updates; done
row kali-rolling $K kali-rolling
