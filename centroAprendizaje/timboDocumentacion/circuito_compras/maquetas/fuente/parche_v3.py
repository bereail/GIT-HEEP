from pathlib import Path
p = Path(__file__).with_name("v3.py")
s = p.read_text(encoding="utf-8")
rep = [
("    alto, sep = 66, 16\n", "    alto, sep = 60, 12\n"),
('''        s.append(t(x + 64, y + 29, nombre, 17.5, 700, TXT))
        s.append(t(x + 64, y + 50, sub''', '''        s.append(t(x + 64, y + 26, nombre, 17.5, 700, TXT))
        s.append(t(x + 64, y + 46, sub'''),
('''            s.append(chip(x + w - 14, y + 9, u, cu, fu, 11, False, 22, anchor="end")[0])''',
 '''            s.append(chip(x + w - 14, y + 6, u, cu, fu, 11, False, 22, anchor="end")[0])'''),
('''                s.append(chip(x + w - 14, y + 36, f"? {pend}''', '''                s.append(chip(x + w - 14, y + 32, f"? {pend}'''),
('''                s.append(chip(x + w - 14, y + 36, "✔ con fuente"''', '''                s.append(chip(x + w - 14, y + 32, "✔ con fuente"'''),
('''                s.append(chip(x + w - 140, y + 36, f"+{prop} a sumar"''', '''                s.append(chip(x + w - 140, y + 32, f"+{prop} a sumar"'''),
('''            s.append(f'<rect x="{x + 14}" y="{y + 15}" width="36" height="36" rx="6" fill="{VIOLETA}" transform="rotate(45 {x + 32} {y + 33})"/>')
            s.append(t(x + 32, y + 39, num, 16, 700, "#fff", "middle"))
        else:
            s.append(f'<circle cx="{x + 32}" cy="{y + 33}" r="18" fill="{NAVY}"/>' + t(x + 32, y + 39, num, 16, 700, "#fff", "middle"))''',
 '''            s.append(f'<rect x="{x + 15}" y="{y + 13}" width="34" height="34" rx="6" fill="{VIOLETA}" transform="rotate(45 {x + 32} {y + 30})"/>')
            s.append(t(x + 32, y + 36, num, 16, 700, "#fff", "middle"))
        else:
            s.append(f'<circle cx="{x + 32}" cy="{y + 30}" r="18" fill="{NAVY}"/>' + t(x + 32, y + 36, num, 16, 700, "#fff", "middle"))'''),
# panel derecho más compacto
('''    s.append(t(X + 28, y, f"{icono}  {titulo}", 15.5, 700, NAVY))
    s.append(f'<line x1="{X + 28}" y1="{y + 8}" x2="{X + 864}" y2="{y + 8}" stroke="{LINEA}"/>')
    return y + 30''', '''    s.append(t(X + 28, y, f"{icono}  {titulo}", 15, 700, NAVY))
    s.append(f'<line x1="{X + 28}" y1="{y + 7}" x2="{X + 864}" y2="{y + 7}" stroke="{LINEA}"/>')
    return y + 26'''),
('''    quienes = [("Evaluadores", "Rol de TIMBÓ · al menos 3 (pto 13) · su opinión no es vinculante", "Quiénes en el hospital: a relevar", TEAL),''',
 '''    quienes = [("Evaluadores", "Rol de TIMBÓ · al menos 3 (pto 13)", "Quiénes en el hospital: a relevar", TEAL),'''),
('''    y += 74
    y = seccion(s, X, y, "☰", "Pasos (9 bloques del circuito oficial)")''', '''    y += 64
    y = seccion(s, X, y, "☰", "Pasos (9 bloques del circuito oficial)")'''),
('''        s.append(chip_estado(X + W - 28, y - 10, est, 10.5))
        y += 30''', '''        s.append(chip_estado(X + W - 28, y - 11, est, 10.5))
        y += 26'''),
('''    y += 26
    y = seccion(s, X, y, "📄", "Documentos")
    s.append(t(X + 28, y, "• Informe de preadjudicación — digital, firmado por los evaluadores; va solo al expediente (pto 7 y 22)", 13, 400, TXT))
    s.append(t(X + 28, y + 19, "• Subtrámites respondidos o descartados — se incorporan solos al expediente (pto 21)", 13, 400, TXT))
    y += 44''', '''    y += 24
    y = seccion(s, X, y, "📄", "Documentos")
    s.append(t(X + 28, y, "• Informe de preadjudicación (digital, firmado; va solo al expediente, ptos 7 y 22) · Subtrámites respondidos o descartados (pto 21)", 12.5, 400, TXT))
    y += 26'''),
('''        s.append(t(X + 28, y, linea, 13, 400, TXT))
        y += 19
    y += 8''', '''        s.append(t(X + 28, y, linea, 12.8, 400, TXT))
        y += 18
    y += 6'''),
('''    for f in ["Circular UG TIMBÓ 7/2026 · ptos 10, 13, 20.2, 21 y 22 · págs. 3 a 5",
              "Pliego Único (Dec. 287/2026) · 5.1, 5.2 y 5.3 · págs. 36 y 37",
              "Circular SCyGB 03/2026 · «Cronograma de impugnación» · pág. 1  ·  Res. ME 73/2026 · art. 2 · pág. 3"]:
        s.append(t(X + 28, y, "🔗 " + f, 13, 600, "#2456c7", "start", 'text-decoration="underline"'))
        y += 19
    y += 8''', '''    for f in ["Circular UG TIMBÓ 7/2026 · ptos 10, 13, 20.2, 21 y 22 · págs. 3 a 5   ·   Pliego Único · 5.1 a 5.3 · págs. 36 y 37",
              "Circular SCyGB 03/2026 · «Cronograma de impugnación» · pág. 1   ·   Res. ME 73/2026 · art. 2 · pág. 3"]:
        s.append(t(X + 28, y, "🔗 " + f, 12.8, 600, "#2456c7", "start", 'text-decoration="underline"'))
        y += 19
    y += 4'''),
('''    s.append(f'<rect x="{X + 24}" y="{y - 4}" width="{W - 48}" height="{984 - y - 10}" rx="12" fill="{PEND_F}" stroke="{PEND}" stroke-width="1.4"/>')''',
 '''    s.append(f'<rect x="{X + 24}" y="{y - 4}" width="{W - 48}" height="52" rx="12" fill="{PEND_F}" stroke="{PEND}" stroke-width="1.4"/>')'''),
('''    s.append(t(X + 40, y + 38, "❓ Para Santa Fe: ¿el control de la URC alcanza a los hospitales?   ❓ Para Compras: ¿quiénes serán los evaluadores?", 12.5, 500, PEND))''',
 '''    s.append(t(X + 40, y + 37, "❓ Para Santa Fe: ¿el control de la URC alcanza a los hospitales?   ❓ Para Compras: ¿quiénes serán los evaluadores?", 12.3, 500, PEND))'''),
('''    s.append(t(X0 + 24, 972, "✔ documentado''', '''    s.append(t(X0 + 24, 974, "✔ documentado'''),
]
for a, b in rep:
    assert a in s, a[:70]
    s = s.replace(a, b, 1)
p.write_text(s, encoding="utf-8")
print("ok")
