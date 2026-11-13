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
2. Consultas abiertas en los chats: SIN sin "comenzar una carga",
   numeración de decisorios, documentos HTML→PDF y servidor propio para
   los videos. Cuando haya respuesta, pasar a `verificado: True` en
   `scripts/importar_faq_chats.py`.
3. Conseguir y cargar las guías PDF de artículos o nomenclador SIPAF.
4. Pulido final de UI/UX.

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
