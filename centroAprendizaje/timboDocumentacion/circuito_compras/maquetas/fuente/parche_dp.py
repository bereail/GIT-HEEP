from pathlib import Path
p = Path(__file__).with_name("dos_paneles.py")
s = p.read_text(encoding="utf-8")
rep = [
# marcador: pendientes + «quién / dónde: a relevar» (sale de los datos)
('''        cuenta = resumen_etapa(ids)
        pend = sum(v for k, v in cuenta.items() if k != "documentado" and k != "confirmado_equipo")
        if pend:
            c, _ = chip(x + w - 150, y + 28, f"? {pend} pendiente{'s' if pend > 1 else ''}", PEND, "#fff", 12, True, 20, 132)
        else:
            c, _ = chip(x + w - 150, y + 28, "✔ documentada", OK, OK_F, 12, False, 20, 132)
        out.append(c)''',
'''        cuenta = resumen_etapa(ids)
        pend = sum(v for k, v in cuenta.items() if k != "documentado" and k != "confirmado_equipo")
        relevar = [i for i in ids if N[i]["tipo"] in ("actividad", "verificacion", "autorizacion")
                   and ((not N[i]["responsables"] and not N[i].get("sector")) or N[i]["sistema"] == "sin_definir")]
        if pend:
            c, _ = chip(x + w - 150, y + 28, f"? {pend} pendiente{'s' if pend > 1 else ''}", PEND, "#fff", 12, True, 20, 132)
        else:
            c, _ = chip(x + w - 150, y + 28, "✔ con fuente", OK, OK_F, 12, False, 20, 132)
        out.append(c)
        if relevar:
            c, _ = chip(x + w - 290, y + 28, "👤 quién/dónde: a relevar", BEIGE, "#fff", 11, True, 20, 132)
            out.append(c)'''),
# leyenda en dos renglones
('''    for clave in ("documentado", "confirmado_equipo", "pendiente_documentacion", "pendiente_confirmacion", "sin_respaldo"):
        ic, txt, col, punt = ESTADO[clave]
        s.append(t(x, ly + 8, ic, 13, 700, col)); s.append(t(x + 16, ly + 8, txt.replace("Pendiente de ", "Pend. "), 12, 500, TXT))
        x += 30 + 6.4 * len(txt.replace("Pendiente de ", "Pend. "))''',
'''    x, ly = X0 + 18, ly + 22
    for clave in ("documentado", "confirmado_equipo", "pendiente_documentacion", "pendiente_confirmacion", "sin_respaldo"):
        ic, txt, col, punt = ESTADO[clave]
        s.append(t(x, ly + 8, ic, 13, 700, col)); s.append(t(x + 16, ly + 8, txt, 12, 500, TXT))
        x += 34 + 6.3 * len(txt)'''),
('''    ly = 950''', '''    ly = 936'''),
# estado de la etapa: contado de los datos
('''    s.append(t(X + 42, y + 26, "Estado de la etapa:  ✔ 5 pasos documentados   ·   ? 1 pendiente de confirmación", 14.5, 700, TXT))''',
'''    cuenta = resumen_etapa(m.ETAPAS[5][3])
    partes = [f"{ESTADO[k][0]} {v} {ESTADO[k][1].lower()}" for k, v in cuenta.items()]
    s.append(t(X + 42, y + 26, "Estado de la etapa:  " + "   ·   ".join(partes), 14.5, 700, TXT))'''),
]
for a, b in rep:
    assert a in s, a[:60]
    s = s.replace(a, b, 1)
p.write_text(s, encoding="utf-8")
print("ok")
