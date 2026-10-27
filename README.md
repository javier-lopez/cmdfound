# cmdfound

From `command not found` to executed in seconds. On-demand binary provisioning.
`cmdfound` asks channels (github releases, aqua, nix, docker...) who can
provide it, picks the quickest and runs it.

[![cmdfound](https://javier.io/assets/img/cmdfound.gif)](https://asciinema.org/a/1270228)

    cmdfound jq --version          # find jq, confirm, run it
    cmdfound -n ripgrep            # only show the routes
    eval "$(cmdfound --hook bash)" # in ~/.bashrc: for the automatic resolution

More demos (routes, channels, distro catalogs, cleanup): https://javier.io/blog/en/2026/10/27/cmdfound.html
    
Install: copy `cmdfound` (one POSIX sh file) anywhere on your PATH.

    cmdfound --update #update cmdfound to its latest
