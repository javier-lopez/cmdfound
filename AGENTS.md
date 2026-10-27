# Agents

cmdfound is one POSIX sh program. Read the file in `.agents/` that matches the
task before touching code.

- `.agents/architecture.md` — the layout of cmdfound.in, how channels load, the build
- `.agents/channels.md`     — the channel protocol and the conventions every channel follows
- `.agents/testing.md`      — running the suite, writing tests, what a test must report
- `.agents/code-freeze.md`  — the review signatures on functions
- `.agents/sh-style.md`     — the owner's sh style, and where cmdfound departs from it

Rules that apply to every change:

1. Edit `cmdfound.in` and `cmdfound.d/`. Never edit `cmdfound`: `./build` writes it,
   and the pre-commit hook rebuilds and stages it
   (`git config core.hooksPath .githooks`, once per clone).
2. POSIX sh only: it must run under dash, bash, busybox ash, and with gawk and mawk.
3. Root cause before any fix. No silenced errors, no weakened tests.
4. Run `cd tests && sh tools.sh` before you say something works, and report the
   suite's time before and after any test you add.
5. Code, comments and commit messages are in English. Comments are short, with
   examples (see the first functions of cmdfound.in); trivial functions get none.
6. Do not push or publish without the owner asking.
7. The repository is private while in development and will be opened: write
   nothing that could not be public (no secrets, no paths of this machine).
