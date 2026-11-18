"""Maqueta conceptual en dos paneles (según la referencia visual de la
usuaria), con los DATOS REALES del gráfico actual. No es la implementación.

    python fuente/dos_paneles.py
"""
from pathlib import Path
from xml.sax.saxutils import escape

import maquetas as m

AQUI = Path(__file__).resolve().parent.parent
N = m.NODOS
FUENTE = 'font-family="Segoe UI, system-ui, Arial, sans-serif"'
TXT, SUB, LINEA = "#1f2937", "#5b6472", "#e2e8f0"
AZUL, AZUL_F = "#1f5fbf", "#e8f0fd"           # en TIMBÓ
BEIGE, BEIGE_F = "#9a6a1c", "#fdf3e1"         # fuera del sistema
VIOLETA, VIOLETA_F = "#6a4fd6", "#f1edff"     # decisión
OK, OK_F = "#1b7a45", "#e7f5ec"
PEND = "#b85400"
ROJO = "#b42318"
NAVY = "#14284b"

# Estado → (ícono, texto, color, punteado)
ESTADO = {
    "documentado": ("✔", "Documentado", OK, False),
    "confirmado_equipo": ("👥", "Confirmado por el equipo", "#2456c7", False),
    "pendiente_documentacion": ("◌", "Pendiente de documentación", PEND, True),
    "pendiente_confirmacion": ("?", "Pendiente de confirmación", PEND, True),
    "sin_respaldo": ("⚠", "Sin respaldo", ROJO, False),
}


def t(x, y, s, size=15, weight=400, color=TXT, anchor="start", extra=""):
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color}" '
            f'text-anchor="{anchor}" {extra}>{escape(s)}</text>')


def chip(x, y, texto, color, fondo, size=13, punteado=False, alto=24, ancho=None):
    w = ancho or (18 + size * 0.58 * len(texto))
    d = ' stroke-dasharray="4 3"' if punteado else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{alto}" rx="{alto / 2}" fill="{fondo}" stroke="{color}" stroke-width="1.5"{d}/>'
            + t(x + w / 2, y + alto / 2 + size * 0.36, texto, size, 700, color, "middle")), w


def chip_estado(x, y, estado, size=13):
    ic, txt, col, punt = ESTADO[estado]
    fondo = OK_F if estado == "documentado" else "#ffffff"
    return chip(x, y, f"{ic} {txt}", col, fondo, size, punt)


def resumen_etapa(ids):
    """Cuenta estados de los pasos de una etapa (nunca la declara completa)."""
    cuenta = {}
    for i in ids:
        cuenta[N[i]["estado"]] = cuenta.get(N[i]["estado"], 0) + 1
    return cuenta


# ------------------------------------------------------- panel izquierdo
def panel_general(sel="6"):
    s = []
    X0, W0 = 24, 800
    s.append(f'<rect x="{X0}" y="96" width="{W0}" height="890" rx="16" fill="#fff" stroke="{LINEA}" stroke-width="1.5"/>')
    s.append(f'<path d="M{X0},112 a16,16 0 0 1 16,-16 h200 v54 h-216 z" fill="{NAVY}"/>')
    s.append(t(X0 + 20, 132, "🗺  Vista general", 20, 700, "#fff"))
    s.append(t(X0 + 240, 130, "El recorrido de una compra, de punta a punta", 15, 400, SUB))

    cx = X0 + W0 / 2
    # Inicio
    s.append(f'<rect x="{cx - 170}" y="164" width="340" height="44" rx="22" fill="{OK_F}" stroke="{OK}" stroke-width="2"/>')
    s.append(t(cx, 192, "▶  INICIO · Necesidad de compra", 16, 700, OK, "middle"))

    def flecha(x1, y1, x2, y2, col="#475569"):
        return f'<path d="M{x1},{y1} L{x2},{y2 - 6}" stroke="{col}" stroke-width="2.4" fill="none" marker-end="url(#p)"/>'

    def etapa(y, num, nombre, sub, donde, ids, w=560):
        x = cx - w / 2
        es = num == sel
        col, fondo, txt_donde = (AZUL, AZUL_F, "En TIMBÓ") if donde == "timbo" else (BEIGE, BEIGE_F, "Fuera de TIMBÓ")
        if donde == "mixto":
            col, fondo, txt_donde = AZUL, AZUL_F, "TIMBÓ + fuera"
        if donde == "sindef":
            col, fondo, txt_donde = "#5b6472", "#f1f3f6", "¿Dónde? a relevar"
        out = []
        if es:
            out.append(f'<rect x="{x - 6}" y="{y - 6}" width="{w + 12}" height="64" rx="16" fill="none" stroke="#2456c7" stroke-width="3"/>')
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="52" rx="12" fill="{fondo}" stroke="{col}" stroke-width="1.8"/>')
        out.append(f'<circle cx="{x + 28}" cy="{y + 26}" r="15" fill="{NAVY}"/>' + t(x + 28, y + 31.5, num, 15, 700, "#fff", "middle"))
        out.append(t(x + 54, y + 23, nombre, 16, 700, TXT))
        out.append(t(x + 54, y + 42, sub, 12.5, 400, SUB))
        c, wc = chip(x + w - 170, y + 6, txt_donde, col, "#ffffff", 12, alto=20, ancho=156)
        out.append(c)
        # marcador de pendientes (nunca se oculta)
        cuenta = resumen_etapa(ids)
        pend = sum(v for k, v in cuenta.items() if k != "documentado" and k != "confirmado_equipo")
        relevar = [i for i in ids if N[i]["tipo"] in ("actividad", "verificacion", "autorizacion")
                   and ((not N[i]["responsables"] and not N[i].get("sector")) or N[i]["sistema"] == "sin_definir")]
        partes = []
        if pend:
            partes.append(f"? {pend} pend.")
        if relevar:
            partes.append("👤 a relevar")
        if partes:
            c, _ = chip(x + w - 170, y + 28, " · ".join(partes), PEND, "#fff", 11.5, True, 20, 156)
        else:
            c, _ = chip(x + w - 170, y + 28, "✔ con fuente", OK, OK_F, 11.5, False, 20, 156)
        out.append(c)
        return out

    y = 220
    s.append(flecha(cx, 208, cx, y))
    s += etapa(y, "1", "Pedido", "Solicitud y documentación técnica", "fuera", m.ETAPAS[0][3])
    s.append(flecha(cx, y + 52, cx, y + 68)); y += 68
    s += etapa(y, "2", "Expediente y presupuesto", "Inicio del expediente y presupuesto", "timbo", m.ETAPAS[1][3])
    s.append(flecha(cx, y + 52, cx, y + 68)); y += 68
    # Decisión 3
    w3 = 600
    s.append(f'<rect x="{cx - w3 / 2}" y="{y}" width="{w3}" height="54" rx="12" fill="{VIOLETA_F}" stroke="{VIOLETA}" stroke-width="2"/>')
    s.append(f'<circle cx="{cx - w3 / 2 + 28}" cy="{y + 27}" r="15" fill="{NAVY}"/>' + t(cx - w3 / 2 + 28, y + 32.5, "3", 15, 700, "#fff", "middle"))
    s.append(t(cx - w3 / 2 + 54, y + 24, "◆  ¿Qué procedimiento corresponde?", 16, 700, TXT))
    s.append(t(cx - w3 / 2 + 54, y + 43, "Según monto y causal · Ley 12.510 art. 116 · montos 2026 (Circ. SCyGB 01/2026)", 12, 400, SUB))
    y += 54
    # Ramas A B C D
    ramas = [
        ("A", "Directa", "monto o causal", "Por expediente", "? pasos sin documentar", True, "beige"),
        ("B", "Urgencia o desierto", "art. 116 c, ap. 2 y 3", "TIMBÓ Compras", "se une en la etapa 4", False, "timbo"),
        ("C", "Licitación o concurso", "público o privado · simple sobre", "TIMBÓ Compras", "camino principal → 4", False, "timbo"),
        ("D", "Etapa múltiple", "sobres en papel", "Expediente + papel", "se une en la etapa 7", False, "mixto"),
    ]
    bw, gap = 180, 14
    total = 4 * bw + 3 * gap
    xs = [cx - total / 2 + i * (bw + gap) for i in range(4)]
    yb = y + 34
    s.append(f'<path d="M{cx},{y} L{cx},{y + 14} M{xs[0] + bw / 2},{y + 14} L{xs[3] + bw / 2},{y + 14}" stroke="{VIOLETA}" stroke-width="2.4" fill="none"/>')
    for (letra, nom, sub, donde, nota, pend, tipo), x in zip(ramas, xs):
        s.append(f'<path d="M{x + bw / 2},{y + 14} L{x + bw / 2},{yb - 6}" stroke="{VIOLETA}" stroke-width="2.4" fill="none" marker-end="url(#pv)"/>')
        principal = letra == "C"
        s.append(f'<rect x="{x}" y="{yb}" width="{bw}" height="92" rx="12" fill="#fff" stroke="{VIOLETA}" stroke-width="{3 if principal else 1.8}"/>')
        s.append(f'<circle cx="{x + 20}" cy="{yb + 20}" r="12" fill="{VIOLETA}"/>' + t(x + 20, yb + 25, letra, 13, 700, "#fff", "middle"))
        s.append(t(x + 38, yb + 25, nom, 13.5, 700, TXT))
        s.append(t(x + 12, yb + 45, sub, 11.5, 400, SUB))
        s.append(t(x + 12, yb + 63, "📍 " + donde, 11.5, 600, AZUL if tipo != "beige" else BEIGE))
        s.append(t(x + 12, yb + 81, nota, 11.5, 700, PEND if pend else (VIOLETA if principal else SUB)))
    y = yb + 92
    # retorno de B y C al camino principal (A queda pendiente, D salta a 7)
    s.append(f'<path d="M{xs[1] + bw / 2},{y} L{xs[1] + bw / 2},{y + 16} L{cx},{y + 16} M{xs[2] + bw / 2},{y} L{xs[2] + bw / 2},{y + 16} L{cx},{y + 16} M{cx},{y + 16} L{cx},{y + 30}" stroke="#475569" stroke-width="2.4" fill="none" marker-end="url(#p)"/>')
    y += 36
    s += etapa(y, "4", "Pliego y aprobación", "Gestor · Supervisor · acto de la autoridad", "timbo", m.ETAPAS[3][3])
    s.append(flecha(cx, y + 52, cx, y + 64)); y += 64
    s += etapa(y, "5", "Publicación y ofertas", "Publicación, portal y ofertas", "mixto", m.ETAPAS[4][3])
    s.append(flecha(cx, y + 52, cx, y + 64)); y += 64
    s += etapa(y, "6", "Evaluación", "Evaluadores · subsanación · preadjudicación", "timbo", m.ETAPAS[5][3])
    s.append(flecha(cx, y + 52, cx, y + 64)); y += 64
    y7 = y
    s += etapa(y, "7", "Adjudicación", "Acto de la autoridad · Tribunal de Cuentas", "timbo", m.ETAPAS[6][3])
    # D salta a 7 (por la derecha)
    xd = xs[3] + bw
    s.append(f'<path d="M{xd},{yb + 46} L{xd + 22},{yb + 46} L{xd + 22},{y7 + 26} L{cx + 286},{y7 + 26}" stroke="{VIOLETA}" stroke-width="2" stroke-dasharray="6 4" fill="none" marker-end="url(#pv)"/>')
    s.append(flecha(cx, y + 52, cx, y + 64)); y += 64
    s += etapa(y, "8", "Recepción, factura y pago", "Reglas del Pliego Único 6.9 a 6.13", "sindef", m.ETAPAS[7][3])
    s.append(flecha(cx, y + 52, cx, y + 64)); y += 64
    s.append(f'<rect x="{cx - 120}" y="{y}" width="240" height="40" rx="10" fill="{NAVY}"/>')
    s.append(t(cx, y + 26, "■  FIN", 16, 700, "#fff", "middle"))
    # leyenda
    ly = 958
    s.append(f'<line x1="{X0 + 16}" y1="{ly - 18}" x2="{X0 + W0 - 16}" y2="{ly - 18}" stroke="{LINEA}"/>')
    x = X0 + 18
    for col, fondo, txt in ((AZUL, AZUL_F, "En TIMBÓ"), (BEIGE, BEIGE_F, "Fuera del sistema"), (VIOLETA, VIOLETA_F, "Decisión")):
        s.append(f'<rect x="{x}" y="{ly - 4}" width="18" height="14" rx="4" fill="{fondo}" stroke="{col}" stroke-width="1.5"/>')
        s.append(t(x + 24, ly + 8, txt, 12.5, 600, TXT)); x += 36 + 7.2 * len(txt)
    x, ly = X0 + 18, ly + 22
    for clave in ("documentado", "confirmado_equipo", "pendiente_documentacion", "pendiente_confirmacion", "sin_respaldo"):
        ic, txt, col, punt = ESTADO[clave]
        s.append(t(x, ly + 8, ic, 13, 700, col)); s.append(t(x + 16, ly + 8, txt, 12, 500, TXT))
        x += 34 + 6.3 * len(txt)
    return s


# -------------------------------------------------------- panel derecho
def panel_detalle():
    s = []
    X, W = 844, 732
    s.append(f'<rect x="{X}" y="96" width="{W}" height="890" rx="16" fill="#fff" stroke="{LINEA}" stroke-width="1.5"/>')
    s.append(f'<path d="M{X},112 a16,16 0 0 1 16,-16 h{W - 32} a16,16 0 0 1 16,16 v38 h-{W} z" fill="{NAVY}"/>')
    s.append(t(X + 20, 132, "🔍  Vista de detalle", 20, 700, "#fff"))
    s.append(t(X + 230, 131, "Etapa seleccionada", 14, 400, "#c7d2e6"))
    s.append(f'<rect x="{X + W - 210}" y="108" width="190" height="30" rx="15" fill="none" stroke="#c7d2e6" stroke-width="1.5"/>')
    s.append(t(X + W - 115, 128, "✎ Editar esta etapa", 14, 700, "#ffffff", "middle"))
    # cabecera de la etapa
    s.append(f'<rect x="{X}" y="150" width="{W}" height="78" fill="{AZUL_F}"/>')
    s.append(f'<circle cx="{X + 44}" cy="189" r="24" fill="{NAVY}"/>' + t(X + 44, 197, "6", 22, 700, "#fff", "middle"))
    s.append(t(X + 82, 184, "Evaluación y preadjudicación", 22, 700, TXT))
    s.append(t(X + 82, 208, "◀ viene de 5 · Publicación y ofertas      sigue en 7 · Adjudicación ▶", 13, 500, SUB))
    c, _ = chip(X + W - 150, 176, "En TIMBÓ Compras", AZUL, "#fff", 12.5, alto=26, ancho=132); s.append(c)

    y = 262
    s.append(t(X + 24, y, "👥  ¿Quién lo hace?", 17, 700, TXT))
    y += 14
    quienes = [
        ("Evaluadores", "Rol de TIMBÓ · al menos 3 · quiénes: a relevar", "rol"),
        ("Oferente / Proveedor", "Responde subsanaciones · puede impugnar", "rol"),
        ("URC (si aplica)", "Control de lo preadjudicado · ? a confirmar", "ext"),
    ]
    xq = X + 24
    for nom, sub, tipo in quienes:
        col = AZUL if tipo == "rol" else BEIGE
        s.append(f'<rect x="{xq}" y="{y}" width="222" height="58" rx="10" fill="#fff" stroke="{LINEA}"/>')
        s.append(t(xq + 12, y + 24, ("👤 " if tipo == "rol" else "🏛 ") + nom, 14, 700, col))
        s.append(t(xq + 12, y + 44, sub, 10.8, 400, SUB))
        xq += 234
    y += 92
    s.append(t(X + 24, y, "☰  Pasos de la etapa", 17, 700, TXT))
    y += 14
    pasos = [
        ("14", "Evaluación de ofertas", "Evaluadores · Circ. UG 7/2026, pto 10", "documentado", None),
        ("◆", "¿Hace falta subsanar, aclarar o mejorar?", "Sí → 15  ·  No → 16", None, "dec"),
        ("15", "Subsanación, aclaración o mejora", "Si el proveedor no responde a tiempo: «descartado» (pto 21)", "documentado", None),
        ("16", "Informe de preadjudicación", "📄 Digital, lo firman los evaluadores en orden (pto 22)", "documentado", None),
        ("", "Control de la preadjudicación (URC)", "Si aplica al hospital · por expediente (Circ. SCyGB 03/2026)", "pendiente_confirmacion", "ext"),
        ("◆", "¿Se presentan impugnaciones?", "Sí → 17  ·  No → sigue en 7", None, "dec"),
        ("17", "Impugnaciones  ↯ excepción", "2 días + garantía · se resuelven con la adjudicación", "documentado", "exc"),
    ]
    for num, tit, sub, est, tipo in pasos:
        alto = 50
        borde = VIOLETA if tipo == "dec" else (ROJO if tipo == "exc" else (BEIGE if tipo == "ext" else LINEA))
        fondo = VIOLETA_F if tipo == "dec" else "#fff"
        dash = ' stroke-dasharray="5 3"' if est and ESTADO[est][3] else ""
        s.append(f'<rect x="{X + 24}" y="{y}" width="{W - 48}" height="{alto}" rx="10" fill="{fondo}" stroke="{borde}" stroke-width="1.6"{dash}/>')
        if num and num != "◆":
            s.append(f'<circle cx="{X + 48}" cy="{y + 25}" r="13" fill="{NAVY}"/>' + t(X + 48, y + 30, num, 12, 700, "#fff", "middle"))
        elif num == "◆":
            s.append(t(X + 48, y + 31, "◆", 18, 700, VIOLETA, "middle"))
        else:
            s.append(t(X + 48, y + 31, "🏛", 15, 400, BEIGE, "middle"))
        s.append(t(X + 72, y + 22, tit, 14.5, 700, TXT))
        s.append(t(X + 72, y + 40, sub, 11.8, 400, SUB))
        if est:
            c, wc = chip_estado(0, 0, est, 11.5)
            ancho = 18 + 11.5 * 0.58 * len(ESTADO[est][0] + " " + ESTADO[est][1])
            c, _ = chip_estado(X + W - 36 - ancho, y + 13, est, 11.5)
            s.append(c)
        else:
            for i, (lab, col) in enumerate((("Sí", VIOLETA), ("No", SUB))):
                c, _ = chip(X + W - 140 + i * 56, y + 13, lab, col, "#fff", 12, ancho=46); s.append(c)
        y += alto + 8
    y += 12
    s.append(t(X + 24, y, "📚  Documentación y fuentes", 17, 700, TXT))
    y += 12
    fuentes = [
        "Circular UG TIMBÓ 7/2026 · puntos 10, 20, 21 y 22 (págs. 3 a 5)",
        "Pliego Único (Dec. 287/2026) · 5.1 Preadjudicación e impugnaciones (págs. 36 y 37)",
        "Circular SCyGB 03/2026 · «Cronograma de impugnación» · Res. ME 73/2026, art. 2",
    ]
    s.append(f'<rect x="{X + 24}" y="{y}" width="{W - 48}" height="{24 * len(fuentes) + 18}" rx="10" fill="#f8fafc" stroke="{LINEA}"/>')
    for i, f in enumerate(fuentes):
        s.append(t(X + 40, y + 28 + i * 24, "🔗 " + f, 13, 500, "#2456c7", "start", 'text-decoration="underline"'))
    y += 24 * len(fuentes) + 34
    s.append(f'<rect x="{X + 24}" y="{y}" width="{W - 48}" height="64" rx="12" fill="#fff8ef" stroke="{PEND}" stroke-width="1.6"/>')
    cuenta = resumen_etapa(m.ETAPAS[5][3])
    partes = [f"{ESTADO[k][0]} {v} {ESTADO[k][1].lower()}" for k, v in cuenta.items()]
    s.append(t(X + 42, y + 26, "Estado de la etapa:  " + "   ·   ".join(partes), 14.5, 700, TXT))
    s.append(t(X + 42, y + 48, "Pendiente: si el control de la URC alcanza al hospital. No se marca «completa» mientras haya pendientes.", 12, 400, SUB))
    return s


def maqueta():
    W, H = 1600, 1004
    s = [f'<rect width="{W}" height="{H}" fill="#f3f5f9"/>']
    # Barra del Centro (la del panel existente, simplificada)
    s.append(f'<rect width="{W}" height="76" fill="{NAVY}"/>')
    s.append(t(28, 34, "🧭 Gestión de procesos · Centro de Aprendizaje", 19, 700, "#fff"))
    s.append(t(28, 58, "Flujo de compras (gráfico de la reunión) · circuito oficial de TIMBÓ, solo con fuente", 14, 400, "#c7d2e6"))
    x = 960
    for txt, activo in (("👁 Ver (reunión)", True), ("✎ Editar", False), ("🕘 Historial", False), ("🖨 Informe", False)):
        w = 24 + 8.4 * len(txt)
        s.append(f'<rect x="{x}" y="22" width="{w}" height="34" rx="9" fill="{"#2456c7" if activo else "none"}" stroke="{"#2456c7" if activo else "#41557d"}"/>')
        s.append(t(x + w / 2, 44, txt, 14, 700, "#fff", "middle"))
        x += w + 10
    s += panel_general()
    s += panel_detalle()
    defs = f"""<defs>
<marker id="p" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#475569"/></marker>
<marker id="pv" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{VIOLETA}"/></marker>
</defs>"""
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" {FUENTE}>{defs}' + "\n".join(s) + "</svg>"


if __name__ == "__main__":
    (AQUI / "maqueta_dos_paneles.svg").write_text(maqueta(), encoding="utf-8")
    print("ok")
