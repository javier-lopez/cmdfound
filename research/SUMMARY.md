# Coverage: which sources get a channel (measured 2026-10-26)

## Measure
A command set is the sorted unique basenames a source installs under
/usr/bin, /bin, /usr/sbin, /sbin, x86_64, read from its official index, never by
installing. `bin/build.sh` rebuilds every set into `sets/` (not committed).

There is no true universe. Here it is the union of 73 measured sets: 184,842
names. The shares move by about one point when sbin-only names (4,797) and
versioned duplicates (gcc-14, python3.12; 14,674) are left out, and the ranking
does not change.

## Coverage, greedy: each row adds what is new after the rows above
| Reach | Adds | Total | Share |
|---|---:|---:|---:|
| nixpkgs, alpine, aqua, pkgx, am (bare names) | | 68,276 | 36.9% |
| + ubuntu 26.04 | +26,660 | 94,936 | 51.4% |
| + fedora 44 | +9,522 | 104,458 | 56.5% |
| + opensuse tumbleweed | +9,056 | 113,514 | 61.4% |
| + epel 10 + alma 10 | +306 | 113,820 | 61.6% |
| + wolfi | +899 | 114,719 | 62.1% |
| + arch | +2,412 | 117,131 | 63.4% |
| + blackarch | +3,832 | 120,963 | 65.4% |
| + ALT Sisyphus | +7,311 | 128,274 | 69.4% |
| + Snap | +6,310 | 134,584 | 72.8% |
| + ROSA 13 | +4,108 | 138,692 | 75.0% |
| + Guix | +3,567 | 142,259 | 77.0% |
| + Homebrew Linux | +3,372 | 145,631 | 78.8% |
| + Julia JLL | +3,207 | 148,838 | 80.5% |
| + PLD Th | +2,778 | 151,616 | 82.0% |
| + everything else measured | | 170,974 | 92.5% |

binstall and conda-forge answer only when named and add nothing to bare names.
github has no catalog. The last ~8% exists only in older releases (Ubuntu
22.04/24.04, Debian sid) or in sources ruled out (Void).

## Channels (rows of a format; cmdfound.d/distro is shared)
| Format | Row | Index | Why this one |
|---|---|---|---|
| apk | alpine 3.22 | APKINDEX `cmd:` provides | smallest images; ~2,000 commands of its own even after Ubuntu and Fedora |
| apk | wolfi | APKINDEX, signed | +899 |
| apt | ubuntu 26.04 | `cnf/Commands-amd64.xz`, ~350 KB, signed | Debian publishes no command index and needs 52-59 MB of Contents; sid adds only +1,643 after Ubuntu |
| rpm | fedora 44 | primary.xml | one release is enough (each changes 2-2.5% of ~35k names) |
| rpm | opensuse tumbleweed | primary.xml, repomd signed | +9,056 |
| rpm | epel 10 + alma 10 | primary.xml | covers Rocky, RHEL, Oracle 10 (27 left) and CentOS Stream 10 (23 left) |
| pacman | arch | `.files` 53 MB; db unsigned on mirrors, packages signed | +2,412 |
| pacman | blackarch | `.files` 8.5 MB, signed | +3,832 pentest tools; replaces Kali, Parrot, BackBox and Exegol |
| aptrpm | alt p11 | pkglists held to the BLAKE2b of the signed release | +7,311 (measured on Sisyphus) |
| rpm | rosa 13 | primary.xml alone lists every bin file (10 MB) | +4,108; covers OpenMandriva |

## Candidates not decided
| Source | Adds | Cost |
|---|---:|---|
| Snap | +6,310 | root and snapd on the host, unless cmdfound unpacks .snap itself |
| Homebrew Linux | +3,372 | `homebrew/brew` image (bottles need /home/linuxbrew); JWS-signed API, 8 MB |
| Julia JLL | +3,207 | new format: resolve JLL deps and LD_LIBRARY_PATH without Julia; 56% is one package (Madagascar) |
| PLD Th | +3,050 (~2,360*) | primary 5 MB, unsigned repomd, DSA rpms; image has poldek only (dnf5 packaged, untested) |
| PyPI via uvx | +2,526 (sample: top 15k) | rootless |
| AOSC | +1,677 (~770*) | apt row with BinContents (656 KB, signed): the cheapest map found; 1.1 GB image |
| Mageia, Flathub, AppImageHub, npm, Chaotic-AUR, openEuler, Terra, oneAPI | under +1,300 each | |

\* From a seeded sample of 30 residual names per source, ±18 points:
distro tooling, version or cross duplicates, alternative names and desktop
apps are taken out.

## Cost per command: `./build.sh ratio`
What each channel costs against the commands only it brings, 2026-10-26.
Unique is greedy among the channels (each after the ones above it); homebrew is
a candidate, measured after all of them, and is about 2,300 once what github,
conda and binstall already reach is taken out. Index MB is what `index bytes`
downloads; image MB the amd64 image compressed, downloaded once, the first time
something of that channel is installed (homebrew's: ubuntu plus ~52 MB of brew).

| channel | index MB | image MB | commands | unique | unique/MB index | unique/MB index+image |
|---|---:|---:|---:|---:|---:|---:|
| am | 1.0 | - | 8,993 | 7,591 | 7,423 | 7,423 |
| homebrew (candidate) | 2.3 | 94 | 22,002 | 3,563 | 1,527 | 37 |
| ubuntu | 20.1 | 42 | 49,890 | 28,242 | 1,402 | 453 |
| nix-portable | 42.6 | - | 54,986 | 54,986 | 1,290 | 1,290 |
| alpine | 2.6 | 4 | 18,196 | 1,997 | 770 | 313 |
| pkgx | 0.5 | - | 4,579 | 329 | 660 | 660 |
| opensuse | 17.4 | 44 | 32,181 | 10,523 | 606 | 172 |
| rosa | 10.0 | 125 | 27,523 | 4,461 | 447 | 33 |
| fedora | 22.5 | 69 | 35,141 | 7,287 | 323 | 79 |
| alt | 37.7 | 46 | 30,963 | 8,679 | 230 | 103 |
| aqua | 3.5 | - | 2,237 | 795 | 227 | 227 |
| blackarch | 17.6 | 150 | 5,490 | 3,703 | 210 | 22 |
| wolfi | 11.3 | 8 | 5,877 | 854 | 76 | 44 |
| arch | 53.0 | 134 | 22,928 | 2,279 | 43 | 12 |
| chaotic-aur | 54.8 | 134 | 3,735 | 779 | 14 | 4 |
| epel | 59.4 | 69 | 16,081 | 222 | 4 | 2 |
ratio 35.16s

## Measured once, not rebuilt by bin/
Each took a run far too long for what it yields. Approximate figures, 2026-10-26:
- Guix: ~33k packages, ~24.5k commands (72% already in nixpkgs), ~3.6k new
  after the rows above. No command index: building one streams every nar,
  about an hour and 20 GB.
- Spack: 1,368 of 9,116 recipes cached (x86_64_v3 only), ~3.7k commands, ~900
  new, mostly HEP/HPC. Read from each tarball's install_manifest.json.

## Findings on current channels
- aqua reads only `github_release` packages, so `http` ones in its registry
  (HashiCorp's boundary, waypoint) are not reached.

Sources ruled out, each with its reason and numbers: `cmdfound.d/discarded/`.
