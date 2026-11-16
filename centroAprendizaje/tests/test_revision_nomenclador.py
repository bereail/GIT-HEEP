"""Revisión del nomenclador: acceso con enlace privado, observaciones sobre
los ítems en amarillo y vista del panel."""
import re

import pytest

from app.extensions import db
from app.models import EquivalenciaArticulo, Tema
from app.models.revision_nomenclador import (
    ObservacionHistorial, ObservacionNomenclador, RevisorNomenclador, clave_item, hash_token,
)

TOKEN = "token-de-prueba-largo-y-secreto-123456"


@pytest.fixture()
def nomenclador(app):
    with app.app_context():
        tema = Tema(slug="timbo-compras", nombre="TIMBÓ Compras", orden=1)
        db.session.add(tema)
        db.session.flush()
        for nombre, confianza in (("Guantes de látex M", "dudosa"), ("Jeringa 5 ml", "dudosa"),
                                  ("Aguja 25/8", "alta"), ("Circuito respirador", "sin_match")):
            db.session.add(EquivalenciaArticulo(tema_id=tema.id, nombre_interno=nombre, confianza=confianza,
                                                bien_o_servicio="Bien", item_especifico="Ítem"))
        db.session.add(RevisorNomenclador(nombre="Ana", token_hash=hash_token(TOKEN), activo=True))
        db.session.commit()


def entrar(cliente, token=TOKEN):
    return cliente.post("/revision/acceso", data={"token": token})


def guardar(cliente, nombre, texto):
    return cliente.post("/revision/observacion", json={"clave": clave_item(nombre), "texto": texto})


def test_enlace_valido_entra_y_ve_solo_los_amarillos(app, nomenclador):
    c = app.test_client()
    assert c.get("/revision/").status_code == 302  # sin enlace, no entra
    r = entrar(c)
    assert r.status_code == 302 and r.headers["Location"].endswith("/revision/")
    html = c.get("/revision/").get_data(as_text=True)
    assert "Guantes de látex M" in html and "Jeringa 5 ml" in html
    assert "Aguja 25/8" not in html and "Circuito respirador" not in html


def test_enlace_invalido_o_dado_de_baja(app, nomenclador):
    c = app.test_client()
    assert entrar(c, "cualquier-cosa-que-no-es-el-token-1234").status_code == 403
    with app.app_context():
        RevisorNomenclador.query.first().activo = False
        db.session.commit()
    assert entrar(c).status_code == 403


def test_la_baja_corta_una_sesion_abierta(app, nomenclador):
    c = app.test_client()
    entrar(c)
    with app.app_context():
        RevisorNomenclador.query.first().activo = False
        db.session.commit()
    assert c.get("/revision/").status_code == 302
    assert guardar(c, "Guantes de látex M", "x").status_code == 403


def test_guardar_editar_e_historial(app, nomenclador):
    c = app.test_client()
    entrar(c)
    r = guardar(c, "Guantes de látex M", "El código correcto es otro.")
    assert r.status_code == 200 and r.get_json()["ok"]
    guardar(c, "Guantes de látex M", "Corrijo: está bien.")
    with app.app_context():
        obs = ObservacionNomenclador.query.one()
        assert obs.texto == "Corrijo: está bien." and obs.nombre_item == "Guantes de látex M"
        assert [h.texto for h in ObservacionHistorial.query] == ["El código correcto es otro."]
    # Al volver a entrar, sigue ahí.
    c2 = app.test_client()
    entrar(c2)
    assert "Corrijo: está bien." in c2.get("/revision/").get_data(as_text=True)


def test_solo_items_amarillos_y_largo_maximo(app, nomenclador):
    c = app.test_client()
    entrar(c)
    assert guardar(c, "Aguja 25/8", "x").status_code == 404           # verde
    assert guardar(c, "Circuito respirador", "x").status_code == 404  # rojo
    assert guardar(c, "No existe", "x").status_code == 404
    assert guardar(c, "Jeringa 5 ml", "x" * 2001).status_code == 400
    assert c.post("/revision/observacion", json=["no", "es", "objeto"]).status_code == 400


def test_no_modifica_el_nomenclador_ni_da_acceso_al_panel(app, nomenclador):
    c = app.test_client()
    entrar(c)
    guardar(c, "Jeringa 5 ml", "Revisar la medida.")
    with app.app_context():
        e = EquivalenciaArticulo.query.filter_by(nombre_interno="Jeringa 5 ml").one()
        assert e.confianza == "dudosa" and e.item_especifico == "Ítem" and e.notas is None
    for url in ("/admin/", "/admin/nomenclador/revision"):
        r = c.get(url)
        assert r.status_code == 302 and "/admin/login" in r.headers["Location"]
    assert c.post("/admin/nomenclador/revisores", data={"nombre": "Intruso"}).status_code == 302
    with app.app_context():
        assert RevisorNomenclador.query.count() == 1


def test_no_se_puede_escribir_a_nombre_de_otro(app, nomenclador):
    with app.app_context():
        db.session.add(RevisorNomenclador(nombre="Beto", token_hash=hash_token(TOKEN + "-beto"), activo=True))
        db.session.commit()
    c = app.test_client()
    entrar(c)
    c.post("/revision/observacion", json={"clave": clave_item("Jeringa 5 ml"), "texto": "Mía", "revisor_id": 2})
    with app.app_context():
        assert ObservacionNomenclador.query.one().revisor.nombre == "Ana"


def test_las_observaciones_sobreviven_a_la_reimportacion(app, nomenclador):
    c = app.test_client()
    entrar(c)
    guardar(c, "Guantes de látex M", "Ojo con el talle.")
    with app.app_context():
        # importar_equivalencias.py borra y recarga todas las filas (cambian los id).
        EquivalenciaArticulo.query.delete()
        tema = Tema.query.filter_by(slug="timbo-compras").one()
        db.session.add(EquivalenciaArticulo(tema_id=tema.id, nombre_interno="Guantes  de LÁTEX m", confianza="dudosa"))
        db.session.commit()
    assert "Ojo con el talle." in c.get("/revision/").get_data(as_text=True)


def test_panel_ve_observaciones_filtros_y_crea_accesos(app, nomenclador, admin_client):
    c = app.test_client()
    entrar(c)
    guardar(c, "Guantes de látex M", "Falta el código.")
    html = admin_client.get("/admin/nomenclador/revision?filtro=con").get_data(as_text=True)
    assert "Falta el código." in html and "Ana" in html and "Jeringa 5 ml" not in html
    html = admin_client.get("/admin/nomenclador/revision?filtro=sin").get_data(as_text=True)
    assert "Jeringa 5 ml" in html and "Falta el código." not in html
    r = admin_client.post("/admin/nomenclador/revisores", data={"nombre": "Carla"}, follow_redirects=True)
    url = re.search(r'id="rev-enlace-url">([^<]+)<', r.get_data(as_text=True)).group(1)
    token = url.split("#", 1)[1]
    with app.app_context():
        carla = RevisorNomenclador.query.filter_by(nombre="Carla").one()
        assert carla.token_hash == hash_token(token) and token not in carla.token_hash
    assert entrar(app.test_client(), token).status_code == 302
    # El enlace se muestra una sola vez.
    assert "rev-enlace-url" not in admin_client.get("/admin/nomenclador/revision").get_data(as_text=True)


def test_nomenclador_publico_con_colores_y_leyenda(app, nomenclador):
    html = app.test_client().get("/temas/timbo-compras/equivalencias").get_data(as_text=True)
    for texto in ("est-leyenda", "estado-verde", "estado-amarillo", "estado-rojo", "🔴 Hay que pedir que se agreguen"):
        assert texto in html, texto
