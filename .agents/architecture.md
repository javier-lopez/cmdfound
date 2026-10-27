# Architecture

## Files

    cmdfound.in        the program, as developed (run it directly from a checkout)
    cmdfound.d/        the channels. One rule at every level: X is code and X.d/
                       is what X serves or uses
      am aqua ...      a channel, one executable sh file each
      docker.d/        what docker uses: confined-launch (udocker loads it too)
      distro           runs the distros' channels; not a channel itself
      distro.d/        the package formats it serves: apk, apt, aptrpm, rpm, pacman
        rpm.d/         rpm's rows, each a channel: fedora, opensuse, epel, rosa
                       (apk.d/ alpine wolfi, apt.d/ ubuntu, aptrpm.d/ alt,
                       pacman.d/ arch blackarch). A row is data only
      discarded/       sources ruled out as channels, one note each with #why:
    cmdfound           built by ./build: cmdfound.in with the channels appended. Do not edit
    build              ./build [OUTPUT]
    .githooks/         pre-commit: builds from the index and stages cmdfound
    tests/             tools.sh runs the block in tools.db; tests/cmdfound.d holds fakes
    .github/           the portability matrix (dash/bash/busybox/BSD, gawk/mawk, curl/wget)

## cmdfound.in, top to bottom

1. constants and cmdfound's own small helpers (`_usage`, `_die`, `_msg`, ...)
2. internal sections: layout, spec, resolution, cache, lock, list and purge,
   indexes and apropos, update, run
3. `api`: functions named `_api_*`. A function is `_api_` when it would change if
   cmdfound's rules changed: answers and protocol, what cmdfound accepts as a name,
   version or format, fetching, the tool's home, a channel's files
4. `util`: functions named `_util_*`, which would read the same in any shell program
5. `main`: clears inherited variables, reads options, resolves, execs

Unprefixed names are cmdfound's own. A second definition of a name later in the
file silently replaces the first: grep before adding one.

## Channels

A channel is loaded by `_api_channel`, which sources it in a subshell, so it
inherits the whole api and carries no copy. The channels directory is, in order:
`CMDFOUND_CHANNELS`; `cmdfound.d` beside the running file (with `.in` dropped
from its name); else the channels a built cmdfound carries, written once to
`~/.cmdfound/bundle/<BUNDLE_ID>` by `_bundle_in`.

## The build

`./build` copies cmdfound.in, writes `BUNDLE_ID` (the sha256 of the channels),
and appends every channel after an `exit` at the end of the file, where
`_bundle_in` reads them back. The shell never parses past that exit, so carrying
the channels costs a run nothing until it needs them.

## The command-not-found hook

A shell has one handler. `cmdfound --hook` prints cmdfound's own, which is what
users outside see; the README names only that one. The owner runs fuck's
(`fuck --hook`, in javier-lopez/learn), supported first: when nothing else in
its chain applies it execs `cmdfound -- "$@"`, so a change to how cmdfound is
called must keep that working. Both run only in interactive shells and answer
127 when nothing ran.

## Things that are easy to break

- The hot path (a program cmdfound already placed) runs before any channel is
  read; keep it free of forks and channel calls.
- `main` unsets every inherited lowercase `_*` and `g_*` variable: a command-not-found
  handler runs with the user's environment, and theirs and ours share a namespace.
  Globals are `g_*`; function outputs are `_name_in__out`.
- Whoever changes IFS restores what was there: code saves and restores it with
  `x="${IFS}"`, which turns an unset IFS into an empty one.
