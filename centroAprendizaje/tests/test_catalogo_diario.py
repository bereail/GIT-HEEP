"""Comparación diaria con el Catálogo WEB: nunca pisa nada y avisa cambios."""
import os

import pytest

from app.extensions import db
from app.models import EquivalenciaArticulo, ObservacionNomenclador, Tema
from app.models.revision_servicio import ActualizacionCatalogo
from app.services import catalogo_diario as cd

ENC = '"' + '"|"'.join(cd.COLUMNAS) + '"\n'


def csv_catalogo(items):
    """items: {código: (bien, ítem)}"""
    return "﻿" + ENC + "".join(f'"1 - X"|"1.1 - Y"|1.1.1|"{b}"|"gasto"|{c}|"{i}"|\n' for c, (b, i) in items.items())


def base(n, extra=None):
    items = {f"9.9.{k}": ("BIEN", f"ITEM {k}") for k in range(n)}
    items.update(extra or {})
    return items


@pytest.fixture()
def entorno(app, tmp_path, monkeypatch):
    monkeypatch.setattr(cd, "MINIMO_ITEMS", 5)
    ruta_base = app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "", 1)
    with app.app_context():
        tema = Tema(slug="timbo-compras", nombre="TIMBÓ Compras", orden=1)
        db.session.add(tema)
        db.session.flush()
        db.session.add(EquivalenciaArticulo(tema_id=tema.id, nombre_interno="Tóner", confianza="alta", bodega="INFORMATICA",
                                            codigo_interno="1", codigo_catalogo="1.1.1.1"))
        db.session.add(EquivalenciaArticulo(tema_id=tema.id, nombre_interno="Fax", confianza="dudosa", bodega="INFORMATICA",
                                            codigo_interno="2", codigo_catalogo="1.1.1.2"))
        db.session.commit()
    return str(tmp_path), ruta_base


def test_primera_corrida_y_cambios(app, entorno):
    inst, ruta = entorno
    with app.app_context():
        r1 = cd.actualizar(inst, ruta, csv_catalogo(base(20, {"1.1.1.1": ("TONER", "TONER X"), "1.1.1.2": ("FAX", "FAX")})))
        assert r1.estado == "ok" and r1.items == 22 and r1.afectados == 0
        r2 = cd.actualizar(inst, ruta, csv_catalogo(base(20, {"1.1.1.1": ("TONER NO UTILIZAR", "TONER X"), "8.8.8.8": ("NUEVO", "N")})))
        assert r2.estado == "ok" and r2.nuevos == 1 and r2.quitados == 1 and r2.no_utilizar == 1
        assert r2.afectados == 2  # el tóner es «NO UTILIZAR» y el código del fax ya no existe
        assert len(os.listdir(os.path.join(inst, "catalogo"))) == 2         # nunca pisa una copia
        assert len(os.listdir(os.path.join(inst, "copias_catalogo"))) == 2  # copia de la base antes de cada corrida
        assert "ya no figura" in cd.aviso_codigo("1.1.1.2", cd.catalogo_vigente(inst))


def test_catalogo_incompleto_o_raro_no_se_usa(app, entorno):
    inst, ruta = entorno
    with app.app_context():
        cd.actualizar(inst, ruta, csv_catalogo(base(40)))
        r = cd.actualizar(inst, ruta, csv_catalogo(base(20)))   # la mitad: no se usa
        assert r.estado == "error" and "incompleto" in r.mensaje
        r = cd.actualizar(inst, ruta, "otra|cosa\n1|2\n")
        assert r.estado == "error" and "columnas" in r.mensaje
        assert len(os.listdir(os.path.join(inst, "catalogo"))) == 1   # quedó el bueno
        assert len(cd.catalogo_vigente(inst)) == 40
        assert ActualizacionCatalogo.query.count() == 3


def test_alerta_si_bajan_las_respuestas(app, entorno):
    from app.models.revision_nomenclador import RevisorNomenclador
    inst, ruta = entorno
    with app.app_context():
        rv = RevisorNomenclador(nombre="x", token_hash="y" * 64, activo=True)
        db.session.add(rv)
        db.session.flush()
        o = ObservacionNomenclador(revisor_id=rv.id, clave_item="a", nombre_item="a", texto="", validacion="si")
        db.session.add(o)
        db.session.commit()
        assert cd.actualizar(inst, ruta, csv_catalogo(base(20))).respuestas == 1
        db.session.delete(o)
        db.session.commit()
        r = cd.actualizar(inst, ruta, csv_catalogo(base(20)))
        assert r.estado == "alerta" and "respuestas" in r.mensaje


def test_panel_muestra_la_comparacion(app, entorno, admin_client):
    inst, ruta = entorno
    with app.app_context():
        cd.actualizar(inst, ruta, csv_catalogo(base(20, {"1.1.1.1": ("T", "T")})))
    html = admin_client.get("/admin/servicios").get_data(as_text=True)
    assert "Catálogo vigente" in html and "Actualizar ahora" in html and "revisar de nuevo (1)" in html


def test_posibles_altas_sugiere_solo_con_palabras_en_comun():
    cargar = [("Informática", "8375", "PENDRIVE 16GB USB"), ("Informática", "1", "CD")]
    nuevos = [("19.1.300.1", "PENDRIVE — PENDRIVE USB 16 GB"), ("19.1.300.2", "MOUSE — MOUSE OPTICO")]
    altas = cd.posibles_altas(cargar, nuevos)
    assert [a["codigo"] for a in altas] == ["19.1.300.1"]       # «CD» tiene una sola palabra: no se sugiere


def test_corrida_guarda_resumen_por_servicio_y_la_fecha_se_ve(app, entorno, client):
    import json
    from app.models.revision_servicio import LlaveServicio
    from app.services import llaves_servicio as ls
    inst, ruta = entorno
    with app.app_context():
        ll = LlaveServicio(servicio="Informática", activo=True)
        token = ls.nuevo_token(ll)
        db.session.add(ll)
        db.session.commit()
        ls.asignar_bodegas(ll, ["INFORMATICA"], {"INFORMATICA"})
        db.session.commit()
        r = cd.actualizar(inst, ruta, csv_catalogo(base(20)))
        resumen = json.loads(r.detalle)["resumen_servicios"]
        assert resumen["Informática"]["estan"] == 1 and resumen["Informática"]["falta"] == 1
    client.post("/servicio/acceso", data={"token": token})
    client.post("/servicio/persona", data={"nombre": "Ana", "apellido": "Paz"})
    html = client.get("/servicio/").get_data(as_text=True)
    assert "</a> actualizado el" in html and "a=catalogo.index" in html


def test_admin_baja_el_catalogo_y_no_superpone_actualizaciones(app, entorno, admin_client, monkeypatch):
    import subprocess
    inst, ruta = entorno
    monkeypatch.setattr(app, "instance_path", inst)
    with app.app_context():
        cd.actualizar(inst, ruta, csv_catalogo(base(20)))
    r = admin_client.get("/admin/servicios/catalogo/descargar")
    assert r.status_code == 200 and b"9.9.0" in r.data
    lanzados = []
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: lanzados.append(a))
    assert admin_client.post("/admin/servicios/catalogo/actualizar").status_code == 302
    assert len(lanzados) == 1
    cd.marca_en_curso(inst)                         # una actualización corriendo
    admin_client.post("/admin/servicios/catalogo/actualizar")
    assert len(lanzados) == 1                       # no se lanza otra
    assert "Actualizando" in admin_client.get("/admin/servicios").get_data(as_text=True)


def test_saltos_de_linea_no_cuentan_como_cambio():
    a = cd.leer_catalogo(ENC + '"1 - X"|"1.1 - Y"|1.1.1|"BIEN"|"g"|5.5.5|"ITEM\r\nCON SALTO"|\n')
    b = cd.leer_catalogo(ENC + '"1 - X"|"1.1 - Y"|1.1.1|"BIEN"|"g"|5.5.5|"ITEM\nCON  SALTO"|\n')
    assert cd.comparar(a, b)["cambiados"] == []
