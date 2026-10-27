# Qué cuesta bajar el bloque cmdfound (82-86 s), y qué se pierde

Base: `integrate/channels` en 9a278d6 (incluye los dos commits de tests y el arreglo de
`~/.wget-hsts`). Todos los diffs de este documento salen de los archivos tal como están en ese
commit, y ninguno está aplicado ni commiteado: son propuestas para que decidas.

Los diagramas ASCII van donde hacen falta y cada uno dice arriba qué muestra. Las líneas de los
diffs son tan largas como las del original, no las corté.

Antes de los números, tres advertencias sobre las mediciones:

- **La máquina no estuvo quieta.** Durante estas mediciones corrían dos `jekyll serve
  --force_polling`, otras sesiones de Claude y node. El load average se movió entre 0.3 y 6.9.
  El mismo bloque sin cambios midió 81.5 s con load 0.3-1.9 y 141 s con load 3.2-6.4.
- **Por eso el número estable no es el reloj sino la cantidad de procesos.** El bloque arranca
  61,683-61,790 procesos, y esa cifra se repitió en cuatro corridas con menos de 0.2% de
  diferencia. Cada proceso que se quita vale ~1.0-1.1 ms de reloj (medido: el prototipo de la
  opción 2 quitó 6,932 procesos y bajó el reloj entre 6 y 14 s según el load del momento).
- **Cuando digo "medido" es que corrí el bloque completo o el experimento. Cuando digo
  "estimado" es aritmética sobre algo medido, y lo digo en cada caso.**

Referencia de reloj que uso en todo el documento: **86 s**, que es la mediana de las corridas
del bloque sin cambios con load entre 1.5 y 2.6, en un namespace de PIDs propio. Con la máquina
quieta son 82 s; con otras sesiones pesadas, 93 s o más.

---

## 1. Dónde se van los 86 s

### 1.1 Procesos, no cálculo

| qué | cuánto | de dónde sale |
|---|---|---|
| líneas del bloque en `tools.db` | 2,716 (632-3349), 1,670 ejecutables | contado |
| procesos que arranca el bloque | 61,683-61,790 | medido, 4 corridas en namespace de PIDs |
| reloj | 82 s quieto / 86-93 s con carga | medido, 11 corridas |
| ms de reloj por proceso | 1.4-1.5 ms | 86 s / 61.7k procesos |
| invocaciones de `cmdfound` | 330 | medido con un tracer de ptrace |
| canales reales llamados directo por el bloque | 257 | medido con el mismo tracer |

El costo de un proceso en esta máquina (WSL2), medido en lazos de dash de 1,000-2,000 vueltas.
Estos son programas reales de la máquina, no stand-ins:

| construcción | ms cada una |
|---|---|
| `$(printf x)` (subshell, dash pequeño) | 0.38 |
| `$(printf x)` en un dash que ya cargó las funciones del core | 0.58 |
| `sh -c :` | 0.79-0.92 |
| `cat </dev/null` | 1.34 |
| `grep` / `sed` | 1.7-1.9 |
| `awk 'BEGIN{}'` (aquí awk es gawk) | 2.0-2.2 |
| `$(printf ... \| awk -F= ...)`, que son 3 procesos | 3.0-3.5 |
| arrancar el core hasta `-V` | 5.35 (de esos, ~4.5 es parsear los 150 KB) |

Con eso, los 86 s son casi enteramente fork+exec de programas chiquitos. Ninguna línea del
bloque cuesta más de 2 s: las 25 más caras suman 18.8 s (23%) y 1,039 líneas de menos de 10 ms
suman 2.6 s. Es muerte por mil cortaditas, no un cuello de botella.

### 1.2 Qué son `tiny`, `alpha` y los demás nombres de estas mediciones

Casi todo lo que sigue se midió contra **stand-ins**: archivos en `sh/tests/cmdfound.d` que
contestan el protocolo de un canal (`meta`, `probe`, `locate`, `obtain`, `collect`) con
respuestas inventadas y sin tocar la red. Para el resolver son canales de verdad -- ejecutables
en el directorio que `CMDFOUND_CHANNELS` nombra -- y por eso el costo que mido es el costo real
del core; lo que no es real es el trabajo del otro lado: no hay descarga, no hay daemon, no hay
nada que esperar. Los `fake-*` de ese mismo directorio no son canales (no son ejecutables): son
stand-ins de los programas que los canales arrancan (aqua, micromamba, pkgx, cargo-binstall,
udocker, docker, nix-portable, AM, curl, wget), y se copian donde un test los necesita.

Los nombres que aparecen en las tablas y diagramas de este documento:

| nombre | qué es | quién lo sirve | qué cuesta |
|---|---|---|---|
| `tiny` | el paquete más barato de la suite, y el piso de una resolución | `alpha` nativo y `boxed` dockerizado | `alpha` anuncia 2.0 KB, `boxed` 10 B con badge `verified`; gana `alpha` porque la clase va antes que los bytes |
| `alpha` | canal stand-in nativo (`kind=artifact`), responde también a `a` y `alfa` | — | sirve `tiny` y `mixed`; el programa que deja imprime `alpha` |
| `boxed` | canal stand-in que confina (`kind=confinement`) | — | 200 veces más barato que `alpha` y aun así pierde: eso es lo que prueba el test |
| `mixed` | paquete que un canal sirve y otro no puede contestar | `alpha` sirve, `down` no puede | igual que `tiny` por `alpha` |
| `offline` | nombre que solo `down` podría tener | `down`, que nunca puede ser preguntado | no se resuelve: sale 127 con "could not be asked" |
| `liar:x` | paquete cuyo canal publica un checksum que no corresponde al archivo | `liar` | se rechaza antes de correr: 127 |
| `twin` | un nombre que pertenece a dos programas (`left/twin`, `right/twin`) | `twins`, que contesta 3 y nombra los dos | 50 B cada uno; sin terminal no se resuelve |
| `nobody-serves-this`, `nobodys-nickname:tiny` | nombre y apodo que ningún canal sirve | nadie | 127 y nada en stdout; son las resoluciones más baratas que igual cuestan ~70 ms |
| `catname`, `catother` | paquetes que solo existen en un catálogo que hay que traer primero | `fastcat` (llega de una) y `slowcat` (escribe su índice byte a byte con `sleep 0.05`) | `slowcat` tarda ~0.6 s a propósito: es lo que hace medible la carrera de catálogos |
| `classname` | paquete que tienen un catálogo nativo y uno dockerizado | `plaincat` (nativo, lento igual que `slowcat`) y `boxcat` (dockerizado, inmediato) | prueba que el nativo se espera antes de tomar el dockerizado |
| `fcname` | paquete de un catálogo que solo corre dentro de una imagen | catálogo `fakecat`; lo corren los runtimes `fastbox`, `slowbox` y `needbox` | 4.9 KB anunciados más 2.9 KB de imagen; `fastbox` corre en 0.10 s y `slowbox` en 0.90 s, números inventados por los stand-ins |
| `figlet`, `jq` | paquetes de nixpkgs | canal **real** `nix-portable`, con `fake-nix-portable` de stand-in y un `nixexprs.tar.xz` armado en el test | anuncia 21.9 MB más 64.9 MB de la herramienta; no se descarga nada |
| `tool`, `extra` | proyectos de la pantry de pkgx | canal **real** `pkgx`, con `fake-pkgx` y una pantry y un dist armados en el test | unos cientos de bytes; el costo medido es el del canal, no de la red |
| `bitool`, `biauthor` | crates | canal **real** `binstall`, con `fake-cargo-binstall` y un índice y releases en disco | `binstall` es el canal más caro del bloque: ~60 procesos por `probe` |
| `cftool` | paquete de conda-forge | canal **real** `conda-forge`, con `fake-micromamba` y un channel en disco | — |
| `amtool` | programa de AM | canal **real** `am`, con `fake-appman` y un repositorio en disco | tamaño y versión desconocidos hasta instalar: eso es lo que prueba |
| `docker:alpine/figlet` | paquete de Alpine dentro de una imagen | canales **reales** `alpine` y `docker`, con `fake-docker` y un registro y un mirror en disco | imagen de 3.5 MB anunciada; no hay daemon |
| `hopname` | paquete de un canal que instala a través de su propia herramienta | `hopper`, que instala con `alpha:tiny` | 100 B, y la herramienta 2.0 KB: es el caso de "falta también la herramienta" |
| `collectme` | paquete de un canal que guarda su propio store | `collector` | sirve para medir `--purge` y `collect` |
| `shyname` | paquete de un canal que solo contesta si el spec lo nombra | `shy` | como conda-forge en la vida real: un nombre pelado es un no inmediato |
| `nph8`, `cfz`, `lph`, `aq` | no son paquetes: son `CMDFOUND_HOME` de distintas secciones | — | cada uno es el estado que una sección arma para sus asserts |
| `nph8keep`, `clsch`, `cfres`, `apres` | directorios que aparecen en los diffs de las opciones 5 y 7 | — | fixtures nuevos o copias, no paquetes |

Lo único que no viene de stand-ins en todo el documento son dos cosas, y las digo donde
aparecen: **el costo de un proceso y el escalado con concurrencia** (esos son `dash`, `gawk`,
`sed`, `grep` y `cat` de verdad, corriendo en esta máquina) y **la auditoría de
`~/.wget-hsts`** que cita 9a278d6, que es medición de otro agente con canales reales y una
descarga real de `github:sharkdp/hexyl`.

### 1.3 El reparto del reloj

```
Reparto del reloj de una corrida contra stand-ins (84.8 s), medido con un envoltorio
0 s                20 s               40 s               60 s               80 s
|------------------|------------------|------------------|------------------|----->
[core: 330 invocaciones de cmdfound ...................................] 59.6 s  70%
                                                                        [chan] 12.1 s  14%
                                                                             [blk] 8.4 s 10%
                                                                                 [s] 2.8 s 3%
                                                                                  [f] 1.1 s 1%
chan = 257 corridas directas de canales reales;  blk = asserts y fixtures del bloque;
s = sleeps y esperas de los tests;  f = armar fixtures (tar, sha256sum, cp -R)
```

```
De esos 59.6 s del core, lo que es diseno de test (medido, misma corrida contra stand-ins)
core, costo propio por invocacion      [############################################] ~45 s
setup que se logra resolviendo de nuevo[######]                                        6.8 s
polling de 100 ms de la carrera catalog[###]                                           3.8 s
directorio de 23 stand-ins compartido  [##]                            2.5 s (estimado)
mismo comando repetido en 13 lineas    [#]                                             1.3 s
```

Leído de otra manera: **~45 s es lo que cuesta el core por invocación** (procesos que arranca
para resolver), **~25-30 s es decisión de los tests** (cómo se arma el estado, cuántos canales
hay en el directorio, cuántas veces se repite un comando, cuánto se duerme) y el resto son los
asserts del propio bloque.

### 1.4 Costo por tipo de invocación

Medido con un envoltorio en `PATH` que cronometró 305 de las 330 invocaciones, todas contra
stand-ins. El envoltorio suma ~1 ms y un proceso a cada una; el proceso ya está descontado.

| tipo | n | total | promedio | procesos promedio |
|---|---|---|---|---|
| `--yes` que resuelve | 131 | 39.2 s | 299 ms | 239 |
| `-n` (dry run) | 57 | 13.4 s | 236 ms | 191 |
| `-i` (index-update) | 20 | 2.35 s | 118 ms | 87 |
| `--purge` | 34 | 2.15 s | 63 ms | 42 |
| decisión recordada (`bare` o `--yes` ya resuelto) | 46 | 1.29 s | 28 ms | 15 |
| `bare` que resuelve (sin tty, o bajo `script`) | 4 | 0.91 s | 227 ms | 206 |
| `--list` | 7 | 0.29 s | 42 ms | 25 |

Las 188 resoluciones (`--yes` + `-n`) son 52.6 s de los 86: **el bloque es caro porque resuelve
188 veces, no porque tenga 1,670 líneas.**

### 1.5 De dónde salen los procesos

```
Origen de los 61,275 procesos de una corrida contra stand-ins (ptrace; base anterior)
core, forks de su propio shell  [#############################################] 37,565  61%
  |- subshells de $(...)        [###############################]          26,014  (69% de esos)
  |- awk                        [######]                                          5,017
  |- resto (tr, date, rm, sort, head, canales)                                     6,534
dentro de programas que el core arranca (canales, stand-ins)  [###########]      11,498  19%
fuera del core: shell del bloque + 257 corridas directas de canales [###########] 12,212  20%
```

```
Una resolucion contra stand-ins: quien arranca que (medido: --yes tiny = 225 procesos)
cmdfound --yes tiny
 |
 +- _probe_all .................................. 45 procesos
 |   +- por cada uno de los 22 canales del directorio: 2
 |   |    +- $(_channels_dir) ................... 1 subshell
 |   |    +- $(".../canal" probe tiny) .......... 1 subshell que hace exec del canal
 |   +- LC_ALL=C sort ........................... 1
 |
 +- _probe_emit ................................. 50 procesos (25 por candidato x 2)
 |   +- $("$(_channels_dir)/canal" meta) ........ 2  (subshell anidado + el canal)
 |   +- 6 x $(printf | awk -F= ...) ............. 18  (3 cada uno: subshell, printf, awk)
 |   +- $(_value confines) + $(_value describes)   2  (shell puro, pero en subshell)
 |   +- $(_channel_home) + $(_est_us) + awk clave  3
 |
 +- _resolve .................................... 21   +- _ask ......... 15 (todos subshells)
 +- _place ...................................... 20   +- _est_us ...... 9
 +- _obtained ................................... 7    +- _cache_key ... 6 (3 subshells + 3 tr)
 +- (main) ...................................... 6    +- _locate ...... 6
```

Los tres primeros son la mitad de todo: en el bloque completo `_probe_emit` arranca 5,344
procesos, `_probe_all` 4,391 y `_resolve` 4,031, de los 37,565 del core.

### 1.6 Reloj por sección

Medido con una marca por línea, contra stand-ins (esa corrida dio 99.8 s con load 2.5-3.6; las
secciones son proporcionales). Las líneas son la numeración de `tools.db` en 9a278d6.

| sección | líneas | s | % | procesos |
|---|---|---|---|---|
| binstall | 1895-2146 | 11.1 | 11.1% | 7,110 |
| nix-portable | 1658-1888 | 10.7 | 10.7% | 6,303 |
| network settings (rc, proxies, -U) | 2683-2910 | 8.8 | 8.8% | 6,497 |
| conda-forge | 1460-1653 | 7.6 | 7.6% | 4,398 |
| docker | 3125-3348 | 7.4 | 7.5% | 2,761 |
| resolver core | 724-877 | 7.4 | 7.4% | 6,066 |
| pkgx | 1249-1403 | 7.1 | 7.1% | 4,379 |
| udocker | 2920-3112 | 5.8 | 5.8% | 2,655 |
| runtimes, catálogos en imagen | 2153-2286 | 5.2 | 5.2% | 4,228 |
| --list / --purge / --ephemeral | 2293-2415 | 4.3 | 4.3% | 2,611 |
| carrera de catálogos | 1137-1174 | 4.2 | 4.2% | 1,604 |
| aqua a través de su tool | 1046-1089 | 3.8 | 3.8% | 2,701 |
| canal que espera un programa | 1179-1209 | 2.9 | 2.9% | 1,952 |
| github digests | 1002-1041 | 2.3 | 2.4% | 1,072 |
| resto (11 secciones chicas) | — | 10.5 | 10.5% | 5,895 |
| setup compartido | 674-721 | 0.12 | 0.1% | 62 |

El setup compartido cuesta 0.12 s: **no hay nada que ganar "compartiendo el setup"**. Lo que
cuesta es el estado que cada sección construye resolviendo de verdad.
---

## 2. Las opciones, una por una

Van en el orden en que las ranqueé por segundos ahorrados. Cada diff sale de 9a278d6 y está
recortado a lo que hay que decidir.

---

### Opción 1 — Correr grupos independientes en paralelo

**Qué cambia.** Hoy el bloque es un solo script que `tools.sh` corre de principio a fin en un
solo directorio. La idea es partirlo en varios bloques (`@begin{cmdfound-core}`,
`@begin{cmdfound-pkgx}`, …), darle a cada uno su propio directorio y correr varios a la vez.
No toca el core ni un solo assert: mueve fixtures y cambia el corredor.

**El diff del corredor** (este sí lo escribí, no lo corrí):

```diff
--- a/sh/tests/tools.sh
+++ b/sh/tests/tools.sh
@@ -46,20 +46,33 @@
 
 [ -z "${1}" ] || TOOLS_WITH_TEST="${1}"
 
+#a directory and a shell for each block, so blocks that share nothing run at
+#once: TESTS_JOBS of them, and each answer is read in the order they started.
+#Two blocks in one directory would step on each other's fixtures, which is
+#why every block gets its own and wipes only that
+jobs="${TESTS_JOBS:-1}"
+started=""
 for tool in ${TOOLS_WITH_TEST}; do
-    rm -rf ./* || (sleep 1; rm -rf ./*)
-    printf "%s\\n" "${tool} ........................" | awk '{ printf("%s ", substr($0, 0, 25)); }'
-    printf "%s\\n" "PATH=../${tools}:/bin:/usr/bin" > run.sh
+    rm -rf "d.${tool}"; mkdir "d.${tool}" || exit 1
+    printf "%s\\n" "PATH=../../${tools}:/bin:/usr/bin" > "d.${tool}/run.sh"
     sed -e "/^@begin{$tool}/,/^@end/p" -e '1,$d' ../${tools_db} |\
     sed -e '/^@begin/d' -e '/^@end/d' \
-        -e 's/\([^\\]\)[ 	]*$/\1 || exit 1/g' >> run.sh
-    printf "exit 0\\n" >> run.sh
+        -e 's/\([^\\]\)[ 	]*$/\1 || exit 1/g' >> "d.${tool}/run.sh"
+    printf "exit 0\\n" >> "d.${tool}/run.sh"
     #stdin is closed, not inherited: 32 of these tools read their arguments
     #from stdin when it is not a terminal, so a runner started from cron, CI
     #or a pipeline hands them an idle descriptor they wait on forever. A block
     #that wants to pipe something in writes the pipe itself
-    sh -x run.sh        > run.log 2>&1 </dev/null
-    if [ "${?}" -ne "0" ]; then
+    (cd "d.${tool}" && sh -x run.sh > run.log 2>&1 </dev/null; printf "%s\\n" "${?}" > rc) &
+    started="${started} ${tool}:${!}"
+    [ "$(printf "%s\n" ${started} | awk 'END {print NR}')" -lt "${jobs}" ] || wait
+done
+wait
+for tool_pid in ${started}; do
+    tool="${tool_pid%:*}"
+    printf "%s\\n" "${tool} ........................" | awk '{ printf("%s ", substr($0, 0, 25)); }'
+    cd "d.${tool}" || exit 1
+    if [ "$(cat rc)" -ne "0" ]; then
         #generate report
         printf "FAILED\\n"
         printf "+---Test------------------------------\\n"
@@ -73,6 +86,7 @@
         printf "ok\\n"
     fi
     ran="$((${ran} + 1))"
+    cd .. || exit 1
 done
 
 #the sandbox goes whether the run passed or not. Keeping it after a failure
```

**Y el diff que no se puede recortar: el de partir el bloque.** Las secciones hoy no son
independientes. Esto es lo que comparten, medido leyendo el bloque:

```
Quien depende de quien hoy (flechas = fixtures, homes o funciones que la seccion de arriba dejo)
setup compartido (hostbin, amrepo, apfix/apmir/apreg)
   |            |                 |               |
   v            v                 v               v
resolver core  alpine           docker          network
   |
   +--> aqua index (define c404, realch, el home aq/)
          |        |          |         |         |        |        |
          v        v          v         v         v        v        v
      github    aqua/tool   pkgx      AM     conda-forge  nix-p.  binstall
                    |         ^
                    +---------+  pkgx copia am/channels/github/cache (linea 1354)
      udocker  --define-->  flcheck() y flsame()  --usa-->  docker (lineas 3250, 3253)
      pkgx, AM, conda-forge, nix-portable, binstall, alpine --9 lineas--> network
```

Cada flecha es trabajo: o se duplica el fixture en el grupo nuevo, o se mueve a un prólogo que
cada bloque repite. Son 9 líneas en la sección network que leen fixtures de otras seis
secciones, una línea en pkgx que copia el home de aqua, dos funciones (`flcheck`, `flsame`)
definidas en udocker y usadas en docker, y tres variables (`c404`, `realch`, `apreg`) que se
rearman en una línea cada una.

**Qué se pierde.** Ningún assert. Se pierde la propiedad de que el bloque es un script lineal
que se lee de arriba a abajo y donde cualquier línea puede usar lo que dejó la anterior: ese es
el estilo de toda la suite hoy. También se pierde el orden determinista de las corridas, que es
lo que hace que un fallo se lea igual dos veces.

**El ahorro.** No lo medí como cambio, porque el cambio no existe todavía. Lo que sí medí es
cómo escala esta máquina cuando varios lazos con muchos forks corren a la vez:

```
Costo de un proceso segun cuantos flujos a la vez (medido con dash y awk reales, no stand-ins)
1 flujo   [################] 1.641 ms/proceso   throughput x1.0
2 flujos  [##########]       0.981 ms/proceso   throughput x1.67
4 flujos  [#######]          0.688 ms/proceso   throughput x2.4
8 flujos  [#####]            0.469 ms/proceso   throughput x3.5
```

Ocho grupos no dan 8x: dan 3.5x. Con 86 s de trabajo total y el reparto de secciones medido,
el piso teórico es la sección más larga (binstall, 11 s) y el techo práctico es 86/3.5 ≈ 25 s.
**Estimado: se aterriza entre 25 y 35 s**, según cuántos grupos y cuánta carga ajena haya.

**Riesgo.** Alto, y de dos tipos. Uno: un fixture que quedó compartido por descuido hace que
dos grupos se pisen, y eso se ve como un test que falla una vez de cada diez, con un mensaje
que no señala al culpable. Dos: los tests que dependen del reloj (la carrera de catálogos con
stand-ins que escriben a 50 ms por byte, los `kill`/`wait`, el Ctrl-C) se vuelven frágiles bajo
carga: ya medí que el mismo bloque pasa de 82 a 141 s cuando el load llega a 6. Ocho grupos en
paralelo *producen* ese load.

**Usuarios reales.** Cero efecto. Es puro test.

**¿Se deshace fácil?** El corredor sí (un revert). La partición del bloque no: una vez que los
fixtures se duplican, volver atrás es otro trabajo de refactor.

---

### Opción 2 — Menos forks en los caminos calientes del core

**Qué cambia.** El core arranca 37,565 procesos propios, y el 69% son subshells de `$(...)` que
capturan la salida de una función que ya está escrita en shell puro. La idea es que esas
funciones dejen el resultado en una variable en vez de imprimirla, y que las extracciones
`$(printf … | awk -F= …)` (3 procesos cada una) se lean con la función `_value` que ya existe.

**Diff, hunk 1: la función que pone el valor en una variable** (`_value` sigue existiendo para
quien la quiera en una sustitución):

```diff
--- a/sh/tools/cmdfound
+++ b/sh/tools/cmdfound
@@ -2297,15 +2311,19 @@
 #the three are read in the shell alone. A step reads dozens of fields, and a
 #pipe into awk for each one doubled what resolving takes
 
-_value() {
-    #$1 => a key, $2 => key=value lines. Prints the value of the first line
-    #with that key, whole: a url keeps the = signs it carries
+_value_in() {
+    #$1 => a key, $2 => key=value lines. Puts the value of the first line with
+    #that key in value, whole - a url keeps the = signs it carries - and
+    #answers 1 when there is none. A caller that reads it this way starts no
+    #subshell for it, which is the whole point: one resolution asks for
+    #dozens of them
+    value=""
     _value__rest="${2}"
     while [ -n "${_value__rest}" ]; do
         _value__line="${_value__rest%%
 *}"
         case "${_value__line}" in
-            "${1}="*) printf "%s\\n" "${_value__line#*=}"; return 0 ;;
+            "${1}="*) value="${_value__line#*=}"; return 0 ;;
         esac
         [ X"${_value__line}" = X"${_value__rest}" ] && break
         _value__rest="${_value__rest#*
@@ -2314,6 +2332,13 @@
     return 1
 }
 
+_value() {
+    #$1 => a key, $2 => key=value lines. Prints what _value_in reads, for a
+    #caller that wants it in a substitution
+    _value_in "${1}" "${2}" || return 1
+    printf "%s\\n" "${value}"
+}
+
 _values() {
     #$1 => a key, $2 => key=value lines. Prints the value of every line with
     #that key, one a line
```

**Hunk 2: las seis extracciones de `_probe_emit`, que es el peor sitio del core.**

```diff
--- a/sh/tools/cmdfound
+++ b/sh/tools/cmdfound
@@ -757,17 +771,17 @@
             return "${?}" ;;
     esac
 
-    _pe__v="$(printf "%s\\n" "${_pe__out}" | awk -F= '$1=="version"{print $2; exit}')"
-    _pe__b="$(printf "%s\\n" "${_pe__out}" | awk -F= '$1=="bytes"{print $2; exit}')"
-    _pe__g="$(printf "%s\\n" "${_pe__out}" | awk -F= '$1=="badge"{print $2; exit}')"
+    _value_in version "${_pe__out}"; _pe__v="${value}"
+    _value_in bytes "${_pe__out}"; _pe__b="${value}"
+    _value_in badge "${_pe__out}"; _pe__g="${value}"
     [ -z "${_pe__v}" ] && return 1
     #a catalog that turns a name into a repository says which one, and that
     #repository is what gets shown, placed and asked about from here
-    _pe__p="$(printf "%s\\n" "${_pe__out}" | awk -F= '$1=="package"{print $2; exit}')"
+    _value_in package "${_pe__out}"; _pe__p="${value}"
     [ -z "${_pe__p}" ] && _pe__p="${_pe__pkg}"
     #a channel that installs through a tool of its own names that tool as a
     #spec, and the resolver gets it the way it gets anything else
-    _pe__r="$(printf "%s\\n" "${_pe__out}" | awk -F= '$1=="requires"{print $2; exit}')"
+    _value_in requires "${_pe__out}"; _pe__r="${value}"
     [ -z "${_pe__r}" ] && _pe__r="-"
     #what a tool installs, the tool downloads and checks, or does not, and
     #cmdfound cannot tell which: such a path keeps no badge of its own, a
```

**Hunk 3: el directorio de canales se calcula una vez, no una por canal preguntado.**

```diff
--- a/sh/tools/cmdfound
+++ b/sh/tools/cmdfound
@@ -375,6 +375,19 @@
     fi
 }
 
+_channels_dir_in() {
+    #puts the directory in channels_dir, once for the whole run: every channel
+    #asked, and every question about what one says of itself, needed it, and
+    #each asked for it in a subshell of its own
+    [ -n "${channels_dir}" ] && return 0
+    if [ -n "${CMDFOUND_CHANNELS}" ]; then
+        channels_dir="${CMDFOUND_CHANNELS}"
+        return 0
+    fi
+    channels_dir="$(_realpath "${0}").d"
+    return 0
+}
+
 _channels_dir() {
     #an environment variable replaces the directory outright, which is how the
     #tests hand this program channels that answer without a network
@@ -517,7 +530,8 @@
     #$1 => channel, $2 => key. A channel that says nothing is an artifact
     #channel that confines nothing and describes itself, which is the common
     #case and the one worth not having to write down
-    _channel_meta__value="$("$(_channels_dir)/${1}" meta 2>/dev/null | \
+    _channels_dir_in
+    _channel_meta__value="$("${channels_dir}/${1}" meta 2>/dev/null | \
         awk -F= -v k="${2}" '$1 == k {print $2; exit}')"
 
     if [ -z "${_channel_meta__value}" ]; then
@@ -744,7 +758,7 @@
     #what the channel says of itself is read once, and only of a channel that
     #had the name: read of every channel on every resolution, it would be one
     #more program started per channel for an answer nobody needs
-    _pe__meta="$("$(_channels_dir)/${_pe__c}" meta 2>/dev/null)"
+    _channels_dir_in; _pe__meta="$("${channels_dir}/${_pe__c}" meta 2>/dev/null)"
     #a catalog is never a path by itself, and is handed over whole. Which
     #kind of channel this is, is a line of what it said, found without
     #starting anything, since every path of every resolution goes by here
@@ -1300,7 +1314,7 @@
                 [ X"$(_channel_meta "${_probe_all__c}" kind)" = X"catalog" ] || continue
                 _probe_all__catalog="1"
             fi
-            _probe_all__out="$("$(_channels_dir)/${_probe_all__c}" probe \
+            _channels_dir_in; _probe_all__out="$("${channels_dir}/${_probe_all__c}" probe \
                 "${_probe_all__pkg}" "${_probe_all__ver}" 2>/dev/null)"
             _probe_all__rc="${?}"
             #a channel with no catalog here is left for below: its catalog is
```

**Cuántos sitios más se ven igual.** En `sh/tools/cmdfound`, hoy: 51 capturas
`$(_path_field …)` (18 de ellas en `_show_paths`), 39 `$(_value …)`, 22 `$(_channels_dir)`, 8
extracciones `$(printf … | awk -F= …)`. El prototipo que medí tocó 23 líneas: 6 extracciones,
2 `_value`, 3 `_channels_dir` y 12 `_path_field` de `_show_paths`. Quedan ~100 sitios del mismo
molde, más los mismos patrones en los 10 canales (por ejemplo `binstall`, opción 10).

```
Una resolucion antes y despues del prototipo (procesos medidos con ptrace, contra stand-ins)

ANTES (9a278d6)                            DESPUES (23 sitios de llamada cambiados)
--yes tiny = 225 procesos                  --yes tiny = 162 procesos  (-28%)
-n tiny    = 184 procesos                  -n tiny    = 110 procesos  (-40%)
(el reloj de una resolucion bajo 55-90 ms segun la corrida; ver el texto)

_probe_emit, por candidato:                _probe_emit, por candidato:
  $(printf|awk version) ... 3 procesos       _value_in version .... 0 procesos
  $(printf|awk bytes) ..... 3                _value_in bytes ...... 0
  $(printf|awk badge) ..... 3                _value_in badge ...... 0
  $(printf|awk package) ... 3                _value_in package .... 0
  $(printf|awk requires) .. 3                _value_in requires ... 0
  $(printf|awk estimate) .. 3                _value_in estimate ... 0
  $(_value confines) ...... 1                _value_in confines ... 0
  $(_value describes) ..... 1                _value_in describes .. 0
  $("$(_channels_dir)/c" meta) .. 2          $("${channels_dir}/c" meta) .. 1
  ----------------------------------         ----------------------------------
  22 procesos por candidato                  1 proceso por candidato
```

**Qué se pierde.** Ningún assert, ningún test, ninguna cobertura. Se pierde legibilidad en un
punto: `_value_in version "$out"; v="${value}"` se lee peor que `v="$(... awk ...)"`, y el
resultado viaja por una variable global (`value`, `field`, `channels_dir`) en un programa que
hoy evita globals fuera de las que ya usa. Es el estilo el que paga, no la funcionalidad.

**El ahorro, medido.** Corrí el bloque completo con el prototipo, dos veces, alternando con la
base:

| corrida | procesos | reloj | load al empezar |
|---|---|---|---|
| base 9a278d6 | 61,685 | 87.3 s | 1.48 |
| prototipo (11 líneas) | 55,334 | 78.6 s | 1.50 |
| base 9a278d6 | 61,683 | 86.0 s | 2.19 |
| prototipo (11 líneas) | 55,334 | 81.3 s | 2.54 |
| prototipo + `_path_field_in` (23 líneas) | 54,752 | 78.3 s | 2.32 |
| base 9a278d6 | 61,684 | 92.9 s | 2.63 |

**Medido: -6,932 procesos (-11.2%) y entre 6 y 14 s de reloj**, con 23 sitios de llamada
cambiados (más dos funciones nuevas, `_value_in` y `_path_field_in`) y los tests pasando en las
tres corridas del prototipo. Tomando el ms por proceso que ya medí (1.0-1.1 ms), esos 23 sitios
valen ~7 s; el rango de 6 a 14 s es el ruido de carga de esta máquina, no del cambio.

**Extrapolación (estimada, no medida):** los ~100 sitios restantes del mismo molde en el core
son del orden de 8,000-13,000 procesos más, o sea **otros 8-14 s, para un total de 15-20 s** si
se hace completo. Es aritmética sobre un patrón medido, no una corrida.

**Riesgo.** Medio, y es el riesgo más sano de la lista: si me equivoco, un test falla en la
corrida siguiente, porque el bloque ya cubre estas rutas línea por línea. Los errores a cuidar
son tres: `$(...)` recorta los newlines del final y una variable no, así que un valor
multilínea cambia de forma; una variable global con el mismo nombre en dos funciones anidadas
se pisa; y `_value` devuelve el valor entero mientras `awk -F= '{print $2}'` cortaba en el
segundo `=` (para `version`, `bytes`, `badge`, `package`, `requires`, `estimate` no hay
diferencia, pero para una `url` sí la habría).

**Usuarios reales.** Sí, y es la única opción que los ayuda de verdad: una resolución de
`--yes` baja de 225 a 162 procesos medidos, y un dry run de 184 a 110. En esta máquina son
55-90 ms menos por comando, según la carga del momento; donde los forks son más caros (WSL2 con
antivirus, contenedor con cgroups apretados) la diferencia es mayor, porque lo que se quita son
forks.

**¿Se deshace fácil?** Sí, hunk por hunk: cada sitio es independiente de los demás.

---

### Opción 3 — La carrera de catálogos sin poll de 100 ms

**Qué cambia.** Cuando ningún catálogo local tiene el nombre, el core los busca todos a la vez
y espera en un lazo que duerme 100 ms entre vueltas. En el bloque eso son 37 sleeps de 100 ms,
3.75 s de reloj medidos con el tracer. El arreglo correcto es que los hijos avisen por un fifo
y el lazo bloquee en un `read`; la versión barata, la que medí, es bajar el poll a 20 ms.

```diff
--- a/sh/tools/cmdfound
+++ b/sh/tools/cmdfound
@@ -1250,7 +1250,7 @@
             break
         done
         _rc__run="${_rc__left}"
-        [ -n "${_rc__run}" ] && { sleep 0.1 2>/dev/null || sleep 1; }
+        [ -n "${_rc__run}" ] && { sleep 0.02 2>/dev/null || sleep 1; }
     done
     [ -n "${_rc__confined}" ] && return 2
     return 1
```

**Qué se pierde.** Nada de cobertura. Con 20 ms el lazo da 5 veces más vueltas, y cada vuelta
pregunta `_channel_meta` de los canales que siguen corriendo: el bloque pasó de 61,683 a 61,815
procesos (medido), o sea el poll más fino cuesta procesos aunque ahorre reloj. La versión con
fifo no tendría ese costo, pero es código nuevo que no escribí: no hay diff para ella.

**El ahorro.** Medido de dos maneras que coinciden más o menos: el techo es 3.75 s (es el reloj
que suman los 37 sleeps, medido con ptrace), y comparando las secciones que hacen carreras
entre la base y la variante de 20 ms dio -3.3 s (carrera de catálogos -0.2 s, canal que espera
-0.9 s, pkgx -1.35 s, runtimes -0.9 s), con la sección resolver core como control en +0.01 s.
Las corridas completas no sirven para esta comparación porque el load se movió entre ellas.
**Medido: ~3 s.** Los tests pasan con el poll de 20 ms.

**Riesgo.** Bajo para la variante de 20 ms (es un número, y el lazo ya tolera cualquier
granularidad). Medio para la variante con fifo: hay que limpiar el fifo en las señales, y un
error ahí cuelga una resolución en vez de hacerla lenta.

**Usuarios reales.** Poco pero positivo: hasta 100 ms menos en la primera resolución que tiene
que traer catálogos (con fifo, hasta 100 ms; con poll de 20 ms, hasta 80 ms). Contra los
segundos que toma bajar un catálogo real, es ruido.

**¿Se deshace fácil?** Sí, es una línea.

---

### Opción 4 — Las esperas fijas de los tests

**Qué cambia.** Tres líneas del bloque duermen un tiempo fijo en vez de esperar por algo: el
test de Ctrl-C de udocker duerme 1 s antes de mandar el `\003` y 1 s después, y los dos tests
de `kill` duermen 0.2 s extra después de que el archivo que esperaban ya apareció.

```diff
--- a/sh/tests/tools.db
+++ b/sh/tests/tools.db
@@ -1484,7 +1484,7 @@
 #with, and the next one goes on from there instead of starting over
 mkdir -p cfcurl && cp ../cmdfound.d/fake-curl cfcurl/curl && chmod 755 cfcurl/curl
 PATH="$(pwd)/cfcurl:${PATH}" FAKE_CURL_BODY="${cfch}/channeldata.json" FAKE_CURL_LOG="$(pwd)/cfcurllog" CMDFOUND_HOME="$(pwd)/cfres" CMDFOUND_CONDA_FORGE_CHANNEL=https://conda-forge.invalid FAKE_CURL_STALL=1 "${cfdir}" index > /dev/null 2>&1 & cfpid="${!}"
-i=0; while [ ! -s cfres/channels/conda-forge/index/channeldata.json.part ] && [ "${i}" -lt 100 ]; do sleep 0.1; i=$((i + 1)); done; sleep 0.2
+i=0; while [ ! -s cfres/channels/conda-forge/index/channeldata.json.part ] && [ "${i}" -lt 100 ]; do sleep 0.02; i=$((i + 1)); done; sleep 0.05
 kill -TERM "${cfpid}"; wait "${cfpid}"; test X"${?}" = X"143"
 test -s cfres/channels/conda-forge/index/channeldata.json.part && test -s cfres/channels/conda-forge/index/channeldata.json.part.etag
 PATH="$(pwd)/cfcurl:${PATH}" FAKE_CURL_BODY="${cfch}/channeldata.json" FAKE_CURL_LOG="$(pwd)/cfcurllog" CMDFOUND_HOME="$(pwd)/cfres" CMDFOUND_CONDA_FORGE_CHANNEL=https://conda-forge.invalid "${cfdir}" index | grep -x 'packages=111' >/dev/null
@@ -2513,7 +2513,7 @@
 #A stand-in curl serves the mirror and cannot reach any registry
 cp ../cmdfound.d/fake-curl apcurl/fake-curl && printf '%s\n' '#!/bin/sh' "for a in \"\${@}\"; do last=\"\${a}\"; done; printf '%s %s\\n' \"\${1}\" \"\${last}\" >> '$(pwd)/apcurllog'" "case \"\${last}\" in https://alpine.invalid/v3.22/main/*) FAKE_CURL_BODY='${apfix}/main/APKINDEX.tar.gz' ;; https://alpine.invalid/v3.22/community/*) FAKE_CURL_BODY='${apfix}/community/APKINDEX.tar.gz' ;; *) exit 7 ;; esac" 'export FAKE_CURL_BODY' 'exec sh "${0%/*}/fake-curl" "${@}"' > apcurl/curl && chmod 755 apcurl/curl
 PATH="${apcurl}:${apbin}:${PATH}" CMDFOUND_HOME="$(pwd)/apres" CMDFOUND_ALPINE_MIRROR=https://alpine.invalid FAKE_CURL_LOG="$(pwd)/apfakelog" FAKE_CURL_STALL=1 "${apch}" index > /dev/null 2>&1 & appid="${!}"
-i=0; while [ ! -s apres/channels/alpine/index/main.part ] && [ "${i}" -lt 100 ]; do sleep 0.1; i=$((i + 1)); done; sleep 0.2
+i=0; while [ ! -s apres/channels/alpine/index/main.part ] && [ "${i}" -lt 100 ]; do sleep 0.02; i=$((i + 1)); done; sleep 0.05
 kill -TERM "${appid}"; wait "${appid}"; test X"${?}" = X"143"
 test -s apres/channels/alpine/index/main.part && test -s apres/channels/alpine/index/main.part.etag
 test X"$(PATH="${apcurl}:${apbin}:${PATH}" CMDFOUND_HOME="$(pwd)/apres" CMDFOUND_ALPINE_MIRROR=https://alpine.invalid FAKE_CURL_LOG="$(pwd)/apfakelog" "${apch}" index | head -1)" = X"packages=142"
@@ -3067,7 +3067,7 @@
 #proot when a program outlives a Ctrl-C by a quarter of a second, and proot
 #leaves in the container the directories it made to mount HOME and the
 #working directory on, empty and unreadable: they go, so du can measure it
-{ ! script --version 2>/dev/null | grep util-linux >/dev/null; } || test X"$( { sleep 1; printf '\003'; sleep 1; } | PATH="${udbin}:${PATH}" HOME="${udhome}" CMDFOUND_HOME="${udh}" script -qec "cd '${udhome}/proj' && cmdfound fcname --sleep 5; echo rc=\$?" /dev/null 2>/dev/null | tr -d '\r' | sed -n 's/.*rc=//p')" = X"130"
+{ ! script --version 2>/dev/null | grep util-linux >/dev/null; } || test X"$( { sleep 0.3; printf '\003'; sleep 0.3; } | PATH="${udbin}:${PATH}" HOME="${udhome}" CMDFOUND_HOME="${udh}" script -qec "cd '${udhome}/proj' && cmdfound fcname --sleep 5; echo rc=\$?" /dev/null 2>/dev/null | tr -d '\r' | sed -n 's/.*rc=//p')" = X"130"
 { ! script --version 2>/dev/null | grep util-linux >/dev/null; } || { test -d "${udc}/ud/containers/f1a-0000-4000-8000-000000000001/ROOT${udhome%/*}" && test X"$(find "${udc}/ud/containers" -type d -perm 000 | wc -l)" = X"0"; }
 #a placement has its container, and another program of the same package gets
 #a launcher and nothing installed; a runtime that has the image and the engines
```

**Qué se pierde.** Nada de cobertura: los tres asserts siguen intactos. Lo que se pierde es
margen. El primer `sleep 1` del test de Ctrl-C existe para que el programa dentro de `script`
haya arrancado antes de que llegue el Ctrl-C; con 0.3 s el margen depende de la carga de la
máquina.

**El ahorro, medido** con marca por línea contra stand-ins, comparando la base y la variante:

| línea | base | variante | delta |
|---|---|---|---|
| 3070 (Ctrl-C de udocker) | 2,008 ms | 607 ms | -1,401 ms |
| 1487 (kill de conda-forge) | 304 ms | 73 ms | -230 ms |
| 2516 (kill de alpine) | 305 ms | 73 ms | -231 ms |

**Medido: -1.86 s**, y el bloque pasó.

**Riesgo.** Este es el que más me preocupa de los baratos: es exactamente el cambio que produce
un test intermitente. Pasó en mi corrida con load 5.75, pero el margen de 0.3 s es una apuesta
a la carga. Si falla, falla raro: el Ctrl-C llega antes de que el programa arranque y el status
esperado (130) no aparece. La versión sin apuesta es esperar por una señal del programa (un
archivo que el stand-in escribe al arrancar) en vez de por el reloj; eso es fixture nuevo y no
lo escribí.

**Usuarios reales.** Cero efecto.

**¿Se deshace fácil?** Sí, son tres números.

---

### Opción 5 — Un directorio de canales por test, no los 23 stand-ins compartidos

**Qué cambia.** El bloque exporta `CMDFOUND_CHANNELS` apuntando al directorio con los 23
stand-ins, y 84 resoluciones corren contra él (medido). Cada canal del directorio es, por
resolución, dos procesos: el subshell de la captura y el canal mismo, aunque no tenga nada que
ver con lo que se pregunta. Los tests que ya se armaron su propio directorio (`ordch`, `fcch`,
`lpch`, `spch`) no pagan eso; los demás sí.

```diff
--- a/sh/tests/tools.db
+++ b/sh/tests/tools.db
@@ -726,10 +726,14 @@
 cmdfound --yes nosuchchannel:x >/dev/null 2>&1; test X"${?}" = X"127"
 #a native channel beats a confining one that is two hundred times cheaper and
 #carries a better badge: class comes before bytes, and no saving on the
-#download buys being put inside a box
-test X"$(cmdfound -n tiny | tail -1 | awk '{print $2}')" = X"alpha:tiny@1.0"
-test X"$(cmdfound -n tiny | tail -1 | awk '{print $4, $5, $6, $7}')" = X"nativo, aunque no el"
-test X"$(cmdfound --yes tiny 2>/dev/null | head -1)" = X"alpha"
+#download buys being put inside a box. Only the two channels this asks about
+#are here: every channel in the directory is one program started per
+#resolution, and a resolution that asks twenty-one channels nothing is
+#twenty-one programs of nothing
+clsch="$(pwd)/clsch"; mkdir -p clsch && for c in alpha boxed; do ln -s "$(cd .. && pwd)/cmdfound.d/${c}" "clsch/${c}"; done
+test X"$(CMDFOUND_CHANNELS="${clsch}" cmdfound -n tiny | tail -1 | awk '{print $2}')" = X"alpha:tiny@1.0"
+test X"$(CMDFOUND_CHANNELS="${clsch}" cmdfound -n tiny | tail -1 | awk '{print $4, $5, $6, $7}')" = X"nativo, aunque no el"
+test X"$(CMDFOUND_CHANNELS="${clsch}" cmdfound --yes tiny 2>/dev/null | head -1)" = X"alpha"
 #with no CMDFOUND_HOME the home is ~/.cmdfound, one place that one rm -rf
 #removes: XDG_CACHE_HOME is not read, and nothing goes under ~/.cache, which
 #cache cleaners wipe along with the channels.conf that would sit in it
```

**Qué se pierde.** Cobertura incidental, y no es poca: hoy cada una de esas 84 resoluciones
pregunta a 22 canales que no tienen el nombre, y ese "no lo tengo" es justo lo que el resolver
tiene que manejar bien. Con directorios estrechos, el caso "veintitantos canales dicen que no"
deja de ejercitarse en cada resolución y hay que escribirlo aparte, una vez. Además el diff no
es de 4 líneas: son ~84 líneas de test que tienen que decir con qué directorio corren, y cada
una es una oportunidad de dejar el directorio incompleto y hacer que el test pruebe menos de lo
que dice probar sin que nadie lo note.

**El ahorro.** Medí una resolución con los 23 stand-ins del directorio y con 2, los que
`tiny` necesita:

| caso | 23 canales | 2 canales | delta |
|---|---|---|---|
| `-n tiny` | 184 procesos, 244 ms | 146 procesos, 208 ms | -38 procesos, -36 ms |
| `--yes tiny` | 225 procesos, 301 ms | 187 procesos, 243 ms | -38 procesos, -58 ms |

Las 84 resoluciones del directorio compartido cuestan 18.6 s en total (medido). Si en promedio
se les quitan 20 de los 22 canales de más, **estimado: 2-3 s** (84 × ~30 ms). No medí el bloque
completo con todos los directorios estrechos; sí verifiqué que el diff de arriba pasa.

**Riesgo.** Medio-alto, pero del tipo peor: no rompe, adelgaza. Un test que hoy prueba "de 23
canales gana el nativo" y mañana prueba "de 2 canales gana el nativo" sigue en verde diciendo
lo mismo en su nombre.

**Usuarios reales.** Cero efecto directo. Lo que sí ayuda a un usuario con muchos canales es la
opción 2 (menos procesos por canal preguntado).

**¿Se deshace fácil?** Línea por línea sí, pero son 84 líneas.

---

### Opción 6 — Una corrida contesta las dos preguntas

**Qué cambia.** Hay 13 líneas que repiten el comando de la línea anterior para mirar otra parte
del resultado: el status en una y la salida en la otra. Guardando la salida y el status de una
sola corrida se contesta lo mismo con la mitad de resoluciones.

```diff
--- a/sh/tests/tools.db
+++ b/sh/tests/tools.db
@@ -721,8 +721,8 @@
 CMDFOUND_UDOCKER_PYPI="$(pwd)/udpypi"; CMDFOUND_UDOCKER_ENGINES="$(pwd)/udengines.tar.gz"; export CMDFOUND_UDOCKER_PYPI CMDFOUND_UDOCKER_ENGINES
 #nothing to serve is 127 and nothing on stdout, so that a caller can tell
 #"nothing ran" from a program that ran and failed
-cmdfound --yes nobody-serves-this >/dev/null 2>&1; test X"${?}" = X"127"
-test X"$(cmdfound --yes nobody-serves-this 2>/dev/null)" = X""
+nsout="$(cmdfound --yes nobody-serves-this 2>/dev/null)"; test X"${?}" = X"127"
+test X"${nsout}" = X""
 cmdfound --yes nosuchchannel:x >/dev/null 2>&1; test X"${?}" = X"127"
 #a native channel beats a confining one that is two hundred times cheaper and
 #carries a better badge: class comes before bytes, and no saving on the
```

**Qué se pierde.** Nada de cobertura: los dos asserts quedan. Se pierde una propiedad chiquita
pero real: hoy cada línea es un experimento independiente, y si la segunda corrida diera algo
distinto de la primera (porque la primera dejó estado), el bloque lo vería. Al reusar una
corrida, eso se deja de comprobar. Las 13 líneas, medidas, son:

| líneas | comando repetido | ms de la repetición |
|---|---|---|
| 724-725 | `cmdfound --yes nobody-serves-this` | 77 |
| 730-731 | `cmdfound -n tiny` | 167 |
| 811-814-815 | `cmdfound --yes liar:x` (tres veces) | 383 |
| 849-850 | `cmdfound --yes nobodys-nickname:tiny` | 117 |
| 868-869-870 | `cmdfound --yes offline` (tres veces) | 209 |
| 941-942 | `cmdfound --yes twin` | 123 |
| 1235-1236 | `setsid cmdfound tiny` | 218 |
| 975-978, 1022-1023, 1303-1304 | `aqua probe`, `github probe`, `pkgx probe` | 36 |

**Medido: 1.33 s** en total, y el diff de ejemplo pasa.

**Riesgo.** Bajo. Un error aquí se ve al instante: el status que se compara es el del
`$(...)`, y si alguien lo pone después de otro comando compara el status equivocado.

**Usuarios reales.** Cero efecto.

**¿Se deshace fácil?** Sí.

---

### Opción 7 — Copiar un home ya armado en vez de resolver otra vez

**Qué cambia.** 35 invocaciones del bloque (6.8 s medidos) corren solo para dejar un estado, no
para probar nada: `--yes figlet` tres veces en tres homes de nix-portable, cinco `--yes` para
armar el home de `--list`/`--purge`, y así. Donde el home vuelve a la misma ruta, se puede
copiar en vez de resolver.

```diff
--- a/sh/tests/tools.db
+++ b/sh/tests/tools.db
@@ -1876,10 +1876,13 @@
 #nix-portable gone too
 nph8="$(pwd)/nph8"; mkdir -p nph8/channels/github/cache nph8/channels/nix-portable && cp nph/channels/github/cache/DavHau_nix-portable_.json nph8/channels/github/cache/ && cp -R nph/channels/nix-portable/index nph/channels/nix-portable/nixpkgs nph/channels/nix-portable/needs nph8/channels/nix-portable/
 CMDFOUND_CHANNELS="${npch}" CMDFOUND_HOME="${nph8}" cmdfound --yes figlet >/dev/null 2>&1
+#the second home is the first one back, copied to the same path so the
+#launchers and the store paths written into it still name where they are:
+#installing figlet again would resolve, fetch and place it a second time
+cp -R nph8 nph8keep
 CMDFOUND_CHANNELS="${npch}" CMDFOUND_HOME="${nph8}" FAKE_NP_LOG="$(pwd)/nppurgelog" cmdfound --yes --purge > nperr 2>&1
 test ! -e nppurgelog && test X"$(grep -c 'could not give back' nperr)" = X"0" && test ! -e nph8
-mkdir -p nph8/channels/github/cache nph8/channels/nix-portable && cp nph/channels/github/cache/DavHau_nix-portable_.json nph8/channels/github/cache/ && cp -R nph/channels/nix-portable/index nph/channels/nix-portable/nixpkgs nph/channels/nix-portable/needs nph8/channels/nix-portable/
-CMDFOUND_CHANNELS="${npch}" CMDFOUND_HOME="${nph8}" cmdfound --yes figlet >/dev/null 2>&1 && rm -rf nph8/channels/nix-portable/tool
+cp -R nph8keep nph8 && rm -rf nph8keep nph8/channels/nix-portable/tool
 CMDFOUND_CHANNELS="${npch}" CMDFOUND_HOME="${nph8}" FAKE_NP_LOG="$(pwd)/nppurgelog" cmdfound --yes --purge > nperr 2>&1
 test ! -e nppurgelog && test X"$(grep -c 'could not give back' nperr)" = X"0" && test ! -e nph8
 #and one rm removes the channel, although nix leaves what it adds without write
```

**Qué se pierde.** Nada de cobertura en el caso de arriba: la segunda instalación no probaba
nada que la primera no probara. Pero hay un límite duro: los launchers y las rutas del store
que quedan escritas dentro del home son absolutas, así que la copia solo sirve si vuelve a la
misma ruta. Copiar `nph` a `nph2` no funciona; copiar `nph8` a `nph8keep` y devolverlo a `nph8`
sí.

**El ahorro, medido** en el caso que hice: la línea que reinstalaba figlet costaba 717 ms y la
que rearmaba el fixture 13 ms; las dos copias cuestan 25 y 28 ms. **-677 ms, y el bloque
pasó.** De las 35 invocaciones de setup, calculo que unas 10 están en la misma situación (el
home vuelve a su ruta): **estimado 2-4 s.** Las otras crean homes nuevos y no se pueden copiar.

**Riesgo.** Medio. Si alguien copia un home a otra ruta, los tests que siguen pasan igual pero
prueban un home que apunta a un lugar que ya no existe; eso es un test que miente. Lo mismo si
el snapshot se toma antes de lo que el test siguiente necesita.

**Usuarios reales.** Cero efecto.

**¿Se deshace fácil?** Sí, caso por caso.

---

### Opción 8 — Asserts con builtins en vez de `$(… | awk …)`

**Qué cambia.** El shell del bloque arranca 3,884 procesos propios (medido), casi todos en
asserts de la forma `test X"$(cmd | awk ...)" = X"..."`. Muchos se pueden leer con builtins.

```diff
--- a/sh/tests/tools.db
+++ b/sh/tests/tools.db
@@ -1137,7 +1137,7 @@
 cath="$(pwd)/cath"
 CMDFOUND_HOME="${cath}" cmdfound -n catname > catout 2> caterr
 grep "no catalog here has 'catname'; fetching fastcat and slowcat at once" caterr >/dev/null
-test X"$(tail -1 catout | awk '{print $2}')" = X"fastcat:catname@1.0"
+while read -r catl; do catlast="${catl}"; done < catout; set -- ${catlast}; test X"${2}" = X"fastcat:catname@1.0"
 grep "fastcat has 'catname'; slowcat paused, to go on when needed" caterr >/dev/null
 #paused is not failed, and is not reported as a catalog that could not be had
 test X"$(grep -c 'not fetched' caterr)" = X"0"
```

**Qué se pierde.** Nada de cobertura, y bastante legibilidad: la versión con `while read` y
`set --` dice mucho menos a quien la lee que `tail -1 | awk '{print $2}'`. En una suite cuyo
valor está en que cada línea se lee como una afirmación, eso cuenta.

**El ahorro.** Los 3,884 procesos del shell del bloque son ~5-6 s a 1.4 ms cada uno; capturar
la mitad sería **estimado 2-3 s.** No medí el bloque completo con este estilo; el diff de
ejemplo pasa.

**Riesgo.** Bajo en lo técnico (falla al instante si se equivoca el campo), alto en lo que
importa: nadie va a querer leer 200 asserts así, y el próximo test se escribirá del modo viejo.

**Usuarios reales.** Cero efecto.

**¿Se deshace fácil?** Sí, línea por línea.

---

### Opción 9 — Partir el core para parsear menos: descartada

Arrancar el core cuesta 5.35 ms medidos, de los cuales ~4.5 ms son parsear los 150 KB del
archivo; por las 330 invocaciones del bloque son ~1.5 s. Sacar el código frío (`-U`, `--purge`,
`--list`, la lectura de rc de curl y wget) a un archivo que se hace `.` cuando se necesita
ahorraría parte de eso.

**No la recomiendo y no escribí el diff**, porque choca con dos cosas del diseño: `cmdfound -U`
se actualiza descargando **un** archivo, y el bloque prueba precisamente eso (`updc/cmdfound -U`
y `updw/cmdfound -U`), y los canales se encuentran "al lado del archivo mismo, como se haya
llegado a él" (el test del link `./srl`). Un segundo archivo obligatorio cambia las dos cosas.
Si se hiciera, el ahorro es **estimado ~0.7 s** en el bloque y ~3 ms por corrida de usuario.

---

### Opción 10 — El mismo recorte de forks dentro de los canales

**Qué cambia.** Los canales tienen el mismo patrón que el core. `binstall` es el más caro: 49
corridas directas en el bloque, ~60 procesos cada una, 2,959 procesos en total (medido). Este
es un sitio de ejemplo, dos `awk` para partir una lista en "primera línea" y "el resto":

```diff
--- a/sh/tools/cmdfound.d/binstall
+++ b/sh/tools/cmdfound.d/binstall
@@ -337,8 +337,14 @@
     #every target is asked about at once, and the first that has a build is taken
     _bd__answers="$(_heads ${_bd__urls})"
     for _bd__t in $(_targets); do
-        _bd__answer="$(printf "%s\\n" "${_bd__answers}" | awk 'NR == 1')"
-        _bd__answers="$(printf "%s\\n" "${_bd__answers}" | awk 'NR > 1')"
+        _bd__answer="${_bd__answers%%
+*}"
+        case "${_bd__answers}" in
+            *"
+"*) _bd__answers="${_bd__answers#*
+}" ;;
+              *) _bd__answers="" ;;
+        esac
         case "${_bd__answer%% *}" in
             200) ;;
             404|410) continue ;;
```

**Qué se pierde.** Nada de cobertura. Legibilidad otra vez: la versión con `case` y
`${var#*\n}` es más fea que dos `awk`.

**El ahorro.** No lo medí como bloque: el diff pasa, pero un sitio no mueve la aguja. Los 10
canales juntos arrancan 11,498 procesos dentro de sus propias corridas (medido); recortar un
tercio sería **estimado 3-5 s**, y hay que hacerlo canal por canal.

**Riesgo.** Medio: es código que corre contra la red de verdad en producción y los tests lo
cubren con stand-ins. Un error de comillas en el manejo de newlines se ve como un canal que no
encuentra un build.

**Usuarios reales.** Sí, en la misma medida que la opción 2: menos procesos por consulta al
canal.

---

## 3. Tabla resumen

Segundos sobre la referencia de 86 s. "Medido" significa que corrí el bloque completo o el
experimento que dice la sección; "estimado" es aritmética sobre algo medido.

| # | opción | segundos | medido/estimado | riesgo | ayuda al usuario | recomendación |
|---|---|---|---|---|---|---|
| 2 | menos forks en el core | 7 medidos con 23 líneas; 15-20 completo | medido + extrapolado | medio, falla en verde/rojo | sí, -30% procesos por resolución | hacerla, por partes |
| 1 | grupos en paralelo | 50-60 (aterriza en 25-35 s) | estimado sobre escalado medido | alto, intermitencias | no | solo si el objetivo es 25-30 s |
| 3 | carrera sin poll de 100 ms | ~3 | medido | bajo (20 ms) / medio (fifo) | leve, hasta 100 ms | hacerla |
| 7 | copiar homes en vez de resolver | 0.7 medido; 2-4 completo | medido + estimado | medio, un test puede mentir | no | hacer los casos de misma ruta |
| 10 | menos forks en los canales | 3-5 | estimado | medio | sí | después de la 2 |
| 8 | asserts con builtins | 2-3 | estimado | bajo técnico, alto de estilo | no | no, salvo en asserts calientes |
| 5 | directorio de canales por test | 2-3 | estimado sobre medición por resolución | medio-alto, adelgaza cobertura | no | solo en las secciones más pesadas |
| 4 | esperas fijas más cortas | 1.9 | medido | alto de intermitencia | no | solo con espera por señal, no por reloj |
| 6 | una corrida, dos asserts | 1.3 | medido | bajo | no | hacerla |
| 9 | partir el core | 0.7 | estimado | choca con `-U` y con `./srl` | ~3 ms | descartada |

Suma de todo lo que no es la opción 1: 15-20 (op. 2) + 3 + 2-4 + 3-5 + 2-3 + 2-3 + 1.9 + 1.3 =
**35 s con los valores medios y 41 s en el extremo optimista**, o sea el bloque entre 45 y 52 s
sin tocar el paralelismo. Ojo: las opciones no se suman limpio, porque varias tocan los mismos
procesos (la 2 y la 5 comparten las resoluciones del directorio compartido, la 3 y la 4
comparten sleeps); por eso el escenario B se lee como un rango y no como un número.

---

## 4. Tres escenarios

La aritmética, con los valores medios de cada opción: op2 17 s (15-20), op3 3 s, op4 1.9 s,
op5 2.5 s, op6 1.3 s, op7 3 s (2-4), op8 2.5 s, op10 4 s (3-5). Todo junto sin paralelismo son
35 s de los 86, o sea 51 s; en el extremo optimista de cada rango, 41 s, o sea 45 s.

```
Donde aterriza cada escenario (base medida 86 s; las barras son proporcionales)
                                                  0s        30s       60s       90s
hoy, 9a278d6                                      [####################### 86 s]
A  op2 parcial + op3 + op6 + op7                  [################# 64 s]
B  A + op2 completa + op10 + op5 + op8 + op4      [############ 45-52 s]
C  B + op1 (8-10 grupos en paralelo)              [####### 25-35 s]
Los tres son estimados: A tiene 7 s medidos de op2, 3 de op3, 1.3 de op6 y 0.7 de op7; lo demas
es aritmetica sobre patrones medidos.
```

### Escenario A — ~64 s, sin riesgo nuevo

**Qué lleva:** la opción 2 en lo que ya medí (23 sitios, -7 s medidos) más la misma receta en
`_resolve`, `_ask` y `_locate`, que son los siguientes por forks (estimado -8 s); opción 3 con
poll de 20 ms (-3 s medidos); opción 6 (-1.3 s medidos); opción 7 en los casos donde el home
vuelve a su ruta (-2 a -4 s, uno medido en -0.7 s).

**Qué pierde la suite:** nada de cobertura. 13 líneas dejan de correr el comando dos veces, un
par de homes se copian en vez de rearmarse, y el core usa tres variables globales nuevas.

**Intermitencia:** la misma que hoy. Nada aquí depende del reloj.

**Confianza:** alta en 11 s de los 22 (medidos), media en el resto.

### Escenario B — 45-52 s, se paga con estilo y con cobertura incidental

**Qué lleva:** todo A, más la opción 2 completa (~100 sitios en el core), la opción 10 en los
tres canales más caros (`binstall`, `alpine`, `github`), la opción 5 en las secciones más
pesadas del resolver, la opción 8 en los asserts más calientes y la opción 4 con espera por
señal en vez de sleeps más cortos.

**Qué pierde la suite:** la cobertura incidental de "veintidós canales dicen que no" en las
resoluciones que pasen a directorio estrecho (hay que escribir ese caso una vez, aparte);
legibilidad en unas 130 líneas del core y de los canales, y en los asserts que se reescriban
con builtins.

**Intermitencia:** igual que hoy si la opción 4 se hace con espera por señal. Si se hace con
sleeps de 0.3 s, aparece la primera intermitencia de la suite.

**Confianza:** media. Solo 12 de los ~35 s están medidos; el resto es aritmética. El rango
45-52 s es justamente la diferencia entre el extremo optimista y el conservador de las
estimaciones.

### Escenario C — 25-35 s, cambia el contrato de la suite

**Qué lleva:** todo B, más partir el bloque en 8-10 grupos independientes y un corredor que
corra varios a la vez.

**Qué pierde la suite:** el bloque deja de ser un script lineal donde cada línea puede usar lo
que dejó la anterior; los fixtures compartidos se duplican o se mueven a un prólogo por grupo;
`flcheck`/`flsame` tienen que vivir en un lugar común; el orden de las corridas deja de ser
determinista y un fallo puede aparecer en distinto momento en dos corridas.

**Intermitencia:** es el escenario que la introduce. Medí que el mismo bloque pasa de 82 a 141 s
cuando el load llega a 6, y correr 8 grupos produce ese load; los tests que dependen del reloj
(la carrera de catálogos con stand-ins a 50 ms por byte, los `kill`/`wait`, el Ctrl-C) son los
primeros que se van a poner nerviosos. Con la opción 4 en su versión de sleeps cortos, peor:
márgenes chicos con carga alta.

**Confianza:** baja en el número exacto; alta en la forma, porque el escalado de esta máquina
(x1.0, x1.67, x2.4, x3.5 para 1, 2, 4 y 8 flujos) está medido.

---

## 5. Lo que hay que decidir

1. **¿Cuál es el objetivo real: el reloj del bloque o el costo por resolución?** Son cosas
   distintas y solo la opción 2 mejora las dos. Si el objetivo es que la suite no moleste al
   trabajar, 60 s sin riesgo (escenario A) alcanza; si el objetivo es que `cmdfound` responda
   más rápido a un usuario, la opción 2 completa es el trabajo, no el paralelismo.
2. **¿Se acepta la variable global (`value`, `field`, `channels_dir`) en el core?** Es el precio
   de estilo de la opción 2 y afecta ~100 sitios. Sin eso, la opción 2 se queda en las
   extracciones `awk` (unos 4-5 s) y el resto del plan pierde su pata más firme.
3. **¿Se acepta perder la cobertura incidental de los 23 canales?** Si la respuesta es no, la
   opción 5 se cae y el escenario B queda en ~48 s.
4. **¿Se acepta que la suite pueda volverse intermitente?** De eso dependen las opciones 1 y 4.
   Mi recomendación: la 4 solo con espera por señal (fixture nuevo), no con sleeps más cortos;
   y la 1 solo si el objetivo es 25-30 s y aceptas pagar la partición de fixtures.
5. **¿Quién corre la suite y cuándo?** Si es CI en una máquina dedicada, el paralelismo es
   mucho más seguro que aquí, donde ya hay dos jekyll y varias sesiones peleando por CPU. Yo
   medí todo en esta máquina; en una dedicada los números de reloj bajan y el escalado sube.
6. **Qué NO hay que hacer todavía:** la opción 9 (choca con `-U` y con `./srl`) y la opción 8
   más allá de un puñado de asserts calientes (el costo de lectura no lo paga).

---

## Apéndice — Cómo se midió

- **Procesos:** namespace de PIDs propio (`unshare --user --map-current-user --pid --fork
  --mount-proc`) y la diferencia del último PID, leída del último campo de `/proc/loadavg`
  (el `read` de dash solo saca el primer byte de `/proc/sys/kernel/ns_last_pid`).
- **Reloj por línea:** una marca antes de cada línea del bloque, escrita a un fifo que un
  proceso aparte le pone la hora; eso no arranca procesos.
- **Costo por invocación:** un envoltorio `cmdfound` en el `PATH` que cronometra y cuenta PIDs;
  cronometró 305 de las 330 invocaciones (las 25 restantes son la sección udocker, que pone su
  propio `PATH` delante, `./srl` y los dos `-U`).
- **Procesos por función:** un tracer en C con ptrace (eventos de fork y exec) más una marca
  `[ -r /__fnmark/NOMBRE ]` en la entrada y la salida de cada función de una copia del core,
  filtrada con seccomp para que solo esa llamada pare al tracer. La copia arranca exactamente
  los mismos procesos que el original (184 y 225, iguales).
- **Costo de un proceso y escalado:** lazos de dash de 1,000-2,000 vueltas, medidos con
  `date +%s%N`.
- **Stand-ins y no stand-ins:** todas las corridas del bloque son contra los stand-ins de
  `sh/tests/cmdfound.d` (ver 1.2), así que los procesos y el reloj son del core y de los
  canales, sin red ni daemon. Los únicos números de programas reales son los de costo de un
  proceso y escalado (dash, gawk, sed, grep, cat de la máquina) y la auditoría de
  `~/.wget-hsts` que cita 9a278d6, que es de otro agente y con una descarga real.
- **Todo lo medido aquí se corrió en esta máquina (WSL2, 8 hilos) con load ajeno entre 0.3 y
  6.9, y con el bloque en su base 9a278d6**, que a la hora de escribir esto ya no es la punta de
  `integrate/channels` (la rama siguió: 82db160). Los diffs siguen aplicando sobre 9a278d6; si
  la rama movió esas líneas, el patrón es el mismo pero los números de línea no.
- **Los scripts de medición** quedaron en `scratchpad/test-cost-work` de la sesión, que es
  temporal: si quieres repetir algo, dilo y lo dejo en un lugar estable.
