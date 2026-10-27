#!/bin/sh
# Rebuilds ../sets for fedora-44/43/rawhide, alma-10, epel-10, opensuse-tumbleweed, arch, void-glibc/musl, wolfi
set -e
H=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$H/dl" "$H/../sets"
F=https://dl.fedoraproject.org/pub/fedora/linux; A=https://repo.almalinux.org/almalinux/10
M=https://geo.mirror.pkgbuild.com; V=https://repo-default.voidlinux.org/current
python3 -I "$H/rpmset.py" fedora-44 primary $F/releases/44/Everything/x86_64/os $F/updates/44/Everything/x86_64
python3 -I "$H/rpmset.py" fedora-43 primary $F/releases/43/Everything/x86_64/os $F/updates/43/Everything/x86_64
python3 -I "$H/rpmset.py" fedora-rawhide primary $F/development/rawhide/Everything/x86_64/os
python3 -I "$H/rpmset.py" alma-10 primary $A/BaseOS/x86_64/os $A/AppStream/x86_64/os $A/CRB/x86_64/os
python3 -I "$H/rpmset.py" epel-10 primary https://dl.fedoraproject.org/pub/epel/10/Everything/x86_64
sort -u "$H/../sets/alma-10.txt" "$H/../sets/epel-10.txt" > "$H/../sets/epel-10+alma-10.txt"
sort -u "$H/../sets/alma-10.sbin.txt" "$H/../sets/epel-10.sbin.txt" > "$H/../sets/epel-10+alma-10.sbin.txt"
python3 -I "$H/rpmset.py" opensuse-tumbleweed primary https://download.opensuse.org/tumbleweed/repo/oss
python3 -I "$H/pacset.py" arch $M/core/os/x86_64/core.files $M/extra/os/x86_64/extra.files $M/multilib/os/x86_64/multilib.files
curl -sfL https://packages.wolfi.dev/os/x86_64/APKINDEX.tar.gz | tar xzO APKINDEX > "$H/dl/wolfi.idx"
python3 -I "$H/wolfiset.py" "$H/dl/wolfi.idx"
git clone -q https://repo-default.voidlinux.org/xlocate/xlocate.git "$H/dl/xlocate"
for r in x86_64 nonfree/x86_64 musl/x86_64-musl musl/nonfree/x86_64-musl; do
  curl -sfL $V/$r-repodata | zstd -dc | tar xO index.plist > "$H/dl/v_$(echo $r | tr / _).plist"
done
python3 -I "$H/voidset.py" void-glibc "$H/dl/xlocate" "$H/dl/v_x86_64.plist" "$H/dl/v_nonfree_x86_64.plist"
python3 -I "$H/voidset.py" void-musl "$H/dl/xlocate" "$H/dl/v_musl_x86_64-musl.plist" "$H/dl/v_musl_nonfree_x86_64-musl.plist"
echo "done; delete $H/dl by hand"
