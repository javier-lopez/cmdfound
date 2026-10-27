_indexer() {
    #the registry's yaml on stdin, a line per command
    #    repo_owner: acme, repo_name: ripgrepx, files: rgx, description: searches for text  =>  rgx<TAB>acme/ripgrepx<TAB>searches for text

    #awk, not a yaml parser: checked byte for byte against one over every package
    awk '
    function emit(name) { printf("%s\t%s/%s\t%s\n", name, owner, repo, desc) }
    function unquote(v) {
        if (v ~ /^".*"$/)      { v = substr(v, 2, length(v) - 2); gsub(/\\\\/, "\\", v) }
        else if (v ~ /^'\''.*'\''$/) { v = substr(v, 2, length(v) - 2); gsub(/'\'''\''/, "'\''", v) }
        #outside quotes, whitespace then # starts a comment, and yaml drops it
        else                   { sub(/[ \t]+#.*$/, "", v) }
        return v
    }
    function squeeze(v) { gsub(/[ \t]+/, " ", v); sub(/^ /, "", v); sub(/ $/, "", v); return v }
    function flush(   list, n, i, parts) {
        if (in_block) { desc = squeeze(desc); in_block = 0 }
        if (type != "github_release" || owner == "" || repo == "") return
        if (ov_true_has_files)  list = ov_true_files
        else if (pkg_has_files) list = pkg_files
        else                    list = ""
        if (list == "") { emit(repo); return }
        n = split(list, parts, SUBSEP)
        for (i = 1; i <= n; i++) if (parts[i] != "") emit(parts[i])
    }
    #a package may open with any of its keys, type, name or repo_owner: reading
    #only "- type:" merged it into the package before, and the commands of one
    #went to the repository of the other - "nsc" came out as nakabonne/ali
    /^  - [a-z_]+:/ {
        flush()
        type = ""; owner = ""; repo = ""; desc = ""; top = ""
        in_ov = 0; ov_true = 0; sub8 = ""; in_block = 0
        pkg_has_files = 0; pkg_files = ""; ov_true_has_files = 0; ov_true_files = ""
        sub(/^  - /, "    ")
    }
    in_block {
        if ($0 ~ /^     / || $0 ~ /^[ \t]*$/) { l = $0; sub(/^ +/, "", l); desc = desc " " l; next }
        desc = squeeze(desc); in_block = 0
    }
    /^    [a-z_]+:/ {
        key = $1; sub(/:$/, "", key)
        val = $0; sub(/^    [a-z_]+:[ ]*/, "", val)
        top = key; in_ov = 0; sub8 = ""
        if (key == "type")             type = unquote(val)
        else if (key == "repo_owner")  owner = unquote(val)
        else if (key == "repo_name")   repo = unquote(val)
        else if (key == "description") { if (val ~ /^[>|]/) { in_block = 1; desc = "" } else desc = squeeze(unquote(val)) }
        else if (key == "files")       pkg_has_files = 1
        next
    }
    top == "files" && /^      - name:/ {
        v = $0; sub(/^      - name:[ ]*/, "", v); pkg_files = pkg_files unquote(v) SUBSEP; next
    }
    top == "version_overrides" && /^      - version_constraint:/ {
        v = $0; sub(/^      - version_constraint:[ ]*/, "", v)
        in_ov = 1; ov_true = (v == "\"true\""); sub8 = ""; next
    }
    top == "version_overrides" && in_ov && /^        [a-z_]+:/ {
        k = $1; sub(/:$/, "", k); sub8 = k
        if (k == "files" && ov_true) ov_true_has_files = 1
        next
    }
    top == "version_overrides" && in_ov && ov_true && sub8 == "files" && /^          - name:/ {
        v = $0; sub(/^          - name:[ ]*/, "", v); ov_true_files = ov_true_files unquote(v) SUBSEP; next
    }
    END { flush() }
    '
}
