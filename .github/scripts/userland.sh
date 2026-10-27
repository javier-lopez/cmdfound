#!/bin/sh
#description: says which implementation answers each name cmdfound calls, for the CI job summary
#usage: userland.sh TARGET

#every target of the cmdfound portability workflow runs this before it runs the
#block, so that a job that fails says what it was running on and a job that
#passes says what it proved. It is written for the poorest shell of the eight -
#busybox ash - and uses nothing but the shell, printf and the programs it is
#asking about. Nothing here may fail the job: a name that is not there is
#reported as not there, which is the answer

target="${1:-unnamed}"
out="${GITHUB_STEP_SUMMARY:-/dev/stdout}"

_first() {
    #$1 => a program, then the arguments that make it say what it is. The first
    #line of what it says, or a dash. Its stderr is part of the answer: busybox
    #writes its banner there, and a program that refuses the argument says so
    _f__p="${1}"; shift
    command -v "${_f__p}" >/dev/null 2>&1 || { printf "%s" "-"; return 0; }
    _f__s="$("${_f__p}" "${@}" 2>&1 | sed -n '1p' | tr -d '|')"
    printf "%s" "${_f__s:--}"
}

_where() {
    #$1 => a program. Where it is, or "not here"
    command -v "${1}" 2>/dev/null || printf "%s" "not here"
}

{
    printf '## %s\n\n' "${target}"
    printf '| what | here |\n|---|---|\n'
    printf '| uname | %s |\n' "$(uname -s -m 2>&1 | tr -d '|')"
    printf '| /bin/sh | %s |\n' "$(_where /bin/sh)"
    printf '| $0 of /bin/sh | %s |\n' "$(/bin/sh -c 'echo "${0}"' 2>&1 | tr -d '|')"
    printf '| awk | %s |\n' "$(_first awk --version) at $(_where awk)"
    printf '| sed | %s |\n' "$(_first sed --version)"
    printf '| grep | %s |\n' "$(_first grep --version)"
    printf '| find | %s |\n' "$(_first find --version)"
    printf '| tar | %s |\n' "$(_first tar --version)"
    printf '| curl | %s |\n' "$(_where curl)"
    printf '| wget | %s |\n' "$(_first wget --version)"
    printf '\n'
    printf 'Programs cmdfound calls, and whether this target has them:\n\n'
    printf '```\n'
    for p in awk sed tr grep sort comm head cat tee wc cp mv rm rmdir mkdir \
             ln chmod ls readlink find du mktemp date sleep expr id uname env \
             getconf tar gzip unzip xz sha256sum shasum openssl curl wget \
             sqlite3 python3 bash git docker; do
        printf '%-11s %s\n' "${p}" "$(_where "${p}")"
    done
    printf '```\n\n'
    printf 'What the clock and the digest can do here, which decide two of the\n'
    printf 'findings this matrix exists to show:\n\n'
    printf '```\n'
    printf 'date +%%s      %s\n' "$(date +%s 2>&1)"
    printf 'date +%%s%%N     %s\n' "$(date +%s%N 2>&1)"
    printf 'date +%%s.%%N    %s\n' "$(date +%s.%N 2>&1)"
    if command -v sha256sum >/dev/null 2>&1; then digest="sha256sum"
    elif command -v shasum >/dev/null 2>&1; then digest="shasum -a 256"
    elif command -v openssl >/dev/null 2>&1; then digest="openssl dgst -sha256"
    else digest="none of the three"; fi
    printf 'digest        %s\n' "${digest}"
    lname="$(find . -name . -prune -lname x 2>&1 >/dev/null | sed -n '1p')"
    printf 'find -lname   %s\n' "${lname:-taken}"
    printf 'getconf glibc %s\n' "$(getconf GNU_LIBC_VERSION 2>&1 || printf 'refused')"
    printf '```\n'
} >> "${out}"

exit 0
