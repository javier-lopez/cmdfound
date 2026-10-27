# usage: find PANTRY/projects -name package.yml | (. pkgx_indexer.sh; _indexer)   (copied verbatim from cmdfound.d/pkgx)
# reads the pkgx pantry's package.yml files: name, dep and cmd lines
_indexer() {
    #package.yml paths on stdin; prints lines a tab apart
    #    .../projects/curl.se/package.yml  =>  name  curl.se  cURL
    #                                          dep   curl.se  openssl.org
    #                                          cmd   curl     curl.se
    while read -r _indexer__f; do
        _indexer__p="${_indexer__f%/package.yml}"
        _indexer__p="${_indexer__p#*/projects/}"
        printf "%s\\t%s\\n" "${_indexer__p}" "${_indexer__f}"
    done | awk -F'\t' '
        function unquote(v) {
            if (v ~ /^"/)      { sub(/^"/, "", v); sub(/"[ \t]*(#.*)?$/, "", v) }
            else if (v ~ /^'\''/) { sub(/^'\''/, "", v); sub(/'\''[ \t]*(#.*)?$/, "", v) }
            else               { sub(/^#.*$/, "", v); sub(/[ \t]+#.*$/, "", v); sub(/[ \t]+$/, "", v) }
            return v
        }
        {
            project = $1; file = $2; sect = ""; sub_key = ""; sub_ind = -1; pend = ""
            while ((getline line < file) > 0) {
                if (line ~ /^[ \t]*#/ || line ~ /^[ \t]*$/) continue
                if (sect == "display-name") {
                    if (line ~ /^ /) {
                        val = line; sub(/^ +/, "", val); val = unquote(val)
                        if (val != "") printf("name\t%s\t%s\n", project, val)
                    }
                    sect = ""
                    if (line ~ /^ /) continue
                }
                #yaml lets a list sit at the same column as its key, so a
                #"- " at column 0 is still an item of provides
                if (sect == "provides" && line ~ /^- /) line = " " line
                if (line ~ /^[^ ]/) {
                    sect = ""; sub_key = ""; sub_ind = -1; pend = ""
                    if (match(line, /^[A-Za-z0-9_-]+:/)) {
                        key = substr(line, 1, RLENGTH - 1)
                        val = substr(line, RLENGTH + 1); sub(/^[ \t]+/, "", val)
                        if (key == "display-name") {
                            val = unquote(val)
                            if (val != "") printf("name\t%s\t%s\n", project, val)
                            else sect = key
                        } else if (key == "provides" || key == "dependencies" || key == "companions") {
                            sect = key
                        }
                    }
                    continue
                }
                if (sect == "") continue
                match(line, /^ +/); ind = RLENGTH; body = substr(line, ind + 1)
                if (sub_ind >= 0 && ind <= sub_ind) { sub_key = ""; sub_ind = -1 }

                if (sect == "provides") {
                    if (body ~ /^[A-Za-z0-9\/_-]+:[ \t]*(#.*)?$/) {
                        sub_key = body; sub(/:.*$/, "", sub_key); sub_ind = ind; continue
                    }
                    if (body !~ /^- /) continue
                    if (sub_ind >= 0 && sub_key != "linux") continue
                    item = body; sub(/^- +/, "", item); item = unquote(item)
                    n = split(item, parts, "/"); prog = parts[n]
                    #a name with a template in it is kept by pkgx as written,
                    #braces and all, and nobody types that
                    if (prog != "" && prog !~ /[{} ]/) printf("cmd\t%s\t%s\n", prog, project)
                    continue
                }

                #dependencies and companions. A project whose constraint is on
                #the lines below it is still a dependency: yaml folds them into
                #its value, and pkgx reads "14" where the file says
                #"gnu.org/gcc:" and then "14" on its own line
                if (pend != "") {
                    if (ind > pend_ind && body !~ /^[^:#]+:/) {
                        if (pend_counts) printf("dep\t%s\t%s\n", project, pend)
                        pend = ""; continue
                    }
                    pend = ""
                }
                if (!match(body, /^[^:#]+:/)) continue
                k = substr(body, 1, RLENGTH - 1); v = substr(body, RLENGTH + 1)
                sub(/^[ \t]+/, "", v); v = unquote(v)
                sub(/^[ \t]+/, "", k); sub(/[ \t]+$/, "", k)
                counts = (sub_ind < 0 || sub_key == "linux")
                if (v == "") {
                    #every project has a dot in its name and no platform key
                    #does, so a key with nothing after it is either a project
                    #whose value comes next, or a block. Only linux is read
                    if (index(k, ".")) { pend = k; pend_ind = ind; pend_counts = counts }
                    else               { sub_key = k; sub_ind = ind }
                    continue
                }
                if (!counts) continue
                if (k == "linux" || k == "darwin" || k == "windows") continue
                printf("dep\t%s\t%s\n", project, k)
            }
            close(file)
        }'
}
