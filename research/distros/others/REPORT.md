# Distributions outside apt and Alpine (x86_64, fetched 2026-10-26)

Sets rebuilt by `build.sh` (rpmset.py, pacset.py, voidset.py, wolfiset.py).

## What each one is
| Distro | Who / libc / format / release model / image |
|---|---|
| Fedora 44, 43, rawhide | Red Hat sponsored; glibc; RPM/dnf; a release every 6 months, ~13 months of support; rawhide rolls. `fedora:44`, `fedora:rawhide` |
| EPEL 10 on Alma/Rocky 10 | Fedora's add-on repo for RHEL clones; glibc; RPM; follows RHEL majors (~10 years). `almalinux:10`, `rockylinux/rockylinux:10` |
| openSUSE Tumbleweed | SUSE; glibc; RPM/zypper; rolling, gated by openQA. `opensuse/tumbleweed` |
| Arch (core+extra+multilib) | community; glibc; pacman; rolling. `archlinux:latest` |
| Void | community; glibc or musl; xbps; rolling. `ghcr.io/void-linux/void-glibc`, `void-musl` (Docker Hub's are stale) |
| Wolfi | Chainguard; glibc; apk; rolling, containers only (no kernel). `chainguard/wolfi-base` |
| Gentoo | source based; its binhost covers part of the tree; `gentoo/stage3` 403 MB. Not measured |
| Slackware | GPG-signed `.txz` with MANIFEST file lists; ~1,400 packages; no official image. Not measured |

## Command sets
| Set | Index | Compressed | Packages | Commands |
|---|---|---|---|---|
| fedora-44 | releases/44 + updates/44 Everything primary.xml | 22.5 MB | 69,906 | 35,141 |
| fedora-43 | releases/43 + updates/43 | 22.0 MB | 73,188 | 35,223 |
| fedora-rawhide | development/rawhide | 16.2 MB | 67,224 | 34,362 |
| epel-10+alma-10 | EPEL 10 Everything + Alma BaseOS/AppStream/CRB | 59.4 MB | 32,959 | 16,081 |
| opensuse-tumbleweed | tumbleweed/repo/oss | 17.4 MB | 52,984 | 32,181 |
| arch | core/extra/multilib `.files` | 53.0 MB | 15,532 | 22,928 |
| void-glibc | xlocate.git file lists filtered by the repodata | 23 MB git + 2.2 MB | 14,897 | 22,177 |
| wolfi | APKINDEX `cmd:` provides | 11.1 MB | 15,846 | 5,877 |

## As a catalog channel
| Candidate | command->package map | Signing | Image |
|---|---|---|---|
| Fedora | primary.xml lists bin files | RPMs GPG-signed; metadata by metalink hashes over https | `fedora:44` 69 MB |
| EPEL+Alma | same | RPMs signed; Alma signs repomd.xml, EPEL does not | `almalinux:10-minimal` 31 MB |
| Tumbleweed | same | repomd.xml.asc and RPMs signed | `opensuse/tumbleweed` 44 MB |
| Arch | `.files` database | packages signed; `.db`/`.files` unsigned on mirrors | `archlinux:latest` 134 MB |
| Void | none in the repo; xlocate git repo, unsigned, glibc only | packages RSA-signed, key trusted on first use | `void-glibc` 27 MB |
| Wolfi | `cmd:` provides, as Alpine | APKINDEX and packages RSA-signed | `wolfi-base` 8 MB |

Fedora: one release is enough; each release changes 2-2.5% of ~35k names, and
the 858 names only in 43 are retired packages. AUR: not measured; even `-bin`
packages run an unreviewed PKGBUILD and have no signed index or file list.
