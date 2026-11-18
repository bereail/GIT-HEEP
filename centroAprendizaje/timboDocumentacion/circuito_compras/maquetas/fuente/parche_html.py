from pathlib import Path
p = Path(__file__).with_name("maquetas.py")
s = p.read_text(encoding="utf-8")
a = '''<section><h2>1. Vista general (para proyectar)</h2><div class="fig">{vista_general()}</div></section>
<section><h2>2. Vista de una etapa (ejemplo: 6 · Evaluación)</h2><div class="fig">{vista_etapa()}</div></section>'''
b = '''<section><h2>1. Maqueta: vista general + detalle de una etapa (ejemplo: 6)</h2><div class="fig">{__import__("dos_paneles").maqueta()}</div></section>'''
assert a in s
s = s.replace(a, b, 1)
p.write_text(s, encoding="utf-8")
print("ok")
