# code-freeze

Functions in cmdfound.in carry a tag on their definition line:

    _has_line() { #@frozen 2026-10-05 m@javier.io <sha>

`#@reviewed` or `#@frozen`, the date, the reviewer, and the commit whose body was
approved. `code-freeze --check cmdfound.in` reports every body that differs from
the one at its commit. The tool lives in github.com/javier-lopez/learn,
`sh/tools/code-freeze`; run it from this repo's root.

- A tag is not a lock. Change a tagged function when the task needs it; it goes
  red until the owner re-reads and re-signs it. Name every tagged function you
  touched when you hand the work over.
- Never re-sign a function yourself unless the owner asks. When asked to sign
  many at once: commit, write each tag with code-freeze's own `tag_awk` naming
  that commit, then run `--check`.
- Channels carry no tags.
