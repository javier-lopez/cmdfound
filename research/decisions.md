# Decisions

The owner's rulings behind cmdfound, distilled from the working notes of
2026-09 (removed on 2026-10-26; git history has them). Each was made by the
owner or accepted by them. The code and `.agents/` win where they disagree.

## Maxims
- Never elevates on the host, never sudo: what needs root runs inside a
  container. Never compiles (nix `--max-jobs 0`, binstall without builds).
  Telemetry off.
- `rm -rf channels/<ch>` removes a channel completely, over any user variable.
  The one exception is docker, which is system-wide.
- Never writes a user's configuration file (`channels.conf`, rc files,
  `~/.docker/config.json`), neither cmdfound nor its channels' tools.
- Native before dockerized, always: the class orders before time. Managers that
  need a runtime of their ecosystem (npm, PyPI, apt, apk, brew) run only
  dockerized.
- Never guesses: a bare name resolves only through an honest command->package
  map; when ambiguous, a menu.
- Reads other people's catalogs. Never writes package recipes, never publishes
  or mirrors a catalog, never needs hosting of its own: the product is the script.
- The first run takes the fastest path; the second is indistinguishable from
  having it installed (direct `exec`, no network, no question, no message).
- Whoever downloads verifies. Badges: `verified` (cmdfound checked a published
  checksum), `none` (nothing to check against), `via <channel>` (its tool
  checks). A checksum that does not match is the only block, and it is strict;
  no checksum installs and says `none`.
- Honest costs: unknown + known = at least the known part. No size is written
  by hand: it is learnt at run time (HEAD, the index) or stays unknown. No byte
  or hop limits: the cost is shown and the user decides.
- GitHub API quota: `GITHUB_TOKEN`/`GH_TOKEN` only if the user exported them,
  only to api.github.com, through stdin. A token is never searched for.
- A channel that could not be asked says it does not know, never "no".

## User configuration
- A channel's tool has the channel as its HOME and never reads the user's rc
  files. Its own variables pass (`AQUA_*`, `PKGX_*`, `NIX_CONFIG`, `CONDA_*`,
  `BINSTALL_*`...), including the ones that turn verification off: that is the
  user's call.
- Only location variables that would move state out of the channel are
  overridden (`MAMBA_ROOT_PREFIX`, `CARGO_HOME`, `NP_LOCATION`, `NIX_STORE*`,
  `UDOCKER_DIR`...). The owner's rulings (no compile, no sudo, no telemetry) win
  over any variable.
- Plumbing (curl, wget, tar, unzip, gzip, sqlite3) ignores rc files: `curl -q`,
  `wget --no-config`, `sqlite3 -init /dev/null`. From `~/.curlrc`/`~/.wgetrc`
  only the network lines pass (proxy, proxy-user, noproxy, cacert, capath,
  proxy-cacert), exported as the standard variables without overriding the
  user's.
- docker uses the real HOME, config, logins and credential helpers. udocker
  does not: its keystore is generated in its channel from docker's config.

## Containers
- Runtimes (docker, udocker) plus catalog channels (one per package format, a
  distro being a row). A catalog gives the recipe; the runtime pulls the image,
  installs as root without mounts, persists, and writes the launcher.
- One path per available runtime; inside the dockerized class the fastest per
  run wins. The user-facing word is "dockerized".
- The program sees the real HOME and environment, minus host-path variables.
  HOME and /tmp are mounted; from another cwd it runs in `/` with a warning.
  Confinement is for installing as root without touching the host, not a sandbox.
- Users pass their own runtime flags with `CMDFOUND_DOCKER_FLAGS` and
  `CMDFOUND_UDOCKER_FLAGS`.
- Images carry `io.cmdfound.*` labels and are swept only by an explicit
  `--purge`, never automatically: the daemon is shared.

## Core
- `--yes` only skips the confirmation before spending bytes; it never chooses
  for the user. Without a terminal nothing downloads and `--yes` is suggested.
  127 means nothing ran; any other code is the program's.
- Cost order: class, estimated time on this machine, hops. Estimates are a
  fixed cost plus a per-byte cost, learnt from the last runs of each step.
- One home, `~/.cmdfound`, holds everything, `channels.conf` included, so one
  `rm -rf` removes cmdfound. `CMDFOUND_HOME` moves it; XDG_CACHE_HOME is not read.
- Two installs of the same channel, package and version take a lock; the second
  waits and uses what the first placed. A full `--purge` refuses while an
  install runs and names its pid.
- Comments only where they say why: a workaround, a portability constraint, an
  owner's ruling, a trap, or a function's contract.
- Name: cmdfound, the opposite of "command not found" (`command-not-found` is
  Ubuntu's and NixOS's package).

## Channel rulings
- conda-forge and binstall answer only when named: neither has a downloadable
  command map.
- binstall: QuickInstall first (signed); otherwise the author's release, shown
  as `none`. The newest version wins even unsigned.
- nix-portable: sizes always unknown; only the floor is announced (the tool and
  nixexprs, each on its own line).
- AM: its size is AM's business; cmdfound does not query GitHub for it.
- x-cmd: deferred. Its tool has no checksum, and of its 114 commands new after
  nix, ~70 are npm or pip.
- Sources ruled out: `cmdfound.d/discarded/<name>`, each with its #why.
  Sources a channel covers: that channel's `#covers:` line.

## Open, for the owner
- `--index-update` with no channel: whether it also fetches catalogs never
  fetched, and whether it becomes `--catalog-update`.
- `--apropos` warns when a catalog is more than a week old; that threshold was
  never justified.
- `-U` and installation: review pending (perhaps a single file).
