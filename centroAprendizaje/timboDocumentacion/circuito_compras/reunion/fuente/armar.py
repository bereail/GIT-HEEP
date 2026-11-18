"""Arma todo: gráficos SVG y PNG, la guía HTML con los gráficos adentro y el PDF.

    python fuente/armar.py
"""
import subprocess
import tempfile
from pathlib import Path

import graficos
import png

SALIDA = graficos.SALIDA
FUENTE = Path(__file__).resolve().parent


def main():
    circuito, quien = graficos.circuito(), graficos.quien_hace_que()
    (SALIDA / "circuito_compra.svg").write_text(circuito, encoding="utf-8")
    (SALIDA / "quien_hace_que.svg").write_text(quien, encoding="utf-8")
    for nombre in ("circuito_compra.svg", "quien_hace_que.svg"):
        png.a_png(SALIDA / nombre)

    html = (FUENTE / "guia_plantilla.html").read_text(encoding="utf-8")
    html = html.replace("{{CIRCUITO}}", circuito).replace("{{QUIEN}}", quien)
    guia = SALIDA / "Guia_reunion_Compras_TIMBO.html"
    guia.write_text(html, encoding="utf-8")
    print("HTML:", guia)

    pdf = guia.with_suffix(".pdf")
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([png.navegador(), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        f"--user-data-dir={Path(tmp) / 'perfil'}", f"--print-to-pdf={pdf}", guia.as_uri()],
                       check=True, capture_output=True, timeout=180)
    print("PDF:", pdf)


if __name__ == "__main__":
    main()
