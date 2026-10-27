#!/bin/sh
# Rebuilds cov/sets/{nixpkgs,alpine-3.22,alpine-edge,aqua,pkgx,am,binstall,current-union}.txt
# from the catalogs under ./dl (fetch them with ./fetch.sh). Uses the cmdfound channels'
# own indexers (aqua_indexer.sh, pkgx_indexer.sh, copied verbatim from cmdfound.d).
set -e
B="$(cd "$(dirname "$0")" && pwd)"; S="$B/../sets"; DL="$B/dl"; export LC_ALL=C
mkdir -p "$S"
# nixpkgs: programs.sqlite, same query and filter as cmdfound.d/nix-portable
rel="$(basename "$(cat "$DL/nix/release")")"
tar -xJf "$DL/nix/nixexprs.tar.xz" -C "$DL/nix" "$rel/programs.sqlite"
python3 -I -c 'import sqlite3,sys
for n,p in sqlite3.connect(sys.argv[1]).execute("SELECT name, package FROM Programs WHERE system = ?",("x86_64-linux",)): print(n+"\t"+p)' \
  "$DL/nix/$rel/programs.sqlite" > "$DL/nix/rows"
awk -F'\t' 'NF == 2 && $1 != "." && $1 != ".." && $1 !~ /^nixpkgs\./ && $1 !~ /[^!-~]/ &&
  $1 !~ /[\/:@"$`\\'\'']/ && $2 ~ /^[A-Za-z0-9_+-][A-Za-z0-9._+-]*$/' "$DL/nix/rows" | sort -u > "$DL/nix/programs.tsv"
cut -f1 "$DL/nix/programs.tsv" | sort -u > "$S/nixpkgs.txt"
# alpine: APKINDEX p: cmd:NAME provides, main+community
for v in v3.22 edge; do
  n="alpine-${v#v}"
  for r in main community; do tar -xzOf "$DL/alp/$v-$r.tar.gz" APKINDEX; echo; done |
    awk '/^P:/{np++} /^p:/{n=split(substr($0,3),a," "); for(i=1;i<=n;i++){t=a[i]; sub(/[=<>~].*/,"",t); if(substr(t,1,4)=="cmd:"&&length(t)>4) print substr(t,5)}} END{print np > "/dev/stderr"}' \
    2> "$DL/alp/$n.pkgs" | sort -u > "$S/$n.txt"
done
# aqua: the channel's own indexer over registry.yaml
. "$B/aqua_indexer.sh"; _indexer < "$DL/aqua/registry.yaml" > "$DL/aqua/aqua.tsv"
cut -f1 "$DL/aqua/aqua.tsv" | sort -u > "$S/aqua.txt"
# pkgx: the channel's own indexer over the pantry's package.yml files
rm -rf "$DL/pkgx/p"; mkdir -p "$DL/pkgx/p"; tar -xJf "$DL/pkgx/pantry.tar.xz" -C "$DL/pkgx/p"
. "$B/pkgx_indexer.sh"; find "$DL/pkgx/p/projects" -name package.yml | sort | _indexer > "$DL/pkgx/pkgx.tsv"
awk -F'\t' '$1=="cmd"{print $2}' "$DL/pkgx/pkgx.tsv" | sort -u > "$S/pkgx.txt"
# am: the app names, same awk as cmdfound.d/am
awk '/^◆ [a-z0-9][a-z0-9._+-]* : /{print $2}' "$DL/am/x86_64-apps" | sort -u > "$S/am.txt"
# binstall: crates with a QuickInstall release tag (<crate>-<semver>); reachable only as binstall:CRATE
sed -n 's|.*refs/tags/||p' "$DL/qi/tags.txt" | sed 's/\^{}$//' |
  sed -nE 's/^(.+)-v?[0-9]+\.[0-9]+\.[0-9]+.*$/\1/p' | sort -u > "$S/binstall.txt"
# unions: bare names only (what a bare command resolves through), and with binstall's named-only crates
sort -u "$S/nixpkgs.txt" "$S/alpine-3.22.txt" "$S/aqua.txt" "$S/pkgx.txt" "$S/am.txt" > "$S/current-union-bare.txt"
sort -u "$S/current-union-bare.txt" "$S/alpine-edge.txt" "$S/binstall.txt" > "$S/current-union.txt"
wc -l "$S"/nixpkgs.txt "$S"/alpine-*.txt "$S"/aqua.txt "$S"/pkgx.txt "$S"/am.txt "$S"/binstall.txt "$S"/current-union*.txt | grep -v sbin
