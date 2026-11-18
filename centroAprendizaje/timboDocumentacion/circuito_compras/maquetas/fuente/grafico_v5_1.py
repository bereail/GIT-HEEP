"""Gráfico didáctico del circuito de compras, armado SOLO con la matriz v5.1.

    python fuente/grafico_v5_1.py
Salida: circuito_v5_1.svg y circuito_v5_1.html (gráfico + leyenda + fichas D1-D20).

El contenido sale de matriz_v5_1.py (ESQUEMA, MATRIZ, ETAPA_MULTIPLE, REGLA_20,
CONSULTA_D7). Al final, verificar() compara el gráfico con la matriz: cada par
(estado, discrepancia) del esquema tiene que aparecer en el gráfico, y ningún
estado del gráfico puede contradecir el de la matriz.
"""
import re
from html import escape as h
from pathlib import Path
from xml.sax.saxutils import escape

import matriz_v5_1 as M

AQUI = Path(__file__).resolve().parent.parent
V, DOC, P, O = "VERIFICADO", "DOCUMENTADO", "PENDIENTE", "OBSERVADO"
COLOR = {V: ("#1b7a45", "#e9f6ee"), DOC: ("#2456c7", "#eaf0fd"), P: ("#b45309", "#fff6ea"), O: ("#b42318", "#fdeeee")}
PESO = {V: 0, DOC: 1, P: 2, O: 3}
TXT, SUB, LINEA, NAVY, VIOLETA, VIOLETA_F = "#1f2937", "#5b6472", "#d9dee7", "#14284b", "#5b3fc4", "#f3f0ff"
FUENTE = 'font-family="Segoe UI, system-ui, Arial, sans-serif"'


# --------------------------------------------------------------- modelo
def e(tipo, titulo, estados=(), detalle=None, quien=None, fin=None, formularios=None, salida=None):
    """Un elemento del gráfico. estados: lista de (ESTADO, texto corto, [D…])."""
    return {"tipo": tipo, "titulo": titulo, "estados": [(s, t, list(d)) for s, t, d in estados],
            "detalle": detalle or [], "quien": quien, "fin": fin, "formularios": formularios, "salida": salida}


ESPINA = [
    e("inicio", "Inicio · nace la necesidad", [(P, "quién: a relevar", [])]),
    e("proceso", "Expediente electrónico (etapa preparatoria)", [(V, "UG 7 ptos 6 y 11 · Dec. 2518/25", [])]),
    e("proceso", "Monto estimado: total con prórrogas", [(V, "Dec. 1104 art. 116.1", ["D15"])]),
]
DEC1 = e("decision", "¿Hay una causal de contratación directa?", [(V, "Ley 116 c", [])])
RAMAS1 = [
    ("Urgencia o desierto", e("rama", "B · Urgencia o desierto", [(P, "recorrido en TIMBÓ Compras", ["D1"])], detalle=[
        e("control", "Intervención previa de la SCyGB si supera $29.250.000", [(V, "Dec. 652/2020", ["D16"])]),
        e("proceso", "Urgencia: ≥3 cotizaciones · desierto: mismas condiciones", [(V, "Dec. 1104 art. 116 c · UG 8 art. 4", [])]),
    ], fin=("pendiente", "Cómo sigue en TIMBÓ Compras: pendiente (D1)"))),
    ("Otra causal (ap. 4 a 8)", e("rama", "A2 · Otra causal · por expediente", [(V, "causales y trámite digital · Ley 116 c · UG 2/2025", [])], detalle=[
        e("control", "Intervención de la SCyGB en ap. 4, 5 y 8", [(P, "Disp. 282/16 sin leer", ["D17"])]),
    ], fin=("sigue", "continúa en: Contrato"))),
]
DEC2 = e("decision", "¿Es una modalidad especial? (rama E)", [])
RAMAS2 = [
    ("Alquiler de inmueble", e("rama", "E · Concurso de precios para locación (≤ $29.250.000)", [(V, "tope", []), (P, "régimen", ["D18"])])),
    ("Etapa múltiple", e("rama", "D · Etapa múltiple: la selecciona la Unidad Rectora", [(V, "Dec. 287/2026 art. 123", ["D2"])], detalle=[
        e("proceso", "Expediente + Documentos Oficiales", [(V, "UG 8 arts. 5-6", [])]),
        e("proceso", "Ofertas en sobres de papel (régimen transitorio)", [(V, "UG 8 art. 7", []), (P, "compatibilidad con el Dec. 2518/25", [])]),
    ], fin=("sigue", "continúa en: Adjudicación"))),
    ("Convenio Marco", e("rama", "E · Convenio Marco", [(P, "normas sin leer", ["D18"])])),
    ("Subasta", e("rama", "E · Subasta (autoriza el Poder Ejecutivo)", [(V, "Ley 116 b", [])], fin=("sigue", "continúa en: Contrato"))),
]
DEC3 = e("decision", "¿Cuánto es el monto? (montos 2026)", [(V, "Circ. SCyGB 01/2026 · Dec. 2233 art. 1", [])])
RAMA_A = e("rama", "A · Directa por monto (hasta $5.850.000)", [], detalle=[
    e("bloque", "Secuencia de formularios", [(V, "Dec. 1247/08 Anexo I", ["D3"])],
      formularios=["CD-01", "CD-02 (según el monto)", "CD-03", "CD-04"], salida="Rechazo: CD-05"),
    e("bloque", "Actores y autorizaciones (no confirmados)", [], detalle=[
        e("responsable", "Quién autoriza y quién adjudica", [(O, "fuentes de distinta fecha", ["D8"])]),
        e("control", "Comunicación al Tribunal de Cuentas", [(O, "fuentes de distinta fecha", ["D9"])]),
        e("proceso", "Soporte (papel / digital) y presupuestos", [(O, "", ["D10"]), (DOC, "video oficial", [])]),
    ]),
], fin=("sigue", "continúa en: Recepción y pago"))
C_PRIV = e("rama", "C · Privado (hasta $58.500.000)", [], detalle=[
    e("proceso", "≥5 invitaciones fehacientes, 5 días corridos", [(V, "Dec. 1104 art. 121.1", [])]),
    e("proceso", "¿Cuentan las invitaciones de TIMBÓ?", [(P, "", ["D6"])]),
])
C_PUB = e("rama", "C · Público (más de $58.500.000)", [], detalle=[
    e("proceso", "Boletín Oficial 2 días", [(V, "Dec. 1104 art. 132.3 · Circ. 04/2026", [])]),
    e("proceso", "Cantidad de diarios (uno o dos)", [(O, "", ["D4"])]),
    e("proceso", "10 días corridos (20 si es internacional)", [(V, "Dec. 1104 art. 132.3", [])]),
])
TRONCO = [
    (e("proceso", "Pliego", [(V, "UG 7 pto 10", [])], quien="Gestor · rol TIMBÓ"), None),
    (e("control", "Revisión de la Jurisdicción comitente", [(V, "rol", []), (P, "orden", ["D13"])], quien="Jurisdicción comitente · rol TIMBÓ"), None),
    (e("decision", "¿El Supervisor aprueba los formularios?", [(V, "UG 7 pto 10", [])], quien="Supervisor · rol TIMBÓ"),
     ("No", e("excepcion", "Rechazado: ¿qué sigue?", [(P, "", ["D12"])]))),
    (e("control", "Control de pliegos de la URC: «si aplica»", [(P, "alcance en hospitales", ["D5"])]), None),
    (e("proceso", "Cronograma y nómina", [(V, "rol", []), (P, "orden respecto de la URC", ["D13"])], quien="Supervisor · rol TIMBÓ"), None),
    (e("proceso", "Acto que aprueba el pliego y autoriza el llamado", [(O, "Dec. 2233 art. 2 y Circ. 01/2026; sin tramos trasladados", ["D7"])], quien="Firma: OBSERVADO (D7)"), None),
    (e("proceso", "SIN y Tribunal de Cuentas del acto", [(V, "UG 11 art. 1", [])]), None),
    (e("proceso", "Publicación (privado / público) → Consultas y circulares", [(V, "", [])]), None),
    (e("proceso", "Ofertas → Apertura automática", [(V, "UG 7 ptos 18-19", [])]), None),
    (e("decision", "¿Impugnan ofertas? (2 días hábiles)", [(V, "Pliego 4.3", [])]),
     ("Sí", e("excepcion", "Impugnación de ofertas", [(V, "Pliego 4.3", [])]))),
    (e("proceso", "Evaluación", [(V, "UG 7 pto 21 · Pliego 5.3 · Dec. 1104 art. 133.1", [])], detalle=[
        e("decision", "¿Subsanar?", [(V, "", [])]),
        e("excepcion", "Empate → mejora (≤5 %) / sorteo", [(V, "", [])]),
        e("excepcion", "Desierto → B", [(V, "paso", []), (P, "", ["D19", "D1"])]),
    ]), None),
    (e("proceso", "Preadjudicación", [(V, "UG 7 pto 22 · Pliego 5.1", [])]), None),
    (e("control", "Control de la preadjudicación de la URC: «si aplica»", [(P, "", ["D5"])]), None),
    (e("decision", "¿Impugnan la preadjudicación? (2 días, garantía 3 %)", [(V, "Pliego 5.1 y 10.1.3", [])]),
     ("Sí", e("excepcion", "Impugnación de la preadjudicación", [(V, "Pliego 5.1", [])]))),
    (e("proceso", "Adjudicación", [], detalle=[
        e("responsable", "Firma según monto", [(V, "texto Dec. 2233 art. 3", []), (P, "equivalente en el hospital", [])]),
        e("proceso", "Notificación ≤10 días hábiles", [(V, "Pliego 5.4", [])]),
        e("proceso", "SIN y Tribunal de Cuentas", [(V, "UG 11 art. 1", [])]),
        e("proceso", "Publicar en Internet", [(V, "público · Ley 132; Dec. 1104 art. 132.4", []), (P, "privado", ["D11"])]),
        e("proceso", "Vale si la adjudicación supera hasta 20 % el máximo", [(V, "Dec. 1104 art. 116.1", ["D15"])]),
    ]), None),
    (e("proceso", "Contrato: orden de compra (10 días corridos) · garantía de fiel cumplimiento (5 días)", [(V, "Pliego 5.6", [])]),
     ("No cumple", e("excepcion", "Se deja sin efecto → siguiente en el orden de mérito", [(V, "Pliego 5.6", [])]))),
    (e("proceso", "Recepción provisoria → definitiva y certificado → factura → pago", [(V, "reglas", []), (P, "sistema y soporte", [])]), None),
]
FUERA = e("excepcion", "Revocación del llamado, en cualquier momento antes del contrato", [(V, "Pliego 5.5", []), (P, "¿es el «sin efecto» del Supervisor?", ["D20"])])


def todos():
    """Todos los elementos (recursivo), para verificar."""
    pila = ESPINA + [DEC1, DEC2, DEC3, RAMA_A, C_PRIV, C_PUB, FUERA] + [r for _, r in RAMAS1 + RAMAS2]
    for t, lado in TRONCO:
        pila.append(t)
        if lado:
            pila.append(lado[1])
    out = []
    while pila:
        x = pila.pop()
        out.append(x)
        pila.extend(x["detalle"])
    return out


# --------------------------------------------------------------- dibujo
def t(x, y, s, size=14, weight=400, color=TXT, anchor="start", extra=""):
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color}" '
            f'text-anchor="{anchor}" {extra}>{escape(s)}</text>')


def ancho_txt(s, size):
    return len(s) * size * 0.56


def ancho_pill(s, size):
    return len(s) * size * 0.64


def envolver(s, max_chars):
    pal, out, act = s.split(), [], ""
    for p in pal:
        if len(act) + len(p) + 1 > max_chars and act:
            out.append(act)
            act = p
        else:
            act = (act + " " + p).strip()
    out.append(act)
    return out


def pill(x, y, estado, texto, ds, size=11.5):
    col, fondo = COLOR[estado]
    etiqueta = estado + (f" {'·'.join(ds)}" if ds else "") + (f" · {texto}" if texto else "")
    w = ancho_pill(etiqueta, size) + 18
    dash = ' stroke-dasharray="4 3"' if estado == P else ""
    extra = ""
    if estado == O:
        extra = f'<rect x="{x + 2.5}" y="{y + 2.5}" width="{w - 5}" height="17" rx="8.5" fill="none" stroke="{col}" stroke-width="0.8"/>'
    out = (f'<rect x="{x}" y="{y}" width="{w}" height="22" rx="11" fill="{fondo}" stroke="{col}" stroke-width="1.4"{dash}/>' + extra
           + t(x + 9, y + 15.5, etiqueta, size, 700, col))
    if ds:
        out = f'<a href="#{ds[0].lower()}">' + out + "</a>"
    return out, w


def pills(x, y, estados, ancho_max):
    out, cx, cy = [], x, y
    for s, tx, ds in estados:
        code, w = pill(cx, cy, s, tx, ds)
        if w > ancho_max and tx:
            if cx > x:
                cx, cy = x, cy + 26
            code, w = pill(cx, cy, s, "", ds)
            out.append(code)
            out.append(t(x + 4, cy + 40, tx, 11.5, 600, COLOR[s][0]))
            cx, cy = x, cy + 46
            continue
        if cx + w > x + ancho_max and cx > x:
            cx, cy = x, cy + 26
            code, w = pill(cx, cy, s, tx, ds)
        out.append(code)
        cx += w + 6
    return out, (cy - y + 26) if estados else 0


def peor(estados):
    return max((s for s, _, _ in estados), key=lambda s: PESO[s], default=None)


def icono(tipo):
    return {"control": "🔍", "excepcion": "↯", "responsable": "👤", "inicio": "●", "bloque": "▤"}.get(tipo, "")


def caja(x, y, w, el, compacta=False):
    """Bloque genérico; devuelve (svg, alto)."""
    tipo = el["tipo"]
    out = []
    lineas = envolver((icono(tipo) + " " if icono(tipo) else "") + el["titulo"], int(w / (7.6 if not compacta else 7.0)))
    size = 15 if not compacta else 13.5
    alto_tit = 22 * len(lineas)
    cuerpo = []
    cy = y + 14 + alto_tit
    if el["quien"]:
        cuerpo.append(t(x + 16, cy + 12, "👤 " + el["quien"], 12, 600, "#0b5f61"))
        cy += 20
    if el["estados"]:
        p, a = pills(x + 14, cy, el["estados"], w - 28)
        cuerpo += p
        cy += a + 4
    if el["formularios"]:
        fx = x + 14
        for i, f in enumerate(el["formularios"]):
            fw = ancho_txt(f, 12) + 26
            cuerpo.append(f'<path d="M{fx},{cy} h{fw - 9} l9,9 v19 h-{fw} z" fill="#fff" stroke="{NAVY}" stroke-width="1.3"/>'
                          + t(fx + 8, cy + 18, f, 12, 700, NAVY))
            fx += fw
            if i < len(el["formularios"]) - 1:
                cuerpo.append(t(fx + 4, cy + 18, "→", 13, 700, SUB))
                fx += 20
        cy += 34
        if el["salida"]:
            cuerpo.append(t(x + 16, cy + 6, "↳ " + el["salida"], 12, 700, "#7a2d2d"))
            cy += 16
    for sub in el["detalle"]:
        s2, a2 = caja(x + 14, cy, w - 28, sub, compacta=True)
        cuerpo.append(s2)
        cy += a2 + 8
    if el["fin"]:
        clase, texto = el["fin"]
        col = COLOR[P][0] if clase == "pendiente" else NAVY
        fw = ancho_txt(texto, 12.5) + 24
        cuerpo.append(f'<rect x="{x + 14}" y="{cy}" width="{fw}" height="24" rx="12" fill="#fff" stroke="{col}" stroke-width="1.5"'
                      f'{" stroke-dasharray=\"5 3\"" if clase == "pendiente" else ""}/>' + t(x + 26, cy + 16.5, "► " + texto, 12.5, 700, col))
        cy += 30
    alto = cy - y + 10
    # forma según el tipo
    estado = peor(el["estados"]) or peor([s for d in el["detalle"] for s in d["estados"]])
    franja = COLOR[estado][0] if estado else LINEA
    if tipo == "control":
        out.append(f'<path d="M{x + 12},{y} h{w - 24} l12,12 v{alto - 24} l-12,12 h-{w - 24} l-12,-12 v-{alto - 24} z" fill="#fbfcfd" stroke="#7d8796" stroke-width="1.6"/>')
    elif tipo == "excepcion":
        out.append(f'<path d="M{x},{y} h{w - 16} l16,16 v{alto - 16} h-{w} z" fill="#fffaf5" stroke="#9a6a1c" stroke-width="1.6" stroke-dasharray="7 3"/>')
    elif tipo == "rama":
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{alto}" rx="14" fill="#ffffff" stroke="{VIOLETA}" stroke-width="2"/>')
    elif tipo == "bloque":
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{alto}" rx="10" fill="#f8fafc" stroke="{LINEA}" stroke-width="1.4"/>')
    elif tipo == "responsable":
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{alto}" rx="{min(20, alto / 2)}" fill="#f2fbfb" stroke="#0b5f61" stroke-width="1.4"/>')
    elif tipo == "decision" and compacta:
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{alto}" rx="8" fill="{VIOLETA_F}" stroke="{VIOLETA}" stroke-width="1.4"/>')
        lineas = ["◆ " + el["titulo"]]
    else:
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{alto}" rx="12" fill="#ffffff" stroke="{LINEA}" stroke-width="1.6"/>')
    if tipo not in ("decision", "rama", "bloque") or not compacta:
        out.append(f'<rect x="{x}" y="{y + 6}" width="6" height="{alto - 12}" rx="3" fill="{franja}"/>')
    for i, l in enumerate(lineas):
        out.append(t(x + 16, y + 26 + i * 22, l, size, 700, VIOLETA if tipo == "rama" else TXT))
    return "\n".join(out + cuerpo), alto


def rombo(cx, y, el, w=520):
    lineas = envolver("◆ " + el["titulo"], 40)
    extra = (26 if el["estados"] else 0) + (20 if el.get("quien") else 0)
    alto = 76 + 20 * len(lineas) + extra
    out = [f'<polygon points="{cx},{y} {cx + w / 2},{y + alto / 2} {cx},{y + alto} {cx - w / 2},{y + alto / 2}" fill="{VIOLETA_F}" stroke="{VIOLETA}" stroke-width="2.2"/>']
    yy = y + alto / 2 - (len(lineas) * 20 + extra) / 2 + 16
    for l in lineas:
        out.append(t(cx, yy, l, 15, 700, TXT, "middle"))
        yy += 20
    if el.get("quien"):
        out.append(t(cx, yy, "👤 " + el["quien"], 12, 600, "#0b5f61", "middle"))
        yy += 20
    if el["estados"]:
        p, _ = pills(cx - 130, yy - 8, el["estados"], 300)
        out += p
    return "\n".join(out), alto


def flecha(x1, y1, x2, y2, etiqueta=None, color="#64748b"):
    s = f'<path d="M{x1},{y1} L{x2},{y2}" stroke="{color}" stroke-width="2.2" fill="none" marker-end="url(#pta)"/>'
    if etiqueta:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        w = ancho_txt(etiqueta, 12) + 16
        s += f'<rect x="{mx - w / 2}" y="{my - 12}" width="{w}" height="22" rx="11" fill="#fff" stroke="{VIOLETA}" stroke-width="1.2"/>' + t(mx, my + 3.5, etiqueta, 12, 700, VIOLETA, "middle")
    return s


def svg_circuito():
    W = 1720
    CX, SW = 440, 560            # espina: centro y ancho
    SX = CX - SW / 2
    RX, RW = 860, 820            # columna lateral
    out, y = [], 150
    # encabezado y leyenda
    out.append(t(40, 52, "Circuito de compras · material de capacitación interna", 28, 700, TXT))
    out.append(t(40, 80, "Basado solo en la matriz v5.1 (18/11/2026). No es una interpretación normativa nueva: lo PENDIENTE y lo OBSERVADO se muestra como tal.", 14, 400, SUB))
    lx = 40
    for s in (V, DOC, P, O):
        code, w = pill(lx, 96, s, "", [])
        out.append(code)
        lx += w + 10
    out.append(t(lx + 6, 112, "La franja de color de cada bloque muestra su estado más restrictivo.", 12.5, 400, SUB))
    lx = 40
    for txt in ("◆ decisión", "▭ proceso", "⬡ 🔍 control", "↯ excepción", "👤 responsable", "▱ formulario", "► continúa en", "D1–D20: tocá para ver la ficha"):
        out.append(t(lx, 136, txt, 12.5, 600, SUB))
        lx += ancho_txt(txt, 12.5) + 26

    def espina(el):
        nonlocal y
        if el["tipo"] == "decision":
            code, alto = rombo(CX, y, el)
        else:
            code, alto = caja(SX, y, SW, el)
        out.append(code)
        top = y
        y += alto
        return top, alto

    for el in ESPINA:
        espina(el)
        out.append(flecha(CX, y, CX, y + 40))
        y += 40

    def decision_con_ramas(dec, ramas):
        nonlocal y
        top, alto = espina(dec)
        # ramas apiladas en la columna lateral, a partir de la altura del rombo
        ry = top
        cy_r = top + alto / 2
        for i, (etq, rama) in enumerate(ramas):
            code, a = caja(RX, ry, RW, rama)
            out.append(code)
            ymid = ry + 24
            if i == 0:
                out.append(flecha(CX + 260, cy_r, RX - 6, ymid, etq))
            else:
                out.append(f'<path d="M{RX - 40},{cy_r} L{RX - 40},{ymid} L{RX - 6},{ymid}" stroke="#64748b" stroke-width="2.2" fill="none" marker-end="url(#pta)"/>')
                w = ancho_txt(etq, 12) + 16
                out.append(f'<rect x="{RX - 40 - w - 6}" y="{ymid - 12}" width="{w}" height="22" rx="11" fill="#fff" stroke="{VIOLETA}" stroke-width="1.2"/>' + t(RX - 46 - w / 2, ymid + 3.5, etq, 12, 700, VIOLETA, "middle"))
            ry += a + 18
        if len(ramas) > 1:
            out.append(f'<path d="M{CX + 260},{cy_r} L{RX - 40},{cy_r}" stroke="#64748b" stroke-width="2.2" fill="none"/>')
        y = max(y, ry - 18)
        out.append(flecha(CX, top + alto, CX, y + 40, "No"))
        y += 40

    decision_con_ramas(DEC1, RAMAS1)
    decision_con_ramas(DEC2, RAMAS2)
    # decisión 3: A a la derecha, C privado y público debajo
    top, alto = espina(DEC3)
    code, a = caja(RX, top, RW, RAMA_A)
    out.append(code)
    out.append(flecha(CX + 260, top + alto / 2, RX - 6, top + 24, "Hasta $5.850.000"))
    yA = top + a
    y = top + alto + 70
    cw = (SW + 160 - 20) / 2
    x1, x2 = SX - 80, SX - 80 + cw + 20
    c1, a1 = caja(x1, y, cw, C_PRIV)
    c2, a2 = caja(x2, y, cw, C_PUB)
    out.append(f'<path d="M{CX},{top + alto} L{CX},{y - 30} M{x1 + cw / 2},{y - 30} L{x2 + cw / 2},{y - 30}" stroke="#64748b" stroke-width="2.2" fill="none"/>')
    out.append(flecha(x1 + cw / 2, y - 30, x1 + cw / 2, y - 4))
    out.append(flecha(x2 + cw / 2, y - 30, x2 + cw / 2, y - 4))
    out.append(t(x1 + cw / 2 - 8, y - 38, "Hasta $58.500.000", 12, 700, VIOLETA, "end"))
    out.append(t(x2 + cw / 2 + 8, y - 38, "Más de $58.500.000", 12, 700, VIOLETA))
    out += [c1, c2]
    yb = y + max(a1, a2)
    out.append(f'<path d="M{x1 + cw / 2},{yb} L{x1 + cw / 2},{yb + 22} L{x2 + cw / 2},{yb + 22} L{x2 + cw / 2},{yb} M{CX},{yb + 22} L{CX},{yb + 52}" stroke="#64748b" stroke-width="2.2" fill="none" marker-end="url(#pta)"/>')
    w = ancho_txt("privado y público comparten el tronco de TIMBÓ Compras", 12) + 16
    out.append(f'<rect x="{CX + 14}" y="{yb + 26}" width="{w}" height="22" rx="11" fill="#fff" stroke="{LINEA}"/>' + t(CX + 22, yb + 41, "privado y público comparten el tronco de TIMBÓ Compras", 12, 600, SUB))
    y = max(yb + 58, yA + 20)
    # tronco
    out.append(f'<rect x="{SX - 30}" y="{y - 6}" width="{SW + 60}" height="30" rx="8" fill="{NAVY}"/>' + t(CX, y + 14, "TRONCO DE TIMBÓ COMPRAS", 14, 700, "#fff", "middle", 'letter-spacing="1"'))
    y += 44
    for i, (el, lado) in enumerate(TRONCO):
        top, alto = espina(el)
        if lado:
            etq, ex = lado
            code, a = caja(RX, top + max(0, alto / 2 - 30), min(RW, 520), ex)
            out.append(code)
            out.append(flecha((CX + 260) if el["tipo"] == "decision" else SX + SW, top + alto / 2, RX - 6, top + max(0, alto / 2 - 30) + 24, etq))
            y = max(y, top + max(0, alto / 2 - 30) + a)
        if i < len(TRONCO) - 1:
            out.append(flecha(CX, top + alto, CX, y + 36))
            y += 36
    out.append(flecha(CX, y, CX, y + 36))
    y += 36
    out.append(f'<rect x="{CX - 110}" y="{y}" width="220" height="44" rx="12" fill="{NAVY}"/>' + t(CX, y + 28, "■ FIN", 17, 700, "#fff", "middle"))
    y += 70
    code, a = caja(RX, y - 70, min(RW, 640), FUERA)
    out.append(t(RX, y - 82, "Fuera de la línea:", 13, 700, SUB))
    out.append(code)
    y += a
    out.append(t(40, y + 20, "D14 (sincronización del mapa público) y el detalle de cada discrepancia están en las fichas complementarias.", 13, 500, SUB))
    alto_total = y + 50
    defs = '<defs><marker id="pta" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#64748b"/></marker></defs>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W} {alto_total}" width="{W}" height="{alto_total}" {FUENTE}>'
            f'<title>Circuito de compras · matriz v5.1</title>{defs}<rect width="{W}" height="{alto_total}" fill="#ffffff"/>' + "\n".join(out) + "</svg>")


# -------------------------------------------------------------- verificación
def pares_esquema():
    pares = set()
    for bracket in re.findall(r"\[([^\]]+)\]", M.ESQUEMA):
        estado = None
        for parte in re.split(r"·", bracket):
            m = re.search(r"\b(VERIFICADO|DOCUMENTADO|PENDIENTE|OBSERVADO)\b", parte)
            if m:
                estado = m.group(1)
            for a, b in re.findall(r"D(\d+)(?:-D?(\d+))?", parte):
                rango = range(int(a), int(b) + 1) if b else [int(a)]
                for n in rango:
                    if estado:
                        pares.add((estado, f"D{n}"))
    return pares


def pares_grafico():
    return {(s, d) for el in todos() for s, _, ds in el["estados"] for d in ds}


def verificar():
    matriz = {f[0]: {w for w in (V, DOC, P, O) if w in f[5]} for f in M.MATRIZ}
    grafico, esquema = pares_grafico(), pares_esquema()
    faltan = esquema - grafico
    contradicen = {(s, d) for s, d in grafico if s not in matriz.get(d, set())}
    usadas = {d for _, d in grafico}
    sin_ficha = usadas - set(matriz)
    assert not faltan, f"Pares del esquema v5.1 que faltan en el gráfico: {sorted(faltan)}"
    assert not contradicen, f"Estados del gráfico que contradicen la matriz: {sorted(contradicen)}"
    assert not sin_ficha, f"Referencias sin ficha: {sin_ficha}"
    assert len(M.MATRIZ) == 20
    for rama in ("A ·", "A2 ·", "B ·", "C · Privado", "C · Público", "D ·", "E ·"):
        assert any(el["titulo"].startswith(rama) for el in todos()), f"Falta la rama {rama}"
    en_grafico = sorted(usadas, key=lambda d: int(d[1:]))
    solo_fichas = [f"D{i}" for i in range(1, 21) if f"D{i}" not in usadas]
    return en_grafico, solo_fichas, len(esquema)


# ------------------------------------------------------------------- HTML
def fichas():
    out = []
    for d, tema, fuentes, tipo, impacto, estado, quien, pregunta, decision in M.MATRIZ:
        colores = [s for s in (O, P, DOC, V) if s in estado]
        col = COLOR[colores[0]][0] if colores else SUB
        out.append(f"""<article class="ficha" id="{d.lower()}" style="border-left-color:{col}">
<h3><span class="id">{h(d)}</span> {h(tema)}</h3>
<p class="estado" style="color:{col}">{h(estado)}</p>
<dl><dt>Fuentes</dt><dd>{h(fuentes)}</dd><dt>Tipo</dt><dd>{h(tipo)}</dd><dt>En el gráfico</dt><dd>{h(impacto)}</dd>
<dt>Consultar a</dt><dd>{h(quien)}</dd><dt>Pregunta</dt><dd>{h(pregunta)}</dd><dt>Decisión de la usuaria</dt><dd>{h(decision)}</dd></dl></article>""")
    return "".join(out)


def html(svg, en_grafico, solo_fichas, n_pares):
    etapa = "".join(f"<tr><td>{h(a)}</td><td>{h(b)}</td></tr>" for a, b in M.ETAPA_MULTIPLE)
    regla = "".join(f"<tr><td>{h(a)}</td><td>{h(b)}</td><td>{h(c)}</td><td>{h(d)}</td></tr>" for a, b, c, d in M.REGLA_20)
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Circuito de compras · capacitación (v5.1)</title>
<style>
body{{margin:0;background:#f4f6f9;color:#1f2937;font:15px/1.5 "Segoe UI",system-ui,Arial,sans-serif}}
main{{max-width:1760px;margin:0 auto;padding:20px 16px 60px}}
section{{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:18px 20px;margin-top:16px}}
h1{{margin:0;font-size:24px}} h2{{margin:0 0 10px;font-size:20px}}
.fig{{overflow:auto;border:1px solid #e2e8f0;border-radius:12px}} .fig svg{{display:block;width:100%;min-width:1100px;height:auto}}
.fichas{{display:grid;grid-template-columns:repeat(auto-fill,minmax(380px,1fr));gap:12px}}
.ficha{{border:1px solid #e2e8f0;border-left:6px solid;border-radius:12px;padding:12px 14px;background:#fff}}
.ficha h3{{margin:0 0 4px;font-size:15.5px}} .id{{background:#14284b;color:#fff;border-radius:6px;padding:0 6px;font-size:13px}}
.ficha .estado{{margin:0 0 6px;font-weight:700;font-size:13px}} dl{{margin:0;font-size:13px}} dt{{font-weight:700;color:#5b6472;margin-top:4px}} dd{{margin:0}}
.ficha:target{{box-shadow:0 0 0 3px #2456c7}}
table{{border-collapse:collapse;width:100%;font-size:13.5px}} th,td{{border-bottom:1px solid #e2e8f0;padding:6px 8px;text-align:left;vertical-align:top}}
.nota{{white-space:pre-wrap;background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:14px;font-size:14px}}
.ok{{color:#1b7a45;font-weight:700}}
</style></head><body><main>
<h1>Circuito de compras · material de capacitación interna</h1>
<p>Fuente única: matriz consolidada v5.1 (18/11/2026). Tocá una referencia D1–D20 en el gráfico para ir a su ficha.</p>
<section><h2>1. Gráfico del circuito</h2><div class="fig">{svg}</div></section>
<section><h2>2. Etapa múltiple: expediente digital y ofertas en papel</h2><table>{etapa}</table></section>
<section><h2>3. La regla del 20 %</h2><table><tr><th>Regla</th><th>Texto literal (Dec. 1104/16, art. 116.1, pág. 17)</th><th>Dónde va</th><th>Estado</th></tr>{regla}</table></section>
<section><h2>4. Fichas de las discrepancias D1–D20</h2><div class="fichas">{fichas()}</div></section>
<section><h2>5. Consulta formal a la SCyGB (D7)</h2><div class="nota">{h(M.CONSULTA_D7)}</div></section>
<section><h2>6. Verificación gráfico ↔ matriz v5.1</h2>
<p class="ok">✔ Los {n_pares} pares (estado, discrepancia) del esquema v5.1 están en el gráfico. ✔ Ningún estado del gráfico contradice la matriz. ✔ Ramas A, A2, B, C privado, C público, D y E presentes. ✔ 20 fichas.</p>
<p>En el gráfico: {h(', '.join(en_grafico))}. Solo en fichas: {h(', '.join(solo_fichas) or '—')} (no tienen un paso propio en el recorrido).</p></section>
</main></body></html>"""


if __name__ == "__main__":
    en_grafico, solo_fichas, n = verificar()
    svg = svg_circuito()
    (AQUI / "circuito_v5_1.svg").write_text(svg, encoding="utf-8")
    (AQUI / "circuito_v5_1.html").write_text(html(svg, en_grafico, solo_fichas, n), encoding="utf-8")
    print("ok · en el gráfico:", en_grafico, "· solo fichas:", solo_fichas, "· pares del esquema:", n)
