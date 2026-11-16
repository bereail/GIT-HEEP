"""Diagrama de flujo (SVG) de qué camino sigue una compra: rombos de decisión,
cajas de destino y flechas, armado desde algoritmo.json. Solo para el panel."""
import textwrap

ANCHO = 1120
CX = 230                    # eje de los rombos
ROMBO_W, ROMBO_H = 160, 66  # medio ancho y media altura del rombo
BUS = 440                   # línea vertical que reparte las opciones
CAJA_X, CAJA_W, CAJA_H, SEP = 700, 360, 68, 12
COLECTOR = ANCHO - 24       # línea que junta todos los caminos hacia el final
SISTEMAS = {"expediente": "📁 Expediente electrónico", "compras": "🛒 TIMBÓ Compras",
            "organismo": "🏛️ Otro organismo", "externo": "↗ Fuera del sistema"}


def _lineas(texto, ancho):
    return textwrap.wrap(texto, ancho) or [""]


def armar(alg):
    nodos = alg["nodos"]
    letra = {}
    for r in alg["ramas"]:
        for n in r.get("nodos") or [r["nodo"]]:
            letra[n] = r["letra"]
    # Decisiones en orden, siguiendo la opción que lleva a otra decisión.
    decisiones, actual = [], nodos[alg["inicio"]].get("siguiente")
    while actual and nodos[actual]["tipo"] == "decision":
        decisiones.append(actual)
        sigue = [o["va"] for o in nodos[actual]["opciones"] if nodos[o["va"]]["tipo"] == "decision"]
        actual = sigue[0] if sigue else None

    y = 20
    inicio = {"x": CX - 150, "y": y, "w": 300, "h": 46, "texto": _lineas(nodos[alg["inicio"]]["titulo"], 38)}
    y += 46 + 40
    rombos, cajas, flechas, etiquetas, buses = [], [], [], [], []
    flechas.append((CX, inicio["y"] + 46, CX, y))
    for d in decisiones:
        n = nodos[d]
        opciones = [o for o in n["opciones"] if nodos[o["va"]]["tipo"] != "decision"]
        alto_cajas = len(opciones) * CAJA_H + (len(opciones) - 1) * SEP
        bloque = max(2 * ROMBO_H, alto_cajas)
        cy = y + bloque / 2
        rombos.append({"cx": CX, "cy": cy, "texto": _lineas(n["titulo"], 22), "id": d})
        flechas.append((CX + ROMBO_W, cy, BUS, cy))
        y0 = cy - alto_cajas / 2
        centros = []
        for j, o in enumerate(opciones):
            destino = nodos[o["va"]]
            by = y0 + j * (CAJA_H + SEP)
            centro = by + CAJA_H / 2
            centros.append(centro)
            cajas.append({"x": CAJA_X, "y": by, "w": CAJA_W, "h": CAJA_H, "id": o["va"], "letra": letra.get(o["va"], ""),
                          "texto": _lineas(destino["titulo"], 40)[:2], "sistema": destino["sistema"],
                          "sistema_txt": SISTEMAS.get(destino["sistema"], ""), "pendiente": destino.get("estado") == "pendiente"})
            flechas.append((BUS, centro, CAJA_X, centro))
            etiquetas.append({"x": BUS + 12, "y": centro, "texto": _lineas(o["texto"], 40)[:3]})
        buses.append((BUS, min(centros + [cy]), BUS, max(centros + [cy])))
        y += bloque + 70
    # Rombo a rombo: la opción "No".
    for a, b in zip(rombos, rombos[1:]):
        flechas.append((CX, a["cy"] + ROMBO_H, CX, b["cy"] - ROMBO_H))
        etiquetas.append({"x": CX + 10, "y": (a["cy"] + ROMBO_H + b["cy"] - ROMBO_H) / 2, "texto": ["No"], "no": True})
    # Todos los caminos terminan en la etapa contractual.
    fin_y = y
    fin = {"x": 380, "y": fin_y, "w": 520, "h": 50, "texto": _lineas(nodos["fin-contractual"]["titulo"], 60)}
    colector = [(c["x"] + c["w"], c["y"] + c["h"] / 2, COLECTOR, c["y"] + c["h"] / 2) for c in cajas]
    colector.append((COLECTOR, cajas[0]["y"] + CAJA_H / 2, COLECTOR, fin_y + 25))
    flechas.append((COLECTOR, fin_y + 25, fin["x"] + fin["w"], fin_y + 25))
    return {"ancho": ANCHO, "alto": fin_y + 50 + 30, "inicio": inicio, "rombos": rombos, "cajas": cajas,
            "flechas": flechas, "etiquetas": etiquetas, "buses": buses, "colector": colector,
            "fin": fin, "rombo_w": ROMBO_W, "rombo_h": ROMBO_H}
