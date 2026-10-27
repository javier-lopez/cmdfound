# usage: aquacmds.py registry.yaml NAME...
# reads aqua's registry.yaml (https://raw.githubusercontent.com/aquaproj/aqua-registry/main/registry.yaml): which NAMEs are commands of a package (files[].name, else the last part of name/repo_name)
import sys, re, collections
pkgs, cur = [], None
for l in open(sys.argv[1]):
    m = re.match(r'^  - (type|name|repo_owner|repo_name|aliases|files|search_words|description|version_source|link|path|url|format|rosetta2|asset|supported_envs|version_constraint|version_filter|version_overrides|checksum|replacements|overrides|private|no_asset|error_message|go_version_path|crate|cargo|windows_arm_emulation|complete_windows_ext|github_artifact_attestations|slsa_provenance|cosign|minisign|build|vars|version_prefix|repo):?', l)
    if m: cur = {'files': []}; pkgs.append(cur)
    if cur is None: continue
    for k in ('name', 'repo_owner', 'repo_name', 'path'):
        mm = re.match(r'^    %s: (\S+)' % k, l) or (re.match(r'^  - %s: (\S+)' % k, l))
        if mm and k not in cur: cur[k] = mm.group(1)
    mm = re.match(r'^      - name: (\S+)', l)
    if mm: cur['files'].append(mm.group(1))
cmd = collections.defaultdict(set)
for p in pkgs:
    pid = p.get('name') or p.get('path') or f"{p.get('repo_owner')}/{p.get('repo_name')}"
    names = p['files'] or [(p.get('name') or p.get('path') or p.get('repo_name') or '').split('/')[-1]]
    for n in names: cmd[n].add(pid)
print(f'aqua packages={len(pkgs)} commands={len(cmd)}', file=sys.stderr)
for n in sys.argv[2:]:
    if n in cmd: print(n, sorted(cmd[n])[:3])
