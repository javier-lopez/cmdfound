#!/bin/sh
# Fetches the catalogs build.sh reads into ./dl (about 50 MB).
set -e
B="$(cd "$(dirname "$0")" && pwd)"; cd "$B"; mkdir -p dl/nix dl/alp dl/aqua dl/pkgx dl/am dl/qi; cd dl
date -u +%FT%TZ > fetched.date
curl -sLI -o /dev/null -w '%{url_effective}\n' https://channels.nixos.org/nixos-unstable > nix/release
curl -sL "$(cat nix/release)/nixexprs.tar.xz" -o nix/nixexprs.tar.xz
for v in v3.22 edge; do for r in main community; do
  curl -sL "https://dl-cdn.alpinelinux.org/alpine/$v/$r/x86_64/APKINDEX.tar.gz" -o "alp/$v-$r.tar.gz"; done; done
curl -sL https://raw.githubusercontent.com/aquaproj/aqua-registry/main/registry.yaml -o aqua/registry.yaml
curl -sL https://dist.pkgx.dev/pantry.tar.xz -o pkgx/pantry.tar.xz
curl -sL https://raw.githubusercontent.com/ivan-hc/AM/main/programs/x86_64-apps -o am/x86_64-apps
git ls-remote --tags https://github.com/cargo-bins/cargo-quickinstall > qi/tags.txt
