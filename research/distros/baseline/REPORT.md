# Baseline: commands cmdfound's current channels already reach

Fetched 2026-10-26T06:32Z. Rebuild: `./fetch.sh && ./build.sh` (aqua/pkgx use the channels' own
`_indexer`, copied verbatim into `aqua_indexer.sh` / `pkgx_indexer.sh`; nix and AM repeat the channels' filters).

| Set | Source (what the channel reads) | Packages | Commands | Only here* |
|---|---|---:|---:|---:|
| nixpkgs | programs.sqlite in nixexprs.tar.xz of nixos-26.11pre1100280.3ec636362e18 (Programs, x86_64-linux) | 26,535 | 54,986 | 38,244 |
| alpine-3.22 | v3.22 main+community x86_64 APKINDEX, `p:` cmd: provides | 26,325 | 18,196 | 4,065 |
| alpine-edge | edge main+community (comparison; channel pins a release) | 29,067 | 19,333 | (1,751 not in 3.22) |
| aqua | aqua-registry main `registry.yaml`, github_release packages, `files:` names (else repo name) | 2,049 | 2,237 | 854 |
| pkgx | dist.pkgx.dev/pantry.tar.xz, package.yml `provides:` (linux) | 1,608 of 1,929 | 4,579 | 529 |
| am | AM `programs/x86_64-apps` app names | 8,993 | 8,993 | 7,722 |
| binstall | cargo-quickinstall release tags -> crate names | 4,772 crates (12,711 tags) | 4,772 | - |
| conda-forge | not measured | - | - | - |
| github | no catalog | - | - | - |

\* among the five bare-name sets (nixpkgs, alpine-3.22, aqua, pkgx, am).

Unions (in `../sets/`):
- `current-union-bare.txt` = nixpkgs + alpine-3.22 + aqua + pkgx + am = **68,276** (what a bare command name resolves through today).
- `current-union.txt` = the above + alpine-edge + binstall = **72,544** (everything produced).

## Caveats
- No `.sbin.txt` here: programs.sqlite, `cmd:` provides, aqua, pkgx and AM give names only, no paths, so /usr/sbin vs /usr/bin cannot be split from these indexes. Not measured.
- **binstall and conda-forge never resolve a bare name**: both `_probe` exit unless `CMDFOUND_NAMED` is themselves (binstall:490, conda-forge:302). binstall's set is crate names, not binary names (ripgrep, not rg), from tags of every target (upper bound for x86_64 Linux) and leaves out crates reachable only through the author's own releases (not measured). Use `current-union-bare.txt` to compute what a new distro adds.
- **conda-forge not measured**: the channel reads channeldata.json (package names, no files); commands are known only after a package downloads (its `paths.json`). A full file list would need the conda-forge-metadata/libcfgraph artifacts (tens of GB, per-version), not cheap; since the channel is named-only it adds nothing to the bare union anyway.
- AM names are app names, which AM installs as the launcher command; usually equal, not checked per app.
- aqua only reads `type: github_release` packages, as the channel does.
- github: no catalog (named owner/repo only); nothing to measure.
