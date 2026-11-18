from pathlib import Path
p = Path(__file__).with_name("v2.py")
s = p.read_text(encoding="utf-8")
rep = [
('''        out.append((recortar(etiqueta, 28) if etiqueta else "", recortar(destino.split(" · ")[0] if " · " in destino else destino, 30), f["tipo"]))
    return out''',
 '''        destino = destino.split(" · ", 1)[1] if destino[:2].strip().isdigit() and " · " in destino else destino
        out.append((recortar(etiqueta, 24) if etiqueta else "", recortar(destino, 24), f["tipo"]))
    orden = {"Aprobado": 0, "Rechazado": 1}
    out.sort(key=lambda x: orden.get(x[0], 2))
    return out'''),
('''            s.append(t(X + 62, y + 80, recortar("↳ " + "  ·  ".join(partes), 104), 10.8, 600, VIOLETA))
        y += alto''',
 '''            s.append(t(X + 62, y + 80, recortar("↳ " + "  ·  ".join(partes), 130), 10.8, 600, VIOLETA))
        if n["tipo"] == "pendiente" and not sal:
            s.append(t(X + W - 36, y + 62, "⛔ sin salida: falta confirmar qué sigue", 11, 700, PEND, "end"))
        y += alto'''),
('''        c, _ = chip(x + w - 170, y + 6, txt_u, col, "#fff", 11.5, alto=20, ancho=156)''',
 '''        c, _ = chip(x + w - 186, y + 6, txt_u, col, "#fff", 11, alto=20, ancho=172)'''),
('''            c, _ = chip(x + w - 170, y + 28, " · ".join(partes), PEND, "#fff", 11.5, True, 20, 156)
        else:
            c, _ = chip(x + w - 170, y + 28, "✔ con fuente", OK, OK_F, 11.5, False, 20, 156)''',
 '''            c, _ = chip(x + w - 186, y + 28, " · ".join(partes), PEND, "#fff", 11.5, True, 20, 172)
        else:
            c, _ = chip(x + w - 186, y + 28, "✔ con fuente", OK, OK_F, 11.5, False, 20, 172)'''),
('''    c, _ = chip(X + W - 176, 172, txt_u, col_u, "#fff", 12, alto=26, ancho=156)''',
 '''    c, _ = chip(X + W - 216, 172, txt_u, col_u, "#fff", 12, alto=26, ancho=196)'''),
]
for a, b in rep:
    assert a in s, a[:70]
    s = s.replace(a, b, 1)
p.write_text(s, encoding="utf-8")
print("ok")
