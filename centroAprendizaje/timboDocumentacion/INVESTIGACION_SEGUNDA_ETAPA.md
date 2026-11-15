# Segunda etapa: auditoría e investigación documental

Relevado el 15/11/2026. Es la base para desarrollar los recursos privados de
`/admin` (roles, glosario, biblioteca, fichas FP, flujos, proveedores y
examen). Nada de esto está publicado.

Cada dato lleva una de estas marcas:

- ✅ **Confirmado**: lo dice un documento oficial (se cita cuál).
- 📘 **Didáctico**: explicación o recomendación nuestra, armada a partir de
  lo confirmado. No es norma.
- ⏳ **Pendiente**: no hay documento oficial que lo diga. No se va a
  presentar como cierto.

---

## 1. Auditoría del proyecto

**Qué hay:**
- Tres temas públicos: miHospital, TIMBÓ (Expedientes) y TIMBÓ Compras.
  Suman 97 lecciones, 92 términos de glosario, 50 situaciones, 91 tareas y
  1089 equivalencias de artículos.
- Chatbot local.
- Consultas con seguimiento.
- Panel `/admin`, con usuario y contraseña. Tiene temas, lecciones,
  glosario, situaciones, tareas, consultas, opiniones, estadísticas e
  imágenes.
- Fuentes oficiales relevadas en `FAQ_SOPORTE_TIMBO.md`, secciones 4, 4.1,
  4.2 y 5.

**Errores y huecos encontrados:**

| Problema | Estado |
|---|---|
| Las flechas de los 7 ejercicios de ordenar nunca funcionaron: siempre estaban desactivadas | Corregido en local (`82a7d1a`), con prueba automática. Falta deployar |
| Guía de artículos no oficial ("Búsqueda Nomenclador SIPAF") | Reemplazada por la oficial en local (`20c458a`). Falta deployar |
| El glosario de Compras lista 3 roles. La Circular UG 7/2026 define 5 (faltan **Jurisdicción comitente** y **Oferente/Proveedor**) | Para corregir en la tanda de recursos |
| La Circular UG 7/2026, que es la fuente de los roles, no estaba en la lista de fuentes de la sección 5 | Se suma acá |
| Faltan normas de 2026 sobre proveedores: Res. SCyGB 110/2026 (nuevo procedimiento RUPC), prórrogas 125/175/205/260, Circular SCyGB 006/26 y Res. ME 73/2026 | Se suman acá |
| El portal dice que hay que estar en el RUPC, pero no explica cómo inscribirse | Para la tanda de proveedores |
| No hay ejercicios de asociar (rol ↔ tarea) ni de casos | Para la tanda de formación |

---

## 2. Fuentes oficiales

Todas se bajaron y se leyeron completas el 15/11/2026.

### 2.1 Unidad de Gestión TIMBÓ (www.santafe.gob.ar/ms/timbo/normativas/)

| Documento | Fecha | Tema | Uso en el centro |
|---|---|---|---|
| [Circular UG 7/2026](https://www.santafe.gob.ar/ms/timbo/wp-content/uploads/sites/68/2026/05/CIRCULAR-7-UG-TYC-TIMBO-COMPRAS.pdf) | 2026 | **Términos y condiciones de TIMBÓ Compras**: roles, etapas por sistema, comisión de evaluación, plazos, notificaciones, ofertas, apertura, impugnaciones, glosario | Roles · Circuito · Glosario · Examen |
| [Circular UG 1/2026](https://www.santafe.gob.ar/ms/timbo/wp-content/uploads/sites/68/2026/01/Circular-01-2026-Implementacion-TIMBO-COMPRAS.pdf) | 2026 | TIMBÓ Compras obligatorio (primeras jurisdicciones). "Alta de perfiles y roles ante el administrador local". Contingencia técnica | Roles · Biblioteca |
| [Circular UG 3/2026](https://www.santafe.gob.ar/ms/timbo/wp-content/uploads/sites/68/2026/03/Circular-03-26.pdf) | 2026 | Obligatorio en todos los ministerios, incluido **Salud**, desde el 1/4/2026. Ejecución operativa descentralizada | Circuito · Biblioteca |
| [Circular UG 2/2026](https://www.santafe.gob.ar/ms/timbo/wp-content/uploads/sites/68/2026/03/Circular-02-26.pdf) | 2026 | RUPC: requisitos de inscripción y de participación; qué verifica la jurisdicción contratante; legajo digital; declaración jurada unificada | Proveedores · Consulta de proveedores |
| [Circular UG 8/2026](https://www.santafe.gob.ar/ms/timbo/wp-content/uploads/sites/68/2026/07/Circular-8-26_TIMBO-COMPRAS.pdf) | 2026 | Directas por urgencia o desierto por TIMBÓ Compras | Circuito |
| [Circular UG 9/2026](https://www.santafe.gob.ar/ms/timbo/wp-content/uploads/sites/68/2026/07/Circular-9-2026-UNIDAD-DE-GESTION-TIMBO.pdf), [10/2026](https://www.santafe.gob.ar/ms/timbo/wp-content/uploads/sites/68/2026/07/Circular-10_Determina-fecha-de-entrada-en-vigencia-de-Circular-9.pdf), [11/2026](https://www.santafe.gob.ar/ms/timbo/wp-content/uploads/sites/68/2026/08/Circular-11_2026-TCP-2.pdf) | 2026 | Vista al Tribunal de Cuentas, SIN y entrada en vigencia | Circuito |
| [Circular UG 3/2025](https://www.santafe.gob.ar/ms/timbo/wp-content/uploads/sites/68/2025/08/3_2025-Circular-Pautas-Generales-para-la-Gestion-Digital-TIMBO.pdf) | 7/7/2025 | **Reglamento general de gestión digital**: oficinas, usuarios, permisos (art. 3 a 5), credenciales, expedientes | Roles (Expedientes) · Glosario |
| [Circular UG 4/2025](https://www.santafe.gob.ar/ms/timbo/wp-content/uploads/sites/68/2025/08/4_2025-Circular-Actos-administrativos.pdf) | 2025 | Actos administrativos, firma electrónica vs. digital, validación en el Firmador Digital Web | Glosario · PDF |
| [Circular UG 8/2025](https://www.santafe.gob.ar/ms/timbo/wp-content/uploads/sites/68/2025/12/Circular-N8-2025-UG-timbo-1.pdf) | 23/12/2025 | Publicación en el Boletín Oficial con enlace al **Sistema de Información Normativa** | Glosario (SIN) |
| [Circular UG 5/2024](https://www.santafe.gob.ar/ms/timbo/wp-content/uploads/sites/68/2024/11/Circular-05-Validacion-Firma-Digital-3.pdf) | 2024 | Validación de documentos con firma digital o electrónica | PDF · Glosario |
| Circulares UG 6/2026, 4/2026, 5/2026, 7/2025 y 3/2024 | 2024-2026 | Notificaciones y domicilio digital, nueva gestión digital, papel cero en MGeIP, no pedir documentación ya disponible, trámites digitales | Biblioteca (Expedientes) |

### 2.2 Subsecretaría de Contrataciones y Gestión de Bienes (compras.santafe.gob.ar/normativas/)

| Documento | Fecha | Tema | Uso |
|---|---|---|---|
| [Res. ME 73/2026](https://compras.santafe.gob.ar/wp-content/uploads/sites/87/2026/06/Res.-ME-N.%C2%B0-0073-2026.pdf) | 7/4/2026 | Desde el 15/4/2026 las licitaciones y concursos públicos por TIMBÓ Compras los gestionan **íntegramente las Unidades Operativas** de la Administración Pública Central. Controles obligatorios de la URC: pliego y preadjudicación | Circuito · Roles |
| [Circular SCyGB 03/2026](https://compras.santafe.gob.ar/wp-content/uploads/sites/87/2026/04/CIRCULAR-003-26.pdf) | 15/4/2026 | Cuándo mandar el expediente a la URC ("Aprobar contratación" y "Cronograma de impugnación"). **Datos de la mesa de ayuda** | Circuito · Soporte |
| [Res. SCyGB 110/2026](https://compras.santafe.gob.ar/wp-content/uploads/sites/87/2026/04/Resolucion-Proveedores-N%C2%B0-00000110-Nuevo-Procedimiento-Inscripcion-RUPC.pdf) | 2026 | **Nuevo procedimiento de inscripción en el RUPC**: portal, plazos, documentación por tipo de persona, requisitos técnicos | Proveedores (inscripción y mini instructivo) |
| Res. SCyGB [125](https://compras.santafe.gob.ar/wp-content/uploads/sites/87/2026/04/RES-2026-00000125-APPSF-PE_MEC_SLyT-SbCyGB.pdf__files-job_63.pdf), [175](https://compras.santafe.gob.ar/wp-content/uploads/sites/87/2026/06/RES-2026-00000175-APPSF-PEMECSLyT-SbCyGB.pdf), [205](https://compras.santafe.gob.ar/wp-content/uploads/sites/87/2026/06/RES-2026-00000205-APPSF-PEMECSLyT-SbCyGB.pdf) y [260/2026](https://compras.santafe.gob.ar/wp-content/uploads/sites/87/2026/09/RESOLUCION-260.pdf) | 2026 | Prórrogas de inscripciones RUPC vencidas con renovación iniciada en 2026 (31/5, 30/6, 31/8 y, la última, **31/12/2026**) | Proveedores (aviso de versiones) |
| [Circular SCyGB 006/2026](https://compras.santafe.gob.ar/wp-content/uploads/sites/87/2026/08/CIRCULAR_006-26_SCYGB.pdf___non-Linux-generated_files-job_287.pdf) | 22/7/2026 | Se suprimió el RBPCME: solo queda el RUPC. Quién no va al RUPC (alta de beneficiario en SIPAF) | Proveedores · Glosario |
| [Decreto 1104/2016](https://www.santafe.gob.ar/ms/compras/wp-content/uploads/sites/87/2025/10/2_Decreto-N%C2%B01.104-2016.pdf) | 2016 (con modificaciones) | Reglamento de la Ley 12.510. Comisión Evaluadora "conforme se establezca en el PBCP"; su opinión no es vinculante | Roles (evaluadores) |
| Circulares SCyGB 01, 04 y 05/2026, Circular 04/2025, Res. 292/2026, Pliego Único (Dec. 287/2026) | 2025-2026 | Ya relevadas en la sección 5 de `FAQ_SOPORTE_TIMBO.md` | Ya en uso |

### 2.3 Material de capacitación oficial

- Videos de las listas "Timbó Compras" (proveedor) y "APP-TimboCompras"
  (organismo), y del canal de la Secretaría de Gestión Pública. Ya están
  relevados en las secciones 4, 4.1 y 4.2 del FAQ. Se volvieron a bajar los
  subtítulos para buscar "Visualizar" y "Detalle".
- Instructivos PDF del lado proveedor (`app/static/docs/timbo-compras/`) y
  la infografía oficial "¿No encontrás un artículo en TIMBÓ?" del
  Ministerio de Salud.

### 2.4 Sitios oficiales comprobados (15/11/2026)

| Sitio | Estado |
|---|---|
| www.santafe.gob.ar/ms/timbo/ | Responde. Solo enlaza a ID Ciudadana, Normativas e "Ingresá acá" (tramites.santafe.gob.ar). No publica canales de soporte |
| www.santafe.gov.ar/proveedores | Responde. Es la plataforma del RUPC (Res. 110/2026) |
| compras.santafe.gob.ar (y /tutoriales/) | Responde |
| Validación de firma (santafe.gob.ar/firma/pages/validacion/…) | **Ahora pide iniciar sesión**. La Circular 5/2024 la citaba como sitio público |
| app.santafe.gov.ar/normativa (SIN) | No responde desde fuera de la red. Coincide con lo de los chats: solo desde la red institucional |

---

## 3. Qué quedó confirmado

### 3.1 Roles de TIMBÓ Compras (Circular UG 7/2026, punto 10) ✅

| Rol | Qué hace (texto oficial, resumido) |
|---|---|
| **Gestor** | Genera la instancia de contratación. Completa los formularios del PBCP. Genera circulares |
| **Supervisor** | Aprueba o rechaza los formularios del PBCP. Confecciona el cronograma y la nómina de proveedores. Carga los actos administrativos que aprueban el pliego y autorizan el llamado, los "sin efecto" y la adjudicación |
| **Evaluador** | Evalúa las ofertas. Genera los trámites de subsanación, mejora de precios y aclaración o documentación complementaria. Preselecciona renglones y oferentes. Organiza a los evaluadores. Preadjudica. Carga el cronograma de impugnaciones. Recibe las impugnaciones |
| **Jurisdicción comitente** | Revisa los pliegos de bases y condiciones particulares |
| **Oferente/Proveedor** | Accede a los procesos publicados, presenta ofertas, consulta, recibe notificaciones en su domicilio digital e impugna |

También confirmado:
- La información del proceso solo la ven "los usuarios cuyos roles
  designados se correspondan al proceso" (Circ. 7/2026, punto 9).
- Hay que designar **al menos 3 evaluadores** en el formulario "Evaluadores"
  del PBCP (Circ. 7/2026, punto 13).
- El informe de preadjudicación lo firman los evaluadores en el orden del
  formulario "Ordenar evaluadores" (punto 22).
- La Comisión Evaluadora se forma "conforme se establezca en el PBCP" y su
  opinión no es vinculante (Dec. 1104/16).
- Los roles se piden **ante el administrador local de cada jurisdicción**
  (Circ. UG 1/2026, punto 4, y 3/2026, punto 6).

### 3.2 Usuarios y permisos de TIMBÓ en general (Circular UG 3/2025, art. 3 a 5) ✅

Son cosas distintas, y el centro las va a mostrar por separado:

| Concepto | Qué dice la norma |
|---|---|
| **Usuario** | Solo personal con vínculo vigente con la administración provincial (art. 4.a). Puede estar en más de una oficina (art. 4.b) |
| **Oficina** | Se organiza por criterio funcional. Una sola Mesa de Entradas por ministerio u organismo (art. 3) |
| **Permiso de carátula** | Solo Mesas de Entradas o Despachos, ministros, sus secretarías privadas y secretarios y subsecretarios políticos (art. 4.c) |
| **Demás permisos** | Según las tareas que efectivamente hace cada persona (art. 4.d) |
| **Quién pide el alta o la baja** | Funcionarios políticos o personal de planta con jerarquía no menor a **jefe de departamento**, por **iTop** (art. 5.C) |
| **Quién la carga** | La **Sectorial de Informática** (altas y bajas) y, para oficinas, la Sectorial y/o los **administradores locales**, después de la validación institucional (art. 5.A.3 y 5.C) |
| **Quién controla** | La **UG TIMBÓ** puede revisar, modificar o revocar permisos (art. 4.e) |
| **Credenciales** | Personales e intransferibles. Lo hecho con la clave se presume hecho por su titular (art. 2.c) |

Esto confirma lo que pediste: quien carga usuarios (Informática o el
administrador local) **no** es quien autoriza. Autoriza la jefatura o el
funcionario que lo pide.

### 3.3 Qué se hace en cada sistema (Circular UG 7/2026, punto 6) ✅

| Etapa | Dónde se hace |
|---|---|
| Etapa preparatoria (pedido, afectación, autorización para iniciar) | **Expediente electrónico** de TIMBÓ |
| Pliego, consultas y circulares, impugnaciones, apertura, ofertas, evaluación, subsanación y mejora, informe de preadjudicación | **TIMBÓ Compras** |
| Adjudicación y etapa contractual | **Expediente electrónico** de TIMBÓ |
| Publicación en el portal web, aviso oficial por mail, carga en el SIN y vista al TCP | **Fuera de TIMBÓ Compras**: portal, correo, SIN, y "Gestión de Visualización" del expediente (Circ. SCyGB 04/2026; UG 9 y 11/2026) |
| Controles de la URC (pliego y preadjudicación) | Por **expediente electrónico**, con pase a la Dirección General de Contrataciones (Res. ME 73/2026; Circ. SCyGB 03/2026) |
| Inscripción de proveedores (RUPC) | **Sistema de Gestión de Proveedores Web** (www.santafe.gov.ar/proveedores), no TIMBÓ (Res. 110/2026) |

Otros datos confirmados del proceso (Circ. UG 7/2026):
- Los plazos se rigen por la hora del servidor de TIMBÓ Compras.
- Al personal se le avisa con "correos de cortesía", que no son
  notificación válida. La notificación vale desde el evento del sistema.
- La apertura es automática y genera el acta y el cuadro comparativo.
- Solo valen las ofertas en estado "Oferta presentada".
- Archivos en PDF, de hasta 5 MB recomendados.
- Si el proveedor no responde un subtrámite a tiempo, pasa a "descartado".

### 3.4 Sistemas relacionados con TIMBÓ ✅

| Sistema | Qué es | Fuente |
|---|---|---|
| **SIN: Sistema de Información Normativa** de la Provincia | Donde se cargan las normas. El Boletín Oficial enlaza a las leyes y decretos cargados ahí. Para Compras: todo acto se carga en el SIN y se envía al TCP | Circ. UG 8/2025; Circ. UG 11/2026 |
| **SIPAF** | Sistema de administración financiera. Ahí se dan de alta los beneficiarios de pago que no van al RUPC | Circ. SCyGB 006/2026 |
| **RUPC** / Sistema de Gestión de Proveedores Web | Registro de proveedores. Inscripción sin vencimiento. Desde la Circ. UG 2/2026, el RUPC solo administra la inscripción: la Unidad Operativa verifica los requisitos de participación | Res. 110/2026; Circ. UG 2/2026 |
| **ID Ciudadana** y **domicilio digital** | Identidad digital (nivel 3 para proveedores) y bandeja de notificaciones fehacientes | Circ. UG 7/2026 (glosario); Circ. UG 2/2026 |
| **iTop** | Canal técnico para pedir altas, bajas y permisos | Circ. UG 3/2025, art. 5 |
| **Portal de Compras** (gestionesdecompras) | Publicación de las gestiones: "Detalle" de cada una, con pliegos y circulares | Sitio oficial; Circ. SCyGB 04/2026 |
| **Firmador Digital Web** | Firma y validación de documentos | Circ. UG 4/2025 y 5/2024 |
| **Atención Virtual** / Gestión Virtual | Trámites ciudadanos y acceso del proveedor (gestionvirtual.santafe.gob.ar) | Circ. UG 3/2025; Portal de Compras |
| **ARCA** (ex AFIP) | Clave fiscal nivel 3 y servicio "ECON SANTA FE – Registro Único de Proveedores y Contratistas" para inscribirse | Res. 110/2026, anexo V |

### 3.5 Inscripción de proveedores (Res. SCyGB 110/2026 y Circ. UG 2/2026) ✅

- **Dónde:** www.santafe.gov.ar/proveedores (Sistema de Gestión de
  Proveedores Web).
- **Requisitos técnicos:**
  - clave fiscal nivel 3 con el servicio "ECON SANTA FE – Registro Único de
    Proveedores y Contratistas";
  - archivos PDF de hasta 8 MB cada uno;
  - escaneo a 200 dpi para texto y 300 dpi en color si hace falta.
- **Documentación** (anexos II a IV):
  - **Personas humanas:**
    - poder ante escribano, si actúa un apoderado;
    - certificado negativo del Registro de Deudores Alimentarios;
    - declaración jurada de ID Ciudadana y domicilio digital;
    - Libre Deuda de la Ley 17.250, de no más de 30 días.
  - **Personas jurídicas:** lo mismo, más el estatuto y la designación de
    autoridades, solo si no están radicadas en Santa Fe. El certificado de
    deudores alimentarios lo presentan todos los miembros del órgano de
    administración.
  - **UT:** las firmas que la forman tienen que estar inscriptas antes.
- **Plazos:** 30 días corridos para completar lo que falte desde la
  notificación; si no, el trámite se da de baja solo. Acepta o rechaza la
  SCyGB, por acto administrativo.
- **Notificaciones:** por mail, a la dirección del domicilio digital.
- **Vigencia:** sin caducidad, mientras no cambien las condiciones. Quienes
  se inscriben quedan suscriptos al Boletín Electrónico de Compras.
- **Qué verifica el hospital al evaluar** (Circ. UG 2/2026, punto B):
  - inscripción en el RUPC;
  - que el objeto o la actividad coincida con lo que se contrata;
  - idoneidad técnica, capacidad financiera y requisitos del pliego;
  - que el proveedor mantenga la aptitud.

  Al terminar el contrato, el hospital manda al RUPC un **informe de
  desempeño**.

### 3.6 Soporte oficial ✅

- **Mesa de ayuda de TIMBÓ Compras** (Circ. SCyGB 03/2026):
  - correo: timbocompras@santafe.gob.ar;
  - teléfono: 0342-4506600 / 4506800, internos 39479 y 39480;
  - WhatsApp: +54 9 342 640-0792;
  - horario: de 8 a 13.
- **Altas, bajas y permisos:** iTop (Circ. UG 3/2025).
- **Inscripción de proveedores:** el propio RUPC, por la plataforma y por
  mail (Res. 110/2026).
- **Imposibilidad técnica de usar TIMBÓ Compras:** la UG TIMBÓ, como
  autoridad de aplicación, puede autorizar otra vía (Circ. UG 1/2026, punto
  7). Dudas sobre el RUPC: la UG y el RUPC (Circ. UG 2/2026, punto 6).

### 3.7 Lector de PDF

- ✅ La capacitación oficial a proveedores muestra que los anexos de los
  pliegos van "embebidos" en el PDF y se ven con el panel de adjuntos del
  "previsualizador de Adobe". Lo mismo dice la Circ. UG 7/2026, punto 7.
- 📘 Recomendación: **Adobe Acrobat Reader**, gratis, desde
  get.adobe.com/es/reader (el sitio responde). Es la herramienta que usa la
  capacitación oficial y muestra adjuntos y firmas. Hay que destildar las
  ofertas de programas extra del instalador. No es parte de TIMBÓ.

---

## 4. Pendiente de verificar ⏳

| # | Qué falta | Por qué | Cómo se puede resolver |
|---|---|---|---|
| 1 | **"Visualizar" vs. "Detalle"** | No aparecen como opciones en ninguna fuente oficial. Los videos muestran ⋮ → **Previsualizar**, **Ver flujo**, **Historial** y **Acciones**. "Detalle" solo aparece en el Portal de Compras público y como nombre del formulario "Detalle de producto y servicio" | Necesito saber **en qué pantalla las ves** (una captura con los datos tapados) |
| 2 | **Quién autoriza** que alguien tenga el rol Gestor, Supervisor o Evaluador | La norma solo dice "tramitar ante el administrador local". No dice quién firma el pedido | Preguntar a la mesa de ayuda o a la UG TIMBÓ. Mientras tanto: "quién autoriza: no establecido" |
| 3 | Si la designación de la Comisión Evaluadora necesita un acto administrativo aparte | El Dec. 1104/16 la remite al PBCP, y la Circ. 7/2026 al formulario "Evaluadores" | Consultar a Compras del hospital o a la URC |
| 4 | Si la Res. ME 73/2026 y la Circ. SCyGB 03/2026 (controles de la URC) alcanzan a los **hospitales** | Están dirigidas a la "Administración Pública Central". Depende de cómo esté encuadrado cada efector | Confirmar con Compras del hospital (ya estaba en pendientes) |
| 5 | **Consulta de proveedores desde el hospital** (si hay una pantalla en TIMBÓ para buscarlos y ver su legajo) | Ninguna fuente oficial muestra esa pantalla. La Circ. 2/2026 habla de un "legajo digital" que arma el RUPC, sin decir quién lo consulta ni dónde | Captura o consulta a la mesa de ayuda |
| 6 | Requisitos y pasos del **curso de Administrador Local** (curso "Paso a paso" + iTop + matrícula) | Sale de los chats de soporte, no de una norma | Se va a mostrar como "práctica informada por soporte", no como norma |
| 7 | **Validar una firma** sin usuario | El sitio que cita la Circ. 5/2024 ahora pide iniciar sesión | Probarlo desde la red del hospital |
| 8 | Horario de soporte de TIMBÓ (Expedientes) | No está publicado. Solo está el de la mesa de ayuda de Compras | — |
| 9 | Estados exactos del proceso en pantalla | Las circulares y videos nombran varios (Aprobar contratación, Publicado, Evaluar ofertas, Cronograma de impugnación, Preadjudicado), pero no hay una lista oficial completa | Armar la lista con los que nombran las fuentes y marcar el resto como no relevado |

---

## 5. Cómo se van a armar los recursos

- **Roles:** tabla y esquema con 3 columnas separadas: **quién pide**,
  **quién carga** y **quién autoriza**. Lo que no está escrito va a decir
  "no establecido en la normativa".
- **Fichas FP-01, FP-02…:** cada paso con su marca (TIMBÓ Compras,
  expediente electrónico o fuera del sistema) y con la cita oficial.
- **Flujos:** los pasos que dependen de algo externo (URC, SIN, portal,
  RUPC) van con otro color y la etiqueta "externo".
- **Examen:** casos de Compras de un hospital, armados solo con lo de la
  sección 3. Por ejemplo:
  - un evaluador que quiere cargar el acto de adjudicación;
  - un proveedor que no está en el RUPC;
  - una oferta que quedó en borrador;
  - un pliego sin informe de la URC.

---

## 6. Revisión complementaria (15/11/2026)

**Dos "Circulares 03/2026" distintas.** No hay que confundirlas:

| Circular | Emisor | Fecha | Qué dice | Respalda |
|---|---|---|---|---|
| [Circular UG TIMBÓ 3/2026](https://www.santafe.gob.ar/ms/timbo/wp-content/uploads/sites/68/2026/03/Circular-03-26.pdf) | Unidad de Gestión TIMBÓ | 2026 (marzo) | TIMBÓ Compras obligatorio en los ministerios restantes, incluido Salud, desde el 1/4/2026. Roles ante el administrador local | Obligatoriedad · roles |
| [Circular SCyGB 03/2026](https://compras.santafe.gob.ar/wp-content/uploads/sites/87/2026/04/CIRCULAR-003-26.pdf) | Subsecretaría de Contrataciones y Gestión de Bienes | 15/4/2026 | Controles de la URC en "Aprobar contratación" y "Cronograma de impugnación". **Datos de la mesa de ayuda de TIMBÓ Compras** | Controles URC · **mesa de ayuda** |

El contenido del centro ya cita cada una con su emisor (se revisaron todas
las menciones).

**Decreto 287/2026** (23/2/2026). Aprueba el Pliego Único y modifica los
artículos 123, 130, 131, 132, 139 y 142 del Dec. 1104/16. Para el
contenido:
- ✅ El PBCP lo elaboran y aprueban "los órganos competentes de las
  Jurisdicciones o Entidades" (art. 131.3), con la lista de lo que tiene que
  incluir.
- ✅ La Comisión Evaluadora actúa "conforme lo establecido en el PBCP", y su
  opinión no es vinculante (art. 123).
- ✅ Se derogó la **foja cero** (art. 4) y se suprimió el **RBPCME** (art. 5).
- ⚠️ **Discrepancia, pendiente de resolver.**
  - El art. 142, en la versión del Dec. 287, dice que la calidad de
    proveedor se otorga "por un tiempo de vigencia preestablecido" y que
    vencido hay que renovarla.
  - La Circ. UG 2/2026 y la Res. SCyGB 110/2026 dicen que la inscripción en
    el RUPC es "sin plazo de caducidad".
  - Las prórrogas 125/175/205/260 hablan de "inscripciones vencidas" con
    renovación iniciada.
  - No se elige ninguna: el centro va a mostrar las dos y marcarlo como
    pendiente de confirmar con el RUPC.

**Res. SCyGB 292/2026** (catalogación). La lección "Pedir el alta de un
artículo" coincide paso a paso con el anexo I:
- búsqueda previa;
- formulario "Timbó Compras: Alta de bienes y servicios CAByS";
- grilla de bienes;
- código externo obligatorio para hospitales;
- lugares de entrega;
- firma del responsable;
- aprobación de la URC con aviso por correo.

La resolución nombra a dos personas como destinatarios. El centro dice "el
destinatario que indica la resolución", así no queda desactualizado ni
publica nombres.

**Control de la URC en hospitales.** Sigue ⏳ pendiente hasta confirmar el
encuadre institucional del hospital. En las lecciones de Compras se marcó
así en los 5 lugares donde aparece:
- los dos pasos de control de "Hacer una compra";
- el paso de "Preadjudicar";
- el ejercicio de ordenar;
- el glosario.
