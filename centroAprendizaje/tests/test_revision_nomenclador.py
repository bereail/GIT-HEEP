"""Revisión del nomenclador: acceso con enlace privado, validación (sí / no /
dudas) y observaciones sobre los ítems en amarillo, descargas y vista del
panel."""
import io
import json
import re
import zipfile

import pytest

from app.extensions import db
from app.models import EquivalenciaArticulo, Tema
from app.models.revision_nomenclador import (
    ObservacionHistorial, ObservacionNomenclador, RevisorNomenclador, clave_item, hash_token,
)

TOKEN = "token-de-prueba-largo-y-secreto-123456"
TOKEN_BETO = TOKEN + "-beto"


@pytest.fixture()
def nomenclador(app):
    with app.app_context():
        tema = Tema(slug="timbo-compras", nombre="TIMBÓ Compras", orden=1)
        db.session.add(tema)
        db.session.flush()
        for nombre, confianza in (("Guantes de látex M", "dudosa"), ("Jeringa 5 ml", "dudosa"),
                                  ("Aguja 25/8", "alta"), ("Circuito respirador", "sin_match")):
            db.session.add(EquivalenciaArticulo(tema_id=tema.id, nombre_interno=nombre, confianza=confianza,
                                                bien_o_servicio="Bien", item_especifico="Ítem",
                                                codigo_catalogo="38.6.1.1",
                                                notas="[cod. interno 412] revisar" if nombre == "Jeringa 5 ml" else None))
        db.session.add(RevisorNomenclador(nombre="Ana", token_hash=hash_token(TOKEN), activo=True))
        db.session.commit()


@pytest.fixture()
def beto(app, nomenclador):
    with app.app_context():
        db.session.add(RevisorNomenclador(nombre="Beto", token_hash=hash_token(TOKEN_BETO), activo=True))
        db.session.commit()


def entrar(cliente, token=TOKEN):
    return cliente.post("/revision/acceso", data={"token": token})


def guardar(cliente, nombre, texto=None, validacion=None):
    datos = {"clave": clave_item(nombre)}
    if texto is not None:
        datos["texto"] = texto
    if validacion is not None:
        datos["validacion"] = validacion
    return cliente.post("/revision/observacion", json=datos)


def items_de_la_pagina(cliente):
    """Los ítems que la pantalla de farmacia recibe (van en un JSON)."""
    html = cliente.get("/revision/").get_data(as_text=True)
    crudo = re.search(r'<script type="application/json" id="val-datos">(.*?)</script>', html, re.S).group(1)
    return {i["nombre"]: i for i in json.loads(crudo)["items"]}


def hojas_xlsx(contenido):
    """{nombre de hoja: [[celdas de cada fila]]} de un .xlsx."""
    z = zipfile.ZipFile(io.BytesIO(contenido))
    nombres = re.findall(r'<sheet name="([^"]+)"', z.read("xl/workbook.xml").decode())
    hojas = {}
    for i, nombre in enumerate(nombres, 1):
        xml = z.read(f"xl/worksheets/sheet{i}.xml").decode()
        hojas[nombre] = [[re.sub(r"&amp;", "&", t) for t in re.findall(r"<t[^>]*>(.*?)</t>", fila)]
                         for fila in re.findall(r"<row[^>]*>(.*?)</row>", xml)]
    return hojas


def test_enlace_valido_entra_y_ve_solo_los_amarillos(app, nomenclador):
    c = app.test_client()
    assert c.get("/revision/").status_code == 302  # sin enlace, no entra
    r = entrar(c)
    assert r.status_code == 302 and r.headers["Location"].endswith("/revision/")
    items = items_de_la_pagina(c)
    assert set(items) == {"Guantes de látex M", "Jeringa 5 ml"}
    jeringa = items["Jeringa 5 ml"]
    assert jeringa["codigo_hospital"] == "412" and jeringa["codigo"] == "38.6.1.1" and jeringa["timbo"] == "Bien — Ítem"
    html = c.get("/revision/").get_data(as_text=True)
    assert "¿Son realmente el mismo artículo?" in html and "Descargar mis revisiones (Excel)" in html
    assert "Aguja 25/8" not in html and "Circuito respirador" not in html
    assert jeringa["nota"] == "Revisar"  # la nota se ve, sin la marca técnica del código interno


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
    assert c.get("/revision/mis-revisiones.xlsx").status_code == 403


def test_tres_respuestas_sin_observacion_obligatoria(app, nomenclador):
    c = app.test_client()
    entrar(c)
    for respuesta in ("si", "no", "duda"):
        r = guardar(c, "Jeringa 5 ml", validacion=respuesta)
        assert r.status_code == 200 and r.get_json()["validacion"] == respuesta and r.get_json()["texto"] == ""
    assert guardar(c, "Jeringa 5 ml", validacion="quizas").status_code == 400
    with app.app_context():
        obs = ObservacionNomenclador.query.one()
        assert obs.validacion == "duda" and obs.texto == ""
        assert [h.validacion for h in ObservacionHistorial.query.order_by(ObservacionHistorial.id)] == ["si", "no"]


def test_responder_y_observar_por_separado_no_se_pisan(app, nomenclador):
    c = app.test_client()
    entrar(c)
    guardar(c, "Jeringa 5 ml", validacion="no")
    guardar(c, "Jeringa 5 ml", texto="Es de 10 ml.")       # solo la observación: la respuesta queda
    assert guardar(c, "Jeringa 5 ml", validacion="si").get_json()["texto"] == "Es de 10 ml."
    with app.app_context():
        obs = ObservacionNomenclador.query.one()
        assert (obs.validacion, obs.texto) == ("si", "Es de 10 ml.")


def test_continua_donde_quedo_y_puede_modificar(app, nomenclador):
    c = app.test_client()
    entrar(c)
    guardar(c, "Guantes de látex M", validacion="si")
    c2 = app.test_client()  # otro día, otra sesión
    entrar(c2)
    items = items_de_la_pagina(c2)
    assert items["Guantes de látex M"]["validacion"] == "si"   # en Revisados
    assert items["Jeringa 5 ml"]["validacion"] is None         # sigue por revisar
    assert 'id="val-n-pend">1<' in c2.get("/revision/").get_data(as_text=True)
    guardar(c2, "Guantes de látex M", validacion="no")
    assert items_de_la_pagina(c2)["Guantes de látex M"]["validacion"] == "no"


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
    assert items_de_la_pagina(c2)["Guantes de látex M"]["observacion"] == "Corrijo: está bien."


def test_observaciones_viejas_sin_respuesta_se_conservan(app, nomenclador):
    """Las observaciones de antes de la validación (sin respuesta) siguen ahí y
    el ítem cuenta como sin revisar."""
    with app.app_context():
        ana = RevisorNomenclador.query.one()
        db.session.add(ObservacionNomenclador(revisor_id=ana.id, clave_item=clave_item("Jeringa 5 ml"),
                                              nombre_item="Jeringa 5 ml", texto="Observación vieja"))
        db.session.commit()
    c = app.test_client()
    entrar(c)
    item = items_de_la_pagina(c)["Jeringa 5 ml"]
    assert item["observacion"] == "Observación vieja" and item["validacion"] is None


def test_solo_items_amarillos_y_largo_maximo(app, nomenclador):
    c = app.test_client()
    entrar(c)
    assert guardar(c, "Aguja 25/8", "x").status_code == 404           # verde
    assert guardar(c, "Circuito respirador", "x").status_code == 404  # rojo
    assert guardar(c, "Aguja 25/8", validacion="si").status_code == 404
    assert guardar(c, "No existe", "x").status_code == 404
    assert guardar(c, "Jeringa 5 ml", "x" * 2001).status_code == 400
    assert c.post("/revision/observacion", json=["no", "es", "objeto"]).status_code == 400


def test_no_modifica_el_nomenclador_ni_da_acceso_al_panel(app, nomenclador):
    c = app.test_client()
    entrar(c)
    guardar(c, "Jeringa 5 ml", "Revisar la medida.", validacion="no")
    with app.app_context():
        e = EquivalenciaArticulo.query.filter_by(nombre_interno="Jeringa 5 ml").one()
        assert e.confianza == "dudosa" and e.item_especifico == "Ítem" and e.codigo_catalogo == "38.6.1.1"
        assert e.notas == "[cod. interno 412] revisar"
    for url in ("/admin/", "/admin/nomenclador/revision", "/admin/nomenclador/revision/exportar"):
        r = c.get(url)
        assert r.status_code == 302 and "/admin/login" in r.headers["Location"]
    assert c.post("/admin/nomenclador/revisores", data={"nombre": "Intruso"}).status_code == 302
    with app.app_context():
        assert RevisorNomenclador.query.count() == 1


def test_no_se_puede_escribir_a_nombre_de_otro(app, beto):
    c = app.test_client()
    entrar(c)
    c.post("/revision/observacion", json={"clave": clave_item("Jeringa 5 ml"), "texto": "Mía", "revisor_id": 2})
    with app.app_context():
        assert ObservacionNomenclador.query.one().revisor.nombre == "Ana"


def test_cada_uno_ve_solo_lo_suyo(app, beto):
    ana, b = app.test_client(), app.test_client()
    entrar(ana)
    entrar(b, TOKEN_BETO)
    guardar(ana, "Jeringa 5 ml", "Secreto de Ana", validacion="no")
    item = items_de_la_pagina(b)["Jeringa 5 ml"]
    assert item["validacion"] is None and item["observacion"] == ""
    assert "Secreto de Ana" not in b.get("/revision/?revisor_id=1").get_data(as_text=True)


def test_descarga_de_farmacia_solo_sus_revisiones(app, beto):
    ana, b = app.test_client(), app.test_client()
    entrar(ana)
    entrar(b, TOKEN_BETO)
    guardar(ana, "Jeringa 5 ml", "Es otra medida", validacion="no")
    guardar(b, "Guantes de látex M", "De Beto", validacion="si")
    with app.app_context():  # una revisión de Ana sobre un ítem que ya no está en amarillo
        db.session.add(ObservacionNomenclador(revisor_id=1, clave_item=clave_item("Aguja 25/8"),
                                              nombre_item="Aguja 25/8", texto="vieja", validacion="si"))
        db.session.commit()
    # Aunque se agreguen parámetros, la descarga sale solo de la sesión.
    r = ana.get("/revision/mis-revisiones.xlsx?revisor_id=2&todo=1")
    assert r.status_code == 200 and r.mimetype.endswith("spreadsheetml.sheet")
    assert r.headers["Cache-Control"] == "no-store"
    hojas = hojas_xlsx(r.data)
    assert list(hojas) == ["COINCIDENCIAS", "NO COINCIDEN", "DUDAS"]
    assert len(hojas["COINCIDENCIAS"]) == 1 and len(hojas["DUDAS"]) == 1  # solo encabezado
    encabezado, *filas = hojas["NO COINCIDEN"]
    assert encabezado == ["Código interno", "Código de artículo", "Bodega/centro de pedido", "Descripción hospital",
                          "Código TIMBÓ", "Descripción TIMBÓ", "Validación", "Observación", "Fecha de revisión"]
    assert len(filas) == 1
    assert filas[0][:8] == ["412", "", "", "Jeringa 5 ml", "38.6.1.1", "Bien — Ítem", "No, son diferentes",
                            "Es otra medida"]
    texto = r.data.decode("latin-1")
    for ajeno in ("De Beto", "Guantes", "Aguja", "Circuito", "Beto"):
        assert ajeno not in str(hojas), ajeno
    assert app.test_client().get("/revision/mis-revisiones.xlsx").status_code == 403  # sin llave
    assert texto  # el archivo no está vacío


def test_las_observaciones_sobreviven_a_la_reimportacion(app, nomenclador):
    c = app.test_client()
    entrar(c)
    guardar(c, "Guantes de látex M", "Ojo con el talle.", validacion="duda")
    with app.app_context():
        # importar_equivalencias.py borra y recarga todas las filas (cambian los id).
        EquivalenciaArticulo.query.delete()
        tema = Tema.query.filter_by(slug="timbo-compras").one()
        db.session.add(EquivalenciaArticulo(tema_id=tema.id, nombre_interno="Guantes  de LÁTEX m", confianza="dudosa"))
        db.session.commit()
    item = items_de_la_pagina(c)["Guantes  de LÁTEX m"]
    assert item["observacion"] == "Ojo con el talle." and item["validacion"] == "duda"


def test_panel_resumen_filtros_y_crea_accesos(app, beto, admin_client):
    ana, b = app.test_client(), app.test_client()
    entrar(ana)
    entrar(b, TOKEN_BETO)
    guardar(ana, "Guantes de látex M", "Falta el código.", validacion="si")
    html = admin_client.get("/admin/nomenclador/revision").get_data(as_text=True)
    for numero, texto in (("2", "Total amarillos"), ("1", "Confirmados"), ("0", "No coinciden"),
                          ("0", "Con dudas"), ("1", "Sin revisar")):
        assert re.search(rf"<b>{numero}</b><span>{texto}</span>", html), texto
    html = admin_client.get("/admin/nomenclador/revision?filtro=si").get_data(as_text=True)
    assert "Falta el código." in html and "Ana" in html and "Jeringa 5 ml" not in html
    html = admin_client.get("/admin/nomenclador/revision?filtro=pendiente").get_data(as_text=True)
    assert "Jeringa 5 ml" in html and "Falta el código." not in html
    html = admin_client.get("/admin/nomenclador/revision?filtro=con").get_data(as_text=True)
    assert "Falta el código." in html and "Jeringa 5 ml" not in html
    # Si dos personas responden distinto, el ítem pasa a "Con dudas".
    guardar(b, "Guantes de látex M", validacion="no")
    html = admin_client.get("/admin/nomenclador/revision?filtro=duda").get_data(as_text=True)
    assert "Guantes de látex M" in html and "respuestas distintas" in html

    r = admin_client.post("/admin/nomenclador/revisores", data={"nombre": "Carla"}, follow_redirects=True)
    url = re.search(r'id="rev-enlace-url">([^<]+)<', r.get_data(as_text=True)).group(1)
    token = url.split("#", 1)[1]
    with app.app_context():
        carla = RevisorNomenclador.query.filter_by(nombre="Carla").one()
        assert carla.token_hash == hash_token(token) and token not in carla.token_hash
    assert entrar(app.test_client(), token).status_code == 302
    # El enlace se muestra una sola vez.
    assert "rev-enlace-url" not in admin_client.get("/admin/nomenclador/revision").get_data(as_text=True)


def test_renovar_y_revocar_la_llave(app, nomenclador, admin_client):
    c = app.test_client()
    entrar(c)
    guardar(c, "Jeringa 5 ml", "Antes de renovar", validacion="si")
    r = admin_client.post("/admin/nomenclador/revisores/1/enlace", follow_redirects=True)
    nuevo = re.search(r'id="rev-enlace-url">([^<]+)<', r.get_data(as_text=True)).group(1).split("#", 1)[1]
    assert entrar(app.test_client()).status_code == 403          # la llave vieja ya no sirve
    c2 = app.test_client()
    assert entrar(c2, nuevo).status_code == 302
    assert items_de_la_pagina(c2)["Jeringa 5 ml"]["observacion"] == "Antes de renovar"  # no se pierde nada
    admin_client.post("/admin/nomenclador/revisores/1/estado")    # baja
    assert entrar(app.test_client(), nuevo).status_code == 403
    admin_client.post("/admin/nomenclador/revisores/1/estado")    # reactivar
    assert entrar(app.test_client(), nuevo).status_code == 302


def test_nomenclador_publico_con_colores_y_leyenda(app, nomenclador):
    html = app.test_client().get("/temas/timbo-compras/equivalencias").get_data(as_text=True)
    for texto in ("est-leyenda", "estado-verde", "estado-amarillo", "estado-rojo", "🔴 Hay que pedir que se agreguen"):
        assert texto in html, texto


def test_exportar_a_excel_en_cuatro_hojas(app, beto, admin_client):
    ana, b = app.test_client(), app.test_client()
    entrar(ana)
    entrar(b, TOKEN_BETO)
    guardar(ana, "Guantes de látex M", "Primera versión", validacion="duda")
    guardar(ana, "Guantes de látex M", "Talle; revisar", validacion="si")
    with app.app_context():
        db.session.add(ObservacionNomenclador(revisor_id=2, clave_item=clave_item("Aguja 25/8"),
                                              nombre_item="Aguja 25/8", texto="Ya en verde", validacion="si"))
        db.session.commit()
    r = admin_client.get("/admin/nomenclador/revision/exportar")
    assert r.status_code == 200 and "attachment" in r.headers["Content-Disposition"]
    assert r.headers["Content-Disposition"].endswith('.xlsx"')
    hojas = hojas_xlsx(r.data)
    assert list(hojas) == ["COINCIDENCIAS", "NO COINCIDEN", "DUDAS", "SIN REVISAR", "YA NO EN AMARILLO"]
    assert hojas["COINCIDENCIAS"][0] == ["Código interno", "Código de artículo", "Bodega/centro de pedido",
                                         "Descripción original", "Código TIMBÓ", "Descripción TIMBÓ", "Resultado",
                                         "Observación", "Revisor/a", "Fecha de revisión", "Versiones anteriores"]
    fila = hojas["COINCIDENCIAS"][1]
    assert fila[3] == "Guantes de látex M" and fila[6] == "Sí, son equivalentes" and fila[7] == "Talle; revisar"
    assert fila[8] == "Ana" and "Primera versión" in fila[10] and "Tengo dudas" in fila[10]
    assert len(hojas["NO COINCIDEN"]) == 1 and len(hojas["DUDAS"]) == 1
    assert [f[3] for f in hojas["SIN REVISAR"][1:]] == ["Jeringa 5 ml"] and hojas["SIN REVISAR"][1][0] == "412"
    assert hojas["YA NO EN AMARILLO"][1][:2] == ["Ahora en verde", "Aguja 25/8"]
    assert app.test_client().get("/admin/nomenclador/revision/exportar").status_code == 302  # sin login


def test_exportar_excel_de_una_persona(app, beto, admin_client):
    ana, b = app.test_client(), app.test_client()
    entrar(ana)
    entrar(b, TOKEN_BETO)
    guardar(ana, "Guantes de látex M", "De Ana", validacion="si")
    guardar(b, "Jeringa 5 ml", "De Beto", validacion="no")
    r = admin_client.get("/admin/nomenclador/revision/exportar?revisor=2")
    assert r.status_code == 200 and "beto" in r.headers["Content-Disposition"]
    hojas = hojas_xlsx(r.data)
    assert [f[3] for f in hojas["NO COINCIDEN"][1:]] == ["Jeringa 5 ml"] and len(hojas["COINCIDENCIAS"]) == 1
    assert "De Ana" not in str(hojas) and "Ana" not in str(hojas)
    assert admin_client.get("/admin/nomenclador/revision/exportar?revisor=99").status_code == 404
    assert b.get("/admin/nomenclador/revision/exportar?revisor=2").status_code == 302  # farmacia no puede


def test_excel_pinta_cada_fila_del_color_de_su_respuesta(app, nomenclador, admin_client):
    c = app.test_client()
    entrar(c)
    guardar(c, "Guantes de látex M", validacion="si")
    guardar(c, "Jeringa 5 ml", validacion="no")
    for url, cliente in (("/admin/nomenclador/revision/exportar", admin_client), ("/revision/mis-revisiones.xlsx", c)):
        z = zipfile.ZipFile(io.BytesIO(cliente.get(url).data))
        estilos = z.read("xl/styles.xml").decode()
        assert "FFE8F6EE" in estilos and "FFFBECEB" in estilos  # verde y rojo
        verde = z.read("xl/worksheets/sheet1.xml").decode()  # COINCIDENCIAS
        rojo = z.read("xl/worksheets/sheet2.xml").decode()   # NO COINCIDEN
        assert 'r="A2" t="inlineStr" s="3"' in verde and 'r="A2" t="inlineStr" s="4"' in rojo, url


def test_xlsx_es_un_archivo_valido():
    """La planilla se abre: zip con las partes que pide Excel y XML bien formado."""
    from xml.dom import minidom

    from app.services import xlsx
    contenido = xlsx.libro([("Hoja 'uno'", ["A", "B"], [["<&>", "ñ\x01"], [None, 3]], [10, 10])])
    z = zipfile.ZipFile(io.BytesIO(contenido))
    for parte in ("[Content_Types].xml", "_rels/.rels", "xl/workbook.xml", "xl/_rels/workbook.xml.rels",
                  "xl/styles.xml", "xl/worksheets/sheet1.xml"):
        minidom.parseString(z.read(parte))
    assert "&lt;&amp;&gt;" in z.read("xl/worksheets/sheet1.xml").decode()


def test_hora_de_argentina():
    from datetime import datetime

    from app.models.revision_nomenclador import hora_ar
    assert hora_ar(datetime(2026, 11, 16, 17, 47)) == "16/11/2026 14:47"
