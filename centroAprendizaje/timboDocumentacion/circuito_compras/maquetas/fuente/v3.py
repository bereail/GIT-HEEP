"""Maqueta v3: dos paneles sobre el CIRCUITO OFICIAL de TIMBÓ.

No modifica nada del Centro: lee datos_actuales.json (copia de solo lectura).
Las correcciones de fidelidad salen de la revisión de fuentes del 18/11/2026
y quedan marcadas como PROPUESTAS (no aplicadas).

    python fuente/v3.py
"""
import json
from html import escape as h
from pathlib import Path
from xml.sax.saxutils import escape

AQUI = Path(__file__).resolve().parent.parent
DATOS = json.loads((AQUI / "datos_actuales.json").read_text(encoding="utf-8"))
OF = DATOS["oficial"]
N = {n["id"]: n for n in OF["nodos"]}
DOCS = DATOS["docs"]

# ------------------------------------------------------------ etapas (oficial)
ETAPAS = [
    ("1", "Preparar la compra", "Etapa preparatoria por expediente electrónico", ["o02", "o03"]),
    ("2", "¿Qué procedimiento corresponde?", "Según el monto y la causal", ["o04", "o05", "o05b", "o06", "o07", "o08"]),
    ("3", "Armar el pliego", "Formularios del pliego en TIMBÓ Compras", ["o09", "o10", "o11", "o13", "o12", "o12b"]),
    ("4", "Aprobar y autorizar el llamado", "Controles, cronograma y acto de la autoridad", ["o14", "o15", "o16"]),
    ("5", "Publicar", "Proceso publicado, difusión y consultas", ["o17", "o18", "o19"]),
    ("6", "Recibir y abrir ofertas", "Ofertas de los proveedores y apertura automática", ["o20", "o20e", "o21", "o21d"]),
    ("7", "Evaluar y preadjudicar", "Evaluadores, subsanaciones e informe", ["o22", "o23", "o24", "o24x", "o25", "o26", "o27", "o28", "o29"]),
    ("8", "Adjudicar", "Acto de la autoridad · SIN y Tribunal de Cuentas", ["o30", "o31"]),
    ("9", "Contrato, recepción y pago", "Recepción, certificado, factura y pago", ["o32", "o33", "o34", "o34d", "o35", "o36", "o36e"]),
]
EXTREMOS = {"o01": "Inicio", "o37": "Fin", "o40": "Transversal (etapas 3 a 7)"}
ETAPA_DE = {i: e[0] for e in ETAPAS for i in e[3]}
ETAPA_DE.update(EXTREMOS)
PENDIENTES = {"pendiente_confirmacion", "pendiente_documentacion", "sin_respaldo", "en_revision", "observado"}

# ----------------------------------------------- hallazgos de fidelidad (18/11)
HALLAZGOS = [
    ("F1", "SIN y Tribunal de Cuentas para TODOS los actos",
     "El circuito lo pone solo después de la adjudicación y «si corresponde control de legalidad».",
     "Todos los actos (con y sin efecto hacendal) se ponen a disposición del TCP y se cargan en el SIN; la carga la hacen las Direcciones Generales de Despacho.",
     "Circular UG TIMBÓ 11/2026, arts. 1 y 2 (pág. 2) · Circular UG 9/2026, art. 3 (pág. 2)",
     "Sumar el paso también después del acto que aprueba el pliego (etapa 4) y quitar el «si corresponde» de la etapa 8.", "4 · 8"),
    ("F2", "Falta la vista e impugnación de las ofertas",
     "El circuito solo tiene la impugnación a la preadjudicación.",
     "Durante 2 días hábiles después de la apertura, los oferentes pueden tomar vista e impugnar el acto de apertura o las ofertas, con garantía; se resuelven junto con la adjudicación.",
     "Pliego Único, 4.3 (pág. 31) · Circular UG 7/2026, pto 20.1 (pág. 5)",
     "Agregar el paso (documentado) en la etapa 6.", "6"),
    ("F3", "La publicidad depende del procedimiento",
     "El circuito aplica a todos los «10 días corridos» y el aviso oficial.",
     "Público: Boletín Oficial 2 días y diarios; 10 días corridos (20 si es internacional). Privado: al menos 5 invitaciones fehacientes con 5 días corridos de antelación y difusión en Internet.",
     "Dec. 1104/16, art. 132.3 (pág. 26) y art. 121.1 (pág. 20) · Ley 12.510, art. 132 (pág. 43)",
     "Separar la publicación de público y de privado en la etapa 5.", "5"),
    ("F4", "Discrepancia: uno o dos diarios",
     "—",
     "El Dec. 1104/16, art. 132.3 (no modificado por el Dec. 287/2026) dice «un (1) día en dos diarios». La nota modelo de la Circular SCyGB 04/2026 (más reciente) dice «un (1) día en un (1) diario».",
     "Dec. 1104/16, art. 132.3 (pág. 26) · Dec. 287/2026, art. 2 (solo modifica el apartado 1) · Circ. SCyGB 04/2026, Anexo II (pág. 4)",
     "No elegir: mostrar las dos y marcar «Pendiente de confirmación».", "5"),
    ("F5", "Falta publicar el acto de adjudicación",
     "No figura.",
     "Los actos que resuelven las adjudicaciones se publican en Internet; en licitaciones y concursos públicos, también la preadjudicación y la adjudicación en el sitio web de contrataciones.",
     "Ley 12.510, art. 132 (pág. 43) · Dec. 1104/16, art. 132.4 (pág. 26)",
     "Agregar el paso en la etapa 8.", "8"),
    ("F6", "Falta el perfeccionamiento del contrato",
     "La etapa contractual pasa directo a la recepción.",
     "El contrato se perfecciona con la notificación de la adjudicación; orden de compra o contrato dentro de 10 días corridos; garantía de fiel cumplimiento dentro de 5 días; si no, caducidad y se puede adjudicar al siguiente en el orden de mérito.",
     "Pliego Único, 5.6 (pág. 38)", "Agregar el paso y su excepción en la etapa 9.", "9"),
    ("F7", "Excepciones no representadas",
     "No figuran.",
     "Revocación del llamado por autoridad competente antes del contrato (5.5) · dejarlo sin efecto si hay un vicio (4.3) · empate → mejora de precios y, si sigue igual, sorteo (5.3; Ley art. 133) · una sola oferta no impide adjudicar (5.2) · desierto → contratación directa por desierto, rama B (Ley art. 116 c.3; Circ. UG 8/2026).",
     "Pliego Único 4.3, 5.2, 5.3, 5.5 (págs. 31, 37, 38) · Ley 12.510 arts. 116 y 133 (págs. 40 y 43) · Circ. UG 8/2026 art. 3 (pág. 1)",
     "Mostrarlas en «Si algo sale distinto» de cada etapa.", "6 · 7 · 8"),
    ("F8", "Controles de la URC dibujados como obligatorios",
     "Las flechas f18 y f39 llevan siempre al control de la URC.",
     "La Res. ME 73/2026 y la Circ. SCyGB 03/2026 son para la Administración Pública Central; si alcanzan al hospital está pendiente.",
     "Res. ME 73/2026, art. 2 (pág. 3) · Circ. SCyGB 03/2026 (pág. 1)",
     "Marcar esos caminos como «si aplica (a confirmar)».", "4 · 7"),
    ("F9", "Órdenes no documentados",
     "Comitente vs. Supervisor, y cronograma vs. URC.",
     "La Circular UG 7/2026 define los roles, no el orden entre esos pasos.",
     "Circular UG 7/2026, pto 10 (pág. 3)", "Se mantienen como pendientes (sin cambios).", "3 · 4"),
    ("F10", "Dónde se firma el acto que aprueba el pliego",
     "El bloque dice «expediente».",
     "La fuente dice que el Supervisor lo carga en TIMBÓ Compras; no dice dónde se firma.",
     "Circular UG 7/2026, pto 10 (pág. 3)", "Ubicación «¿Dónde? a relevar» con la aclaración.", "4"),
    ("F11", "Mejora de precios: a quiénes",
     "El circuito no lo dice.",
     "Se puede pedir mejora a las ofertas admisibles mejor colocadas: hasta un 5 % por encima del menor precio.",
     "Dec. 1104/16, art. 133.1 (pág. 27)", "Agregarlo al detalle del subtrámite de mejora (etapa 7).", "7"),
    ("F12", "Pasos de la compra directa (rama A)",
     "Bloque pendiente.",
     "La biblioteca tiene la capacitación oficial en video de compras directas, pero sus pasos no se verificaron cita por cita para este circuito.",
     "Biblioteca: «video-capacitacion-compras-directas» (sin verificar acá)", "Se mantiene pendiente hasta verificarlo.", "2"),
    ("F13", "Recepción y pago: dónde y quién",
     "Ubicación sin definir.",
     "El Pliego Único fija las reglas, pero no el sistema ni la oficina.",
     "Pliego Único 6.9 a 6.13 (págs. 46 a 49)", "Se mantiene «a relevar».", "9"),
]

# Bloques PROPUESTOS por los hallazgos (no aplicados)
PROPUESTOS = {
    "4": [("SIN y Tribunal de Cuentas del acto aprobatorio", "documentado", "F1")],
    "5": [("Publicación de licitación o concurso privado: 5 invitaciones y difusión en Internet", "documentado", "F3"),
          ("¿Uno o dos diarios? (discrepancia)", "pendiente_confirmacion", "F4")],
    "6": [("Vista e impugnación de las ofertas (2 días hábiles)", "documentado", "F2")],
    "8": [("Publicar el acto de adjudicación en Internet", "documentado", "F5")],
    "9": [("Perfeccionamiento: orden de compra y garantía de fiel cumplimiento", "documentado", "F6")],
}

# ------------------------------------------------------------------- estilo
FUENTE_SVG = 'font-family="Segoe UI, system-ui, Arial, sans-serif"'
TXT, SUB, LINEA, FONDO = "#1f2937", "#5b6472", "#e3e8ef", "#f3f5f9"
AZUL, AZUL_F = "#1f5fbf", "#e8f0fd"
TEAL, TEAL_F = "#0f7f86", "#e2f4f3"
BEIGE, BEIGE_F = "#9a6a1c", "#fdf3e1"
GRIS, GRIS_F = "#5b6472", "#f1f3f6"
VIOLETA, VIOLETA_F = "#6a4fd6", "#f1edff"
OK, OK_F = "#1b7a45", "#e7f5ec"
PEND, PEND_F, ROJO, NAVY = "#b85400", "#fff4e8", "#b42318", "#14284b"
ESTADO = {
    "documentado": ("✔", "Documentado", OK, OK_F, False),
    "confirmado_equipo": ("👥", "Confirmado por el equipo", "#2456c7", AZUL_F, False),
    "pendiente_documentacion": ("◌", "Pendiente de documentación", PEND, PEND_F, True),
    "pendiente_confirmacion": ("?", "Pendiente de confirmación", PEND, PEND_F, True),
    "sin_respaldo": ("⚠", "Sin respaldo", ROJO, "#fdeceb", False),
}


def t(x, y, s, size=15, weight=400, color=TXT, anchor="start", extra=""):
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color}" '
            f'text-anchor="{anchor}" {extra}>{escape(s)}</text>')


def chip(x, y, texto, color, fondo, size=12, punteado=False, alto=24, ancho=None, anchor="start"):
    w = ancho or (20 + size * 0.6 * len(texto))
    if anchor == "end":
        x -= w
    d = ' stroke-dasharray="4 3"' if punteado else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{alto}" rx="{alto / 2}" fill="{fondo}" stroke="{color}" stroke-width="1.4"{d}/>'
            + t(x + w / 2, y + alto / 2 + size * 0.36, texto, size, 700, color, "middle")), w


def chip_estado(x, y, estado, size=11.5, anchor="end"):
    ic, txt, col, fondo, punt = ESTADO[estado]
    return chip(x, y, f"{ic} {txt}", col, fondo, size, punt, 22, anchor=anchor)[0]


def cuenta(ids):
    c = {}
    for i in ids:
        c[N[i]["estado"]] = c.get(N[i]["estado"], 0) + 1
    return c


def ubic_etapa(num, ids):
    if num == "2":
        return "Decisión", VIOLETA, VIOLETA_F
    sis = {N[i]["sistema"] for i in ids if N[i]["tipo"] not in ("decision", "condicion")}
    if num == "4":
        sis = sis | {"sin_definir"}  # F10: dónde se firma el acto, a relevar
    if sis == {"sin_definir"}:
        return "¿Dónde? a relevar", GRIS, GRIS_F
    if "sin_definir" in sis:
        return "En TIMBÓ · parte a relevar", TEAL, TEAL_F
    if sis <= {"expediente", "compras"}:
        return "En TIMBÓ", TEAL, TEAL_F
    return "TIMBÓ + fuera", TEAL, TEAL_F


def defs():
    return f"""<defs>
<marker id="p" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#94a3b8"/></marker>
<filter id="s" x="-5%" y="-10%" width="110%" height="130%"><feDropShadow dx="0" dy="2" stdDeviation="2.5" flood-color="#0f172a" flood-opacity="0.08"/></filter>
</defs>"""


# ----------------------------------------------------------- marco común
def marco(pestana, subtitulo):
    W = 1600
    s = [f'<rect width="{W}" height="1004" fill="{FONDO}"/>', f'<rect width="{W}" height="72" fill="{NAVY}"/>']
    s.append(t(28, 33, "🧭 Circuito de compras", 21, 700, "#fff"))
    s.append(t(28, 57, subtitulo, 13.5, 400, "#c7d2e6"))
    x = 760
    for clave, txt in (("oficial", "🏛 Oficial TIMBÓ"), ("hospital", "🏥 Hospital (relevamiento)"), ("comparar", "⇆ Comparación")):
        w = 30 + 8.6 * len(txt)
        activo = clave == pestana
        s.append(f'<rect x="{x}" y="18" width="{w}" height="36" rx="10" fill="{"#ffffff" if activo else "none"}" stroke="{"#ffffff" if activo else "#41557d"}"/>')
        s.append(t(x + w / 2, 41, txt, 14.5, 700, NAVY if activo else "#e2e8f0", "middle"))
        x += w + 10
    s.append(f'<rect x="{W - 132}" y="18" width="108" height="36" rx="10" fill="none" stroke="#41557d"/>')
    s.append(t(W - 78, 41, "✎ Editar", 14.5, 700, "#e2e8f0", "middle"))
    return s


# ------------------------------------------------------- panel izquierdo
def panel_general(sel, modo="oficial"):
    s = []
    X0, W0 = 24, 640
    s.append(f'<rect x="{X0}" y="90" width="{W0}" height="896" rx="18" fill="#fff" stroke="{LINEA}" stroke-width="1.5"/>')
    s.append(t(X0 + 24, 124, "Vista general", 20, 700, TXT))
    s.append(t(X0 + 24, 146, "Tocá una etapa para ver el detalle", 13.5, 400, SUB))
    cx = X0 + W0 / 2
    y = 166
    s.append(f'<rect x="{cx - 150}" y="{y}" width="300" height="40" rx="20" fill="{OK_F}" stroke="{OK}" stroke-width="1.8"/>')
    s.append(t(cx, y + 26, "▶  Inicio", 16, 700, OK, "middle"))
    y += 40
    alto, sep = 60, 12
    for num, nombre, sub, ids in ETAPAS:
        s.append(f'<path d="M{cx},{y + 2} L{cx},{y + sep - 2}" stroke="#94a3b8" stroke-width="2" marker-end="url(#p)"/>')
        y += sep
        x, w = X0 + 24, W0 - 48
        es = num == sel
        decision = num == "2"
        borde = VIOLETA if decision else ("#2456c7" if es else LINEA)
        fondo = VIOLETA_F if decision else ("#f5f8ff" if es else "#fff")
        s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{alto}" rx="14" fill="{fondo}" stroke="{borde}" stroke-width="{3 if es else 1.5}" filter="url(#s)"/>')
        if decision:
            s.append(f'<rect x="{x + 15}" y="{y + 13}" width="34" height="34" rx="6" fill="{VIOLETA}" transform="rotate(45 {x + 32} {y + 30})"/>')
            s.append(t(x + 32, y + 36, num, 16, 700, "#fff", "middle"))
        else:
            s.append(f'<circle cx="{x + 32}" cy="{y + 30}" r="18" fill="{NAVY}"/>' + t(x + 32, y + 36, num, 16, 700, "#fff", "middle"))
        s.append(t(x + 64, y + 26, nombre, 17.5, 700, TXT))
        s.append(t(x + 64, y + 46, sub if not decision else "A · B · C · D — tocá para ver las alternativas", 12.8, 400, VIOLETA if decision else SUB))
        if modo == "oficial":
            u, cu, fu = ubic_etapa(num, ids)
            s.append(chip(x + w - 14, y + 6, u, cu, fu, 11, False, 22, anchor="end")[0])
            c = cuenta(ids) if modo == "oficial" else {}
            pend = sum(v for k, v in c.items() if k in PENDIENTES)
            prop = len(PROPUESTOS.get(num, []))
            if pend:
                s.append(chip(x + w - 14, y + 32, f"? {pend} pendiente{'s' if pend > 1 else ''}", PEND, "#fff", 11, True, 22, anchor="end")[0])
            else:
                s.append(chip(x + w - 14, y + 32, "✔ con fuente", OK, OK_F, 11, False, 22, anchor="end")[0])
            if prop:
                s.append(chip(x + w - 140, y + 32, f"+{prop} a sumar", AZUL, AZUL_F, 11, True, 22, anchor="end")[0])
        else:
            s.append(chip(x + w - 14, y + 22, "Sin relevar", GRIS, GRIS_F, 11.5, True, 22, anchor="end")[0])
        y += alto
    s.append(f'<path d="M{cx},{y + 2} L{cx},{y + sep - 2}" stroke="#94a3b8" stroke-width="2" marker-end="url(#p)"/>')
    y += sep
    s.append(f'<rect x="{cx - 150}" y="{y}" width="300" height="40" rx="12" fill="{NAVY}"/>')
    s.append(t(cx, y + 26, "■  Fin", 16, 700, "#fff", "middle"))
    # Leyenda compacta, fuera del recorrido
    s.append(t(X0 + 24, 974, "✔ documentado   ? pendiente   ◆ decisión   «En TIMBÓ» / «¿Dónde? a relevar» = dónde pasa", 12, 500, SUB))
    return s


# -------------------------------------------------------- panel derecho
def caja_detalle(sub=""):
    X, W = 684, 892
    return X, W, [f'<rect x="{X}" y="90" width="{W}" height="896" rx="18" fill="#fff" stroke="{LINEA}" stroke-width="1.5"/>']


def seccion(s, X, y, icono, titulo):
    s.append(t(X + 28, y, f"{icono}  {titulo}", 15, 700, NAVY))
    s.append(f'<line x1="{X + 28}" y1="{y + 7}" x2="{X + 864}" y2="{y + 7}" stroke="{LINEA}"/>')
    return y + 26


def detalle_etapa7():
    X, W, s = caja_detalle()
    ids = ETAPAS[6][3]
    s.append(f'<rect x="{X}" y="90" width="{W}" height="92" rx="18" fill="{TEAL_F}"/>')
    s.append(f'<rect x="{X}" y="160" width="{W}" height="22" fill="{TEAL_F}"/>')
    s.append(f'<circle cx="{X + 52}" cy="136" r="26" fill="{NAVY}"/>' + t(X + 52, 144, "7", 22, 700, "#fff", "middle"))
    s.append(t(X + 92, 130, "Evaluar y preadjudicar", 24, 700, TXT))
    s.append(t(X + 92, 156, "◀ viene de 6 · Recibir y abrir ofertas      sigue en 8 · Adjudicar ▶", 13, 500, SUB))
    s.append(chip(X + W - 24, 112, "📍 TIMBÓ Compras", TEAL, "#fff", 12.5, False, 28, anchor="end")[0])
    y = 214
    y = seccion(s, X, y, "💡", "Qué se hace")
    s.append(t(X + 28, y, "Los evaluadores analizan las ofertas, piden subsanaciones, aclaraciones o mejoras si hace falta,", 14, 400, TXT))
    s.append(t(X + 28, y + 20, "y firman el informe de preadjudicación, que se publica y notifica a los oferentes.", 14, 400, TXT))
    y += 46
    y = seccion(s, X, y, "👥", "Quién interviene")
    quienes = [("Evaluadores", "Rol de TIMBÓ · al menos 3 (pto 13)", "Quiénes en el hospital: a relevar", TEAL),
               ("Oferente / Proveedor", "Responde subtrámites · puede impugnar", "Rol de TIMBÓ", TEAL),
               ("URC", "Control de lo preadjudicado", "? Si alcanza al hospital: a confirmar", PEND)]
    xq = X + 28
    for nom, a, b, col in quienes:
        s.append(f'<rect x="{xq}" y="{y - 8}" width="272" height="62" rx="12" fill="#fff" stroke="{LINEA}"/>')
        s.append(t(xq + 14, y + 14, nom, 14.5, 700, col))
        s.append(t(xq + 14, y + 32, a, 11, 400, SUB))
        s.append(t(xq + 14, y + 47, b, 11, 600, BEIGE if "relevar" in b else (PEND if "?" in b else SUB)))
        xq += 284
    y += 64
    y = seccion(s, X, y, "☰", "Pasos (9 bloques del circuito oficial)")
    pasos = [
        ("1", "Evaluación de ofertas y preselección", "Evaluadores · pto 10", "documentado", ""),
        ("◆", "¿Hace falta subsanar, aclarar o mejorar?", "Sí → subtrámite · No → informe", "documentado", "dec"),
        ("2", "Subtrámite al proveedor", "Si no responde a tiempo: «descartado» (pto 21)", "documentado", ""),
        ("3", "Informe de preadjudicación", "📄 Digital · firman en orden (pto 22)", "documentado", ""),
        ("4", "Control de la preadjudicación (URC)", "Si aplica · por expediente (SCyGB 03/2026)", "pendiente_confirmacion", ""),
        ("5", "Cronograma de impugnación: publica y notifica", "Evaluador · pto 10", "documentado", ""),
        ("◆", "¿Hay impugnaciones?", "Sí → impugnación · No → etapa 8", "documentado", "dec"),
        ("6", "Impugnación a la preadjudicación", "2 días + garantía (Pliego 5.1)", "documentado", "exc"),
    ]
    for num, tit, sub, est, tipo in pasos:
        col = VIOLETA if tipo == "dec" else (ROJO if tipo == "exc" else NAVY)
        if num == "◆":
            s.append(t(X + 42, y + 5, "◆", 15, 700, VIOLETA, "middle"))
        else:
            s.append(f'<circle cx="{X + 42}" cy="{y}" r="11" fill="{col}"/>' + t(X + 42, y + 4.5, num, 11, 700, "#fff", "middle"))
        s.append(t(X + 62, y + 5, tit, 14, 700, TXT))
        s.append(t(X + 420, y + 5, sub, 12, 400, SUB))
        s.append(chip_estado(X + W - 28, y - 11, est, 10.5))
        y += 26
    s.append(t(X + 62, y + 2, "+1 nota del circuito: lo firmado en TIMBÓ Compras se incorpora solo al expediente (pto 7)", 11.5, 400, SUB))
    y += 24
    y = seccion(s, X, y, "📄", "Documentos")
    s.append(t(X + 28, y, "• Informe de preadjudicación (digital, firmado; va solo al expediente, ptos 7 y 22) · Subtrámites respondidos o descartados (pto 21)", 12.5, 400, TXT))
    y += 26
    y = seccion(s, X, y, "↯", "Si algo sale distinto")
    for linea in ["• El proveedor no responde un subtrámite → queda «descartado» (Circ. UG 7/2026, pto 21)",
                  "• Hay empate → se pide mejora de precios; si siguen iguales, sorteo (Pliego 5.3 · Ley art. 133)  + a sumar",
                  "• Hay impugnación → la resuelve la autoridad junto con la adjudicación (Pliego 5.1)",
                  "• Hay una sola oferta → no impide adjudicar si se ajusta al pliego (Pliego 5.2)  + a sumar"]:
        s.append(t(X + 28, y, linea, 12.8, 400, TXT))
        y += 18
    y += 6
    y = seccion(s, X, y, "📚", "Fuentes oficiales (documento · apartado · página)")
    for f in ["Circular UG TIMBÓ 7/2026 · ptos 10, 13, 20.2, 21 y 22 · págs. 3 a 5   ·   Pliego Único · 5.1 a 5.3 · págs. 36 y 37",
              "Circular SCyGB 03/2026 · «Cronograma de impugnación» · pág. 1   ·   Res. ME 73/2026 · art. 2 · pág. 3"]:
        s.append(t(X + 28, y, "🔗 " + f, 12.8, 600, "#2456c7", "start", 'text-decoration="underline"'))
        y += 19
    y += 4
    c = cuenta(ids)
    partes = [f"{ESTADO[k][0]} {v} {ESTADO[k][1].lower()}" for k, v in c.items()]
    s.append(f'<rect x="{X + 24}" y="{y - 4}" width="{W - 48}" height="52" rx="12" fill="{PEND_F}" stroke="{PEND}" stroke-width="1.4"/>')
    s.append(t(X + 40, y + 18, "Estado: " + "  ·  ".join(partes) + "  (nunca se marca «completa» con pendientes)", 13, 700, TXT))
    s.append(t(X + 40, y + 37, "❓ Para Santa Fe: ¿el control de la URC alcanza a los hospitales?   ❓ Para Compras: ¿quiénes serán los evaluadores?", 12.3, 500, PEND))
    return s


def detalle_decision():
    X, W, s = caja_detalle()
    s.append(f'<rect x="{X}" y="90" width="{W}" height="92" rx="18" fill="{VIOLETA_F}"/>')
    s.append(f'<rect x="{X}" y="160" width="{W}" height="22" fill="{VIOLETA_F}"/>')
    s.append(f'<rect x="{X + 34}" y="118" width="36" height="36" rx="6" fill="{VIOLETA}" transform="rotate(45 {X + 52} {136})"/>' + t(X + 52, 142, "2", 18, 700, "#fff", "middle"))
    s.append(t(X + 92, 130, "¿Qué procedimiento corresponde?", 24, 700, TXT))
    s.append(t(X + 92, 156, "Regla general: licitación o concurso público. Las demás son excepciones (Ley 12.510, art. 116 · pág. 40)", 13, 500, SUB))
    alts = [
        ("A", "Contratación directa", "Hasta $5.850.000 (montos 2026) o por causal: especialización, exclusividad, entre",
         "organismos públicos, reparación, compra en origen (art. 116 c, ap. 1 y 4 a 8).",
         "📍 Expediente electrónico (Circ. UG 2/2025) · no va por TIMBÓ Compras", "◌ Pasos: pendientes de documentación", PEND, True),
        ("B", "Directa por urgencia o desierto", "Urgencia o emergencia imprevisible, o licitación desierta o fracasada",
         "(art. 116 c, ap. 2 y 3). Mínimo 3 proveedores invitados; consultas e impugnaciones se pueden acortar.",
         "📍 TIMBÓ Compras (Circ. UG 8/2026, arts. 3 y 4) · sigue en la etapa 3", "✔ Documentado", OK, False),
        ("C", "Licitación o concurso, de simple sobre", "Privado: hasta $58.500.000 · Público: más de $58.500.000 (Circ. SCyGB 01/2026).",
         "Licitación si se elige por precio; concurso si pesan factores no económicos (art. 118).",
         "📍 TIMBÓ Compras, obligatorio en Salud desde el 1/4/2026 (Circ. UG 3/2026) · camino principal", "✔ Documentado", OK, False),
        ("D", "Etapa múltiple", "Cuando la complejidad, el monto o la prestación lo justifican.",
         "Ofertas en sobres de papel; actas y adjudicación como Documentos Oficiales.",
         "📍 Expediente + Documentos Oficiales (Circ. UG 8/2026, arts. 5 a 8) · sigue en la etapa 8", "✔ Documentado", OK, False),
    ]
    y = 204
    for letra, tit, l1, l2, donde, estado, col, punt in alts:
        principal = letra == "C"
        s.append(f'<rect x="{X + 24}" y="{y}" width="{W - 48}" height="148" rx="14" fill="#fff" stroke="{VIOLETA}" stroke-width="{3 if principal else 1.5}" filter="url(#s)"/>')
        s.append(f'<circle cx="{X + 58}" cy="{y + 34}" r="20" fill="{VIOLETA}"/>' + t(X + 58, y + 41, letra, 18, 700, "#fff", "middle"))
        s.append(t(X + 92, y + 34, tit, 18, 700, TXT))
        if principal:
            s.append(chip(X + 92 + 10 * len(tit) + 14, y + 17, "camino principal", VIOLETA, VIOLETA_F, 11.5, False, 24)[0])
        s.append(t(X + 92, y + 62, l1, 13.2, 400, TXT))
        s.append(t(X + 92, y + 81, l2, 13.2, 400, TXT))
        s.append(t(X + 92, y + 106, donde, 13, 600, TEAL))
        s.append(chip(X + 92, y + 116, estado, col, PEND_F if punt else OK_F, 11.5, punt, 22)[0])
        s.append(chip(X + W - 48, y + 112, "Ver recorrido ›", VIOLETA, "#fff", 13, False, 28, anchor="end")[0])
        y += 160
    s.append(t(X + 28, y + 10, "Las 4 alternativas son los bloques A, B, C y D actuales; sus montos salen de la tabla de rangos (Circ. SCyGB 01/2026).", 12.5, 400, SUB))
    return s


def detalle_comparacion():
    X, W, s = caja_detalle()
    s.append(t(X + 28, 128, "⇆ Comparación · etapa 7 · Evaluar y preadjudicar", 22, 700, TXT))
    s.append(t(X + 28, 152, "Neutral: una diferencia no es un error. Cada fila la marcás vos en la reunión.", 13, 400, SUB))
    col1, col2 = X + 28, X + 456
    s.append(f'<rect x="{col1}" y="170" width="412" height="40" rx="10" fill="{TEAL_F}"/>' + t(col1 + 16, 196, "🏛 Oficial TIMBÓ (con fuente)", 15, 700, TEAL))
    s.append(f'<rect x="{col2}" y="170" width="412" height="40" rx="10" fill="{BEIGE_F}"/>' + t(col2 + 16, 196, "🏥 Hospital (lo que cuenta Compras)", 15, 700, BEIGE))
    filas = [("Evaluación de ofertas y preselección", "documentado"),
             ("¿Subsanar, aclarar o mejorar?", "documentado"),
             ("Informe de preadjudicación", "documentado"),
             ("Control de la URC", "pendiente_confirmacion"),
             ("Cronograma de impugnación", "documentado"),
             ("Impugnación a la preadjudicación", "documentado")]
    y = 226
    for tit, est in filas:
        s.append(f'<rect x="{col1}" y="{y}" width="412" height="52" rx="10" fill="#fff" stroke="{LINEA}"/>')
        s.append(t(col1 + 14, y + 22, tit, 13.5, 700, TXT))
        s.append(chip_estado(col1 + 14, y + 27, est, 10, anchor="start"))
        s.append(f'<rect x="{col2}" y="{y}" width="412" height="52" rx="10" fill="#fff" stroke="{LINEA}" stroke-dasharray="5 4"/>')
        s.append(t(col2 + 14, y + 22, "Sin relevar todavía", 13.5, 600, GRIS))
        s.append(t(col2 + 14, y + 41, "+ Registrar cómo lo hacen", 12, 700, "#2456c7"))
        y += 60
    y += 14
    s.append(t(X + 28, y, "Relación de cada paso del hospital con el oficial (la elegís vos):", 14, 700, TXT))
    y += 14
    x = X + 28
    for txt, col in (("Coincide", OK), ("Se hace distinto", PEND), ("Se hace fuera de TIMBÓ", BEIGE), ("Sin paso oficial equivalente", GRIS)):
        c, w = chip(x, y, txt, col, "#fff", 12, False, 26)
        s.append(c)
        x += w + 10
    y += 50
    s.append(f'<rect x="{X + 24}" y="{y}" width="{W - 48}" height="150" rx="12" fill="{PEND_F}" stroke="{PEND}" stroke-width="1.4"/>')
    s.append(t(X + 40, y + 26, "❓ Consultas pendientes para Santa Fe (salen de los comentarios del circuito oficial)", 14, 700, PEND))
    for k, q in enumerate(["¿La Res. ME 73/2026 y la Circ. SCyGB 03/2026 (controles de la URC) alcanzan a los hospitales?",
                           "¿En qué momento revisa la Jurisdicción comitente: antes o después del Supervisor?",
                           "Después de un rechazo del Supervisor, ¿el formulario vuelve al Gestor?",
                           "¿Uno o dos diarios para la publicación? (Dec. 1104/16 vs. nota modelo de la Circ. 04/2026)"]):
        s.append(t(X + 40, y + 52 + 22 * k, "• " + q, 12.8, 400, TXT))
    s.append(t(X + 28, 966, "El circuito del hospital tiene hoy 0 pasos: se completa en la reunión, nunca por suposición.", 12.5, 600, SUB))
    return s


def svg(partes):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1004" width="1600" height="1004" {FUENTE_SVG}>{defs()}'
            + "\n".join(partes) + "</svg>")


# ------------------------------------------------------------- auditoría
def html(imagenes):
    filas_b = []
    for n in OF["nodos"]:
        etapa = ETAPA_DE.get(n["id"], "⚠ SIN ETAPA")
        nombre = next((e[1] for e in ETAPAS if e[0] == etapa), "")
        filas_b.append(f"<tr><td><code>{h(n['id'])}</code></td><td>{h(n['titulo'])}</td><td>{h(n['tipo'])}</td>"
                       f"<td>{h(n['estado'].replace('_', ' '))}</td><td>{len(n['fuentes'])}</td>"
                       f"<td>{h(etapa + (' · ' + nombre if nombre else ''))}</td></tr>")
    sin_etapa = [n["id"] for n in OF["nodos"] if n["id"] not in ETAPA_DE]
    filas_f = []
    dentro = conector = 0
    tit = {n["id"]: n["titulo"] for n in OF["nodos"]}
    for f in OF["flechas"]:
        a, b = ETAPA_DE.get(f["desde"]), ETAPA_DE.get(f["hasta"])
        if a == b:
            como, dentro = f"dentro de la etapa {a}", dentro + 1
        else:
            como, conector = f"conector «viene de {a} / sigue en {b}»", conector + 1
        filas_f.append(f"<tr><td><code>{h(f['id'])}</code></td><td>{h(tit[f['desde']])}</td><td>{h(tit[f['hasta']])}</td>"
                       f"<td>{h(f['etiqueta'])}</td><td>{h(f['tipo'])}</td><td>{h(como)}</td></tr>")
    filas_h = "".join(f"<tr><td><b>{h(c)}</b></td><td>{h(tit_)}</td><td>{h(antes)}</td><td>{h(que)}</td><td>{h(fte)}</td><td>{h(acc)}</td><td>{h(et)}</td></tr>"
                      for c, tit_, antes, que, fte, acc, et in HALLAZGOS)
    filas_p = "".join(f"<tr><td>{h(num)}</td><td>{h(tit_)}</td><td>{h(est.replace('_', ' '))}</td><td>{h(ref)}</td></tr>"
                      for num, lst in PROPUESTOS.items() for tit_, est, ref in lst)
    figs = "".join(f"<section><h2>{h(titulo)}</h2><div class='fig'>{s}</div></section>" for titulo, s in imagenes)
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Circuito de compras · propuesta v3</title>
<style>
body{{margin:0;background:#f6f7f9;color:#1f2937;font:15px/1.5 "Segoe UI",system-ui,Arial,sans-serif}}
main{{max-width:1240px;margin:0 auto;padding:24px 16px 60px}}
section{{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:20px 22px;margin-top:18px}}
h1{{margin:0 0 4px;font-size:26px}} h2{{margin:0 0 8px;font-size:20px}}
.fig{{border:1px solid #e2e8f0;border-radius:12px;overflow:auto}} .fig svg{{display:block;width:100%;height:auto;min-width:1000px}}
table{{border-collapse:collapse;width:100%;font-size:13.5px}} th,td{{border-bottom:1px solid #e2e8f0;padding:6px 8px;text-align:left;vertical-align:top}}
th{{background:#f8fafc}} code{{font-size:12px}} .tabla{{overflow-x:auto}} .ok{{color:#1b7a45;font-weight:700}}
</style></head><body><main>
<h1>Circuito de compras · propuesta v3 (circuito oficial)</h1>
<p>Maqueta y auditoría. <b>Nada está aplicado en el Centro.</b> Los hallazgos de fidelidad salen de releer las fuentes oficiales el 18/11/2026; los bloques nuevos son propuestas a aprobar.</p>
{figs}
<section><h2>1. Hallazgos de fidelidad (revisión de fuentes del 18/11/2026)</h2>
<div class="tabla"><table><thead><tr><th></th><th>Hallazgo</th><th>Hoy en el circuito</th><th>Qué dice la fuente</th><th>Fuente (apartado · página)</th><th>Propuesta</th><th>Etapa</th></tr></thead><tbody>{filas_h}</tbody></table></div></section>
<section><h2>2. Bloques propuestos (no aplicados)</h2>
<div class="tabla"><table><thead><tr><th>Etapa</th><th>Bloque</th><th>Estado</th><th>Hallazgo</th></tr></thead><tbody>{filas_p}</tbody></table></div></section>
<section><h2>3. Auditoría de bloques del circuito oficial</h2>
<p class="ok">{len(OF['nodos'])} bloques originales · {len(OF['nodos']) - len(sin_etapa)} con etapa asignada{'' if not sin_etapa else ' · sin etapa: ' + ', '.join(sin_etapa)}. Ninguno se borra ni cambia de texto, estado o fuentes.</p>
<div class="tabla"><table><thead><tr><th>Id</th><th>Bloque</th><th>Tipo</th><th>Estado</th><th>Fuentes</th><th>Etapa</th></tr></thead><tbody>{''.join(filas_b)}</tbody></table></div></section>
<section><h2>4. Auditoría de flechas</h2>
<p class="ok">{len(OF['flechas'])} flechas originales, todas conservadas: {dentro} dentro de una etapa y {conector} como conector entre etapas.</p>
<div class="tabla"><table><thead><tr><th>Id</th><th>Desde</th><th>Hasta</th><th>Condición</th><th>Tipo</th><th>Cómo se ve</th></tr></thead><tbody>{''.join(filas_f)}</tbody></table></div></section>
<section><h2>5. Los otros dos circuitos</h2>
<p>El <b>circuito del hospital</b> (hoy vacío) usa las mismas 9 etapas como guía, sin ningún paso cargado. El <b>gráfico de la reunión</b> queda como está (sus 35 bloques y 42 flechas no se tocan); su trazabilidad está en la propuesta v2. La <b>comparación</b> une los dos sin mezclarlos: cada paso del hospital se relaciona con un paso oficial solo cuando lo marcás vos.</p></section>
</main></body></html>"""


if __name__ == "__main__":
    vistas = [
        ("A · Vista general + detalle de una etapa (7 · Evaluar y preadjudicar)",
         svg(marco("oficial", "Circuito oficial de TIMBÓ · solo con fuente") + panel_general("7") + detalle_etapa7())),
        ("B · Alternativas: se abren al tocar «¿Qué procedimiento corresponde?»",
         svg(marco("oficial", "Circuito oficial de TIMBÓ · solo con fuente") + panel_general("2") + detalle_decision())),
        ("C · Hospital y comparación",
         svg(marco("comparar", "El circuito del hospital se completa en la reunión · la comparación no juzga") + panel_general("7", "hospital") + detalle_comparacion())),
    ]
    for i, (titulo, s) in enumerate(vistas):
        (AQUI / f"v3_{'ABC'[i]}.svg").write_text(s, encoding="utf-8")
    (AQUI / "propuesta_v3.html").write_text(html(vistas), encoding="utf-8")
    print("bloques", len(OF["nodos"]), "· flechas", len(OF["flechas"]), "· sin etapa", [n["id"] for n in OF["nodos"] if n["id"] not in ETAPA_DE])
