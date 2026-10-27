# Which distributions get a channel (2026-10-26)

Measure: basenames under /usr/bin, /bin, /usr/sbin, /sbin from each distro's
official file-list index (BRIEF.md), with versioned aliases and cross-toolchain
names filtered out. Comparative, not absolute: not every name is a command a
person types. Baseline: what the current channels reach by bare name, 67,013
(nixpkgs, alpine-3.22, aqua, pkgx, am; conda-forge and binstall answer only
when named). Reports: apt/, others/, baseline/.

## Coverage, adding what adds most each time
| Added | New commands | Total |
|---|---:|---:|
| ubuntu-26.04 | +22,410 | 89,423 |
| fedora-44 | +8,665 | 98,088 |
| opensuse-tumbleweed | +4,923 | 103,011 |
| arch | +2,227 | 105,238 |
| wolfi | +772 | 106,010 |

## Decisions
- apt: one Ubuntu, 26.04 LTS. Sid adds about the same (+23,138 alone, +1,643
  after Ubuntu), but Ubuntu publishes a signed command->package index,
  `cnf/Commands-amd64.xz` (~350 KB), which includes update-alternatives names
  and games; Debian publishes none and needs 52-59 MB of Contents. Older
  Ubuntus add mostly dead software (22.04: +5,300). Kali (+2,077, pentest) is
  a candidate row.
- rpm: Fedora 44 (+8,665), one release. Tumbleweed (+4,923) shares the format.
- apk: Alpine stays (~2,000 of its own even with Ubuntu and Fedora, the
  smallest images); Wolfi (+772) is a row of the same format.
- Arch (+2,227): 53 MB index, unsigned databases on mirrors. Undecided.
- Ruled out: PPAs (48 popular ones add 680 parallel versions; no command index;
  one trust root each), Void (its only command map is an unsigned glibc-only
  git repo), AUR (unreviewed PKGBUILDs, no signed index), Gentoo, Slackware.

## Code
One channel per package format, not per distro. The registry/image code goes to
the api; a distro is a row (image, mirror, release, repos) in its format's
channel, and a channel name is a link to that file, picking its row by name.
