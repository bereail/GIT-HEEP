# Nomenclador de artículos — Informe de investigación (etapa 1)

Fecha: 19/11/2026 · Rama: `nomenclador-capacitacion` · Estado: **borrador interno, sin publicar**

Este informe separa lo que dice la documentación oficial de lo que todavía hay que
confirmar. No describe pantallas, botones, roles ni circuitos que no estén escritos en
una fuente. Lo que falta lleva la etiqueta **PENDIENTE DE CONFIRMACIÓN**.

Las correcciones al contenido ya publicado están en
[`NOMENCLADOR_CORRECCIONES_PROPUESTAS.md`](NOMENCLADOR_CORRECCIONES_PROPUESTAS.md).

## Referencias de estado

| Marca | Significa |
|---|---|
| ✅ | Lo dice textualmente un documento oficial publicado (con enlace) |
| 👁️ | Observado directamente en un sistema oficial público (fecha indicada), sin norma que lo diga |
| 🏥 | Respuesta interna del hospital, sin documento oficial publicado detrás |
| ⏳ | PENDIENTE DE CONFIRMACIÓN: no hay fuente oficial |

## 1. Fuentes revisadas

| Id | Documento | Emisor / fecha | Enlace | Lectura | Aporte |
|---|---|---|---|---|---|
| F1 | Res. SCyGB 292/2026: Procedimiento Digital de Catalogación de Bienes, Servicios y Lugares de Entrega en TIMBÓ COMPRAS y SIPAF | Subsecretaría de Contrataciones y Gestión de Bienes, 06/10/2026 | [PDF](https://compras.santafe.gob.ar/wp-content/uploads/sites/87/2026/10/RES-2026-00000292-APPSF-PEMECSLyT-SbCyGB.pdf) · también [santafe.gov.ar/normativa](https://www.santafe.gov.ar/normativa/getFile.php?id=1728637&item=369305&cod=ba577d6f18f7b2ac127bd833f4dc7e96) (mismo archivo, comparado byte a byte) | Completa (9 págs.) | Búsqueda previa, formulario CAByS, firma, aprobación por la URC |
| F2 | Infografía «¿No encontrás un artículo en TIMBÓ? Resolvelo en 4 pasos» | Ministerio de Salud, sin fecha | Copia local: `app/static/docs/timbo-compras/como-solicitar-alta-de-articulos.pdf` | Completa | Única fuente que menciona Farmacia, la Dirección Provincial de Farmacia y SUFYD |
| F3 | Circular UG TIMBÓ 7/2026: Términos y condiciones de TIMBÓ COMPRAS | Unidad de Gestión TIMBÓ | [PDF](https://www.santafe.gob.ar/ms/timbo/wp-content/uploads/sites/68/2026/05/CIRCULAR-7-UG-TYC-TIMBO-COMPRAS.pdf) | Completa | Roles de TIMBÓ Compras (pto. 10). No menciona catálogo ni altas |
| F4 | Circular UG TIMBÓ 3/2025: Reglamento General de Gestión Digital Interna (RGGDI) | Secretaría de Gestión Pública, 07/07/2025 | [PDF](https://www.santafe.gob.ar/ms/timbo/wp-content/uploads/sites/68/2025/08/3_2025-Circular-Pautas-Generales-para-la-Gestion-Digital-TIMBO.pdf) | Búsqueda dirigida | Carga de usuarios (art. 3); «Nomenclador de Trámites» (art. 6) |
| F5 | Circulares UG TIMBÓ 1/2026 y 3/2026 (implementación de TIMBÓ COMPRAS) | Unidad de Gestión TIMBÓ | [1/2026](https://www.santafe.gob.ar/ms/timbo/wp-content/uploads/sites/68/2026/01/Circular-01-2026-Implementacion-TIMBO-COMPRAS.pdf) · [3/2026](https://www.santafe.gob.ar/ms/timbo/wp-content/uploads/sites/68/2026/03/Circular-03-26.pdf) | Búsqueda dirigida | «Tramitar el alta de perfiles y roles ante el administrador local» |
| F6 | Catálogo WEB del Portal de Compras: descarga completa («Descargar Excel», sin filtros) | Provincia de Santa Fe | [Catálogo WEB](https://www.santafe.gob.ar/gestionesdecompras/site/index.php?a=catalogo.index) · [descarga](https://www.santafe.gob.ar/gestionesdecompras/site/output.php?a=catalogo.get_csv) | Bajado el 19/11/2026: 17.825 filas, 17.793 códigos de ítem | Verificación de códigos |
| F7 | «Consultas y respuestas sobre TIMBÓ» (docx interno) | Hospital (autor no indicado) | `timboDocumentacion/dudasPlanteada/Nomenclador-Publicidad-CronogramaEntregaProveedores.docx` | Completa | Respuesta interna sobre el nomenclador |

**Revisadas sin resultados sobre el tema** (búsqueda de «autoregistro», «catálogo»,
«nomenclador», «alta de bienes», «farmacia», «SUFYD», «perfil» y «administrador local»
en las 22 circulares de la UG TIMBÓ enlazadas en `app/recursos/biblioteca.json`):

- Ninguna menciona **Autoregistro**, **SUFYD** ni **Farmacia**.
- Ninguna menciona el catálogo de artículos. Solo aparecen el «Nomenclador de Trámites» y el nomenclador de actos administrativos.

**Fuentes no oficiales consultadas, solo como pista:**

- Notas de prensa sobre SUFYD (p. ej. [Cadena 3](https://www.cadena3.com/noticia/sociedad/como-funciona-el-sistema-que-distribuye-medicamentos-en-santa-fe_557242)).
- Lo que dicen: SUFYD sería el «Sistema Único de Farmacia y Droguería», por el que hospitales y centros de salud piden medicamentos, integrado con el operador logístico de Funes.
- **No es fuente oficial.** Tampoco dicen nada sobre el catálogo de TIMBÓ.

**No encontrado:**

- Ningún instructivo oficial de SUFYD.
- Ningún documento de la Dirección Provincial de Farmacia sobre altas de artículos.
- Ningún manual de roles y permisos de TIMBÓ que hable del catálogo o de Autoregistro.

## 2. Qué es el «nomenclador» (cuidado con el término)

| Afirmación | Fuente | Estado |
|---|---|---|
| El catálogo oficial de bienes y servicios es el **Catálogo WEB del Portal de Compras**. La resolución habla de bienes «catalogados o nomenclados» | F1, Anexo I pto. 1-2 | ✅ |
| La catalogación se hace «en el ecosistema TIMBO COMPRAS y el módulo de Contrataciones y Gestión de Bienes del SIPAF» | F1, art. 1 | ✅ |
| En la normativa TIMBÓ, «Nomenclador» a secas es el **Nomenclador de Trámites** del Expediente Electrónico, que es otra cosa | F4, art. 6 y Anexo | ✅ |
| En miHospital existe además el «Nomenclador Nacional de Cirugías» (Quirófano) | `content_mihospital.json:1284` | (otro sistema) |
| Lo que el Centro llama «Nomenclador de artículos» es la **lista interna del hospital** (código interno y bodega) emparejada con el Catálogo WEB. No es un sistema oficial | `scripts/equivalencias_articulos.csv` | Interno |
| El Catálogo WEB se consulta y se descarga sin usuario ni contraseña | F6 | 👁️ 19/11/2026 |
| Columnas del Catálogo WEB: Rubro/Especie, Sub-Rubro/Familia, Código y nombre del Elemento, Objeto del Gasto, Código Ítem, Ítem Específico y **Cód. Sistema Externo**. **No hay columna de unidad de medida ni de presentación** | F6 | 👁️ |
| 5.117 ítems tienen «Cód. Sistema Externo»: 2.588 del rubro 37 (productos medicinales y químicos) y 2.477 del 38 (equipamiento médico). **El catálogo no dice de qué sistema es ese código** | F6 | 👁️ / ⏳ qué sistema |
| La solicitud de compra de TIMBÓ Compras **no** es el lugar para pedir artículos nuevos: «Este trámite no se realiza desde TIMBÓ Compras», se hace con un Documento Oficial | F7 (y F1, que lo ubica en Documentos Oficiales) | ✅ por F1 / 🏥 |

**Propuesta para la capacitación:** seguir diciendo «nomenclador», porque así lo
llama la gente, y aclarar siempre que el oficial es el **Catálogo WEB** y que la
lista del hospital es una ayuda para encontrar el código.

## 3. Circuito de alta documentado (bienes y servicios generales)

Todo este circuito sale de F1. Es el único completamente documentado.

1. **Búsqueda previa obligatoria.** El organismo busca en el Catálogo WEB con palabras clave o sinónimos (Anexo I, pto. 1). ✅
2. Si no está catalogado, se completa el **Documento Oficial «Timbó Compras: Alta de bienes y servicios CAByS»**: TIMBÓ → Documentos oficiales → Gestión → Nuevo Documento Oficial (Paso 1). ✅
3. **Encabezado:** fecha, jurisdicción, solicitante (el agente que la confecciona), mail institucional y teléfono (Paso 2). ✅
4. **Cada bien:** rubro, subrubro, elemento, nombre o descripción, objeto del gasto, unidad de medida, marca y documentación adicional (Paso 3). **Hospitales: el código externo es obligatorio en «Nombre o descripción».** ✅
5. **Destinatario:** Carolina Retamar y/o Maximiliano Sodero. **Firma conjunta:** «deberá estar firmado por el responsable del área». ✅
6. **Envío y firma:** Acciones → Enviar a Firmar. El responsable lo firma desde su bandeja con EVALUAR (Pasos 5 y 6). ✅
7. **La Unidad Rectora Central** recibe el formulario, revisa, controla y aprueba o rechaza. Si lo aprueba, asigna el código en el catálogo y avisa al mail del formulario (Finalización). ✅

**Prevención de duplicados:** la norma prevé la búsqueda previa obligatoria (pto. 1) y
el control de la URC (Finalización). No hay otro mecanismo documentado. ✅

Nota sobre la URC:

- F1 dice que, según el art. 106 de la Ley 12.510, la URC es la **Dirección General** de Contrataciones y Gestión de Bienes.
- El glosario y la ficha de roles del Centro dicen que la URC es «la Subsecretaría de Contrataciones y Gestión de Bienes», con fuentes en otras circulares.
- No se corrige nada todavía: se registra como posible discrepancia entre fuentes, para revisar.

## 4. Matriz de roles, permisos y responsabilidades

| Acción | Quién | Fuente | Estado |
|---|---|---|---|
| **Consultar** el Catálogo WEB | Cualquier persona (no pide usuario) | F6 | 👁️ |
| **Buscar antes de pedir** (obligatorio) | «El Organismo, Jurisdicción o Entidad» | F1 pto. 1 | ✅ |
| **Solicitar** el alta de un bien o servicio general (CAByS) | El «agente que confecciona la solicitud» | F1 Paso 2 | ✅ |
| Quién del hospital está designado para solicitar altas | No definido | F7: «Pendiente: definir quién será el responsable de designar y gestionar estas solicitudes (SUFyD a definir)» | ⏳ |
| **Firmar** el CAByS | El «responsable del área» | F1 | ✅ (⏳ qué cargo es en el hospital) |
| **Aprobar o rechazar** y **asignar el código** | Unidad Rectora Central | F1 Finalización | ✅ |
| **Cargar** artículos directamente en el catálogo | Ningún rol del hospital. Solo consta que la URC asigna el código | F1; F3 no prevé ningún rol de catálogo | ✅ no hay rol documentado |
| **Modificar** un artículo ya catalogado | No documentado | — | ⏳ |
| Solicitar un **medicamento o descartable del área Farmacia** | «A través del Servicio de Farmacia de tu efector» | F2 | ✅ (solo esta frase) |
| Qué hacen la Dirección Provincial de Farmacia y SUFYD | F2 solo muestra flechas: Servicio de Farmacia del efector → Dirección Provincial de Farmacia → SUFYD → TIMBÓ. No dice quién crea, valida ni carga | F2 | ⏳ |
| Roles de TIMBÓ Compras | Gestor, Supervisor, Evaluador, Jurisdicción comitente, Oferente/Proveedor. **Ninguno tiene funciones de catálogo** | F3 pto. 10 | ✅ |
| Usar Expediente y Documentos Oficiales | «Cualquier persona que tenga acceso a TIMBÓ» | F7 | 🏥 |
| Acceder a TIMBÓ Compras | Hay que tener asignado ese módulo; el hospital define usuarios y permisos internamente | F7 | 🏥 |
| **Cargar usuarios** en TIMBÓ | Sectoriales de Informática y/o administradores locales, después de la validación institucional | F4 art. 3 | ✅ |
| **Tramitar perfiles y roles** de TIMBÓ Compras | Ante el administrador local de la jurisdicción | F5 | ✅ (⏳ quién autoriza el pedido) |
| Qué permite el rol **«Autoregistro»** | Sin documento | — | ⏳ |
| Si los permisos dependen del servicio o del establecimiento | F4 habla de «oficinas y usuarios» por jurisdicción; nada sobre catálogo | F4 | ⏳ |

**Consultar, solicitar, cargar, modificar y aprobar** (lo que se puede afirmar hoy):

- **Consultar** es público.
- **Solicitar** se hace con un Documento Oficial. Para bienes generales, el CAByS; para el área Farmacia, a través del Servicio de Farmacia.
- **Cargar** y **aprobar** le corresponden a la URC, al menos para el CAByS.
- **Modificar** no está documentado.

## 5. Circuito de Farmacia y SUFYD

**Lo único confirmado (F2):**

- Para medicamentos y productos descartables del área Farmacia («insumos de uso farmacéutico»), «solicitá la incorporación del artículo a través del Servicio de Farmacia de tu efector».
- La infografía dibuja el esquema Servicio de Farmacia del efector → Dirección Provincial de Farmacia → SUFYD → TIMBÓ.
- Dice además «El alta de medicamentos y descartables se gestiona a través del Servicio de Farmacia de tu efector», y para estos casos el recorrido «finaliza aquí» sin pasar por el CAByS.

**F1 no menciona ni a Farmacia ni a SUFYD.**

| Pregunta | Respuesta |
|---|---|
| ¿Los artículos se cargan primero en SUFYD? | ⏳ F2 muestra SUFYD antes de TIMBÓ, pero no dice que se «carguen» ahí ni quién lo hace |
| ¿Farmacia debe hacer alguna gestión adicional en TIMBÓ? | ⏳ |
| ¿Hay integración entre SUFYD y TIMBÓ? | ⏳ Sin documento. El «Cód. Sistema Externo» del catálogo es un indicio sin confirmar |
| ¿Se sincroniza automáticamente? | ⏳ **Ninguna fuente lo dice** |
| ¿Interviene la Dirección Provincial de Farmacia? | ✅ Figura en el esquema de F2 (⏳ qué hace exactamente) |
| ¿Quién valida? | ⏳ |
| ¿Qué datos o documentación presenta Farmacia? | ⏳ |
| ¿Cómo se sabe que ya está disponible para comprar? | ⏳ Para el CAByS, la URC avisa por mail (F1). Para Farmacia no hay nada documentado |
| ¿Qué entra en «área Farmacia» (por ejemplo, reactivos de laboratorio)? | ⏳ |

**Conclusión:** el circuito Farmacia–SUFYD **no se puede enseñar todavía como
procedimiento**. El módulo 5 queda como borrador interno en `/admin`.

## 6. Caso práctico: reactivo HAI para Chagas

Verificado contra F6 (Catálogo WEB bajado el 19/11/2026):

| Código | Ítem específico (texto oficial) | Objeto del gasto | Cód. Sist. Externo |
|---|---|---|---|
| 37.2.289.7 | ANTICUERPOS ANTI-TRIPANOSONA CRUZI por Hemaglutinación indirecta | 2.5.2.0 Prod. farmac. medic. | (vacío) |
| 37.2.289.6 | ANTICUERPOS ANTI-TRIPANOSONA CRUZI por Enzimoinmunoensayo | 2.5.2.0 | (vacío) |
| 37.2.289.2 | ANTICUERPO ANTI-TRIPANOSOMA CRUZZI (CHAGAS) | 2.5.2.0 | (vacío) |
| 37.2.1.10 | REACTIVO PARA DETERMINACION DE CHAGAS | 2.5.1.0 Compuestos químicos | (vacío) |

Respuesta a las 6 preguntas del caso:

1. **¿Ya existe?** Hay un ítem cuyo texto coincide con el método: **37.2.289.7** («por Hemaglutinación indirecta»). 👁️ Que sea el producto que necesita el Laboratorio lo tiene que confirmar Laboratorio.
2. **Código y presentación.** El código existe. **El Catálogo WEB no informa presentación ni unidad de medida**, así que la presentación no se puede verificar desde el catálogo. ⏳ Cómo se define en la solicitud.
3. **Si no aparece:** buscar con sinónimos (F1). Si no está, pedir el alta. ✅
4. **¿Laboratorio o Farmacia?** ⏳ F2 distingue entre el «área Farmacia (insumos de uso farmacéutico)» y los «otros bienes», pero no clasifica los reactivos de laboratorio. En la lista interna del hospital, el artículo figura en las bodegas FARMACIA **y** LABORATORIO (cod. interno 4836). Que el objeto del gasto sea «Prod. farmac. medic.» no define el canal.
5. **¿Quién autoriza el alta?** Por CAByS, la URC (F1) ✅. Por Farmacia ⏳.
6. **Cómo se sigue hasta la solicitud de compra:** ⏳ No hay documento que describa el paso del código ya asignado a su uso en TIMBÓ Compras.

No se inventan cantidades, códigos ni características técnicas.

### 6.1 Verificación de emparejamientos (19/11/2026)

Se revisaron uno por uno los seis emparejamientos de Chagas marcados como incorrectos. El detalle está en [`NOMENCLADOR_CORRECCIONES_PROPUESTAS.md`, sección B.1](NOMENCLADOR_CORRECCIONES_PROPUESTAS.md).

- Fuente: el Catálogo WEB bajado hoy, idéntico al archivo `Catalogo_WEB_al_19112026.csv` de la usuaria.
- En los seis, el texto oficial del ítem actual muestra que no corresponde: FAX, test de COVID, hepatitis A, VDRL, anticuerpo de Chagas para un ASCA, enzimoinmunoensayo para una PCR.
- En ninguno hay un reemplazo seguro sin Laboratorio. Para dos casos (ASCA y test rápido) el catálogo no tiene ningún ítem equivalente.
- **No se modificó ninguna equivalencia.**

### 6.2 Módulos de roles/Autoregistro y Farmacia/SUFYD

Por decisión de la usuaria (19/11/2026):

- Quedan como **borradores internos en `/admin`** hasta tener confirmación oficial.
- Todavía **no se desarrollaron**: la usuaria pidió revisar esta etapa antes de seguir.
- No hay nada de esos módulos en el sitio público.

## 7. Preguntas para elevar

### Ya respondidas por fuente oficial (total o parcialmente)

| # | Pregunta | Qué está respondido | Qué sigue pendiente |
|---|---|---|---|
| 1 | ¿Quién es responsable de cargar artículos en el nomenclador? | La URC aprueba y asigna el código (F1). En el hospital se **solicita**, no se carga | Quién del hospital está designado para solicitar (F7 lo deja «a definir») |
| 2 | ¿Existe un rol específico para realizar altas? | No figura en los roles de TIMBÓ Compras (F3). El alta se pide con un Documento Oficial (F1) | Si hace falta algún permiso de TIMBÓ para usar el tipo de documento CAByS |
| 5 | ¿Quién valida las altas y evita duplicados? | Búsqueda previa obligatoria y control de la URC (F1) | Si hay una validación interna del hospital antes de mandar el CAByS |
| 9 | ¿Quién gestiona los artículos que no existen? | Generales: la URC por CAByS (F1). Área Farmacia: a través del Servicio de Farmacia (F2) | Qué hacen la Dirección Provincial de Farmacia y SUFYD |
| 11 | ¿Cómo se informa que el artículo ya está habilitado? | CAByS: mail al correo informado en el formulario (F1) | Circuito de Farmacia |
| 12 | ¿Existe un manual oficial actualizado? | Res. SCyGB 292/2026 (06/10/2026) para el CAByS, y la infografía del Ministerio de Salud | No hay manual sobre Farmacia/SUFYD, roles del catálogo ni Autoregistro |

### Necesitan confirmación institucional

| # | Pregunta | A quién |
|---|---|---|
| 3 | ¿Cualquier usuario puede iniciar el CAByS o necesita autorización? (F7 dice que Documentos Oficiales lo usa cualquiera con acceso a TIMBÓ, y F1 exige la firma del responsable del área) | Administrador local de TIMBÓ del hospital / Unidad de Gestión TIMBÓ |
| 4 | ¿Cada servicio pide sus propios artículos o lo centraliza un área (Compras, Farmacia)? | Dirección del hospital / Compras |
| 6 | ¿Qué permite exactamente el rol «Autoregistro»? ¿Alcanza para crear Documentos Oficiales? ¿Y para TIMBÓ Compras? | Administrador local / Unidad de Gestión TIMBÓ |
| 7 | ¿Cómo procede Farmacia si trabaja con SUFYD? ¿Qué pide, a quién, por qué medio y con qué datos? | Dirección Provincial de Farmacia |
| 8 | ¿Los artículos dados de alta en SUFYD aparecen solos en el Catálogo WEB y en TIMBÓ? ¿El «Cód. Sistema Externo» del catálogo es el código de SUFYD? | Dirección Provincial de Farmacia / Subsecretaría de Contrataciones y Gestión de Bienes |
| 10 | ¿Por dónde pide Laboratorio un reactivo (p. ej. HAI Chagas): por Farmacia o por CAByS? ¿Los reactivos son «área Farmacia»? | Dirección Provincial de Farmacia / Compras |
| — | ¿Quién es el «responsable del área» que firma el CAByS en el hospital? | Dirección del hospital |
| — | ¿Cómo se modifica un artículo ya catalogado (descripción, unidad)? | Subsecretaría de Contrataciones y Gestión de Bienes |
| — | Cuando el catálogo no indica presentación ni unidad, ¿dónde se define en la solicitud de compra? | Compras / capacitación oficial de TIMBÓ Compras |

## 8. Cómo actualizar este informe

1. Cuando llegue una respuesta, anotar quién respondió, la fecha y el medio. Si hay documento, poner el enlace.
2. Una respuesta **sin documento** pasa a 🏥, no a ✅. Solo lo ✅ puede ir al sitio público (regla del 16/11/2026, `ESTADOS_PUBLICOS` en `app/recursos/__init__.py`).
3. Para volver a verificar códigos:
   - Bajar el catálogo de `output.php?a=catalogo.get_csv` (separado por `|`, UTF-8 con BOM).
   - Comparar por «Código Ítem» (columna 6).
   - El 19/11/2026, los 27.626 renglones de `equivalencias_articulos.csv` apuntaban a códigos existentes y con el mismo texto (cero diferencias).
4. Revisar las fuentes F1 a F5 cada vez que la Subsecretaría o la UG TIMBÓ publiquen una circular nueva.
