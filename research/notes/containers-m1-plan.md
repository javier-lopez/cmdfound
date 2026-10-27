# cmdfound containers, milestone 1: `alpine` on `docker` and `udocker`
> **Owner changes, 2026-09-16, which override the text below:**
> - "confined"/"confinado" is shown to users as "dockerized"/"dockerizado".
>   Internal names (`confines=`) stay.
> - When a udocker path is taken because docker is unavailable, one stderr
>   line says `cmdfound: docker is not available, using udocker` (Q6
>   reversed).
> - The question no longer prints `then ~X a run (…)` nor the environment warning.
>   The warning is gone entirely and `environment=` is dropped from the catalog
>   contract; per-run time may still show in `-n`.
> - Ranking inside the dockerized class is the fastest per run (Q4 confirmed).
> - cwd (Q5): the cwd is mounted only when its physical path is under
>   `$HOME` or `/tmp` (their physical targets included); anywhere else it runs in
>   `/` with the cwd not mounted and one stderr line (no refusal). Sockets named
>   by variables are the one mount outside HOME and /tmp.
> - Variables that turn off a tool's verification pass through (owner: "the
>   user's problem"); only location variables are overridden.
> - Docker is a system-level exception: the docker CLI runs with the user's real
>   HOME, `~/.docker/config.json`, logins and credential helpers. What cmdfound
>   keeps for docker still lives in `channels/docker`.
> - udocker uses the user's docker credentials. udocker does not read `~/.docker`,
>   and its keystore format differs (`{url: {"auth": b64}}`, no `auths` level,
>   different Docker Hub key), so the channel generates its keystore inside
>   `channels/udocker` (mode 600) from `config.json` (or `DOCKER_CONFIG`) on each
>   call, translating keys. Entries backed by credential helpers are skipped
>   with a note.
> - User configuration: a channel tool's HOME is the channel and it never reads
>   rc files from the user's HOME; its own variables pass, except location ones
>   (the maxim: `rm -rf channels/<ch>` removes it all) and those that disable
>   verification. Plumbing (curl -q first, wget --no-config, tar/unzip/gzip
>   variables emptied) ignores user rc files. Only network lines of
>   `~/.curlrc`/`~/.wgetrc` are read, exported as standard variables by the core.
> - S6 notes for S8/S9 are in the header of `sh/tools/cmdfound.d/confined-launch`
>   (udocker by-value names, udocker strips whitespace only from `-e NAME=VALUE`,
>   `:` in mounted paths, symlinked HOME with udocker/proot unverified).
Design only. Built against `integrate/channels` (master + race fix + conda-forge),
plus the `collects=yes` / `collect` contract of `ea43c99`, which step S0 brings in.
Owner decisions from the brief and the 2026-09-16 ruling on user configuration are
treated as settled. Where this plan departs from them or from the phase-1 prototype,
it says so and why.

What the user sees the first time, with both runtimes present:

    $ cmdfound figlet hola
    cmdfound: no catalog here has 'figlet'; fetching alpine, am, aqua and pkgx at once
    cmdfound: alpine: 26410 packages, 18196 names
    cmdfound: alpine has 'figlet', confined; reading the native am, aqua and pkgx first
    cmdfound: figlet 2.2.5-r3 -> udocker:alpine/figlet  about 150.9 KB, <1 s  [via alpine]  confined
                first udocker:udocker 1.3.17, 288.3 KB, <1 s, fetched once and kept up to date [verified]
                first setup udocker-englib-1.2.11, 44.0 MB, ~44 s, once [none]
                first image docker.io/library/alpine:3.22, 3.6 MB, ~4 s, once [via udocker]
                total about 48.0 MB, ~49 s
                then ~0.25 s a run (docker:alpine/figlet: ~1.2 s a run)
                confined in Alpine 3.22: it answers about that system, not this one
    cmdfound: proceed? [y/N]

`cmdfound docker:alpine/figlet` pins docker; `cmdfound alpine:figlet` offers both.

---------------------------------------------------------------------------------

## 1. Contract

### 1.1 Kinds and meta keys

`kind=` already exists and defaults to `artifact`. Two values gain meaning; every
other value (`artifact`, the fakes' `confinement`) keeps today's behaviour exactly.

| key | artifact (unchanged) | catalog (new) | runtime (new) |
|---|---|---|---|
| `kind=` | `artifact` | `catalog` | `runtime` |
| `confines=` | `no` / `yes` | `yes` | `yes` |
| `describes=` | `self` | `environment` (alpine) | ignored |
| `environment=` | - | `Alpine 3.22`, the words the warning uses | - |
| `needs=` | programs `index` runs | same | programs the runtime runs (udocker: `python3`) |
| `manager=` | tool kept up to date | - | its own tool (udocker: `udocker:udocker`) |
| `collects=` | `ea43c99` | - | `yes` (both) |
| `aliases=` | unchanged | allowed | allowed |

A catalog is never a path by itself: each hit becomes one path per runtime. A runtime
has no names of its own: it is asked about `<catalog>/<pkg>` only by the resolver, and
about its own tool only when a spec names it.

### 1.2 Verbs by kind

| verb | artifact | catalog | runtime |
|---|---|---|---|
| `meta` | yes | yes | yes |
| `index` | optional | yes | no: exit 1, and `_index_one` never asks |
| `search WORDS` | optional | yes | no |
| `probe NAME [VER]` | yes | yes, plus `image=`, `image_bytes=` | its own tool only, and only when `CMDFOUND_NAMED` is itself; any other bare name exits 1 **without running docker or python** |
| `probe CAT/PKG VER` | - | - | only when `CMDFOUND_IMAGE` is set (the fan-out marker), else exit 1 |
| `locate PKG VER [BIN]` | yes | not asked | its own tool only |
| `recipe PKG VER [BIN]` | - | yes (new) | - |
| `obtain PKG VER [BIN]` | when `requires=` | - | yes, for `CAT/PKG` |
| `collect` | when `collects=yes` | - | yes |
| `size PKG VER` | - | - | new, optional: `bytes=`; exit 1 means "count with du" |

Nothing an artifact channel prints or is asked changes. The two keys the resolver
reads newly from `probe` (`image=`, `image_bytes=`) are only read from catalogs.

### 1.3 Catalog answers, exactly

    probe NAME [VER]
      0  version=2.2.5-r3
         bytes=154521              download size of the package and every dependency the
                                   base image lacks, summed from APKINDEX S:
         estimate=yes              always: apk's own solve inside the image is the truth
         package=figlet            the Alpine package; differs from NAME for cmd: hits
         image=docker.io/library/alpine:3.22@sha256:<hex>   (@digest omitted when never known)
         image_bytes=3642132       compressed layers for this platform; line omitted when unknown
      1  no package gives NAME, or VER is not the version the index has
      2  unreachable=... [needs=index]
      3  candidate=vim  candidate=nvi ...  (NAME is a command of several packages)

    recipe PKG VER [PROGRAM]
      0  image=docker.io/library/alpine:3.22@sha256:<hex>
         install=apk add --no-cache --repositories-file /dev/null -X <mirror>/v3.22/main -X <mirror>/v3.22/community figlet=2.2.5-r3
         bin=figlet                PROGRAM when the index lists cmd:PROGRAM for PKG; else the
                                   only cmd: PKG has; else exit 1
         environment=Alpine 3.22
      1  failed=figlet has no program called X, it has figlet and chkfont; name one with --bin

`install=` is one shell command line, run by `/bin/sh -c` inside the image as root, with
the network and no host mounts. The catalog writes it; every name and version in it has
been checked against `[a-z0-9][a-z0-9._+-]*` / `[0-9A-Za-z._+-]+` first. The version is
pinned: what was shown is what installs, and a mirror that moved on fails as
"alpine's index is older than its mirror; cmdfound --index-update alpine".

### 1.4 Runtime answers, exactly

    probe CAT/PKG VER          env: CMDFOUND_IMAGE=<ref>, CMDFOUND_IMAGE_BYTES=<n or empty>
      0  run_ms=1200                          default cost of one run, until timings exist
         requires=udocker:udocker             udocker only; always said, the core checks tool/
         once=<step>|<label>|<bytes or ->|<badge>   zero or more one-time hops, steps: setup, image
      2  unreachable=<why>                    daemon down, rootless, --ephemeral, tool not had

    probe udocker / locate udocker VER        (udocker only, named)
      probe:  version=1.3.17  bytes=<sdist size>  badge=verified
      locate: url=<PyPI sdist url>  format=tar.gz  bin=maincmd.py  sha256=<PyPI digest>

    obtain CAT/PKG VER [PROGRAM]   env: CMDFOUND_RECIPE=<recipe lines>, CMDFOUND_REQUIRED=<tool> (udocker)
      0  program=<launcher>
         asset=<image id | container id>
         member=<path relative to the channel>      one or more
         timing=<step>:<bytes or ->:<ms>            one per step it took: setup, image, install, run
      1  failed=<why>     2  unreachable=<why>

    collect          env: CMDFOUND_COLLECT=all only for a whole --purge
      0  freed=<bytes>   non-zero: unreachable=<why>
    size CAT/PKG VER
      0  bytes=<n>       1  count it with du

`once=` labels carry no spaces, `|` or `;` (the runtime guarantees it), so the resolver can
keep them inside the path line.

### 1.5 New environment variables

| variable | set by | read by | meaning |
|---|---|---|---|
| `CMDFOUND_RUNTIME` | `_probe_all`, when the spec named a runtime | `_fan_out` | fan out to that runtime only |
| `CMDFOUND_IMAGE`, `CMDFOUND_IMAGE_BYTES` | `_fan_out` | runtime `probe` | the catalog's image; also the fan-out marker |
| `CMDFOUND_RECIPE` | `_obtain_through_tool` | runtime `obtain` | the catalog's `recipe` answer, whole |
| `CMDFOUND_COLLECT=all` | whole `--purge` | `collect` | nothing is named any more |
| `CMDFOUND_EPHEMERAL=1` | main, with `--ephemeral` | docker `probe` | docker answers unreachable |
| `CMDFOUND_ALPINE_MIRROR`, `CMDFOUND_ALPINE_REGISTRY`, `CMDFOUND_UDOCKER_PYPI` | tests | the channel | a directory here instead of the network, as every channel already has |

---------------------------------------------------------------------------------

## 2. Resolver changes, function by function

### 2.1 The path line: 14 fields, a new key

Fields 1–12 keep their names and positions. Two are appended, and `_path_field` learns them:

| # | field | artifact path | catalog x runtime path |
|---|---|---|---|
| 1 | key | see below | see below |
| 2 | channel | channel | the runtime: `udocker` |
| 3 | version | probe | catalog `version=` |
| 4 | bytes | probe | catalog `bytes=` (package closure only) |
| 5 | badge | probe | `via:alpine`, shown `[via alpine]`: apk installs and checks, in the image |
| 6 | confines | meta | `yes` |
| 7 | describes | meta | the **catalog's** meta: `environment` |
| 8 | package | probe / NAME | `alpine/figlet` (catalog `package=`, prefixed) |
| 9 | requires | probe | runtime `requires=` or `-` |
| 10 | estimate | probe | `yes` if the catalog or any hop says so |
| 11 | marginal | as today | `0` when `channels/<rt>/by/alpine/figlet/<ver>` exists; else bytes + once bytes + tool bytes when the tool is missing. Unknown + anything = `-` |
| 12 | ms (µs) | as today | est(install, bytes) + Σ est(step, bytes) over once + est(tool) when missing. Unknown + anything = `-` |
| 13 | once (new) | `-` | once entries joined by `;`, each `step|label|bytes|badge` |
| 14 | run (new, µs) | `0` | mean of the runtime's last ten `run` timings, else `run_ms` × 1000 |

Key = `class`(1) `run`(10 digits µs, `9999999999` unknown) `ms`(14) `hops`(1), hops = tool
missing + number of once entries, capped at 9. Artifact paths have `run` = `0000000000`,
so native and existing confined ordering is byte-for-byte what it is today.

Ranking inside the confined class is **per-run time first**, then one-time time: a
remembered decision runs for ever and its one-time cost is paid once. This is what makes
udocker win by default when both runtimes exist (open question Q4).

### 2.2 `_probe_all`

- Kind is read only from a channel that answered 0 or 3, or that the spec named. Reading
  it from every channel on every resolution would be one more `meta` fork per channel per
  resolution, about 15 s over today's test block.
- Name loop: unchanged for every channel. Runtimes answer `probe <bare name>` with exit 1
  before touching docker or python.
- Spec names a runtime and the package contains `/` (`docker:alpine/figlet`): export
  `CMDFOUND_RUNTIME=docker`, split `alpine` / `figlet`, and probe the catalog alone with
  `CMDFOUND_NAMED=alpine`. `needs=index` sends it through `_first_catalogs` as a missing
  catalog, as today. The catalog is not in `_channels`: `~unreachable docker no catalog called alpine`.
- Spec names a runtime and the package has no `/` (`udocker:udocker`, the tool): probe it
  as an ordinary channel, with no fan-out. `_tool_for`, `_requires_bytes` and
  `_manager_update` reach the tool this way, unchanged.
- Spec names a catalog (`alpine:figlet`): as today; the fan-out in `_probe_emit` does the rest.

### 2.3 `_probe_emit` and the new `_fan_out`

`_probe_emit C out rc pkg`: when rc is 0 and C's kind is `catalog`, it hands over to
`_fan_out C out pkg`, which:

1. lists runtimes: `_channels` with `kind=runtime`, restricted to `CMDFOUND_RUNTIME`
   when set (`CMDFOUND_WITHOUT` already filters `_channels`);
2. for each runtime R whose `needs=` are here (`_needs_here`), runs
   `PATH=<R>/needs:$PATH CMDFOUND_IMAGE=<image> CMDFOUND_IMAGE_BYTES=<image_bytes> R probe C/<package> <version>`;
3. composes R's answer with C's (`version`, `bytes`, `estimate`, `package` from C;
   `requires`, `run_ms`, `once` from R) and writes the line of 2.1;
4. an R that exits 2 prints `~unavailable R <why>`, not `~unreachable`: a runtime that is
   not there hides a way to run the program, not the program;
5. an R whose needs are not here is asked only after every other runtime, and only if none
   gave a path: `_needs_met R` then gets python3 the way `needy` gets its helper
   (resolved, asked about, remembered, linked in `needs/`). In a dry run it is not got:
   `~unavailable udocker python3 is not here, and a dry run does not get it`;
6. returns 2 when at least one line was written. Otherwise it prints
   `~unrunnable C <each runtime: why>` and returns **3**, which callers treat as 1 for
   flow; `_race_catalogs` then says "alpine has 'figlet', and nothing here can run it"
   instead of "has nothing called".

`_probe_emit` for a catalog with rc 3 (ambiguous) prints `~ambiguous alpine vim nvi` and
returns 2, as a confining channel does today.

### 2.4 `_pick`, `_spec_*`, `_canonical`

- `_spec_channel`, `_spec_package`, `_spec_version` and `_canonical` need no change:
  `docker:alpine/figlet@2.2.5-r3` is channel `docker`, package `alpine/figlet`, version
  `2.2.5-r3`; `want` is `figlet`; the cache key is `docker_alpine_figlet`.
- `_pick`: a path whose channel is a runtime contributes `<catalog>:<pkg>` (split at the
  first `/`), deduplicated, so one program is offered once and not once per runtime.

### 2.5 `_resolve`

- `~unavailable` lines become `unavailable=` in the resolution; `~unrunnable` with no path
  at all ends in "alpine has 'figlet', and nothing here can run it: docker: <why>; udocker: <why>", 127.
- The `_tool_for` loop is unchanged. udocker's tool not had puts udocker in
  `CMDFOUND_NO_MANAGER`; its runtime `probe` then exits 2, and the docker path is taken
  with the existing "udocker goes without it; docker:alpine/figlet instead".

### 2.6 `_show_paths` (`-n`) and `_ask`

- Badge of a runtime path: field 5, `via:alpine` shown `[via alpine]`. No `locate` call.
- Per-run time is shown for any path with `run` > 0, with a new `_human_run` (`~0.25 s`).
- `_show_paths`: under the `+ tool` line, one `+ <step> <label>  <bytes>  needed once [<badge>]`
  per once entry of the taken path; `unavailable=` lines listed as `  docker: not available, <why>`;
  the reason says `confinado, el más rápido por corrida` when per-run decided it.
- `_ask`, taken runtime path, in order: the path line; the tool line (now with `[badge]`
  appended at the end, for every channel, so no existing grep breaks); one line per once
  entry; `total` summing path + tool + once bytes and times (unknown + anything = unknown,
  estimate + anything = estimate); `then ~X a run`, plus the other runtime's per-run
  figure when it has a path; and, when describes is `environment`,
  `confined in <environment>: it answers about that system, not this one`, reading
  `environment=` from the catalog's meta. `unavailable=` is not printed here: that
  docker is not usable is not a quicker path someone could not ask.

### 2.7 `_locate`, `_obtain`, `_obtain_through_tool`

- `_locate`: for a runtime path it asks the **catalog** `recipe <pkg> <ver> <want>`, not the
  runtime `locate`. `where` is the recipe; `_ask` finds `bin=` in it as today.
- `_obtain`: a path goes through `_obtain_through_tool` when `requires` is set **or its
  channel is a runtime** (docker has no tool). With `requires` empty, no tool is placed
  and `CMDFOUND_REQUIRED` is not set.
- `_obtain_through_tool`: runs the channel with `PATH=<ch>/needs:$PATH` and
  `CMDFOUND_RECIPE="${where}"`; writes the path's badge into the inventory (`via alpine`);
  and, when the answer has `timing=` lines, records each (`_timing_add ch step bytes ms`,
  step `[a-z]+` only) **instead of** the whole-call `install` line. A channel without
  `timing=` lines is recorded exactly as today.

`timing=` evaluated: adopted. A pull is not an install (docker's store and udocker's
extraction work at different speeds per byte), engines are a 44 MB download that happens
once, and a run is a fixed cost with no bytes; averaging them into one `install` speed is
what made git's question say ~4 min for 25 s. `image=` / `image_bytes=` evaluated:
adopted, but split. The catalog knows its image and what it weighs (2.1, 3.1). Only the
runtime knows whether it lacks it, so the runtime turns the pair into a generic `once=`
entry, which also carries udocker's engines. One mechanism covers both hops.

### 2.8 Estimates: fixed cost plus cost per byte (core-wide)

`_est_us bytes ch step` from the last ten samples of that step in that channel:
- two or more with numeric bytes whose largest is at least twice the smallest:
  least-squares `ms = a + b·bytes`; negative `b` gives `b=0, a=mean`; negative `a` gives
  `a=0, b=Σms/Σbytes`;
- otherwise, samples with bytes: today's speed model (`a=0`);
- samples without bytes only, or no bytes asked about: mean ms (today);
- nothing recorded: 1 MiB/s, `a=0` (today).
`_speed` stays for the speed branch. The one test that seeds a single `install` sample
(`hop3`) ranks exactly as before.

### 2.9 `--list`, `--purge`, `collect`, `--index-update`, `--ephemeral`

- `_list`: runtime placements are `udocker:alpine/figlet@2.2.5-r3  8.9 MB  confined`; for a
  `collects=yes` channel the size is `size` when it exits 0, else du over members as today.
- `_purge SPEC`: when SPEC's channel is a catalog (`alpine:figlet`), it matches
  `by/alpine/figlet/*` in every runtime channel. `figlet` and `docker:alpine/figlet` already
  match through the existing `lpkg##*/` rule. `collect` runs through `ea43c99` for every
  touched channel with `collects=yes`.
- `_purge ""`: after the confirmation and **before** `rm -rf home`, every channel directory
  whose channel says `collects=yes` is asked `collect` with `CMDFOUND_COLLECT=all`.
  That is the only way docker's labelled images of this home are swept by a whole purge.
- `_index_one`: a runtime returns 2 before `_needs_met`, so `--index-update` never gets
  python3 for udocker. `_manager_update` for `udocker:udocker` works unchanged.
- `--ephemeral` exports `CMDFOUND_EPHEMERAL=1`. docker's probe answers
  `unreachable=--ephemeral does not use docker: its images would outlive the throwaway root`.

---------------------------------------------------------------------------------

## 3. The three channels

### 3.1 `alpine` (catalog)

- meta: `kind=catalog confines=yes describes=environment environment=Alpine 3.22`.
- index: `<mirror>/v3.22/{main,community}/<arch>/APKINDEX.tar.gz`, mirror defaulting to
  `https://dl-cdn.alpinelinux.org/alpine`, arch from `uname -m` (x86_64, aarch64, armv7,
  x86, ppc64le, s390x, riscv64). Kept in `index/alpine.tsv` as `pkg name ver S I repo desc`,
  `cmd command name`, `prov token name` (so:, pc:, cmd:) and `dep name token`. Fewer than
  100 packages keeps the old index, as aqua and conda-forge do. Answers `packages=` `names=` `bytes=`.
- probe: `cmd` lookup, else package name. Closure over `D:` through `prov`, first provider,
  minus the base set, summing `S:`. Base set = closure of the minirootfs roots declared in
  the channel (`alpine-baselayout alpine-keys apk-tools busybox busybox-binsh
  ca-certificates-bundle libc-utils ssl_client`); always `estimate=yes`. The builder
  checks the figure once against `apk add --simulate` in the real image and records it in
  the commit message.
- image: token from `auth.docker.io`, then `HEAD /v2/library/alpine/manifests/3.22`
  (free) → `docker-content-digest`, cached 24 h in `cache/image.digest`, asked again under
  `CMDFOUND_REFRESH`. The manifest (index, then this platform's manifest: counts as one
  Docker Hub pull) is read only for a digest not in `cache/manifests/<digest>.<arch>`, and
  `image_bytes` = Σ `layers[].size`. With the registry out of reach, the cached digest is
  used; with none, `image=` has no digest and `image_bytes` is omitted. Probe never fails
  over the registry: the catalog is local.
- search: `alpine:<pkg>\t<cmds>\t<desc>`, matched on name, commands and description.
- APKINDEX's RSA signature is not checked here: apk inside the image checks it before
  installing, and what this index decides is only what to ask apk for.

### 3.2 `docker` (runtime)

Layout: `channels/docker/{run/ by/ members/ images/<cat>/<pkg>/<ver> pulled/<hex> cache/ tmp/ lib/ timings inventory}`.
Docker is the system-level exception (§5): every docker CLI call runs with the user's real
HOME and environment. What cmdfound keeps for the channel is all in the layout above,
and `rm -rf channels/docker` removes it; images and what the CLI writes in `~/.docker` are
docker's.

- probe CAT/PKG: exits 1 without `CMDFOUND_IMAGE`; 2 under `CMDFOUND_EPHEMERAL`; 2 when
  no `docker` is on PATH. `docker info --format '{{json .SecurityOptions}}'` failing gives
  2 with docker's own first line ("permission denied while trying to connect…: this user
  cannot reach the daemon, and cmdfound does not use sudo"). `name=rootless` gives 2
  "docker is rootless: files the program writes in your home would not be yours". An
  endpoint that is not a unix socket or loopback tcp gives 2 "the daemon at <host> does
  not see this machine's files" (R8). Otherwise `run_ms=1200`; and when
  `docker image inspect --format '{{.Id}}' <image@digest>` fails,
  `once=image|<ref>|<CMDFOUND_IMAGE_BYTES or ->|via docker`.
- obtain CAT/PKG VER PROGRAM, all as root inside, nothing of the host mounted:
  1. a record `images/<cat>/<pkg>/<ver>` whose image still exists: skip to 5;
  2. image missing: `docker pull <repo>@sha256:<hex>`, by digest so no tag of the user's
     moves; `pulled/<hex>` written only when it was absent before; `timing=image:<bytes>:<ms>`;
  3. `docker create --name cmdfound-build-<pid> --label io.cmdfound.home=<home> --network=host
     <network variables, §5> --entrypoint /bin/sh <image> -c "<install>"`, `docker cp` of the CA
     file when there is one (§5), `docker start -a`, then
     `docker commit --change 'LABEL io.cmdfound.home="<home>"' ...catalog/package/version... <ctr> cmdfound/<cat>:<pkg>-<ver>`
     (characters outside `[A-Za-z0-9_.-]` in the tag become `_`; the labels carry the exact
     values), then `docker rm <ctr>`; `timing=install:<pkg bytes>:<ms>`. Record: `<id>\t<image ref>`.
     A home containing `"`, `$`, a backquote, a backslash or a newline is refused, as conda-forge refuses them;
  4. on any failure: remove the build container, and the committed image if there is one: `failed=`;
  5. copy `confined-launch` into `lib/`, write `run/<cat>/<pkg>/<ver>/<program>` (§4);
  6. run the launcher with `/bin/sh -c 'command -v <program>'` as the program: a failure
     is `failed=<pkg> installed no program called <program>`; its duration is
     `timing=run:-:<ms>`;
  7. `program=`, `asset=<id>`, `member=run/<cat>/<pkg>/<ver>`, `member=images/<cat>/<pkg>/<ver>`.
- collect: labelled = `docker image ls -a -q --no-trunc --filter label=io.cmdfound.home=<home>`;
  named = the ids in `images/**` (none under `COLLECT=all`). For each labelled id that is
  not named: unique size = `.Size` minus its base's `.Size`, then `docker rmi <id>` (never
  `-f`). Then each `pulled/<hex>` that no remaining record names: `docker rmi <ref>`,
  without `-f`, so docker itself refuses a base something still uses; the record goes
  only when the rmi worked. Exited `cmdfound-build-*` containers labelled with this home
  are removed. Answers `freed=`. Never run automatically: only from a purge.
- size: `bytes=` the same unique size.

### 3.3 `udocker` (runtime, with its tool)

Layout: `channels/udocker/{tool/<ver>/udocker-<ver>/udocker/maincmd.py tool/current ud/ home/ tmp/ xdg/ needs/ run/ by/ members/ containers/<cat>/<pkg>/<ver> pulled/ cache/ lib/ timings inventory}`.
`ud/` is `UDOCKER_DIR`: engines in `ud/bin` and `ud/lib`, then `repos/`, `layers/` and `containers/`.

- meta: `kind=runtime confines=yes collects=yes needs=python3 manager=udocker:udocker`.
- The tool is the **PyPI sdist**, not the wheel (Q2): `udocker-1.3.17.tar.gz`, sha256
  `f7f4d0cb…9f2f59` from `https://pypi.org/pypi/udocker/json` (cached 24 h), 295 KB. It
  holds `udocker/maincmd.py` with mode 775, so `_place_tool` needs nothing new
  (`format=tar.gz`, `bin=maincmd.py`, found by `_find_program`). The wheel (verified,
  same digest source) has `maincmd.py` at 664 and needs `unzip`, which the core would
  then have to require or replace.
- Every udocker invocation: `PATH=<ch>/needs:$PATH python3 -E -s "$(readlink <ch>/tool/current)" [--allow-root when id -u is 0] <command>`,
  by its real path: `maincmd.py` finds its package from `argv[0]`, which a link breaks.
  Environment as in §5.
- Engines: a `once` hop, not part of the tool. `probe CAT/PKG` compares `ud/lib/VERSION`
  with the `tarball_release:` of `udocker version` (cached per tool version; before the
  tool is here, the channel's constant `1.2.11` and its URL), weighs the first URL with a
  HEAD (cached per release), and says `once=setup|udocker-englib-<rel>|<bytes>|none`.
  Nobody publishes a sum for it (owner: badge none).
- probe CAT/PKG: exit 1 without `CMDFOUND_IMAGE`; 2 when listed in `CMDFOUND_NO_MANAGER`;
  `requires=udocker:udocker`, `run_ms=250`, the setup hop when due, and
  `once=image|<ref>|<bytes>|via udocker` when `ud/repos` has no such image. The
  presence check reads `ud/repos` directly, so probe costs no python start.
- obtain:
  1. setup when due: `udocker install`, with the user's `UDOCKER_TARBALL` if set (§5), so udocker
     downloads its engines itself; `timing=setup:<bytes>:<ms>`;
  2. image missing: `udocker pull <repo>@sha256:<hex>`; `pulled/<ref>`; `timing=image:…`;
  3. `udocker create <ref>` (prints the id), `udocker setup --execmode=P1 <id>`, then
     the CA file copied into `ud/containers/<id>/ROOT` when there is one (§5), then
     `udocker run --nobanner --user=root <network variables, §5> <id> /bin/sh -c "<install>"`,
     with no `-v` and no `--hostenv`; `chmod -R u+w ud/containers/<id>` so that `rm -rf` works
     on what apk left read-only; `timing=install:…`. Record `containers/<cat>/<pkg>/<ver>` = `<id>\t<ref>`;
  4. failure: `rm -rf ud/containers/<id>` after the chmod: `failed=`;
  5–6 as docker (lib copy, launcher, `command -v` check, `timing=run`);
  7. `member=run/…`, `member=containers/<cat>/<pkg>/<ver>`, `member=ud/containers/<id>`.
     One container per placement: purge's rm takes it, du counts it.
- collect: each `pulled/<ref>` that no remaining `containers/**` record names:
  `udocker rmi <ref>`, with freed = du of `ud/layers` before and after. Under
  `COLLECT=all`: `chmod -R u+w ud`, so the rm that follows works.
- size: exit 1 (du is right: everything is in the channel).

---------------------------------------------------------------------------------

## 4. The launcher

Written by the runtime at obtain into `run/<cat>/<pkg>/<ver>/<program>`. It sources
`<ch>/lib/confined-launch`: one shared file in the repository,
`sh/tools/cmdfound.d/confined-launch`, mode 644 (not a channel), copied into the
channel at every obtain. The channel finds it next to its own **real** path, since the
tests reach channels through links. `rm -rf channels/<rt>` removes the copy; an obtain
after a cmdfound update refreshes it.

### 4.1 Shared rules (`confined-launch`)

**Mounts**, each bound at its own path, read-write:
- `$HOME`: when set, absolute, a directory, and not `/`;
- cwd (`pwd`) when it is not under an already-mounted directory. A cwd that is `/`, or an
  ancestor of or equal to `/bin /dev /etc /lib /lib64 /proc /run /sbin /sys /usr /var /var/lib`,
  or under `/dev /proc /sys`, is not mounted: workdir `/`, and one stderr line saying so
  (Q5). Anything else (`/tmp/x`, `/etc/nginx`, `/srv/site`) is mounted;
- `$SSH_AUTH_SOCK`, when it is a socket not under a mounted directory.

**Workdir**: cwd when it is mounted or under a mount, else `/`.

**Environment** passed to the program. Every variable, except:
1. always dropped, as host layout that breaks a musl userland whatever its value: `PATH`,
   `LD_*`, `SHELL`, `PWD`, `OLDPWD`, `SHLVL`, `_`, `HOSTNAME`, `MAIL`, `TERMINFO`,
   `TERMINFO_DIRS`, `MANPATH`, `INFOPATH`, `XDG_DATA_DIRS`, `XDG_CONFIG_DIRS`,
   `XDG_RUNTIME_DIR`, `PKG_CONFIG_PATH`, `LIBRARY_PATH`, `CPATH`, `C_INCLUDE_PATH`,
   `CPLUS_INCLUDE_PATH`, `LOCPATH`, `GCONV_PATH`, `NLSPATH`, `PYTHONPATH`, `PYTHONHOME`,
   `PYTHONUSERBASE`, `VIRTUAL_ENV`, `CONDA_*`, `MAMBA_*`, `PERL5LIB`, `PERLLIB`,
   `PERL_LOCAL_LIB_ROOT`, `RUBYLIB`, `RUBYOPT`, `GEM_HOME`, `GEM_PATH`, `NODE_PATH`,
   `LUA_PATH`, `LUA_CPATH`, `CLASSPATH`, `JAVA_HOME`, `GOROOT`, `GIO_MODULE_DIR`,
   `GTK_PATH`, `QT_PLUGIN_PATH`, `SSL_CERT_FILE`, `SSL_CERT_DIR`, `CURL_CA_BUNDLE`,
   `REQUESTS_CA_BUNDLE`, `NODE_EXTRA_CA_CERTS` (host CA paths, which the container has
   its own of);
2. path rule: a value that is an absolute path, or a `:` list of absolute paths, passes
   only when every element is under a mount or is the mounted socket (`GNUPGHOME=~/.gnupg`
   passes, `EDITOR=/usr/bin/vim` does not, `EDITOR=vim` does);
3. names not matching `[A-Za-z_][A-Za-z0-9_]*` are skipped (read as `env | awk`, as conda-forge does).

A kept variable is passed **by name** (`-e NAME`), so no value, a token included, is ever
on an argv. The one exception is a variable the launcher changed for the runtime process
itself. That never happens for docker. For udocker it is `HOME`, `XDG_CONFIG_HOME` and
`CURL_HOME` (§5), each passed by value as the user had it (`-e HOME=/home/m`), or dropped
when the user had it unset.

**User**: uid, gid and every supplementary gid of the caller; names resolve through the
host's passwd and group.

### 4.2 docker

    exec docker run --rm -i [-t] --init --log-driver=none --network=host --pull=never \
        -u <uid>:<gid> [--group-add <gid>]... \
        -v /etc/passwd:/etc/passwd:ro -v /etc/group:/etc/group:ro \
        -v <mount>:<mount>... -w <workdir> \
        -e HOME=<user's HOME> -e NAME... \
        <image id> <program> "$@"

- `-t` only when stdin, stdout **and** stderr are terminals: a tty has one output stream,
  so `2>err` with a terminal stdout would otherwise lose stderr into stdout.
- `exec`: docker's status is the program's; `--init` (tini) plus the CLI's signal proxy
  turn Ctrl-C into 130 and TERM into 143 (measured in phase 1).
- The docker CLI runs with the user's own HOME and environment (§5), so its logins,
  contexts and `detachKeys` are the user's, as in the user's own `docker run`.
- Status 125 with the image id gone (`docker image inspect` fails): print
  `cmdfound: the docker image for <program> is gone; cmdfound --latest <spec> makes it again`
  and exit 127.

### 4.3 udocker

    PATH=<ch>/needs:$PATH HOME=<ch>/home XDG_CONFIG_HOME=<ch>/home/.config \
    UDOCKER_DIR=<ch>/ud UDOCKER_KEYSTORE=<ch>/ud/keystore XDG_RUNTIME_DIR=<ch>/xdg \
    UDOCKER_TMP=<ch>/tmp UDOCKER_TARBALL= [unset CURL_HOME, UDOCKER_BIN/LIB/DOC/REPOS/LAYERS/CONTAINERS] \
      python3 -E -s <real path of tool/current> [--allow-root] --quiet run --nobanner \
        --hostauth --user=<uid> \
        -v <mount>... -w <workdir> \
        -e HOME=<user's HOME> -e NAME... \
        <container id> <program> "$@"

- Not `exec`: `trap 'interrupted=1' INT`, run in the foreground, then exit 130 when
  interrupted, else udocker's status. udocker ends a Ctrl-C with 1, which is also a program
  failing. Foreground is required: a background job of a non-interactive shell ignores
  SIGINT, and so would the program.
- No `-t` and no pty: proot passes the three descriptors through, so terminals stay
  terminals and redirections stay apart.
- `--quiet`: only udocker's errors reach stderr, and the rest of stderr is the program's.
- The user's `UDOCKER_*` variables other than those listed pass (§5). `UDOCKER_TARBALL` is
  emptied here: udocker installs its engines before **any** command when they look
  missing, and that would be 44 MB fetched with no question.

### 4.4 Divergences from `proto/confined-run`, and why

| prototype | here | why |
|---|---|---|
| HOME = a channel directory mounted over `$HOME` | the real HOME at its path | owner: HOME and environment as native |
| env allowlist of 8 names | denylist + path rule, by name | owner: the whole environment except host paths |
| `-t` when stdin and stdout are terminals | stdin, stdout and stderr | keeps stderr apart under `2>file` |
| bridge network | `--network=host` | localhost reachable as natively and as under udocker (Q3) |
| image by tag | by id, `--pull=never` | tags are shared between homes on one daemon (R6) |
| primary gid only | `--group-add` each supplementary gid | group-readable files in HOME stay readable |
| cwd always mounted | not when it would hide the container's system | `cd /usr && cmdfound …` must not mount the host's /usr |
| `python3 udocker` | `python3 -E -s <real path>`, HOME in the channel, `--quiet`, `--allow-root` for uid 0 | owner ruling; udocker refuses root otherwise |
| `--user=<name>` | `--user=<uid>` | the same entry, without a name lookup that can differ |
| no socket handling | `SSH_AUTH_SOCK` bound | owner: sockets mounted |
| docker 125 passed through | a gone image becomes 127 with the way out | a remembered decision must not fail forever in silence |

---------------------------------------------------------------------------------

## 5. User configuration (owner rulings of 2026-09-16)

| who | runs with | the user's variables | why |
|---|---|---|---|
| plumbing: curl, wget, tar, gzip | `curl -q` first, `wget --no-config`, `TAR_OPTIONS= GZIP=` for the call | `http(s)_proxy`, `no_proxy`, `SSL_CERT_FILE`, `CURL_CA_BUNDLE` kept | ruling 1; `TAR_OPTIONS=--verbose` would put names into `tar -xzOf APKINDEX` output |
| docker CLI (probe, obtain, collect, size, launcher) | **the user's real HOME and environment**: `~/.docker/config.json`, logins, credential helpers, contexts, cli-plugins, and `DOCKER_HOST`/`DOCKER_CONTEXT`/`DOCKER_CONFIG` as the user has them | all | owner: docker is system-level, and the only exception to "everything in CMDFOUND_HOME", together with its images and what the CLI writes under `~/.docker`. Every call whose output is parsed passes `--format` (`info`, `image inspect`, `image ls -q`) or prints an id only (`commit`, `create`), so `imagesFormat`/`psFormat` in the user's config cannot reach a parser. Labels, the explicit `--purge` sweep and never sudo stay |
| python3 (udocker's interpreter) | `-E -s`, `HOME` in the channel | `PYTHON*` ignored | ruling 3a: `PYTHONPATH`, `PYTHONHOME`, `PYTHONUSERBASE` and `PYTHONPYCACHEPREFIX` read or place code outside the channel, and `PYTHONSAFEPATH` breaks udocker's import |
| udocker | `HOME`, `XDG_CONFIG_HOME` in the channel; `CURL_HOME` unset; `UDOCKER_DIR`, `UDOCKER_KEYSTORE`, `XDG_RUNTIME_DIR`, `UDOCKER_TMP` set; `UDOCKER_BIN/LIB/DOC/REPOS/LAYERS/CONTAINERS` unset | the other `UDOCKER_*` pass: `LOGLEVEL`, `REGISTRY`, `INDEX`, `USE_CURL_EXECUTABLE`, `USE_PROOT_EXECUTABLE`, `DEFAULT_EXECUTION_MODE`; `TARBALL` only during setup | ruling 3a for the ones that place state; 3b for `TARBALL` (no download without the question) |
| apk (inside the image) | the image's `/root`, no host mounts | the network variables, below | ruling 2 holds by construction |
| the program | the real HOME and environment, §4.1 | all but host paths | ruling 4 |

**Network variables, one set for every installer.** `http_proxy https_proxy no_proxy
all_proxy` and their upper-case forms, `SSL_CERT_FILE` and `CURL_CA_BUNDLE`, as the resolver's
environment has them. udocker's process keeps them, since only the variables listed above
are changed, and its curl or pycurl honours them. A build (docker `create`, udocker `run
--user=root`) gets the proxy variables by name (`-e NAME`). A CA file (`SSL_CERT_FILE`, else
`CURL_CA_BUNDLE`) is **copied** into the build container at `/etc/cmdfound/ca.pem`, not
mounted: builds mount nothing. `SSL_CERT_FILE` then points at the copy for apk's OpenSSL,
and the install command removes it before the commit. Both runtimes do this in one
function, `_build_network`, in `confined-launch`. If the pending owner question adds
"read only the network lines of `~/.curlrc` and `~/.wgetrc`", the core exports those
variables before it calls any channel, and nothing downstream changes.

What udocker reads from HOME, checked in the 1.3.17 source: `~/.udocker/udocker.conf`
(`Config.homedir` is `expanduser("~")`), its default topdir and keystore there, and,
when pycurl is missing, `curl` run with `-q` not first (`utils/curl.py`), which reads
`~/.curlrc` or `$XDG_CONFIG_HOME/curlrc`. `/etc/udocker.conf` is still read; it is the
machine's, not the user's.

**Consequence, stated for the owner: udocker's pulls are anonymous.** Docker keeps the
user's logins through the exception above. udocker cannot: logins made with `udocker login`
live in its keystore, which is one of the three variables the channel must keep inside
`channels/udocker`, and nothing may appear in `~/.udocker`. So udocker pulls from Docker
Hub anonymously: 100 an hour for this IP, shared. The catalog's HEAD for the digest is
anonymous too, and free.

Recommendation: accept it for milestone 1, and make it discoverable.
- Milestone 1 pulls one base image per catalog release, once, so the limit is rarely what stops it.
- When a udocker pull fails with 429/`toomanyrequests`, `failed=` says so and names the way
  out that exists: `docker:<spec>`, when docker is available and logged in.
- A login for udocker (a keystore inside the channel, filled by a cmdfound verb) waits until a catalog needs a private registry.

---------------------------------------------------------------------------------

## 6. Build order

Every step is one commit, passes `cd sh/tests && sh tools.sh cmdfound`, and reports that
block's wall-clock time before and after, plus the new tests alone (CLAUDE.md). The
figures below are estimates. The block is about 40–55 s today and noisy (ea43c99: 43.5/39.1 s).

| step | what | files | tests and fakes | cost est. | after |
|---|---|---|---|---|---|
| **S0** | `collects=yes` / `collect` (cherry-pick `ea43c99`) | `cmdfound` `_purge`; `tests/cmdfound.d/collector`; tools.db | as in ea43c99 | +0.7–2.4 s (measured) | - |
| **S1** | fixed + per-byte estimator (2.8) | `_est_us`, `_speed` | two `install` samples (1000 B/5000 ms, 1001000 B/6000 ms) → `-n` shows `~5 s` where the speed model says `<1 s`; `hop3` unchanged | +0.4 s | - |
| **S2** | plumbing neutralized core-wide (ruling 1) | `_retriever`, `_unpack`; `_get`/`_head_size`/`_fetch_resumable` in github, aqua, pkgx, am, conda-forge | a fake `curl` asserting `-q` is argv[1]; `TAR_OPTIONS=--verbose` in the environment of an existing unpack test | +0.5 s | - |
| **S3** | kinds, fan-out, ranking, display (dry run) | `_path_field`, `_probe_all`, `_probe_emit` + new `_fan_out`, `_pick`, `_resolve`, `_show_paths`, `_human_run`, `_index_one` | new executable test channels: `fakecat` (catalog; `fcname`, ambiguous `fcamb`; image `fake.invalid/base:1@sha256:0…`, image_bytes 3000), `fastbox` (runtime, run_ms 100, image missing), `slowbox` (runtime, run_ms 900, image here), `needbox` (runtime, `needs=srneed-helper`). Asserts: both paths listed, fastbox chosen over fewer bytes; `slowbox:fakecat/fcname` pins; `fakecat:fcname` offers both; a native name beats both; a runtime exiting 2 is `not available` in `-n`; no runtime is the unrunnable message and 127; needbox asked only when alone; ambiguous menu lists `fakecat:x` once; `-i fastbox` gets no helper | +3 s | - |
| **S4** | obtain side | `_locate`, `_ask`, `_obtain`, `_obtain_through_tool` | fastbox/slowbox `obtain` write a launcher and print `timing=`: `--yes fcname` runs; the question has once lines, total, per-run line and environment warning; inventory `via fakecat`; timings hold `image`/`install`/`run` and no whole-call line | +2 s | S3 |
| **S5** | list, purge, ephemeral | `_list`, `_purge` (catalog spec, whole purge collects), main | `--purge fakecat:fcname` takes both runtimes' placements; whole purge calls `collect` with `CMDFOUND_COLLECT=all` before the rm; `--list` uses `size`; `--ephemeral` exports the flag | +1.5 s | S0, S4 |
| **S6** | `confined-launch` | new `cmdfound.d/confined-launch` (644) | sourced directly in tests with a fixture HOME: mounts (HOME, cwd under HOME, `/usr` not mounted, socket), env (PATH/LD_PRELOAD dropped, `GNUPGHOME` under HOME kept, `EDITOR=/usr/bin/vim` dropped, a token passed by name only), `_build_network` (proxy names listed, CA file chosen from `SSL_CERT_FILE` then `CURL_CA_BUNDLE`) | +0.5 s | - |
| **S7** | `alpine` | new `cmdfound.d/alpine`; top of block exports `CMDFOUND_ALPINE_MIRROR`/`_REGISTRY` to local fixtures | APKINDEX fixture (≥100 packages, gzip-built in the test), registry fixture dir; index/probe/recipe/search; closure bytes; `candidate=`; version mismatch 1; bad index keeps old; `TAR_OPTIONS` immune; existing "fetching am, aqua and pkgx at once" lines now read "alpine, am, aqua and pkgx" (updated to the new truth, not weakened) | +2 s | contract only |
| **S8** | `docker` | new `cmdfound.d/docker`; `tests/cmdfound.d/fake-docker` (644) | fake-docker: images are directories with `bin/`, `labels`, `id`; `run` executes `<root>/bin/<prog>` with **only** the `-e` environment, honours `-w`; logs argv and its own HOME. Asserts: down/rootless/ephemeral unavailable; build by digest, labels, tag mapping; launcher argv (`-i`, no `-t` without a tty, `--init`, `-u`, `--group-add`, HOME and cwd mounts, `-e NAME` without values, `-e HOME=<real>`); program sees the token and not `LD_PRELOAD`; stdin, exit status, stderr apart; the docker CLI sees the test HOME and `DOCKER_CONFIG`/`DOCKER_HOST` exactly as set; nothing cmdfound keeps lands outside `channels/docker` (a `find`, allowing `$HOME/.docker`); a proxy variable reaches the build and a CA file is copied, not mounted; 125 with a missing image gives 127; collect removes unnamed labelled images and pulled bases, never with `-f`; size | +4 s | S5, S6, S7 |
| **S9** | `udocker` | new `cmdfound.d/udocker`; `tests/cmdfound.d/fake-udocker` (the `maincmd.py` of a fake sdist tar.gz), `fake-python3` (drops `-E -s`, runs the script with sh), PyPI JSON fixture, engines tar.gz fixture | tool hop verified (fake sdist digest); setup hop `[none]`; python3 through `needs/`; env of each udocker call logged: HOME, UDOCKER_DIR/KEYSTORE, XDG_RUNTIME_DIR in the channel, `UDOCKER_TARBALL` empty at run and the user's value during setup, the user's `UDOCKER_LOGLEVEL` passed; `http_proxy` and `SSL_CERT_FILE` reach udocker's process, and the build gets the proxy by name and the CA as a copy; nothing written under the test HOME, `~/.udocker` above all; ranking udocker over docker with both present; Ctrl-C → 130 through util-linux `script` feeding `\003`, skipped without it as the `twin` tests do; purge rm works on a read-only dir left inside a container | +5 s | S5, S6, S7 |

Parallel: S0, S1, S2, S3, S6 and S7 start together. They touch disjoint functions (S1's
`_est_us` is called but not changed by S3/S4; S2 touches `_retriever` and the channel
files only). S4 follows S3 (same area); S5 follows S0 and S4. S8 and S9 run in parallel
after S5+S6+S7: disjoint new files. All steps append to the cmdfound block of
`tools.db`; a textual conflict there is mechanical and resolved at rebase. Expected total
≈ +20 s on the block, including ≈1.5 s of three extra fake channels and two runtimes
answering `probe` 1 on every resolution.

Before S9 merges, a spike on the real udocker (not a test): `apk add` under P1, pull by
digest and presence by `ud/repos`, SIGTERM behaviour; results in the commit message (R1, R2, R4).

---------------------------------------------------------------------------------

## 7. Risks

- **R1** `apk add` under udocker P1 (proot fake root) was not built in phase 1 (`persist/`
  holds docker builds). If it fails, udocker has no install step: verify first (S9 spike).
- **R2** udocker pull by `repo@sha256:<index digest>` and the layout of `ud/repos` for
  a digest are unverified. Fallback: pull by tag and check the digest in its manifest.
- **R3** Docker 29 on the containerd image store (the default for new installs) keeps no
  parent/child link. `rmi` of a base then succeeds while committed images keep its layers
  (harmless: re-pulled when needed), and `.Size` minus the base's may not be the unique
  size. This machine runs overlay2, so check containerd elsewhere before trusting `size`.
- **R4** SIGTERM sent to the udocker launcher's pid alone leaves udocker running until it
  ends: the shell must stay in the foreground for Ctrl-C. Signals sent to the group
  (terminal, `timeout`, systemd) are unaffected.
- **R5** Users not in `/etc/passwd` (LDAP, sssd): udocker `--hostauth` fails to start and
  docker names do not resolve. Later: a passwd generated from `getent`.
- **R6** One daemon, several homes: `cmdfound/alpine:figlet-2.2.5-r3` moves to the last
  home that built it. Launchers use ids and collect uses labels, so nothing breaks; only
  the tag moves.
- **R7** Resolution cost: each alpine hit adds `docker info` (~0.1–0.3 s) and a udocker
  `version` once per tool version.
- **R8** Endpoint: the user's context or `DOCKER_HOST` may be `ssh://…` or a non-loopback
  `tcp://…`, a daemon that cannot mount this machine's HOME. The probe reads the endpoint
  with `docker context inspect --format '{{.Endpoints.docker.Host}}'` and refuses one
  that is neither a unix socket nor loopback tcp, saying why.
- **R14** With the user's `~/.docker` in play, a broken credential helper or cli-plugin now
  fails cmdfound's docker calls the way it fails the user's own. The failure's first line
  is passed through as `unreachable=`.
- **R9** Per-run-first ranking: under `--latest`, a package already built for docker can be
  built again through udocker, because udocker runs faster. The question shows both, and
  `docker:` pins.
- **R10** A host `TERM` Alpine's terminfo lacks (`xterm-kitty`) is passed and complained
  about. Out of scope.
- **R11** `--init` needs docker-init; a `docker` that is podman's shim fails `info --format`,
  which reads as unavailable with podman's message.
- **R12** Simultaneous obtains of one package (an open core item) now also race on
  `docker commit` tags and udocker container records.
- **R13** A mirror newer than the index fails the pinned install (1.3): honest, but one
  `--index-update alpine` away.

---------------------------------------------------------------------------------

## 8. Open questions for the owner

- **Q1 udocker pulls are anonymous** (§5): its keystore must stay in the channel, so
  `udocker login` credentials are never read. Recommend accepting this for milestone 1:
  one base pull per catalog release, and the 429 failure points at `docker:<spec>`.
  A cmdfound login verb for udocker waits until a private registry is needed.
- **Q2 The udocker tool is the PyPI sdist, not the wheel.** Same PyPI sha256 verification.
  The sdist keeps `maincmd.py` executable and unpacks with tar, which the core already
  requires. The wheel needs `unzip` (or a python fallback in `_unpack`) and a chmod rule
  in `_place_tool`. Recommend the sdist.
- **Q3 `--network=host` for docker runs and builds.** Localhost services reachable as natively
  and as udocker already allows; it widens the container's network view. Recommend yes,
  since confinement here is for installing, not for sandboxing.
- **Q4 How per-run time ranks.** Per-run first, then one-time (recommended: a decision runs
  for ever, and it gives "udocker wins by default"), versus one-time + K × per-run with some
  fixed K. With K = 10, docker would win every first install, since udocker's engines
  cost ~44 s once.
- **Q5 A cwd that would hide the container's system** (`/`, `/usr`, `/etc`…). Recommend: run
  unmounted in `/` with one stderr line. The alternative is to refuse with 127.
- **Q6 Runtime unavailability in the question.** Recommend: `docker: not available, <why>` only
  in `-n`, or in the error when nothing can run the program. Otherwise a user without
  docker access would read "(docker could not be asked, a quicker path may exist)" on
  every Alpine question, and it would be untrue: docker runs slower.
