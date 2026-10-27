# De qué herramientas depende cmdfound, y qué distribuciones hacen falta para verificarlo

Base: `integrate/channels` en **845e9dd**, leído en un worktree propio. No se tocó nada del árbol de
`/home/m/learn` ni se cambió una línea de código. Este documento es el inventario que pediste y la
matriz derivada de él; el workflow no está escrito y no se escribe hasta que lo revises.

Antes de las tablas, tres advertencias sobre la procedencia de cada dato:

- **"Verificado" quiere decir que lo corrí en esta máquina o dentro de `alpine:3.22`.** Hay un
  apéndice al final con exactamente lo que se ejecutó. Todo lo verificado lleva su salida real.
- **"Inferido" quiere decir que lo leí en el código y razoné sobre la implementación, sin poder
  correrlo.** Todo lo BSD/macOS es inferido: en esta máquina no hay macOS ni FreeBSD, y no se puede
  levantar uno en Docker. Lo digo en cada caso, no una sola vez al principio.
- **`rtk` filtra `grep`, `cat` y `head` y devuelve una versión esquemática.** La primera lectura de
  este árbol salió vacía por eso. Todo lo de abajo se leyó con `rtk proxy` o con la herramienta de
  lectura directa. Lo apunto porque cualquiera que repita este trabajo se va a tropezar igual.

Lo que hay en esta máquina, que es el sesgo de todo lo que sigue: `/bin/sh` es **dash**, `awk` es
**gawk 5.2.1** (y hay `mawk` aparte), `sed` GNU 4.9, `tar` GNU 1.35, `grep` GNU 3.11, `find`
GNU 4.9.0, `wget` GNU 1.21.4, `curl` 8.5.0, glibc. **No hay busybox, no hay sqlite3.** Por eso se
usó un contenedor `alpine:3.22` (una sola descarga de Docker Hub, la imagen queda en la caché
compartida junto a las otras `alpine:*` que ya estaban).

---

## 1. El inventario

### 1.1 De dónde sale y contra qué se comprobó

Se leyeron enteros los 15,465 renglones de `sh/tools/cmdfound` (3,446), los once archivos de
`sh/tools/cmdfound.d/` (7,146) y los 2,824 del bloque `@begin{cmdfound}` de `sh/tests/tools.db`,
más `sh/tests/tools.sh`. Cada nombre de programa se buscó en posición de comando y se leyó su
invocación completa, con sus banderas; no hay ningún nombre en las tablas de abajo que no se haya
visto en su línea.

La clasificación POSIX se hizo contra el texto de POSIX.1-2017 (XCU) para cada utilidad, no de
memoria, y las divergencias se comprobaron contra **las implementaciones que están aquí**: GNU
coreutils/findutils/sed/grep/tar/wget, gawk, mawk, y busybox 1.37.0 dentro de `alpine:3.22`.

**Cuántos nombres son.** 55 programas externos para cmdfound y 13 más que sólo necesita el bloque de
tests; 68 nombres distintos en total. Repartidos así:

| grupo | cuántos | nombres |
|---|---|---|
| utilidades del sistema, se esperan en el `PATH` | 39 | `awk` `sed` `tr` `grep` `sort` `comm` `head` `cat` `tee` `wc` `cp` `mv` `rm` `rmdir` `mkdir` `ln` `chmod` `ls` `readlink` `find` `du` `mktemp` `date` `sleep` `expr` `id` `uname` `env` `getconf` `kill` `tar` `gzip` `unzip` `xz` `sha256sum` `shasum` `openssl` `curl` `wget` |
| se consiguen por `needs=` o son requisito de un canal | 4 | `sqlite3` `python3` `bash` `git` |
| herramientas de canal que cmdfound se busca por sus propios canales | 7 | `aqua` `micromamba` `cargo-binstall` `pkgx` `nix-portable` `udocker` `APP-MANAGER`/`appman` |
| programas que traen esas herramientas, o el runtime de la máquina | 5 | `docker` `nix` `nix-store` `bwrap` `proot` |
| sólo el bloque de tests | 13 | `dd` `seq` `cmp` `mkfifo` `basename` `setsid` `perl` `bzip2` `cut` `tail` `uniq` `touch` `cat -A` (de `cat`) |

### 1.2 Dónde se llama cada cosa

Este diagrama muestra en qué capa vive cada dependencia: lo de arriba corre en cada resolución, lo
de abajo en cada corrida del programa ya instalado.

```
  core (sh/tools/cmdfound), 330 invocaciones por corrida del bloque
  +-----------------------------------------------------------------------------------+
  | awk  tr  sort  head  cat  find  du  rm rmdir mkdir mv cp ln chmod  readlink        |
  | mktemp  date  sleep  expr  wc  kill  curl|wget  sha256sum|shasum|openssl           |
  | tar  unzip  (para desempacar el artefacto)                                         |
  +-----------------------------------------------------------------------------------+
         |                                       |                       |
         v                                       v                       v
  canales artifact                          catalogo               runtimes
  +--------------------------+       +----------------+   +--------------------------+
  | aqua      sed(1) tr awk  |       | alpine         |   | docker   docker CLI      |
  | github    awk grep       |       |  tar -xzOf     |   | udocker  python3 id du   |
  | am        bash env head  |       |  grep -F sha.. |   |          find -perm 000  |
  | binstall  gzip tar tee   |       |  uname -m      |   +--------------------------+
  |           grep -F getconf|       +----------------+                |
  | conda-forge ls -A comm   |                                         v
  | pkgx      tar -xJf xz    |                          confined-launch (source)
  | nix-portable sqlite3 git |                          +--------------------------+
  |           comm sed grep  |                          | id -u/-g/-G (solo si no  |
  |           bwrap proot nix|                          |   hay /proc/self/status) |
  +--------------------------+                          +--------------------------+
         |
         v
  launchers, uno por programa, corren en CADA corrida
  +-----------------------------------------------------------------------------------+
  | docker:   . confined-launch ; docker image inspect ; exec docker run              |
  | udocker:  . confined-launch ; readlink ; python3 -E -s maincmd.py ; find rmdir    |
  | nix-portable: _namespaces (solo builtins) ; bwrap | proot ; readlink ; env        |
  | pkgx:     exec pkgx                                                               |
  | conda-forge: exec micromamba run ... /bin/sh -c ...   (o exec directo del bin)    |
  | am:       no es script, es un ln -s al programa                                   |
  +-----------------------------------------------------------------------------------+
```
*Las tres capas de dependencias y qué programa entra en cada una. Las 330 invocaciones son la cifra
medida en `~/cmdfound-test-cost.md`, no una medición de este documento.*

### 1.3 Lo que necesita cmdfound: tabla por programa

`req.` dice qué pasa si falta: **duro** = no hay salida, **needs=** = cmdfound se lo consigue por sus
propios canales, **blando** = el camino se descarta y sigue otro, **fallback** = hay alternativa.
`test` dice si el bloque lo ejercita de verdad (**real**) o a través de un stand-in (**stand-in**).

| programa | desde dónde | banderas y forma de la salida en que se confía | POSIX? | req. | test |
|---|---|---|---|---|---|
| `awk` | core (64 usos) y los 11 canales | `-F=`, `-F'\t'`, `-v`, `ENVIRON[]`, `getline < f`, `close()`, `match/RSTART/RLENGTH`, `SUBSEP`, `split("",a)`, `RS="\""`, `sprintf("%c",n)` para UTF-8, `printf("%010d%014d")`, `!seen[$0]++` | todo POSIX salvo lo que se dice en 1.5 | duro | real, **con un solo awk**: el bloque nunca nombra `gawk`, `mawk` ni busybox awk |
| `sed` | `aqua:455`, `nix-portable:449` y `:845` | `sed -n '/re/,/re/p'` (POSIX); `s/\x1b\[[0-9;]*m//g` (**GNU/busybox**); `s|^export PATH="||` (POSIX) | `\x1b` no es POSIX | blando | `aqua:455` real sólo en el camino de error; `nix-portable:449` real |
| `tr` | core:1115,1760,2931 y 10 canales | `tr -d '\r'`, `tr ',' '\n'`, `tr 'A-Z' 'a-z'` escrito como dos cadenas enteras | POSIX | duro | real |
| `grep` | `alpine:657,798`, `binstall:388,743,981,994`, `conda-forge:488,829`, `github:161`, `nix-portable:844` | `-F -q -e X -e Y`, `-Fx --`, `-E`, `-a -m1 -o` (`-a`,`-m`,`-o` **GNU+BSD+busybox, no POSIX**), BRE `\{32\}` | `-q`,`-F`,`-E` sí; `-x` sí; `-a -m -o` no | duro | real |
| `sort` | core:1494,1947,2109 y 9 canales | `LC_ALL=C sort`, `-u`, `-r`. **Ni `-V` ni `-h` en ninguna parte** | POSIX | duro | real |
| `comm` | `conda-forge` collect, `nix-portable:857` | `comm -12`, `comm -23` | POSIX | blando | stand-in (el nix del otro lado es `fake-nix-portable`) |
| `head` | core:1587,2334,2688; `am:156,158,160,377`; `binstall:644`; `conda-forge:365` | `head -1`, `head -20`, forma obsolescente `-NUM` | obsolescente en POSIX, aceptada por GNU/busybox/BSD | duro | real |
| `cat` | core:78,1337; 10 canales | sin banderas | POSIX | duro | real |
| `tee` | `binstall:974` | `tee "${log}"`, sólo con terminal | POSIX | blando | stand-in (`fake-cargo-binstall`) |
| `wc` | `wc -c < f \| awk '{print $1}'` en core:1660,1731 y 9 canales | `-c`; el `awk` está ahí porque BSD `wc` alinea con espacios | POSIX | duro | real |
| `cp` `mv` `rm` `rmdir` `mkdir` `ln` `chmod` | por todas partes | `mkdir -p`, `rm -rf`, `rm -f`, `mv -f`, `ln -s` (también `ln -s a b dir/`), `chmod 755`, `chmod 600`, `chmod -R u+w`, `cp` simple. **`cp -a` y `ln -T` no aparecen** | POSIX | duro | real |
| `ls` | `conda-forge:857` | `ls -A "${d}"` para ver si un directorio tiene algo | **`-A` no es POSIX** (GNU/BSD/busybox sí) | blando | real |
| `readlink` | core:345,1701,1747,1952,2132; docker, udocker, nix-portable, am | `readlink f`, **sin `-f`**: el seguimiento de enlaces se hace a mano, con tope de 16 saltos | `readlink` entró en POSIX 2024; sin `-f` es el uso portable | duro | real |
| `find` | core:1587,1591,1947,2109,2199,2248,2416; 8 canales | `-type f/d/l`, `-name`, `-perm -u+x`, `-perm 000`, `! -perm -u+w`, `-mmin -1440`, `-mtime +7`/`+0`, `-path ... -prune -o`, `-exec cat {} +`, `-exec chmod u+w {} +`, `-exec rmdir {} +`, **`-lname`**. Sin `-maxdepth`, sin `-printf` | `-mmin` y `-lname` no son POSIX; `{} +` sí (2008); `-perm -u+x` simbólico sí | duro | real, salvo `-lname` |
| `du` | core:1820, `conda-forge`, `nix-portable:861`, `udocker:930,947` | `du -sk` y se lee `<kb>TAB<path>`. **Ni `-b` ni `--apparent-size`** | POSIX | blando (si falla, "freed an unknown amount") | real |
| `mktemp` | core:3390 | `mktemp -d "${TMPDIR:-/tmp}/cmdfound-eph.$$.XXXXXX"` | POSIX 2024; template de 6 X, aceptado en los tres | blando (`--ephemeral`) | real |
| `date` | core:642,644,1684,1742,3300; docker:88; udocker:552; binstall:480 | `date +%s` (universal, no POSIX), `date +%s%N` (**GNU**), `date +%Y-%m-%dT%H:%M:%S` (POSIX). **Ni `-d` ni `-r`** | `%s` y `%N` no están en POSIX | duro | real |
| `sleep` | core:1407 | `sleep 0.1 2>/dev/null \|\| sleep 1` — el fraccionario tiene respaldo explícito | fraccionario no POSIX, con fallback | duro | real |
| `expr` | core:3353 | `expr "${0}" : '.*/\([^/]*\)'`, con fallback si sale vacío | POSIX | duro | real |
| `id` | `confined-launch:365-366`, `udocker:382,776,879,929` | `id -u`, `id -g`, `id -G`; en confined-launch **sólo si `/proc/self/status` no se puede leer** | POSIX (`-G` no lo es; GNU/BSD/busybox sí) | duro donde se usa | `id -u` real; **el fallback de `confined-launch` nunca se prueba**: el bloque siempre le pasa `CL_STATUS` |
| `uname` | `alpine:113`, `am:57`, `binstall:215`, `conda-forge:97`, `github:193`, `nix-portable:97`, `pkgx:50` | `uname -m`, `uname -s` | POSIX | duro | **stand-in**: `tools.db:56` pone un `hostbin/uname` que siempre contesta `x86_64`/`Linux` |
| `env` | `am:190`, `conda-forge`(no), `nix-portable:281` y su launcher | `env NAME=v ... prog` | POSIX | duro donde se usa | real |
| `getconf` | `binstall:233` | `getconf GNU_LIBC_VERSION >/dev/null` — sólo el estado, no la salida | POSIX (la variable no) | blando, y su ausencia es la respuesta correcta | stand-in (`biplat2/getconf` es un enlace al `uname` falso) |
| `kill` | core:393,1332,1382-1384; docker:266; nix-portable:370 | `kill -0 pid`, `kill pid` | POSIX, y builtin en dash/bash/ash | duro | real |
| `tar` | core:1572-1575; `alpine:604`; `binstall:388,403`; `nix-portable:194,388,570`; `pkgx:547` | `-xzf -C`, `-xJf -C`, `-xjf -C`, `-xf -C`, `-xzOf f MEMBER`, `-tJf`, `-xOf - MEMBER`, `--occurrence=1` (**GNU**, y se comprueba con `tar --version \| grep 'GNU tar'`), `TAR_OPTIONS=`/`GZIP=` vaciados | `tar` no está en POSIX (es `pax`); `-O` y `-J` los tienen los tres | duro | real |
| `gzip` | `binstall:402` | `gzip -dc` en un pipe | universal | blando | real |
| `unzip` | core:1576-1577 | `command -v unzip \|\| return 1` y luego `unzip -qq -o f -d d` | no POSIX, con guarda | blando | real |
| `xz` | indirecto: `tar -J`; `pkgx:557` lo comprueba con `command -v xz` | ninguna bandera propia | no POSIX | blando en pkgx, **no comprobado en nix-portable** | real (hay `tar -cJf` en las fixtures) |
| `sha256sum` / `shasum` / `openssl` | core:309-317; `alpine:396-404` | `sha256sum f` → `$1`; `shasum -a 256 f` → `$1`; `openssl dgst -sha256 f` → `$NF` (`SHA256(f)= hex`). Cadena de tres con `command -v` | ninguno es POSIX; la cadena es la portabilidad | duro (uno de los tres) | **sólo `sha256sum`**: las otras dos ramas no se ejecutan nunca |
| `curl` | core:90-91; los 9 canales que bajan algo | `-q` **primero** (el único lugar donde curl lo obedece), `-fsSL`, `-o`, `-sSL -w '%{http_code}'`, `-sSI`/`-sSIL` para HEAD, `-C -` para reanudar, `-D f` para headers, `-K -` para leer la config de stdin (el token), `-H`, `-r 0-1023` | no POSIX | duro (uno de curl/wget) | **stand-in** (`fake-web`), salvo dos líneas guardadas con `command -v curl` |
| `wget` | core:92-94; los mismos canales | `--no-config`, `--no-hsts`, `-q`, `-O f`, `-O-`, `-S`, `--spider`, `-c`, `--max-redirect=0`, `--header=K: V`; se lee `wget --help` y se ramifica por `*BusyBox*` / `*hsts*`; se leen los headers de `-S` y **el estado 8** | no POSIX | duro (uno de curl/wget) | **stand-in**, con las tres variantes simuladas |
| `sqlite3` | `nix-portable:566` | `sqlite3 -batch -init /dev/null -noheader -separator TAB db 'SELECT ...'` | no POSIX | **needs=sqlite3** en `nix-portable` meta | stand-in (`fake-sqlite3`) |
| `python3` | `udocker:348,654` y el launcher | `python3 -E -s "${tool}"` | no POSIX | **needs=python3** en `udocker` meta | stand-in (`fake-python3`) |
| `bash` | `am:282` | `command -v bash \|\| exit 1` — AM es un script de bash | no POSIX | duro para el canal `am`; sin bash el canal contesta "no" a todo | real (el bloque no lo quita) |
| `git` | `nix-portable:277` | `command -v git` y se le pasa en `NP_GIT`; si no hay, nix-portable se baja 22 MB de git | no POSIX | blando | stand-in (`hostbin/git` es `exit 0`) |
| `docker` | `docker` (52 usos) y su launcher | `context inspect --format`, `info --format '{{json .SecurityOptions}}'`, `ps -a --no-trunc --filter --format`, `image inspect --format '{{.Id}}'`/`'{{.Size}} {{.Parent}}'`, `image ls -a`, `pull`, `create --name --label --network=host --pull=never --user=0:0 --entrypoint ""`, `cp`, `start -a`, `wait`, `commit --change`, `rm`, `rm -f`, `rmi`, `run --rm -i --init --log-driver=none --network=host --pull=never` | — | blando (el canal se descarta con `unreachable=`) | **stand-in** (`fake-docker`, con `DOCKER_HOST` apuntando a un socket falso) |
| `nix` `nix-store` `bwrap` `proot` | `nix-portable` y su launcher | `nix eval --read-only --max-jobs 0 --raw`, `nix build --out-link`, `nix path-info --recursive --size`, `nix-store --gc --print-dead`, `nix-store --delete`; `bwrap --die-with-parent --bind ... --dev-bind`; `proot -r -b -w` | — | blando | stand-in (`fake-nix-portable`) |
| `aqua` `micromamba` `cargo-binstall` `pkgx` `udocker` `appman` | su canal | cada uno con su propio conjunto; cmdfound los trae y los mantiene al día | — | los trae cmdfound | stand-in (`fake-*`) |

### 1.4 Las construcciones que difieren, una por una

La lista que pediste, contestada. "usa" quiere decir que aparece en `sh/tools`; "sólo tests" que
aparece únicamente en el bloque o en `tools.sh`.

| construcción | ¿se usa? | veredicto |
|---|---|---|
| `sed -i` | **no** | nunca se edita un archivo en sitio |
| `sed -E` / `-r` | **no** | todo BRE |
| direccionamiento GNU vs BSD en `sed` | usa `sed -n '/^_namespaces() {$/,/^}$/p'` | rango de dos direcciones, POSIX en los tres |
| `sed 's/\x1b.../'` | usa, `aqua:455` | **GNU y busybox sí** (verificado en ambos); BSD `sed` no conoce `\xHH` y casaría la literal `x1b` (inferido) |
| dialecto de `awk` | usa todo lo de 1.3 | gawk, mawk y busybox awk verificados; **busybox awk rompe `%d` sobre 2^31** (ver Parte 3); BWK awk de macOS inferido |
| `mktemp` templates y banderas | usa `mktemp -d PREFIX.XXXXXX` | 6 X, forma portable; verificado en busybox |
| `stat -c` / `stat -f` | **no** | no hay un solo `stat` en el árbol |
| `readlink -f` | **no** | seguimiento a mano; es la decisión correcta |
| `du -b` / `--apparent-size` | **no** | sólo `du -sk`, que es POSIX |
| `du -k` | usa, `du -sk` | POSIX |
| `sort -V` / `-h` | **no** | el orden de versiones lo hace `awk` (`pkgx:_newest`, `udocker:_version_ge`, `binstall:_versions`) |
| `grep -P` | **no** | ninguno |
| `grep -q` | usa, `alpine:657` | POSIX |
| `grep -x` | usa, `-Fx` en `alpine:798`, `binstall:994`, `conda-forge:829` | POSIX |
| `date -d` / `-r` | **no** | ninguno |
| `date +%s%N` | usa, tres veces | **GNU**; el guard existe pero no cubre busybox (Parte 3, #3) |
| `head -c` / `tail -c` / `cut -b` | **no** | ninguno |
| `head -NUM` | usa `head -1`, `head -20` | obsolescente en POSIX, los tres lo aceptan (verificado en busybox) |
| `od` | **no** | ninguno |
| `xargs -r` | **no** | se usa `-exec ... {} +`, que es POSIX y no necesita `-r` |
| `ln -T` | **no** | ninguno |
| `cp -a` | **no** | `cp` simple; `cp -R` sólo en el bloque |
| `find -maxdepth` | **sólo tests** (8 usos, `-mindepth 1 -maxdepth 1`) | `tools.sh:18` dice explícitamente que `-maxdepth` no es POSIX y lo evita; el bloque no |
| `find -printf` | **no** | ninguno |
| `find -lname` | usa, `cmdfound:2248`, **una vez** | **GNU**. Verificado ausente en busybox 1.37.0; BSD `find` tampoco lo tiene (inferido). Consecuencia en Parte 3, #5 |
| `tar --occurrence` | usa, `binstall:388`, **con guarda** `tar --version \| grep 'GNU tar'` | GNU; la guarda está bien puesta |
| `tar --strip-components` | **no** | ninguno |
| `sha256sum` vs `shasum -a 256` vs `openssl dgst` | usa las tres, en cadena | la cadena es correcta; sólo la primera se ejecuta en CI |
| `kill -0` | usa, 6 veces | POSIX, y builtin |
| `unshare` | **no** | el aislamiento lo dan `bwrap`/`proot`, que trae nix-portable |
| `nproc` | **no** | el paralelismo de pkgx es `_batch`, fijo en 16 |
| `getent` | **no** | los nombres de uid/gid los resuelve el contenedor con `-v /etc/passwd:/etc/passwd:ro` |
| `id -u` | usa | POSIX; `id -G` no lo es |
| `python3` | usa, `needs=python3` | lo consigue cmdfound |
| `sqlite3` | usa, `needs=sqlite3` | lo consigue cmdfound |
| `curl` | usa | ver 1.3 |
| `wget` | usa | ver 1.3; tres variantes, y es donde está casi todo lo roto |
| `busybox wget` | **es la variante crítica** | verificado dentro de `alpine:3.22`: tiene `-c -q -S --spider -O -o --header --post-data -Y -P -U -T` y **nada más** |

### 1.5 Detalles de `awk` que hay que tener presentes

No son banderas, son diferencias de implementación que el código ya ejercita:

- **`sprintf("%c", n)` para armar UTF-8** (`alpine:83-88`, `conda-forge`, `udocker:114-119`). Va
  dentro de `LC_ALL=C awk`, que es lo que lo hace correcto. Verificado byte a byte idéntico en gawk,
  mawk y busybox awk: `226 151 134` → `e2 97 86`.
- **`printf("%010d%014d")` con centinelas de 10 y 14 dígitos** (`cmdfound:1095`). gawk y mawk lo
  hacen con 64 bits; **busybox awk satura en `INT32`**. Verificado: `2147483648` → `-2147483648`.
  Es la única línea de todo el árbol que construye una clave de orden con `awk` en vez de con el
  `printf` de la shell, y por eso es la única que se rompe.
- **`\047` octal dentro de una expresión regular** (`binstall:420`). Verificado en gawk, mawk y
  busybox awk: los tres lo aceptan.
- **`ENVIRON[]`, `getline < f`, `close(f)`, `split("", arr)`, `RS="\""`**: verificados en busybox awk.
- **`substr(s, 0, n)`**: gawk devuelve un carácter menos que busybox awk. Sólo aparece en
  `tools.sh:51`, que alinea el nombre del test. Cosmético.
- El comentario de `alpine:636` ("mawk makes `c[$3]` before it asks whether `c` has it") y el de
  `aqua:178` ("byte for byte the same under gawk, mawk, nawk and busybox") son afirmaciones sobre
  dialectos que **nada en el repositorio comprueba**: el bloque corre con el `awk` que haya.

### 1.6 Lo que necesita sólo el bloque de tests

Aterrizan en otro sitio de CI: son dependencias del runner, no del programa.

| programa | dónde | para qué | POSIX? |
|---|---|---|---|
| `sha256sum` | 22 usos en el bloque | firmar las fixtures y comparar con lo que el canal publica | no POSIX; **macOS no lo tiene con ningún nombre en `/bin` ni `/usr/bin`** |
| `tar -cf/-czf/-cjf/-cJf` | 39 usos | armar APKINDEX de dos flujos gzip, pantries, crates, sdists, `.conda` | `-J` necesita `xz` |
| `xz` `gzip` `bzip2` | fixtures | los tres formatos que cmdfound desempaca | no POSIX |
| `unzip` | fixture zip | el zip se escribe con `printf '\120\113\003\004...'`, byte a byte, sin `zip` | — |
| `dd` | `cmdblock:79` | `dd if=sig.tar bs=512 count=2` para cortar el flujo de firma del APKINDEX | POSIX |
| `mkfifo` | `tools.sh:23` | el diff de "herramientas sin test" | POSIX |
| `basename` | `tools.sh:19` | listar las herramientas | POSIX |
| `cmp` | `cmdblock:2202,2212` | que el índice por red y el índice local salgan idénticos | POSIX |
| `seq` | `cmdblock:2536` | 200 argumentos para medir el coste de las banderas | no POSIX (GNU/BSD/busybox sí) |
| `cut` | `cmdblock:2792` | `cut -f1` de un registro de docker | POSIX |
| `tail` `uniq` `touch` | varios | `tail -1`/`-3`, `uniq`, `touch -t 200001010000` | POSIX |
| `setsid` | 9 usos, **todos guardados** con `! command -v setsid` | probar el camino sin terminal de control | util-linux; busybox lo tiene, macOS no |
| `python3` o `perl` | `cmdblock:2073`, con `\|\| :` | crear un socket unix para los tests de `confined-launch` | con guarda |
| `id` | `cmdblock:26,2385,2675` | el home real y los uid que el launcher debe escribir | POSIX |
| `find -mindepth/-maxdepth` | 8 usos | que un canal no escriba fuera de su directorio | **no POSIX** |
| `sh` | `tools.sh:61` | `sh -x run.sh`: **el `/bin/sh` del sistema es el eje** | — |
| `test -nt` | `cmdblock:29,31` | el guard que vigila el home real | no POSIX, pero está en dash, bash y ash |

Y la línea que más pesa para la matriz, `tools.sh:52`:

```sh
printf "%s\\n" "PATH=../${tools}:/bin:/usr/bin" > run.sh
```

El bloque corre con un `PATH` de **`/bin:/usr/bin` y nada más**. En Linux eso está bien. En macOS
deja fuera `/usr/local/bin` y `/opt/homebrew/bin`, que es donde viven `xz`, `docker` y cualquier
coreutils de GNU que se haya instalado; y `sha256sum` no está en ninguna parte de macOS.

### 1.7 Qué pasa cuando falta: `needs=`, o no

```
   falta el programa
        |
        +-- lo declara un canal en needs=  -->  cmdfound lo resuelve por sus canales,
        |     (sqlite3 en nix-portable,          lo enlaza en <canal>/needs/ y lo pone
        |      python3 en udocker)               primero en el PATH de ese canal
        |
        +-- hay cadena de alternativas     -->  sha256sum | shasum -a 256 | openssl dgst
        |                                       curl | wget
        |                                       sleep 0.1 | sleep 1
        |                                       date +%s%N | date +%s
        |
        +-- el canal se descarta           -->  bash (am), docker (docker), unzip (zip),
        |                                       xz (pkgx), getconf (binstall), git (np)
        |
        +-- no hay salida                  -->  awk tr grep sort head cat wc cp mv rm
                                                rmdir mkdir ln chmod readlink find du
                                                mktemp date expr id uname env tar
```
*Los cuatro destinos posibles de un programa que no está, y quién va a cada uno.*

Los únicos dos `needs=` del árbol son `nix-portable` → `sqlite3` y `udocker` → `python3`. Todo lo
demás de la última fila es requisito duro y sin aviso: si falta `awk`, cmdfound no dice nada
inteligible, simplemente no resuelve.

### 1.8 Lo que el bloque mide de verdad y lo que mide contra un stand-in

Esta es la columna que te interesa, porque es donde se esconden los agujeros como el de `aqua`.

```
   real (programas de esta maquina)          stand-in (sh/tests/cmdfound.d/)
   +-----------------------------+           +-----------------------------------------+
   | awk sed tr grep sort head   |           | curl, wget  -> fake-web                 |
   | cat wc cp mv rm rmdir mkdir |           | uname       -> hostbin/uname (x86_64)   |
   | ln chmod ls readlink find   |           | sqlite3     -> hostbin + fake-sqlite3   |
   | du mktemp date sleep expr   |           | git         -> hostbin/git (exit 0)     |
   | kill tar gzip unzip xz      |           | docker      -> fake-docker + socket      |
   | sha256sum  id -u  bash      |           | python3     -> fake-python3             |
   | comm(*) tee(*)              |           | aqua micromamba cargo-binstall pkgx     |
   +-----------------------------+           | nix-portable udocker appman -> fake-*   |
   (*) se llaman, pero el programa            | getconf     -> enlace al uname falso    |
       del otro lado es un stand-in           +-----------------------------------------+
```
*Qué programa del sistema se ejercita de verdad y qué se sustituye.*

Los tres agujeros de `fake-web`, que son de la misma familia que el que ya encontraste:

| línea de `fake-web` | lo que hace el stand-in | lo que hace el programa real |
|---|---|---|
| 114 | imprime `Location: <url>` y nada más | GNU wget imprime **dos** líneas `Location:`, y la última con ` [following]` (**verificado**, wget 1.21.4) |
| 93 | acepta `--max-redirect=0` incluso con `FAKE_WEB_BUSYBOX=1` | busybox wget **no tiene `--max-redirect`**: sale 1 con `unrecognized option` (**verificado**, busybox 1.37.0) |
| 134 | `exit 8` para cualquier cosa que no sea 200, también en modo busybox | busybox wget sale **1** en 404, 403 y 500; el 8 es de GNU (**verificado en los dos**) |

---

## 2. La matriz

### 2.1 Los ejes, y cuál de ellos se derrumba

```
   /bin/sh        coreutils      awk            libc         fetcher
   +--------+     +--------+     +--------+     +-------+    +------------------+
   | dash   |     | GNU    |     | gawk   |     | glibc |    | curl + wget      |
   | bash 5 |  x  | busybox |  x | mawk   |  x  | musl  | x  | curl solo        |
   | ash    |     | BSD    |     | bb awk |     +-------+    | wget GNU solo    |
   | bash3.2|     +--------+     | BWK    |                  | busybox wget solo|
   +--------+                    +--------+                  | ninguno          |
                                                             +------------------+
```
*Los cinco ejes del enunciado. El producto completo son 4x3x4x2x5 = 480 celdas.*

No hacen falta 480 corridas, ni 10, porque **tres de los ejes no son independientes**:

- **libc se derrumba a una línea.** cmdfound es shell puro: no compila nada y no enlaza nada. La
  única línea de todo el árbol cuyo comportamiento depende de la libc es `binstall:233`,
  `getconf GNU_LIBC_VERSION`, que decide si se añade el target `-unknown-linux-gnu` a la lista.
  Verificado en Alpine: `getconf: GNU_LIBC_VERSION: unknown variable`, estado 1, que es exactamente
  la respuesta que se quiere. musl no aporta un eje: aporta esa línea, y viene de regalo con Alpine.
- **coreutils y awk viajan juntos** en la práctica: busybox trae los dos, y BSD trae los dos. Los
  únicos cruces que existen de verdad son GNU+gawk, GNU+mawk, busybox+bb awk y BSD+BWK.
- **el fetcher no es una distribución**, es un `PATH`. Se cambia con un enlace simbólico.

### 2.2 Los objetivos

Tres imágenes, ocho corridas. Cada línea dice qué implementación existe sólo ahí.

| # | objetivo | qué variantes ejercita | qué quedaría sin probar sin él |
|---|---|---|---|
| 1 | `ubuntu-24.04`, tal como viene | `sh`=dash, GNU coreutils/sed/grep/find/tar, `awk`=gawk, glibc, curl y wget presentes | el caso base, y **el único sitio donde aparece el ` [following]` real de GNU wget y el estado 8 real** |
| 2 | `ubuntu-24.04`, `awk` → `mawk` (un enlace en un directorio delante del `PATH`) | el dialecto mawk | los tres comentarios del árbol que afirman "igual bajo gawk y mawk" y que nada comprueba |
| 3 | `ubuntu-24.04`, `sh` → `bash` (un shim en el `PATH` que `tools.sh:61` recoge) | bash como `/bin/sh` **sin** userland BSD | si algo se rompe en bash, distinguirlo de un fallo de BSD; y la rama `declare -x` de `confined-launch:447` |
| 4 | `ubuntu-24.04`, `PATH` sin `curl`; y otra sin `curl` ni `wget` | GNU wget solo, y ningún fetcher, **sobre el bloque entero** | hoy el bloque prueba el camino sin curl con un `PATH` armado a mano (`cmdblock:2155`) y sólo para unas pocas llamadas de canal, no para las 330 invocaciones del core |
| 5 | `alpine:3.22` en `container:` sobre el runner de ubuntu, con `apk add xz` | `sh`=busybox ash, busybox coreutils/sed/grep/find/tar/awk, musl, **busybox wget y sin curl** | `--max-redirect=0`, el estado 1 en vez de 8, `%d` de 32 bits en awk, `find -lname`, `date +%s%N` silencioso, `tar -J` sin `xz`, `shasum`/`openssl` ausentes, `getconf GNU_LIBC_VERSION` ausente. **Es el objetivo que más encuentra** |
| 6 | `alpine:3.22` + `apk add curl` | musl y busybox **con** curl | separar "lo rompió musl/busybox" de "lo rompió el wget de busybox". Sin esta corrida, cada fallo de #5 tiene dos culpables posibles |
| 7 | `macos-14` (arm64) | BSD sed/grep/find/tar(libarchive)/du/comm/ls, BWK awk, bash 3.2 como `/bin/sh`, sin `/proc`, sin `sha256sum` | lo que se detalla abajo |
| 8 | `macos-14`, `PATH` sin `curl` | BSD + wget de Homebrew | el cruce BSD × wget, que es donde el bug de `aqua` y el `\x1b` de `sed` se juntan |

**Qué está macOS para atrapar, exactamente.** No "porque BSD". Estos ítems del inventario:

1. `cmdfound:311-312`, la rama `shasum -a 256` de `_digest`. macOS no tiene `sha256sum` y sí tiene
   `shasum`: es el único objetivo donde esa rama se ejecuta.
2. `cmdfound:642-646`, `date +%s%N`. BSD `date` imprime los dígitos seguidos de una `N` literal, y
   es el único objetivo donde el guard `''|*[!0-9]*` hace lo que se escribió que hiciera.
3. `confined-launch:365-366`, el fallback `id -u`/`id -g`/`id -G`. Sin `/proc/self/status`, es el
   único camino; hoy no se prueba en ninguna parte.
4. `cmdfound:2248`, `find -type l -lname`. BSD `find` no lo tiene (inferido), con la consecuencia de
   la Parte 3, #5.
5. `aqua:455`, `sed 's/\x1b\[[0-9;]*m//g'`. BSD `sed` no conoce `\xHH` (inferido).
6. `alpine:604`, `tar -xzOf APKINDEX.tar.gz APKINDEX` sobre un tar de **dos flujos gzip
   concatenados**. GNU tar verificado aquí, busybox tar verificado en Alpine; bsdtar/libarchive es
   el tercer lector y no está probado.
7. `binstall:403`, `tar -xOf - MEMBER` desde un pipe, con `--occurrence=1` ausente por la guarda de
   GNU: bsdtar lee todo el archivo en vez de parar en el primer match. Cambia el coste, no el
   resultado.
8. `confined-launch:447`, `export -p`. bash 3.2 imprime `declare -x NAME="value"`; dash y ash
   imprimen `export NAME='value'`. Las dos ramas existen en el código y sólo una se ejecuta en CI.
9. `conda-forge:95-105` es el único `_subdir` que nombra `Darwin`: es el único canal que dice
   soportar macOS. Que los otros siete se comporten sensatamente ahí no se ha visto nunca.
10. `tools.sh:52`, el `PATH=/bin:/usr/bin` que en macOS no alcanza `/usr/local/bin`. Esto hay que
    arreglarlo **antes** de que macOS pueda arrancar el bloque.

### 2.3 Dónde una variante sale más barata como segundo eje

Cuatro de las ocho corridas no son imágenes nuevas, son un `PATH` o un enlace sobre una imagen que
ya está levantada:

| variante | cómo se hace en la imagen que ya hay | por qué no merece una distribución |
|---|---|---|
| `awk` = mawk / gawk | `ln -s $(command -v mawk) $d/awk; PATH=$d:$PATH` | la única diferencia que importa es el binario de awk; el resto de Debian y Ubuntu es idéntico, y sería una imagen de 200 MB para cambiar un enlace |
| `sh` = bash | un `sh` en un directorio delante del `PATH`; `tools.sh:61` lo recoge solo | una Fedora entera para cambiar `/bin/sh` cambia además el awk, el tar y el grep, y un fallo ya no dice quién lo causó |
| sin `curl` / sin `wget` / sin ninguno | un directorio con enlaces a lo que sí debe estar, como ya hace `cmdblock:2155` | no existe una distribución "sin curl": es una decisión de `PATH` |
| musl con curl vs sin curl | `apk add curl` en la misma imagen | `apk add` cuesta segundos; una segunda imagen no aporta nada |

Lo contrario también vale: **no** se puede simular busybox con enlaces sobre Ubuntu. `/bin/sh`,
`awk`, `find`, `sed`, `grep`, `tar` y `wget` tienen que ser los del mismo binario multi-call para
que los fallos de la Parte 3 aparezcan; y `date +%s%N`, que es el más traicionero, depende de la
libc del `date` que corre. Alpine es una imagen de verdad o no es nada.

### 2.4 Red y daemon

**El bloque no necesita red, y tampoco necesita daemon, ni para docker ni para udocker.**

Esto cambia lo que habíamos supuesto y hay que decirlo claro:

- `tools.db:57` escribe un `hostbin/docker` que es un shim a `sh/tests/cmdfound.d/fake-docker`, y
  `tools.db:58` pone `hostbin` primero en el `PATH` **para todo el bloque**. El comentario de
  `tools.db:52` lo dice: *"Its docker is fake-docker with no daemon to reach, so no resolution below
  asks this machine's docker anything, whether it has one or not"*.
- La sección de docker (`cmdblock:2591-2800`) corre con `DOCKER_HOST=unix://${dkroot}/docker.sock`,
  un socket que nunca se abre, y con un store de imágenes y contenedores en directorios.
- La sección de udocker corre con `fake-python3` ejecutando `fake-udocker`.
- Los catálogos salen de directorios (`CMDFOUND_ALPINE_MIRROR`, `CMDFOUND_PKGX_DIST`,
  `CMDFOUND_AM_REPO`, ...) y los fetchers son `fake-web` sirviendo un árbol de archivos.

O sea: **las ocho corridas se pueden ejecutar en cualquier runner, sin red y sin daemon.** Lo único
que necesita un daemon es el propio `container: alpine:3.22` de las corridas #5 y #6, y eso lo
provee el runner de GitHub sin que nadie tenga que pedirlo.

La contrapartida, que es un hallazgo y no un detalle: **ninguna corrida prueba docker de verdad**.
Que `docker run --network=host` no exista en Docker Desktop de macOS, o que
`-v /etc/passwd:/etc/passwd:ro` no tenga sentido ahí, no lo va a encontrar esta matriz. Eso es otro
trabajo, con su propio coste, y no es el que pediste.

### 2.5 Qué corre `act` y qué no

```
  act (local, contra el daemon de esta maquina)
  +-------------------------------------------------------------+
  | #1 ubuntu tal cual        | #2 awk=mawk   | #3 sh=bash       |
  | #4 sin curl / sin ninguno | #5 alpine     | #6 alpine+curl   |
  +-------------------------------------------------------------+
  fuera del alcance de act
  +-------------------------------------------------------------+
  | #7 macos-14               | #8 macos-14 sin curl            |
  +-------------------------------------------------------------+
```
*Seis de las ocho corridas son locales; las dos de macOS sólo existen en GitHub.*

- **Corren con `act`**: #1 a #6. Todas son `runs-on: ubuntu-*`, y #5 y #6 son un `container:`, que
  `act` soporta directamente. Con `-P ubuntu-24.04=catthehacker/ubuntu:act-24.04` la imagen por
  defecto ya trae dash, gawk, mawk, curl, wget, tar, xz y perl; hay que comprobar `sqlite3` no, el
  bloque lo sustituye.
- **No corren con `act`**: #7 y #8. `act` no tiene runners de macOS y no los puede emular; el
  userland BSD no se simula. Esas dos corridas sólo se ven en GitHub, y por eso son las que más
  conviene poner en un job aparte que no bloquee: fallan por cosas que nadie puede reproducir en su
  máquina.
- Aviso para `act`: necesita un daemon de Docker **fuera** para arrancar el contenedor del job, y
  este repositorio comparte el daemon con otras sesiones. Un `act` que levanta seis jobs a la vez
  son seis contenedores en ese daemon.

---

## 3. Lo que ya está roto

Del análisis estático y de lo verificado. No se arregló nada; esta es la lista para que decidas.
El orden es por probabilidad de morder, no por gravedad.

### #1 — Cuatro canales se quedan sin "cuál es la última versión" con el wget de busybox

`aqua:113`, `binstall:651`, `conda-forge:370`, `nix-portable:200`

Las cuatro pasan `--max-redirect=0`. **Verificado en busybox 1.37.0**: la opción no existe, y wget
sale 1 con `wget: unrecognized option: max-redirect=0` sin imprimir nada. Los cuatro `awk` que leen
la salida reciben una cadena vacía y los cuatro canales contestan que no pudieron preguntar:

- `aqua`: `unreachable=the tag of the newest aqua catalog could not be read from github.com`
- `conda-forge`: `unreachable=the newest micromamba release could not be read from ...`
- `binstall`: `unreachable=the newest cargo-binstall release could not be read from ...`
- `nix-portable`: `unreachable=which release ... is at could not be read`

En una máquina Alpine sin curl, **cuatro de los ocho canales están muertos**, y los cuatro culpan a
github.com de un problema que está en la línea de comandos. `_wget_options` ya sabe que ese wget es
de busybox (`case "$(wget --help 2>&1)" in *BusyBox*)`), y esa información no llega a la línea que
la necesita. Lo esconde `fake-web:93`, que acepta la opción también en modo busybox.

### #2 — Con el wget de busybox, "no existe" se convierte en "no se pudo preguntar"

`alpine:161`, `alpine:221`, `am:117`, `aqua:161`, `binstall:156`, `conda-forge:151`,
`conda-forge:192`, `nix-portable:155`, `pkgx:99`, `pkgx:135`, `udocker:231` — once sitios, el mismo
`case`:

```sh
case "${?}" in
    0) return 0 ;;
    8) rm -f "${2}"; return 1 ;;
esac
return 2
```

**Verificado contra un servidor local**: GNU wget 1.21.4 sale **8** en 404, 403 y 500; busybox wget
sale **1** en los tres. El 1 no casa con nada y cae en `return 2`, "could not be had". El core
entonces dice *"so whether anything provides 'x' is not known"* en vez de *"no channel provides
'x'"* — que es justo la mentira que los comentarios del propio `github` dicen que el diseño existe
para evitar (*"this channel was rate limited once and the user was told jq does not exist"*, al
revés). Lo esconde `fake-web:134`, que sale 8 también en modo busybox.

### #3 — En Alpine, cada medición de tiempo sale 0 ms, y el archivo de timings queda envenenado

`cmdfound:642-646`, y las copias en `docker:88-92` y `udocker:552-556`:

```sh
_nm__t="$(date +%s%N 2>/dev/null)"
case "${_nm__t}" in
    ''|*[!0-9]*) printf "%s\\n" "$(( $(date +%s) * 1000 ))" ;;
    *) printf "%s\\n" "$(( _nm__t / 1000000 ))" ;;
esac
```

El guard está escrito para BSD, que imprime una `N` literal. **Verificado en busybox**: `date
+%s%N` imprime `1789698281` — exactamente lo mismo que `date +%s`, con el `%N` descartado **en
silencio**. Diez dígitos, todos dígitos: pasa el guard, entra por la rama buena y se divide por
1,000,000, dando **1789 ms**. Dos llamadas seguidas dan el mismo 1789, y toda duración medida en
Alpine es 0.

No se cae nada: `_timing_add` acepta el 0, lo escribe en `<canal>/timings`, y `_est_us` ajusta sus
mínimos cuadrados sobre columnas de ceros. Cada pregunta futura dirá `<1 s` para cualquier tamaño, y
el archivo no se limpia nunca. Es el fallo más silencioso de la lista y el que peor se diagnostica
después.

### #4 — La clave de orden entre runtimes se desborda en busybox awk

`cmdfound:1095`:

```sh
_fo__key="$(awk -v r="${_fo__first}" -v t="${_fo__mk}" 'BEGIN {printf("%010d%014d", r, t)}')"
```

`_fo__rk` vale 9999999999 cuando no se sabe cuánto cuesta una corrida y `_fo__mk` vale
99999999999999 cuando no se sabe cuánto cuesta llegar — que es el caso común de la primera
resolución, porque el tamaño de la imagen viene vacío. **Verificado**: busybox awk convierte `%d`
con un `int` de 32 bits y ambos centinelas salen `-2147483648`. La clave queda
`1-2147483648-00021474836480<pos>`: deja de tener ancho fijo, empieza a llevar signos menos, y el
`LC_ALL=C sort` de `cmdfound:1494` ordena docker y udocker de forma arbitraria. gawk y mawk
verificados correctos.

Es la única clave del árbol que se arma con `awk`; `_probe_emit:945` usa el `printf` de la shell,
que en busybox da `00000000000123` bien (verificado).

### #5 — Un purge en Alpine borra una entrada del store que otra colocación todavía usa

`cmdfound:2248`:

```sh
if find "${_purge__sh}/by" -type l -lname "${_purge__dir}" 2>/dev/null | \
   awk 'NF{n++} END{exit !(n+0)}'; then
```

`-lname` es de GNU. **Verificado ausente en busybox** (`find: unrecognized: -lname`); BSD `find`
tampoco lo tiene (inferido, hay que comprobarlo en macOS). El `2>/dev/null` se come el error, `find`
no imprime nada, el `awk` contesta "nadie apunta aquí", y el directorio del store entra en
`_purge__doomed` y se va con el `rm -rf` de `cmdfound:2261`.

O sea: en Alpine, purgar una colocación borra el contenido compartido por todas las demás
colocaciones del mismo archivo, en silencio y sin una línea de aviso. Es el único de esta lista que
destruye datos. El comentario de arriba dice *"a store entry outlives the link that named it only
until nobody else points at it, which is what content addressing buys"*, y con busybox no compra
nada.

### #6 — `nix-portable` culpa al catálogo cuando lo que falta es `xz`

`nix-portable:194`, `:388`, `:570` usan `tar -tJf` y `tar -xJf`. **Verificado en Alpine**: busybox
tar lanza un `xz` externo que la imagen base no tiene (`tar: can't execute 'xz': No such file or
directory`, y `tar -tJf` da `short read`). El mensaje que sale de `:573` es:

```
unreachable=the catalog of <release> came without its programs.sqlite, and is not kept
```

que es falso: el catálogo llegó entero. `meta` declara `needs=sqlite3` y no declara `xz`, así que
cmdfound consigue el sqlite3 y no el xz. `pkgx:557` sí distingue este caso y dice *"which needs
xz"*; `nix-portable` no. `cmdfound:1573` (`tar -xJf` para el formato `tar.xz`) al menos dice *"could
not unpack the tar.xz artifact"*, que es cierto aunque no explique por qué.

### #7 — En macOS, el canal `github` entrega un binario de Linux

`github:286-320`. `_platform` mira sólo `uname -m`, y `usable()` decide:

```awk
if (lower ~ /(darwin|apple|macos|windows|freebsd|netbsd|openbsd|android)/) return 0
...
if (lower ~ /(linux|musl|gnu)/) return 1
```

No hay ni un `uname -s` en el canal. En macOS eso rechaza todos los assets de macOS y acepta los de
Linux: el canal contesta que sí, el core lo baja, lo verifica, lo coloca y `exec` falla. Inferido de
la lectura; no se pudo ejecutar.

### #8 — `am` y `udocker` se ofrecen en macOS

`am:56-64` (`_arch`) mira `uname -m` y no `uname -s`, así que en macOS arm64 contesta `aarch64` y el
canal ofrece AppImages, que no corren ahí. Lo único que a veces lo salva es el
`command -v bash \|\| exit 1` de `am:282`, y macOS trae bash.

`udocker` no tiene ninguna comprobación de sistema: sus motores (`proot`, `runc`, `patchelf`,
`fakechroot`) son de Linux. `conda-forge` es el único canal con `Darwin` en su tabla; `pkgx`,
`binstall` y `nix-portable` sí se cierran con `uname -s`, y hacen lo correcto. Inferido.

### #9 — El bloque de tests no arranca en macOS

`tools.sh:52` fija `PATH=../../tools/:/bin:/usr/bin`. En macOS:

- `sha256sum` no existe con ningún nombre (hay `shasum`), y el bloque lo usa 22 veces para firmar
  fixtures. Primera línea que falla.
- `xz` vive en `/usr/local/bin` o `/opt/homebrew/bin`, fuera del `PATH`: las fixtures `tar -cJf` de
  pkgx y nix-portable fallan.
- `setsid` no existe, pero eso ya está guardado con `! command -v setsid` en las nueve líneas que lo
  usan, así que no rompe.

Es lo primero que hay que tocar si macOS entra en la matriz, y es una línea.

### #10 — El mensaje de error de `aqua` se queda con los escapes ANSI en BSD

`aqua:455`, `sed 's/\x1b\[[0-9;]*m//g'`. **Verificado**: GNU sed 4.9 y busybox sed 1.37 lo entienden
los dos. BSD `sed` no conoce `\xHH` y casaría la literal `x1b` (inferido), así que el `failed=` de
aqua sale con los colores dentro. Cosmético, y va al final por eso.

### #11 — El desbordamiento de 32 bits de busybox awk también toca los estimados

`cmdfound:735` (`printf("%d\n", (fixed + per * b) * 1000)`) y `cmdfound:739`
(`printf("%d\n", b * 1000000 / s)`). **Verificado**: para 3 GB a 1 MB/s el segundo da
`-2147483648`, que `_is_number` rechaza por el signo, y la pregunta dice "time unknown". Degrada
bien, no corrompe nada. El primero se desborda a partir de unos 36 minutos estimados.

---

## Lo que se ejecutó para este documento

Todo lo marcado "verificado" sale de aquí. Nada de esto escribió en el repositorio.

| qué | cómo |
|---|---|
| inventario de implementaciones locales | `command -v` y `--version` de 35 programas |
| las dos líneas `Location:` de GNU wget | servidor HTTP local en `127.0.0.1:8732` que contesta 302, y `wget --no-config --no-hsts -S --spider --max-redirect=0`. Salida completa, con `cat -A` |
| los cuatro lectores de `Location:` | la salida real de wget pasada por los cuatro `awk` del árbol, uno por uno |
| estados de salida de wget en 404/403/500 | el mismo servidor, GNU wget y busybox wget contra `/nf`, `/403`, `/500`, `/x` |
| busybox: todo lo demás | **una** descarga de `alpine:3.22` de Docker Hub y dos `docker run --rm` (uno con `--network none`, uno con `--network host` para hablar con el servidor local). Un script de 90 comprobaciones: wget, awk, coreutils, find, tar, sed, grep y las construcciones de shell |
| `awk`: gawk vs mawk vs busybox awk | los mismos programas de una línea en los tres |
| GNU tar sobre un APKINDEX de dos flujos gzip | la fixture se reconstruyó tal como la arma `cmdblock:79`, con `dd` y `gzip -n` |
| `${!}`, `[![:space:]]`, `export -p`, `cd -P`, `-nt` | dash, bash y busybox ash |

La imagen `alpine:3.22` quedó en la caché del daemon compartido, junto a las `alpine:3`,
`alpine:3.20` y `alpine:latest` que ya estaban. No se borró: borrarla podría cruzarse con otra
sesión, y ocupa 8 MB.

Lo que **no** se ejecutó, y por qué: la suite completa (`cd sh/tests && sh tools.sh cmdfound`), que
cuesta 82-93 s por corrida según `~/cmdfound-test-cost.md` y que no hacía falta para nada de lo de
arriba; y cualquier cosa BSD o macOS, que no hay manera de correr aquí.
