"""Maquetas conceptuales del rediseño del gráfico de compras (no es la
implementación). Lee los datos actuales exportados en datos_actuales.json
(solo lectura) y arma:

- vista_general.svg  — para proyectar en la reunión
- vista_etapa_6.svg  — cómo se despliega una etapa
- propuesta_rediseno.html — las dos maquetas + tabla de trazabilidad

    python fuente/maquetas.py
"""
import json
from html import escape as h
from pathlib import Path
from xml.sax.saxutils import escape

AQUI = Path(__file__).resolve().parent.parent
DATOS = json.loads((AQUI / "datos_actuales.json").read_text(encoding="utf-8"))
FUENTE = 'font-family="Segoe UI, system-ui, Arial, sans-serif"'

# Colores: UN significado por canal.
#  - color de la tarjeta = DÓNDE pasa
#  - ícono / borde       = QUÉ TAN SEGURO es
DONDE = {
    "hospital": ("#7a6a52", "#f4efe6", "Fuera de TIMBÓ (hospital)"),
    "expediente": ("#2f6fde", "#e9f1ff", "Expediente electrónico TIMBÓ"),
    "compras": ("#0f8b8d", "#e0f4f3", "TIMBÓ Compras"),
    "mixto": ("#0f8b8d", "#e0f4f3", "TIMBÓ Compras + expediente"),
    "decision": ("#6a4fd6", "#f3efff", "Decisión"),
}
PEND = "#c25e00"
TXT, SUB = "#1f2937", "#4b5563"

# --------------------------------------------------------------- etapas
ETAPAS = [
    ("1", "Pedido", "hospital", ["r02", "r03"]),
    ("2", "Expediente y presupuesto", "expediente", ["r04", "r05", "r05b"]),
    ("3", "¿Qué procedimiento?", "decision", ["r06", "rA", "rA2", "rB", "rC", "rD"]),
    ("4", "Pliego y aprobación", "mixto", ["r07", "r08", "r09", "r09u", "r09a"]),
    ("5", "Publicación y ofertas", "compras", ["r10", "r10p", "r11", "r12", "r13"]),
    ("6", "Evaluación", "compras", ["r14", "r15", "r16", "r16u", "r17"]),
    ("7", "Adjudicación", "expediente", ["r18", "r18s", "r19"]),
    ("8", "Recepción y pago", "hospital", ["r20", "r21"]),
]
EXTREMOS = {"r01": "Inicio", "r99": "Fin"}
TRANSVERSAL = {"rObs": "Nota que se muestra en las etapas 4, 5 y 6"}

NODOS = {n["id"]: n for n in DATOS["reunion"]["nodos"]}
FLECHAS = DATOS["reunion"]["flechas"]
ETAPA_DE = {nid: e[0] for e in ETAPAS for nid in e[3]}
ETAPA_DE.update({k: v for k, v in EXTREMOS.items()})
PENDIENTES = {"pendiente_confirmacion", "pendiente_documentacion", "sin_respaldo", "en_revision", "observado"}


def pendientes_de(ids):
    return [i for i in ids if NODOS[i]["estado"] in PENDIENTES]


def sin_responsable(ids):
    return [i for i in ids if NODOS[i]["tipo"] in ("actividad", "verificacion", "autorizacion")
            and not NODOS[i]["responsables"] and not NODOS[i].get("sector")]


def t(x, y, s, size=16, weight=400, color=TXT, anchor="middle", extra=""):
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color}" '
            f'text-anchor="{anchor}" {extra}>{escape(s)}</text>')


def defs():
    return """<defs>
<marker id="p" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="9" markerHeight="9" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#334155"/></marker>
<marker id="pr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#6a4fd6"/></marker>
<pattern id="rayado" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="8" height="8" fill="#f4efe6"/><line x1="0" y1="0" x2="0" y2="8" stroke="#e6dccb" stroke-width="3"/></pattern>
<filter id="s" x="-5%" y="-5%" width="110%" height="120%"><feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#0f172a" flood-opacity="0.12"/></filter>
</defs>"""


# ======================================================== vista general
def vista_general():
    W, H = 1600, 900
    s = [f'<rect width="{W}" height="{H}" fill="#ffffff"/>']
    s.append(t(60, 70, "Cómo se hace una compra", 34, 700, TXT, "start"))
    s.append(t(60, 104, "Licitación o concurso en un hospital de Santa Fe · tocá una etapa para ver el detalle", 18, 400, SUB, "start"))

    cw, ch = 210, 150
    fila1_y, fila2_y = 200, 560
    # fila 1: Inicio, 1, 2, 3 ; fila 2 (de derecha a izquierda no: de izquierda a derecha): 4..8, Fin
    pos = {}
    xs1 = [60, 330, 600]
    for (num, nombre, donde, ids), x in zip(ETAPAS[:2], xs1[1:]):
        pos[num] = (x, fila1_y)
    pos["3"] = (900, fila1_y - 10)
    xs2 = [130, 400, 670, 940, 1210]
    for (num, *_), x in zip(ETAPAS[3:], xs2):
        pos[num] = (x, fila2_y)

    def tarjeta(num, nombre, donde, ids, x, y):
        col, fondo, _ = DONDE[donde]
        out = []
        relleno = "url(#rayado)" if donde == "hospital" else fondo
        out.append(f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="18" fill="{relleno}" stroke="{col}" stroke-width="3" filter="url(#s)"/>')
        out.append(f'<circle cx="{x + 34}" cy="{y + 34}" r="22" fill="{col}"/>')
        out.append(t(x + 34, y + 42, num, 22, 700, "#fff"))
        palabras = nombre.split(" ")
        lineas = [nombre] if len(nombre) <= 14 else [" ".join(palabras[:len(palabras) // 2 + (len(palabras) % 2)]), " ".join(palabras[len(palabras) // 2 + (len(palabras) % 2):])]
        for i, l in enumerate(lineas):
            out.append(t(x + cw / 2, y + 84 + i * 24, l, 21, 700, TXT))
        p = len(pendientes_de(ids))
        sr = len(sin_responsable(ids))
        if p or sr:
            txt = []
            if p:
                txt.append(f"? {p}")
            if sr:
                txt.append("👤 a relevar")
            etiqueta = "  ".join(txt)
            ancho = 16 + 9 * len(etiqueta)
            out.append(f'<rect x="{x + cw / 2 - ancho / 2}" y="{y + ch - 38}" width="{ancho}" height="26" rx="13" fill="#fff" stroke="{PEND}" stroke-width="2" stroke-dasharray="5 3"/>')
            out.append(t(x + cw / 2, y + ch - 20, etiqueta, 15, 700, PEND))
        else:
            out.append(t(x + cw / 2, y + ch - 20, "✔ documentado", 15, 700, "#1b7a45"))
        return out

    def flecha(x1, y1, x2, y2, color="#334155", marca="p", dash=""):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        return f'<path d="M{x1},{y1} L{x2},{y2}" stroke="{color}" stroke-width="4" fill="none" marker-end="url(#{marca})"{d}/>'

    # Inicio
    s.append(f'<rect x="60" y="{fila1_y + 45}" width="190" height="60" rx="30" fill="#1b7a45"/>')
    s.append(t(155, fila1_y + 84, "● INICIO", 20, 700, "#fff"))
    s.append(t(155, fila1_y + 132, "Necesidad de compra", 15, 400, SUB))
    s.append(flecha(250, fila1_y + 75, 322, fila1_y + 75))
    for num, nombre, donde, ids in ETAPAS[:2]:
        s += tarjeta(num, nombre, donde, ids, *pos[num])
    s.append(flecha(540, fila1_y + 75, 592, fila1_y + 75))
    s.append(flecha(810, fila1_y + 75, 892, fila1_y + 75))
    # Decisión 3
    dx, dy = 900, fila1_y - 10
    s.append(f'<polygon points="{dx + 130},{dy} {dx + 260},{dy + 85} {dx + 130},{dy + 170} {dx},{dy + 85}" fill="#f3efff" stroke="#6a4fd6" stroke-width="3" filter="url(#s)"/>')
    s.append(f'<circle cx="{dx + 130}" cy="{dy + 42}" r="20" fill="#6a4fd6"/>')
    s.append(t(dx + 130, dy + 50, "3", 20, 700, "#fff"))
    s.append(t(dx + 130, dy + 92, "¿Qué", 20, 700, TXT))
    s.append(t(dx + 130, dy + 116, "procedimiento?", 20, 700, TXT))
    s.append(t(dx + 130, dy + 142, "según monto y causal", 13, 400, SUB))
    # Ramas A, B, D (a la derecha) y C (camino principal, hacia abajo)
    ramas = [("A", "Directa", "por monto o causal", "? sigue sin documentar", dy - 10),
             ("B", "Urgencia o desierto", "se une en la etapa 4", "", dy + 60),
             ("D", "Etapa múltiple", "papel · se une en la etapa 7", "", dy + 130)]
    for letra, nom, nota, pend, ry in ramas:
        x0 = 1250
        s.append(f'<path d="M{dx + 260},{dy + 85} C{dx + 300},{dy + 85} {x0 - 50},{ry + 30} {x0 - 6},{ry + 30}" stroke="#6a4fd6" stroke-width="3" fill="none" marker-end="url(#pr)"/>')
        s.append(f'<rect x="{x0}" y="{ry}" width="300" height="60" rx="14" fill="#fff" stroke="#6a4fd6" stroke-width="2.5"/>')
        s.append(f'<circle cx="{x0 + 28}" cy="{ry + 30}" r="17" fill="#6a4fd6"/>')
        s.append(t(x0 + 28, ry + 37, letra, 18, 700, "#fff"))
        s.append(t(x0 + 56, ry + 27, nom, 17, 700, TXT, "start"))
        s.append(t(x0 + 56, ry + 48, nota if not pend else pend, 13, 600, PEND if pend else SUB, "start"))
        s.append(t(x0 + 286, ry + 37, "›", 24, 700, "#6a4fd6", "end"))
    # C: camino principal
    s.append(f'<path d="M{dx + 130},{dy + 170} L{dx + 130},{fila1_y + 250} L235,{fila1_y + 250} L235,{fila2_y - 8}" stroke="#334155" stroke-width="4" fill="none" marker-end="url(#p)"/>')
    s.append(f'<rect x="{dx - 40}" y="{fila1_y + 228}" width="340" height="44" rx="22" fill="#fff" stroke="#6a4fd6" stroke-width="2.5"/>')
    s.append(f'<circle cx="{dx - 14}" cy="{fila1_y + 250}" r="15" fill="#6a4fd6"/>')
    s.append(t(dx - 14, fila1_y + 256, "C", 16, 700, "#fff"))
    s.append(t(dx + 8, fila1_y + 256, "Licitación o concurso · camino principal", 15, 700, TXT, "start"))
    # fila 2
    for num, nombre, donde, ids in ETAPAS[3:]:
        s += tarjeta(num, nombre, donde, ids, *pos[num])
    for a, b in zip(xs2, xs2[1:]):
        s.append(flecha(a + cw, fila2_y + 75, b - 8, fila2_y + 75))
    # Fin
    s.append(flecha(1420, fila2_y + 75, 1452, fila2_y + 75))
    s.append(f'<rect x="1458" y="{fila2_y + 45}" width="110" height="60" rx="12" fill="#1f2937"/>')
    s.append(t(1513, fila2_y + 84, "■ FIN", 20, 700, "#fff"))
    # Leyenda mínima
    ly = 800
    s.append(f'<line x1="60" y1="{ly - 30}" x2="{W - 60}" y2="{ly - 30}" stroke="#e2e8f0" stroke-width="2"/>')
    x = 60
    for clave in ("compras", "expediente", "hospital"):
        col, fondo, nombre = DONDE[clave]
        relleno = "url(#rayado)" if clave == "hospital" else fondo
        s.append(f'<rect x="{x}" y="{ly}" width="34" height="24" rx="6" fill="{relleno}" stroke="{col}" stroke-width="2.5"/>')
        s.append(t(x + 44, ly + 18, nombre, 16, 600, TXT, "start"))
        x += 64 + 9 * len(nombre)
    s.append(t(x + 10, ly + 18, "✔ documentado", 16, 700, "#1b7a45", "start"))
    s.append(f'<rect x="{x + 160}" y="{ly - 1}" width="40" height="26" rx="13" fill="#fff" stroke="{PEND}" stroke-width="2" stroke-dasharray="5 3"/>')
    s.append(t(x + 180, ly + 18, "? n", 15, 700, PEND))
    s.append(t(x + 210, ly + 18, "pendientes", 16, 600, TXT, "start"))
    s.append(t(60, ly + 60, "Maqueta conceptual · datos del gráfico actual · los «?» cuentan pasos pendientes de confirmar o documentar.", 14, 400, SUB, "start"))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" {FUENTE}>' + defs()
            + "\n".join(s) + "</svg>")


# ====================================================== vista de etapa 6
def vista_etapa():
    W, H = 1600, 1000
    s = [f'<rect width="{W}" height="{H}" fill="#ffffff"/>']
    s.append(t(40, 46, "Vista general  ›", 17, 600, "#2456c7", "start"))
    s.append(f'<circle cx="200" cy="40" r="18" fill="#0f8b8d"/>' + t(200, 47, "6", 18, 700, "#fff"))
    s.append(t(228, 48, "Evaluación y preadjudicación", 26, 700, TXT, "start"))
    s.append(t(40, 84, "📎 Todo lo que se firma en TIMBÓ Compras se incorpora solo al expediente (Circ. UG 7/2026, pto 7).", 15, 400, SUB, "start"))
    # viene de
    s.append(f'<rect x="40" y="104" width="420" height="40" rx="20" fill="#f1f5f9" stroke="#cbd5e1"/>')
    s.append(t(60, 130, "◀ Viene de 5 · Publicación y ofertas (13 Apertura)", 15, 600, TXT, "start"))
    # carriles (salen del campo «sistema» de cada paso)
    LX = {"compras": (40, 480), "expediente": (540, 400)}
    s.append(f'<rect x="40" y="160" width="480" height="760" rx="16" fill="#e0f4f3" opacity="0.6"/>')
    s.append(f'<rect x="40" y="160" width="480" height="36" rx="12" fill="#0f8b8d"/>' + t(280, 184, "TIMBÓ COMPRAS", 15, 700, "#fff"))
    s.append(f'<rect x="540" y="160" width="400" height="760" rx="16" fill="#e9f1ff" opacity="0.6"/>')
    s.append(f'<rect x="540" y="160" width="400" height="36" rx="12" fill="#2f6fde"/>' + t(740, 184, "EXPEDIENTE ELECTRÓNICO", 15, 700, "#fff"))

    def paso(x, y, w, num, titulo, quien, extra, estado="ok", tipo="paso", sel=False):
        out = []
        borde = "#0f8b8d" if x < 530 else "#2f6fde"
        dash = ' stroke-dasharray="7 4"' if estado == "pend" else ""
        if tipo == "excepcion":
            borde = "#b42318"
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="96" rx="14" fill="#fff" stroke="{borde}" stroke-width="{4 if sel else 2.5}"{dash} filter="url(#s)"/>')
        if sel:
            out.append(f'<rect x="{x - 6}" y="{y - 6}" width="{w + 12}" height="108" rx="18" fill="none" stroke="#2456c7" stroke-width="3" opacity="0.5"/>')
        if num:
            out.append(f'<circle cx="{x + 26}" cy="{y + 28}" r="16" fill="{borde}"/>' + t(x + 26, y + 34, num, 15, 700, "#fff"))
        out.append(t(x + 52, y + 34, titulo, 17, 700, TXT, "start"))
        # chip de quién
        out.append(f'<rect x="{x + 14}" y="{y + 50}" width="{w - 28}" height="24" rx="12" fill="{"#e0f4f3" if "rol" in quien else "#f1f5f9"}"/>')
        out.append(t(x + 24, y + 67, quien, 13, 600, "#0b5f61" if "rol" in quien else SUB, "start"))
        out.append(t(x + 14, y + 90, extra, 12.5, 400, SUB, "start"))
        icono = "✔" if estado == "ok" else "?"
        out.append(f'<circle cx="{x + w - 22}" cy="{y + 26}" r="14" fill="{"#e7f5ec" if estado == "ok" else "#fff"}" stroke="{"#1b7a45" if estado == "ok" else PEND}" stroke-width="2"{dash}/>')
        out.append(t(x + w - 22, y + 32, icono, 16, 700, "#1b7a45" if estado == "ok" else PEND))
        return out

    def rombo(cx, cy, texto, nota):
        out = [f'<polygon points="{cx},{cy - 46} {cx + 150},{cy} {cx},{cy + 46} {cx - 150},{cy}" fill="#f3efff" stroke="#6a4fd6" stroke-width="2.5"/>',
               t(cx, cy + 2, texto, 15, 700, TXT), t(cx, cy + 22, nota, 11.5, 400, SUB)]
        return out

    def pastilla(x, y, texto, color="#6a4fd6"):
        w = 16 + 8 * len(texto)
        return [f'<rect x="{x - w / 2}" y="{y - 13}" width="{w}" height="26" rx="13" fill="#fff" stroke="{color}" stroke-width="2"/>',
                t(x, y + 5, texto, 13, 700, color)]

    def linea(d, color="#334155", dash=""):
        dd = f' stroke-dasharray="{dash}"' if dash else ""
        return f'<path d="{d}" stroke="{color}" stroke-width="3" fill="none" marker-end="url(#p)"{dd}/>'

    s.append(linea("M250,144 L250,206"))
    s += paso(60, 210, 440, "14", "Evaluación de ofertas", "👤 Evaluadores · rol TIMBÓ", "Evalúan y preseleccionan · 1 fuente")
    s.append(linea("M280,306 L280,330"))
    s += rombo(280, 380, "¿Hace falta subsanar?", "flechas actuales g29 / g30")
    s += pastilla(140, 440, "Sí")
    s += pastilla(420, 440, "No")
    s.append(linea("M190,410 L140,428 L140,470", "#6a4fd6"))
    s += paso(60, 480, 300, "15", "Subsanación o mejora", "👤 Evaluadores → Proveedor · rol", "Si no responde a tiempo: «descartado»")
    s.append(linea("M370,410 L420,428 L420,600", "#6a4fd6"))
    s.append(linea("M210,576 L210,610 L330,610"))
    s += paso(60, 620 - 10, 440, "16", "Informe de preadjudicación", "👤 Evaluadores firman en orden · rol", "📄 Documento digital firmado · 1 fuente", sel=True)
    # URC
    s.append(linea("M500,650 L580,650", "#2f6fde", "7 4"))
    s += pastilla(540, 630, "si aplica", "#c25e00")
    s += paso(590, 610, 330, "", "Control de la preadjudicación", "🏛 URC · organismo externo", "Antes del cronograma de impugnación", estado="pend")
    # impugnaciones
    s.append(linea("M280,706 L280,736"))
    s += rombo(280, 786, "¿Se presentan impugnaciones?", "flechas actuales g34 / g35")
    s += pastilla(140, 846, "Sí")
    s += pastilla(430, 846, "No")
    s.append(linea("M190,816 L140,834 L140,858", "#6a4fd6"))
    s.append(f'<rect x="60" y="862" width="420" height="50" rx="12" fill="#fff5f4" stroke="#b42318" stroke-width="2.5"/>')
    s.append(t(76, 884, "↯ 17 Impugnaciones · excepción", 15, 700, "#b42318", "start"))
    s.append(t(76, 903, "👤 Proveedor impugna · Evaluador recibe · 2 días + garantía", 12.5, 400, SUB, "start"))
    # sigue en 7
    s.append(f'<rect x="560" y="860" width="360" height="50" rx="25" fill="#2f6fde"/>')
    s.append(t(740, 891, "Sigue en 7 · Adjudicación ▶", 17, 700, "#fff"))
    s.append(linea("M480,887 L552,887", "#334155"))
    s.append(linea("M430,860 L430,850", "#334155"))
    s.append(linea("M755,706 L755,852", "#2f6fde", "7 4"))
    s += pastilla(840, 790, "con el informe de la URC", "#2f6fde")
    s.append(t(460, 878, "se resuelven con la adjudicación", 11.5, 600, SUB, "end"))

    # Panel de detalle del paso seleccionado (16)
    px = 970
    s.append(f'<rect x="{px}" y="104" width="600" height="816" rx="16" fill="#ffffff" stroke="#e2e8f0" stroke-width="2" filter="url(#s)"/>')
    s.append(t(px + 24, 142, "16 · Informe de preadjudicación", 21, 700, TXT, "start"))
    s.append(f'<rect x="{px + 24}" y="156" width="190" height="26" rx="13" fill="#e7f5ec" stroke="#1b7a45"/>' + t(px + 119, 174, "✔ Documentado", 14, 700, "#1b7a45"))
    s.append(f'<rect x="{px + 224}" y="156" width="150" height="26" rx="13" fill="#e0f4f3" stroke="#0f8b8d"/>' + t(px + 299, 174, "TIMBÓ Compras", 14, 700, "#0b5f61"))
    s.append(f'<rect x="{px + 24}" y="198" width="552" height="46" rx="12" fill="#2456c7"/>' + t(px + 300, 228, "📚 CONSULTAR DOCUMENTACIÓN", 17, 700, "#fff"))
    y = 276
    filas = [
        ("Quién", "Evaluadores (rol TIMBÓ): firman en el orden de «Ordenar evaluadores»"),
        ("Documento", "Informe de preadjudicación · digital, firmado en TIMBÓ Compras"),
        ("Después", "Sí impugnan → 17 · No → sigue en 7 · si aplica → control de la URC"),
        ("Pendiente", "Si el control de la URC alcanza al hospital (a confirmar)"),
    ]
    for k, v in filas:
        s.append(t(px + 24, y, k, 15, 700, SUB, "start"))
        s.append(t(px + 130, y, v, 15, 400, TXT, "start"))
        y += 34
    s.append(f'<line x1="{px + 24}" y1="{y}" x2="{px + 576}" y2="{y}" stroke="#e2e8f0" stroke-width="2"/>')
    y += 34
    s.append(t(px + 24, y, "Fuente oficial", 16, 700, TXT, "start"))
    y += 12
    s.append(f'<rect x="{px + 24}" y="{y}" width="552" height="170" rx="10" fill="#f8fafc" stroke="#cbd5e1"/>')
    s.append(f'<rect x="{px + 24}" y="{y}" width="6" height="170" rx="3" fill="#2456c7"/>')
    s.append(t(px + 44, y + 30, "Circular UG TIMBÓ N° 7/2026 — Términos y condiciones", 15, 700, TXT, "start"))
    s.append(t(px + 44, y + 54, "Unidad de Gestión TIMBÓ · Punto 22 · página 5", 13.5, 400, SUB, "start"))
    s.append(t(px + 44, y + 86, "«Sobre el informe de preadjudicación actuarán y firmarán", 14, 400, TXT, "start", 'font-style="italic"'))
    s.append(t(px + 44, y + 108, "aquellos evaluadores designados en el orden del formulario", 14, 400, TXT, "start", 'font-style="italic"'))
    s.append(t(px + 44, y + 130, "Ordenar evaluadores.»", 14, 400, TXT, "start", 'font-style="italic"'))
    s.append(t(px + 44, y + 158, "Abrir el PDF en la página 5 ↗", 14, 700, "#2456c7", "start"))
    y += 210
    s.append(t(px + 24, y, "Pendientes de esta etapa", 16, 700, PEND, "start"))
    s.append(t(px + 24, y + 28, "? Control de la preadjudicación de la URC: ¿aplica al hospital?", 14, 400, TXT, "start"))
    s.append(t(px + 24, y + 70, "Comentarios (2) · Historial de este paso", 14, 600, "#2456c7", "start"))
    s.append(t(40, 960, "Maqueta conceptual. Los carriles salen del campo «sistema» de cada paso; los rombos «¿Hace falta subsanar?» y «¿Se presentan", 13.5, 400, SUB, "start"))
    s.append(t(40, 980, "impugnaciones?» se dibujan con las dos flechas que ya existen (no son bloques nuevos).", 13.5, 400, SUB, "start"))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" {FUENTE}>' + defs()
            + "\n".join(s) + "</svg>")


# ====================================================== trazabilidad
def tabla_trazabilidad():
    nombres = {e[0]: f"{e[0]} · {e[1]}" for e in ETAPAS}
    nombres.update({"Inicio": "Inicio", "Fin": "Fin"})
    filas, sin_etapa = [], []
    for n in DATOS["reunion"]["nodos"]:
        etapa = ETAPA_DE.get(n["id"])
        if not etapa and n["id"] in TRANSVERSAL:
            etapa_txt = "Transversal: " + TRANSVERSAL[n["id"]]
        elif etapa:
            etapa_txt = nombres[etapa]
        else:
            etapa_txt = "⚠ SIN ETAPA: bloque agregado después de la carga (vacío). A decidir."
            sin_etapa.append(n)
        filas.append((n, etapa_txt))
    flechas = []
    for f in FLECHAS:
        a, b = ETAPA_DE.get(f["desde"]), ETAPA_DE.get(f["hasta"])
        if a == b:
            cuenta = f"dentro de la etapa {a}"
        else:
            cuenta = f"conector «sigue en {b}» / «viene de {a}»"
        flechas.append((f, cuenta))
    return filas, flechas, sin_etapa


def html():
    filas, flechas, sin_etapa = tabla_trazabilidad()
    rangos = DATOS["rangos"]
    total_asignados = sum(1 for _, e in filas if not e.startswith("⚠"))
    tr_b = "\n".join(
        f"<tr><td><code>{h(n['id'])}</code></td><td>{h(n['titulo'])}</td><td>{h(n['tipo'])}</td><td>{h(n['estado'].replace('_', ' '))}</td>"
        f"<td>{len(n['fuentes'])}</td><td>{h(e)}</td></tr>" for n, e in filas)
    tr_f = "\n".join(
        f"<tr><td><code>{h(f['id'])}</code></td><td>{h(DATOS['reunion'] and next(x['titulo'] for x in DATOS['reunion']['nodos'] if x['id']==f['desde']))}</td>"
        f"<td>{h(next(x['titulo'] for x in DATOS['reunion']['nodos'] if x['id']==f['hasta']))}</td>"
        f"<td>{h(f['etiqueta'] or rangos.get(str(f['rango']), '') if f['rango'] is not None else f['etiqueta'])}</td><td>{h(c)}</td></tr>"
        for f, c in flechas)
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Rediseño del circuito de compras</title>
<style>
body{{margin:0;background:#f6f7f9;color:#1f2937;font:15px/1.5 "Segoe UI",system-ui,Arial,sans-serif}}
main{{max-width:1200px;margin:0 auto;padding:24px 16px 60px}}
section{{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:20px 22px;margin-top:18px}}
h1{{margin:0 0 4px;font-size:26px}} h2{{margin:0 0 8px;font-size:20px}}
.fig{{border:1px solid #e2e8f0;border-radius:12px;overflow:auto;background:#fff}} .fig svg{{display:block;width:100%;height:auto;min-width:900px}}
table{{border-collapse:collapse;width:100%;font-size:13.5px}} th,td{{border-bottom:1px solid #e2e8f0;padding:6px 8px;text-align:left;vertical-align:top}}
th{{background:#f8fafc}} code{{font-size:12px}} .ok{{color:#1b7a45;font-weight:700}} .warn{{color:#c25e00;font-weight:700}}
.tabla{{overflow-x:auto}}
</style></head><body><main>
<h1>Rediseño del circuito de compras: propuesta para revisar</h1>
<p>Maquetas conceptuales. No modifican los circuitos del Centro: salen de una copia de solo lectura del gráfico actual.</p>
<section><h2>1. Maqueta: vista general + detalle de una etapa (ejemplo: 6)</h2><div class="fig">{__import__("dos_paneles").maqueta()}</div></section>
<section><h2>3. Trazabilidad: cada bloque actual y su etapa</h2>
<p class="{'ok' if not sin_etapa else 'warn'}">{total_asignados} de {len(filas)} bloques tienen etapa asignada{'' if not sin_etapa else f' · {len(sin_etapa)} bloque sin etapa (ver abajo)'}.</p>
<div class="tabla"><table><thead><tr><th>Id</th><th>Bloque actual</th><th>Tipo</th><th>Estado</th><th>Fuentes</th><th>Etapa nueva</th></tr></thead><tbody>{tr_b}</tbody></table></div></section>
<section><h2>4. Trazabilidad: cada flecha actual</h2>
<p class="ok">Las {len(flechas)} flechas se conservan: las de adentro de una etapa se dibujan en su vista; las que cruzan etapas pasan a ser «viene de / sigue en».</p>
<div class="tabla"><table><thead><tr><th>Id</th><th>Desde</th><th>Hasta</th><th>Condición o monto</th><th>Cómo se ve</th></tr></thead><tbody>{tr_f}</tbody></table></div></section>
</main></body></html>"""


if __name__ == "__main__":
    (AQUI / "vista_general.svg").write_text(vista_general(), encoding="utf-8")
    (AQUI / "vista_etapa_6.svg").write_text(vista_etapa(), encoding="utf-8")
    (AQUI / "propuesta_rediseno.html").write_text(html(), encoding="utf-8")
    filas, flechas, sin_etapa = tabla_trazabilidad()
    print(len(filas), "bloques,", len(flechas), "flechas, sin etapa:", [n["id"] for n in sin_etapa])
