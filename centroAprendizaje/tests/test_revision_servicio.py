"""Planilla descargable de revisión de artículos por servicio (bodega)."""
import json
import re

import pytest

from app.extensions import db
from app.models import EquivalenciaArticulo, Tema
from app.services import revision_servicio

URL = "/temas/timbo-compras/equivalencias/revision-servicio"


@pytest.fixture()
def nomenclador(app):
    with app.app_context():
        tema = Tema(slug="timbo-compras", nombre="TIMBÓ Compras", orden=1)
        db.session.add(tema)
        db.session.flush()
        filas = (
            ("Sonda K30", "sin_match", "MANTENIMIENTO", "10", None, None),
            ("Tubo 5,5", "dudosa", "MANTENIMIENTO", "11", "38.1.5.22", "TUBO ENDOTRAQUEAL"),
            ("Guantes látex M", "alta", "MANTENIMIENTO", "12", "38.6.1.1", "GUANTES NO UTILIZAR"),
            ("Aguja 25/8", "alta", "MANTENIMIENTO", "13", "38.6.2.1", "AGUJA"),
            ("Paracetamol 500", "alta", "FARMACIA", "14", "37.1.1.1", "PARACETAMOL"),
        )
        for nombre, confianza, bodega, cod, codigo, bien in filas:
            db.session.add(EquivalenciaArticulo(
                tema_id=tema.id, nombre_interno=nombre, confianza=confianza, bodega=bodega,
                codigo_interno=cod, codigo_catalogo=codigo, bien_o_servicio=bien, item_especifico="Ítem"))
        db.session.commit()


def _datos(html):
    return json.loads(re.search(r'<script type="application/json" id="rs-datos">(.*?)</script>', html, re.S).group(1))


def test_descarga_la_planilla_de_una_bodega(client, nomenclador):
    r = client.get(URL, query_string={"bodega": "MANTENIMIENTO"})
    assert r.status_code == 200
    assert "attachment" in r.headers["Content-Disposition"]
    assert re.search(r'filename="revision-mantenimiento-\d{4}-\d{2}-\d{2}\.html"', r.headers["Content-Disposition"])
    datos = _datos(r.get_data(as_text=True))
    assert datos["bodega"] == "MANTENIMIENTO"
    # Por sección y, dentro de cada una, por nombre.
    assert [i["id"] for i in datos["items"]] == ["10", "12", "11", "13"]


def test_secciones_por_confianza_y_no_utilizar(app, nomenclador):
    with app.app_context():
        tema = Tema.query.filter_by(slug="timbo-compras").one()
        items = {i["id"]: i for i in revision_servicio.armar_planilla(tema, "MANTENIMIENTO")["items"]}
    assert items["10"]["s"] == 1 and items["10"]["cp"] == ""
    assert items["11"]["s"] == 2
    # Un verde cuyo código el catálogo marca «NO UTILIZAR» pasa a confirmación.
    assert items["12"]["s"] == 2 and items["12"]["nu"] is True
    assert items["13"]["s"] == 3


@pytest.mark.parametrize("bodega", ["", "FARMACIA", "LABORATORIO", "NO EXISTE"])
def test_bodegas_excluidas_o_vacias_dan_404(client, nomenclador, bodega):
    assert client.get(URL, query_string={"bodega": bodega}).status_code == 404


def test_el_selector_no_ofrece_farmacia(client, nomenclador):
    html = client.get("/temas/timbo-compras/equivalencias").get_data(as_text=True)
    selector = re.search(r'name="bodega".*?</select>', html, re.S).group(0)
    assert "MANTENIMIENTO" in selector and "FARMACIA" not in selector


def test_planilla_trae_la_seccion_de_articulos_que_no_estan(client, nomenclador):
    html = client.get(URL, query_string={"bodega": "MANTENIMIENTO"}).get_data(as_text=True)
    assert 'id="rs-nec-form"' in html
    # La orientación repite solo lo publicado como oficial en el nomenclador.
    assert "Alta de bienes y servicios CAByS" in html
    assert "a través del Servicio de Farmacia del hospital" in html
    assert "todavía no está definido" in html
    # Es un archivo autónomo: el enlace a la guía oficial tiene que ser absoluto.
    assert re.search(r'href="https?://[^"]+/static/docs/timbo-compras/como-solicitar-alta-de-articulos\.pdf"', html)


def _cargar(app, filas, bodega="INFORMATICA"):
    with app.app_context():
        tema = Tema.query.filter_by(slug="timbo-compras").first()
        if not tema:
            tema = Tema(slug="timbo-compras", nombre="TIMBÓ Compras", orden=1)
            db.session.add(tema)
            db.session.flush()
        for nombre, confianza, cod, codigo in filas:
            db.session.add(EquivalenciaArticulo(
                tema_id=tema.id, nombre_interno=nombre, confianza=confianza, bodega=bodega,
                codigo_interno=cod, codigo_catalogo=codigo, bien_o_servicio="DRUM", item_especifico="Ítem"))
        db.session.commit()
        return {i["id"]: i for i in revision_servicio.armar_planilla(tema, bodega)["items"]}


def test_agrupa_los_que_comparten_codigo_propuesto(app):
    items = _cargar(app, (
        ("DRUM 1060", "dudosa", "18784", "19.1.283.1"),
        ("DRUM 2340", "dudosa", "18785", "19.1.283.1"),
        ("DRUM 420/450", "alta", "18830", "19.1.283.1"),
        ("Tóner 12A", "alta", "500", "19.1.1.1"),
        ("Cable USB", "sin_match", "600", "19.9.9.9"),
        ("Cable HDMI", "sin_match", "601", "19.9.9.9"),
    ))
    grupo = [items[c] for c in ("18784", "18785", "18830")]
    assert {i["g"] for i in grupo} == {"19.1.283.1"}
    # Todo el grupo va a la sección más temprana: el verde pasa a confirmación.
    assert {i["s"] for i in grupo} == {2}
    assert all("se propuso para 3 artículos" in i["m"] for i in grupo)
    assert not any(i["dup"] for i in grupo)
    assert "g" not in items["500"] and items["500"]["s"] == 3
    # Los rojos no tienen código propuesto: nunca se agrupan.
    assert "g" not in items["600"] and "g" not in items["601"]


def test_marca_mismo_nombre_dentro_del_grupo(app):
    items = _cargar(app, (
        ("ALCOHOL ETILICO 96 x 500 ml", "alta", "4074", "37.2.13.6"),
        ("Alcohol  etílico 96 x 500 ml", "alta", "4128", "37.2.13.6"),
        ("Alcohol en gel x 500 ml", "dudosa", "4200", "37.2.13.6"),
    ), bodega="DEPOSITO")
    assert items["4074"]["dup"] and items["4128"]["dup"]
    assert not items["4200"]["dup"]


def test_grupos_muy_grandes_quedan_sueltos_con_aviso(app):
    n = revision_servicio.MAX_GRUPO + 1
    items = _cargar(app, [(f"Llave T {k}", "dudosa", str(1000 + k), "22.1.61.8") for k in range(n)], bodega="MANTENIMIENTO")
    assert not any("g" in i for i in items.values())
    assert all(f"se propuso para {n} artículos" in i["m"] for i in items.values())
