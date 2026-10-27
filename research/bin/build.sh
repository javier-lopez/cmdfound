#!/bin/sh
# usage: build.sh [ROUND|SOURCE ...]   (no argument: baseline distros pentest candidates missed, then greedy.py)
# reads each source's own index (the URLs below); writes ../sets/NAME.txt (+ .sbin.txt, + maps/NAME.map), downloads to ../dl/
# slow, only when named: pypi, npm, bioconda, ppa; docker also for chimera. guix and spack are not rebuilt (SUMMARY.md)
set -eu
B=$(cd "$(dirname "$0")" && pwd); R=$(dirname "$B"); S=$R/sets; DL=$R/dl; export LC_ALL=C
mkdir -p "$S/maps" "$DL"
py() { f=$1; shift; python3 -I "$B/$f" "$@"; }
mk() { rm -rf "$DL/$1"; mkdir -p "$DL/$1"; }
get() { curl -sfL --retry 5 -A Mozilla/5.0 -o "$1" "$2"; }
#command<TAB>package rows on stdin -> maps/$1.map, a line per command with its packages
tsvmap() { sort -u | awk -F'\t' '{a[$1] = ($1 in a) ? a[$1] "," $2 : $2} END {for (k in a) print k "\t" a[k]}' | sort > "$S/maps/$1.map"; }

round() {
  case $1 in
    baseline)   echo nixpkgs alpine-3.22 alpine-edge aqua pkgx am binstall current-union ;;
    distros)    echo debian-trixie debian-sid ubuntu-22.04 ubuntu-24.04 ubuntu-26.04 ubuntu-26.10 fedora-44 fedora-43 fedora-rawhide \
                     alma-10 epel-10 epel-10+alma-10 opensuse-tumbleweed arch void wolfi ;;
    pentest)    echo kali-rolling blackarch parrot reach ;;
    candidates) echo homebrew-linux snap flathub appimagehub x-cmd mageia-cauldron openeuler-24.03 openmandriva-rolling \
                     rpmfusion-fedora-44 chaotic-aur alt-sisyphus ;;
    missed)     echo rosa-13 pld-th openmamba centos-stream-10 oracle-10 amazon-2023 azure-linux-3 photon-5 terra-44 packman-tw \
                     cuda-rhel10 cuda-opt oneapi oneapi-opt pmc-rhel9 hashicorp-rpm grafana-rpm docker-rpm postmarketos-master \
                     adelie-current deepin-25 openkylin-nile mint-zena kde-neon-user deb-multimedia aosc tinycore-16 pclinuxos \
                     chromebrew julia-jll chimera ;;
    *)          echo "$1" ;;
  esac
}

#the Contents files of an apt suite
aptcontents() {
  D=http://deb.debian.org/debian/dists; U=http://archive.ubuntu.com/ubuntu/dists; K=http://http.kali.org/kali/dists
  case $1 in
    debian-trixie|debian-sid)
      s=${1#debian-}; suites=$s; [ "$s" = trixie ] && suites="trixie trixie-updates"
      for su in $suites; do for c in main contrib non-free non-free-firmware; do for a in amd64 all; do
        echo "$D/$su/$c/Contents-$a.gz"; done; done; done ;;
    ubuntu-*)
      case $1 in ubuntu-22.04) s=jammy;; ubuntu-24.04) s=noble;; ubuntu-26.04) s=resolute;; ubuntu-26.10) s=stonking;; esac
      echo "$U/$s/Contents-amd64.gz $U/$s-updates/Contents-amd64.gz" ;;
    kali-rolling)
      for c in main contrib non-free non-free-firmware; do echo "$K/kali-rolling/$c/Contents-amd64.gz"; done ;;
  esac
}

F=https://dl.fedoraproject.org/pub/fedora/linux; AL=https://repo.almalinux.org/almalinux/10; M=https://geo.mirror.pkgbuild.com
CS=https://mirror.stream.centos.org/10-stream; AZ=https://packages.microsoft.com/azurelinux/3.0/prod
PH=https://packages.broadcom.com/photon/5.0; RO=https://mirror.yandex.ru/rosa/rosa13/repository/x86_64
OPT='^(/opt/.*|/usr/local/cuda[^/]*)/s?bin/(x)?([^/]+)$'

one() {
  case $1 in
    # --- baseline: the channels on master
    nixpkgs) #programs.sqlite, same query and filter as cmdfound.d/nix-portable
      mk nix; rel=$(curl -sLI -o /dev/null -w '%{url_effective}' https://channels.nixos.org/nixos-unstable)
      get "$DL/nix/nixexprs.tar.xz" "$rel/nixexprs.tar.xz"; r=$(basename "$rel")
      tar -xJf "$DL/nix/nixexprs.tar.xz" -C "$DL/nix" "$r/programs.sqlite"
      python3 -I -c 'import sqlite3,sys
for n,p in sqlite3.connect(sys.argv[1]).execute("SELECT name, package FROM Programs WHERE system = ?",("x86_64-linux",)): print(n+"\t"+p)' \
        "$DL/nix/$r/programs.sqlite" |
        awk -F'\t' 'NF == 2 && $1 != "." && $1 != ".." && $1 !~ /^nixpkgs\./ && $1 !~ /[^!-~]/ &&
          $1 !~ /[\/:@"$`\\'\'']/ && $2 ~ /^[A-Za-z0-9_+-][A-Za-z0-9._+-]*$/' | sort -u > "$DL/nix/programs.tsv"
      cut -f1 "$DL/nix/programs.tsv" | sort -u > "$S/nixpkgs.txt"; tsvmap nixpkgs < "$DL/nix/programs.tsv"
      echo "nixpkgs $r: $(wc -l < "$S/nixpkgs.txt") cmds" ;;
    alpine-3.22|alpine-edge)
      v=${1#alpine-}; [ "$v" = edge ] || v=v$v
      py apkset.py "$1" https://dl-cdn.alpinelinux.org/alpine/$v/main/x86_64/APKINDEX.tar.gz https://dl-cdn.alpinelinux.org/alpine/$v/community/x86_64/APKINDEX.tar.gz ;;
    aqua) #the channel's own indexer over registry.yaml
      mk aqua; get "$DL/aqua/registry.yaml" https://raw.githubusercontent.com/aquaproj/aqua-registry/main/registry.yaml
      . "$B/aqua_indexer.sh"; _indexer < "$DL/aqua/registry.yaml" > "$DL/aqua/aqua.tsv"
      cut -f1 "$DL/aqua/aqua.tsv" | sort -u > "$S/aqua.txt"; cut -f1,2 "$DL/aqua/aqua.tsv" | tsvmap aqua
      echo "aqua: $(wc -l < "$S/aqua.txt") cmds" ;;
    pkgx) #the channel's own indexer over the pantry's package.yml files
      mk pkgx; get "$DL/pkgx/pantry.tar.xz" https://dist.pkgx.dev/pantry.tar.xz
      mkdir -p "$DL/pkgx/p"; tar -xJf "$DL/pkgx/pantry.tar.xz" -C "$DL/pkgx/p"
      . "$B/pkgx_indexer.sh"; find "$DL/pkgx/p/projects" -name package.yml | sort | _indexer > "$DL/pkgx/pkgx.tsv"
      awk -F'\t' '$1=="cmd"{print $2}' "$DL/pkgx/pkgx.tsv" | sort -u > "$S/pkgx.txt"
      awk -F'\t' '$1=="cmd"{print $2 "\t" $3}' "$DL/pkgx/pkgx.tsv" | tsvmap pkgx
      echo "pkgx: $(wc -l < "$S/pkgx.txt") cmds" ;;
    am) #the app names, same awk as cmdfound.d/am
      mk am; get "$DL/am/x86_64-apps" https://raw.githubusercontent.com/ivan-hc/AM/main/programs/x86_64-apps
      awk '/^◆ [a-z0-9][a-z0-9._+-]* : /{print $2}' "$DL/am/x86_64-apps" | sort -u > "$S/am.txt"
      echo "am: $(wc -l < "$S/am.txt") apps" ;;
    binstall) #crates with a QuickInstall release tag (<crate>-<semver>); reachable only as binstall:CRATE
      mk qi; git ls-remote --tags https://github.com/cargo-bins/cargo-quickinstall > "$DL/qi/tags.txt"
      sed -n 's|.*refs/tags/||p' "$DL/qi/tags.txt" | sed 's/\^{}$//' |
        sed -nE 's/^(.+)-v?[0-9]+\.[0-9]+\.[0-9]+.*$/\1/p' | sort -u > "$S/binstall.txt"
      echo "binstall: $(wc -l < "$S/binstall.txt") crates" ;;
    current-union) #bare names only (what a bare command resolves through), and with binstall's named-only crates
      sort -u "$S/nixpkgs.txt" "$S/alpine-3.22.txt" "$S/aqua.txt" "$S/pkgx.txt" "$S/am.txt" > "$S/current-union-bare.txt"
      sort -u "$S/current-union-bare.txt" "$S/alpine-edge.txt" "$S/binstall.txt" > "$S/current-union.txt"
      wc -l "$S/current-union-bare.txt" "$S/current-union.txt" ;;

    # --- distros: the rows on feature/distros and their neighbours
    debian-*|ubuntu-2[0-9].[0-9][0-9]|kali-rolling) py contentsset.py "$1" $(aptcontents "$1") ;;
    fedora-44|fedora-43)
      v=${1#fedora-}; py rpmset.py "$1" primary $F/releases/$v/Everything/x86_64/os $F/updates/$v/Everything/x86_64 ;;
    fedora-rawhide) py rpmset.py "$1" primary $F/development/rawhide/Everything/x86_64/os ;;
    alma-10) py rpmset.py "$1" primary $AL/BaseOS/x86_64/os $AL/AppStream/x86_64/os $AL/CRB/x86_64/os ;;
    epel-10) py rpmset.py "$1" primary https://dl.fedoraproject.org/pub/epel/10/Everything/x86_64 ;;
    epel-10+alma-10)
      sort -u "$S/alma-10.txt" "$S/epel-10.txt" > "$S/$1.txt"; sort -u "$S/alma-10.sbin.txt" "$S/epel-10.sbin.txt" > "$S/$1.sbin.txt"
      wc -l < "$S/$1.txt" ;;
    opensuse-tumbleweed) py rpmset.py "$1" primary https://download.opensuse.org/tumbleweed/repo/oss ;;
    arch) py pacset.py "$1" $M/core/os/x86_64/core.files $M/extra/os/x86_64/extra.files $M/multilib/os/x86_64/multilib.files ;;
    void|void-glibc|void-musl) #xlocate's file lists, the packages picked by each repodata
      mk void; V=https://repo-default.voidlinux.org/current
      git clone -q https://repo-default.voidlinux.org/xlocate/xlocate.git "$DL/void/xlocate"
      for r in x86_64 nonfree/x86_64 musl/x86_64-musl musl/nonfree/x86_64-musl; do
        curl -sfL "$V/$r-repodata" | zstd -dc | tar xO index.plist > "$DL/void/$(echo "$r" | tr / _).plist"
      done
      py voidset.py void-glibc "$DL/void/xlocate" "$DL/void/x86_64.plist" "$DL/void/nonfree_x86_64.plist"
      py voidset.py void-musl "$DL/void/xlocate" "$DL/void/musl_x86_64-musl.plist" "$DL/void/musl_nonfree_x86_64-musl.plist" ;;
    wolfi) py apkset.py --newest wolfi https://packages.wolfi.dev/os/x86_64/APKINDEX.tar.gz ;;

    # --- pentest
    blackarch) py pacset.py "$1" https://mirror.math.princeton.edu/pub/blackarch/blackarch/os/x86_64/blackarch.files ;;
    parrot) #Packages for pentest.py: who maintains kali's and parrot's packages
      mk pentest; K=http://http.kali.org/kali/dists/kali-rolling; P=https://deb.parrot.sh/parrot/dists
      for c in main contrib non-free non-free-firmware; do get "$DL/pentest/kali-$c.Packages.gz" "$K/$c/binary-amd64/Packages.gz" || echo "miss kali $c"; done
      for s in echo echo-updates echo-security; do for c in main contrib non-free; do
        get "$DL/pentest/parrot-$s-$c.Packages.gz" "$P/$s/$c/binary-amd64/Packages.gz" || echo "miss parrot $s $c"; done; done ;;
    reach) #what the branch reaches: the baseline's bare names plus its rows
      cat "$S/current-union-bare.txt" "$S/ubuntu-26.04.txt" "$S/fedora-44.txt" "$S/opensuse-tumbleweed.txt" "$S/epel-10+alma-10.txt" \
        "$S/wolfi.txt" "$S/arch.txt" "$S/blackarch.txt" | sort -u > "$S/reach.txt"
      wc -l < "$S/reach.txt" ;;

    # --- candidates
    homebrew-linux)
      mk brew; get "$DL/brew/linux.jws.json" https://formulae.brew.sh/api/internal/formula.x86_64_linux.jws.json
      py brewset.py "$DL/brew/linux.jws.json" "$S/$1.txt" ;;
    snap) mk snap; sh "$B/snapfetch.sh" "$DL/snap" strict; sh "$B/snapfetch.sh" "$DL/snap" classic; py snapset.py "$DL/snap" "$S/snap.txt" ;;
    flathub)
      mk flathub; get "$DL/flathub/appstream.json" https://flathub.org/api/v2/appstream
      py flathubset.py "$DL/flathub/appstream.json" "$S/flathub.txt" "$DL/flathub/rows.json" ;;
    appimagehub) mk appimage; get "$DL/appimage/feed.json" https://appimage.github.io/feed.json; py appimageset.py "$DL/appimage/feed.json" "$S/$1.txt" ;;
    x-cmd)
      mk xcmd; curl -sfL https://raw.githubusercontent.com/x-cmd/pkg/main/dist/v0.1.4.tar.gz | tar xz -C "$DL/xcmd"
      py xcmdset.py "$DL/xcmd/pkg" "$S/x-cmd.txt" ;;
    mageia-cauldron) G=https://mirrors.kernel.org/mageia/distrib/cauldron/x86_64/media
      py rpmset.py "$1" primary $G/core/release $G/nonfree/release $G/tainted/release ;;
    openeuler-24.03) G=https://repo.openeuler.org/openEuler-24.03-LTS-SP2; py rpmset.py "$1" primary $G/everything/x86_64 $G/EPOL/main/x86_64 ;;
    openmandriva-rolling) G=https://abf-downloads.openmandriva.org/rolling/repository/x86_64
      py rpmset.py "$1" primary $G/main/release $G/unsupported/release $G/non-free/release $G/restricted/release ;;
    rpmfusion-fedora-44) G=https://download1.rpmfusion.org
      py rpmset.py "$1" primary $G/free/fedora/releases/44/Everything/x86_64/os $G/free/fedora/updates/44/x86_64 \
        $G/nonfree/fedora/releases/44/Everything/x86_64/os $G/nonfree/fedora/updates/44/x86_64 ;;
    chaotic-aur) py pacset.py "$1" https://builds.garudalinux.org/repos/chaotic-aur/x86_64/chaotic-aur.files ;;
    alt-sisyphus) G=https://ftp.altlinux.org/pub/distributions/ALTLinux/Sisyphus
      py aptrpmset.py "$1" $G/x86_64/base/pkglist.classic.xz $G/noarch/base/pkglist.classic.xz ;;
    alt-p11) G=https://ftp.altlinux.org/pub/distributions/ALTLinux/p11/branch
      py aptrpmset.py "$1" $G/x86_64/base/pkglist.classic.xz $G/noarch/base/pkglist.classic.xz ;;
    ratio) python3 -I "$B/ratio.py" "$S" "$(dirname "$R")/cmdfound.d" ;;
    pypi|pypi-top15000) #~15,000 wheels read by HTTP range
      mk pypi; get "$DL/pypi/top.json" https://hugovk.github.io/top-pypi-packages/top-pypi-packages.min.json
      py pypiset.py "$DL/pypi/top.json" "$S/pypi-top15000.txt" "$DL/pypi/rows.json" ;;
    npm|npm-high-impact) #one registry request per package; a rerun resumes from rows.jsonl
      mkdir -p "$DL/npm"; curl -sfL https://registry.npmjs.org/npm-high-impact/-/npm-high-impact-1.13.0.tgz | tar xz -C "$DL/npm"
      py npmset.py "$DL/npm/package/lib/top.js" "$S/npm-high-impact.txt" "$DL/npm/rows.jsonl" ;;

    # --- missed: the sources the second search found (filelists, as measured)
    rosa-13) py rpmset.py "$1" filelists $RO/main/release/ $RO/contrib/release/ $RO/non-free/release/ ;;
    pld-th) py rpmset.py "$1" filelists https://ftp.pld-linux.org/dists/th/PLD/x86_64/RPMS/ ;;
    openmamba) py rpmset.py "$1" filelists https://cdn.openmamba.org/pub/openmamba/base/RPMS.x86_64/ ;;
    centos-stream-10) py rpmset.py "$1" filelists $CS/BaseOS/x86_64/os/ $CS/AppStream/x86_64/os/ $CS/CRB/x86_64/os/ ;;
    oracle-10) G=https://yum.oracle.com/repo/OracleLinux/OL10
      py rpmset.py "$1" filelists $G/baseos/latest/x86_64/ $G/appstream/x86_64/ $G/codeready/builder/x86_64/ ;;
    amazon-2023) py rpmset.py "$1" filelists https://cdn.amazonlinux.com/al2023/core/guids/762fda855b4bc601a07d99c19a1a9ff82429e78f450f59450cd12522ec5b7ae6/x86_64/ ;;
    azure-linux-3) py rpmset.py "$1" filelists $AZ/base/x86_64/ $AZ/ms-oss/x86_64/ $AZ/extended/x86_64/ $AZ/cloud-native/x86_64/ $AZ/ms-non-oss/x86_64/ ;;
    photon-5) py rpmset.py "$1" filelists $PH/photon_release_5.0_x86_64/ $PH/photon_updates_5.0_x86_64/ $PH/photon_extras_5.0_x86_64/ ;;
    terra-44) py rpmset.py "$1" filelists https://repos.fyralabs.com/terra44/ ;;
    packman-tw) py rpmset.py "$1" filelists https://ftp.gwdg.de/pub/linux/misc/packman/suse/openSUSE_Tumbleweed/ ;;
    cuda-rhel10) py rpmset.py "$1" filelists https://developer.download.nvidia.com/compute/cuda/repos/rhel10/x86_64/ ;;
    oneapi) py rpmset.py "$1" filelists https://yum.repos.intel.com/oneapi/ ;;
    #the vendor trees under /opt and /usr/local/cuda*
    cuda-opt) BINRE=$OPT py rpmset.py "$1" filelists https://developer.download.nvidia.com/compute/cuda/repos/rhel10/x86_64/ ;;
    oneapi-opt) BINRE=$OPT py rpmset.py "$1" filelists https://yum.repos.intel.com/oneapi/ ;;
    pmc-rhel9) py rpmset.py "$1" filelists https://packages.microsoft.com/rhel/9/prod/ ;;
    hashicorp-rpm) py rpmset.py "$1" filelists https://rpm.releases.hashicorp.com/RHEL/9/x86_64/stable/ ;;
    grafana-rpm) py rpmset.py "$1" filelists https://rpm.grafana.com/ ;;
    docker-rpm) py rpmset.py "$1" filelists https://download.docker.com/linux/rhel/10/x86_64/stable/ ;;
    postmarketos-master) py apkset.py "$1" https://mirror.postmarketos.org/postmarketos/master/x86_64/APKINDEX.tar.gz ;;
    adelie-current) G=https://distfiles.adelielinux.org/adelie/current
      py apkset.py "$1" $G/system/x86_64/APKINDEX.tar.gz $G/user/x86_64/APKINDEX.tar.gz ;;
    deepin-25) G=https://community-packages.deepin.com/beige/dists/crimson
      py contentsset.py "$1" $G/main/Contents-amd64.bz2 $G/commercial/Contents-amd64.bz2 $G/community/Contents-amd64.bz2 ;;
    openkylin-nile) py contentsset.py "$1" https://archive.openkylin.top/openkylin/dists/nile/Contents-amd64.gz ;;
    mint-zena) G=http://packages.linuxmint.com/dists/zena
      py contentsset.py "$1" $G/main/Contents-amd64.gz $G/upstream/Contents-amd64.gz $G/import/Contents-amd64.gz $G/backport/Contents-amd64.gz ;;
    kde-neon-user) py contentsset.py "$1" https://archive.neon.kde.org/user/dists/noble/main/Contents-amd64.gz ;;
    deb-multimedia) py contentsset.py "$1" https://www.deb-multimedia.org/dists/unstable/main/Contents-amd64.gz ;;
    aosc) #BinContents lists only executable dirs, and the set takes every basename in it (signed via InRelease)
      mk aosc; get "$DL/aosc/bin" https://repo.aosc.io/debs/dists/stable/main/BinContents-amd64
      awk '{n=$1; sub(/.*\//,"",n); print n}' "$DL/aosc/bin" | sort -u > "$S/aosc.txt"
      awk '{n=$1; sub(/.*\//,"",n); p=$2; gsub(/[a-z0-9-]+\//,"",p); print n "\t" p}' "$DL/aosc/bin" | sort -u -k1,1 > "$S/maps/aosc.map"
      echo "aosc pkgs=$(awk '{print $2}' "$DL/aosc/bin" | tr , '\n' | sort -u | wc -l) cmds=$(wc -l < "$S/aosc.txt")" ;;
    tinycore-16) #provides.db: a NAME.tcz line, then its files
      mk tc; get "$DL/tc/provides.db.gz" http://tinycorelinux.net/16.x/x86_64/tcz/provides.db.gz
      zcat "$DL/tc/provides.db.gz" | grep -E '^/?(usr/)?(local/)?s?bin/[^/]+$' | sed 's|.*/||' | sort -u > "$S/$1.txt"
      zcat "$DL/tc/provides.db.gz" | awk '/\.tcz$/ {p = $0; sub(/\.tcz$/, "", p); next}
        /^\/?(usr\/)?(local\/)?s?bin\/[^\/]+$/ {n = $0; sub(/.*\//, "", n); print n "\t" p}' | tsvmap "$1"
      echo "tinycore-16 tcz=$(zcat "$DL/tc/provides.db.gz" | grep -c '\.tcz$') cmds=$(wc -l < "$S/$1.txt")" ;;
    pclinuxos) #apt-rpm pkglists of each component
      mk pclos; G=https://ftp.belnet.be/mirror/pclinuxonline.com/pclinuxos/apt/pclinuxos/64bit/base
      for c in x86_64 kde6 mate xfce4 trinity kernel; do get "$DL/pclos/pkglist.$c.bz2" "$G/pkglist.$c.bz2"; done
      du -cb "$DL"/pclos/*.bz2 | tail -1; py aptrpmset.py "$1" "$DL"/pclos/*.bz2 ;;
    chromebrew) #manifest/x86_64/*/NAME.filelist, sparse clone
      mk crew; git clone -q --depth 1 --filter=blob:none --sparse https://github.com/chromebrew/chromebrew.git "$DL/crew"
      git -C "$DL/crew" sparse-checkout set manifest/x86_64
      find "$DL/crew/manifest/x86_64" -name '*.filelist' -exec grep -HE '^/usr/local/s?bin/[^/]+$' {} + |
        sed 's|^.*/\([^/]*\)\.filelist:.*/\([^/]*\)$|\2\t\1|' | tsvmap "$1"
      cut -f1 "$S/maps/$1.map" > "$S/$1.txt"; wc -l < "$S/$1.txt" ;;
    julia-jll) #ExecutableProduct(...) names in Yggdrasil's build_tarballs.jl recipes (recipes, not built artifacts)
      mk ygg; git clone -q --depth 1 https://github.com/JuliaPackaging/Yggdrasil.git "$DL/ygg/y"
      find "$DL/ygg/y" -name build_tarballs.jl | while read -r f; do p=$(basename "$(dirname "$f")")
        grep -hoE 'ExecutableProduct\(\s*(\[[^]]*\]|"[^"]+")' "$f" | grep -oE '"[^"]+"' | tr -d '"' | sed 's|.*/||; s/\.exe$//' | sed "s/\$/	${p}_jll/"
      done | tsvmap "$1"
      cut -f1 "$S/maps/$1.map" > "$S/$1.txt"; wc -l < "$S/$1.txt" ;;
    chimera) #cmd: provides of main+user (apk v3 index, signed), read by apk itself in a throwaway container
      mk chimera
      docker run --rm --name cmdfound-chimera -v "$DL/chimera:/out" chimeralinux/chimera sh -c 'apk update >/dev/null 2>&1; apk add chimera-repo-user >/dev/null 2>&1;
        apk update 2>&1 | tail -1; apk query --summarize provides --from repositories "*" > /out/prov.txt'
      grep '^cmd:' "$DL/chimera/prov.txt" | sed 's/^cmd://; s/[=<>~].*//' | sort -u > "$S/chimera.txt"; wc -l < "$S/chimera.txt" ;;
    bioconda) #an estimate, not a set: paths.json of 120 sampled tool packages by HTTP range
      mk bioconda; for s in linux-64 noarch; do get "$DL/bioconda/$s.json.zst" https://conda.anaconda.org/bioconda/$s/repodata.json.zst; done
      py bioconda.py "$DL/bioconda" "$S/reach.txt" 120 ;;

    # --- slow, only when named
    ubuntu-26.04-cnf) #the command-not-found index instead of Contents
      U=http://archive.ubuntu.com/ubuntu/dists
      py cnfset.py "$1" $(for s in resolute resolute-updates; do for c in main restricted universe multiverse; do echo $U/$s/$c/cnf/Commands-amd64.xz; done; done) ;;
    ppa) #48 PPAs often cited in install how-tos, noble amd64, every .deb (~9 GB downloaded); new = not in ubuntu-24.04
      mk ppa; U=http://archive.ubuntu.com/ubuntu/dists
      for s in noble noble-updates; do for c in main restricted universe multiverse; do
        curl -sfL "$U/$s/$c/binary-amd64/Packages.xz" | xz -dc | sed -n 's/^Package: //p'; done; done | sort -u > "$DL/ppa/noble.pkgnames"
      py ppa.py "$S" "$DL/ppa" git-core/ppa deadsnakes/ppa ondrej/php ondrej/nginx ondrej/apache2 graphics-drivers/ppa kisak/kisak-mesa \
        oibaf/graphics-drivers obsproject/obs-studio neovim-ppa/unstable fish-shell/release-4 ansible/ansible longsleep/golang-backports \
        kdenlive/kdenlive-stable inkscape.dev/stable libreoffice/ppa mozillateam/ppa wireshark-dev/stable x2go/stable apt-fast/stable \
        yubico/stable qbittorrent-team/qbittorrent-stable lutris-team/lutris team-xbmc/ppa flatpak/stable cappelikan/ppa linrunner/tlp \
        ubuntu-toolchain-r/test zhangsongcui3371/fastfetch alessandro-strada/ppa maveonair/helix-editor phoerious/keepassxc \
        nextcloud-devs/client openshot.developers/ppa danielrichter2007/grub-customizer rmescandon/yq hluk/copyq unit193/encryption \
        serge-rider/dbeaver-ce pipewire-debian/pipewire-upstream mutlaqja/ppa stebbins/handbrake-releases tomtomtom/yt-dlp \
        savoury1/ffmpeg7 savoury1/multimedia ubuntuhandbook1/apps xtradeb/apps papirus/papirus ;;
    greedy) py greedy.py "$S" ;;
    *) echo "build.sh: unknown round or source: $1" >&2; exit 1 ;;
  esac
}

[ $# -gt 0 ] || set -- baseline distros pentest candidates missed greedy
for a in "$@"; do for n in $(round "$a"); do echo "== $n"; one "$n"; done; done
