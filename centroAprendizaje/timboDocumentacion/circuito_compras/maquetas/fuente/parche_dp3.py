from pathlib import Path
p = Path(__file__).with_name("dos_paneles.py")
s = p.read_text(encoding="utf-8")
rep = [
('''        if donde == "mixto":
            col, fondo, txt_donde = AZUL, AZUL_F, "TIMBÓ + fuera"''',
 '''        if donde == "mixto":
            col, fondo, txt_donde = AZUL, AZUL_F, "TIMBÓ + fuera"
        if donde == "sindef":
            col, fondo, txt_donde = "#5b6472", "#f1f3f6", "¿Dónde? a relevar"'''),
('''"Reglas del Pliego Único 6.9 a 6.13", "fuera",''', '''"Reglas del Pliego Único 6.9 a 6.13", "sindef",'''),
]
for a, b in rep:
    assert a in s, a[:60]
    s = s.replace(a, b, 1)
p.write_text(s, encoding="utf-8")
print("ok")
