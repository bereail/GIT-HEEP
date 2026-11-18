"""Matriz consolidada v5.1 — corrige solo problemas de coherencia de la v5.
Archivo independiente (no importa la v4 ni la v5). Local: no toca el proyecto.

    python fuente/matriz_v5_1.py   →   matriz_v5_1.html
"""
from collections import Counter
from html import escape as h
from pathlib import Path

AQUI = Path(__file__).resolve().parent.parent
FECHA = "18/11/2026"
SCYGB, UG, LEER = "SCyGB (Unidad Rectora Central)", "Unidad de Gestión TIMBÓ", "Lectura pendiente (equipo)"

ESTADOS = [
    ("VERIFICADO", "#1b7a45", "Coincide con el texto vigente de una norma leída completa, con punto y página."),
    ("DOCUMENTADO", "#2456c7", "Lo respalda material operativo oficial (video, instructivo, guía), sin cotejo completo con la norma vigente."),
    ("PENDIENTE", "#b85400", "Falta fuente, o falta confirmar alcance, orden o actor."),
    ("OBSERVADO", "#b42318", "Hay discrepancia entre fuentes oficiales o entre representaciones del proyecto."),
]

REGLA_20 = [
    ("Cálculo del monto (para elegir el procedimiento)",
     "«…se considerará el importe total en que se estimen las adjudicaciones, incluidas las opciones de prórroga previstas.»",
     "Antes de elegir, en la decisión «¿Cuánto es el monto?»", "VERIFICADO"),
    ("Validez del procedimiento (al adjudicar)",
     "«Será válido el procedimiento de selección seguido de acuerdo con la estimación del valor del contrato cuando el importe de la adjudicación supere hasta el veinte por ciento (20%) del importe máximo admitido para cada procedimiento.»",
     "En la adjudicación, como regla; no cambia el camino elegido", "VERIFICADO"),
]

# recorrido, qué cubre, fuentes, estado, observaciones
RECORRIDOS = [
    ("Inicio y etapa preparatoria", "Necesidad, expediente electrónico, número de EE",
     "Circ. UG 7/2026 ptos 6 y 11 (págs. 2-3) · Dec. 2518/25 arts. 1-2", "VERIFICADO", "Quién arma el pedido en el hospital: PENDIENTE (a relevar)"),
    ("Monto a considerar", "Cálculo con prórrogas; validez hasta +20 %", "Dec. 1104/16 art. 116.1 (pág. 17)", "VERIFICADO", "Dos reglas separadas"),
    ("Montos 2026", "Topes por procedimiento", "Circ. SCyGB 01/2026 (pág. 1) · Ley 14.424 art. 36 · Dec. 2233/16 art. 1 (pág. 2)", "VERIFICADO", "—"),
    ("Autoridades por tramo", "Quién aprueba o adjudica según el monto",
     "Circ. SCyGB 01/2026 «Aprobación de actos licitatorios» · Dec. 2233/16 arts. 2 y 3 (pág. 2)",
     "VERIFICADO (textos) · OBSERVADO (D7) · PENDIENTE (2.º tramo y equivalente en el hospital)",
     "La Circ. 01 dice «Por Resolución» sin decir de quién. Que sea de los Ministros (Dec. 2233 art. 3.b) es una interpretación por coincidencia de tramos: no está confirmada"),
    ("◆1 ¿Causal de directa?", "Excepciones al procedimiento licitatorio", "Ley 12.510 art. 116 c ap. 1 a 8 (pág. 40)", "VERIFICADO",
     "Ap. 9 (Ley 13.861 / Dec. 667/19): en la biblioteca, sin leer → PENDIENTE"),
    ("A · Directa por monto — secuencia de formularios", "CD-01 solicitud → CD-02 pedido de presupuesto (según el monto) → CD-03 evaluación y adjudicación → CD-04 orden de provisión · CD-05 notificación de rechazo",
     "Dec. 1247/08 Anexo I (págs. 5 a 8) · vigencia del procedimiento: Dec. 2175/2022 art. 1 · Dec. 2233/16 art. 1 (≤10 % del privado)", "VERIFICADO",
     "Solo la secuencia y los formularios"),
    ("A · Directa por monto — actores, autorizaciones y detalle operativo",
     "Quién informa el presupuesto, quién autoriza, quién adjudica, imputación, modificación presupuestaria, comunicación al TCP, soporte",
     "Dec. 1247/08 Anexo I (2008, antecedente histórico) · Dec. 2233/16 art. 3.a · Circ. SCyGB 01/2026 · Circ. UG 9 y 11/2026 · Circ. UG 2/2025 pto 2 · Dec. 2518/25 · video oficial QH7zvgZ7sbQ",
     "OBSERVADO (D8, D9, D10) · DOCUMENTADO (detalle operativo digital, video)",
     "No se presenta ningún actor como confirmado para la directa digital"),
    ("A2 · Directa por otra causal (ap. 4 a 8)", "Causales, fundamentación y trámite por expediente",
     "Ley 116 c ap. 4 a 8 (pág. 40) · Dec. 1104 art. 116 c ap. 4 y 6 (pág. 18) · Circ. UG 2/2025 pto 2 (pág. 8) · Dec. 652/2020 (ap. 7, si supera el 50 %)",
     "VERIFICADO (causales y trámite digital) · PENDIENTE (intervención de la SCyGB en ap. 4, 5 y 8: D17)",
     "No se muestra la intervención de la SCyGB en ap. 4, 5 y 8 como obligatoria hasta leer la Disp. 282/16"),
    ("B · Urgencia o desierto", "Causal; intervención previa de la SCyGB si supera el 50 % del privado; ≥3 cotizaciones (urgencia); mismas condiciones (desierto); TIMBÓ Compras con flexibilizaciones",
     "Ley 116 c ap. 2 y 3 (pág. 40) · Dec. 1104 art. 116 c ap. 2 y 3 (pág. 18) · Dec. 652/2020 arts. 1 y 3 (págs. 2-3) · Circ. UG 8/2026 arts. 3 y 4 (págs. 1-2)",
     "VERIFICADO (normas citadas) · PENDIENTE (recorrido en TIMBÓ Compras: D1)", "Decisión de la usuaria: dejar pendiente"),
    ("◆2 Modalidades especiales (rama E)", "Locación · etapa múltiple · Convenio Marco · subasta",
     "Circ. SCyGB 01/2026 y Ley art. 140 (locación) · Dec. 1104 art. 123, texto Dec. 287/2026 (pág. 3) · Circ. UG 8/2026 arts. 5 a 8 · Ley y Dec. 1104 art. 116 b (subasta)",
     "VERIFICADO (tope de locación, selección de la etapa múltiple, subasta) · PENDIENTE (Convenio Marco, régimen de locaciones: D18; papel en etapa múltiple vs. Dec. 2518/25)",
     "Ver la aclaración sobre etapa múltiple y gestión digital"),
    ("◆3 ¿Cuánto es el monto?", "Directa / privado / público", "Circ. SCyGB 01/2026 · Dec. 2233/16 art. 1 · Ley 116 a", "VERIFICADO", "—"),
    ("C · Licitación o concurso privado", "≥5 invitaciones fehacientes con 5 días corridos; difusión en Internet",
     "Ley 116 a y 118 · Dec. 1104 art. 116 a.1 (pág. 17) y art. 121.1 (pág. 20) · Circ. UG 3/2026", "VERIFICADO (requisito) · PENDIENTE (si las invitaciones de TIMBÓ cumplen: D6)", "—"),
    ("C · Licitación o concurso público — publicación", "Boletín Oficial 2 días · diarios · 10 días corridos (20 internacional) · portal y aviso",
     "Ley 132 (pág. 43) · Dec. 1104 art. 132.3 y 132.4 (pág. 26) · Circ. SCyGB 04/2026 Anexo II (pág. 4)",
     "VERIFICADO (Boletín Oficial 2 días y plazo de 10/20 días: coinciden decreto y circular) · OBSERVADO (cantidad de diarios: D4) · PENDIENTE (alcance de la Circ. 04/2026 al hospital)", "—"),
    ("Tronco de TIMBÓ Compras", "Pliego, revisión, aprobación, controles, acto, publicación, consultas, ofertas, apertura, vista e impugnación, evaluación, preadjudicación, impugnación",
     "Circ. UG 7/2026 ptos 6 a 22 (págs. 2-5) · Circ. SCyGB 03/2026 (pág. 1) · Pliego Único 4.3, 5.1-5.3, 10.1.3 · Dec. 1104 art. 133.1",
     "VERIFICADO (pasos citados) · OBSERVADO (D7) · PENDIENTE (D5, D12, D13)",
     "Los controles de la URC se muestran «si aplica», nunca como obligatorios para el hospital (D5)"),
    ("Adjudicación y contrato", "Acto, notificación, SIN y TCP, publicación, perfeccionamiento, caducidad",
     "Circ. UG 7/2026 pto 6 · Dec. 2233/16 art. 3 · Pliego Único 5.4 a 5.6 (pág. 38) · Ley 132 · Circ. UG 11/2026 art. 1",
     "VERIFICADO (textos) · PENDIENTE (equivalente en el hospital; publicación del privado: D11)", "—"),
    ("Recepción, factura y pago", "Recepción provisoria y definitiva, certificado, factura, pago",
     "Pliego Único 6.9 a 6.13 (págs. 46-49)", "VERIFICADO (reglas) · PENDIENTE (sistema, oficina y soporte)", "Para la directa, el Dec. 1247/08 es antecedente histórico"),
    ("Excepciones", "Revocación, vicio, empate, oferta única, desierto → B, caducidad",
     "Pliego Único 4.3, 5.2, 5.3, 5.5, 5.6 · Ley 116 c.3 y 133 · Dec. 1104 art. 116 c ap. 3",
     "VERIFICADO (reglas) · PENDIENTE (D19: quién declara desierta · D20: equivalencia revocación / «sin efecto»)", "—"),
]

# id, tema, fuentes, tipo, impacto, estado, consultar a, pregunta, decisión de la usuaria
MATRIZ = [
    ("D1", "Recorrido de la rama B (urgencia o desierto) en TIMBÓ Compras",
     "Algoritmo público (salta a «ofertas») · Circ. UG 8/2026 arts. 3 y 4 (págs. 1-2) · circuito oficial (entra por el pliego) · Dec. 652/2020 arts. 1 y 3 · Dec. 1104 art. 116 c ap. 2 y 3 (pág. 18)",
     "Diferencia entre representaciones + falta documentación", "Dónde se une B al tronco; si urgencia y desierto recorren lo mismo", "PENDIENTE",
     UG, "En las contrataciones directas por urgencia y por desierto en TIMBÓ Compras, ¿se completan los formularios del pliego particular? ¿Qué etapas del módulo se omiten o se acortan, además de lo que dice el art. 4 de la Circ. 8/2026? ¿Es el mismo recorrido para los dos supuestos?",
     "Dejar pendiente hasta verificar"),
    ("D2", "Quién selecciona la etapa múltiple", "Dec. 1104 art. 123, texto del Dec. 287/2026 (pág. 3) · algoritmo público (la elige el organismo)",
     "Texto superado en el proyecto", "Opción de la decisión ◆2", "VERIFICADO", "—", "—", "Representar que la selecciona la Unidad Rectora"),
    ("D3", "Pasos de la directa por monto", "Dec. 1247/08 Anexo I (págs. 5 a 8) · Dec. 2175/2022 art. 1 · video oficial QH7zvgZ7sbQ · Circ. UG 2/2025 pto 2 (pág. 8)",
     "Diferencia entre representaciones", "Rama A",
     "VERIFICADO (solo la secuencia de formularios CD-01 a CD-05) · actores y detalle operativo: ver D8 a D10", "—", "—",
     "Conservar CD-01 a CD-04 como recorrido documentado; verificar contra la normativa antes de validar"),
    ("D4", "Publicación de la licitación pública: diarios",
     "Boletín Oficial 2 días: Dec. 1104 art. 132.3 (pág. 26) y Circ. SCyGB 04/2026 Anexo II (pág. 4) coinciden · Diarios: el decreto dice «un (1) día en dos diarios»; la nota modelo de la circular, «un (1) día en un (1) diario» · Dec. 287/2026 art. 2 solo modifica el 132.1",
     "Contradicción normativa (decreto vs. nota modelo de circular), limitada a la cantidad de diarios", "Publicación del público",
     "OBSERVADO (cantidad de diarios) · el Boletín Oficial 2 días queda VERIFICADO",
     SCYGB, "La nota modelo de la Circular 04/2026 pide la publicación «por un (1) día en un (1) diario»; el art. 132.3 del Dec. 1104/16 dice «un (1) día en dos diarios». ¿Cuál corresponde aplicar?",
     "Dejar pendiente hasta verificar alcance y vigencia de la Circ. 04/2026"),
    ("D5", "Controles de la URC en el hospital", "Res. ME 73/2026 art. 2 (pág. 3) y Circ. SCyGB 03/2026 (pág. 1): obligatorios para la Administración Pública Central",
     "Alcance no confirmado", "Dos controles del tronco: se muestran «si aplica»", "PENDIENTE", SCYGB,
     "Los controles de pliegos y de preadjudicación que la Res. ME 73/2026 declara obligatorios para la Administración Pública Central, ¿alcanzan a los hospitales del Ministerio de Salud?", "—"),
    ("D6", "Las 5 invitaciones del privado", "Dec. 1104 art. 121.1 (pág. 20) · Circ. UG 7/2026 pto 15 (pág. 4)",
     "Alcance no confirmado", "Publicación del privado", "PENDIENTE", f"{UG} / {SCYGB}",
     "¿Las invitaciones que TIMBÓ Compras envía a la nómina cumplen el requisito de «medio fehaciente» del art. 121.1, o hay que acreditarlas aparte en el expediente?", "—"),
    ("D7", "Competencia para aprobar el pliego",
     "Dec. 2233/16 art. 2 (pág. 2): Subsecretario de Coordinación Técnica y Gestión Administrativa o equivalente (o delegado), sin tramos · Circ. SCyGB 01/2026 (pág. 1): «Aprobación de actos licitatorios» por montos · Dec. 2233/16 art. 3: tramos para adjudicación",
     "Contradicción o diferencia de interpretación entre normas", "Actor del acto de la etapa 4", "OBSERVADO", SCYGB,
     "Ver la consulta formal", "Conservar las dos referencias; no trasladar los tramos de adjudicación a la aprobación del pliego"),
    ("D8", "Quién adjudica la directa por monto",
     "Dec. 1247/08 Anexo I (pág. 7, 2008, antecedente histórico): Disposición del Director del SAF · Dec. 2233/16 art. 3.a (2016) y Circ. SCyGB 01/2026: Subsecretario o equivalente (o delegado)",
     "Fuentes de distinta fecha", "Actor de la rama A", "OBSERVADO", SCYGB,
     "En la directa por monto, ¿el acto de adjudicación lo dicta el Subsecretario de Coordinación Técnica o su equivalente (Dec. 2233/16, art. 3.a), o sigue vigente la disposición del Director del Servicio Administrativo-Financiero que describe el Manual del Dec. 1247/08?",
     "Usar las fuentes más recientes como referencia de análisis, sin presentarlas como confirmadas; mantener OBSERVADO"),
    ("D9", "Comunicación al Tribunal de Cuentas en la directa",
     "Dec. 1247/08 Anexo I (pág. 7, 2008): copia a la Delegación Fiscal (Res. TCP 007/06, no leída) · Circ. UG 9/2026 art. 3 y UG 11/2026 arts. 1-2 (pág. 2): todos los actos al SIN y a la visualización",
     "Fuentes de distinta fecha", "Rama A (y alcance de F1 en la directa)", "OBSERVADO", f"{UG} / {SCYGB}",
     "¿La comunicación al TCP de los actos de la directa por monto se hace solo por SIN y «Gestión de Visualización» (Circ. 9 y 11/2026) o se mantiene la copia a la Delegación Fiscal?", "Igual que D8"),
    ("D10", "Soporte de la directa",
     "Dec. 1247/08 Anexo I (pág. 7, 2008): presupuestos por teléfono, fax o correo · Circ. UG 2/2025 pto 2 (pág. 8) y Dec. 2518/25: exclusivamente digital",
     "Fuentes de distinta fecha", "Soporte de la rama A", "OBSERVADO", f"{UG} / {SCYGB}",
     "¿Cómo se incorporan los presupuestos en la gestión directa digital (documento informativo, CD-03, otro)? ¿Sigue el umbral de las habilitaciones para pedir presupuestos sin CD-02?", "Igual que D8"),
    ("D11", "Publicación de la adjudicación en el privado", "Ley 12.510 art. 132 (pág. 43) · Dec. 1104 art. 132.4 (pág. 26): se refieren a licitación y concurso público",
     "Alcance no confirmado", "Etapa de adjudicación: la publicación se muestra solo para el público", "PENDIENTE", SCYGB,
     "¿La adjudicación de una licitación o concurso privado se publica en el sitio web de contrataciones?", "—"),
    ("D12", "Qué sigue después de un rechazo del Supervisor", "Circ. UG 7/2026 pto 10 (pág. 3)", "Falta documentación", "Salida «Rechazado» sin destino",
     "PENDIENTE", UG, "Cuando el Supervisor rechaza un formulario del PBCP, ¿vuelve al Gestor para corregirlo? ¿Queda registro en el expediente?", "—"),
    ("D13", "Orden entre pasos del pliego",
     "Circ. UG 7/2026 pto 10 (pág. 3): define roles, no el orden · Circ. SCyGB 03/2026 (pág. 1): el control de la URC va con el pliego ya aprobado por el Supervisor y antes del acto",
     "Falta documentación", "Revisión de la comitente y cronograma/nómina se muestran sin orden afirmado", "PENDIENTE", UG,
     "¿En qué momento revisa la Jurisdicción comitente respecto de la aprobación del Supervisor? ¿El cronograma y la nómina se cargan antes o después del control de la URC?", "—"),
    ("D14", "El algoritmo público y el circuito oficial no coinciden", "algoritmo.json (público) · circuito oficial en /admin/procesos", "Diferencia entre representaciones",
     "Riesgo de enseñar cosas distintas", "PENDIENTE", "—", "—",
     "No modificar algoritmo.json hasta aprobar el circuito; después sincronizar y probar todos sus consumidores"),
    ("D15", "Representación del 20 %", "Dec. 1104 art. 116.1 (pág. 17)", "Error de representación (corregido)", "Decisión ◆3 y adjudicación",
     "VERIFICADO", "—", "—", "Separar cálculo y validez"),
    ("D16", "Intervención de la SCyGB en urgencia y desierto", "Dec. 652/2020 arts. 1 y 3 (págs. 2-3)", "Diferencia entre representaciones (falta en el circuito oficial)",
     "Rama B", "VERIFICADO (la norma) · el recorrido de B sigue PENDIENTE (D1)", "—", "—", "—"),
    ("D17", "Intervención de la SCyGB en ap. 4, 5 y 8", "Disp. 282/16 (PDF escaneado, en la biblioteca, sin leer)", "Falta lectura",
     "Rama A2: la intervención no se muestra como obligatoria", "PENDIENTE", LEER, "Leer la Disp. 282/16 (requiere reconocimiento de texto)", "—"),
    ("D18", "Convenio Marco y régimen de locaciones", "Res. 211/2018 y 101/2019 · Dec. 1178/2025 · Circ. 007 de locaciones", "Falta lectura", "Rama E", "PENDIENTE", LEER,
     "Leer las cuatro normas", "—"),
    ("D19", "Quién declara desierta la licitación", "Ley 116 c.3 (pág. 40) · Dec. 1104 art. 116 c ap. 3 (pág. 18)", "Falta documentación", "Desierto → B",
     "PENDIENTE", SCYGB, "¿Qué autoridad declara desierta o fracasada una licitación o concurso y por qué acto?", "—"),
    ("D20", "Equivalencia entre la revocación del llamado y el acto «sin efecto» del Supervisor",
     "Revocación: Pliego Único 5.5 (pág. 38) — regla VERIFICADA · «sin efecto»: Circ. UG 7/2026 pto 10 (pág. 3)", "Alcance no confirmado",
     "Excepción de revocación (la regla se muestra; la equivalencia, no)", "PENDIENTE (equivalencia) · la regla de revocación: VERIFICADA", UG,
     "¿El acto «sin efecto» que carga el Supervisor en TIMBÓ Compras es el de la revocación del llamado del Pliego Único 5.5?", "—"),
]

CONSERVADOS = [
    ("Rama E · Locación de inmuebles", "VERIFICADO (tope del concurso de precios) · PENDIENTE (régimen: D18)"),
    ("Rama E · Etapa múltiple", "VERIFICADO (la selecciona la Unidad Rectora; expediente + DO; sobres en papel según Circ. UG 8/2026) · PENDIENTE (compatibilidad del papel con el Dec. 2518/25)"),
    ("Rama E · Convenio Marco", "PENDIENTE (D18)"),
    ("Rama E · Subasta", "VERIFICADO (Ley 116 b; Dec. 1104 art. 116 b)"),
    ("F1 · SIN y Tribunal de Cuentas", "VERIFICADO el texto de la Circ. UG 11/2026 art. 1 («todos los actos administrativos —con y sin efecto hacendal—») para los actos del tronco de TIMBÓ Compras · OBSERVADO su alcance en la directa por monto (D9)"),
    ("F2 · Vista e impugnación de ofertas", "VERIFICADO (Pliego 4.3; Circ. UG 7 pto 20.1)"),
    ("F5 · Publicar la adjudicación", "VERIFICADO para público · PENDIENTE para privado (D11)"),
    ("F6 · Perfeccionamiento y caducidad", "VERIFICADO (Pliego 5.4 y 5.6)"),
    ("F7 · Empate, oferta única, vicio", "VERIFICADO (Pliego 4.3, 5.2, 5.3; Ley 133; Dec. 1104 art. 133.1)"),
    ("F7 · Revocación del llamado", "VERIFICADO (Pliego 5.5) · PENDIENTE la equivalencia con el «sin efecto» (D20)"),
    ("F7 · Desierto → B", "VERIFICADO (Ley 116 c.3) · PENDIENTE quién lo declara (D19) y el recorrido de B (D1)"),
]

ETAPA_MULTIPLE = [
    ("Dec. 2518/25 arts. 1 y 2 (03/10/2025)", "Desde el 01/07/2026 la Administración centralizada y descentralizada gestiona todas sus actuaciones exclusivamente por medios digitales (TIMBÓ); no se puede iniciar ninguna gestión en papel por el SIE."),
    ("Circ. UG 8/2026 arts. 5, 7 y 8 (08/07/2026)", "Régimen transitorio: la etapa múltiple se sustancia por Expediente Electrónico y Documentos Oficiales; las ofertas se entregan en sobres de papel, que son el formato válido y vinculante; la documentación en papel no se digitaliza y queda en custodia; el expediente deja constancia."),
    ("Lo que se puede afirmar", "El expediente y las actas son digitales (coincide con el Dec. 2518/25). Lo que queda en papel son las ofertas de los proveedores, por un régimen transitorio de la Unidad de Gestión, posterior al decreto."),
    ("Lo que queda PENDIENTE", "La Circ. UG 8/2026 no menciona el Dec. 2518/25 ni dice expresamente que sea una excepción a él. Falta confirmar que la entrega de ofertas en papel sea compatible con el decreto (la UG TIMBÓ orienta y operativiza su implementación, art. 3 del Dec. 2518/25)."),
]

ESQUEMA = """● INICIO · nace la necesidad                                   [PENDIENTE: quién, a relevar]
→ Expediente electrónico (etapa preparatoria)                  [VERIFICADO · UG 7 ptos 6 y 11 · Dec. 2518/25]
→ Monto estimado: total con prórrogas                          [VERIFICADO · Dec. 1104 art. 116.1]
◆1 ¿Hay una causal de contratación directa?                    [VERIFICADO · Ley 116 c]
   ├ Urgencia o desierto ──► B                                 [PENDIENTE D1: recorrido en TIMBÓ Compras]
   │     · si supera $29.250.000: intervención previa SCyGB    [VERIFICADO · Dec. 652/2020]
   │     · urgencia ≥3 cotizaciones · desierto mismas condic.   [VERIFICADO · Dec. 1104 art. 116 c; UG 8 art. 4]
   ├ Otra causal (ap. 4 a 8) ──► A2 · por expediente ──► Contrato
   │     causales y trámite digital                            [VERIFICADO · Ley 116 c; UG 2/2025]
   │     intervención SCyGB en ap. 4, 5 y 8                    [PENDIENTE D17]
   └ No ▼
◆2 ¿Es una modalidad especial? (rama E)
   ├ Alquiler de inmueble ──► concurso de precios (≤ $29.250.000) [VERIFICADO tope · PENDIENTE régimen D18]
   ├ Etapa múltiple ──► D · la selecciona la Unidad Rectora     [VERIFICADO · Dec. 287/2026 art. 123]
   │     expediente + Documentos Oficiales                     [VERIFICADO · UG 8 arts. 5-6]
   │     ofertas en sobres de papel (régimen transitorio)      [VERIFICADO UG 8 art. 7 · PENDIENTE compatibilidad Dec. 2518/25]
   │     ──► Adjudicación
   ├ Convenio Marco                                            [PENDIENTE D18]
   ├ Subasta (autoriza el Poder Ejecutivo) ──► Contrato         [VERIFICADO · Ley 116 b]
   └ No ▼
◆3 ¿Cuánto es el monto? (montos 2026)                          [VERIFICADO · Circ. SCyGB 01/2026; Dec. 2233/16 art. 1]
   ├ Hasta $5.850.000 ──► A · directa por monto
   │     Secuencia de formularios                              [VERIFICADO · Dec. 1247/08 Anexo I]
   │       CD-01 → CD-02 (según el monto) → CD-03 → CD-04 · rechazo: CD-05
   │     Quién autoriza y quién adjudica                       [OBSERVADO D8]
   │     Comunicación al Tribunal de Cuentas                   [OBSERVADO D9]
   │     Soporte (papel / digital) y presupuestos              [OBSERVADO D10 · DOCUMENTADO video]
   │     ──► Recepción y pago
   ├ Hasta $58.500.000 ──► C · privado
   │     ≥5 invitaciones fehacientes, 5 días corridos          [VERIFICADO · Dec. 1104 art. 121.1]
   │     ¿cuentan las invitaciones de TIMBÓ?                   [PENDIENTE D6]
   └ Más de $58.500.000 ──► C · público
         Boletín Oficial 2 días                                [VERIFICADO · Dec. 1104 art. 132.3 y Circ. 04/2026]
         cantidad de diarios (uno o dos)                       [OBSERVADO D4]
         10 días corridos (20 si es internacional)             [VERIFICADO · Dec. 1104 art. 132.3]
                   ▼ (privado y público comparten el tronco de TIMBÓ Compras)
Pliego (Gestor)                                                [VERIFICADO · UG 7 pto 10]
· revisión de la Jurisdicción comitente — orden no documentado [VERIFICADO rol · PENDIENTE orden D13]
◆ ¿El Supervisor aprueba los formularios?                      [VERIFICADO · UG 7 pto 10]
   └ No → ? qué sigue                                          [PENDIENTE D12]
→ Control de pliegos de la URC: «si aplica»                    [PENDIENTE D5]
· cronograma y nómina (Supervisor) — orden respecto de la URC  [VERIFICADO rol · PENDIENTE orden D13]
→ Acto que aprueba el pliego y autoriza el llamado             [OBSERVADO D7: Dec. 2233 art. 2 y Circ. 01/2026; sin tramos trasladados]
→ SIN y Tribunal de Cuentas del acto                           [VERIFICADO · UG 11 art. 1]
→ Publicación (privado / público) → Consultas y circulares     [VERIFICADO]
→ Ofertas → Apertura automática                                [VERIFICADO · UG 7 ptos 18-19]
→ ◆ ¿Impugnan ofertas? (2 días hábiles)                        [VERIFICADO · Pliego 4.3]
→ Evaluación: ◆subsanar · ◆empate → mejora (≤5 %) / sorteo     [VERIFICADO · UG 7 pto 21; Pliego 5.3; Dec. 1104 art. 133.1]
              ◆desierto → B                                    [VERIFICADO paso · PENDIENTE D19 y D1]
→ Preadjudicación                                              [VERIFICADO · UG 7 pto 22; Pliego 5.1]
→ Control de la preadjudicación de la URC: «si aplica»         [PENDIENTE D5]
→ ◆ ¿Impugnan la preadjudicación? (2 días, garantía 3 %)       [VERIFICADO · Pliego 5.1 y 10.1.3]
→ Adjudicación
   · firma según monto                                         [VERIFICADO texto Dec. 2233 art. 3 · PENDIENTE equivalente en el hospital]
   · notificación ≤10 días hábiles                             [VERIFICADO · Pliego 5.4]
   · SIN y Tribunal de Cuentas                                 [VERIFICADO · UG 11 art. 1]
   · publicar en Internet: público                             [VERIFICADO · Ley 132; Dec. 1104 art. 132.4]
                           privado                             [PENDIENTE D11]
   · vale si la adjudicación supera hasta 20 % el máximo       [VERIFICADO · Dec. 1104 art. 116.1]
→ Contrato: orden de compra (10 días corridos) · garantía de fiel cumplimiento (5 días)
   ◆ no cumple → se deja sin efecto → siguiente en el orden de mérito  [VERIFICADO · Pliego 5.6]
→ Recepción provisoria → definitiva y certificado → factura → pago [VERIFICADO reglas · PENDIENTE sistema y soporte]
■ FIN
Fuera de la línea:
   revocación del llamado, en cualquier momento antes del contrato [VERIFICADO · Pliego 5.5]
   ¿es el acto «sin efecto» que carga el Supervisor?            [PENDIENTE D20]"""

CONSULTA_D7 = """Nota de consulta — Subsecretaría de Contrataciones y Gestión de Bienes (Unidad Rectora Central)

Ref.: competencia para aprobar el pliego de bases y condiciones particulares en procedimientos tramitados por TIMBÓ Compras.

Al revisar la normativa vigente para representar el circuito de compras de un hospital del Ministerio de Salud, encontramos dos referencias que podrían interpretarse de manera distinta:

1. Decreto N° 2233/16, artículo 2°: los actos de aprobación de los pliegos de bases y condiciones particulares de las contrataciones efectuadas según los arts. 116 y 140 de la Ley N° 12.510 «serán suscriptos por» el Subsecretario de Coordinación Técnica y Gestión Administrativa o su equivalente funcional (o a quien se le haya delegado la facultad), o por el Director Provincial de Contrataciones y Gestión de Bienes en los procedimientos de la Unidad Rectora Central. El artículo no establece tramos por monto.

2. Circular SCyGB N° 01/2026 (5/1/2026), apartado «Aprobación de actos licitatorios»: hasta $5.850.000, resolución del Subsecretario de Administración o su equivalente; entre $5.850.000 y $29.250.000, resolución; entre $29.250.000 y $58.500.000, resolución conjunta con el Ministerio de Economía; más de $58.500.000, decreto. Los valores de estos tramos coinciden con los porcentajes del art. 3° del Decreto N° 2233/16 (10 %, 50 % y 100 % del tope del privado), referido a los actos de adjudicación y/o aprobación de las contrataciones.

Consultamos:
a) ¿El acto que aprueba el pliego y autoriza el llamado (Circular UG TIMBÓ N° 7/2026, punto 10) debe suscribirlo siempre el funcionario del art. 2° del Decreto N° 2233/16, cualquiera sea el monto?
b) ¿Los tramos de la Circular N° 01/2026 se aplican a ese acto, a la adjudicación, o a ambos? En el segundo tramo, ¿de qué funcionario es la «Resolución»?
c) En un hospital, ¿qué funcionario es el «equivalente funcional» del Subsecretario de Coordinación Técnica y Gestión Administrativa?

Mientras tanto, el circuito muestra las dos referencias y deja la competencia como OBSERVADA."""

SINCRONIZAR = [
    ("Sitio público: «¿Qué camino sigue una compra?»", "/recursos/algoritmo · algoritmo_publico()"),
    ("Buscador global (índice de Recursos)", "app/recursos/__init__.py"),
    ("«Explicame este paso»", "capacitacion.json → nodos del algoritmo"),
    ("Flujos paso a paso y gráfico SVG (admin)", "/admin/recursos/flujos · /admin/recursos/grafico"),
    ("Capacitación: algoritmo y modo capacitadora", "/admin/capacitacion/algoritmo · /modo-capacitadora"),
    ("Inventario", "app/services/inventario.py"),
    ("Pruebas", "tests/test_recursos.py"),
]

CAMBIOS = [
    ("1", "Excepciones citaba una discrepancia con número 21, que no existe (la matriz va de D1 a D20)", "Ahora cita D19 (quién declara desierta) y D20 (revocación / «sin efecto»). No se creó ninguna discrepancia nueva."),
    ("2", "Etapa múltiple: «expediente + DO + papel» frente a la gestión digital obligatoria desde el 01/07/2026",
     "Sección nueva con las dos citas, lo que se puede afirmar (expediente y actas digitales; papel solo para las ofertas, por régimen transitorio posterior al decreto) y lo PENDIENTE (la Circ. UG 8/2026 no menciona el Dec. 2518/25). Se agregó la consulta a la UG TIMBÓ."),
    ("3", "F1 afirmaba «todos los actos» aunque D9 está observado",
     "F1 ahora dice: texto de la Circ. UG 11 VERIFICADO para el tronco de TIMBÓ Compras; alcance en la directa OBSERVADO (D9). En el esquema, la rama A no muestra SIN/TCP como verificado."),
    ("4", "Rama A mezclaba secuencia y actores",
     "Dos filas: secuencia de formularios (VERIFICADO) y actores, autorizaciones y detalle operativo (OBSERVADO D8-D10 / DOCUMENTADO video). En el esquema, cuatro líneas separadas."),
    ("5", "D8 sugería al Subsecretario como confirmado", "D8 dice «fuentes más recientes como referencia de análisis, sin presentarlas como confirmadas». También se corrigió la fila de autoridades: «Por Resolución = Ministros» pasó a ser una interpretación PENDIENTE (antes figuraba como verificada) y se agregó a la consulta formal."),
    ("6", "D4 englobaba toda la publicación", "Boletín Oficial 2 días y plazo de 10/20 días: VERIFICADO (decreto y circular coinciden). Solo la cantidad de diarios queda OBSERVADA."),
    ("7", "D20 mezclaba regla y equivalencia", "La revocación (Pliego 5.5) se muestra VERIFICADA; la equivalencia con el «sin efecto» del Supervisor, PENDIENTE."),
    ("8", "Etiquetas de D5, D11, D13 y D17",
     "D5: controles «si aplica», nunca obligatorios para el hospital. D11: publicación solo para el público; privado PENDIENTE. D13: comitente y cronograma sin orden afirmado (se agregaron al esquema con su rol verificado y su orden pendiente). D17: la intervención de la SCyGB en ap. 4, 5 y 8 no se muestra como obligatoria; A2 pasó de «Documentado» a VERIFICADO (causales y trámite) + PENDIENTE (D17)."),
    ("9", "Conservación", "Se mantienen D1 a D20, todas las ramas (A, A2, B, C privado y público, D, E) y F1, F2, F5, F6 y F7. No se cambió el estado de ninguna discrepancia: solo se separaron partes con fuentes distintas."),
]

NO_RESUELTAS = [
    (UG, "D1", "Recorrido de urgencia y desierto en TIMBÓ Compras"),
    (UG, "D12", "Qué sigue después de un rechazo del Supervisor"),
    (UG, "D13", "Orden entre comitente / Supervisor y entre cronograma / URC"),
    (UG, "D20", "Si el «sin efecto» del Supervisor es la revocación del llamado"),
    (UG, "Etapa múltiple", "Compatibilidad de las ofertas en papel (Circ. UG 8/2026) con el Dec. 2518/25"),
    (f"{UG} / {SCYGB}", "D6", "Si las invitaciones de TIMBÓ son «medio fehaciente»"),
    (f"{UG} / {SCYGB}", "D9", "Comunicación al TCP en la directa por monto"),
    (f"{UG} / {SCYGB}", "D10", "Soporte y presupuestos en la directa digital"),
    (SCYGB, "D4", "Uno o dos diarios"),
    (SCYGB, "D5", "Si los controles de la URC alcanzan a los hospitales"),
    (SCYGB, "D7", "Competencia para aprobar el pliego (consulta formal)"),
    (SCYGB, "D7 · b", "De quién es la «Resolución» del 2.º tramo de la Circ. 01/2026"),
    (SCYGB, "D7 · c", "Equivalente funcional del Subsecretario en el hospital"),
    (SCYGB, "D8", "Quién adjudica la directa por monto"),
    (SCYGB, "D11", "Publicación de la adjudicación en el privado"),
    (SCYGB, "D19", "Quién declara desierta la licitación"),
]
# D14 (sincronización interna), D17 y D18 (lecturas pendientes) no requieren consulta externa.


def tabla(cab, filas):
    th = "".join(f"<th>{h(c)}</th>" for c in cab)
    tr = "".join("<tr>" + "".join(f"<td>{h(str(c))}</td>" for c in f) + "</tr>" for f in filas)
    return f"<div class='tabla'><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>"


def html():
    estado_principal = Counter(f[5].split(" ")[0] for f in MATRIZ)
    resumen = " · ".join(f"{k}: {v}" for k, v in estado_principal.items())
    est = "".join(f"<span class='chip' style='border-color:{c};color:{c}'>{h(n)}</span> {h(d)}<br>" for n, c, d in ESTADOS)
    consultas = {}
    for f in MATRIZ:
        if f[6] != "—":
            consultas.setdefault(f[6], []).append(f"{f[0]}: {f[7]}")
    consultas.setdefault(UG, []).append("Etapa múltiple: ¿la entrega de ofertas en sobres de papel que prevé la Circ. UG 8/2026 es una excepción admitida al Dec. 2518/25?")
    bloques = "".join(f"<h3>{h(k)}</h3><ul>{''.join(f'<li>{h(q)}</li>' for q in v)}</ul>" for k, v in consultas.items())
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Circuito de compras · matriz consolidada v5.1</title>
<style>
body{{margin:0;background:#f6f7f9;color:#1f2937;font:15px/1.5 "Segoe UI",system-ui,Arial,sans-serif}}
main{{max-width:1320px;margin:0 auto;padding:24px 16px 60px}}
section{{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:20px 22px;margin-top:18px}}
h1{{margin:0 0 4px;font-size:26px}} h2{{margin:0 0 8px;font-size:20px}} h3{{margin:14px 0 4px;font-size:16px}}
table{{border-collapse:collapse;width:100%;font-size:12.8px}} th,td{{border-bottom:1px solid #e2e8f0;padding:6px 8px;text-align:left;vertical-align:top}}
th{{background:#f8fafc}} .tabla{{overflow-x:auto}} pre{{background:#0f172a;color:#e2e8f0;padding:16px;border-radius:12px;overflow-x:auto;font-size:12.3px;line-height:1.45;white-space:pre}}
.nota{{white-space:pre-wrap;background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:14px;font-size:14px}}
.chip{{display:inline-block;border:1.5px solid;border-radius:999px;padding:0 10px;font-weight:700;font-size:12.5px;margin:2px 4px 2px 0}}
</style></head><body><main>
<h1>Circuito de compras · matriz consolidada v5.1</h1>
<p>Corrige solo problemas de coherencia de la v5 ({FECHA}). 20 discrepancias (D1 a D20). Estado principal: {h(resumen)}. Ninguna discrepancia cambió de estado.</p>
<section><h2>Estados</h2><p>{est}</p></section>
<section><h2>1. Cambios respecto de la v5</h2>{tabla(["#", "Problema", "Corrección"], CAMBIOS)}</section>
<section><h2>2. Matriz consolidada (D1 a D20)</h2>
{tabla(["Id", "Tema", "Fuentes (punto · página)", "Tipo", "Impacto en el mapa", "Estado", "Consultar a", "Pregunta", "Decisión de la usuaria"], MATRIZ)}</section>
<section><h2>3. Etapa múltiple y gestión digital obligatoria</h2>{tabla(["Fuente o conclusión", "Contenido"], ETAPA_MULTIPLE)}</section>
<section><h2>4. Esquema v5.1</h2><pre>{h(ESQUEMA)}</pre></section>
<section><h2>5. La regla del 20 %</h2>
{tabla(["Regla", "Texto literal (Dec. 1104/16, art. 116, «1. Monto a considerar», pág. 17)", "Dónde va", "Estado"], REGLA_20)}</section>
<section><h2>6. Fuentes por recorrido</h2>
{tabla(["Recorrido", "Qué cubre", "Fuentes (punto · página)", "Estado", "Observaciones"], RECORRIDOS)}</section>
<section><h2>7. Ramas y hallazgos conservados</h2>{tabla(["Elemento", "Estado"], CONSERVADOS)}</section>
<section><h2>8. Consulta formal a la SCyGB (D7)</h2><div class="nota">{h(CONSULTA_D7)}</div></section>
<section><h2>9. Consultas agrupadas por destinatario</h2>{bloques}</section>
<section><h2>10. Inconsistencias que no se pueden resolver sin consultar</h2>
{tabla(["Consultar a", "Id", "Tema"], NO_RESUELTAS)}
<p>D14 (sincronización interna), D17 y D18 (lecturas pendientes) no requieren consulta externa.</p></section>
<section><h2>11. Sincronización de algoritmo.json (cuando se apruebe el circuito)</h2>
<p>No se modifica todavía. Consumidores a probar después:</p>{tabla(["Funcionalidad", "Dónde"], SINCRONIZAR)}</section>
</main></body></html>"""


if __name__ == "__main__":
    assert [f[0] for f in MATRIZ] == [f"D{i}" for i in range(1, 21)], "deben ser D1 a D20"
    texto = html()
    assert "D21" not in texto, "no debe haber referencias a D21"
    (AQUI / "matriz_v5_1.html").write_text(texto, encoding="utf-8")
    print("ok", len(MATRIZ), dict(Counter(f[5].split(" ")[0] for f in MATRIZ)))
