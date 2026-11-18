from pathlib import Path
p = Path(__file__).with_name("v2.py")
s = p.read_text(encoding="utf-8")
rep = [
# ubicación de etapa: mixta → «(en parte)»
('''    sis = {N[i]["sistema"] for i in ids if N[i]["tipo"] not in ("decision", "condicion")}
    if "sin_definir" in sis:
        return "¿Dónde? a relevar", GRIS, GRIS_F''',
 '''    sis = {N[i]["sistema"] for i in ids if N[i]["tipo"] not in ("decision", "condicion")}
    if sis == {"sin_definir"}:
        return "¿Dónde? a relevar", GRIS, GRIS_F
    if "sin_definir" in sis:
        return "¿Dónde? a relevar (en parte)", GRIS, GRIS_F'''),
# filas del detalle: alto variable, renglones separados
('''    alto = 66 if len(ids) <= 5 else 58
    for i in ids:
        n = N[i]''',
 '''    for i in ids:
        n = N[i]
        sal = salidas(i)
        con_salidas = len(sal) > 1 or n["tipo"] == "decision" or any(x[2] == "rechazo" for x in sal)
        alto = 92 if con_salidas else 76'''),
('''        s.append(t(X + 70 + w_u, y + 41, recortar(resumen_quien(n), 52), 11, 600, BEIGE if "relevar" in resumen_quien(n) else "#0b5f61"))
        sal = salidas(i)
        linea2 = "📚 " + resumen_fuente(n)
        if len(sal) > 1 or tipo in ("decision",) or any(x[2] in ("rechazo",) for x in sal):
            linea2 = "↳ " + "  ·  ".join(f"{e} → {dst}" if e else f"→ {dst}" for e, dst, _ in sal)
        s.append(t(X + 62, y + alto - 12, recortar(linea2, 100), 10.8, 400, SUB))
        y += alto''',
 '''        s.append(t(X + 70 + w_u, y + 41, recortar(resumen_quien(n), 60), 11, 600, BEIGE if "relevar" in resumen_quien(n) else "#0b5f61"))
        s.append(t(X + 62, y + 62, recortar("📚 " + resumen_fuente(n), 100), 10.8, 400, SUB))
        if con_salidas:
            vistos, partes = set(), []
            for e, dst, tipo_f in sal:
                clave = (e, dst)
                if clave in vistos:
                    continue
                vistos.add(clave)
                partes.append(f"{e} → {dst}" if e else f"→ {dst}")
            s.append(t(X + 62, y + 80, recortar("↳ " + "  ·  ".join(partes), 104), 10.8, 600, VIOLETA))
        y += alto'''),
('''        s.append(t(X + 62, y + 20, recortar(nombre_p, 46), 14, 700, TXT))''',
 '''        s.append(t(X + 62, y + 21, recortar(nombre_p, 50), 14, 700, TXT))'''),
('''        c, _ = chip(X + W - 32 - w_e, y + 8, f"{ic} {etxt}"''', '''        c, _ = chip(X + W - 32 - w_e, y + 7, f"{ic} {etxt}"'''),
('''        c, w_u = chip(X + 62, y + 28, u_txt, u_col, u_fondo, 10, False, 18)''',
 '''        c, w_u = chip(X + 62, y + 29, u_txt, u_col, u_fondo, 10, False, 18)'''),
]
for a, b in rep:
    assert a in s, a[:70]
    s = s.replace(a, b, 1)
p.write_text(s, encoding="utf-8")
print("ok")
