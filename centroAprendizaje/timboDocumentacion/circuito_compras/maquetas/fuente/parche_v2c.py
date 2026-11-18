from pathlib import Path
p = Path(__file__).with_name("v2.py")
s = p.read_text(encoding="utf-8")
a = '''    partes = [f"{ESTADO[k][0]} {v} {ESTADO[k][1].lower()}" for k, v in cuenta.items() if k in ESTADO]'''
b = '''    def plural(txt, v):
        if v == 1:
            return txt
        primera, _, resto = txt.partition(" ")
        return primera + "s" + (" " + resto if resto else "")
    partes = [f"{ESTADO[k][0]} {v} {plural(ESTADO[k][1].lower(), v)}" for k, v in cuenta.items() if k in ESTADO]'''
assert a in s
p.write_text(s.replace(a, b, 1), encoding="utf-8")
print("ok")
