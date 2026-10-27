# cmdfound: decisiones

Estado al 2026-09-17:
- **master:** canales github, aqua, pkgx y AM.
- **`integrate/channels`** (sin subir, 3e3b8a5): cmdfound con home `~/.cmdfound`, conda-forge (con collect), nix-portable, binstall (opción
  B), alpine, el reparto a runtimes, docker, udocker, S2, S5, S6, arreglos de channels.conf y
  `CMDFOUND_BYTES`, badges coherentes (`none` de un canal, `-n` igual a la pregunta), un solo lector de
  flags lineal para docker/udocker. Todo integrado, más la auditoría real (fugas), catálogos anunciados y wording. Bloque: 54.820 procesos (antes 64.562).
- **Siguiente:** la estabilización. x-cmd, diferido.

Código en `sh/tools/cmdfound`, canales en `sh/tools/cmdfound.d/`, pruebas en `sh/tests/tools.db`;
este documento vive fuera del repositorio. Plan de contenedores (inglés; contrato detallado, pasos S0–S9,
riesgos): `~/cmdfound-containers-m1-plan.md`; si choca con este documento, gana este. Va en español;
código, opciones, rutas y salidas, en inglés.

## Qué es
Ante `command not found`, averiguar qué gestor tiene el programa y si compensa instalarlo para usarlo una
vez es trabajo manual. El repositorio carga 33 `.dockerized`, una receta por programa; crecer a cientos está
descartado, porque ya hay catálogos públicos con miles. cmdfound es un resolutor: dado un comando que
esta máquina no tiene, dice quién puede ejecutarlo y toma el camino más rápido hasta ahí.

    cmdfound [OPTION]... [CHANNEL:]PACKAGE[@VERSION] [ARGUMENT]...
      -n, --dry-run            el camino que tomaría, con sus alternativas
      -a, --apropos words      busca por lo que hace, en los catálogos locales
      -i, --index-update [ch]  catálogos y herramientas al día; uno solo si se nombra
      -l, --list               lo que ya está aquí, con la ruta de cada programa
      -b, --bin name           el programa dentro del paquete, cuando difiere
      -p, --purge [spec]       quita una colocación, o todo
      -y, --yes                se salta la confirmación antes de gastar bytes
      -L, --latest             resuelve de nuevo en vez de usar la decisión
      -e, --ephemeral          raíz desechable, borrada al salir
      -U, --update             actualiza cmdfound

## Decisiones vigentes
Todas son del dueño o aceptadas por él; si dos chocaban, aquí queda la más reciente.
### Máximas
- Nunca eleva privilegios en el anfitrión ni usa sudo: lo que pide root va dentro de un contenedor. Nunca
  compila (nix `--max-jobs 0`, binstall sin compilar). Telemetría apagada.
- `rm -rf channels/<ch>` quita el canal completo y le gana a cualquier variable del usuario. Única
  excepción: docker, que es de sistema.
- Bajo ninguna circunstancia modifica un archivo de configuración del usuario (`channels.conf`, rc files,
  `~/.docker/config.json`…): los lee, nunca los escribe, ni él ni las herramientas de sus canales.
- Nativo (sin root ni runtime de un ecosistema) antes que dockerizado, siempre: la clase ordena antes que
  el tiempo. Gestores dependientes (npm, PyPI, apt, apk, brew…) solo dentro de dockerizado.
- Nunca adivina: un nombre suelto solo se resuelve con un mapa comando→paquete honesto; ambiguo, menú.
- Lee catálogos ajenos. Nunca escribe recetas de paquete ni publica o replica catálogos.
- La primera corrida toma el camino más rápido; la segunda es indistinguible de tenerlo instalado
  (`exec` directo, sin red, pregunta ni mensajes).
- Quien descarga, verifica: `verified` (cmdfound lo bajó y el checksum publicado cuadró), `none` (sin
  contra qué comprobar), `via <canal>` (responde su herramienta). Un checksum que no cuadra es el único
  bloqueo, y es regla estricta (dueño, 2026-09-17): si hay checksum y no cuadra, algo está mal y no se
  instala nada, sea un programa o una herramienta que baja cmdfound. Sin checksum, se instala y se marca `none`
  (dueño). Las dos cosas las cubren pruebas propias. cmdfound no verifica por un gestor; mantiene al día cada herramienta que baja.
- Costes honestos: desconocido + algo = al menos ese algo (el total dice su piso, que es el aviso que
  pidió el dueño para nix); estimado + algo = estimado. Sin límites de bytes ni
  de saltos: se muestra el coste y decide el usuario.
- Ningún tamaño va escrito a mano (dueño, 2026-09-17): o se averigua en la corrida (HEAD, índice), o queda
  desconocido, para no tener que actualizarlo. Las descargas de catálogo de la primera vez también se
  anuncian, como línea `once=` propia, con lo que el índice del canal diga y `-` cuando no lo diga. El
  aviso de antes de bajarlo dice su tamaño, averiguado con un HEAD sobre la url del catálogo, sin bajar
  nada: `no local catalog has 'figlet'; fetching alpine's catalog (2.5 MB)`. Una sola palabra, "catalog",
  en todo lo que lee el usuario: la línea de una vez dice `first catalog alpine` y `first tool …`. El
  verbo `index` del contrato se queda; si `--index-update` pasa a `--catalog-update` está por decidir.
  Un catálogo ya bajado para poder responder no aparece en la pregunta ni en `-n`, y no suma nada
  (dueño: confundía; 9f9c150 y 2fc30a0, que quitaron la línea y el campo `spent` que la sostenía). Lo
  que sí está por venir (imagen, motores) sigue sumando. Lo que costó bajarlo se guarda igual en las
  mediciones del canal, que es de donde sale la próxima estimación.
  Única excepción: nix avisa que su primera vez baja mucho, aunque no se sepa el total exacto; lo que se
  puede medir (herramienta 64,9 MB + nixexprs 39,9 MB) es el piso y los paquetes van como desconocidos.
  Hecho en 1dcb8ab y 82db160; los únicos tamaños escritos a mano eran los del arranque de nix y ya no
  están. Quedan dos tiempos semilla (docker 1200 ms, udocker 250 ms) que la primera medición reemplaza.
- Cuida la cuota de la API de GitHub: `GITHUB_TOKEN`/`GH_TOKEN` solo si el usuario los exportó, solo
  hacia api.github.com y por stdin a curl. Nunca se busca un token.
- Un canal que no se pudo consultar no dice "no": dice que no se sabe.
### Configuración del usuario
- Herramienta de canal (aqua, pkgx, appman, micromamba, nix-portable, cargo-binstall, udocker): su HOME
  es el canal y nunca lee rc files del HOME del usuario. Sus variables pasan (`AQUA_*`, `PKGX_*`,
  `NIX_CONFIG`, `NIX_USER_CONF_FILES`, `NP_*`, `CONDA_*`, `BINSTALL_*`…): quien ya la usa, sigue igual.
- Pasan también las que apagan verificación (`AQUA_DISABLE_COSIGN`/`_SLSA`/`_POLICY`,
  `MAMBA_SSL_VERIFY=false`, `*_SAFETY_CHECKS=disabled`, `require-sigs` de nix): problema del usuario.
- Pasan `AQUA_GOOS`/`GOARCH` y `CONDA_SUBDIR` (otra plataforma es válido; `--list` muestra la ruta),
  `AM_EXTRA_SOURCES`, `amdeps_on` y `APPSDB` (el índice del canal am sigue a `APPSDB`).
- Solo se pisan las de ubicación, que pondrían estado fuera del canal (`MAMBA_ROOT_PREFIX`,
  `CONDA_PKGS_DIRS`, `CONDA_ENVS_*`, `CARGO_HOME`, `NP_LOCATION`, `NP_RUN`, `NIX_REMOTE`, `NIX_STORE*`,
  `NIX_STATE_DIR`, la línea `store` de `NIX_CONFIG`, `UDOCKER_DIR`…). Se quitan `MAMBA_DRY_RUN` y
  `MAMBA_DOWNLOAD_ONLY` (instalación vacía en silencio). Las decisiones del dueño le ganan a la variable
  que choque: nunca compilar, nunca sudo, sin telemetría.
- Variables que apuntan a un archivo de configuración: pasan `AQUA_GLOBAL_CONFIG`, `AQUA_POLICY_CONFIG`,
  `WGETRC` (para AM) y `NIX_USER_CONF_FILES`. Se quitan `MAMBARC`, `CONDARC` y `ZDOTDIR`, porque mueven
  estado fuera del canal.
- Plomería (curl, wget, tar, unzip, gzip, sqlite3): ningún rc cambia la salida que cmdfound lee.
  `curl -q` primero, `wget --no-config`, `sqlite3 -init /dev/null`; `TAR_OPTIONS`, `UNZIP`, `UNZIPOPT`,
  `GZIP`, `BASH_ENV` y `CDPATH` vacías.
- Red transparente: de `~/.curlrc`/`~/.wgetrc` solo se leen `proxy`, `proxy-user`, `noproxy`, `cacert`,
  `capath` y `proxy-cacert`; el núcleo las exporta una vez como variables estándar (`https_proxy`,
  `SSL_CERT_FILE`…) sin pisar las del usuario, y curl usa `-q -K <filtrado>`. `proxy-cacert` no tiene
  variable: se avisa si el proxy es https. Las variables de red y un token exportado pasan.
- docker es de sistema: su CLI usa el HOME real, `~/.docker/config.json`, logins, credential helpers y
  contextos. Lo que cmdfound guarda de docker sigue en `channels/docker`.
- udocker no: todo lo suyo queda en su canal. Usa las credenciales de docker con un keystore (modo 600)
  generado en el canal en cada llamada desde `~/.docker/config.json` (o `DOCKER_CONFIG`), traduciendo
  claves; las entradas con credential helper se saltan con aviso.
### Canales
- Un canal es un ejecutable en `cmdfound.d/` y un directorio `channels/<ch>/`; declara sus alias (`gh`
  es github) y la decisión se guarda bajo el nombre real. `needs=`: lo que un canal necesita para leer su
  índice, o un runtime para correr, se obtiene con cmdfound mismo.
- `channels.conf` (la lista de canales) se queda, junto a los canales y no en su lugar.
  `CMDFOUND_CHANNELS` sustituye el directorio de canales (así usan falsos las pruebas).
### Contenedores (dockerizado)
- Arquitectura B: runtimes (docker, udocker) más catálogos (alpine primero). El catálogo da `recipe`; el
  runtime baja la imagen, instala como root sin montajes, persiste, escribe el lanzador y responde
  `collect`. Descartadas A (catálogo × runtime: duplica catálogos) y C (canal `oci`: muestra un runtime).
- Un camino por runtime disponible: `alpine:figlet` ofrece ambos; `docker:alpine/figlet` fija docker.
- Al usuario se le dice "dockerized"; por dentro sigue `confines=`.
- Dentro de dockerizado gana el más rápido por corrida (udocker, si están los dos); luego, el de una vez.
- Sin docker se avisa `docker is not available, using udocker`; otra indisponibilidad de runtime solo
  sale en `-n` o cuando nada puede correr el programa.
- La pregunta no muestra el tiempo por corrida ni aviso de entorno; `environment=` sale del contrato.
- cmdfound es transparente con el runtime: pasa los flags del usuario a `docker run` y `udocker run`,
  después de los suyos y antes de la imagen, con `CMDFOUND_DOCKER_FLAGS` y `CMDFOUND_UDOCKER_FLAGS`.
  Se leen en cada corrida, con comillas como en el shell y sin `eval`.
- Aviso al correr en `/` fuera de HOME y `/tmp`: se queda.
- El programa ve el HOME real y el entorno como en nativo, menos las variables con rutas del anfitrión
  (`PATH`, `LD_*`…). Dockerizado es para instalar como root sin tocar el anfitrión, no un sandbox.
- cwd: se montan HOME y `/tmp`, con sus destinos físicos (enlazados funcionan). Desde otro directorio el
  programa corre en `/`, sin montar el cwd y con una línea de aviso; nunca se niega. Los sockets
  nombrados por variables (`SSH_AUTH_SOCK`) son el único montaje fuera de HOME y `/tmp`.
- Se instala una vez y se persiste (una colocación por paquete en el primer hito), nunca en cada corrida.
- docker: `--network=host`; demonio inalcanzable o rootless → `unreachable`, nunca sudo; `--ephemeral`
  no usa docker por ahora.
- Imágenes de docker, única excepción a "todo dentro de `CMDFOUND_HOME`": labels
  `io.cmdfound.{home,catalog,package,version}`; solo `--purge` barre las de este home que ningún
  registro nombra y las bases que cmdfound bajó y nadie usa. Nunca automático: el demonio es compartido.
- udocker: herramienta del sdist de PyPI (sha256 publicado); motores con insignia `none`; python3 por
  `needs=`. Se instala la primera vez que hace falta o con `cmdfound udocker:udocker …`; se quita con
  `rm -rf <CMDFOUND_HOME>/channels/udocker`.
- Docker Hub, con HEAD para los digests. GPG, mirror y `describes` por paquete: hasta Debian.
- Imagen base = catálogo (alpine → apk, debian → apt). Una tabla de comandos de gestores, si hiciera
  falta: upt (Apache-2.0) se puede transcribir; pacaptr (GPL-3.0) solo como programa aparte.
### Núcleo
- Spec = (catálogo, identificador, versión), p. ej. `aqua:jqlang/jq@1.6`. Un nombre suelto vale si lo
  reclama un solo programa. Ambiguo: con terminal, menú recordado bajo el nombre escrito; sin terminal o
  con `--yes`, lista candidatos y sale con 127.
- `--yes` solo se salta la confirmación de gastar bytes; nunca elige por el usuario.
- Coste, en orden: clase, tiempo estimado en esta máquina (µs; en dockerizado, primero por corrida),
  saltos. Solo cuenta lo que falta: lo colocado cuesta 0; una herramienta que falta suma bytes y tiempo.
- Tiempos por paso y canal en `channels/<ch>/timings`. Estimado = costo fijo + costo por byte, de las
  diez últimas veces del paso. Sin registro, 1 MiB/s con `~`; sin bytes, la duración media; sin nada,
  desconocido y último en su clase. `timing=` separa pasos para que un costo de una vez (arranque de
  nix, motores de udocker) no infle el promedio de instalación.
- Primera vez: los catálogos que faltan se bajan a la vez y se leen según llegan. Gana el primero con el
  nombre; los demás se pausan con lo bajado y siguen luego con `curl -C -` (aqua, bajo la etiqueta del
  registro). Una respuesta dockerizada no para a los nativos (los que faltan se bajan antes de
  aceptarla) y solo pausa a los dockerizados; una nativa pausa a todos. Un dry run también los baja.
- La pregunta (tamaño, tiempo, insignia, clase, herramienta a traer, total) va por `/dev/tty`; sin
  terminal no se baja nada y se sugiere `--yes`. Mensajes por stderr; stdout es del programa. 127 = no se
  ejecutó nada; cualquier otro código es del programa.
- Una decisión (`cache/`: spec → programa) registra su colocación; si la colocación ya no está
  (`rm -rf channels/<ch>`, `--purge`), deja de ser ejecutable y se vuelve a tomar. Las versiones
  conviven en `by/<pkg>/<ver>` y se llaman por spec, sin estado.
- `--purge` quita enlaces, recoge `store` y `members` que nadie referencia y pide `collect` a los canales
  `collects=yes`. Tamaños: un canal con store propio reporta el suyo; el resto, un solo `du` sobre todos
  sus miembros. "Liberado" es lo que de verdad desaparece.
- `--index-update`: sin canal, todos los catálogos y herramientas presentes; con canal, solo ese. Una
  herramienta nueva se baja, se verifica, `tool/current` la apunta y la vieja se borra; una ausente
  espera a hacer falta, cuando su coste se puede preguntar. Si sin canal trae también catálogos nunca
  bajados se decide al final, con números.
- `--apropos` no usa red. Hoy avisa cuando un catálogo tiene más de una semana, pero **ese umbral es
  arbitrario**: lo puso un agente en `2545c1c` sin razón, y aquí se anotó sin cuestionarlo. Pendiente del
  dueño (2026-09-22): decir la edad sin umbral, quitar el aviso, o un ritmo por canal.
- Nada bloquea hoy dos obtenciones simultáneas del mismo paquete; el arreglo es del núcleo, no del canal.
- Forma: funciones arriba, `main` abajo y ninguna función después. `main` lee opciones, despacha las
  acciones sueltas y luego es solo `_canonical`, `_remembered`, `_resolve`, `_locate`, `_ask`, `_obtain`,
  `_remember`. Cada paso recibe argumentos e imprime `key=value` (comentario `$1 =>` y "Prints"), leído
  con `_value`/`_values` en shell puro, sin `awk`; si falla, `NOTHING_RAN` (127). La sección `run` no
  lee más globales que `PROGNAME` y `CMDFOUND_NO_MANAGER`.
- Estilo POSIX: `[ X"$a" = X"$b" ]`, `printf` antes que `echo`, variables con llaves, locales `_fn__var`.
- Por construir: `--default` (enlace `default` en `by/`); `--shim spec --as jq16` (atajo en `bin/`, que
  nunca entra solo en el PATH ni tapa un comando); insignia mínima y tamaño máximo, apagados por defecto;
  el gancho `eval "$(fuck --hook bash)"` (`command_not_found_handle` → fuck → cmdfound): solo
  interactivo (según `$-`), argumentos intactos, fuck no sorbe stdin, marca de recursión solo para esa
  invocación, 127 = "sigue tú"; cmdfound no sabe nada del corrector.
- Fuera de alcance: tocar el `bashrc` de nadie; shells sin gancho (`sh`, `dash`), donde se invoca por
  nombre; Windows.
### Pruebas
- Bloque `cmdfound` en `sh/tests/tools.db`, sin red, con canales falsos y dobles de aqua, pkgx y AppMan
  en `sh/tests/cmdfound.d`; los dobles de contenedores, en el plan. Solo comportamiento externo (qué
  imprime, con qué código sale, a qué resuelve), independiente de la máquina.
- Cada prueba trae su costo: tiempo del bloque antes, después y la prueba sola.

## Contrato de canal
    meta                  aliases= kind= confines= describes= manager=<spec> needs= collects=yes
    probe NAME [VER]      0 version= bytes= estimate= badge= package= requires= [image= image_bytes=]
                          1 no lo tiene  2 unreachable=<por qué> [needs=index]  3 candidate=...
    probe CAT/PKG VER     runtime, con CMDFOUND_IMAGE: 0 run_ms= requires= once=...  2 unreachable=
    locate PKG VER [BIN]  url= format= bin= sha256=
    recipe PKG VER [BIN]  catálogo: 0 image= install= bin=  1 failed=
    obtain PKG VER [BIN]  0 program= asset= member=... timing=...  1 failed=  2 unreachable=
    index                 packages= names= bytes=
    search WORDS...       name<TAB>...<TAB>description
    collect               collects=yes: borra lo que ya nada sostiene; 0 freed=
    size PKG VER          runtime, opcional: 0 bytes=; 1 = contar con du

- `kind=`: `artifact` (por defecto); `catalog`, nunca camino por sí solo (da uno por runtime); `runtime`,
  sin nombres propios salvo su herramienta.
- `once=<step>|<label>|<bytes|->|<badge>`: saltos de una vez (`setup`, `image`), etiquetas sin espacios,
  `|` ni `;`. `timing=<step>:<bytes|->:<ms>`: uno por paso (`index`, `tool`, `fetch`, `install`, `setup`,
  `image`, `run`), en vez de la línea de toda la llamada.
- `collect` nunca es automático, solo desde un purge; `CMDFOUND_COLLECT=all` en un purge completo.
- Línea de camino, 14 campos (la escribe `_probe_emit`; solo `_path_field` sabe cuál es cuál): key,
  channel, version, bytes, badge, confines, describes, package, requires, estimate, marginal, ms, once,
  run. Key = clase, run, ms, saltos.
- Variables: `CMDFOUND_CHANNELS` (directorio de canales), `CMDFOUND_REQUIRED` (herramienta con la que
  instala `obtain`), `CMDFOUND_NO_MANAGER` (canales sin herramienta: se les pregunta sin ella y se dice
  por qué). Las de contenedores (`_RUNTIME`, `_IMAGE`, `_RECIPE`, `_COLLECT`, `_EPHEMERAL`…): plan §1.5.

      ${CMDFOUND_HOME:-${XDG_CACHE_HOME:-~/.cache}/cmdfound}/
        channels/<ch>/
          index/  cache/        catálogo y respuestas del canal
          tool/<ver>/           la herramienta, una versión por directorio
          tool/current          enlace al programa; los lanzadores lo apuntan
          store/<sha256>/       lo que cmdfound bajó, por contenido
          by/<pkg>/<ver>        enlace a lo colocado
          members/<pkg>/<ver>   lo que la herramienta guarda para ese paquete
          needs/  run/  timings  inventory
        channels.conf           qué canales preguntar: uno por línea, # y !
        cache/                  decisiones: spec -> programa
        tmp/                    staging; nada sale de aquí sin su digest

## Canales
- **github** (master): releases; cmdfound instala y verifica. Un asset sin sistema en el nombre sirve
  solo si ninguno de la release nombra linux, y si es tar, AppImage o sin extensión.
- **aqua** (master): nombre → repositorio; aqua instala y verifica. Atestaciones apagadas por defecto: la
  primera baja el cli de github (42 MB) sin preguntar.
- **pkgx** (master): un lanzador le pasa cada ejecución a pkgx, que monta el entorno.
- **am** (master): AppMan sin root, con HOME, XDG y `appman_location` en el canal; `nolibfuse` si falta
  libfuse2. "size unknown": el tamaño es cosa de AM; no se consulta la API de github ni sus páginas.
- **conda-forge** (integrate, nativo): micromamba; solo `conda-forge:paquete`, porque nadie publica un
  mapa comando→paquete al día y descargable; conda-suggest queda descartado, abandonado desde 2021
  (dueño, 2026-09-17). Ejecuta directo si no hay nada que activar ni otro entorno
  activo. Hoy borra todas las `CONDA_*`/`MAMBA_*`: a corregir. El 252 de `micromamba run` ante SIGTERM
  es de micromamba y no se tapa.
- **nix-portable** (integrate, nativo): nixos-unstable; mapa `programs.sqlite` con `needs=sqlite3`;
  paquete `nixpkgs.ATTR`, `version=` es la release; raíces GC en `roots/`; nixpkgs viejo se borra al
  cambiar de release; lo que no está en cache.nixos.org no está. Lanzador: bwrap interno, con respaldo en
  corrida a proot o a la entrada normal, `--die-with-parent`. `collect` borra solo lo que nix da por
  muerto y cmdfound registró; aborta si falla la consulta de raíces. Store con escritura del dueño para
  `rm -rf`. "size unknown" siempre, también la primera vez: nix no sabe un tamaño sin evaluar nixpkgs y
  el primer programa va de 10 MB a 1,6 GB. Lo único que se anuncia es el piso, cada parte en su línea:
  la herramienta (64,9 MB, de la release de github) y el nixexprs (39,9 MB, por HEAD). La mediana de
  ~22 MB que se anunciaba antes era un número medido en otra máquina y se quitó en 82db160 (regla del
  dueño: un tamaño anunciado se aprende al correr o queda desconocido); ya no hay revisión semestral.
- **binstall** (integrate, nativo): solo `binstall:crate` (sin mapa descargable); nunca compila; sin
  telemetría. Más cobertura (dueño):
  - Si QuickInstall tiene build, se instala solo de ahí (`--only-signed`); una firma mala falla a la
    vista.
  - Si no hay build, se usa la release del autor (`crate-meta-data`), con "size unknown", ofrecida solo
    si su página HTML muestra un binario de Linux.
  - Las releases de los autores casi nunca vienen firmadas (~37 de ~8.400) y se permiten: la seguridad es
    del usuario, cmdfound solo es transparente (dueño, 2026-09-17). Badge `via binstall` con
    QuickInstall (binstall comprueba la firma) y `none` con la release del autor (nada que comprobar).
  - QuickInstall lo mantiene la organización cargo-bins, la misma de cargo-binstall; construye desde el
    código de crates.io y firma con una clave fija en binstall. Solo cuenta si tiene build de la versión
    actual (~1.930 crates en Linux x86_64).
  - Gana la versión más nueva aunque venga sin firma (opción a, dueño, 2026-09-17): con fd-find,
    QuickInstall tiene 10.4.2 firmada y el autor 10.5.0 sin firma, y se toma 10.5.0 `[none]`.
  - Consultas a la API: 1 con QuickInstall, 1–2 con el autor (4 si el repositorio es un subdirectorio);
    el probe no gasta ninguna. Antes de instalar se lee `rate_limit` (gratis): si no alcanza, falla al
    instante nombrando la cuota y `GITHUB_TOKEN`/`GH_TOKEN`, en vez de esperar 18–63 s y fallar.
  - cargo-binstall se verifica solo con sha256, y basta. Un `GITHUB_TOKEN` exportado pasa y solo va a
    api.github.com.
- **x-cmd** (diferido por el dueño): se retoma después de verificar los comandos por docker; quizá
  pocos catálogos grandes cubran a los chicos. Lo investigado:
  - La herramienta es `latest.tgz`, sin checksum.
  - Catálogo v0.1.3 (973 KB, 598 paquetes, versiones atrasadas).
  - 632 comandos, 114 nuevos tras nix: 24 artefactos con hash, 17 sin hash y ~70 de npm o pip.
  - Su verificación pasa con hash vacío.
  - Decisiones para entonces: el badge de lo que no tiene hash (o que cmdfound baje los artefactos
    él mismo), y si npm/pip cuenta como nativo.
- **alpine** (integrate): catálogo, Alpine 3.22, primero de dockerizado. **docker** y **udocker** (por
  hacer): runtimes; reglas arriba, construcción en el plan.
- **Arch:** después de Alpine. **Runtime `rootfs`** (Alpine, unshare o proot; clase dockerizado): TODO.
- **Candidatos sin decidir:** Debian sid, botellas de Homebrew y Flathub (irían con contenedores), Wolfi,
  Void (sin medir) y los 33 `.dockerized`.

Descartados:
- **soar:** bincache/pkgcache congelados y sin firma; soarpkgs aporta 63 comandos (se revisa si crece).
- **dbin:** el mismo bincache congelado, más pkgforge-go y -cargo, también congelados.
- **Hysp:** archivado.
- **kelp, ubi, eget, stew y similares:** sin catálogo; ya lo cubre github.
- **mise:** 120 comandos nuevos después de nix.
- **arkade:** 204 herramientas, 37 nuevas.
- **webi, binenv, 0install, Spack, pkgsrc, appimage.github.io:** poco nuevo o sin verificación.
- **JuNest:** abandonado, y descarga con `curl -k`.
- **Conty:** 2 GB.
- **Guix:** necesita root.
- **huber, zap:** abandonados.
- **static-get:** s.minos.io solo sirve HTTP y está congelado desde 2017.

## Pendientes del dueño
- Gancho `command_not_found_handle` (bash; `command_not_found_handler` en zsh): que escribir `figlet`
  llegue a cmdfound. Tu bash ya define uno para `thefuck`. Se ve en la revisión de instalación.
- `--index-update` sin canal: se decide con los números de la estabilización. ¿Y el flag pasa a
  `--catalog-update`, con el viejo como alias, ahora que todo lo que lee el usuario dice "catalog"?
- Meta del bloque de pruebas: aprobadas solo las opciones 2 (rutas calientes, sin globales que enreden) y
  6 del documento, "nada más, nada menos" (dueño). La 10 (forks en los canales) no se trabaja más: su
  commit queda quieto en `feature/channel-forks`; el dueño la decide con `~/cmdfound-test-cost.md` (1.014 líneas, 10 opciones
  con su diff, 5 diagramas, 3 escenarios). Dato clave: el reloj no sirve de meta (el mismo bloque midió
  81,5 s a carga 0,3 y 141 s a carga 6,4), y los procesos sí (61.683, estables al 0,2 %). Recomendado:
  meta en procesos, ≤55.000, que es lo que deja la opción 2.
- Opciones 2 y 6 hechas e integradas (ca27dcf, 845e9dd): bloque 64.562 → **53.791 procesos** (−16,7 %) y
  ~92 → ~80 s; `-n tiny` 187→113, `--yes tiny` 228→154, corrida recordada 11→10. La 2 también acelera al
  usuario. +4 nombres netos de variable, con la convención documentada en cada función.
- Diferidos: x-cmd, `conda:<canal>/<paquete>`, Arch y el runtime `rootfs`. No entran más canales
  (dueño, 2026-09-17).

## Decisiones de estabilización (2026-09-17)
- `channels.conf`:
  - Un nombre desconocido genera un aviso.
  - Un comentario al final de la línea no apaga el canal.
  - Los empates los rompe el orden del archivo.
- binstall: ignora `CARGO_REGISTRY_DEFAULT` (sus builds firmados solo existen para crates.io).
- Dependencias: solo el núcleo mínimo va en el anfitrión; todo lo que cmdfound pueda conseguir por sí
  mismo con ese mínimo, lo consigue él (`needs=`).
- `cmdfound -U` e instalación: se discuten en la estabilización. Quizá todo pase a un solo archivo, o se
  evalúan otros métodos de instalación y actualización. Hoy `-U` solo actualiza el archivo `cmdfound`,
  no `cmdfound.d/`.
- Documentación: ninguna por el momento.
- Comentarios: solo los estrictamente necesarios (dueño, 2026-09-21). Un comentario se gana el lugar
  diciendo por qué, no qué: un rodeo, una restricción de portabilidad, una decisión del dueño, una trampa
  en la que caería un cambio futuro, o el contrato de una función. Lo demás va en el mensaje del commit.
- Candado (dueño: por canal, paquete y versión, "el único lugar donde realmente hay conflicto"):
  `${home}/locks/<canal>_<paquete>_<versión>` con `mkdir`, el pid adentro, tomado antes de la pregunta y
  liberado por trampa; uno de un pid muerto se barre. El que espera avisa en una línea y usa lo que dejó
  el otro. Un purge de la misma especificación espera; un `--purge` completo se niega y nombra el pid
  (confirmado por el dueño, 2026-09-21): se espera lo que se puede nombrar, y un purge completo no choca
  con una colocación sino con cualquier instalación que empiece después, que no hay cómo esperar. El
  mensaje dice qué pasó y qué lo destraba, y se detiene ahí.
  Los catálogos ya se escriben en temporal y se renombran, así que no llevan candado (e328211..3e3b8a5).
- Review humano del código: funciones aprobadas se marcan con una etiqueta dentro de la función, y las
  congeladas solo se tocan por un bug importante. La herramienta que lo verifica va en `sh/tools`.
  La herramienta se llama `code-freeze` (dueño). Especificación: `~/code-freeze-spec.md`. Un agente nunca escribe ni actualiza una etiqueta: se detiene y
  lo reporta.
- Nombre: **cmdfound** (dueño, 2026-09-17), lo contrario de "command not found". Descartado
  `command-not-found`: es el paquete de Ubuntu/Debian (instalado aquí) y el de NixOS, y los mensajes
  parecerían un error. Libre en npm, PyPI, crates.io, Homebrew, GitHub, la web y las 15 listas. Variables
  `CMDFOUND_*`, `cmdfound.d/`, etiquetas `io.cmdfound.*`.
- Un solo lugar: `~/.cmdfound/` guarda todo, `channels.conf` incluido, para que un `rm -rf` quite
  cmdfound entero, a salvo de los limpiadores de caché. `CMDFOUND_HOME`
  lo sigue cambiando; `XDG_CACHE_HOME` ya no se consulta. Hecho junto con el renombre (415bf26).
- Instalación real del dueño: shundle clona learn en `~/.shundle/bundle/learn` y expone `sh/tools`
  (`Expose="sh/tools: !battery"`). Ese clon está en 283b684, de la historia anterior a la reescritura del
  2026-09-16: guarda el commit del spec quitado (da2b4ae) y no trae static-run ni cmdfound (nada de eso
  está en el PATH). Para la revisión de instalación: cmdfound llega a los usuarios por shundle tras el
  push a master, y `-U` reescribiría un archivo dentro de un clon de git.
- Pruebas: el bloque corre con HOME propio, sin XDG_* ni variables de ubicación de las herramientas, y
  falla si cambió algún lugar del HOME real donde escriben cmdfound o sus herramientas (a83ce8d, c9b2df1;
  cuesta ~3 ms). Antes, una mutación había escrito en el `~/.cmdfound` real.
- Auditoría real por canal con HOME vacío (2026-09-17): ningún canal escribe fuera de `.cmdfound`
  salvo wget, que escribía `~/.wget-hsts` (arreglado, 9a278d6: `--no-hsts` si wget lo entiende). pkgx,
  nix, micromamba, udocker y AM, descartados. `--ephemeral` dejaba su raíz en /tmp porque el `exec` borra
  la trampa. El dueño eligió mantener el `exec` (para que un TERM al pid, como el de `timeout`, llegue al
  programa) y que la siguiente corrida barra las raíces de pids muertos (d9d0b6e; la corrida recordada
  sigue en 12 procesos).
- Segunda corrida real: 11–24 ms y 14–24 procesos nativos; udocker 118 ms, docker 575 ms.
- Bugs a arreglar en la estabilización:
  - aqua con wget y sin curl: el tag sale `v4.564.0 [following]` y el índice falla.
  - `--purge` deja enlaces colgando (am `bin/hyperfine`, aqua `root/bin/hexyl`) y subestima lo liberado
    (nix 7,8 MiB, pkgx 76 KB de 136 KB).
  - docker: tras `rm -rf channels/docker` nadie reclama la imagen base bajada.
  - La pregunta no cuenta los catálogos de la primera vez: aqua 3,4 MB, conda-forge 23,2 MB, alpine
    ~2,6 MB, nixexprs 42 MB.
  - ~~nix: el arranque real es ~132 MB (68 MB herramienta, 42 MB nixexprs, ~22 MB paquetes), no 22 MB.~~
    Resuelto en 82db160: ya no se anuncia ningún 22 MB; el piso (herramienta + nixexprs) sale en sus
    propias líneas y los paquetes quedan como desconocidos.
- Restos de una obtención fallida:
  - **conda-forge:** la caché de micromamba se reutiliza (un reintento u otro paquete no baja de nuevo).
    `collects=yes`: `collect` borra al hacer purge lo que ninguna instalación usa, y bajo
    `CMDFOUND_COLLECT=all` no hace nada.
  - **docker:** sin contenedores de build que esperen 24 h. La instalación es el proceso principal del
    contenedor, y los secretos de red van en un archivo temporal que se borra antes del commit.
    Los builds viejos de este home se limpian al empezar cada obtención y con `--purge`.
  - **nix-portable:** retoma lo más que puede. El catálogo se reanuda con `curl -C -`, los paths
    terminados se reutilizan, y solo el archivo a medias se baja de nuevo.
- Flags de `CMDFOUND_DOCKER_FLAGS`/`_UDOCKER_FLAGS` con una comilla sin cerrar: aviso y 127, sin llamar
  al runtime (decisión del constructor).

## Estadísticas (para el post)
Se actualiza en cada hito. Lo contable lo recalcula `~/cmdfound-stats.sh`; lo de investigación se anota a
mano cuando llega el reporte.

Corte: 2026-09-21 23:32Z (b223d35). El anterior fue el 2026-09-17 07:58Z (144da86).
- **Línea de tiempo:**
  - Primera mención de la herramienta: 2026-09-15 17:51 local; la conversación había empezado unos 7
    minutos antes como "static-get".
  - Primer commit: 2026-09-16 01:53.
  - 144 h (6 días) desde la primera mención hasta el corte, con una parada de cuatro días por el límite
    semanal.
- **Agentes:**
  - 51 creados, 50 de cmdfound: 48 general-purpose y 2 chore.
  - Todos los que corrieron usaron Opus 5. Los 3 lanzados con Fable fallaron al arrancar por su límite de
    uso.
  - 47 retomas y hasta 9 agentes a la vez; 38 mensajes enviados a agentes ya corriendo.
  - ~48,6 h-agente de reloj y ~6.000 usos de herramientas.
  - Tokens gastados por los agentes: 7,7 M de salida, 54 M de entrada más escritura de caché y 1.850 M
    leídos de caché.
  - Los más grandes: la auditoría de fugas del HOME real, S2 (plomería y configuración del usuario) y
    nix-portable.
- **Sesión principal:**
  - 1 sesión y 8 compactaciones desde la primera mención.
  - 1.544 respuestas del modelo y 1.496 llamadas a herramientas (Bash 1.086, Edit 144, SendMessage 85,
    Agent 52, Read 37, PushNotification 33, Write 17).
  - Tokens: 2,4 M de salida y 575 M leídos de caché.
  - 156 mensajes del dueño.
  - Estas cifras incluyen algo de coordinación ajena; la sesión entera, con un día previo de otro trabajo,
    da 1.841 respuestas y 178 mensajes.
- **Git:**
  - master: 21 commits, todos con el nombre viejo; de cmdfound no hay nada publicado.
  - `integrate/channels`: 125 commits por encima de master, sin subir, con +16.321 −313 líneas en 49
    archivos.
  - 16 ramas `feature/*` a lo largo del trabajo; al corte quedan dos, master y la de integración.
- **Código, master → `integrate/channels`:**
  - Núcleo: 1.820 → 3.347 líneas.
  - Canales: 4 → 10, con 1.834 → 7.290 líneas, más `confined-launch` (613).
  - Simulaciones: 16 → 36 archivos, 393 → 2.773 líneas.
  - Bloque de pruebas: 576 → 2.561 líneas, 247 → 1.161 aserciones, repartidas en 22 secciones.
  - Variables `CMDFOUND_*`: 14 → 38. Funciones: 116 → 299.
  - 22 % de las líneas son comentarios, después de recortar 1.249.
- **Contador de Claude Code (2026-09-17, captura del dueño):** 42 agentes hasta el momento; modelo Opus 5
  (1M de contexto), esfuerzo Extra high; seguido desde el teléfono con Remote Control; 88 % del límite
  semanal usado, con 4 días para reiniciar.
- **Pruebas:** bloque de cmdfound 76.8 s en 144da86 (carga ~2); todas las pruebas nuevas se escriben
  primero en rojo y se validan con mutaciones.
- **Mutaciones reportadas el 2026-09-17** (las anteriores no se contaron): docker 25, channels.conf +
  `CMDFOUND_BYTES` 34, conda collect 10, binstall B 29.
- **Medición de binstall:** 79.257 crates de crates.io con binarios; 2.225 pedidos web, 0 a la API; 3.973
  manifiestos leídos; ~2 h de agente. Resultado: QuickInstall ~1.930 instalables, autores +~8.400.
- **Nombres:** 3 agentes, ~150 candidatos probados por grupo contra 15 listas de paquetes, npm, PyPI,
  crates.io, Homebrew y la web; 30 limpios.
- **Daemon de docker compartido:** cada prueba real deja el mismo conteo de imágenes (72 antes y después)
  y usa como máximo 2 descargas de Docker Hub por agente.
- **Costo del bloque de pruebas (415bf26, medido 2026-09-17):** ~82 s y 61.276 procesos por corrida, a
  ~1,35 ms cada uno. 330 corridas de cmdfound: `--yes` que resuelve 299 ms/239 procesos, `-n` 236 ms/191,
  decisión recordada 18 ms/12. El 61 % de los procesos los lanza el propio shell del núcleo (26.014
  subshells `$(...)`, 5.017 awk). Reparto: ~45 s son costo propio del núcleo y ~25–30 s diseño de las
  pruebas (resoluciones solo para preparar, esperas del `sleep 0.1` de la carrera de catálogos, 23 canales
  falsos compartidos, sleeps fijos).
- **Después de las opciones 2 y 6 (b223d35):** ~54.930 procesos por corrida, unos 70 por debajo de la meta
  de 55.000 del dueño. El reloj no sirve de meta: el mismo bloque da 100 s con carga 3,3 y 170 s con carga
  7 en esta máquina.
- **Correr por secciones (b223d35):** el bloque se corta al final de cualquiera de sus 22 secciones. Una
  mutación que antes costaba el bloque entero (~145 s de referencia) ahora cuesta lo que pesa su sección:
  1,6 s en `home` (98,9 % menos), 14 s en `github`, 37 s en `pkgx`, 65 s en `nix-portable`, 93 s en
  `alpine`, 112 s en `docker`. El propio corredor tiene 11 pruebas suyas que corren en 0,6–1,0 s.
