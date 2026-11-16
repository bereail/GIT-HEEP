"""Convierte los subtítulos .vtt de YouTube en texto legible con minutos, para
cotejar las lecciones contra los videos oficiales.

    python scripts/vtt_a_texto.py timboDocumentacion/transcripciones [titulos.txt]

Usa el .es-orig.vtt (lo que se dijo) y, si no está, el .es.vtt. Los subtítulos
automáticos repiten cada frase en dos cuadros: se quitan los repetidos. Agrupa
el texto en bloques de unos 30 segundos y borra los .vtt al terminar.
`titulos.txt` (opcional): líneas "id | título" para el encabezado.
"""
import glob
import os
import re
import sys

carpeta = sys.argv[1]
titulos = {}
if len(sys.argv) > 2:
    for linea in open(sys.argv[2], encoding="utf-8"):
        if " | " in linea:
            vid, titulo = linea.rstrip("\n").split(" | ", 1)
            titulos[vid.strip()] = titulo.strip()

TIEMPO = re.compile(r"^(\d+):(\d+):(\d+)\.\d+ --> ")
ETIQUETA = re.compile(r"<[^>]+>")

ids = sorted({os.path.basename(p).split(".")[0] for p in glob.glob(os.path.join(carpeta, "*.vtt"))})
for vid in ids:
    ruta = os.path.join(carpeta, f"{vid}.es-orig.vtt")
    if not os.path.exists(ruta):
        ruta = os.path.join(carpeta, f"{vid}.es.vtt")
    bloques, vistas, inicio = {}, set(), 0
    for linea in open(ruta, encoding="utf-8"):
        linea = linea.strip()
        m = TIEMPO.match(linea)
        if m:
            h, mi, s = map(int, m.groups())
            inicio = h * 3600 + mi * 60 + s
            continue
        if not linea or linea.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")) or "-->" in linea:
            continue
        texto = ETIQUETA.sub("", linea).strip()
        if not texto or texto in vistas:
            continue
        vistas.add(texto)
        bloques.setdefault(inicio // 30 * 30, []).append(texto)
    with open(os.path.join(carpeta, f"{vid}.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# {titulos.get(vid, vid)}\n# https://youtu.be/{vid}\n# Subtítulos de YouTube ({os.path.basename(ruta).split('.')[1]}), sin corregir.\n\n")
        for seg in sorted(bloques):
            f.write(f"[{seg // 3600}:{seg % 3600 // 60:02d}:{seg % 60:02d}] {' '.join(bloques[seg])}\n")
    for p in glob.glob(os.path.join(carpeta, f"{vid}.*.vtt")):
        os.remove(p)
    print(vid, len(bloques), "bloques")
