# Brief: which Linux distributions are worth a cmdfound channel

## Context
cmdfound (this repository; read README.md, AGENTS.md, .agents/channels.md and
cmdfound.d/alpine) runs a command that is not installed by asking channels. Its maxim: any program
that runs on Linux is one step away, covered with the fewest channels and the least code. Distros
run as CATALOG channels inside the docker/udocker runtimes (like `alpine`, which installs with apk
inside an image), so anything with an official container image is reachable without root on the host.
Maxims that rule sources out: never compiles, never elevates on the host, verifies what it downloads,
never guesses (a bare command name resolves only through an honest command->package map).

## The common measure (everyone uses exactly this)
A distro's COMMAND SET = sorted, unique basenames of files its binary packages install under
/usr/bin, /bin, /usr/sbin, /sbin (one name per line, nothing else), for x86_64, from the official
file-list index - never by installing packages:
  apt: dists/<suite>/<comp>/Contents-amd64.gz (or <suite>/Contents-amd64.gz)
  rpm: repodata *filelists.xml* ; pacman: <repo>.files ; apk: APKINDEX `p:` cmd:NAME provides
  xbps: whatever Void publishes (say what you used)
Write each set to research/distros/sets/<name>.txt
(name like debian-sid, ubuntu-24.04, fedora-43, arch, ...). Also keep /usr/sbin+/sbin names separately
countable (write <name>.sbin.txt with only those) since they are mostly root tools.
Record for each: index URLs, date fetched, package count, command count.

## Rules
- Work in your own directory under .../scratchpad/cov/<your-topic>/; keep downloads there; delete
  big downloads when done, keep the sets and a small script that rebuilds them.
- Do not touch this repository or any repo. No pushes, no installs on the host, no sudo.
- Numbers you could not measure are said as "not measured", never estimated silently.
- Report: write .../scratchpad/cov/<your-topic>/REPORT.md (English, short, tables) and reply with
  its path plus the 5-10 lines that matter.
