"""Matriz de discrepancias, fuentes por recorrido y esquema v4 (local).
No toca el proyecto.   python fuente/matriz_v4.py
"""
from html import escape as h
from pathlib import Path

AQUI = Path(__file__).resolve().parent.parent
FECHA = "18/11/2026"

ESTADOS = [
    ("Verificado", "#1b7a45", "Coincide con el texto vigente de una norma leída completa, con punto y página."),
    ("Documentado", "#2456c7", "Lo respalda material operativo oficial (video, instructivo, guía) o una norma leída, pero falta cotejarlo con la norma vigente o con su alcance."),
    ("Pendiente", "#b85400", "Falta fuente, o falta confirmar alcance, orden o actor."),
    ("Observado", "#b42318", "Hay discrepancia entre fuentes oficiales o entre representaciones del proyecto."),
]

# Fuentes nuevas leídas en esta ronda (además de las de la v3.1)
NUEVAS_FUENTES = [
    ("Decreto 1247/08 + Anexo I «Manual de Procedimiento para la Gestión de Contrataciones Directas»", "15/05/2008 · BO 22/05/2008",
     "SIN: santafe.gov.ar/normativa (item 48663)", "Decreto y Anexo I leídos completos (Anexo: págs. 5 a 8 = procedimiento)", "No está en la biblioteca: sumarlo"),
    ("Decreto 2175/2022, art. 1", "24/10/2022 · BO 27/10/2022", "Boletín Oficial", "Leído: confirma la vigencia del procedimiento del Dec. 1247/08 para la directa por monto", "No está en la biblioteca: sumarlo"),
    ("Decreto 2233/16, arts. 1 a 3", "02/09/2016", "Biblioteca: dec-2233-2016", "Leído completo (pág. 2)", "En la biblioteca"),
    ("Decreto 652/2020, arts. 1 y 3", "2020", "Biblioteca: intervencion-scygb-directas", "Leído completo (págs. 2-3)", "En la biblioteca"),
    ("Decreto 1104/16, art. 116 «1. Monto a considerar» y art. 116 c ap. 2, 3, 4 y 6", "2016, no modificado por el Dec. 287/2026", "Biblioteca: dec-1104-2016", "Leído (págs. 17-18)", "En la biblioteca"),
    ("Índice oficial de normativa de Compras", f"consultado el {FECHA}", "compras.santafe.gob.ar/normativas", "No hay circular SCyGB posterior a la 04/2026 sobre publicación (siguen 05 y 06/2026)", "—"),
]

REGLA_20 = [
    ("Cálculo del monto (para elegir el procedimiento)",
     "«…se considerará el importe total en que se estimen las adjudicaciones, incluidas las opciones de prórroga previstas.»",
     "Antes de elegir: en la decisión «¿Cuánto es el monto?»", "Verificado"),
    ("Validez del procedimiento (después, al adjudicar)",
     "«Será válido el procedimiento de selección seguido de acuerdo con la estimación del valor del contrato cuando el importe de la adjudicación supere hasta el veinte por ciento (20%) del importe máximo admitido para cada procedimiento.»",
     "En la adjudicación, como regla: no cambia el camino elegido", "Verificado"),
]

# recorrido, qué cubre, fuentes (punto · página), estado, observaciones
RECORRIDOS = [
    ("Inicio y etapa preparatoria", "Necesidad, expediente electrónico, número de EE",
     "Circ. UG 7/2026 ptos 6 y 11 (págs. 2-3) · Dec. 2518/25 arts. 1-2 (todo digital desde 01/07/2026)", "Verificado",
     "Quién arma el pedido en el hospital: pendiente (a relevar)"),
    ("Monto a considerar", "Cálculo con prórrogas y validez hasta +20 %", "Dec. 1104/16 art. 116.1 (pág. 17)", "Verificado", "Dos reglas separadas (ver tabla)"),
    ("Montos 2026 y quién adjudica", "Topes y autoridades por tramo",
     "Circ. SCyGB 01/2026 (pág. 1) · Ley 14.424 art. 36 · Dec. 2233/16 arts. 1 y 3 (pág. 2)", "Verificado",
     "2.º tramo «Por Resolución» = Ministros (Dec. 2233 art. 3.b). «Equivalente» en el hospital: pendiente"),
    ("◆1 ¿Causal de directa?", "Excepciones al procedimiento licitatorio", "Ley 12.510 art. 116 c ap. 1 a 8 (pág. 40)", "Verificado",
     "El ap. 9 (Ley 13.861 / Dec. 667/19) está en la biblioteca y no se leyó: pendiente"),
    ("A · Directa por monto", "CD-01 solicitud → informe de presupuesto (SAF) → autoriza el Subsecretario (rechazo: CD-05; sin presupuesto: modificación presupuestaria) → imputación preventiva → 3 presupuestos (CD-02 si supera el monto de habilitaciones) → CD-03 evaluación y adjudicación → acto de adjudicación → CD-04 orden de provisión → recepción (certificado) → pago",
     "Dec. 1247/08 Anexo I, págs. 5 a 8 · vigencia: Dec. 2175/2022 art. 1 · digital por expediente: Circ. UG 2/2025 pto 2 (pág. 8) · Dec. 2233/16 art. 1 (≤10 % del privado) · video oficial QH7zvgZ7sbQ",
     "Verificado (secuencia y formularios) · Observado (actores y soporte, ver D8 a D10)",
     "El manual es de 2008 (papel, fax, SIE): lo operativo actual lo muestra el video oficial"),
    ("A2 · Directa por otra causal (ap. 4 a 8)", "Fundamentación e informes; intervención de la SCyGB según el apartado",
     "Ley 116 c ap. 4 a 8 · Dec. 1104 art. 116 c ap. 4 y 6 (pág. 18) · Dec. 652/2020 (ap. 7, si supera el 50 %) · Circ. UG 2/2025 pto 2", "Documentado",
     "Disp. 282/16 (intervención SCyGB en ap. 4, 5 y 8) es un PDF escaneado: no leída"),
    ("B · Urgencia o desierto", "Causal, intervención previa de la SCyGB si supera el 50 % del privado, ≥3 cotizaciones (urgencia), mismas condiciones (desierto), TIMBÓ Compras con flexibilizaciones",
     "Ley 116 c ap. 2 y 3 (pág. 40) · Dec. 1104 art. 116 c ap. 2 y 3 (pág. 18) · Dec. 652/2020 arts. 1 y 3 (págs. 2-3) · Circ. UG 8/2026 arts. 3 y 4 (págs. 1-2)",
     "Pendiente (D1: qué pasos de TIMBÓ Compras recorre)", "Decisión de la usuaria: dejar pendiente"),
    ("◆2 Modalidades especiales (rama E)", "Locación de inmuebles · etapa múltiple · Convenio Marco · subasta",
     "Circ. SCyGB 01/2026 y Ley art. 140 (locación ≤ $29.250.000) · Dec. 1104 art. 123 texto Dec. 287/2026 (pág. 3) y Circ. UG 8/2026 arts. 5 a 8 (etapa múltiple) · Ley art. 116 b y Dec. 1104 art. 116 b (subasta)",
     "Verificado: etapa múltiple y subasta · Pendiente: Convenio Marco y régimen de locaciones",
     "Etapa múltiple: la selecciona la Unidad Rectora (decisión de la usuaria). Locaciones: Dec. 1178/2025 y Circ. 007 sin leer"),
    ("◆3 ¿Cuánto es el monto?", "Directa / privado / público", "Circ. SCyGB 01/2026 · Dec. 2233/16 art. 1 · Ley 116 a", "Verificado", "—"),
    ("C · Licitación o concurso privado", "≥5 invitaciones fehacientes, 5 días corridos, difusión en Internet",
     "Ley 116 a y 118 · Dec. 1104 art. 116 a.1 (pág. 17) y art. 121.1 (pág. 20) · Circ. UG 3/2026 (TIMBÓ Compras obligatorio)", "Verificado · Pendiente (D6)", "—"),
    ("C · Licitación o concurso público", "Boletín Oficial 2 días + diarios, 10/20 días, portal y aviso",
     "Ley 132 (pág. 43) · Dec. 1104 art. 132.3 y 132.4 (pág. 26) · Circ. SCyGB 04/2026 (Adm. Central)", "Verificado · Observado (D4)", "—"),
    ("Tronco de TIMBÓ Compras", "Pliego, aprobación, acto, publicación, consultas, ofertas, apertura, vista e impugnación, evaluación, preadjudicación, impugnación",
     "Circ. UG 7/2026 ptos 6 a 22 (págs. 2-5) · Pliego Único 4.3, 5.1-5.3 y 10.1.3 · Dec. 1104 art. 133.1 · Circ. UG 9 y 11/2026",
     "Verificado · Observado (D7) · Pendiente (D5, D12, D13)", "—"),
    ("Adjudicación y contrato", "Acto (firma según monto), notificación, publicación (públicos), perfeccionamiento, caducidad",
     "Circ. UG 7/2026 pto 6 · Dec. 2233/16 art. 3 · Pliego Único 5.4 a 5.6 (pág. 38) · Ley 132", "Verificado · Pendiente (D11)", "—"),
    ("Recepción, factura y pago", "Recepción provisoria y definitiva, certificado, factura, pago",
     "Pliego Único 6.9 a 6.13 (págs. 46-49) · para la directa: Dec. 1247/08 Anexo I pág. 8", "Verificado (reglas) · Pendiente (sistema, oficina y soporte)", "—"),
    ("Excepciones", "Revocación, vicio, empate, oferta única, desierto → B, caducidad",
     "Pliego Único 4.3, 5.2, 5.3, 5.5, 5.6 · Ley 116 c.3 y 133 · Dec. 1104 art. 116 c ap. 3", "Verificado · Pendiente (D11, D21)", "—"),
]

# id, tema, fuente A, fuente B, tipo, impacto en el mapa, propuesta, estado
MATRIZ = [
    ("D1", "Recorrido de la rama B en TIMBÓ Compras", "Algoritmo público: salta del inicio a «ofertas»", "Circ. UG 8/2026 art. 4: solo flexibiliza autorización, plazos, requisitos e invitaciones; circuito oficial: entra por el pliego",
     "Diferencia entre representaciones del proyecto + falta documentación", "Dónde se une B al tronco", "Mostrar B con su causal, la intervención SCyGB (Dec. 652) y «recorrido en TIMBÓ Compras: pendiente»; sin unir al tronco", "Pendiente (decisión de la usuaria)"),
    ("D2", "Quién selecciona la etapa múltiple", "Algoritmo: la elige el organismo", "Dec. 1104 art. 123, texto Dec. 287/2026 (pág. 3): «De seleccionar la Unidad Rectora…»",
     "Texto superado en el proyecto", "La opción ◆2 no la decide el hospital", "Representar «la selecciona la Unidad Rectora»", "Resuelto (aprobado por la usuaria)"),
    ("D3", "Pasos de la directa por monto", "Circuito oficial: pendiente", "Algoritmo: CD-01 a CD-04 (video oficial) · Dec. 1247/08 Anexo I (verificado hoy)",
     "Diferencia entre representaciones", "Rama A completa", "Secuencia y formularios: Verificado (Dec. 1247/08); detalles operativos: Documentado (video)", "Resuelto en parte (ver D8 a D10)"),
    ("D4", "Uno o dos diarios", "Dec. 1104 art. 132.3 (2016, vigente): «un (1) día en dos diarios»", "Circ. SCyGB 04/2026, Anexo II (nota modelo, 19/05/2026): «un (1) día en un (1) diario»",
     "Contradicción normativa (decreto vs. nota modelo de circular)", "Publicación del público", "Mostrar las dos citas, sin elegir. El Dec. 287/2026 solo modificó el 132.1 (pliegos en la web), que la Circ. 04/2026 cita textual", "Pendiente (decisión de la usuaria)"),
    ("D5", "Controles de la URC en el hospital", "Res. ME 73/2026 y Circ. SCyGB 03/2026", "Dirigidas a la Administración Pública Central",
     "Alcance no confirmado", "Dos controles en el tronco", "«Si aplica (a confirmar)»", "Pendiente"),
    ("D6", "Invitaciones del privado", "Dec. 1104 art. 121.1: 5 invitaciones «por medio fehaciente»", "Circ. UG 7/2026 pto 15: TIMBÓ Compras envía invitaciones a la nómina (complementarias)",
     "Alcance no confirmado", "Publicación del privado", "Mostrar el requisito y la duda", "Pendiente"),
    ("D7", "Quién firma el acto que aprueba el pliego", "Dec. 2233/16 art. 2 (pág. 2): el Subsecretario de Coordinación Técnica y Gestión Administrativa o equivalente (o delegado); sin tramos", "Circuito oficial (o16) y algoritmo: «autoridad según monto» (Circ. SCyGB 01/2026, «aprobación de actos licitatorios»)",
     "Contradicción entre normas o error de interpretación del proyecto", "Actor de la etapa 4", "Mostrar las dos y consultar a la SCyGB: ¿los tramos de la Circ. 01 son para la aprobación del pliego o para la adjudicación?", "Observado · NUEVO"),
    ("D8", "Quién adjudica la directa por monto", "Dec. 1247/08 Anexo I (2008): «Disposición de Adjudicación» del Director del SAF", "Dec. 2233/16 art. 3.a (2016) y Circ. SCyGB 01/2026: Subsecretario o equivalente (o delegado)",
     "Fuentes de distinta fecha", "Actor de la rama A", "Mostrar las dos; la más reciente (Dec. 2233/16 y Circ. 01/2026) coincide en el Subsecretario", "Observado · NUEVO"),
    ("D9", "Comunicación al Tribunal de Cuentas en la directa", "Dec. 1247/08 Anexo I: copia del acto a la Delegación Fiscal (Res. TCP 007/06)", "Circ. UG 9 y 11/2026: todo acto al SIN y vista con «Gestión de Visualización»",
     "Fuentes de distinta fecha", "Rama A", "Mostrar la de 2026 como vigente para la comunicación; la Res. TCP 007/06 no se leyó", "Observado · NUEVO"),
    ("D10", "Soporte de la directa", "Dec. 1247/08 (2008): presupuestos por teléfono, fax o correo; expediente en papel", "Circ. UG 2/2025 pto 2 y Dec. 2518/25: exclusivamente digital",
     "Fuentes de distinta fecha", "Soporte de la rama A", "Digital por expediente; los presupuestos como documento informativo (video oficial: Documentado)", "Observado · NUEVO"),
    ("D11", "Publicación de la adjudicación en el privado", "Ley 132 y Dec. 1104 art. 132.4: hablan de licitación y concurso público", "—",
     "Alcance no confirmado", "Etapa de adjudicación", "Público: verificado; privado: pendiente", "Pendiente"),
    ("D12", "Qué sigue después de un rechazo del Supervisor", "Circ. UG 7/2026 pto 10: «aprueba o rechaza»", "—", "Falta documentación", "Salida «Rechazado» sin destino", "Pendiente de documentación", "Pendiente"),
    ("D13", "Orden entre pasos del pliego", "Circ. UG 7/2026 define roles, no el orden (comitente/Supervisor; cronograma/URC)", "—", "Falta documentación", "Orden en la etapa 4", "Mostrar sin orden afirmado", "Pendiente"),
    ("D14", "El algoritmo público y el circuito oficial no coinciden", "algoritmo.json (público)", "Circuito oficial en /admin/procesos",
     "Diferencia entre representaciones del proyecto", "Riesgo de enseñar cosas distintas", "El mapa nuevo será la referencia; la sincronización del público se decide aparte", "Pendiente (decisión de la usuaria)"),
    ("D15", "Representación del 20 %", "v3.1 los presentaba juntos", "Dec. 1104 art. 116.1 (pág. 17): son dos reglas", "Error de representación (corregido)", "Decisión ◆3 y adjudicación", "Separadas (ver tabla)", "Resuelto"),
    ("D16", "Intervención de la SCyGB en urgencia y desierto", "Dec. 652/2020 arts. 1 y 3: intervención previa si supera el 50 % del privado", "Circuito oficial: no la tiene (el algoritmo sí)",
     "Diferencia entre representaciones", "Rama B", "Sumarla a la rama B (Verificado)", "Para sumar"),
    ("D17", "Intervención de la SCyGB en ap. 4, 5 y 8", "Disp. 282/16 (PDF escaneado)", "—", "Falta lectura", "Rama A2", "Pendiente hasta leerla", "Pendiente"),
    ("D18", "Convenio Marco y régimen de locaciones", "Res. 211/2018, 101/2019, Dec. 1178/2025, Circ. 007", "—", "Falta lectura", "Rama E", "Pendiente hasta leerlas", "Pendiente"),
    ("D19", "Quién declara desierta la licitación", "—", "—", "Falta documentación", "Desierto → B", "Pendiente", "Pendiente"),
    ("D20", "Relación entre «sin efecto» del Supervisor y la revocación", "Circ. UG 7/2026 pto 10", "Pliego Único 5.5", "Alcance no confirmado", "Excepción de revocación", "Pendiente", "Pendiente"),
]

# Elementos que la usuaria pidió conservar identificados (rama E y F1, F2, F5, F6, F7)
CONSERVADOS = [
    ("Rama E · Locación de inmuebles", "Pendiente (régimen Dec. 1178/2025 sin leer) · Verificado el tope del concurso de precios"),
    ("Rama E · Etapa múltiple", "Verificado (Dec. 287/2026 art. 123; Circ. UG 8/2026 arts. 5 a 8). La selecciona la Unidad Rectora"),
    ("Rama E · Convenio Marco", "Pendiente"),
    ("Rama E · Subasta", "Verificado (Ley 116 b; Dec. 1104 art. 116 b)"),
    ("F1 · SIN y TCP para todos los actos", "Verificado (Circ. UG 11/2026 arts. 1-2)"),
    ("F2 · Vista e impugnación de ofertas", "Verificado (Pliego 4.3; Circ. UG 7 pto 20.1)"),
    ("F5 · Publicar la adjudicación", "Verificado para público · Pendiente para privado (D11)"),
    ("F6 · Perfeccionamiento y caducidad", "Verificado (Pliego 5.4 y 5.6)"),
    ("F7 · Empate, oferta única, vicio", "Verificado (Pliego 4.3, 5.2, 5.3; Ley 133; Dec. 1104 art. 133.1)"),
    ("F7 · Revocación", "Verificado (Pliego 5.5) · Pendiente la relación con «sin efecto» (D20)"),
    ("F7 · Desierto → B", "Verificado el paso (Ley 116 c.3) · Pendiente quién lo declara (D19) y el recorrido de B (D1)"),
]

ESQUEMA = """● INICIO · nace la necesidad                                        [Pendiente: quién, a relevar]
→ Expediente electrónico (etapa preparatoria)                       [Verificado · UG 7 ptos 6 y 11 · Dec. 2518/25]
→ Monto estimado: total con prórrogas                               [Verificado · Dec. 1104 art. 116.1]
◆1 ¿Hay una causal de contratación directa?                         [Verificado · Ley 116 c]
   ├ Urgencia o desierto ──► B ─────────────────────────────────────[Pendiente D1: recorrido en TIMBÓ Compras]
   │     · si supera $29.250.000: intervención previa de la SCyGB  [Verificado · Dec. 652/2020]
   │     · urgencia: ≥3 cotizaciones · desierto: mismas condiciones [Verificado · Dec. 1104 art. 116 c; UG 8 art. 4]
   ├ Otra causal (ap. 4 a 8) ──► A2 · por expediente ──► Contrato   [Documentado · Disp. 282/16 sin leer]
   └ No ▼
◆2 ¿Es una modalidad especial? (rama E)
   ├ Alquiler de inmueble ──► concurso de precios (≤ $29.250.000)   [Verificado tope · Pendiente régimen]
   ├ Etapa múltiple ──► D · la selecciona la Unidad Rectora ──► expediente + DO + papel ──► Adjudicación
   │                                                               [Verificado · Dec. 287/2026 art. 123; UG 8]
   ├ Convenio Marco ─────────────────────────────────────────────── [Pendiente]
   ├ Subasta (autoriza el Poder Ejecutivo) ──► Contrato             [Verificado · Ley 116 b]
   └ No ▼
◆3 ¿Cuánto es el monto? (montos 2026)                               [Verificado · Circ. SCyGB 01/2026; Dec. 2233/16]
   ├ Hasta $5.850.000 ──► A · directa por monto
   │     CD-01 → informe de presupuesto → ◆autoriza? (No → CD-05 rechazo · sin crédito → modificación presupuestaria)
   │     → imputación → 3 presupuestos (CD-02) → CD-03 evaluación → acto de adjudicación → CD-04 orden de provisión
   │                                                               [Verificado · Dec. 1247/08 · Observado D8-D10]
   │     ──► Recepción y pago
   ├ Hasta $58.500.000 ──► C · privado (≥5 invitaciones, 5 días)  [Verificado · Pendiente D6]
   └ Más de $58.500.000 ──► C · público (BO 2 días + diarios, 10 días) [Verificado · Observado D4]
                   ▼ (privado y público comparten el tronco de TIMBÓ Compras)
Pliego (Gestor) → ◆Supervisor aprueba? (No → ? qué sigue · D12) → [URC si aplica · D5]
→ Acto que aprueba el pliego y autoriza el llamado [Observado D7: ¿Subsecretario (Dec. 2233 art. 2) o según monto?]
→ SIN y TCP [Verificado · UG 11] → Publicación (privado / público) → Consultas y circulares
→ Ofertas → Apertura automática → ◆¿Impugnan ofertas? (2 días) [Verificado · Pliego 4.3]
→ Evaluación ◆subsanar · ◆empate → mejora (≤5 %) / sorteo · ◆desierto → B [Verificado · Pendiente D19]
→ Preadjudicación → [URC si aplica] → ◆¿Impugnan? (2 días, garantía 3 %) [Verificado]
→ Adjudicación: firma según monto (Dec. 2233 art. 3) · notificación ≤10 días hábiles · SIN y TCP
   · publicar en Internet (público; privado: D11)                 [Verificado · Pendiente D11]
   · regla: vale si la adjudicación supera hasta 20 % el máximo   [Verificado · Dec. 1104 art. 116.1]
→ Contrato: orden de compra (10 días corridos) · garantía de fiel cumplimiento (5 días)
   ◆no cumple → se deja sin efecto → siguiente en el orden de mérito [Verificado · Pliego 5.6]
→ Recepción provisoria → definitiva y certificado → factura → pago [Verificado reglas · Pendiente sistema y soporte]
■ FIN
Fuera de la línea: revocación del llamado, en cualquier momento antes del contrato [Verificado · Pliego 5.5 · D20]"""


def tabla(cab, filas):
    th = "".join(f"<th>{h(c)}</th>" for c in cab)
    tr = "".join("<tr>" + "".join(f"<td>{h(str(c))}</td>" for c in f) + "</tr>" for f in filas)
    return f"<div class='tabla'><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>"


def html():
    est = "".join(f"<span class='chip' style='border-color:{c};color:{c}'>{h(n)}</span> {h(d)}<br>" for n, c, d in ESTADOS)
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Circuito de compras · matriz v4</title>
<style>
body{{margin:0;background:#f6f7f9;color:#1f2937;font:15px/1.5 "Segoe UI",system-ui,Arial,sans-serif}}
main{{max-width:1300px;margin:0 auto;padding:24px 16px 60px}}
section{{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:20px 22px;margin-top:18px}}
h1{{margin:0 0 4px;font-size:26px}} h2{{margin:0 0 8px;font-size:20px}}
table{{border-collapse:collapse;width:100%;font-size:13px}} th,td{{border-bottom:1px solid #e2e8f0;padding:6px 8px;text-align:left;vertical-align:top}}
th{{background:#f8fafc}} .tabla{{overflow-x:auto}} pre{{background:#0f172a;color:#e2e8f0;padding:16px;border-radius:12px;overflow-x:auto;font-size:12.5px;line-height:1.45}}
.chip{{display:inline-block;border:1.5px solid;border-radius:999px;padding:0 10px;font-weight:700;font-size:13px;margin:2px 4px 2px 0}}
</style></head><body><main>
<h1>Circuito de compras · matriz de discrepancias y esquema v4</h1>
<p>Revisión del {FECHA}. Archivo local: no modifica el proyecto.</p>
<section><h2>Estados de validación</h2><p>{est}</p></section>
<section><h2>1. Esquema del recorrido (v4)</h2><pre>{h(ESQUEMA)}</pre></section>
<section><h2>2. La regla del 20 %: dos reglas distintas</h2>
{tabla(["Regla", "Texto literal (Dec. 1104/16, art. 116, «1. Monto a considerar», pág. 17)", "Dónde va en el mapa", "Estado"], REGLA_20)}</section>
<section><h2>3. Fuentes oficiales por recorrido</h2>
{tabla(["Recorrido", "Qué cubre", "Fuentes (punto · página)", "Estado", "Observaciones"], RECORRIDOS)}</section>
<section><h2>4. Matriz de discrepancias</h2>
{tabla(["Id", "Tema", "Fuente A", "Fuente B", "Tipo", "Impacto en el mapa", "Propuesta", "Estado"], MATRIZ)}</section>
<section><h2>5. Rama E y F1, F2, F5, F6, F7: conservados y clasificados</h2>
{tabla(["Elemento", "Estado"], CONSERVADOS)}</section>
<section><h2>6. Fuentes nuevas leídas en esta ronda</h2>
{tabla(["Documento", "Fecha", "Dónde", "Lectura", "Biblioteca"], NUEVAS_FUENTES)}</section>
</main></body></html>"""


if __name__ == "__main__":
    (AQUI / "matriz_v4.html").write_text(html(), encoding="utf-8")
    print("ok", len(MATRIZ), "discrepancias,", len(RECORRIDOS), "recorridos")
