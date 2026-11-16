"""Inventario del material en el panel: se arma solo, filtra y exporta."""
import json
import os

from app import recursos


def test_inventario_lista_todo_y_filtra(app, admin_client):
    html = admin_client.get("/admin/inventario").get_data(as_text=True)
    for texto in ("Inventario del material", "Documento oficial", "Término del Diccionario", "Paso del algoritmo",
                  "Exportar a Excel", "Resumen por tipo de material"):
        assert texto in html, texto
    html = admin_client.get("/admin/inventario?tipo=documento&q=compre").get_data(as_text=True)
    assert "Compre Santafesino" in html and "Término del Diccionario</td>" not in html
    assert app.test_client().get("/admin/inventario").status_code == 302  # sin login


def test_inventario_exporta_con_filtros(admin_client):
    r = admin_client.get("/admin/inventario/exportar?tipo=documento")
    texto = r.get_data(as_text=True)
    assert "attachment" in r.headers["Content-Disposition"] and texto.startswith("﻿")
    assert "Fuente oficial" in texto and "Documento oficial" in texto and "Paso del algoritmo" not in texto


def test_estados_de_lecciones_son_validos():
    with open(os.path.join(recursos.CARPETA, "inventario.json"), encoding="utf-8") as f:
        datos = json.load(f)
    validos = set(datos["estados"])
    for tema in datos["lecciones"].values():
        for slug, reg in tema.items():
            assert reg["estado"] in validos, slug
    for reg in datos["temas"].values():
        assert reg["estado"] in validos
