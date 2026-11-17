# Centro de Aprendizaje — memoria del proyecto

Contexto para retomar el trabajo desde cualquier PC. El detalle técnico está
en `README.md`; acá va lo que no se deduce del código.

## Qué es

Portal de capacitación y soporte interno para hospitales de Santa Fe.
Es multi-tema, y hoy tiene tres temas: **miHospital**, **TIMBÓ (Expedientes)**
(con la categoría interna **Licitaciones y Compras**) y **TIMBÓ Compras**
(lado proveedor/oferente). Flask + SQLAlchemy + SQLite (con migraciones
Alembic), y chatbot + buscador global 100% locales por palabras clave
(`app/services/buscador.py`), sin IA externa.

## Cómo levantarlo en una PC nueva

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts/importar_mihospital.py
python scripts/importar_timbo_expedientes.py
python scripts/importar_timbo_compras.py
python scripts/importar_equivalencias.py   # siempre DESPUES de importar_timbo_compras
python scripts/importar_faq_chats.py       # siempre al final
python run.py                          # http://127.0.0.1:5000
```

La base (`instance/*.sqlite3`) no está en git: se recrea con los scripts.
Para cambios de esquema se usa Flask-Migrate (`flask db migrate` / `flask db upgrade`),
no hace falta borrar la base para eso.

🔴 **Trampa encontrada 2026-11-13**: `importar_timbo_compras.py` borra y
recrea el `Tema` completo, y `EquivalenciaArticulo` tiene
`cascade="all, delete-orphan"` contra `Tema` — así que reimportar el
contenido de TIMBÓ Compras borra en cascada TODAS las equivalencias de
artículos. Si tocás `content_timbo_compras.json` y reimportás, correr
`scripts/importar_equivalencias.py` inmediatamente después (nunca antes)
o se pierde el trabajo de equivalencias sin aviso ni error.

## Criterios de la usuaria (respetarlos siempre)

- El chatbot y los tutoriales tienen que ser **muy prácticos, intuitivos y
  fáciles**: completos pero sin saturar. Van respuestas cortas, y lo extra se
  pone en "Ver más" o en botones para tocar, no en párrafos largos.
- Escribir en español rioplatense (voseo), con lenguaje simple.
- **Nunca** cargar datos personales de los chats de soporte (nombres,
  teléfonos, correos, CUIL). Los exports de WhatsApp en
  `timboDocumentacion/historialWp/` están en `.gitignore` por eso: no se
  suben. Si hacen falta en otra PC, se copian a mano.
- Las respuestas que no quedaron confirmadas van con `verificado: False`
  (el chatbot les muestra un aviso "sin confirmar").
- Antes de subir una captura de pantalla real al repo, revisar que no
  tenga de fondo contenido ajeno al tutorial (otras ventanas, videollamadas,
  nombres de personas, otras sesiones) — recortarla si hace falta.

## Dos líneas de trabajo en paralelo (2026-11-12)

Este proyecto se trabajó un tiempo desde dos PCs distintas, con historias de
git completamente separadas (sin commits en común) y hasta una estructura de
carpetas distinta (todo bajo `centroAprendizaje/` acá vs. en la raíz del repo
en la otra). Se reconciliaron a mano el 2026-11-12, usando esta carpeta como
base: se portó el tema **TIMBÓ Compras** completo (contenido, importador
genérico `importar_timbo_expedientes.importar(ruta_json, orden_tema)`,
situaciones de FAQ y el bloque de tutorial `{"type": "video", ...}`) desde la
otra línea de trabajo, sin tocar el contenido ya verificado de esta. Si
aparece de nuevo una divergencia de git sin commits en común, es probable que
sea por lo mismo: confirmá en qué PC se trabajó antes de asumir que es un
error.

## Segunda reconciliación y deploy (2026-11-13)

Volvió a pasar: la PC "BERE-PC" (repo `D:\Bere\GIT\GIT-HEEP`, todo en la raíz)
trabajó un día entero en paralelo. Se integró acá con una combinación de 3
vías del contenido (base: commit `2537247` de esa línea) y se deployó. Lo que
sumó:
- Revisión contra fuentes oficiales: circulares SCyGB y UG TIMBÓ, Pliego
  Único, guías PDF y videos (listas "APP-TimboCompras", "Timbó para la
  Reforma", "Timboteca", "Timbó Rendiciones").
- Compras: lecciones por rol (Gestor, Supervisor, Evaluador), pliego modelo,
  montos 2026, adjudicar y después de adjudicar; alta de artículos con la vía
  de Farmacia (SUFYD) para medicamentos y descartables.
- Expedientes: licencias (SJL), documento importado y embebidos, Firmador
  Digital Web, módulo "Rendiciones de subsidios".
- Chatbot: puntaje mínimo y "¿Te referís a...?", sugerencias, pasos plegados,
  sinónimos y errores de tipeo, derivación a otro tema; 👎 queda en
  estadísticas como "sin respuesta".
- `app/services/importacion.py`: al reimportar un tema, consultas, feedback y
  eventos pasan al tema nuevo (antes quedaban huérfanos). El nomenclador se
  borra con el tema: correr siempre `importar_equivalencias.py` al final.
- miHospital figuraba como "TIMBÓ" en su JSON: corregido.

**Deploy en el servidor** (app en
`/var/www/timbo-capacitaciones/centroAprendizaje`, con su `.venv` e
`instance/` adentro; servicio `timbo-capacitaciones`): `cd` a esa carpeta, y
`git pull` y scripts (`.venv/bin/python scripts/...`) como el usuario
`timbo-capacitaciones` (`sudo -u timbo-capacitaciones -H ...`), nunca como
root: quedaron 132 archivos a nombre de root y el `git pull` fallaba. Orden:
importar_mihospital → importar_timbo_expedientes → importar_timbo_compras →
importar_faq_chats → importar_equivalencias, y después
`systemctl restart timbo-capacitaciones`. Antes, backup de
`instance/centro_aprendizaje.sqlite3`.

Hecho después (13/11, commit `2108bcb`, deployado): se revisaron los 10
videos oficiales sin subtítulos. Los que tienen voz se transcribieron en esta
PC con whisper.cpp; los mudos (y la Clase 01, que whisper leyó como
"música") se miraron cuadro por cuadro con mosaicos de ffmpeg. Lo útil quedó
en el portal: tips en subir archivo, pase, vincular, buscar, documentos
oficiales; tabla "¿Dónde pedir asistencia?" en "Hacer una compra"; y la
lección del RUPC con los 7 pasos del instructivo oficial (servicio
"API_ECON SANTA FE REGISTRO ÚNICO DE PROVEEDORES Y CONTRATISTAS" en ARCA).
6 videos de las listas son privados y no se pueden ver. "Edición
MS-Compras" y "Del papel a la IA" no aplican al hospital.

Cómo transcribir (por si aparecen videos nuevos): yt-dlp
`--js-runtimes node` para bajar el audio; whisper.cpp b5130 para Windows,
variante `ggml-cpu-sse42` (esta PC es un Celeron sin AVX:
faster-whisper/ctranslate2 se cuelga), modelo `ggml-base.bin`, con
`-l es -t 2 -mc 0 -sns` (sin `-mc 0 -sns` entra en un bucle de "(Música)").
Necesita el Visual C++ Redistributable (VCOMP140.DLL). El clasificador de
permisos no deja que Claude ejecute `whisper-cli.exe`: lo corre la usuaria
con un `.bat`.

## Revisión del 14/11

- **Deploy**: el 14/11 se subió `integracion-deploy` a `main` y al servidor
  (lección de urgencia/desierto y chatbot de `d407af2`). Más tarde ese día
  se deployó también `e7e93ab`, con todo lo de esta sección. Se hizo copia
  de la base, se corrieron los 5 importadores y se reinició el servicio.
  En el servidor, la batería del chatbot dio 88/88. **El servidor y `main`
  están en `e7e93ab`.**
- **Videos**: se cruzó el canal oficial completo con el portal (sección 4.2
  de `timboDocumentacion/FAQ_SOPORTE_TIMBO.md`). Se leyeron por subtítulos
  los 13 que no estaban enlazados, incluido "Atención Virtual ¿Cómo lo
  hacemos?", y el CD-01 (mudo) se miró cuadro por cuadro. Lo nuevo quedó en
  16 lecciones, y cada video, enlazado en su lección. Lo único que falta es
  el texto hablado de la Clase 01 de Compras (resuelto el 16/11: ver
  pendiente 4).
- La integración del 13/11 había perdido las secciones 4.1 y 5 de
  `FAQ_SOPORTE_TIMBO.md`: se recuperaron de la otra PC.
- **Chatbot**: la batería ahora está en `scripts/bateria_chatbot.py` (88
  preguntas; correrla después de importar). Pasó de 69 a 88 bien. Cambios:
  tareas nuevas de Atención Virtual (agente), situaciones "No me deja
  firmar" (Expedientes y Compras), palabras clave afinadas, "¿qué es X?"
  reconoce la sigla al final del término ("... (SIN)"), el bonus por título
  exacto ya no deriva a otro tema, y la respuesta trae "▶ Ver el video
  oficial" (el más corto de la lección).
- El test que fallaba a veces era un error real: un mensaje del usuario con
  la misma hora que la última vista del admin quedaba como leído. Ahora el
  mensaje siempre queda después (`_despues_de_la_vista_del_admin`).
- miHospital sigue sin contenido de "evolución" ni "receta": no están en el
  manual. Hay que relevarlo con alguien que use el sistema.
- Sugerencias que quedaron:
  - Una vez por semana, revisar en /admin/chatbot las preguntas sin
    respuesta y los 👎, y sumarlas a la batería.
  - Tener copia de los videos más cortos en la red interna, porque en
    muchos hospitales YouTube está bloqueado.

La vista previa local se cierra sola si a la PC le falta memoria (7,7 GB):
levantarla solo cuando haga falta.

## Revisión del nomenclador por una persona externa (16/11/2026)

- **Colores del nomenclador** (`templates/equivalencias.html`): son los
  estados de `confianza`, sin datos nuevos. 🟢 `alta` = revisado y correcto,
  🟡 `dudosa` = revisar, 🔴 `sin_match` = problema pendiente (no está en el
  catálogo). Hay leyenda, chip con texto en cada fila y franja de color.
  Clases compartidas: `.estado-verde/-amarillo/-rojo` en `styles.css`.
- **Acceso de la revisora** (`app/revision/routes.py`, blueprint `/revision`):
  enlace privado `/revision/acceso#<token>`. El token va después del `#`
  (no viaja en la URL ni queda en logs); `revision.js` lo manda por POST con
  CSRF. En la base solo se guarda el hash (`revisores_nomenclador`). La
  sesión usa `revisor_id`, aparte de `admin_autenticado`: no entra al panel.
  Se da de baja o se genera un enlace nuevo desde `/admin/nomenclador/revision`
  (el enlace se muestra una sola vez, con botón para descargar el acceso
  directo `.url` de Windows).
- **Observaciones** (`observaciones_nomenclador` + `_historial`): una por
  revisor e ítem, editable, con fecha y versiones anteriores. Solo para ítems
  en amarillo. Se vinculan por `clave_item` (nombre interno normalizado),
  NO por el `id`, porque `importar_equivalencias.py` borra y recarga la
  tabla en cada deploy. Nunca modifican `equivalencias_articulos`.
- **Migración** `5e1f0a7c2b90` (solo crea las 3 tablas). El deploy ahora
  corre `flask db upgrade` (paso 3b de `scripts/deploy_servidor.sh`).
- Tests: `tests/test_revision_nomenclador.py`.

### Validación de equivalencias por farmacia (17/11/2026, deployado en `8a667ee`)

Pedido de la usuaria: que farmacia solo valide los amarillos, rápido y sin
capacitación. La comparación automática y los colores NO se tocan.
- **Pantalla `/revision/`** (la llave sigue igual): lista con buscador como
  el nomenclador público, **de a 15** con flechas (y teclas ← →). Filtros
  Por revisar / Revisados / Todos. Cada tarjeta: pedido + código interno del
  hospital (sale de `[cod. interno N]` en las notas), TIMBÓ + código +
  Copiar, la nota limpia (`nota_visible`, mismas reglas que el público), y
  tres botones con ayuda al pasar el mouse: **✓ Confirmar**, **✎ Editar**
  (abre el campo con un mini botón **Guardar**; también guarda al salir) y
  **✗ No coincide**. Si solo escribe, sin ✓ ni ✗, queda "con dudas". Los
  revisados se ven teñidos y con la marca del resultado y la fecha. Los
  guardados van en cola (de a uno), para que no se pisen.
  La usuaria pidió esta forma después de ver la versión "de a un artículo",
  que se descartó: prefiere la lista con buscador.
- **Datos:** columna `validacion` (`si` / `no` / `duda` / NULL) en
  `observaciones_nomenclador` y en el historial (migración `8a3c4d2e1f07`,
  solo agrega columnas). Las observaciones viejas quedan sin respuesta =
  "sin revisar". `/revision/observacion` acepta `validacion` y/o `texto`.
- **Excel sin dependencias** (`app/services/xlsx.py`, sin openpyxl en el
  servidor): filas pintadas por color (verde sí, rojo no, naranja dudas,
  gris sin revisar).
  - Farmacia: `/revision/mis-revisiones.xlsx`, solo lo suyo, sale de la
    sesión (no acepta parámetros). Hojas COINCIDENCIAS / NO COINCIDEN /
    DUDAS (+ SIN RESPUESTA si hay observaciones viejas).
  - Admin: `/admin/nomenclador/revision/exportar` con 4 hojas
    (COINCIDENCIAS, NO COINCIDEN, DUDAS, SIN REVISAR) + "YA NO EN AMARILLO"
    si hay. `?revisor=<id>` = Excel de una sola persona (botón ⬇️ Excel en
    la tabla de accesos).
- **Panel:** resumen Total / Confirmados / No coinciden / Con dudas / Sin
  revisar, que también son filtros (+ "Con observación escrita"). Si dos
  personas responden distinto, el ítem cuenta como "Con dudas".
- **Local:** `python run.py` usa siempre la contraseña `admin123` (pedido de
  la usuaria). El servidor no pasa por ahí (gunicorn `run:app`).
- Pendiente: el PDF `static/descargas/llave_de_acceso_revision.pdf` todavía
  explica la pantalla vieja ("Agregar observación"). No hay asignación de
  artículos por persona: cada llave ve todos los amarillos.

## Estado al 16/11/2026 (deployado: servidor y `main` al día)

**Reglas nuevas de la usuaria (16/11), además de las de arriba:**
- **Nada que no esté chequeado como oficial, en TODO el centro.** Cada
  frase normativa u operativa se coteja con el texto oficial (bajar el PDF
  y buscar el punto). No deducir ni completar con sentido común. Lo que no
  tiene respaldo se saca o queda solo en /admin. Ya aparecieron errores así:
  garantía de impugnación "150%" (el Pliego Único dice 3%) y "una persona
  puede tener más de un rol" (la Circular UG 7/2026 no lo dice).
- **Todo formulario o documento que se nombre va con su link oficial.**
- Los manuales y videos de miHospital cuentan como fuente oficial.
- Mostrar en local antes de subir; la usuaria decide cuándo se deploya.

**Cómo funciona "solo lo oficial" en el sitio público:**
- `app/recursos/__init__.py`: `es_publico(estado)` (confirmado o
  discrepancia), `glosario_publico()` y `algoritmo_publico()` filtran lo
  pendiente, didáctico o de práctica. En /admin se ve todo. Las plantillas
  usan `oficial(estado)` (lo da el context processor de `ui/routes.py`).
- `OCULTOS_PUBLICO = {"simulador", "checklists"}`: dan 404 en el sitio y
  siguen en /admin. (Los "Modelos de mensajes" se volvieron a mostrar por
  pedido de la usuaria.)
- Los importadores no cargan los casos con `verificado: False`.
- `tests/test_recursos.py::test_sitio_publico_solo_muestra_lo_verificado`
  controla que no quede nada pendiente o didáctico en las páginas públicas.

**Lo nuevo del 16/11:**
- Inicio con "¿Qué necesitás hacer hoy?" (9 accesos directos), Recursos
  plegado (botón desplegable, barra lateral y "Ir a otro recurso"), un solo
  glosario (el de cada tema redirige al Diccionario filtrado), buscador
  global que incluye Recursos, "¿Te sirvió esta página?" (votos en
  /admin/estadisticas), "Revisado al…", ícono de la pestaña.
- Recursos: Roles corto (tarjetas + matriz + "Ver más"), **Montos y topes
  2026** (copia de la Circular SCyGB 01/2026), **Para proveedores**
  (requisitos, RUPC, paso a paso con las guías y videos oficiales, mensaje
  para copiar), **Ficha A4 para asignar roles** (`/recursos/roles/ficha`;
  PDF en `timboDocumentacion/capacitacion/`), formularios **CD-01 a CD-05**
  en el Diccionario.
- `app/static/js/topes.js`: en todo el sitio, "monto menor al tope",
  "licitación privada", etc. muestran el tope al pasar el mouse
  (`recursos.topes()`), los formularios (CAByS, CD-01 a CD-04, Pliego
  Único) se vuelven link oficial (`recursos.enlaces_oficiales()`; CAByS y
  CD abren TIMBÓ en tramites.santafe.gob.ar porque se crean adentro) y las
  direcciones santafe.gob.ar/gov.ar escritas como texto quedan clickeables.
- Solo en /admin: **Flujos paso a paso** (`/admin/recursos/flujos`) y el
  **Gráfico de flujo** en SVG (`/admin/recursos/grafico`,
  `app/recursos/grafico.py`).
- Biblioteca nueva: Circular UG TIMBÓ 2/2025 (compras directas 100%
  digitales), videos oficiales de compras directas, guías para
  proveedores, manuales del Firmador Digital Web.
- **Seguridad del servidor aplicada** (`scripts/servidor/aplicar_seguridad.sh`):
  base y copias con permisos 600 en `/var/www/timbo-capacitaciones/copias`,
  copia diaria a las 3:15 (14 días) y pip-audit el día 1 de cada mes
  (resultado arriba en /admin), nginx sin versión y con límite de intentos
  en `/admin/login`. Sin contraseña extra en /admin (la usuaria no quiso).
- **Copia en la PC:** tarea de Windows "Centro de Aprendizaje - copia de la
  base" (10 h) corre `scripts/traer_copia.sh` → `D:\Bere\Copias\timbo-capacitaciones`.
  En otra PC hay que crearla de nuevo (PowerShell como administrador, ver
  el script) si se quiere ahí también.

**Deploy:** `git push origin integracion-deploy:main` y después, aparte,
`tr -d '\r' < scripts/deploy_servidor.sh | ssh -i ~/.ssh/timboheep_ed25519 -p5440 root@138.36.238.175 'sh -s'`.
El script hace copia, pull, dependencias, los 5 importadores, batería del
chatbot (88/88), reinicio y controles. El clasificador de permisos suele
bloquear que Claude corra el deploy: lo corre la usuaria con `!` (un
comando por mensaje: si se pegan dos juntos, el segundo no corre).

**Transcripciones de videos:** `timboDocumentacion/transcripciones/` (no
se sube a git: nombran a participantes). Se regeneran con yt-dlp
(`--extractor-args "youtube:player_client=web_embedded"`, y para los que no
salen, `player_client=ios`) y `scripts/vtt_a_texto.py`.

**Verificación frase por frase (16/11, en curso):** el registro está en
`timboDocumentacion/VERIFICACION_LECCIONES.md`. Tandas 1 (proveedor) y 2
(compras directas): hechas. **Tanda 3 (gestión interna): van 10 de 17**
(quedan 7: las de Gestor/Supervisor/Evaluador y "notificar-proveedor",
bloqueadas por ahora porque no se pudieron bajar subtítulos de YouTube —
yt-dlp devuelve "Only images are available" con varios clientes). Esta
tanda encontró y corrigió 4 atribuciones de rol que contradecían la
Circular UG TIMBÓ 7/2026 (el Supervisor carga los actos de adjudicación y
"sin efecto", no el Gestor). Lista de lo que falta y las fuentes en ese
archivo. Copia de la memoria de Claude de esta PC: `timboDocumentacion/memoria_claude/`.

**Deploy 16/11 (commit `484777d`): servidor y `main` al día.** Además de
lo de la tanda 3: se sacaron del nomenclador las 89 filas de "Pedido 1984
- Microbiología" (quedan las 1000 del nomenclador interno completo), el
inicio del portal se simplificó (se sacó "¿Qué necesitás hacer hoy?",
queda "Elegí un sistema" + Recursos) y en `/admin/estadisticas` se
agregaron "Todas las búsquedas" y "Todas las preguntas al asistente" (antes
solo se veían las que no tuvieron resultado). Batería del chatbot: 88/88.

**Sigue (punto 2):** verificar frase por frase las lecciones de TIMBÓ
Compras (empezando por proveedor: las 8 guías ya están en texto), después
Recursos y el diccionario, TIMBÓ (Expedientes) y miHospital; a cada
formulario, su link oficial. Pendientes institucionales: aplicación de la
URC al hospital, vigencia del RUPC, quién autoriza los roles, si una
persona puede tener más de un rol, Convenio Marco en TIMBÓ (la intervención
de la SCyGB en otras causales quedó resuelta el 16/11: Dec. 652/2020 y Disp. 282/16), "Territorio 5.0" (lección de compra directa:
falta identificar la norma).

## Segunda etapa (15/11/2026) — deployada el 16/11

- **Seguridad** (`timboDocumentacion/AUDITORIA_SEGURIDAD.md`, `app/seguridad.py`,
  `tests/test_seguridad.py`): límites de intentos, sin contraseña por
  defecto, cookies seguras, CSP con nonce (no usar JS en línea: los
  `onsubmit`/`onclick` van en `admin.js` con `data-*`), Flask 3.1.3. Al
  deployar: `pip install -r requirements.txt`. Pendientes en el servidor
  (con autorización): `chmod 600` a la base y las copias, `server_tokens
  off` y `limit_req` en nginx.
- **Investigación** (`timboDocumentacion/INVESTIGACION_SEGUNDA_ETAPA.md`):
  fuentes, confirmado y pendiente.
  - Hay **dos "Circulares 03/2026"**: la UG TIMBÓ (obligatoriedad) y la
    SCyGB (URC y mesa de ayuda).
  - Hay una discrepancia sobre la vigencia del RUPC.
  - El control de la URC en el hospital queda pendiente.
- **Recursos** (`/recursos` en el sitio y `/admin/recursos`): roles y
  alcances, circuito, glosario de todos los temas, biblioteca y
  nomenclador. Datos en `app/recursos/*.json`, con estado (confirmado,
  didáctico, práctica, pendiente o discrepancia) y fuentes por id de la
  biblioteca. Plantillas en `templates/recursos/`, compartidas entre el
  sitio y el panel.
- **Capacitación** (privado, `/admin/capacitacion`): guía de la primera
  clase, material para participantes y presentación de 20 diapositivas
  (`app/recursos/archivos/`, se descarga solo con sesión). Para
  regenerarla: `timboDocumentacion/capacitacion/generar_presentacion.js`
  (pptxgenjs). El PDF se exporta con PowerPoint.
- **15/11, segunda tanda (local):**
  - algoritmo "¿Qué camino sigue una compra?", con las ramas A a E (`algoritmo.json`);
  - simulador con 6 escenarios (`simulador.json`);
  - checklist por procedimiento;
  - diccionario A–E (`glosario.json`);
  - plazos, a quién preguntar, modelos de mensajes y estados (`herramientas.json`);
  - modo capacitadora (`/admin/capacitacion/modo-capacitadora`) y modo participante (`/recursos/aprender`).

  `tests/test_recursos.py` valida fuentes y caminos.
- **Faltan:**
  - el inventario exhaustivo de documentos y videos;
  - la matriz de trazabilidad de todo el contenido;
  - capacitación: "qué se hace en cada sistema" (`/recursos/sistemas`), la
    matriz de responsabilidades (en Roles), "explicame este paso"
    (`/recursos/explicame`) y la evaluación final (simulador, 12 preguntas)
    quedaron hechos el 15/11. Falta revisarlos en un navegador: no se
    levantó el servidor por falta de memoria en la PC;
  - las fichas FP y el examen profesional.
  - Para las causales de contratación directa hay que leer el art. 116 de
    la Ley 12.510 (todavía no se leyó completa).

## Pendientes (actualizado 2026-11-14)

Contenido:
1. ~~Lección de contrataciones directas por urgencia o por proceso
   desierto~~ — hecha: `directa-urgencia-o-desierto` (Gestión interna),
   armada con el texto completo de la Circular UG TIMBÓ 8/2026. Los nombres
   de las opciones en pantalla para estos casos no están relevados (la
   lección lo avisa): confirmarlos con Compras.
2. Montos de "¿Qué procedimiento corresponde según el monto?": actualizarlos
   cada año con la circular nueva de la SCyGB.
3. ~~"Atención Virtual ¿Cómo lo hacemos?"~~: hecho el 14/11.
4. ~~Texto hablado de la Clase 01 de Compras (7rIDyLtWlHM)~~: transcripto el
   16/11 con faster-whisper "small" limpiando antes la voz con ffmpeg (receta en
   la sección 4.1 de FAQ_SOPORTE_TIMBO.md). Lo nuevo quedó en "Hacer una compra".

Para confirmar con personas del hospital:
5. Compras: los nombres exactos de botones del lado del hospital en "Hacer
   una compra" (salen de los videos y circulares; la lección lo avisa), y si
   les aplica el control de la URC (Circular SCyGB 03/2026, dirigida a la
   Administración Central).
6. RRHH: si ya rige el domicilio digital para el personal.
7. Consultas abiertas de los chats: ~~SIN sin "comenzar una carga"~~ (resuelta
   el 16/11 con el video oficial SDAEZ_4rjZo: Ingresar → Cargar → Comenzar una
   carga; si no aparece, bibliotecanormativa@santafe.gob.ar), numeración de
   decisorios (para resoluciones en AAR el número lo pone TIMBÓ al protocolizar,
   Circ. UG 2/2024; falta saber si el decisorio del hospital va por AAR), documentos HTML→PDF y servidor propio para los
   videos. Cuando haya respuesta, pasar a `verificado: True` en
   `scripts/importar_faq_chats.py`.

Técnico:
8. ~~Test que fallaba a veces~~: corregido el 14/11.
9. Pulido final de UI/UX. Hecho el 14/11:
   - Caja "¿Qué necesitás hacer?" en el inicio de cada tema. Las preguntas
     escritas ahí y los botones abren el chatbot ya respondiendo.
   - En el celular: tarjetas en fila, tablas que bajan de línea y chatbot
     casi a pantalla completa.
   El 15/11, en el resto de las páginas:
   - "Tengo un problema": tarjetas plegables, con buscador. El link del
     chatbot abre la situación justa (`#s-<slug>`). Solo se marca "Sin
     confirmar".
   - "Quiero hacer": tareas agrupadas por módulo.
   - Formularios con margen interno y campos sin el hueco del ícono: solo
     los `.input` dentro de `.input-wrap` dejan lugar para el ícono.
   - Nomenclador: de a 30 artículos.
   Las capturas se sacan con Chrome headless por CDP (Node 22, sin
   dependencias), con el servidor local levantado solo para eso.

## Estado (2026-11-12)

Hecho:
- Los 3 temas completos (miHospital, TIMBÓ Expedientes con Licitaciones y
  Compras, TIMBÓ Compras).
- Consultas con estado, estadísticas de uso, buscador global, migraciones
  con Alembic.
- Relevamiento de preguntas frecuentes de los chats de soporte:
  `timboDocumentacion/FAQ_SOPORTE_TIMBO.md`.

Pendiente (ver también la sección 3 de FAQ_SOPORTE_TIMBO.md y el README):
1. ~~Ver a mano 3 videos que YouTube no dejó procesar~~ — resuelto 2026-11-13:
   se miraron **tSYfZ3yVE58** (documento embebido) y **Wb4ZRvB3YSo** (registro
   de proveedor, sin subtítulos; se leyó visualmente paso a paso) directo en
   el navegador y se agregaron como tutoriales nuevos a
   `scripts/content_timbo_compras.json`: `ver-documentos-embebidos` (categoría
   `ofertar`) e `inscribirse-como-proveedor-rupc` (categoría `primeros-pasos`,
   primero en el orden — es el paso previo real a "requisitos"). Sumaron
   también 2 tareas y 2 términos de glosario (RUPC, Documento embebido).
   Reimportado y verificado: 12 tutoriales, 22 términos, 12 tareas.
   ~~Quedan pendientes los otros 2 de la lista~~ — resuelto 2026-11-13 (2):
   se miraron también **Yp3TIlDxpms** (49 min, capacitación en vivo completa)
   y **JJExl9hnYbo** (35 min, ídem), ambos con transcripción completa. Como
   se esperaba, la mayor parte se solapaba con los videos cortos ya cargados,
   pero salió información nueva y concreta que no estaba:
   - ID Ciudadana tiene que estar en **nivel 2** (no alcanza con crearla
     nomás) — se sube con foto de DNI, ARCA o la app Mi Argentina.
   - El domicilio digital tiene la **misma validez legal** que el domicilio
     físico.
   - Santa Fe no tiene identidad digital de personas jurídicas/UTE: quien
     oferta siempre es una persona física que acredita representación
     (contrato social o poder especial) — esto no estaba cubierto para nada.
   - Los decimales se cargan con **coma, no punto** (con punto se pierde el
     decimal) — error común, nuevo.
   - Los anexos solo aceptan **PDF** (nada de ZIP ni imágenes), con un tope
     de **45 MB** por oferta; los documentos embebidos sin descarga previa
     entran en vigencia recién el 21/09.
   - Se puede marcar un requisito como "vigente en el Registro Único de
     Proveedores" en vez de adjuntarlo (si no está vigente ahí, te lo piden
     como subsanación), y se pueden cargar ofertas alternativas por renglón.
   - Garantía de impugnación: habitualmente **150%** del valor de la oferta;
     plazo para revisar competidores: 2 días hábiles administrativos + 1 de
     gracia (igual que en el mundo papel).
   - Mail de soporte: **timbocompras@santafe.gob.ar**.
   Todo esto se sumó ampliando los tutoriales `requisitos`,
   `completar-y-presentar`, `impugnaciones` y `ver-documentos-embebidos` (no
   se crearon tutoriales nuevos, ya estaba el lugar natural para cada dato) y
   se agregaron los 2 videos largos como referencia ampliada donde correspondía.
   Sumó además 2 situaciones nuevas (precio mal cargado por el punto decimal,
   cómo ofertar en nombre de una empresa/UTE), 2 tareas y 1 término de
   glosario (Acreditación de representación). Reimportado y verificado:
   12 tutoriales, 23 términos, 7 situaciones, 14 tareas.
   Lista completa: https://www.youtube.com/playlist?list=PLJKcMr5XTsSc5jJV-Uszw7OXCzG3LwG76

   **Búsqueda exhaustiva 2026-11-13 (3) — lado Compras Directas / gestión
   interna del hospital.** El canal de YouTube "Secretaría de Gestión
   Pública" tiene muchas más playlists de las que se habían mirado (Timbó
   Rendiciones, APP-TimboCompras, Edición MS-Compras, Santa Fe Evalúa,
   Timboteca con 26 videos, Timbó para la Reforma, etc. — ver
   `@SecretariadeGestionPublica/playlists`). Se encontró un circuito
   **completamente nuevo y no cubierto en ningún JSON**: la compra directa
   por monto menor al tope, que NO pasa por TIMBÓ Compras (licitaciones)
   sino que se tramita dentro del expediente electrónico con un documento
   oficial especial, el **CD-01** (hay CD-01 a CD-04 para las distintas
   etapas, y un CD-05 que es nota de rechazo). Fuente: transcripción
   completa de **QH7zvgZ7sbQ** ("Gestión Timbó. Capacitación en Compras
   directas a través de la plataforma digital.", 70 min) más el video corto
   **BzxCGnsajmw** ("Gestión de pago para compras directas"). El video corto
   **b76RDFmcV3c** (CD-01) no tiene transcripción ni se pudo mirar bien a
   mano (autoplay lo interrumpía constantemente) — queda pendiente si se
   quiere profundizar más.
   Se creó la categoría nueva `compras-directas` en
   `scripts/content_timbo_compras.json` (se evaluó ponerla en
   `content_timbo_expedientes.json` por ser técnicamente un Documento
   Oficial del módulo de Expedientes, pero se decidió dejarla en
   TIMBÓ Compras por audiencia y descubribilidad: la busca el mismo
   personal de Compras/Mesa de Entradas que ya usa ese tema) con 3
   tutoriales: `que-es-compra-directa`, `generar-formulario-cd01` y
   `armar-expediente-y-pase`. Incluye datos operativos concretos: nombre
   exacto del trámite a caratular, marco normativo (inciso 1 art. 116 Ley
   12.510 y Decreto 1104), cómo generar el CD-01 como Documento Oficial con
   firma conjunta, diferencia entre documento incorporado/informativo,
   límite de 50 MB por archivo (solo PDF, nunca escaneados), cómo vincular
   el CD-01 ya firmado al expediente, cómo hacer el pase, y que un
   documento incorporado no se puede eliminar (solo subsanar). Sumó 3
   términos de glosario (CD-01, Gestión Directa por Monto Menor al Tope,
   Documento informativo), 3 tareas y 1 situación nueva.
   Reimportado y verificado: 15 tutoriales, 26 términos, 8 situaciones,
   17 tareas (sobre la base que ya traía los cambios de la sección anterior).
   **No se tocó** `content_timbo_expedientes.json` en esta pasada (otro
   trabajo en paralelo estaba sobre ese archivo). Quedó identificado pero
   sin revisar en detalle: la serie corta "Paso 01" a "Paso 04" (¿cómo
   iniciar/aprobar/evaluar/preadjudicar una licitación?, ~7 meses, más nueva
   que las Clases 01-03) y "Clase 02 - Confección de Pliego..." (1:06:01,
   la que le faltaba a la numeración Clase 01/03 ya cargada) — es altamente
   probable que sean puramente redundantes con la categoría
   `licitaciones-compras` ya cargada (mismos pasos, mismas imágenes), pero
   no se confirmó. Si se quiere cerrar del todo, agregarlos como referencia
   de video a esos tutoriales ya existentes.
   **Búsqueda exhaustiva 2026-11-13 (4) — lado TIMBÓ Expedientes / Atención
   Virtual / ID Ciudadana (trabajo en paralelo al punto anterior, mismo
   canal).** Se armó el catálogo completo del canal "Secretaría de Gestión
   Pública" (81 videos, 11 playlists — ver `@SecretariadeGestionPublica/videos`
   y `/playlists`: Timbó Rendiciones, Enlace Digital, Timboteca con 26 videos,
   Timbó para la Reforma con 13, etc.). El hueco más grande encontrado: casi
   todo el contenido de `content_timbo_expedientes.json` está narrado del
   lado del **agente/oficina**, pero el canal tiene varios videos del lado
   del **ciudadano** que no tenían ningún equivalente en el tema:
   "¿Cómo crear tu ID Ciudadana?" (transcripción completa obtenida),
   "¿Cómo realizar una gestión online en Atención Virtual?" (sin transcripción,
   relevado con screenshots), "Atención Virtual ¿Cómo lo hacemos?" (sin
   transcripción, resultó ser del lado agente — no se profundizó),
   "¿Cómo adherirme al Domicilio Digital en Atención Virtual?", "Consultar un
   Expediente mediante Atención Virtual", "Solicitud de registro en el SIPREC
   por Atención Virtual" y "Presentación de Oficios ante el Registro Civil
   por Atención Virtual" — estos últimos 4 quedaron identificados por título
   pero **sin mirar en detalle** por la limitación de abajo.
   Se agregó el tutorial nuevo `crear-id-ciudadana` (categoría
   `primeros-pasos`, con el detalle completo: URL real
   www.santafe.gob.ar/portalciudadano, que no coincide con la que ya estaba
   en `content_timbo_compras.json` — revisar cuál es la vigente —, 3 formas
   de registro, requisitos de contraseña, cómo adherir el domicilio digital,
   y las 3 formas de recuperar la contraseña + teléfono 0800-770-801) y
   `hacer-tramite-como-ciudadano` (categoría `atencion-virtual`, aclarando
   la diferencia de perspectiva con el resto del módulo). Se amplió la
   situación `olvide-mi-contrasena` con el detalle de recuperación y se sumó
   el término de glosario "Portal Ciudadano". Reimportado y verificado:
   42 tutoriales, 25 términos, 20 situaciones, 33 tareas.
   🔴 **Limitación encontrada — no usar dos forks de navegador en paralelo
   sobre el mismo canal/playlist.** Este trabajo corrió al mismo tiempo que
   el del punto anterior (ambos usando `claude-in-chrome`) y las pestañas
   se pisaron entre sí varias veces (navegaciones de un fork aparecían en la
   pestaña del otro, y `tabs_create_mcp`/`tabs_context_mcp` con
   `createIfEmpty` a veces recreó el grupo completo y tiró el tab del otro).
   Por eso quedaron sin revisar en detalle los 4 videos cortos de Atención
   Virtual mencionados arriba, y el video "Atención Virtual ¿Cómo lo
   hacemos?" (8:45) solo se miró parcialmente. Si se retoma, hacerlo de a
   un fork de browser por vez, o en sesiones separadas.

   ~~Limitación de arriba~~ — resuelto 2026-11-13 (5), trabajando solo (sin
   otro fork tocando el navegador a la vez):

   - **URL de ID Ciudadana, resuelta.** Confirmado en la transcripción de
     "¿Cómo crear tu ID Ciudadana?" (se repite 3 veces) y navegando a ambas
     URLs reales: **www.santafe.gob.ar/portalciudadano** es el punto de
     entrada oficial para crear la cuenta (tiene el botón "Crear cuenta");
     `santafe.gob.ar/idciudadana/...` existe y funciona, pero es para otra
     cosa — **editar datos de una cuenta que ya existe** (aparece como
     link "si tus datos son incorrectos, entrá a santafe.gob.ar/idciudadana"
     dentro de los trámites de Atención Virtual). Se corrigió
     `content_timbo_compras.json` (tutorial `requisitos`) para que use
     `portalciudadano`, igual que ya tenía `content_timbo_expedientes.json`.
   - **Los 4 videos cortos, revisados.** "¿Cómo adherirme al Domicilio
     Digital en Atención Virtual?" (gV_qoxpmAjE) y "Consultar un Expediente
     mediante Atención Virtual" (M2AUtzccRyI) no tenían transcripción —se
     miraron a mano con scrub de video (`currentTime` por JS) y capturas—;
     salieron dos más que no estaban identificados: "Solicitud de registro
     en el SIPREC por Atención Virtual" (XyDulXhA2d0) y "Presentación de
     Oficios ante el Registro Civil por Atención Virtual" (5fTbgJH5Ru8),
     tampoco con transcripción, mismo método. Datos nuevos encontrados:
     - Si la ID Ciudadana está en **nivel 1**, Atención Virtual la rechaza
       con el mensaje exacto "Nivel incorrecto: Usted tiene nivel 1 de
       idCiudadana, para el servicio que desea ingresar debe contar con
       nivel 2 o superior" + botón "Subir nivel" (4 formas: DNI, Mi
       Argentina, Token, AFIP/ARCA).
     - El **Domicilio Digital es obligatorio** para usar Atención Virtual:
       si no está adherido, aparece automáticamente la pantalla "No te
       encuentras adherido" con el texto legal completo y botón
       "Adherirme" → pide correo (de los ya cargados en ID Ciudadana, o
       agregar uno nuevo entrando ahí), celular y aceptar términos.
     - El login de Atención Virtual acepta **CUIL, email o IUP** como
       usuario (IUP: término nuevo de glosario).
     - El buscador de "Nuevo trámite" sugiere por nombre (ej. "SIPREC" →
       "Solicitud de registro en el Sistema Provincial de Capturas,
       Secuestros y Paraderos"); si no aparece el trámite buscado, hay un
       catálogo completo en **santafe.gob.ar/tramites**.
     - Antes de arrancar cualquier trámite, una pantalla "Datos del
       trámite" muestra los datos de contacto ya cargados y el link para
       corregirlos (ver URL de ID Ciudadana arriba).
     - Al consultar el expediente generado: tabla con Nombre/Usuario y
       fecha/Referencia/Orden (carátula, formulario, constancias) más una
       sección aparte "Documentos enviados" con lo que el ciudadano fue
       adjuntando después.
     Todo esto amplió el tutorial `hacer-tramite-como-ciudadano` (categoría
     `atencion-virtual` de `content_timbo_expedientes.json`), sin crear
     tutoriales nuevos. Sumó 1 situación (`nivel-incorrecto-atencion-virtual`),
     2 términos de glosario (IUP, SIPREC) y 2 tareas. **"Atención Virtual
     ¿Cómo lo hacemos?" (8:45) sigue sin profundizar** — ya se había
     confirmado que es del lado agente, de menor prioridad para este hueco
     del lado ciudadano.
     Reimportado y verificado: `content_timbo_expedientes.json` → 42
     tutoriales, 27 términos, 21 situaciones, 35 tareas.
     `content_timbo_compras.json` → 16 tutoriales, 27 términos, 8
     situaciones, 17 tareas (solo cambió la URL, no el conteo).
2. ~~Consultas abiertas en los chats~~ — pasó a "Pendientes (actualizado
   2026-11-13)", más arriba.
3. ~~Conseguir y cargar las guías PDF de artículos o nomenclador SIPAF~~ —
   hecho. Desde el 15/11/2026 se usa solo la guía oficial en 4 pasos
   (`como-solicitar-alta-de-articulos.pdf`). La de "Búsqueda Nomenclador
   SIPAF" se borró porque no es la oficial: no volver a cargarla.
4. Pulido final de UI/UX — pasó a la lista de arriba.

## Equivalencia de artículos (cerrado 2026-11-13)

Sección nueva bajo "Recursos" (junto a "Documentación oficial") en
TIMBÓ Compras: traduce el nombre libre con el que se pide un artículo en
el sistema interno de compras del hospital al código/nombre del Catálogo
WEB oficial de la Provincia, que es el que hay que usar para cargar la
gestión en TIMBÓ Compras. Modelo `EquivalenciaArticulo`
(`app/models/equivalencia_articulo.py`), ruta pública
`/temas/<tema_slug>/equivalencias` (`app/ui/routes.py`), template
`equivalencias.html` (buscador + lista con badge de confianza), semilla
en `scripts/equivalencias_articulos.csv`, importador
`scripts/importar_equivalencias.py`.

Las 89 filas del Pedido 1984 (Microbiología) quedaron completas: no a
mano en el navegador, sino cruzando el nombre de cada artículo contra
`infoTimbo/Catalogo_WEB_al_13112026.csv` (descarga completa del catálogo
oficial, 17.818 filas, columnas separadas por `|`) con un script de
coincidencia de palabras clave — mucho más rápido y confiable que buscar
ítem por ítem en `gestionesdecompras`. Se hicieron **tres** pasadas de
revisión manual (no solo automática) fila por fila, pedido explícito de
la usuaria de dejarlo "lo más completo posible":
1. Primera pasada automática + revisión de las "dudosa" (antibióticos
   combinados con ácido clavulánico/sulbactam, sinónimos de laboratorio,
   errores de tipeo del catálogo) → subió 2 a "alta", corrigió 30.
2. Segunda pasada sobre los "sin_match" con sinónimos técnicos más
   amplios no probados antes (anaerobiosis, sorbitol/O157, Stuart, LAM/
   tuberculosis, papel indicador de pH de rango amplio) → subió 6 más
   (1 a "alta": el escobillón con medio Stuart calzaba exacto; 5 a
   "dudosa").
3. Se completó la nota de los "sin_match" que quedaban sin explicación,
   para que cada uno declare qué sinónimos se buscaron y por qué no hay
   nada razonable (ej. "safranina", "decolorante/alcohol cetona",
   "micoplasma", "agar chocolate" no existen en absoluto en el catálogo).
Resultado final: **19 "alta"** (match exacto), **57 "dudosa"** (hay un
ítem candidato pero sin coincidencia perfecta — ver columna `notas` del
CSV para el motivo puntual de cada uno; 29 de estas 57 son los distintos
antibióticos de la familia BLISTER, para los que el catálogo solo tiene
el ítem genérico "MONODISCOS PARA ANTIBIOGRAMAS" sin discriminar por
antibiótico salvo 2 excepciones ya resueltas como "alta"), **13
"sin_match"** confirmado, cada uno con nota de qué se buscó (puede hacer
falta pedir la incorporación de un ítem nuevo al catálogo para estos
13). Si aparece un pedido nuevo, repetir este método (cruce contra el
CSV del catálogo + revisión manual de las dudosas y sin_match con
sinónimos técnicos del dominio, no búsqueda manual en el navegador desde
cero) salvo que la descarga del catálogo haya quedado desactualizada.

**Ampliado el 13/11 con el nomenclador interno completo**
(`infoTimbo/articulos.csv`, 1000 filas, no solo el Pedido 1984). Mismo
método (cruce contra `Catalogo_WEB_al_13112026.csv`), pero a esta escala
no se revisó cada fila a mano — se usó un script de matching automático
más elaborado que el del Pedido 1984, con dos reglas duras agregadas
después de encontrar errores en una muestra:
1. Los números (dosis de medicamento, calibre de sutura/sonda/tubo) se
   comparan como tokens completos ("3-0" ≠ "0" suelto) — sin esto,
   "ESPIRONOLACTONA 100 mg" matcheaba con "50 MG" por tener el resto del
   texto parecido.
2. "con" / "sin" nunca se tratan como palabras de relleno — sin esto,
   "con aguja" matcheaba con "sin aguja" (la negación se perdía).
Con ambas reglas: un ítem solo sube a "alta" si tiene cobertura total de
palabras clave, similitud de texto alta, Y los números coinciden exacto.
**Las "alta" del nomenclador ya se revisaron a mano, línea por línea
(pedido explícito de la usuaria)** — las 357/361 que había tras el
matching automático, leídas completas (no muestreo). Antes de esa
lectura se agregaron dos reglas automáticas duras más (ambas a partir de
errores reales encontrados en una muestra):
- Forma/vía especial: "SL" (sublingual), "LP"/"AP" (liberación o acción
  prolongada — se tratan como sinónimos), "VAG" (vaginal) y "rectal" no
  pueden ser intercambiables aunque el resto del texto coincida.
- Unidad de dosis como token (ya existía desde el Pedido 1984).
Con esas reglas puestas, la lectura manual completa encontró 6 errores
más que ningún script iba a atajar solo: el pedido pedía un fármaco
**solo** y el único ítem del catálogo era la **combinación en dosis
fija** de ese fármaco con otro (abacavir+lamivudina, fentanilo
+droperidol, timolol+pilocarpina), o una vía distinta no capturada por
las reglas (isosorbide SL↔LP, metronidazol oral↔vaginal, pramipexol
sin especificar↔LP) — las 6 bajaron a "dudosa" con nota explicando el
motivo exacto. Tasa de error real tras las reglas automáticas: ~1,7%
(6 de 357) — bajo pero no cero, por eso vale la pena la lectura manual
en vez de confiar ciegamente en el script.

Las 1000 filas del nomenclador llevan `origen = "Nomenclador interno
completo"` (vs. `"Pedido 1984 - Microbiologia"`) y la nota incluye
`[cod. interno NNN]` para rastrear el artículo original — se puede
filtrar por origen en la UI pública y en el artifact. Resultado final
(1089 filas = 89 del Pedido 1984 + 1000 del nomenclador, ambos con sus
"alta" ya revisadas a mano): **374 "alta"**, **701 "dudosa"**, **14
"sin_match"**.

**Las 644 "dudosa" del nomenclador también se revisaron a mano, completas
(no muestreo) — 2026-11-13.** Fue la pasada más grande: se leyó el archivo
entero y se corrigieron errores sistemáticos que ningún umbral automático
iba a atajar solo. Patrones encontrados, cada uno con docenas de casos:
- **Insumos con marca comercial** (Abbocath, Kertz, Peezer, Argyle, etc.)
  matcheando por palabras genéricas ("descartable", "x1 unidad") contra un
  producto de función clínica totalmente distinta — ej. catéter IV
  matcheado con catéter urinario externo, "tubo de Kertz" con tubo de
  centrífuga de laboratorio, sensor de oximetría con memoria RAM.
- **Medicamentos con el fármaco completamente distinto** al candidato — el
  matching por palabras clave eligió "lo menos malo" cuando no había
  ningún candidato real (Aciclovir↔Timolol, Azatioprina↔Olanzapina,
  Ciclosporina↔Clozapina, Ritonavir solo↔combinado con Lopinavir). Se
  armó una regla automática (`detectar_farmaco_distinto.py` en el
  historial de esta sesión): si la primera palabra del nombre del fármaco
  pedido no aparece en absoluto en el candidato, es señal fuerte de error
  — encontró 20 casos reales entre 34 candidatos sospechosos (el resto eran
  falsos positivos por plurales/sinónimos).
- **Diferencias críticas de concentración/dosis** que cambian el uso
  clínico (agua oxigenada 100 vol vs 10 vol, morfina 50x menos
  concentrada, penicilina 10x menos dosis).
- **Contradicciones de población o tipo** (neonatal vs adulto, estéril vs
  no estéril, con/sin aguja o balón) que el matching por palabras clave no
  detecta porque ambas palabras están "presentes" en algún lado del texto.
- Variantes **ortográficas del mismo fármaco** que en realidad SÍ eran
  buenos matches y estaban subvaloradas (Diazepan/Diazepam,
  Isoniacida/Isoniazida, Octreotide/Octreotida) — estas subieron a "alta".
Resultado de esta pasada sobre las 644: ~50 subieron a "alta", ~86
bajaron a "sin_match", el resto quedó en "dudosa" con nota mejorada donde
aplicaba. Total final (1089 filas): **424 "alta"**, **542 "dudosa"**,
**123 "sin_match"**.

**Las "sin_match" se revisaron a mano, dos veces.** La primera ronda
confirmó que el candidato que había (si lo había) era incorrecto y lo
sacó. La segunda ronda (pedido explícito de la usuaria: "revisá a mano
las sin_match de nuevo con esto") buscó si existía un candidato
**correcto** alternativo que el matching automático simplemente no había
encontrado por usar sinónimos o abreviaturas distintas. Esto resultó ser
un hallazgo grande: **~46 de las "sin_match" SÍ tenían un candidato
correcto en el catálogo** que el algoritmo de palabras clave nunca
encontró —
- Sinónimos de jerga hospitalaria no contemplados: "bigotera" = cánula
  nasal de oxígeno, "Urodrop" = catéter externo masculino, "Tuohy" =
  aguja/kit epidural, "papagayo" = orinal con asa.
- Nombres comerciales sin su equivalente genérico en la búsqueda:
  "Abbocath"/"Terumo" → "catéter intravenoso [calibre]G".
- **El hallazgo más serio: varios medicamentos (Adalimumab, Etanercept,
  Azatioprina, Amiodarona, Nistatina vaginal, Olanzapina, Atropina
  colirio, Ciprofloxacina, Clonazepam, Morfina) SÍ estaban en el
  catálogo con un match casi exacto, pero el algoritmo había elegido
  otro candidato completamente ajeno en su lugar** (ej. Aciclovir
  puntuaba más alto contra Timolol que contra el Aciclovir real del
  catálogo). Esto es un bug real del script de matching, no solo una
  limitación de cobertura — no se investigó la causa raíz en el código
  del script (quedó en el historial de esta sesión, no en el repo), pero
  vale la pena tenerlo presente: **el script de matching automático no es
  confiable al 100% ni siquiera para casos obvios**, cualquier "sin_match"
  merece una revisión manual con grep directo contra el catálogo antes
  de darla por perdida.
Las que siguen sin equivalencia tras ambas rondas tienen en `notas` el
detalle de qué se probó o por qué el candidato descartado era incorrecto.
Si se necesita alguno de estos artículos, la vía es pedir la
incorporación del ítem al catálogo oficial (ver el PDF "Guía en 4 pasos"
en Documentación oficial), no forzar una equivalencia aproximada.
Estado tras esta segunda ronda: **456 "alta"**, **556 "dudosa"**, **77
"sin_match"**.

## Página pública del nomenclador — rediseño 2026-11-13

A pedido de la usuaria ("sumamente UI/UX sencillo y fácil de entender",
"debe estar en el inicio"), se rehizo `equivalencias.html` desde cero:
3 tiles grandes (Listos para cargar / Confirmar antes de usar / Hay que
pedir que se agreguen) que funcionan como filtro al tocarlos, buscador,
selector de origen (Pedido 1984 vs Nomenclador completo), filas en dos
columnas ("Como figura en el pedido" / "Buscar en TIMBÓ como"), y el
paso a paso en 4 pasos (con link a Documentación oficial) que aparece
automáticamente al filtrar por "Hay que pedir que se agreguen". Todo el
filtrado es client-side (los 1089 ítems se mandan una sola vez como JSON
embebido vía `| tojson` — ver `ver_equivalencias` en `routes.py`), sin
recargar la página. Se agregó también:
- Una tarjeta "Nomenclador de artículos" en la portada del tema
  (`tema_inicio.html`), condicionada a `tema.equivalencias_articulos`,
  para que sea visible desde el inicio y no solo en el sidebar.
- El texto del sidebar pasó de "Equivalencia de artículos" a
  "Nomenclador de artículos" (`base.html`).
- Fecha de "Última actualización" (el máximo de `creado_en` de las filas,
  que coincide con la fecha del último `importar_equivalencias.py`
  porque ese script borra y recarga todo).
- Tarjeta "Nomenclador de artículos" también en el portal general
  (`portal_inicio.html`), debajo de las tarjetas de los temas (no
  arriba) — visible desde el `/` del sitio, no solo dentro de TIMBÓ
  Compras.
- Callout corto explicando "Confirmar antes de usar" (categoría
  "dudosa"), visible solo con ese filtro activo.
  🔴 **Bug real encontrado y corregido**: el callout usaba la clase
  `.callout` del sistema de diseño, que fija `display:flex` explícito —
  esto **anula el atributo HTML `hidden`** por empate de especificidad
  (gana la última regla de autor). El bloque quedaba siempre visible sin
  importar el filtro. Se corrigió agregando `#id[hidden]{display:none}`
  específico. Ojo con esto si se reusa `.callout` (o cualquier clase con
  `display` explícito) en otro lugar controlado por el atributo `hidden`
  vía JS — hace falta la misma regla de override.
- Se agregaron 2 PDFs más a Documentación oficial (misma carpeta
  `app/static/docs/timbo-compras/`): "Guía en 4 pasos..." y "Guía
  completa: búsqueda en el Nomenclador TIMBÓ y solicitud de artículos
  faltantes (paso a paso del formulario CAByS)" — este último es el
  instructivo detallado (6 páginas, con capturas reales del sistema) que
  complementa al resumen de 4 pasos.

## Buscador/chatbot: ahora indexa el Nomenclador

`app/services/buscador.py` → `construir_indice(tema)` agrega una entrada
por cada `EquivalenciaArticulo` del tema (`kind: "Nomenclador"`), indexando
solo nombre/bien/ítem específico (nunca las `notas`, que son texto libre
largo y ensuciarían el ranking con coincidencias espurias). Esto hace que
el buscador global, el buscador por tema, y el chatbot encuentren
artículos del nomenclador por nombre. `armar_respuesta_chatbot()` tiene
un caso nuevo para este `kind`: muestra el código si lo hay, avisa
"confirmá antes de usarlo" si es "dudosa", o "hay que pedir que lo
agreguen" si es "sin_match". Probado con `curl` contra
`/temas/timbo-compras/buscar.json`, `/buscar.json` (global) y
`/temas/timbo-compras/chatbot` (POST) — los tres funcionan.

## Nomenclador contra el Catálogo WEB completo (16/11/2026)

- El catálogo oficial completo se baja del Catálogo WEB con «Descargar Excel» sin filtros
  (`output.php?a=catalogo.get_csv`, 17.818 ítems, separado por `|`). No trae bodega.
- Los 936 renglones con código siguen existiendo y con el mismo texto.
- 34 renglones rojos tenían un candidato claro en el catálogo completo (butterfly, Kehr,
  Peezer, manguitos neonatales, lanreotida, cotrimoxazol, ortoftalaldehído, etc.): pasaron a
  amarillo con la nota "candidato encontrado el 16/11/2026… Confirmar antes de usar". Quedan
  30 rojos. Para repetir: bajar el catálogo y cruzar los rojos por palabras y medidas.
- Amarillos (16/11/2026): se cruzaron los 533 con el catálogo completo. En 119 había un ítem que
  coincide en medida o dosis con el pedido (sobre todo remedios con otra dosis, tubos
  endotraqueales, sondas, suturas y agujas): se cambió el código, siguen en amarillo con la nota
  "actualizado el 16/11/2026…". Se revisaron a mano; los dudosos quedaron como estaban.
- Estadísticas: desde el 16/11 no cuentan robots ni controles automáticos
  (`estadisticas.es_automatico`). Las vistas viejas mezclan robots (≈452 de 769) con personas.
- Rojos y amarillos sin medida (16/11/2026, noche): 25 amarillos sin medida apuntaban a un código
  de otra edad o tipo (pañales de niño con código de adulto, válvula espiratoria con "cemento
  biológico", etc.): se cambiaron y siguen en amarillo. Los guantes de látex apuntaban a un bien
  que el catálogo marca «NO UTILIZAR». El manguito neo Nº 5 y la cánula CPAP grande no existen en
  el catálogo: pasaron a rojo. Quedan 437 verdes, 531 amarillos y 32 rojos. Al reescribir notas,
  conservar el `[cod. interno N]` (se había perdido en 117 y se devolvió desde 85d04c6).
- Página del nomenclador: la búsqueda no distingue tildes ni orden de palabras y busca también
  por código; botón "Copiar" junto al código; las etiquetas dicen lo mismo que las tarjetas; las
  notas se muestran sin lo técnico ("match automatico…").

## Documentos oficiales leídos el 16/11/2026 (noche)

Se cruzaron las páginas de normativa de TIMBÓ (`/ms/timbo/normativa/`) y de Compras
(`compras.santafe.gob.ar/normativas/`) contra la biblioteca: 12 documentos nuevos (Circ. UG
1/2024, 2/2024, 3/2024, 1/2025, 5/2025, 4/2026, 5/2026, 6/2026; Dec. 2233/2016, 923/2019,
914/2018; Circ. SCyGB 003/2025 del RDAM) y se completó la lectura de la Circ. UG 3/2025, la 2/2025,
el Dec. 667/2019 (tope 30 %), la Res. 101/2019 y, con reconocimiento de texto de Windows, las
escaneadas (Disp. 226, 227, 282 y Res. 211/2018, Ley 14.295). Para repetir el OCR: renderizar con
pymupdf y pasar `Windows.Media.Ocr` (es-ES) desde PowerShell. Respuestas nuevas: RDAM, trámites de
personal solo digitales, plazo de las comunicaciones oficiales, número y rechazo de resoluciones,
convenios, Compre Santafesino, alquileres, economía social, OCA, Convenio Marco, Foja Cero.
Videos: la capacitación qVf-yyXoE0k y el de la Biblioteca Digital de Normativa (SDAEZ_4rjZo) ya
tienen subtítulos y están leídos. La Ley 12.510 y el Dec. 1104/16 siguen "por temas" (son largos;
las lecciones citan los artículos que usan).
