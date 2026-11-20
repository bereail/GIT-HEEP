# Nomenclador de artículos — Problemas publicados y correcciones propuestas

Fecha: 19/11/2026 · Rama: `nomenclador-capacitacion`. Las fuentes F1 a F7 son las de
[`NOMENCLADOR_INVESTIGACION.md`](NOMENCLADOR_INVESTIGACION.md#1-fuentes-revisadas).

**Estado al 19/11/2026:**

- **A1 a A6:** aplicadas **solo en local**, con autorización de la usuaria. Sin commit, sin push, sin deploy. Detalle en la sección C.
- **Ajuste de `:2517`:** propuesto, **no aplicado** (no estaba en la autorización).
- **Equivalencias (sección B):** verificadas una por una, **sin modificar**. Están a la espera de la decisión de la usuaria y de Laboratorio.

## A. Afirmaciones sin respaldo sobre Farmacia y SUFYD

Única fuente oficial sobre el tema: la infografía del Ministerio de Salud (F2). Dice:

- «Solicitá la incorporación del artículo a través del **Servicio de Farmacia de tu efector**».
- Dibuja el esquema Servicio de Farmacia → Dirección Provincial de Farmacia → SUFYD → TIMBÓ, sin texto que lo explique.
- «El alta de medicamentos y descartables se gestiona a través del Servicio de Farmacia de tu efector».

**F2 no dice:**

- que la Dirección Provincial de Farmacia **cree** el artículo;
- que se cree **en SUFYD**;
- que después **pase solo** (automáticamente) a TIMBÓ;
- que el pedido se haga **a** la Dirección Provincial de Farmacia.

Además, la respuesta interna del hospital (F7) deja ese circuito «a definir».

| # | Archivo y línea | ¿Público? | Texto actual | Problema |
|---|---|---|---|---|
| A1 | `scripts/content_timbo_compras.json:2530` (lección `pedir-alta-articulo`, tabla «¿Por dónde lo pido?») | Sí | «Pedido formal a la Dirección Provincial de Farmacia, que crea el artículo en el sistema SUFYD. De ahí pasa solo a TIMBÓ.» | Afirma la **creación por la Dirección Provincial de Farmacia en SUFYD** y la **sincronización automática**. F2 dice «a través del Servicio de Farmacia de tu efector», no «pedido a la Dirección Provincial» |
| A2 | `scripts/content_timbo_compras.json:2606-2613` (quiz de la misma lección) | Sí | Pregunta: «Falta un medicamento en el catálogo. ¿Cómo se pide?». Correcta: «A la Dirección Provincial de Farmacia». Explicación: «Medicamentos y descartables los da de alta Farmacia (en SUFYD).» | Da por buena una vía que F2 no indica (el pedido va **a través del Servicio de Farmacia del efector**) y afirma que el alta se hace en SUFYD |
| A3 | `scripts/importar_faq_chats.py:252-256` (FAQ `articulo-no-esta-en-nomenclador`, `verificado: True`) | Sí | «…los medicamentos y descartables se le piden a la Dirección Provincial de Farmacia (los crea en SUFYD)…» | Igual que A1 y A2, y además figura como **verificada** |
| A4 | `app/recursos/simulador.json:283` y `:285` | No (el simulador está oculto en el público: `OCULTOS_PUBLICO`) | «Por el Servicio de Farmacia del efector, que lo eleva a la Dirección Provincial de Farmacia (SUFYD)». Explicación: «…se piden por el Servicio de Farmacia → Dirección Provincial de Farmacia → SUFYD → TIMBÓ» | «Que lo eleva» y «(SUFYD)» como sigla de la Dirección son interpretaciones. SUFYD es un sistema, no la Dirección |
| A5 | `app/templates/equivalencias.html:76` (paso 3 de la página del nomenclador) | Sí | «**Farmacia:** Servicio de Farmacia → Dirección Provincial de Farmacia → SUFYD → TIMBÓ.» | Copia fiel del esquema de F2, pero escrito como paso a seguir parece un procedimiento confirmado. Riesgo bajo |
| A6 | `scripts/content_timbo_compras.json:2875` (glosario, término SIPAF) | Sí | «De él depende el catálogo (nomenclador) de artículos: si se cae, TIMBÓ Compras no deja cargar artículos.» | Lo de «si se cae, no deja cargar» viene de un chat. La FAQ equivalente (`timbo-compras-caido-por-sipaf`) ya está como `verificado: False`. F1 solo dice que la catalogación se hace en TIMBÓ COMPRAS y en el módulo de Contrataciones y Gestión de Bienes del SIPAF |

**Revisadas y sin problema:**

- `app/recursos/biblioteca.json:366` y `app/recursos/herramientas.json:167`: describen la infografía sin agregar nada.
- `app/recursos/capacitacion.json:232` y `:952` (`/admin`): dicen «por el Servicio de Farmacia».
- `scripts/content_timbo_compras.json:2517`: dice «van por Farmacia», que es impreciso pero no falso. Igual se propone ajustarlo.
- Los pasos 1 a 6 del CAByS ya se habían cotejado contra F1. Los volví a leer y siguen coincidiendo.

### Textos propuestos (solo lo que dice F2)

- **A1:** «A través del Servicio de Farmacia de tu hospital (guía oficial del Ministerio de Salud).»
  - Sin mencionar creación, SUFYD ni pase automático.
  - El esquema de la infografía se ve en el PDF que ya está enlazado en la lección.
- **A2:**
  - Opciones: «A través del Servicio de Farmacia del hospital» (correcta) / «Con el formulario CAByS» / «Por mail a la mesa de ayuda».
  - Explicación: «La guía del Ministerio de Salud indica que los medicamentos y descartables del área Farmacia se piden a través del Servicio de Farmacia del efector. El CAByS es para los demás bienes y servicios.»
- **A3:** «…los medicamentos y descartables del área Farmacia, a través del Servicio de Farmacia del hospital; el resto, con el Documento Oficial "Timbó Compras: Alta de bienes y servicios CAByS" (Res. SCyGB 292/2026).»
- **A4:**
  - Opción: «Por el Servicio de Farmacia del efector».
  - Explicación: «Así lo indica la guía del Ministerio de Salud. Lo que pasa después (Dirección Provincial de Farmacia, SUFYD) está pendiente de confirmar.» Puede decir «pendiente» porque es `/admin`.
- **A5:** «**Farmacia:** pedilo a través del Servicio de Farmacia del hospital (ver la guía oficial).» Sacar el esquema escrito o mostrarlo como «Esquema de la guía del Ministerio de Salud».
- **A6:** «Sistema provincial de administración financiera. La Res. SCyGB 292/2026 ubica la catalogación de bienes y servicios en TIMBÓ COMPRAS y en el módulo de Contrataciones y Gestión de Bienes del SIPAF.» El desarrollo exacto de la sigla está **PENDIENTE DE CONFIRMACIÓN** contra un documento oficial.
- **`:2517`:** «…los medicamentos y descartables del área Farmacia se piden a través del Servicio de Farmacia del hospital; todo lo demás, con el formulario CAByS.»

**Cómo se aplicaría (cuando se autorice):**

1. Editar los JSON y el `.py`.
2. Reimportar los contenidos y las FAQ.
3. Correr `pytest` y `scripts/bateria_chatbot.py`. Puede haber preguntas de la batería que esperen el texto viejo.
4. Mostrar el resultado en local antes de commitear.

## B. Emparejamientos del nomenclador relacionados con Chagas

Verificados contra el Catálogo WEB oficial bajado el 19/11/2026 (F6):

- **Los 27.626 renglones** de `scripts/equivalencias_articulos.csv` apuntan a códigos que **existen** en el catálogo, y el texto del ítem coincide con el oficial en todos. No hay códigos inventados ni dados de baja.
- El problema **no** está en los códigos: está en **la elección del ítem**. El emparejamiento automático del 17/11 (`84ea95a`, `matching_nomenclador_heep.py`) no se revisó a mano. Hoy son públicos 25.039 renglones «dudosa» (amarillos) y 1.600 «sin_match».

Muestra revisada: todos los artículos internos con «chagas», «cruzi» o «hemaglut». Es una muestra chica y no aleatoria, así que no permite extrapolar un porcentaje.

| Cod. interno | Nombre interno | Código actual → ítem oficial | Evaluación | Evidencia | Propuesta |
|---|---|---|---|---|---|
| 4836 | Acs anti Trip. cruzi - HAI(det) | 37.2.289.7 → «…por Hemaglutinación indirecta» | **Coincide en el método** | HAI = hemaglutinación indirecta, como en el nombre del ítem oficial | Sin cambio. Sigue en amarillo hasta que Laboratorio confirme |
| 4834 | Acs anti Trip. cruzi - EIA(det) | 37.2.289.7 → «…por Hemaglutinación indirecta» | **No coincide el método** | EIA es enzimoinmunoensayo. El catálogo tiene 37.2.289.6 «…por Enzimoinmunoensayo» | Proponer a Laboratorio el 37.2.289.6. No cambiar sin su OK |
| 4854 | Acs anti Trip. cruzi - test rapido(det) | 37.2.490.1 → «TEST RAPIDO DE AG COVID» | **Incorrecto** | Otra enfermedad | Sacar el código actual. No hay test rápido de Chagas en el catálogo: candidato a rojo («hay que pedir que se agregue») o a 37.2.289.2 si Laboratorio lo acepta |
| 12622 | Acs anti Trypanosoma cruzi - ECLIA(det) | 37.2.289.6 → «…por Enzimoinmunoensayo» | **Dudoso** | ECLIA es electroquimioluminiscencia, otro método | Consultar a Laboratorio |
| 14728 | chagas hai equipo(equipo) | 12.2.8.1 → «EQUIPO FAX» (rubro Comunicaciones) | **Incorrecto** | Rubro sin relación | Sacar el código actual. Candidato 37.2.289.7, a confirmar por Laboratorio |
| 14729 | chagas elisa equipo(equipo) | 37.2.322.2 → «EQUIPO DE HAV IG M POR ELISA» | **Incorrecto** | HAV es hepatitis A | Sacar el código actual. Candidato 37.2.289.6, a confirmar |
| 17369 | Reacciones PCR-RT Chagas(det) | 37.2.442.1 → «VDRL» | **Incorrecto** | VDRL es una prueba de sífilis | Sacar el código actual. Ver la fila siguiente |
| 18348 | Reacciones PCR-RT Chagas | 37.2.1.10 → «REACTIVO PARA DETERMINACION DE CHAGAS» | Genérico | Mismo nombre que 17369 con otro código: hay inconsistencia interna | Laboratorio decide si 37.2.1.10 sirve para ambos |
| 18926 | Acs. anti-Saccharomyces (ASCA) (det) | 37.2.289.2 → «ANTICUERPO ANTI-TRIPANOSOMA CRUZZI (CHAGAS)» | **Incorrecto** | ASCA no tiene relación con Chagas | Sacar el código actual |
| 19872 · 21114 | PCR-TRIPANOSOMA CRUZI · qPCR-Tripanosoma cruzi | 37.2.289.6 → «ANTICUERPOS… por Enzimoinmunoensayo» | **No coincide el método** | La PCR detecta ADN, no anticuerpos | Sacar el código actual. Candidato 37.2.1.10, a confirmar |

### B.1 Verificación individual de los seis emparejamientos incorrectos (19/11/2026)

**Fuentes y método:**

- Catálogo WEB bajado el 19/11/2026. Coincide fila por fila con el archivo que pasó la usuaria (`Catalogo_WEB_al_19112026.csv`): 17.793 códigos en ambos, misma cabecera, cero diferencias.
- Para cada artículo se buscó en **todo** el catálogo, sin tildes, por los términos del nombre interno y del método.
- Términos buscados: CHAGAS, CRUZ, TRIPANO/TRYPANO; TEST RÁPIDO, PRUEBA RÁPIDA, INMUNOCROMAT; HEMAGLUT, HAI; ELISA, ENZIMOINMUNO, EIA; PCR, AMPLIFICACIÓN, BIOLOGÍA MOLECULAR, TIEMPO REAL; SACCHAROM, ASCA; QUIMIOLUMIN, ECLIA; equipos y kits reactivos del rubro 37.

**Ítems de Chagas en todo el catálogo (son 4):**

- 37.2.1.10 REACTIVO PARA DETERMINACION DE CHAGAS
- 37.2.289.2 ANTICUERPO ANTI-TRIPANOSOMA CRUZZI (CHAGAS)
- 37.2.289.6 ANTICUERPOS ANTI-TRIPANOSONA CRUZI por Enzimoinmunoensayo
- 37.2.289.7 ANTICUERPOS ANTI-TRIPANOSONA CRUZI por Hemaglutinación indirecta

Ninguno de los cuatro informa presentación, unidad ni código de sistema externo.

| # | Cod. interno · nombre | Código actual (texto oficial) | ¿El actual es incorrecto? | ¿Hay ítem correcto en el catálogo? | Resultado |
|---|---|---|---|---|---|
| 1 | 4854 · Acs anti Trip. cruzi - test rapido | 37.2.490.1 TEST RAPIDO DE AG COVID | **Sí**: es un test de COVID | **No.** Los únicos tests rápidos del catálogo son de COVID (37.2.490.1), hidatidosis (37.2.606.1) y toxina Shiga (37.2.609.1) | Sin candidato específico. Si Laboratorio no acepta un ítem genérico (37.2.289.2 o 37.2.1.10), corresponde rojo: pedir el alta |
| 2 | 14728 · chagas hai equipo | 12.2.8.1 EQUIPO FAX (rubro 12, Comunicaciones) | **Sí**: rubro sin relación | **Parcial.** El único ítem por hemaglutinación de Chagas es 37.2.289.7 («Anticuerpos… por Hemaglutinación indirecta»). El 37.2.322.1 es un «Equipo de hemoaglutinación indirecta» pero **para Echinococcus**, no sirve | Candidato 37.2.289.7. Falta que Laboratorio confirme que el ítem «anticuerpos» cubre el «equipo» |
| 3 | 14729 · chagas elisa equipo | 37.2.322.2 EQUIPO DE HAV IG M POR ELISA | **Sí**: HAV es hepatitis A | **Parcial.** Hay equipos por ELISA para otras enfermedades (37.2.322.x), ninguno de Chagas. El único de Chagas por enzimoinmunoensayo es 37.2.289.6 | Candidato 37.2.289.6, a confirmar por Laboratorio |
| 4 | 17369 · Reacciones PCR-RT Chagas | 37.2.442.1 VDRL | **Sí**: VDRL es una prueba de sífilis | **No específico.** No hay PCR de Chagas. Los ítems de PCR son insumos genéricos (master mix, tubos, extracción) o de otras enfermedades (37.2.524.1, varicela) | Candidato genérico 37.2.1.10, que es el que ya tiene el mismo nombre con cod. 18348. Laboratorio decide; si no lo acepta, rojo |
| 5 | 18926 · Acs. anti-Saccharomyces (ASCA) | 37.2.289.2 ANTICUERPO ANTI-TRIPANOSOMA CRUZZI (CHAGAS) | **Sí**: ASCA no tiene relación con Chagas | **No.** El único «Saccharomyces» del catálogo es un medicamento (37.16.770.1, S. boulardii 250 mg sobres) | Sin candidato: corresponde rojo, pedir el alta |
| 6 | 19872 · PCR-TRIPANOSOMA CRUZI y 21114 · qPCR-Tripanosoma cruzi | 37.2.289.6 ANTICUERPOS… por Enzimoinmunoensayo | **Sí**: la PCR no es un ensayo de anticuerpos | **No específico.** Igual que el n.º 4 | Candidato genérico 37.2.1.10, a confirmar por Laboratorio; si no, rojo |

**Conclusión de la verificación:**

- En los seis casos, **el texto oficial del ítem actual prueba que no corresponde**. Esa es la evidencia para sacar el código.
- En **ninguno** hay evidencia suficiente para poner otro código sin que Laboratorio lo confirme: los candidatos son genéricos o no coinciden en el tipo de producto.
- **No se modificó ninguna equivalencia.**

**Acción propuesta (para decidir):**

- **Opción 1 (mínima):** dejar el código, pero cambiar la nota a «El código actual no corresponde a este artículo (verificado contra el Catálogo WEB el 19/11/2026). Consultar a Laboratorio».
- **Opción 2:** pasar los seis a «sin_match» (rojo) con el candidato en la nota, hasta que Laboratorio confirme.

Cualquiera de las dos se hace en `scripts/equivalencias_articulos.csv`, en las dos filas por bodega cuando corresponda, y después hay que correr `importar_equivalencias.py`.

**Recomendación:**

- No cambiar ninguna equivalencia todavía.
- Una vez autorizado, la propuesta mínima es sacar el código en los 6 casos marcados «Incorrecto». En esos casos el error se ve en el propio texto oficial.
- En el resto, mandar los candidatos a Laboratorio por la pantalla de revisión (`/revision/`) o en un Excel.
- Antes de usar el nomenclador en la capacitación, decidir si los amarillos siguen públicos tal como están, o si se avisa con más fuerza que **no se usen sin confirmar**.

## C. Correcciones aplicadas en local (19/11/2026)

Solo en la copia de trabajo de la rama `nomenclador-capacitacion`. Sin commit, sin push, sin deploy.

| # | Archivo | Antes | Después |
|---|---|---|---|
| A1 | `scripts/content_timbo_compras.json` (tabla de la lección `pedir-alta-articulo`) | «Pedido formal a la Dirección Provincial de Farmacia, que crea el artículo en el sistema SUFYD. De ahí pasa solo a TIMBÓ.» | «A través del Servicio de Farmacia de tu hospital (guía oficial del Ministerio de Salud, al final de esta lección).» |
| A2 | `scripts/content_timbo_compras.json` (quiz de la misma lección) | Opción correcta: «A la Dirección Provincial de Farmacia». Explicación: «Medicamentos y descartables los da de alta Farmacia (en SUFYD). El CAByS es para artículos generales.» | Opción correcta: «A través del Servicio de Farmacia del hospital». Explicación: «La guía del Ministerio de Salud indica que los medicamentos y descartables del área Farmacia se piden a través del Servicio de Farmacia del efector. El CAByS es para los demás bienes y servicios.» |
| A3 | `scripts/importar_faq_chats.py` (FAQ `articulo-no-esta-en-nomenclador`) | «…los medicamentos y descartables se le piden a la Dirección Provincial de Farmacia (los crea en SUFYD); el resto…» | «…los medicamentos y descartables del área Farmacia, a través del Servicio de Farmacia del hospital; el resto…» |
| A4 | `app/recursos/simulador.json` (solo `/admin`) | «Por el Servicio de Farmacia del efector, que lo eleva a la Dirección Provincial de Farmacia (SUFYD)». Explicación: «Medicamentos y descartables se piden por el Servicio de Farmacia → Dirección Provincial de Farmacia → SUFYD → TIMBÓ.» | «Por el Servicio de Farmacia del efector». Explicación: «Así lo indica la guía del Ministerio de Salud. Lo que pasa después (Dirección Provincial de Farmacia, SUFYD) está pendiente de confirmar.» |
| A5 | `app/templates/equivalencias.html` (paso 3) | «**Farmacia:** Servicio de Farmacia → Dirección Provincial de Farmacia → SUFYD → TIMBÓ.» | «**Farmacia:** pedilo a través del Servicio de Farmacia del hospital (ver la guía oficial, abajo).» |
| A6 | `scripts/content_timbo_compras.json` (glosario del tema, SIPAF) | «Sistema Informático Provincial de Administración Financiera. De él depende el catálogo (nomenclador) de artículos: si se cae, TIMBÓ Compras no deja cargar artículos.» | «El sistema financiero de la Provincia. Según la Res. SCyGB 292/2026, la catalogación de bienes y servicios se hace en TIMBÓ Compras y en el módulo de Contrataciones y Gestión de Bienes del SIPAF.» |

Sobre A6:

- El desarrollo de la sigla («Sistema Informático Provincial…») no aparece en la Res. 292 ni en la Circ. SCyGB 006/2026, así que se sacó.
- «El sistema financiero de la Provincia» es la misma frase que ya usa el glosario general (`app/recursos/glosario.json`, término SIPAF, confirmado con la Circ. SCyGB 006/2026 y la Res. 292).

### Pruebas (19/11/2026)

- **`pytest`, suite completa:** 132 pasaron, 0 fallaron.
  - Se corrió con el entorno de `GIT-HEEP-integracion`, porque el `.venv` de este repo no tiene pytest instalado.
  - Ese entorno tiene Flask 3.1.3 y pytest 8.3.4, las versiones de `requirements-dev.txt`.
- **Batería del chatbot** (`scripts/bateria_chatbot.py`): **117/117** antes y después de los cambios.
  - Se corrió sobre dos bases nuevas en copias temporales (`create_all` + `db stamp head` + los 5 importadores), sin tocar ninguna base del repo.
- **Páginas, con el cliente de pruebas de Flask, en la copia con los cambios:**

  | Página | Respuesta | Texto nuevo | Texto viejo |
  |---|---|---|---|
  | Lección `pedir-alta-articulo` | 200 | Sí | No |
  | Problemas frecuentes de TIMBÓ Compras | 200 | Sí | No |
  | Nomenclador (`/temas/timbo-compras/equivalencias`) | 200 | Sí | No |
  | Simulador público | 404 (sigue oculto al público, como corresponde) | — | — |

- **Base importada con los cambios:** cero apariciones de «SUFYD», «si se cae» y el desarrollo viejo de la sigla. En la base de antes había 4: glosario, bloques y quiz de la lección, y FAQ.
- **JSON modificados:** se cargan sin errores.
