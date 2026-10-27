# apt family: command coverage (fetched 2026-10-26, x86_64)

Rebuild: `apt/bin/build.sh <name>` (sets + cmd->pkg maps in `apt/maps/`), `apt/bin/sizes.sh` (index sizes, package counts),
`apt/bin/overlap.py`, `apt/bin/ppa.py`. Sets in `cov/sets/<name>.txt` and `<name>.sbin.txt`.

## 1. Command sets

Index = `Contents-amd64.gz` (Debian: per component, **plus `Contents-all.gz`**, because Debian's amd64 file leaves out
Arch:all packages; Ubuntu: one file per suite, all components, Arch:all included). Ubuntu = release pocket **+ `-updates`**
(Contents is per pocket; `-security` not added, it is published into `-updates` too; `-backports`/`-proposed` excluded).
Debian stable = `trixie` + `trixie-updates` (security.debian.org and backports not added).

| set | suites read | binary pkgs (unique names, Packages) | pkgs shipping a command | commands | of which in sbin |
|---|---|---|---|---|---|
| debian-trixie | trixie, trixie-updates; main contrib non-free non-free-firmware | 69,908 | 14,710 | 47,028 | 4,262 |
| debian-sid | sid; same comps | 77,944 | 16,396 | 52,395 | 4,367 |
| ubuntu-22.04 | jammy, jammy-updates; main restricted universe multiverse | 66,476 (release pocket) | 14,668 | 46,119 | 4,473 |
| ubuntu-24.04 | noble, noble-updates | 72,499 | 15,547 | 50,432 | 4,419 |
| ubuntu-26.04 (newest LTS) | resolute, resolute-updates | 75,317 | 15,736 | 49,890 | 4,359 |
| ubuntu-26.10 (newest, released 2026-10-15) | stonking, stonking-updates | 76,934 | 16,011 | 51,183 | 4,314 |
| kali-rolling | kali-rolling; main contrib non-free non-free-firmware | 72,871 | 15,666 | 47,828 | 4,100 |

URLs: `http://deb.debian.org/debian/dists/{trixie,trixie-updates,sid}/{main,contrib,non-free,non-free-firmware}/Contents-{amd64,all}.gz`;
`http://archive.ubuntu.com/ubuntu/dists/{jammy,noble,resolute,stonking}{,-updates}/Contents-amd64.gz`;
`http://http.kali.org/kali/dists/kali-rolling/{comp}/Contents-amd64.gz` (Kali has no Contents-all; its amd64 file includes Arch:all).
"sbin" names are those found under /sbin or /usr/sbin in any package (a name can also be in bin).

## 2. sid vs Ubuntu

| A | B | A | B | A-B | B-A | A∩B |
|---|---|---|---|---|---|---|
| debian-sid | ubuntu-22.04 | 52,395 | 46,119 | 14,884 | 8,608 | 37,511 |
| debian-sid | ubuntu-24.04 | 52,395 | 50,432 | 9,641 | 7,678 | 42,754 |
| debian-sid | ubuntu-26.04 | 52,395 | 49,890 | 4,570 | 2,065 | 47,825 |
| debian-sid | ubuntu-26.10 | 52,395 | 51,183 | 2,806 | 1,594 | 49,589 |
| debian-trixie | ubuntu-26.04 | 47,028 | 49,890 | 2,788 | 5,650 | 44,240 |
| debian-trixie | debian-sid | 47,028 | 52,395 | 2,116 | 7,483 | 44,912 |

**Ubuntu is not a superset of sid.** sid has 4,570 names 26.04 lacks and 2,806 that 26.10 lacks; the newer the Ubuntu,
the smaller both gaps (Ubuntu is a frozen sid snapshot plus Ubuntu-only packages). sid ∪ 26.04 = 54,460 names.

sid-only vs 26.04 (4,570 names, 1,479 pkgs; 819 are cross-toolchain names). Biggest: openfoam 261, vmtk 184, ceph-test 141,
python3-dials 97, llvm-23 84, megacmd 72. Examples: image2gridmap (mrpt-apps), comskip-gui, llvm-dwarfutil-23 (llvm-23),
reactingParcelFoam (openfoam), asysocks-brute (python3-asysocks), btorsim (btor2tools), uim-wayland, oci-system-serial,
ceph_test_cls_log (ceph-test), kylin-ai-vector-engine, picosvg (python3-picosvg), xrt-replay (libxrt-utils), nvbandwidth,
djbsort-fulltest (djbsort), megacmd's mega-* tools. Kind: packages newer than the 26.04 freeze, newest toolchains.

26.04-only vs sid (2,065 names, 693 pkgs). Biggest: gnu-coreutils 105 (Ubuntu ships rust coreutils as default and GNU's
under gnu-* names), llvm-20 80, llvm-17 79, ubiquity 38, pktools 36, clang-tools-17/20, libemos-bin, unoconv, anc-api-tools,
request-tracker4. Examples: bcbio_fastq_umi_prep.py (bcbio), clang-installapi-20, sortreadtest (sra-toolkit),
select_mountpoint (ubiquity), cargo-1.91 (cargo-1.91), linssid, clang-repl-20, siac (sia), bufr_nt1 (libemos-bin),
ec2-delete-bundle (ec2-ami-tools), jupyter-nbextension (jupyter-notebook), bugpoint-20, rt-munge-attachments-4,
brprintconf_mfc230c (brother-lpr-drivers-extra), jcontrol (julius). Kind: older versioned toolchains kept by Ubuntu,
Ubuntu's own packages (ubiquity, rust-coreutils transition), packages Debian has since removed.
26.10-only vs sid adds run-one, rpi-make-boot-image, raspi-utils-otp, nvidia-imex-ctl, python3-bumble, php8.5 tools.

## 3. One Ubuntu or several

Old release minus (26.04 ∪ 26.10):

| release | names missing from 26.04 and 26.10 | of which version churn (stem still present, e.g. clang-check-14) | cross-toolchain names | rest found in sid | rest found in current-union-bare | rest found nowhere measured (not sid, not union) |
|---|---|---|---|---|---|---|
| 22.04 | 7,761 | 1,817 | 1,588 | 303 | 770 | 5,150 |
| 24.04 | 6,442 | 1,564 | 2,415 | 176 | 596 | 3,307 |

26.04 vs 26.10: 26.04 has 1,056 names 26.10 lacks (427 still in sid); 26.10 has 2,349 that 26.04 lacks.

Why they vanish: whole packages removed from Debian/Ubuntu (22.04 loses 2,222 packages' worth, 24.04 1,594):
ec2-api-tools (332 cmds), cdftools 146, ion 117, tss2 106 (replaced by tpm2-tools), scotch, mrpt-apps, pvm-examples,
ecaccess, sagemath, faust, pki-tools, mono-xsp/mod-mono, slony1-2, libbpf-tools; old LLVM/GCC/gnat versions and
their cross builds; qemu-user-static renamed (qemu-*-static gone from 26.x, still in trixie); python2 (python2,
python2.7, pip2, pycompile from python2-minimal) and youtube-dl exist only in 22.04; neofetch and gopass only up to 24.04;
ec2-describe-instances only up to 24.04. Examples of 22.04-only (not in 26.x nor sid): nauty-checks6, nv-nsight-cu-cli
(nsight-compute), nautilus-filename-repairer, portrelease (portreserve), prelude-lml, octo_world_stats (octopussy),
thawab-server, mueval-core, ec2cpsnap.

Conclusion: **one Ubuntu is enough, and it is the newest LTS (26.04)**, with sid as the second apt set if any. What the
older LTS releases add is mostly dead software (removed upstream, python2, old toolchain versions); 5,150 / 3,307 names
are in no other measured source, but they are the long tail of abandoned packages, and running a 2022 userland to get
them costs a second and third image. 26.10 adds 2,349 names over 26.04 but lives 9 months; sid covers most of that
direction (26.10-only vs sid is just 1,594) and is always current. If the owner wants one apt set only: sid (52,395)
is the largest and the most current; 26.04 is the stable choice. sid ∪ 26.04 = 54,460.

What apt adds over the current channels (`current-union-bare`, 68,276): sid +28,157 (25,928 not sbin-only),
26.04 +26,660, trixie +24,337, Kali +23,993; sid ∪ 26.04 ∪ 26.10 adds +30,028.

## 5. Derivatives

| derivative | own repo read | own pkgs | pkg names not in sid/trixie/24.04/26.04 | commands beyond Debian/Ubuntu |
|---|---|---|---|---|
| Kali | http.kali.org kali-rolling (full archive, Contents) | 72,871 | n/a (full archive) | **1,173** names not in sid/trixie/26.04/26.10 (531 pkgs); 770 also not in current-union-bare |
| MX Linux | mxrepo.com/mx/repo trixie main non-free ahs (has Contents) | 1,427 | 554 | 354 names not in trixie/sid/26.04 (mostly mx-* GUIs/scripts: mx-repo-manager, live-kernel-updater, mx-service-manager) |
| Pop!_OS | apt.pop-os.org/release noble (no Contents) | 897 | 278 | not measured (no file list) |
| Linux Mint | packages.linuxmint.com zena main upstream import backport (no Contents) | 561 | 184 | not measured (no file list) |
| elementary OS | PPAs elementary-os/stable + os-patches, noble (no Contents) | 223 | 146 | not measured (no file list) |

Kali is the only one with weight: john-data 96 (*2john), impacket-scripts 56, spike 29, john 22, nethunter-utils,
dex2jar, metasploit-framework 17, oletools, rizin, poshc2; examples kerberoast, wce, faraday-manage, krbrelayx,
wifipumpkin3, kali-undercover, slim-sensor. Kali has an official image (kalilinux/kali-rolling). Mint, Pop and
elementary add a few hundred desktop/branding packages to Ubuntu; MX adds ~350 scripts. None worth a channel.

## 6. Metadata for an apt catalog channel

- **Contents-<arch>.gz**: honest path->package map, signed through InRelease (Release hashes). Debian needs
  `Contents-all.gz` too (measured: `usr/bin/ack`, `dh`, `yt-dlp` are only in Contents-all).
- **Contents misses names that exist on an installed system**: update-alternatives links and /usr/games.
  In sid's Contents there is no `vi`, `vim` (vim ships vim.basic), `awk`, `nc`, `telnet`, `ftp`, `java`, `javac`, `cc`,
  `c++`, `editor`, `pager`, `rename`, `pinentry`; 26.04's `sudo` (sudo-rs) also comes via alternatives. Debian renames
  matter too: `bat` -> bacula-console-qt (the bat tool ships `batcat`), `fd` -> fdclone (fd-find ships `fdfind`).
- **Ubuntu's command-not-found index** `dists/<suite>/<comp>/cnf/Commands-amd64.xz` (signed via Release, ~350 KB per
  suite for all four components) lists commands per package **including alternatives and /usr/games**
  (vim: editor,ex,vi,view,vim,...; mawk: awk,nawk; netcat-openbsd: nc,netcat; inetutils-telnet: telnet).
  Counts cnf vs Contents: 22.04 47,904 vs 46,119; 24.04 52,659 vs 50,432; 26.04 51,636 vs 49,890; 26.10 52,631 vs 51,183.
  For 26.04: cnf-only = 1,850 (≈1,291 /usr/games names + ≈579 alternatives/other); Contents-only = 104 (names with a
  comma, which cnf cannot express, plus some toolchain names such as ghc-9.10.3). **Debian publishes no cnf index**
  (0 entries in sid's Release); Debian's command-not-found builds its DB from Contents locally.
  Kali/derivatives: no cnf.
- Ambiguity: names shipped by >1 package: sid 727 (11 with >4 pkgs), 26.04 856 (18). A resolver must pick or ask.
- Hashes: 26.10's Release lists **SHA512 only** (no SHA256 section); 26.04 still has SHA256. Kali lists MD5/SHA1/SHA256.

Download sizes per suite (compressed, x86_64; Contents = amd64 [+all for Debian]; Packages = binary-amd64 [+all] .xz, Kali .gz):

| suite | Contents | Packages |
|---|---|---|
| trixie (+ trixie-updates 9 KB) | 52.2 MB | 14.4 MB |
| sid | 58.7 MB | 16.2 MB |
| jammy / jammy-updates | 46.9 MB / **330.1 MB** (every kernel ABI's module paths) | 15.8 / 12.0 MB |
| noble / noble-updates | 51.3 / 82.4 MB | 16.8 / 5.0 MB |
| resolute / resolute-updates | 56.9 / 24.2 MB | 17.9 / 1.6 MB |
| stonking / stonking-updates | 58.8 / 0.1 MB | 12.5 / 0.03 MB |
| kali-rolling | 55.4 MB | 22.1 MB (gz) |
| Ubuntu cnf (all comps, one suite) | ~0.35 MB | - |

The derived command->package map (bin+sbin lines only) is 1.2-1.4 MB raw, **260-360 KB gzip/xz** per distro, i.e.
~1/170 of the Contents download. -updates Contents are not deltas: they grow for the whole life of the release.

## 4. PPAs

- **Reading a PPA without installing**: every PPA is a plain signed apt repo,
  `https://ppa.launchpadcontent.net/<owner>/<ppa>/ubuntu/dists/<series>/{InRelease,main/binary-amd64/Packages.xz}`
  -> package names, versions, .deb URLs, SHA256. **PPAs publish no Contents and no cnf**, so file lists need the .deb
  (`dpkg-deb --fsys-tarfile | tar -t`). Launchpad API (anonymous, JSON):
  `https://api.launchpad.net/devel/~<owner>/+archive/ubuntu/<ppa>?ws.op=getPublishedBinaries&status=Published`
  (binary name/version/series/arch), `<binary_pub>?ws.op=binaryFileUrls&include_meta=true` (url, size, sha1, sha256),
  `<binary_pub>?ws.op=getDownloadCount` (works; e.g. deadsnakes python3.12 = 694). No file-list API.
- **How many PPAs**: Launchpad offers no global count (`searchPPAs` does not exist in the API; the web search does not
  accept an empty filter). Lower bound from https://launchpad.net/ubuntu/+ppas?name_filter=ppa: **7,159** PPAs with
  published packages, **9,839** including empty ones (only those matching "ppa"). True total: not measured.
- **Sample**: 48 PPAs chosen by hand as those most often cited in install instructions/how-tos (no public popularity
  ranking exists); series noble, amd64, all packages except -dbg/-dbgsym, cap 1.5 GB per PPA (3 PPAs hit it: 22 large
  packages skipped). 44 had noble packages (ondrej/nginx, team-xbmc, rmescandon/yq, stebbins/handbrake: none). Total
  downloaded ~8.8 GB, deleted. "New" = not in the ubuntu-24.04 Contents set. Result in `apt/ppa-result.json`.
  - 22 of 44 PPAs add **0** (one, oibaf, had no noble packages) new command names (git-core, neovim, fish, ansible, golang-backports, libreoffice,
    wireshark, inkscape, keepassxc, yt-dlp, flatpak...): they ship newer versions of archive packages.
  - The rest add **680** names in total, almost all version-parallel builds: kisak-mesa 186 (LLVM-21 tools),
    ubuntu-toolchain-r/test 122 (gcc-15/16), ondrej/php 116 (lsphp*, phar*, php5.6-8.x), deadsnakes 96 (python3.7-3.16),
    savoury1/multimedia 95, xtradeb/apps 37 (chromium, avidemux3, czkawka), x2go 6, savoury1/ffmpeg7 6.
  - Single-tool PPAs: apt-fast, mainline (cappelikan), veracrypt (unit193), google-drive-ocamlfuse, grub-customizer,
    hx (helix), fastfetch, papirus-folders, tlpctl.
  - Of the 680: 274 are in neither sid nor 26.04; 211 are in neither sid, 26.04 nor current-union-bare.
- **Trust/signing**: each PPA has its own Launchpad-generated signing key (fingerprint in the API field
  `signing_key_fingerprint`, key on keyserver.ubuntu.com); InRelease is signed by it, Packages hashes chain to the .debs.
  Launchpad builds binaries from the owner's signed source upload, but anyone with an account can own a PPA:
  the signature proves "built by Launchpad for this PPA", not that the owner is trustworthy. Each PPA is a separate
  trust root; there is no review.
- **command->PPA index**: none found. apt-file / command-not-found cover only enabled repos; Launchpad has no file
  search. Building one means downloading every .deb of thousands of PPAs (this 44-PPA sample alone was ~8.8 GB).
  Conclusion: PPAs are not a catalog source for bare names; at most an explicitly named channel per PPA.

## Bottom lines

1. One apt set: **Ubuntu 26.04** (stable, 49,890) or **sid** (52,395, most current); both together 54,460; apt adds
   ~27-30k names over the current channels' union.
2. Older Ubuntus (22.04, 24.04) add 6-8k names, nearly all dead/removed software or old toolchain versions: not worth it.
3. Contents underreports installed names: alternatives (vi, vim, awk, nc, java, telnet, sudo on 26.04) and /usr/games
   are missing. Ubuntu's signed `cnf/Commands-amd64.xz` (~350 KB/suite) fixes both; Debian has no equivalent.
4. Kali adds 1,173 names (pentest tools); Mint/Pop/elementary/MX add a few hundred desktop scripts.
5. PPAs: no Contents, no index, per-PPA trust; 44 popular PPAs add 680 names, mostly parallel versions.
