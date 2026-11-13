"""Carga el diccionario de equivalencias de artículos: nombre con el que un
artículo se pide en el sistema interno de compras del hospital → código y
nombre del Catálogo WEB oficial de la Provincia
(santafe.gov.ar/gestionesdecompras), que es el que hay que usar para cargar
la gestión en TIMBÓ Compras.

La fuente de verdad es `scripts/equivalencias_articulos.csv`, versionada en
git. Esta tabla se va alimentando pedido a pedido: cuando se resuelve un
artículo nuevo, se agrega una fila al CSV y se reimporta. Es idempotente a
nivel del tema completo: borra y recarga todas las filas de "timbo-compras".

Uso: python scripts/importar_equivalencias.py
"""

import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import EquivalenciaArticulo, Tema

RUTA_CSV = os.path.join(os.path.dirname(__file__), "equivalencias_articulos.csv")
TEMA_SLUG = "timbo-compras"


def importar(ruta_csv=RUTA_CSV, tema_slug=TEMA_SLUG):
    tema = Tema.query.filter_by(slug=tema_slug).first()
    if not tema:
        raise RuntimeError(f"No existe el tema '{tema_slug}'. Corré primero su importador de contenido.")

    EquivalenciaArticulo.query.filter_by(tema_id=tema.id).delete()

    total = 0
    with open(ruta_csv, encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            nombre_interno = (fila.get("nombre_interno") or "").strip()
            if not nombre_interno:
                continue
            db.session.add(EquivalenciaArticulo(
                tema_id=tema.id,
                nombre_interno=nombre_interno,
                codigo_catalogo=(fila.get("codigo_catalogo") or "").strip() or None,
                rubro_especie=(fila.get("rubro_especie") or "").strip() or None,
                sub_rubro_familia=(fila.get("sub_rubro_familia") or "").strip() or None,
                bien_o_servicio=(fila.get("bien_o_servicio") or "").strip() or None,
                item_especifico=(fila.get("item_especifico") or "").strip() or None,
                confianza=(fila.get("confianza") or "sin_match").strip() or "sin_match",
                origen=(fila.get("origen") or "").strip() or None,
                notas=(fila.get("notas") or "").strip() or None,
            ))
            total += 1

    db.session.commit()
    print(f"Equivalencias de artículos importadas para '{tema.nombre}': {total} filas.")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        importar()
