"""Maqueta v2 (dos paneles) con las decisiones de la usuaria del 18/11:

1. El bloque vacío «Actividad» se elimina del circuito activo (con auditoría).
2. El paso 9 suma la salida «Rechazado» → bloque «pendiente de documentación»
   sin conexión hacia adelante.
3. Ubicación: «¿Dónde? a relevar» en todo paso cuya fuente no diga dónde se
   hace.
4. Los circuitos no se fusionan: el detalle del circuito oficial se muestra
   como «información relacionada» en las etapas 5 y 8.

Todo se aplica sobre una COPIA de los datos (no se toca la base). Salen las
imágenes por etapa, y propuesta_rediseno.html con las tablas de trazabilidad.

    python fuente/v2.py
"""
import copy
import json
from html import escape as h
from pathlib import Path
from xml.sax.saxutils import escape

AQUI = Path(__file__).resolve().parent.parent
DATOS = json.loads((AQUI / "datos_actuales.json").read_text(encoding="utf-8"))
ORIGINAL = DATOS["reunion"]
OFICIAL = {n["id"]: n for n in DATOS["oficial"]["nodos"]}
DOCS = DATOS["docs"]
RANGOS = DATOS["rangos"]

# ------------------------------------------------- cambios planificados
VACIO = "nmwliiyt94s9d"
RELEVAR = {  # id → por qué la ubicación no está confirmada
    "r01": "ninguna fuente dice dónde se registra la necesidad",
    "r02": "ninguna fuente dice dónde se hace la solicitud",
    "r03": "la Res. 292/2026 cubre el alta de artículos, no dónde se arma la documentación",
    "r05": "la Res. ME 73/2026, art. 4, no dice en qué sistema se imputa",
    "r05b": "no hay fuente sobre el área presupuestaria del hospital",
    "rA2": "el bloque no tiene fuente propia",
    "r09a": "el Supervisor lo carga en TIMBÓ Compras (pto 10), pero no dice dónde se firma",
    "r20": "el Pliego Único no dice en qué sistema",
    "r21": "el Pliego Único no dice en qué sistema",
}
RECHAZO = {
    "id": "r09r", "tipo": "pendiente", "titulo": "Rechazado: qué sigue", "estado": "pendiente_documentacion",
    "sistema": "compras", "soporte": "sin_definir", "responsables": [], "sector": "",
    "descripcion": "La Circular UG 7/2026 dice que el Supervisor «aprueba o rechaza» los formularios. Qué pasa "
                   "después de un rechazo no está documentado: falta confirmarlo.",
    "fuentes": [f for f in ORIGINAL["nodos"] if f["id"] == "r09"][0]["fuentes"][:1],  # misma cita del Supervisor
}
FLECHA_RECHAZO = {"id": "g43", "desde": "r09", "hasta": "r09r", "etiqueta": "Rechazado", "tipo": "rechazo", "rango": None}


def planificado():
    c = copy.deepcopy(ORIGINAL)
    c["nodos"] = [n for n in c["nodos"] if n["id"] != VACIO]
    for n in c["nodos"]:
        if n["id"] in RELEVAR:
            n["sistema"] = "sin_definir"
    c["nodos"].append(copy.deepcopy(RECHAZO))
    c["flechas"].append(dict(FLECHA_RECHAZO))
    return c


PLAN = planificado()
N = {n["id"]: n for n in PLAN["nodos"]}

ETAPAS = [
    ("1", "Pedido", "Solicitud y documentación técnica", ["r02", "r03"]),
    ("2", "Expediente y presupuesto", "Inicio del expediente y presupuesto", ["r04", "r05", "r05b"]),
    ("3", "¿Qué procedimiento?", "Según monto y causal", ["r06", "rA", "rA2", "rB", "rC", "rD"]),
    ("4", "Pliego y aprobación", "Gestor · Supervisor · acto de la autoridad", ["r07", "r08", "r09", "r09r", "r09u", "r09a"]),
    ("5", "Publicación y ofertas", "Publicación, portal y ofertas", ["r10", "r10p", "r11", "r12", "r13"]),
    ("6", "Evaluación", "Evaluadores · subsanación · preadjudicación", ["r14", "r15", "r16", "r16u", "r17"]),
    ("7", "Adjudicación", "Acto de la autoridad · Tribunal de Cuentas", ["r18", "r18s", "r19"]),
    ("8", "Recepción, factura y pago", "Reglas del Pliego Único 6.9 a 6.13", ["r20", "r21"]),
]
ETAPA_DE = {i: e[0] for e in ETAPAS for i in e[3]}
ETAPA_DE.update({"r01": "Inicio", "r99": "Fin", "rObs": "Transversal"})
NOMBRE_ETAPA = {e[0]: e[1] for e in ETAPAS}
# Información relacionada del circuito oficial (se consulta, no se mezcla)
RELACIONADA = {
    "5": ["o20e", "o21d"],
    "8": ["o33", "o34", "o34d", "o35", "o36", "o36e"],
}

# ------------------------------------------------------------- estilo
FUENTE_SVG = 'font-family="Segoe UI, system-ui, Arial, sans-serif"'
TXT, SUB, LINEA = "#1f2937", "#5b6472", "#e2e8f0"
AZUL, AZUL_F = "#1f5fbf", "#e8f0fd"
BEIGE, BEIGE_F = "#9a6a1c", "#fdf3e1"
GRIS, GRIS_F = "#5b6472", "#f1f3f6"
VIOLETA, VIOLETA_F = "#6a4fd6", "#f1edff"
OK, OK_F = "#1b7a45", "#e7f5ec"
PEND, ROJO, NAVY = "#b85400", "#b42318", "#14284b"
ESTADO = {
    "documentado": ("✔", "Documentado", OK, False),
    "confirmado_equipo": ("👥", "Confirmado por el equipo", "#2456c7", False),
    "pendiente_documentacion": ("◌", "Pendiente de documentación", PEND, True),
    "pendiente_confirmacion": ("?", "Pendiente de confirmación", PEND, True),
    "sin_respaldo": ("⚠", "Sin respaldo", ROJO, False),
}
PENDIENTES = {"pendiente_confirmacion", "pendiente_documentacion", "sin_respaldo", "en_revision", "observado"}
UBIC = {
    "expediente": ("📍 Expediente TIMBÓ", AZUL, AZUL_F),
    "compras": ("📍 TIMBÓ Compras", AZUL, AZUL_F),
    "fuera": ("📍 Fuera de TIMBÓ", BEIGE, BEIGE_F),
    "otro_sistema": ("📍 Otro sistema", BEIGE, BEIGE_F),
    "sin_definir": ("📍 ¿Dónde? a relevar", GRIS, GRIS_F),
}
CORTO = {
    "circ-ug-7-2026": "Circ. UG 7/2026", "circ-ug-8-2026": "Circ. UG 8/2026", "circ-ug-3-2026": "Circ. UG 3/2026",
    "circ-ug-2-2025": "Circ. UG 2/2025", "circ-ug-9-2026": "Circ. UG 9/2026", "circ-scygb-1-2026": "Circ. SCyGB 01/2026",
    "circ-scygb-3-2026": "Circ. SCyGB 03/2026", "circ-scygb-4-2026": "Circ. SCyGB 04/2026", "res-me-73-2026": "Res. ME 73/2026",
    "ley-12510": "Ley 12.510", "pliego-unico-2026": "Pliego Único", "res-scygb-292-2026": "Res. SCyGB 292/2026",
}


def t(x, y, s, size=15, weight=400, color=TXT, anchor="start", extra=""):
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color}" '
            f'text-anchor="{anchor}" {extra}>{escape(s)}</text>')


def chip(x, y, texto, color, fondo, size=12, punteado=False, alto=22, ancho=None):
    w = ancho or (18 + size * 0.6 * len(texto))
    d = ' stroke-dasharray="4 3"' if punteado else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{alto}" rx="{alto / 2}" fill="{fondo}" stroke="{color}" stroke-width="1.5"{d}/>'
            + t(x + w / 2, y + alto / 2 + size * 0.36, texto, size, 700, color, "middle")), w


def recortar(s, n):
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def cuenta_estados(ids):
    c = {}
    for i in ids:
        c[N[i]["estado"]] = c.get(N[i]["estado"], 0) + 1
    return c


def a_relevar(ids):
    """Pasos con quién o dónde sin confirmar (calculado de los datos)."""
    out = []
    for i in ids:
        n = N[i]
        if n["tipo"] in ("decision", "condicion"):
            continue
        sin_quien = n["tipo"] in ("actividad", "verificacion", "autorizacion") and not n["responsables"] and not n.get("sector")
        if sin_quien or n["sistema"] == "sin_definir":
            out.append(i)
    return out


def ubicacion_etapa(ids):
    sis = {N[i]["sistema"] for i in ids if N[i]["tipo"] not in ("decision", "condicion")}
    if sis == {"sin_definir"}:
        return "¿Dónde? a relevar", GRIS, GRIS_F
    if "sin_definir" in sis:
        return "¿Dónde? a relevar (en parte)", GRIS, GRIS_F
    if sis <= {"expediente", "compras"}:
        return "En TIMBÓ", AZUL, AZUL_F
    return "TIMBÓ + fuera", AZUL, AZUL_F


def defs():
    return f"""<defs>
<marker id="p" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#475569"/></marker>
<marker id="pv" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{VIOLETA}"/></marker>
</defs>"""


# ------------------------------------------------------- panel izquierdo
def panel_general(sel):
    s = []
    X0, W0 = 24, 800
    s.append(f'<rect x="{X0}" y="96" width="{W0}" height="890" rx="16" fill="#fff" stroke="{LINEA}" stroke-width="1.5"/>')
    s.append(f'<path d="M{X0},112 a16,16 0 0 1 16,-16 h200 v54 h-216 z" fill="{NAVY}"/>')
    s.append(t(X0 + 20, 132, "🗺  Vista general", 20, 700, "#fff"))
    s.append(t(X0 + 240, 130, "El recorrido de una compra, de punta a punta", 15, 400, SUB))
    cx = X0 + W0 / 2
    s.append(f'<rect x="{cx - 170}" y="164" width="340" height="44" rx="22" fill="{OK_F}" stroke="{OK}" stroke-width="2"/>')
    s.append(t(cx, 192, "▶  INICIO · Necesidad de compra", 16, 700, OK, "middle"))

    def flecha(y1, y2):
        return f'<path d="M{cx},{y1} L{cx},{y2 - 6}" stroke="#475569" stroke-width="2.4" fill="none" marker-end="url(#p)"/>'

    def etapa(y, num, w=560):
        _, nombre, sub, ids = next(e for e in ETAPAS if e[0] == num)
        x = cx - w / 2
        txt_u, col, fondo = ubicacion_etapa(ids)
        out = []
        if num == sel:
            out.append(f'<rect x="{x - 6}" y="{y - 6}" width="{w + 12}" height="64" rx="16" fill="none" stroke="#2456c7" stroke-width="3"/>')
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="52" rx="12" fill="{fondo}" stroke="{col}" stroke-width="1.8"/>')
        out.append(f'<circle cx="{x + 28}" cy="{y + 26}" r="15" fill="{NAVY}"/>' + t(x + 28, y + 31.5, num, 15, 700, "#fff", "middle"))
        out.append(t(x + 54, y + 23, nombre, 16, 700, TXT))
        out.append(t(x + 54, y + 42, sub, 12.5, 400, SUB))
        c, _ = chip(x + w - 186, y + 6, txt_u, col, "#fff", 11, alto=20, ancho=172)
        out.append(c)
        cuenta = cuenta_estados(ids)
        pend = sum(v for k, v in cuenta.items() if k in PENDIENTES)
        partes = ([f"? {pend} pend."] if pend else []) + (["👤 a relevar"] if a_relevar(ids) else [])
        if partes:
            c, _ = chip(x + w - 186, y + 28, " · ".join(partes), PEND, "#fff", 11.5, True, 20, 172)
        else:
            c, _ = chip(x + w - 186, y + 28, "✔ con fuente", OK, OK_F, 11.5, False, 20, 172)
        out.append(c)
        return out

    y = 220
    s.append(flecha(208, y))
    for num in ("1", "2"):
        s += etapa(y, num)
        s.append(flecha(y + 52, y + 68))
        y += 68
    w3 = 600
    s.append(f'<rect x="{cx - w3 / 2}" y="{y}" width="{w3}" height="54" rx="12" fill="{VIOLETA_F}" stroke="{VIOLETA}" stroke-width="{3 if sel == "3" else 2}"/>')
    s.append(f'<circle cx="{cx - w3 / 2 + 28}" cy="{y + 27}" r="15" fill="{NAVY}"/>' + t(cx - w3 / 2 + 28, y + 32.5, "3", 15, 700, "#fff", "middle"))
    s.append(t(cx - w3 / 2 + 54, y + 24, "◆  ¿Qué procedimiento corresponde?", 16, 700, TXT))
    s.append(t(cx - w3 / 2 + 54, y + 43, "Según monto y causal · Ley 12.510 art. 116 · montos 2026 (Circ. SCyGB 01/2026)", 12, 400, SUB))
    y += 54
    ramas = [
        ("A", "Directa", "monto o causal", "📍 Expediente TIMBÓ", "? pasos sin documentar", True),
        ("B", "Urgencia o desierto", "art. 116 c, ap. 2 y 3", "📍 TIMBÓ Compras", "se une en la etapa 4", False),
        ("C", "Licitación o concurso", "público o privado · simple sobre", "📍 TIMBÓ Compras", "camino principal → 4", False),
        ("D", "Etapa múltiple", "sobres en papel", "📍 Expediente + papel", "se une en la etapa 7", False),
    ]
    bw, gap = 180, 14
    total = 4 * bw + 3 * gap
    xs = [cx - total / 2 + i * (bw + gap) for i in range(4)]
    yb = y + 34
    s.append(f'<path d="M{cx},{y} L{cx},{y + 14} M{xs[0] + bw / 2},{y + 14} L{xs[3] + bw / 2},{y + 14}" stroke="{VIOLETA}" stroke-width="2.4" fill="none"/>')
    for (letra, nom, sub, donde, nota, pend), x in zip(ramas, xs):
        s.append(f'<path d="M{x + bw / 2},{y + 14} L{x + bw / 2},{yb - 6}" stroke="{VIOLETA}" stroke-width="2.4" fill="none" marker-end="url(#pv)"/>')
        principal = letra == "C"
        s.append(f'<rect x="{x}" y="{yb}" width="{bw}" height="92" rx="12" fill="#fff" stroke="{VIOLETA}" stroke-width="{3 if principal else 1.8}"/>')
        s.append(f'<circle cx="{x + 20}" cy="{yb + 20}" r="12" fill="{VIOLETA}"/>' + t(x + 20, yb + 25, letra, 13, 700, "#fff", "middle"))
        s.append(t(x + 38, yb + 25, nom, 13.5, 700, TXT))
        s.append(t(x + 12, yb + 45, sub, 11.5, 400, SUB))
        s.append(t(x + 12, yb + 63, donde, 11.5, 600, AZUL))
        s.append(t(x + 12, yb + 81, nota, 11.5, 700, PEND if pend else (VIOLETA if principal else SUB)))
    y = yb + 92
    s.append(f'<path d="M{xs[1] + bw / 2},{y} L{xs[1] + bw / 2},{y + 16} L{cx},{y + 16} M{xs[2] + bw / 2},{y} L{xs[2] + bw / 2},{y + 16} L{cx},{y + 16} M{cx},{y + 16} L{cx},{y + 30}" stroke="#475569" stroke-width="2.4" fill="none" marker-end="url(#p)"/>')
    y += 36
    y7 = None
    for num in ("4", "5", "6", "7", "8"):
        if num == "7":
            y7 = y
        s += etapa(y, num)
        s.append(flecha(y + 52, y + 64))
        y += 64
    xd = xs[3] + bw
    s.append(f'<path d="M{xd},{yb + 46} L{xd + 22},{yb + 46} L{xd + 22},{y7 + 26} L{cx + 286},{y7 + 26}" stroke="{VIOLETA}" stroke-width="2" stroke-dasharray="6 4" fill="none" marker-end="url(#pv)"/>')
    s.append(f'<rect x="{cx - 120}" y="{y}" width="240" height="40" rx="10" fill="{NAVY}"/>')
    s.append(t(cx, y + 26, "■  FIN", 16, 700, "#fff", "middle"))
    ly = 958
    s.append(f'<line x1="{X0 + 16}" y1="{ly - 18}" x2="{X0 + W0 - 16}" y2="{ly - 18}" stroke="{LINEA}"/>')
    x = X0 + 18
    for col, fondo, txt in ((AZUL, AZUL_F, "En TIMBÓ"), (BEIGE, BEIGE_F, "Fuera de TIMBÓ"), (GRIS, GRIS_F, "¿Dónde? a relevar"), (VIOLETA, VIOLETA_F, "Decisión")):
        s.append(f'<rect x="{x}" y="{ly - 4}" width="18" height="14" rx="4" fill="{fondo}" stroke="{col}" stroke-width="1.5"/>')
        s.append(t(x + 24, ly + 8, txt, 12.5, 600, TXT))
        x += 36 + 7.2 * len(txt)
    x, ly = X0 + 18, ly + 22
    for clave in ("documentado", "confirmado_equipo", "pendiente_documentacion", "pendiente_confirmacion", "sin_respaldo"):
        ic, txt, col, _ = ESTADO[clave]
        s.append(t(x, ly + 8, ic, 13, 700, col))
        s.append(t(x + 16, ly + 8, txt, 12, 500, TXT))
        x += 34 + 6.3 * len(txt)
    return s


# -------------------------------------------------------- panel derecho
def salidas(i):
    out = []
    for f in PLAN["flechas"]:
        if f["desde"] != i:
            continue
        destino = N.get(f["hasta"], {}).get("titulo", "?")
        etiqueta = f["etiqueta"] or (RANGOS.get(str(f["rango"]), "") if f["rango"] is not None else "")
        e_dest = ETAPA_DE.get(f["hasta"])
        if e_dest != ETAPA_DE.get(i) and e_dest not in (None, "Transversal"):
            destino = f"sigue en {e_dest}" if e_dest in NOMBRE_ETAPA else e_dest
        destino = destino.split(" · ", 1)[1] if destino[:2].strip().isdigit() and " · " in destino else destino
        out.append((recortar(etiqueta, 24) if etiqueta else "", recortar(destino, 24), f["tipo"]))
    orden = {"Aprobado": 0, "Rechazado": 1}
    out.sort(key=lambda x: orden.get(x[0], 2))
    return out


def resumen_quien(n):
    if n["responsables"]:
        return recortar(" · ".join(r["quien"] + (" (rol TIMBÓ)" if r["perfil_timbo"] else "") for r in n["responsables"]), 70)
    if n.get("sector"):
        return recortar(n["sector"], 70)
    return "👤 a relevar"


def resumen_fuente(n):
    if not n["fuentes"]:
        return "Sin fuente"
    f = n["fuentes"][0]
    base = CORTO.get(f["doc"], f["doc"]) + (" · " + f["punto"].split(" (")[0] if f["punto"] else "")
    base += (f" · pág. {f['pagina']}" if f.get("pagina") else "")
    extra = len(n["fuentes"]) - 1
    return base + (f" · +{extra}" if extra else "") + ("" if any(x["verificada"] for x in n["fuentes"]) else " · sin verificar")


def panel_detalle(num):
    _, nombre, _, ids = next(e for e in ETAPAS if e[0] == num)
    s = []
    X, W = 844, 732
    s.append(f'<rect x="{X}" y="96" width="{W}" height="890" rx="16" fill="#fff" stroke="{LINEA}" stroke-width="1.5"/>')
    s.append(f'<path d="M{X},112 a16,16 0 0 1 16,-16 h{W - 32} a16,16 0 0 1 16,16 v38 h-{W} z" fill="{NAVY}"/>')
    s.append(t(X + 20, 132, "🔍  Vista de detalle", 20, 700, "#fff"))
    s.append(f'<rect x="{X + W - 210}" y="108" width="190" height="30" rx="15" fill="none" stroke="#c7d2e6" stroke-width="1.5"/>')
    s.append(t(X + W - 115, 128, "✎ Editar esta etapa", 14, 700, "#ffffff", "middle"))
    txt_u, col_u, fondo_u = ubicacion_etapa(ids)
    s.append(f'<rect x="{X}" y="150" width="{W}" height="70" fill="{fondo_u}"/>')
    s.append(f'<circle cx="{X + 44}" cy="185" r="24" fill="{NAVY}"/>' + t(X + 44, 193, num, 22, 700, "#fff", "middle"))
    s.append(t(X + 82, 182, nombre, 22, 700, TXT))
    previa = {"1": "Inicio", "2": "1", "3": "2", "4": "3", "5": "4", "6": "5", "7": "6", "8": "7"}[num]
    sig = {"1": "2", "2": "3", "3": "4", "4": "5", "5": "6", "6": "7", "7": "8", "8": "Fin"}[num]
    s.append(t(X + 82, 205, f"◀ viene de {previa}      sigue en {sig} ▶", 13, 500, SUB))
    c, _ = chip(X + W - 216, 172, txt_u, col_u, "#fff", 12, alto=26, ancho=196)
    s.append(c)
    y = 252
    s.append(t(X + 24, y, "☰  Pasos de la etapa (todos)", 16, 700, TXT))
    y += 10
    for i in ids:
        n = N[i]
        sal = salidas(i)
        con_salidas = len(sal) > 1 or n["tipo"] == "decision" or any(x[2] == "rechazo" for x in sal)
        alto = 92 if con_salidas else 76
        est = n["estado"]
        ic, etxt, ecol, punt = ESTADO.get(est, ESTADO["pendiente_confirmacion"])
        tipo = n["tipo"]
        borde = VIOLETA if tipo in ("decision", "condicion") else (ROJO if tipo in ("excepcion", "error") else (PEND if est in PENDIENTES else LINEA))
        fondo = VIOLETA_F if tipo in ("decision", "condicion") else "#fff"
        d = ' stroke-dasharray="5 3"' if punt else ""
        s.append(f'<rect x="{X + 20}" y="{y}" width="{W - 40}" height="{alto - 6}" rx="10" fill="{fondo}" stroke="{borde}" stroke-width="1.6"{d}/>')
        titulo = n["titulo"]
        numero = titulo.split(" · ")[0] if " · " in titulo else ""
        nombre_p = titulo.split(" · ", 1)[1] if numero else titulo
        if numero:
            s.append(f'<circle cx="{X + 42}" cy="{y + 20}" r="12" fill="{NAVY if tipo not in ("decision", "condicion") else VIOLETA}"/>' + t(X + 42, y + 24.5, numero, 11.5, 700, "#fff", "middle"))
        else:
            sim = {"verificacion": "🔍", "autorizacion": "✍", "pendiente": "?", "excepcion": "↯", "responsable": "👤"}.get(tipo, "•")
            s.append(t(X + 42, y + 25, sim, 15, 700, PEND if tipo == "pendiente" else SUB, "middle"))
        s.append(t(X + 62, y + 21, recortar(nombre_p, 50), 14, 700, TXT))
        c, w_e = chip(0, 0, f"{ic} {etxt}", ecol, "#fff", 10.5, punt, 20)
        c, _ = chip(X + W - 32 - w_e, y + 7, f"{ic} {etxt}", ecol, OK_F if est == "documentado" else "#fff", 10.5, punt, 20)
        s.append(c)
        u_txt, u_col, u_fondo = UBIC[n["sistema"]] if tipo not in ("decision", "condicion") else ("◆ decisión", VIOLETA, VIOLETA_F)
        c, w_u = chip(X + 62, y + 29, u_txt, u_col, u_fondo, 10, False, 18)
        s.append(c)
        s.append(t(X + 70 + w_u, y + 41, recortar(resumen_quien(n), 60), 11, 600, BEIGE if "relevar" in resumen_quien(n) else "#0b5f61"))
        s.append(t(X + 62, y + 62, recortar("📚 " + resumen_fuente(n), 100), 10.8, 400, SUB))
        if con_salidas:
            vistos, partes = set(), []
            for e, dst, tipo_f in sal:
                clave = (e, dst)
                if clave in vistos:
                    continue
                vistos.add(clave)
                partes.append(f"{e} → {dst}" if e else f"→ {dst}")
            s.append(t(X + 62, y + 80, recortar("↳ " + "  ·  ".join(partes), 130), 10.8, 600, VIOLETA))
        if n["tipo"] == "pendiente" and not sal:
            s.append(t(X + W - 36, y + 62, "⛔ sin salida: falta confirmar qué sigue", 11, 700, PEND, "end"))
        y += alto
    rel = RELACIONADA.get(num)
    if rel:
        y += 6
        s.append(f'<rect x="{X + 20}" y="{y}" width="{W - 40}" height="{30 + 19 * len(rel)}" rx="10" fill="#f8fafc" stroke="{AZUL}" stroke-width="1.4" stroke-dasharray="6 3"/>')
        s.append(t(X + 34, y + 21, "🏛 Información relacionada del circuito oficial (no es práctica confirmada del hospital)", 12.5, 700, AZUL))
        for k, oid in enumerate(rel):
            o = OFICIAL[oid]
            ic, etxt, ecol, _ = ESTADO[o["estado"]]
            s.append(t(X + 40, y + 41 + 19 * k, f"{ic} {recortar(o['titulo'], 60)}  ·  {resumen_fuente_ofi(o)}", 11.5, 500, TXT))
        y += 36 + 19 * len(rel)
    else:
        y += 6
    # pendientes y estado (calculados)
    pend = [i for i in ids if N[i]["estado"] in PENDIENTES]
    relev = a_relevar(ids)
    cuenta = cuenta_estados(ids)
    alto_box = 50 + 17 * min(4, len(pend) + (1 if relev else 0))
    s.append(f'<rect x="{X + 20}" y="{y}" width="{W - 40}" height="{alto_box}" rx="12" fill="#fff8ef" stroke="{PEND}" stroke-width="1.6"/>')
    def plural(txt, v):
        if v == 1:
            return txt
        primera, _, resto = txt.partition(" ")
        return primera + "s" + (" " + resto if resto else "")
    partes = [f"{ESTADO[k][0]} {v} {plural(ESTADO[k][1].lower(), v)}" for k, v in cuenta.items() if k in ESTADO]
    s.append(t(X + 36, y + 22, "Estado de la etapa:  " + "  ·  ".join(partes), 13, 700, TXT))
    yy = y + 42
    for i in pend[:3]:
        s.append(t(X + 36, yy, f"{ESTADO[N[i]['estado']][0]} {recortar(N[i]['titulo'], 80)}", 11.5, 500, PEND))
        yy += 17
    if relev:
        s.append(t(X + 36, yy, f"👤📍 A relevar quién o dónde: {recortar(', '.join(N[i]['titulo'].split(' · ')[0] for i in relev), 80)}", 11.5, 500, BEIGE))
    return s


def resumen_fuente_ofi(o):
    if not o["fuentes"]:
        return "sin fuente"
    f = o["fuentes"][0]
    return CORTO.get(f["doc"], f["doc"]) + (" · " + f["punto"].split(" (")[0] if f["punto"] else "")


def maqueta(sel):
    W, H = 1600, 1004
    s = [f'<rect width="{W}" height="{H}" fill="#f3f5f9"/>']
    s.append(f'<rect width="{W}" height="76" fill="{NAVY}"/>')
    s.append(t(28, 34, "🧭 Gestión de procesos · Centro de Aprendizaje", 19, 700, "#fff"))
    s.append(t(28, 58, "Flujo de compras (gráfico de la reunión) · circuito oficial de TIMBÓ, solo con fuente", 14, 400, "#c7d2e6"))
    x = 960
    for txt, activo in (("👁 Ver (reunión)", True), ("✎ Editar", False), ("⇆ Comparar", False), ("🕘 Historial", False)):
        w = 24 + 8.4 * len(txt)
        s.append(f'<rect x="{x}" y="22" width="{w}" height="34" rx="9" fill="{"#2456c7" if activo else "none"}" stroke="{"#2456c7" if activo else "#41557d"}"/>')
        s.append(t(x + w / 2, 44, txt, 14, 700, "#fff", "middle"))
        x += w + 10
    s += panel_general(sel)
    s += panel_detalle(sel)
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" {FUENTE_SVG}>{defs()}' + "\n".join(s) + "</svg>"


# ------------------------------------------------------- trazabilidad
def filas_bloques():
    plan_ids = {n["id"] for n in PLAN["nodos"]}
    filas = []
    for n in ORIGINAL["nodos"]:
        if n["id"] == VACIO:
            cambio = "ELIMINAR del circuito activo (vacío). Queda en la auditoría y en las versiones anteriores."
            etapa = "—"
        elif n["id"] in RELEVAR:
            cambio = f"Ubicación «{n['sistema']}» → «¿Dónde? a relevar»: {RELEVAR[n['id']]}."
            etapa = ETAPA_DE[n["id"]]
        else:
            cambio = "Sin cambios."
            etapa = ETAPA_DE[n["id"]]
        filas.append((n, etapa, cambio, n["id"] in plan_ids))
    filas.append((RECHAZO, "4", "NUEVO: salida «Rechazado» del paso 9, pendiente de documentación, sin conexión hacia adelante.", True))
    return filas


def filas_flechas():
    salida = []
    for f in PLAN["flechas"]:
        a, b = ETAPA_DE.get(f["desde"]), ETAPA_DE.get(f["hasta"])
        como = f"dentro de la etapa {a}" if a == b else f"conector: «sigue en {b}» / «viene de {a}»"
        nuevo = f["id"] == FLECHA_RECHAZO["id"]
        salida.append((f, como + (" · NUEVA" if nuevo else "")))
    return salida


def html(imagenes):
    filas = filas_bloques()
    flechas = filas_flechas()
    titulos = {n["id"]: n["titulo"] for n in ORIGINAL["nodos"]}
    titulos["r09r"] = RECHAZO["titulo"]
    activos = sum(1 for _, _, _, activo in filas if activo)
    sin_etapa = [n["id"] for n, e, _, activo in filas if activo and e not in ETAPA_DE.values() and e not in NOMBRE_ETAPA]
    tr_b = "\n".join(
        f"<tr class='{'baja' if not activo else ('nuevo' if n['id'] == 'r09r' else '')}'><td><code>{h(n['id'])}</code></td><td>{h(n['titulo'])}</td>"
        f"<td>{h(n['tipo'])}</td><td>{h(n['estado'].replace('_', ' '))}</td><td>{len(n['fuentes'])}</td>"
        f"<td>{h(etapa if etapa not in NOMBRE_ETAPA else etapa + ' · ' + NOMBRE_ETAPA[etapa])}</td><td>{h(cambio)}</td></tr>"
        for n, etapa, cambio, activo in filas)
    tr_f = "\n".join(
        f"<tr class='{'nuevo' if 'NUEVA' in como else ''}'><td><code>{h(f['id'])}</code></td><td>{h(titulos.get(f['desde'], '?'))}</td><td>{h(titulos.get(f['hasta'], '?'))}</td>"
        f"<td>{h(f['etiqueta'] or (RANGOS.get(str(f['rango']), '') if f['rango'] is not None else ''))}</td><td>{h(f['tipo'])}</td><td>{h(como)}</td></tr>"
        for f, como in flechas)
    rel = "".join(
        f"<tr><td>{h(num)} · {h(NOMBRE_ETAPA[num])}</td><td><code>{h(oid)}</code></td><td>{h(OFICIAL[oid]['titulo'])}</td>"
        f"<td>{h(OFICIAL[oid]['estado'].replace('_', ' '))}</td><td>{h(resumen_fuente_ofi(OFICIAL[oid]))}</td></tr>"
        for num, ids in RELACIONADA.items() for oid in ids)
    figs = "".join(f"<section><h2>Maqueta · etapa {num} seleccionada</h2><div class='fig'>{svg}</div></section>" for num, svg in imagenes)
    n_orig_b, n_orig_f = len(ORIGINAL["nodos"]), len(ORIGINAL["flechas"])
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Rediseño del circuito de compras · v2</title>
<style>
body{{margin:0;background:#f6f7f9;color:#1f2937;font:15px/1.5 "Segoe UI",system-ui,Arial,sans-serif}}
main{{max-width:1240px;margin:0 auto;padding:24px 16px 60px}}
section{{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:20px 22px;margin-top:18px}}
h1{{margin:0 0 4px;font-size:26px}} h2{{margin:0 0 8px;font-size:20px}}
.fig{{border:1px solid #e2e8f0;border-radius:12px;overflow:auto}} .fig svg{{display:block;width:100%;height:auto;min-width:1000px}}
table{{border-collapse:collapse;width:100%;font-size:13.5px}} th,td{{border-bottom:1px solid #e2e8f0;padding:6px 8px;text-align:left;vertical-align:top}}
th{{background:#f8fafc}} code{{font-size:12px}} .tabla{{overflow-x:auto}}
tr.baja td{{background:#fdeceb;text-decoration:line-through;color:#7f1d1d}} tr.baja td:last-child{{text-decoration:none}}
tr.nuevo td{{background:#eaf0fd}} .ok{{color:#1b7a45;font-weight:700}}
</style></head><body><main>
<h1>Rediseño del circuito de compras · maqueta v2</h1>
<p>Con las decisiones del 18/11: bloque vacío eliminado (con auditoría), salida «Rechazado» del paso 9 pendiente, ubicaciones sin respaldo como «¿Dónde? a relevar», y el circuito oficial solo como información relacionada. <b>Nada de esto está aplicado todavía en el Centro</b>: es una copia.</p>
{figs}
<section><h2>Trazabilidad de bloques</h2>
<p class="ok">Originales: {n_orig_b} · se elimina 1 (vacío) · se agrega 1 (rechazo) · activos después: {activos}. Todos los activos tienen etapa.{'' if not sin_etapa else ' Sin etapa: ' + ', '.join(sin_etapa)}</p>
<div class="tabla"><table><thead><tr><th>Id</th><th>Bloque</th><th>Tipo</th><th>Estado</th><th>Fuentes</th><th>Etapa</th><th>Cambio planificado</th></tr></thead><tbody>{tr_b}</tbody></table></div></section>
<section><h2>Trazabilidad de flechas</h2>
<p class="ok">Originales: {n_orig_f}, todas se conservan · se agrega 1 («Rechazado») · total: {len(flechas)}.</p>
<div class="tabla"><table><thead><tr><th>Id</th><th>Desde</th><th>Hasta</th><th>Condición o monto</th><th>Tipo</th><th>Cómo se ve</th></tr></thead><tbody>{tr_f}</tbody></table></div></section>
<section><h2>Información relacionada del circuito oficial</h2>
<p>Se consulta desde la etapa, con la leyenda «no es práctica confirmada del hospital». No se copia al circuito de la reunión ni al del hospital.</p>
<div class="tabla"><table><thead><tr><th>Etapa</th><th>Id oficial</th><th>Bloque oficial</th><th>Estado</th><th>Fuente</th></tr></thead><tbody>{rel}</tbody></table></div></section>
</main></body></html>"""


if __name__ == "__main__":
    imagenes = []
    for num in ("4", "5", "8"):
        svg = maqueta(num)
        (AQUI / f"v2_etapa_{num}.svg").write_text(svg, encoding="utf-8")
        imagenes.append((num, svg))
    (AQUI / "propuesta_rediseno.html").write_text(html(imagenes), encoding="utf-8")
    print("bloques originales", len(ORIGINAL["nodos"]), "· plan", len(PLAN["nodos"]), "· flechas", len(ORIGINAL["flechas"]), "→", len(PLAN["flechas"]))
