from pathlib import Path
p = Path(__file__).with_name("dos_paneles.py")
s = p.read_text(encoding="utf-8")
rep = [
('''        if pend:
            c, _ = chip(x + w - 150, y + 28, f"? {pend} pendiente{'s' if pend > 1 else ''}", PEND, "#fff", 12, True, 20, 132)
        else:
            c, _ = chip(x + w - 150, y + 28, "✔ con fuente", OK, OK_F, 12, False, 20, 132)
        out.append(c)
        if relevar:
            c, _ = chip(x + w - 290, y + 28, "👤 quién/dónde: a relevar", BEIGE, "#fff", 11, True, 20, 132)
            out.append(c)''',
'''        partes = []
        if pend:
            partes.append(f"? {pend} pend.")
        if relevar:
            partes.append("👤 a relevar")
        if partes:
            c, _ = chip(x + w - 170, y + 28, " · ".join(partes), PEND, "#fff", 11.5, True, 20, 156)
        else:
            c, _ = chip(x + w - 170, y + 28, "✔ con fuente", OK, OK_F, 11.5, False, 20, 156)
        out.append(c)'''),
('''        c, wc = chip(x + w - 150, y + 6, txt_donde, col, "#ffffff", 12, alto=20, ancho=132)''',
 '''        c, wc = chip(x + w - 170, y + 6, txt_donde, col, "#ffffff", 12, alto=20, ancho=156)'''),
('''    ly = 936''', '''    ly = 958'''),
('"Solicitud y documentación técnica · quién: a relevar"', '"Solicitud y documentación técnica"'),
('"Inicio del expediente · presupuesto y autorizaciones"', '"Inicio del expediente y presupuesto"'),
('"Proceso publicado · portal y aviso oficial · ofertas"', '"Publicación, portal y ofertas"'),
('"Pliego Único 6.9 a 6.13 · quién y dónde: a relevar"', '"Reglas del Pliego Único 6.9 a 6.13"'),
('"Acto de la autoridad · vista al Tribunal de Cuentas"', '"Acto de la autoridad · Tribunal de Cuentas"'),
]
for a, b in rep:
    assert a in s, a[:60]
    s = s.replace(a, b, 1)
p.write_text(s, encoding="utf-8")
print("ok")
