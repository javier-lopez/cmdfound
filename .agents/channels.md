# Channels

## Protocol

A channel is `cmdfound.d/<name>`, or a row `cmdfound.d/<family>.d/<format>.d/<name>`
run by its family, called as `<name> VERB ARGS...`; no two share a name:

- `meta` prints its fields: `kind confines manager needs reclaims`, in that order
- catalog channels: `index [bytes]`, `search WORDS...`; asked ones: `probe`, `locate`,
  `obtain`, `size`, `reclaim` (each channel's `#usage:` line says which it has)

Answers are `key=value` lines on stdout. Status codes:

    0  answered             1  does not have it (failed=why)
    2  could not be asked   (unreachable=why)    3  ambiguous (candidate= lines)

Use the api to answer: `_api_answer_failed`, `_api_answer_unreachable`,
`_api_answer_no_index`, `_api_answer_bytes_of`. stderr is a log, never an answer.

## Conventions

- One concept, one name, in every channel: `_platform`, `_run_tool`, `INDEX`, the
  verb functions `_meta _index _probe _locate _obtain ...`. Before naming a function
  look for the concept in the other channels and use their name. One name also
  means one contract: same outputs and same accepted inputs, or two names.
- The boilerplate lines (`SELF=`, `CH=`) are the same, with the same comment, in
  every channel.
- No channel calls curl or wget: fetch with the api's `_api_fetcher*` family. When
  it lacks something, add the smallest general member to the api.
- An index that has its download is not cut short: `_api_catalog_arrived` there,
  never a bare `trap '' TERM`. It tells cmdfound the catalog is here, so a race
  another channel wins leaves this one reading to the end instead of waiting on it.
- An interrupted obtain is undone the same way everywhere: `made` holds what is
  being built, `_util_trap_exit '_undo'` removes it, `made` is emptied once the
  placement is whole.
- Arguments: a function of 25 lines or fewer reads `${1}` and documents it on its
  `#$1 =>` line; a longer one names its arguments on its first code line.
- Channels may define names the api has (`_resolve`, `_placed`, `_tool_version`);
  that is deliberate.
- File header: `#description:` and `#usage:` only; the usage matches the dispatch case.

## Coverage: before adding a channel

cmdfound's premise: if a program runs on Linux, it is one step away. The
channels here are the smallest set found that covers all of it, or nearly. A
new channel earns its place only by what it adds after them, measured as
commands no current channel reaches.

- A source whose packages a channel already reaches is named on that channel's
  `#covers:` header line, with what was measured (`grep '^#covers:' cmdfound.d/* cmdfound.d/*.d/*.d/*`).
- A source no channel covers but that was ruled out is a note `cmdfound.d/discarded/<name>`,
  a directory and so never a channel nor built in, with `#why:` (`grep '^#why:' cmdfound.d/discarded/*`).
- Look in both before proposing one. The tests keep them apart from the channels.

From research/SUMMARY.md (2026-10-26): one channel per package format,
a distro being a row in it. A row (`cmdfound.d/distro.d/<format>.d/<name>`:
alpine, wolfi, ubuntu, alt, fedora, opensuse, epel, rosa, arch, blackarch) is
data only, what differs: mirror, repositories, image, base. `cmdfound.d/distro`
runs it: it loads the row, then its format (`distro.d/apk`, `apt`, `aptrpm`,
`rpm`, `pacman`, the file the row's directory is named after), which says how the
catalog is weighed, fetched and read into rows (`_index_bytes`, `_fetch`,
`_rows`) and the one line that installs (`_install_line`); distro has
everything else once: the machine, the verbs, one index for every format,
and what a package pulls in beyond its image, walked once when the catalog is
indexed. What reads an image off a registry is the api's `_api_registry_*` and
`_api_image_in`. Before writing anything in a format, look whether distro has
it. Pentest tools come from blackarch; Kali, Parrot, BackBox and Exegol are
discarded. Not decided yet: x-cmd (deferred; 114
commands after nix, ~70 of them npm or pip), Homebrew bottles, Flathub, and a
rootfs runtime (Alpine with unshare or proot).

## Comments

Short. The model is the first functions of cmdfound.in:

    _has_line() {
        #$1 => lines, $2 => a whole line
        #    _has_line "${meta}" "confines=no"  =>  0
        #    _has_line "${meta}" "confines"     =>  1

        #the newlines make the match whole, and a case, because a grep is a process

Trivial functions get no comment. A why-note is one line, only where the code
would read as a mistake without it. Every example must be true: run it against
the real function (copy it into a probe file and load it with
`cmdfound.in --channel <probe>`) or check its shape against the fakes in
`tests/cmdfound.d`.
