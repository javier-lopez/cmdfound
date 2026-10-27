# cmdfound

From `command not found` to executed in seconds. On-demand binary provisioning.
`cmdfound` asks channels (github releases, aqua, nix, docker...) who can
provide it, picks the quickest and runs it.

    cmdfound jq --version          # find jq, confirm, run it
    cmdfound -n ripgrep            # only show the routes
    eval "$(cmdfound --hook bash)" # in ~/.bashrc: for the automatic resolution
    
Install: copy `cmdfound` (one POSIX sh file) anywhere on your PATH.

    cmdfound --upgrade #for automatic upgrades
