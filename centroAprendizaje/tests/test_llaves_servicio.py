"""Revisión por servicio en línea: llaves con bodegas, acceso, respuestas,
necesidades, terminar y panel. Aparte de la revisión de Farmacia."""
import io
import json
import re
import zipfile

import pytest

from app.extensions import db
from app.models import EquivalenciaArticulo, ObservacionNomenclador, Tema
from app.models.revision_servicio import (
    LlaveServicio, NecesidadServicio, RevisionArticuloServicio, RevisionServicioHistorial,
)


@pytest.fixture()
def nomenclador(app):
    with app.app_context():
        tema = Tema(slug="timbo-compras", nombre="TIMBÓ Compras", orden=1)
        db.session.add(tema)
        db.session.flush()
        for nombre, conf, bodega, cod, codigo in (
            ("Mouse USB", "dudosa", "INFORMATICA", "700", "19.1.5.1"),
            ("Fax Panasonic", "alta", "INFORMATICA", "701", "19.1.9.9"),
            ("Cable UTP", "sin_match", "INFORMATICA", "702", None),
            ("Cable UTP", "sin_match", "MANTENIMIENTO", "702", None),   # compartido
            ("Llave inglesa", "alta", "MANTENIMIENTO", "800", "22.1.1.1"),
            ("Paracetamol", "alta", "FARMACIA", "900", "37.1.1.1"),
        ):
            db.session.add(EquivalenciaArticulo(tema_id=tema.id, nombre_interno=nombre, confianza=conf, bodega=bodega,
                                                codigo_interno=cod, codigo_catalogo=codigo, bien_o_servicio="X"))
        db.session.commit()


def _crear_llave(admin_client, servicio, bodegas):
    r = admin_client.post("/admin/servicios", data={"servicio": servicio, "bodegas": bodegas})
    assert r.status_code == 302
    with admin_client.session_transaction() as s:
        url = s["enlace_servicio_nuevo"]["url"]
    return url.split("#", 1)[1]


def _entrar(client, token, persona=("Ana", "Paz")):
    assert client.post("/servicio/acceso", data={"token": token}).status_code == 302
    client.post("/servicio/persona", data={"nombre": persona[0], "apellido": persona[1]})


def _datos(client):
    html = client.get("/servicio/").get_data(as_text=True)
    return json.loads(re.search(r'<script type="application/json" id="rs-datos"[^>]*>(.*?)</script>', html, re.S).group(1))


def _post(client, url, cuerpo):
    return client.post(url, data=json.dumps(cuerpo), content_type="application/json")


def test_panel_ofrece_bodegas_sin_farmacia(admin_client, nomenclador):
    html = admin_client.get("/admin/servicios").get_data(as_text=True)
    assert 'value="INFORMATICA"' in html and 'value="MANTENIMIENTO"' in html
    assert 'value="FARMACIA"' not in html


def test_crear_llave_exige_bodega(admin_client, nomenclador, app):
    admin_client.post("/admin/servicios", data={"servicio": "Informática", "bodegas": ["FARMACIA"]})
    with app.app_context():
        assert LlaveServicio.query.count() == 0


def test_sin_persona_pide_nombre_y_apellido(client, admin_client, nomenclador):
    token = _crear_llave(admin_client, "Informática", ["INFORMATICA"])
    client.post("/servicio/acceso", data={"token": token})
    html = client.get("/servicio/").get_data(as_text=True)
    assert 'name="apellido"' in html and "INFORMATICA" in html
    assert client.post("/servicio/persona", data={"nombre": "Ana", "apellido": ""}).status_code == 400


def test_token_invalido(client, nomenclador):
    assert client.post("/servicio/acceso", data={"token": "x" * 40}).status_code == 403
    assert client.get("/servicio/").status_code == 302


def test_ve_solo_sus_bodegas_y_compartidos_una_vez(client, admin_client, nomenclador):
    token = _crear_llave(admin_client, "Informática", ["INFORMATICA", "MANTENIMIENTO"])
    _entrar(client, token)
    ids = [i["id"] for i in _datos(client)["items"]]
    assert sorted(ids) == ["700", "701", "702", "800"]  # el 702 está en las dos bodegas: una sola vez
    assert "900" not in ids
    token2 = _crear_llave(admin_client, "Mantenimiento", ["MANTENIMIENTO"])
    _entrar(client, token2)
    items = {i["id"]: i for i in _datos(client)["items"]}
    assert sorted(items) == ["702", "800"]
    assert items["702"]["ob"] == ["INFORMATICA"]  # «también figura en»


def test_no_puede_responder_articulos_de_otra_bodega(client, admin_client, nomenclador):
    token = _crear_llave(admin_client, "Mantenimiento", ["MANTENIMIENTO"])
    _entrar(client, token)
    assert _post(client, "/servicio/respuesta", {"codigo": "700", "resultado": "correcto"}).status_code == 404
    assert _post(client, "/servicio/respuesta", {"codigo": "900", "resultado": "correcto"}).status_code == 404
    assert _post(client, "/servicio/respuesta", {"codigo": "800", "resultado": "inventado"}).status_code == 400


def test_respuesta_con_persona_historial_y_deshacer(client, admin_client, nomenclador, app):
    token = _crear_llave(admin_client, "Informática", ["INFORMATICA"])
    _entrar(client, token)
    assert _post(client, "/servicio/respuesta", {"codigo": "701", "resultado": "no_necesario"}).get_json()["ok"]
    _entrar(client, token, ("Beto", "Gil"))
    _post(client, "/servicio/respuesta", {"codigo": "701", "resultado": None, "observacion": ""})  # deshacer
    with app.app_context():
        r = RevisionArticuloServicio.query.filter_by(codigo_interno="701").one()
        assert r.resultado is None and r.persona == "Beto Gil"
        h = RevisionServicioHistorial.query.filter_by(revision_id=r.id).one()
        assert h.resultado == "no_necesario" and h.persona == "Ana Paz"
        assert ObservacionNomenclador.query.count() == 0  # Farmacia no se toca


def test_terminar_y_cualquier_cambio_reabre(client, admin_client, nomenclador, app):
    token = _crear_llave(admin_client, "Informática", ["INFORMATICA"])
    _entrar(client, token)
    assert _post(client, "/servicio/finalizar", {"observaciones": "todo ok"}).get_json()["finalizado"]
    r = _post(client, "/servicio/respuesta", {"codigo": "700", "resultado": "correcto"}).get_json()
    assert r["finalizado"] is None
    _post(client, "/servicio/finalizar", {})
    assert _post(client, "/servicio/finalizar", {"reabrir": True}).get_json()["finalizado"] is None
    with app.app_context():
        acciones = [x.accion for x in LlaveServicio.query.one().registro]
        assert "revisión terminada" in acciones and "revisión reabierta" in acciones


def test_necesidades_agregar_editar_quitar_y_volver(client, admin_client, nomenclador, app):
    token = _crear_llave(admin_client, "Informática", ["INFORMATICA"])
    _entrar(client, token)
    assert _post(client, "/servicio/necesidad", {"d": ""}).status_code == 400
    r = _post(client, "/servicio/necesidad", {"d": "Toner 85A", "tipo": "otro", "cat": "no_esta", "cod": "ignorar"}).get_json()
    nid = r["id"]
    assert r["necesidades"][nid]["cod"] == ""  # sin «está en el catálogo», el código no se guarda
    _post(client, "/servicio/necesidad", {"id": nid, "d": "Toner 85A original", "tipo": "otro", "cat": "no_esta"})
    assert _post(client, "/servicio/necesidad/quitar", {"id": nid, "quitar": True}).get_json()["necesidades"][nid]["baja"]
    assert not _post(client, "/servicio/necesidad/quitar", {"id": nid, "quitar": False}).get_json()["necesidades"][nid]["baja"]
    with app.app_context():
        n = NecesidadServicio.query.one()
        assert n.descripcion == "Toner 85A original" and n.quitada_en is None and n.persona == "Ana Paz"
        assert any("antes:" in x.detalle for x in LlaveServicio.query.one().registro)


def test_otra_llave_no_toca_necesidades_ajenas(client, admin_client, nomenclador):
    t1 = _crear_llave(admin_client, "Informática", ["INFORMATICA"])
    t2 = _crear_llave(admin_client, "Mantenimiento", ["MANTENIMIENTO"])
    _entrar(client, t1)
    nid = _post(client, "/servicio/necesidad", {"d": "Toner"}).get_json()["id"]
    _entrar(client, t2)
    assert _post(client, "/servicio/necesidad", {"id": nid, "d": "pisado"}).status_code == 404
    assert _post(client, "/servicio/necesidad/quitar", {"id": nid, "quitar": True}).status_code == 404


def test_baja_corta_el_acceso_en_el_momento(client, admin_client, nomenclador, app):
    token = _crear_llave(admin_client, "Informática", ["INFORMATICA"])
    _entrar(client, token)
    with app.app_context():
        llave_id = LlaveServicio.query.one().id
    admin_client.post(f"/admin/servicios/{llave_id}/estado")
    assert _post(client, "/servicio/respuesta", {"codigo": "700", "resultado": "correcto"}).status_code == 403
    admin_client.post(f"/admin/servicios/{llave_id}/estado")  # se reactiva: el mismo enlace vuelve a andar
    _entrar(client, token)
    assert _post(client, "/servicio/respuesta", {"codigo": "700", "resultado": "correcto"}).status_code == 200


def test_sacar_bodega_conserva_respuestas(client, admin_client, nomenclador, app):
    token = _crear_llave(admin_client, "Informática", ["INFORMATICA", "MANTENIMIENTO"])
    _entrar(client, token)
    _post(client, "/servicio/respuesta", {"codigo": "800", "resultado": "correcto"})
    with app.app_context():
        llave_id = LlaveServicio.query.one().id
    admin_client.post(f"/admin/servicios/{llave_id}/bodegas", data={"bodegas": ["INFORMATICA"]})
    assert "800" not in [i["id"] for i in _datos(client)["items"]]
    admin_client.post(f"/admin/servicios/{llave_id}/bodegas", data={"bodegas": ["INFORMATICA", "MANTENIMIENTO"]})
    assert _datos(client)["estado"]["respuestas"]["800"]["r"] == "correcto"


def test_diferencias_entre_servicios(client, admin_client, nomenclador):
    t1 = _crear_llave(admin_client, "Informática", ["INFORMATICA"])
    t2 = _crear_llave(admin_client, "Mantenimiento", ["MANTENIMIENTO"])
    _entrar(client, t1)
    _post(client, "/servicio/respuesta", {"codigo": "702", "resultado": "correcto"})
    _entrar(client, t2)
    _post(client, "/servicio/respuesta", {"codigo": "702", "resultado": "no_necesario"})
    assert "No hay diferencias" in admin_client.get("/admin/servicios").get_data(as_text=True)
    _post(client, "/servicio/respuesta", {"codigo": "702", "resultado": "no_corresponde"})
    html = admin_client.get("/admin/servicios").get_data(as_text=True)
    assert "Diferencias entre servicios (1)" in html


def test_excel_del_panel(client, admin_client, nomenclador):
    token = _crear_llave(admin_client, "Informática", ["INFORMATICA"])
    _entrar(client, token)
    _post(client, "/servicio/respuesta", {"codigo": "701", "resultado": "no_necesario"})
    _post(client, "/servicio/necesidad", {"d": "Toner 85A"})
    r = admin_client.get("/admin/servicios/exportar")
    assert r.status_code == 200
    with zipfile.ZipFile(io.BytesIO(r.data)) as z:
        libro = z.read("xl/workbook.xml").decode()
        textos = "".join(z.read(n).decode() for n in z.namelist() if n.startswith("xl/worksheets/"))
    for hoja in ("CORRECTOS", "NO CORRESPONDEN", "NO SE USAN", "SIN REVISAR", "FALTAN EN EL NOMENCLADOR", "DIFERENCIAS ENTRE SERVICIOS"):
        assert hoja in libro
    assert "Fax Panasonic" in textos and "Toner 85A" in textos and "Ana Paz" in textos


def test_la_llave_no_da_acceso_al_panel(app, admin_client, nomenclador):
    token = _crear_llave(admin_client, "Informática", ["INFORMATICA"])
    servicio = app.test_client()  # otra PC: solo con la llave, sin sesión de admin
    _entrar(servicio, token)
    assert servicio.get("/servicio/").status_code == 200
    assert servicio.get("/admin/servicios").status_code == 302
    assert servicio.get("/admin/servicios/exportar").status_code == 302


def test_decision_y_planilla_final(client, admin_client, nomenclador, app):
    token = _crear_llave(admin_client, "Informática", ["INFORMATICA", "MANTENIMIENTO"])
    _entrar(client, token)
    _post(client, "/servicio/respuesta", {"codigo": "702", "resultado": "correcto"})             # sección 1: falta en el catálogo
    _post(client, "/servicio/respuesta", {"codigo": "700", "resultado": "no_corresponde", "decision": "agregar"})
    _post(client, "/servicio/respuesta", {"codigo": "800", "resultado": "no_corresponde", "decision": "codigo",
                                          "codigo_correcto": "22.1.1.7"})
    _post(client, "/servicio/respuesta", {"codigo": "701", "resultado": "no_necesario", "decision": "agregar"})  # se ignora
    _post(client, "/servicio/necesidad", {"d": "Toner 85A", "tipo": "otro", "cat": "no_esta"})
    assert _post(client, "/servicio/respuesta", {"codigo": "700", "resultado": "no_corresponde", "decision": "x"}).status_code == 400
    with app.app_context():
        from app.services import llaves_servicio as ls
        llave = LlaveServicio.query.one()
        assert RevisionArticuloServicio.query.filter_by(codigo_interno="701").one().decision is None
        g = ls.planilla_final(llave)
        cargar = {f[2] or f[3] for f in g["cargar"]}
        assert cargar == {"702", "700", "Toner 85A"}
        estan = {f[2]: f for f in g["estan"]}
        assert estan["800"][6] == "22.1.1.7"  # código que indicó el servicio
        assert {f[2] for f in g["fuera"]} == {"701"}
        assert ls.sin_decidir(llave) == []
    # Cambiar el resultado borra la decisión (queda en el historial).
    _post(client, "/servicio/respuesta", {"codigo": "700", "resultado": "correcto"})
    with app.app_context():
        r = RevisionArticuloServicio.query.filter_by(codigo_interno="700").one()
        assert r.decision is None and r.historial[0].decision == "agregar"
    r = client.get("/servicio/planilla-final.xlsx")
    assert r.status_code == 200
    with zipfile.ZipFile(io.BytesIO(r.data)) as z:
        textos = "".join(z.read(n).decode() for n in z.namelist() if n.startswith("xl/"))
    for hoja in ("HAY QUE CARGAR EN CATALOGO WEB", "YA ESTAN EN TIMBO", "NO SE REVISARON", "QUEDAN FUERA"):
        assert hoja in textos
    assert "22.1.1.7" in textos and "Toner 85A" in textos
    assert app.test_client().get("/servicio/planilla-final.xlsx").status_code == 403
    libro = admin_client.get("/admin/servicios/exportar").data
    with zipfile.ZipFile(io.BytesIO(libro)) as z:
        assert "PEDIR EL ALTA EN CATALOGO WEB" in z.read("xl/workbook.xml").decode()


def test_item_general_con_detalle(client, admin_client, nomenclador, app):
    token = _crear_llave(admin_client, "Informática", ["INFORMATICA"])
    _entrar(client, token)
    _post(client, "/servicio/respuesta", {"codigo": "702", "resultado": "correcto", "decision": "general",
                                          "codigo_correcto": "19.4.4.1", "detalle_timbo": "Remanufactura tóner Brother TN-760"})
    _post(client, "/servicio/respuesta", {"codigo": "700", "resultado": "correcto", "decision": "general",
                                          "detalle_timbo": "Mouse óptico USB negro"})   # usa el código propuesto
    _post(client, "/servicio/respuesta", {"codigo": "701", "resultado": "no_necesario", "detalle_timbo": "se ignora"})
    with app.app_context():
        from app.services import llaves_servicio as ls
        llave = LlaveServicio.query.one()
        estan = {f[2]: f for f in ls.planilla_final(llave)["estan"]}
        assert estan["702"][6] == "19.4.4.1" and estan["702"][7] == "Remanufactura tóner Brother TN-760"
        assert estan["700"][6] == "19.1.5.1" and "ítem general" in estan["700"][1]
        assert RevisionArticuloServicio.query.filter_by(codigo_interno="701").one().detalle_timbo == ""


def test_traer_respuestas_de_farmacia_sin_tocarlas(client, admin_client, nomenclador, app):
    from app.models import ObservacionNomenclador
    from app.models.revision_nomenclador import RevisorNomenclador, clave_item
    with app.app_context():
        rv = RevisorNomenclador(nombre="bereComputos", token_hash="x" * 64, activo=True)
        db.session.add(rv)
        db.session.flush()
        for nombre, val in (("Mouse USB", "no"), ("Fax Panasonic", "si"), ("Llave inglesa", "duda"), ("Paracetamol", "si")):
            db.session.add(ObservacionNomenclador(revisor_id=rv.id, clave_item=clave_item(nombre), nombre_item=nombre,
                                                  texto="ojo" if nombre == "Mouse USB" else "", validacion=val))
        db.session.commit()
        rv_id = rv.id
    token = _crear_llave(admin_client, "Informática", ["INFORMATICA"])
    _entrar(client, token)
    _post(client, "/servicio/respuesta", {"codigo": "701", "resultado": "no_necesario"})  # ya respondido: no se pisa
    with app.app_context():
        llave_id = LlaveServicio.query.one().id
    admin_client.post(f"/admin/servicios/{llave_id}/importar-farmacia", data={"revisor": rv_id})
    with app.app_context():
        r = {x.codigo_interno: x for x in RevisionArticuloServicio.query.filter_by(llave_id=llave_id)}
        assert r["700"].resultado == "no_corresponde" and r["700"].observacion == "ojo" and r["700"].decision is None
        assert "Farmacia" in r["700"].persona
        assert r["701"].resultado == "no_necesario"           # no se pisó
        assert "800" not in r and "900" not in r              # otras bodegas
        assert ObservacionNomenclador.query.count() == 4      # Farmacia intacta
    admin_client.post(f"/admin/servicios/{llave_id}/importar-farmacia", data={"revisor": rv_id})  # dos veces: no duplica
    with app.app_context():
        assert RevisionArticuloServicio.query.filter_by(llave_id=llave_id).count() == 2


def test_no_es_de_este_servicio_queda_fuera(client, admin_client, nomenclador, app):
    token = _crear_llave(admin_client, "Informática", ["INFORMATICA"])
    _entrar(client, token)
    assert _post(client, "/servicio/respuesta", {"codigo": "702", "resultado": "otro_servicio"}).status_code == 200
    with app.app_context():
        from app.services import llaves_servicio as ls
        final = ls.planilla_final(LlaveServicio.query.one())
        assert any("702" in fila for fila in final["fuera"])
    r = admin_client.get("/admin/servicios/exportar")
    with zipfile.ZipFile(io.BytesIO(r.data)) as z:
        assert "NO SON DE ESTE SERVICIO" in z.read("xl/workbook.xml").decode()


def test_ya_estan_en_timbo_cuentan_como_ya_estan_sin_responder(client, admin_client, nomenclador, app):
    token = _crear_llave(admin_client, "Informática", ["INFORMATICA"])
    _entrar(client, token)
    with app.app_context():
        from app.services import llaves_servicio as ls
        final = ls.planilla_final(LlaveServicio.query.one())
        assert any("701" in fila for fila in final["estan"])   # «alta» = sección 3


def test_enviar_cierra_la_revision_y_el_admin_la_reabre(client, admin_client, nomenclador, app):
    token = _crear_llave(admin_client, "Informática", ["INFORMATICA"])
    _entrar(client, token)
    _post(client, "/servicio/respuesta", {"codigo": "700", "resultado": "correcto"})
    assert _post(client, "/servicio/enviar", {}).status_code == 400           # hace falta confirmar
    r = _post(client, "/servicio/enviar", {"confirmo": True}).get_json()
    assert r["enviado"] and r["finalizado"]
    assert _datos(client)["servidor"]["enviado"]
    # Enviada: no se puede cambiar nada, y lo guardado sigue igual
    r = _post(client, "/servicio/respuesta", {"codigo": "700", "resultado": "no_necesario"})
    assert r.status_code == 409 and r.get_json()["enviado"]
    assert _post(client, "/servicio/necesidad", {"d": "Toner"}).status_code == 409
    assert _post(client, "/servicio/finalizar", {"reabrir": True}).status_code == 409
    with app.app_context():
        llave = LlaveServicio.query.one()
        assert llave.revisiones[0].resultado == "correcto"
        llave_id = llave.id
    # Solo el administrador la reabre; las respuestas se conservan
    assert admin_client.post(f"/admin/servicios/{llave_id}/reabrir").status_code == 302
    _entrar(client, token)
    assert _post(client, "/servicio/respuesta", {"codigo": "700", "resultado": "no_necesario"}).status_code == 200
    with app.app_context():
        acciones = [x.accion for x in LlaveServicio.query.one().registro]
        assert "revisión enviada" in acciones and "revisión reabierta por el administrador" in acciones


def test_copia_de_lo_enviado_y_tutorial(client, admin_client, nomenclador):
    token = _crear_llave(admin_client, "Informática", ["INFORMATICA"])
    _entrar(client, token)
    _post(client, "/servicio/respuesta", {"codigo": "702", "resultado": "correcto"})
    html = client.get("/servicio/copia").get_data(as_text=True)
    assert "Borrador" in html and "Cable UTP" in html
    _post(client, "/servicio/enviar", {"confirmo": True})
    html = client.get("/servicio/copia").get_data(as_text=True)
    assert "Copia de lo enviado" in html and "Ana Paz" in html
    assert html.index("Hay que cargar en TIMBÓ") < html.index("Ya están en TIMBÓ") < html.index("No se revisaron") < html.index("Quedan fuera")
    assert client.get("/servicio/tutorial").status_code == 200


def test_item_de_solo_devuelve_articulos_de_sus_bodegas(app, admin_client, nomenclador):
    _crear_llave(admin_client, "Informática", ["INFORMATICA"])
    with app.app_context():
        from app.services import llaves_servicio as ls
        llave = LlaveServicio.query.one()
        assert ls.item_de(llave, "700")["n"] == "Mouse USB"
        assert ls.item_de(llave, "800") is None       # es de MANTENIMIENTO
        assert ls.item_de(llave, "900") is None       # FARMACIA nunca


def test_limite_de_respuestas_cuenta_por_llave_y_no_por_ip(app, client, admin_client, nomenclador):
    from app.seguridad import limitador
    t1 = _crear_llave(admin_client, "Informática", ["INFORMATICA"])
    t2 = _crear_llave(admin_client, "Mantenimiento", ["MANTENIMIENTO"])
    _entrar(client, t1)
    with app.app_context():
        ids = {ll.servicio: ll.id for ll in LlaveServicio.query}
    for _ in range(900):
        limitador.registrar(f"servicio-respuesta:llave-{ids['Informática']}", 600)
    assert _post(client, "/servicio/respuesta", {"codigo": "700", "resultado": "correcto"}).status_code == 429
    otro = app.test_client()          # misma IP, otra llave: no queda bloqueado
    _entrar(otro, t2)
    assert _post(otro, "/servicio/respuesta", {"codigo": "800", "resultado": "correcto"}).status_code == 200


def test_tengo_una_duda_lleva_a_la_consulta_con_el_servicio(client, admin_client, nomenclador):
    assert "consultas/nueva?contexto=Revisi" in client.get("/servicio/instructivo").get_data(as_text=True)
    token = _crear_llave(admin_client, "Informática", ["INFORMATICA"])
    _entrar(client, token)
    for url in ("/servicio/", "/servicio/instructivo", "/servicio/tutorial"):
        html = client.get(url).get_data(as_text=True)
        assert "consultas/nueva?contexto=Revisi%C3%B3n+de+art%C3%ADculos+%C2%B7+Inform%C3%A1tica" in html, url
