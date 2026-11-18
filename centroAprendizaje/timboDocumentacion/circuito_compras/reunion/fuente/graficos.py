"""Genera los dos gráficos de la guía de reunión con Compras.

    python fuente/graficos.py

Salida (en la carpeta de arriba): circuito_compra.svg y quien_hace_que.svg.
Para cambiar un texto, buscalo en este archivo y volvé a correrlo; después
corré fuente/armar.py para actualizar la guía HTML, los PNG y el PDF.
"""
from pathlib import Path
from xml.sax.saxutils import escape

SALIDA = Path(__file__).resolve().parent.parent
FUENTE = "font-family=\"Segoe UI, system-ui, -apple-system, Roboto, Arial, sans-serif\""

# Colores: uno por sistema
EXP = dict(fill="#e9f1ff", stroke="#2f6fde", ink="#1d4fae", nombre="EXPEDIENTE ELECTRÓNICO TIMBÓ")
COM = dict(fill="#e2f6ee", stroke="#11936a", ink="#0b6b4d", nombre="MÓDULO TIMBÓ COMPRAS")
EXT = dict(fill="#fff3df", stroke="#d48806", ink="#8a5800", nombre="ÁREAS DEL HOSPITAL Y ORGANISMOS EXTERNOS")
DEC = dict(fill="#f3efff", stroke="#6a4fd6", ink="#4a33a8")
TXT, SUB = "#1f2937", "#4b5563"


def t(x, y, s, size=13, weight=400, color=TXT, anchor="middle", extra=""):
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color}" '
            f'text-anchor="{anchor}" {extra}>{escape(s)}</text>')


# ---------------------------------------------------------------------------
# Gráfico 1: circuito completo de una compra
# ---------------------------------------------------------------------------

W = 1420
CARRIL = {1: (160, 560), 2: (580, 980), 3: (1000, 1400)}   # x de cada carril
CX = {k: (a + b) // 2 for k, (a, b) in CARRIL.items()}
BW = 340


def caja(carril, y, num, titulo, lineas, kind, h=None, punteada=False, etiqueta=None, ancho=BW, cx=None):
    cx = cx or CX[carril]
    h = h or (40 + 16 * len(lineas))
    return dict(x=cx - ancho / 2, y=y, w=ancho, h=h, cx=cx, num=num, titulo=titulo,
                lineas=lineas, kind=kind, punteada=punteada, etiqueta=etiqueta, carril=carril)


def dibujar_caja(b, pid):
    k = b["kind"]
    dash = ' stroke-dasharray="7 5"' if b["punteada"] else ""
    out = [f'<rect x="{b["x"]}" y="{b["y"]}" width="{b["w"]}" height="{b["h"]}" rx="12" '
           f'fill="{k["fill"]}" stroke="{k["stroke"]}" stroke-width="2"{dash} filter="url(#{pid}sombra)"/>']
    ty = b["y"] + 24
    out.append(t(b["cx"], ty, b["titulo"], 15, 700, k["ink"]))
    for i, ln in enumerate(b["lineas"]):
        out.append(t(b["cx"], ty + 19 + 16 * i, ln, 12.5, 400, SUB))
    if b["num"]:
        out.append(f'<circle cx="{b["x"]}" cy="{b["y"]}" r="15" fill="{k["stroke"]}" stroke="#fff" stroke-width="2.5"/>')
        out.append(t(b["x"], b["y"] + 5, str(b["num"]), 13, 700, "#fff"))
    if b["etiqueta"]:
        ew = 9 + 6.6 * len(b["etiqueta"])
        ex = b["x"] + b["w"] - ew - 8
        out.append(f'<rect x="{ex}" y="{b["y"] - 10}" width="{ew}" height="20" rx="10" fill="#fff" '
                   f'stroke="{k["stroke"]}" stroke-width="1.5"{dash}/>')
        out.append(t(ex + ew / 2, b["y"] + 4, b["etiqueta"], 10.5, 700, k["ink"]))
    return "\n".join(out)


def flecha(a, b, pid, color="#475569", punteada=False, lado=False, texto=None):
    dash = ' stroke-dasharray="6 5"' if punteada else ""
    if lado:  # misma fila: de costado
        y = a["y"] + a["h"] / 2
        if b["cx"] < a["cx"]:
            x1, x2 = a["x"], b["x"] + b["w"]
        else:
            x1, x2 = a["x"] + a["w"], b["x"]
        d = f"M{x1},{y} L{x2 + (8 if x2 < x1 else -8)},{y}"
        lab = t((x1 + x2) / 2, y - 8, texto, 11.5, 600, color) if texto else ""
    else:
        x1, y1 = a["cx"], a["y"] + a["h"]
        x2, y2 = b["cx"], b["y"]
        if abs(x1 - x2) < 2:
            d = f"M{x1},{y1} L{x2},{y2 - 8}"
        else:
            ym = y1 + (y2 - y1) / 2
            d = f"M{x1},{y1} L{x1},{ym} L{x2},{ym} L{x2},{y2 - 8}"
        lab = t(x1 + 8, y1 + 18, texto, 11.5, 600, color, "start") if texto else ""
    return (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2.2"{dash} '
            f'marker-end="url(#{pid}punta)"/>' + lab)


def defs(pid):
    return f"""<defs>
  <marker id="{pid}punta" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
    <path d="M0,0 L10,5 L0,10 z" fill="#475569"/>
  </marker>
  <filter id="{pid}sombra" x="-5%" y="-10%" width="110%" height="130%">
    <feDropShadow dx="0" dy="1.5" stdDeviation="1.5" flood-color="#0f172a" flood-opacity="0.12"/>
  </filter>
</defs>"""


def circuito():
    pid = "c1-"
    s = []
    y0 = 196
    paso = 96

    cajas = {}
    y = y0
    # --- Etapa preparatoria
    cajas[1] = caja(1, y, 1, "Necesidad de compra", ["La detecta un servicio o área del hospital"], EXT); y += paso
    cajas[2] = caja(1, y, 2, "Solicitud del servicio", ["Pedido: qué, cuánto, para cuándo"], EXT); y += paso
    cajas[3] = caja(1, y, 3, "Documentación técnica y administrativa",
                    ["Especificaciones · artículo del catálogo", "(si falta: alta CAByS, Res. SCyGB 292/26)"], EXT); y += paso + 12
    cajas[4] = caja(2, y, 4, "Inicio del expediente electrónico",
                    ["Sin N° de expediente no se puede", "iniciar TIMBÓ Compras (Circ. UG 7/26, pto 11)"], EXP); y += paso + 12
    cajas[5] = caja(2, y, 5, "Verificación presupuestaria y autorizaciones",
                    ["Imputación previa y autorización del gasto", "Quién lo hace en el hospital: A RELEVAR"], EXP)
    cajas["5b"] = caja(1, y, None, "Área presupuestaria / administrativa",
                       ["¿Quién interviene? A RELEVAR"], EXT, punteada=True)
    y += paso + 18
    # decisión (rombo)
    ydec = y
    y += 150
    # bifurcación
    yb = y
    bw, gap = 292, 24
    xs = [160 + bw / 2 + i * (bw + gap) for i in range(4)]
    ramas = [
        caja(0, yb, None, "A · Directa por monto u otra causal",
             ["Hasta $5.850.000, o causal del art. 116 c", "(especialización, exclusividad, etc.)",
              "→ Gestión directa por EXPEDIENTE", "(Circ. UG 2/2025) · sigue en ⑱"], EXP, ancho=bw, cx=xs[0], h=118),
        caja(0, yb, None, "B · Directa por urgencia o desierto",
             ["Art. 116 c, ap. 2 y 3", "→ TIMBÓ COMPRAS, con flexibilizaciones:", "mínimo 3 proveedores invitados",
              "(Circ. UG 8/2026)"], COM, ancho=bw, cx=xs[1], h=118),
        caja(0, yb, None, "C · Licitación o concurso",
             ["Público o privado, de simple sobre", "→ TIMBÓ COMPRAS, camino completo", "obligatorio en Salud desde 1/4/2026",
              "(Circ. UG 1 y 3/2026)"], COM, ancho=bw, cx=xs[2], h=118, etiqueta="CAMINO DE ABAJO"),
        caja(0, yb, None, "D · Etapa múltiple",
             ["Por EXPEDIENTE + Documentos Oficiales", "ofertas en sobres de papel", "hasta que el módulo lo incorpore",
              "(Circ. UG 8/2026, título II)"], EXP, ancho=bw, cx=xs[3], h=118),
    ]
    y = yb + 118 + 56
    # --- Selección en TIMBÓ Compras
    ysel = y - 28
    cajas[7] = caja(3, y, 7, "Inicio del proceso en TIMBÓ Compras", ["Gestor: genera la instancia de contratación"], COM); y += paso
    cajas[8] = caja(3, y, 8, "Pliego particular (PBCP)",
                    ["Gestor: completa los formularios", "incluye al menos 3 evaluadores (pto 13)"], COM); y += paso + 12
    cajas[9] = caja(3, y, 9, "Revisión y aprobación del pliego",
                    ["Supervisor: aprueba o rechaza formularios", "Jurisdicción comitente: revisa el PBCP"], COM)
    cajas["9u"] = caja(1, y, None, "Control de pliegos de la URC",
                       ["Adm. Central (Res. ME 73/26; Circ. SCyGB 03/26)", "¿Aplica al hospital? A CONFIRMAR"], EXT,
                       punteada=True, etiqueta="SI APLICA")
    y += paso + 12
    cajas["acto1"] = caja(2, y, None, "Acto: aprueba el pliego y autoriza el llamado",
                          ["Lo firma la autoridad competente según monto", "El Supervisor lo carga en TIMBÓ Compras"], EXP,
                          etiqueta="ACTO")
    y += paso + 12
    cajas[10] = caja(3, y, 10, "Publicación del procedimiento",
                     ["Proceso publicado + invitaciones por mail", "a la nómina de proveedores (pto 15 y 16)"], COM)
    cajas["10p"] = caja(1, y, None, "Portal web de Compras + aviso oficial",
                        ["Carga en el portal con enlace a TIMBÓ;", "mail a avisosoficiales@ ≥ 3 días antes",
                         "(Circ. SCyGB 04/2026)"], EXT)
    y += paso + 18
    cajas[11] = caja(3, y, 11, "Consultas y circulares",
                     ["Proveedor consulta · Gestor genera circulares"], COM, punteada=True, etiqueta="SI HAY"); y += paso
    cajas[12] = caja(3, y, 12, "Presentación de ofertas",
                     ["Proveedor con ID Ciudadana y RUPC;", "solo vale \"Oferta presentada\" (pto 18)"], COM); y += paso + 12
    cajas[13] = caja(3, y, 13, "Apertura automática",
                     ["A la hora fijada: acta y cuadro", "comparativo automáticos (pto 19)"], COM); y += paso + 12
    cajas[14] = caja(3, y, 14, "Evaluación de ofertas", ["Evaluadores: evalúan y preseleccionan"], COM); y += paso
    cajas[15] = caja(3, y, 15, "Subsanación, aclaración o mejora",
                     ["Subtrámites al proveedor; si no responde", "a tiempo, queda \"descartado\" (pto 21)"], COM,
                     punteada=True, etiqueta="SI CORRESPONDE"); y += paso + 12
    cajas[16] = caja(3, y, 16, "Informe de preadjudicación",
                     ["Firman los evaluadores en el orden", "de \"Ordenar evaluadores\" (pto 22)"], COM)
    cajas["16u"] = caja(1, y, None, "Control de la preadjudicación (URC)",
                        ["Antes del cronograma de impugnación", "¿Aplica al hospital? A CONFIRMAR"], EXT,
                        punteada=True, etiqueta="SI APLICA")
    y += paso + 12
    cajas[17] = caja(3, y, 17, "Impugnaciones",
                     ["A las ofertas o a la preadjudicación,", "con garantía; las recibe el Evaluador"], COM,
                     punteada=True, etiqueta="SI SE PRESENTAN"); y += paso + 30
    # --- Adjudicación y ejecución
    yadj = y - 28
    cajas[18] = caja(2, y, 18, "Adjudicación",
                     ["Acto en el expediente: firma la autoridad", "según monto · el Supervisor lo carga"], EXP,
                     etiqueta="ACTO")
    cajas["18s"] = caja(1, y, None, "SIN + vista al Tribunal de Cuentas",
                        ["\"Gestión de Visualización\" del expediente", "(Circ. UG 9 y 11/2026)"], EXT)
    y += paso + 12
    cajas[19] = caja(2, y, 19, "Etapa contractual", ["Se resuelve por expediente (pto 6)"], EXP); y += paso + 8
    cajas[20] = caja(1, y, 20, "Recepción de bienes o servicios",
                     ["Quién recibe y certifica: A RELEVAR"], EXT); y += paso
    cajas[21] = caja(1, y, 21, "Facturación y pago",
                     ["Según el circuito administrativo", "del hospital: A RELEVAR"], EXT); y += paso
    alto = y + 150

    # fondo y carriles
    s.append(f'<rect width="{W}" height="{alto}" fill="#ffffff"/>')
    ytop = 150
    for k, kind in ((1, EXT), (2, EXP), (3, COM)):
        a, b = CARRIL[k]
        s.append(f'<rect x="{a}" y="{ytop}" width="{b - a}" height="{alto - ytop - 130}" rx="14" fill="{kind["fill"]}" opacity="0.45"/>')
        s.append(f'<rect x="{a}" y="{ytop}" width="{b - a}" height="34" rx="10" fill="{kind["stroke"]}"/>')
        s.append(t((a + b) / 2, ytop + 22, kind["nombre"], 13, 700, "#fff", extra='letter-spacing="0.6"'))
    # etapas (franja izquierda)
    fases = [(ytop + 40, ydec - 24, ["ETAPA", "PREPARATORIA", "por expediente"], EXP["stroke"]),
             (ydec - 14, yb + 132, ["ELECCIÓN", "DEL", "PROCEDIMIENTO"], DEC["stroke"]),
             (ysel, yadj - 10, ["SELECCIÓN", "en TIMBÓ", "Compras"], COM["stroke"]),
             (yadj, alto - 140, ["ADJUDICACIÓN", "Y EJECUCIÓN", "por expediente"], EXP["stroke"])]
    for a, b, lineas, col in fases:
        s.append(f'<rect x="20" y="{a}" width="122" height="{b - a}" rx="10" fill="{col}" opacity="0.10"/>')
        s.append(f'<rect x="20" y="{a}" width="6" height="{b - a}" rx="3" fill="{col}"/>')
        m = (a + b) / 2 - 12
        for i, ln in enumerate(lineas):
            s.append(t(84, m + 17 * i, ln, 12 if i < 2 else 11, 700 if i < 2 else 600, col))
    # banda de bifurcación
    s.append(f'<rect x="152" y="{ydec - 14}" width="{W - 162}" height="{yb + 132 - ydec + 14}" rx="16" fill="#ffffff" '
             f'stroke="{DEC["stroke"]}" stroke-width="1.5" stroke-dasharray="4 4" opacity="0.9"/>')

    # flechas
    def F(a, b, **kw):
        s.append(flecha(cajas[a] if not isinstance(a, dict) else a, cajas[b] if not isinstance(b, dict) else b, pid, **kw))

    F(1, 2); F(2, 3); F(3, 4); F(4, 5)
    F(5, "5b", lado=True, punteada=True)
    # rombo de decisión
    dcx, dcy, dw, dh = CX[2], ydec + 60, 360, 116
    rombo = dict(x=dcx - dw / 2, y=ydec, w=dw, h=dh + 4, cx=dcx)
    F(5, rombo)
    s.append(f'<polygon points="{dcx},{ydec + 2} {dcx + dw / 2},{dcy} {dcx},{dcy + dh / 2 + 2} {dcx - dw / 2},{dcy}" '
             f'fill="{DEC["fill"]}" stroke="{DEC["stroke"]}" stroke-width="2.2" filter="url(#{pid}sombra)"/>')
    s.append(f'<circle cx="{dcx - 150}" cy="{dcy - 34}" r="15" fill="{DEC["stroke"]}" stroke="#fff" stroke-width="2.5"/>')
    s.append(t(dcx - 150, dcy - 29, "6", 13, 700, "#fff"))
    s.append(t(dcx, dcy - 14, "¿Qué procedimiento corresponde?", 14.5, 700, DEC["ink"]))
    s.append(t(dcx, dcy + 5, "Según monto estimado y causal", 12.5, 400, SUB))
    s.append(t(dcx, dcy + 21, "Ley 12.510 art. 116 · Circ. SCyGB 01/2026", 11.5, 600, DEC["ink"]))
    # bus hacia las 4 ramas
    ybus = yb - 26
    s.append(f'<path d="M{dcx},{dcy + dh / 2 + 2} L{dcx},{ybus} M{xs[0]},{ybus} L{xs[3]},{ybus}" stroke="#475569" stroke-width="2.2" fill="none"/>')
    for x in xs:
        s.append(f'<path d="M{x},{ybus} L{x},{yb - 8}" stroke="#475569" stroke-width="2.2" fill="none" marker-end="url(#{pid}punta)"/>')
    for r in ramas:
        s.append(dibujar_caja(r, pid))
    # B y C entran a TIMBÓ Compras
    yin = cajas[7]["y"] - 26
    for r in (ramas[1], ramas[2]):
        s.append(f'<path d="M{r["cx"]},{yb + 118} L{r["cx"]},{yin} L{CX[3]},{yin}" stroke="#475569" stroke-width="2.2" fill="none"/>')
    s.append(f'<path d="M{CX[3]},{yin} L{CX[3]},{cajas[7]["y"] - 8}" stroke="#475569" stroke-width="2.2" fill="none" marker-end="url(#{pid}punta)"/>')

    F(7, 8); F(8, 9)
    F(9, "9u", lado=True, punteada=True, color="#b06f00", texto="pase del expediente")
    F(9, "acto1"); F("acto1", 10)
    F(10, "10p", lado=True)
    F(10, 11); F(11, 12); F(12, 13); F(13, 14); F(14, 15); F(15, 16)
    F(16, "16u", lado=True, punteada=True, color="#b06f00", texto="pase del expediente")
    F(16, 17); F(17, 18)
    F(18, "18s", lado=True)
    F(18, 19); F(19, 20); F(20, 21)

    # incorporación automática de documentos: barra entre expediente y Compras
    ya, yz = cajas[7]["y"], cajas[17]["y"] + cajas[17]["h"]
    xb = 1386
    s.append(f'<rect x="{xb - 7}" y="{ya}" width="14" height="{yz - ya}" rx="7" fill="#ffffff" stroke="{COM["stroke"]}" '
             f'stroke-width="1.5" stroke-dasharray="3 4"/>')
    s.append(f'<text x="{xb + 4}" y="{(ya + yz) / 2}" font-size="10.5" font-weight="700" fill="{COM["ink"]}" text-anchor="middle" '
             f'transform="rotate(-90 {xb + 4} {(ya + yz) / 2})">Todo lo firmado en TIMBÓ Compras se incorpora solo al expediente (Circ. UG 7/2026, pto 7)</text>')

    for k, b in cajas.items():
        s.append(dibujar_caja(b, pid))

    # título
    cab = [t(40, 52, "Circuito de una compra en un hospital público de Santa Fe", 26, 700, TXT, "start"),
           t(40, 80, "Camino completo: licitación o concurso de simple sobre (rama C). Las demás ramas se separan en el paso 6.",
             14, 400, SUB, "start"),
           t(40, 102, "Qué etapa va en cada sistema: Circular UG TIMBÓ 7/2026, punto 6. Versión del 17/11/2026.",
             12.5, 400, SUB, "start")]
    # leyenda
    lx, ly = 40, 118
    ley = []
    items = [(EXP, "Expediente electrónico", False), (COM, "TIMBÓ Compras", False),
             (EXT, "Otras áreas / externos", False), (DEC, "Decisión", False),
             (dict(fill="#fff", stroke="#64748b"), "Punteado: depende del caso o falta confirmar", True)]
    x = lx
    for k, lab, pun in items:
        dash = ' stroke-dasharray="5 4"' if pun else ""
        ley.append(f'<rect x="{x}" y="{ly}" width="26" height="16" rx="4" fill="{k["fill"]}" stroke="{k["stroke"]}" stroke-width="2"{dash}/>')
        ley.append(t(x + 34, ly + 13, lab, 12.5, 600, TXT, "start"))
        x += 44 + 7.2 * len(lab)
    pie_y = alto - 110
    pie = [f'<line x1="40" y1="{pie_y - 14}" x2="{W - 20}" y2="{pie_y - 14}" stroke="#e2e8f0" stroke-width="1.5"/>',
           t(40, pie_y + 6, "Fuentes: Ley 12.510 (art. 116) · Circ. SCyGB 01, 03 y 04/2026 · Res. ME 73/2026 · Circ. UG TIMBÓ 2/2025, 1, 3, 7, 8, 9 y 11/2026 · Res. SCyGB 292/2026.",
             12, 400, SUB, "start"),
           t(40, pie_y + 26, "Los controles de la URC están dirigidos a la Administración Pública Central: confirmar si alcanzan al hospital.",
             12, 400, SUB, "start"),
           t(40, pie_y + 46, "\"A RELEVAR\": la normativa no dice qué área del hospital lo hace; se completa en la reunión. Montos 2026 (Ley de Presupuesto 14.424, art. 36).",
             12, 400, SUB, "start")]

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {alto}" width="{W}" height="{alto}" {FUENTE} '
           f'role="img" aria-label="Circuito de una compra en un hospital público de Santa Fe">\n'
           f'<title>Circuito de una compra en un hospital público de Santa Fe</title>\n'
           + defs(pid) + "\n" + s[0] + "\n" + "\n".join(cab + ley + s[1:] + pie) + "\n</svg>\n")
    return svg


# ---------------------------------------------------------------------------
# Gráfico 2: quién hace qué
# ---------------------------------------------------------------------------

GRUPOS = [
    ("ÁREAS DEL HOSPITAL · a relevar", "#8a5800", "#fff3df",
     ["Área\nsolicitante", "Compras", "Presupuesto /\nAdministración", "Mesa de Ent. /\nDespacho"]),
    ("ROLES EN TIMBÓ COMPRAS · Circ. UG 7/2026, pto 10", "#0b6b4d", "#e2f6ee",
     ["Gestor", "Supervisor", "Evaluadores\n(3 o más)", "Jurisdicción\ncomitente", "Oferente /\nProveedor"]),
    ("AUTORIDAD Y EXTERNOS", "#1d4fae", "#e9f1ff",
     ["Autoridad\ncompetente", "URC\n(SCyGB)", "Otros\nexternos"]),
]
COLS = [c for g in GRUPOS for c in g[3]]
# códigos: H hace · A aprueba/firma · C carga en el sistema · R revisa/controla
#          ? completar en la reunión · minúscula = solo si aplica (a confirmar)
FILAS = [
    ("PREPARATORIA", None),
    ("Detectar la necesidad y hacer el pedido", "? ? ? . . . . . . . . ."),
    ("Especificaciones técnicas / artículo del catálogo", "? ? . . . . . . . . . ."),
    ("Caratular el expediente electrónico ¹", ". . . H . . . . . . . ."),
    ("Imputación y autorización del gasto ²", ". ? ? . . . . . . . . h"),
    ("Elegir el procedimiento según monto y causal", ". ? ? . . . . . . . . ."),
    ("TIMBÓ COMPRAS", None),
    ("Generar la instancia de contratación", ". . . . H . . . . . . ."),
    ("Completar los formularios del pliego (PBCP)", ". ? . . H . . . . . . ."),
    ("Aprobar o rechazar los formularios del PBCP", ". . . . . A . . . . . ."),
    ("Revisar el pliego particular", ". . . . . . . R . . . ."),
    ("Control de pliegos ³", ". . . . . . . . . . r ."),
    ("Cronograma y nómina de proveedores", ". . . . . H . . . . . ."),
    ("Acto que aprueba el pliego y autoriza el llamado", ". . . . . C . . . A . ."),
    ("Publicar en el portal y pedir el aviso oficial ⁴", ". ? . . . . . . . . . H"),
    ("Consultas (proveedor) y circulares (Gestor)", ". . . . H . . . H . . ."),
    ("Presentar ofertas", ". . . . . . . . H . . ."),
    ("Evaluar, pedir subsanación o mejora, preseleccionar", ". . . . . . H . . . . ."),
    ("Informe de preadjudicación (firman en orden)", ". . . . . . A . . . . ."),
    ("Control de la preadjudicación ³", ". . . . . . . . . . r ."),
    ("Cronograma de impugnación; recibir impugnaciones", ". . . . . . H . H . . ."),
    ("ADJUDICACIÓN Y EJECUCIÓN", None),
    ("Acto de adjudicación", ". . . . . C . . . A . ."),
    ("Vista al Tribunal de Cuentas y SIN ⁵", ". . . H . . . . . . . R"),
    ("Recepción de bienes o servicios", "? ? ? . . . . . . . . ."),
    ("Facturación y pago", ". ? ? . . . . . . . . ."),
]
NOTAS = [
    "¹ Permiso de carátula: solo Mesas de Entradas o Despachos (Circ. UG 3/2025, art. 4.c). Quién lo pide en el hospital: a relevar.",
    "² El Ministerio de Economía interviene para la imputación previa y/o autorización del gasto (Res. ME 73/2026, art. 4; Adm. Central).",
    "³ Controles obligatorios de la URC para la Administración Pública Central (Res. ME 73/2026; Circ. SCyGB 03/2026). ¿Alcanzan al hospital? A confirmar.",
    "⁴ Publica la Secretaría de Comunicación a pedido por mail (Circ. SCyGB 04/2026). Quién carga el portal en el hospital: a relevar.",
    "⁵ Administran la visualización las áreas con funciones de Despacho (Circ. UG 9/2026, art. 4). Todo acto va al SIN (Circ. UG 11/2026).",
    "Autoridad competente: según el monto (Circ. SCyGB 01/2026). Un rol del sistema NO da facultades para aprobar ni adjudicar: el Supervisor carga el acto que firma la autoridad.",
]
SIMBOLO = {"H": ("Hace", "#334155"), "A": ("Aprueba / firma", "#7c3aed"), "C": ("Carga en el sistema", "#0e7490"),
           "R": ("Revisa / controla", "#b45309")}


def quien_hace_que():
    pid = "c2-"
    LW, CW, RH = 380, 86, 34
    x0, ytab = 30, 214
    W2 = x0 + LW + CW * len(COLS) + 30
    s = []
    nfil = len(FILAS)
    alto_tabla = sum(26 if f[1] is None else RH for f in FILAS)
    alto = ytab + alto_tabla + 34 + 20 * len(NOTAS) + 36
    s.append(f'<rect width="{W2}" height="{alto}" fill="#ffffff"/>')
    s.append(t(x0, 46, "¿Quién hace qué en una compra por TIMBÓ Compras?", 24, 700, TXT, "start"))
    s.append(t(x0, 72, "Separa los roles del sistema (que da la norma) de las áreas y cargos del hospital (que hay que relevar en la reunión).",
               13.5, 400, SUB, "start"))
    # leyenda
    lx, ly = x0, 92
    for cod, (lab, col) in SIMBOLO.items():
        s.append(f'<circle cx="{lx + 11}" cy="{ly + 11}" r="11" fill="{col}"/>')
        s.append(t(lx + 11, ly + 15.5, cod, 12, 700, "#fff"))
        s.append(t(lx + 28, ly + 16, lab, 12.5, 600, TXT, "start"))
        lx += 44 + 7.4 * len(lab)
    s.append(f'<circle cx="{lx + 11}" cy="{ly + 11}" r="10" fill="#fff" stroke="#b45309" stroke-width="2" stroke-dasharray="3 3"/>')
    s.append(t(lx + 11, ly + 15.5, "r", 12, 700, "#b45309"))
    s.append(t(lx + 28, ly + 16, "Solo si aplica al hospital (a confirmar)", 12.5, 600, TXT, "start"))
    lx += 290
    s.append(f'<rect x="{lx}" y="{ly}" width="22" height="22" rx="6" fill="#fff" stroke="#d48806" stroke-width="1.8" stroke-dasharray="3 3"/>')
    s.append(t(lx + 11, ly + 16, "?", 13, 700, "#d48806"))
    s.append(t(lx + 30, ly + 16, "Preguntar en la reunión", 12.5, 600, TXT, "start"))

    # cabeceras de grupo y de columna
    x = x0 + LW
    for nombre, ink, fondo, cols in GRUPOS:
        w = CW * len(cols)
        s.append(f'<rect x="{x + 2}" y="132" width="{w - 4}" height="24" rx="6" fill="{ink}"/>')
        s.append(t(x + w / 2, 149, nombre, 10.8, 700, "#fff"))
        s.append(f'<rect x="{x + 2}" y="160" width="{w - 4}" height="{ytab - 160 + alto_tabla}" rx="6" fill="{fondo}" opacity="0.55"/>')
        for i, c in enumerate(cols):
            cx = x + CW * i + CW / 2
            partes = c.split("\n")
            for j, p in enumerate(partes):
                s.append(t(cx, 182 + 15 * j + (7 if len(partes) == 1 else 0), p, 12, 700, ink))
        x += w
    s.append(t(x0 + 6, 196, "Tarea o etapa", 13, 700, TXT, "start"))

    y = ytab
    for i, (tarea, cod) in enumerate(FILAS):
        if cod is None:
            s.append(f'<rect x="{x0}" y="{y + 2}" width="{W2 - x0 - 30}" height="22" rx="5" fill="#334155"/>')
            s.append(t(x0 + 10, y + 18, tarea, 11.5, 700, "#fff", "start", 'letter-spacing="1"'))
            y += 26
            continue
        if i % 2 == 0:
            s.append(f'<rect x="{x0}" y="{y}" width="{W2 - x0 - 30}" height="{RH}" fill="#0f172a" opacity="0.035"/>')
        s.append(t(x0 + 10, y + RH / 2 + 5, tarea, 13, 500, TXT, "start"))
        for j, c in enumerate(cod.split()):
            cx = x0 + LW + CW * j + CW / 2
            cy = y + RH / 2
            if c in SIMBOLO:
                s.append(f'<circle cx="{cx}" cy="{cy}" r="12" fill="{SIMBOLO[c][1]}"/>')
                s.append(t(cx, cy + 4.5, c, 12.5, 700, "#fff"))
            elif c in ("h", "r"):
                col = "#b45309"
                s.append(f'<circle cx="{cx}" cy="{cy}" r="11" fill="#fff" stroke="{col}" stroke-width="2" stroke-dasharray="3 3"/>')
                s.append(t(cx, cy + 4.5, c, 12.5, 700, col))
            elif c == "?":
                s.append(f'<rect x="{cx - 12}" y="{cy - 12}" width="24" height="24" rx="6" fill="#fff" stroke="#d48806" stroke-width="1.8" stroke-dasharray="3 3"/>')
                s.append(t(cx, cy + 5, "?", 14, 700, "#d48806"))
        y += RH
    # separadores verticales de grupos
    x = x0 + LW
    for g in GRUPOS[:-1]:
        x += CW * len(g[3])
        s.append(f'<line x1="{x}" y1="132" x2="{x}" y2="{y}" stroke="#94a3b8" stroke-width="1.5"/>')
    y += 34
    for n in NOTAS:
        s.append(t(x0, y, n, 12, 400, SUB, "start"))
        y += 20
    s.append(t(x0, y + 10, "Fuentes: Circ. UG TIMBÓ 3/2025, 7, 9 y 11/2026 · Circ. SCyGB 01, 03 y 04/2026 · Res. ME 73/2026. Versión del 17/11/2026.",
               12, 600, SUB, "start"))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W2} {alto}" width="{W2}" height="{alto}" {FUENTE} '
           f'role="img" aria-label="Quién hace qué en una compra por TIMBÓ Compras">\n'
           f'<title>Quién hace qué en una compra por TIMBÓ Compras</title>\n' + defs(pid) + "\n" + "\n".join(s) + "\n</svg>\n")
    return svg


if __name__ == "__main__":
    (SALIDA / "circuito_compra.svg").write_text(circuito(), encoding="utf-8")
    (SALIDA / "quien_hace_que.svg").write_text(quien_hace_que(), encoding="utf-8")
    print("SVG generados en", SALIDA)
