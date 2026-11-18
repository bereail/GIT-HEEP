"""Pasa los SVG a PNG (doble resolución) con Edge o Chrome sin ventana.

    python fuente/png.py
"""
import re
import subprocess
import tempfile
from pathlib import Path

SALIDA = Path(__file__).resolve().parent.parent
NAVEGADORES = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
               r"C:\Program Files\Google\Chrome\Application\chrome.exe"]


def navegador():
    for n in NAVEGADORES:
        if Path(n).exists():
            return n
    raise SystemExit("No encontré Edge ni Chrome")


def a_png(svg: Path):
    texto = svg.read_text(encoding="utf-8")
    w, h = map(float, re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', texto).groups())
    w, h = int(w), int(h)
    with tempfile.TemporaryDirectory() as tmp:
        pagina = Path(tmp) / "p.html"
        pagina.write_text(f"<!doctype html><meta charset='utf-8'><style>html,body{{margin:0;background:#fff}}"
                          f"svg{{display:block}}</style>{texto}", encoding="utf-8")
        png = svg.with_suffix(".png")
        subprocess.run([navegador(), "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--force-device-scale-factor=2", f"--window-size={w},{h}",
                        f"--user-data-dir={Path(tmp) / 'perfil'}",
                        f"--screenshot={png}", pagina.as_uri()], check=True, capture_output=True, timeout=120)
    print("PNG:", png)


if __name__ == "__main__":
    for nombre in ("circuito_compra.svg", "quien_hace_que.svg"):
        a_png(SALIDA / nombre)
