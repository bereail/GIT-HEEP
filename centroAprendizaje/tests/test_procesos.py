"""Gestión de procesos y circuitos (/admin/procesos)."""
import json

import pytest

from app import recursos
from app.extensions import db
from app.models import AuditoriaProceso, Circuito, CircuitoVersion, ComentarioCircuito, RangoMonto, SugerenciaRelevamiento
from app.procesos import logica
from app.procesos.semilla import SLUG_HOSPITAL, SLUG_OFICIAL, contenido_oficial, sembrar


def _nodo(nid, tipo="actividad", **kw):
    n = {"id": nid, "tipo": tipo, "titulo": kw.pop("titulo", nid), "x": 0, "y": 0, "estado": "pendiente_confirmacion",
         "responsables": [], "fuentes": []}
    n.update(kw)
    return n


def _flecha(fid, desde, hasta, **kw):
    f = {"id": fid, "desde": desde, "hasta": hasta, "etiqueta": "", "tipo": "normal", "rango": None}
    f.update(kw)
    return f


@pytest.fixture()
def sembrado(app):
    with app.app_context():
        sembrar()


# ------------------------------------------------------------------ permisos

RUTAS_GET = ["/admin/procesos/", f"/admin/procesos/{SLUG_OFICIAL}", f"/admin/procesos/{SLUG_OFICIAL}/historial",
             f"/admin/procesos/{SLUG_OFICIAL}/informe", f"/admin/procesos/{SLUG_OFICIAL}/exportar.json",
             "/admin/procesos/comparar", "/admin/procesos/montos", "/admin/procesos/relevamiento",
             f"/admin/procesos/{SLUG_OFICIAL}/version/1"]


@pytest.mark.parametrize("ruta", RUTAS_GET)
def test_sin_sesion_no_se_entra(client, sembrado, ruta):
    r = client.get(ruta)
    assert r.status_code == 302 and "/admin/login" in r.headers["Location"]


def test_sin_sesion_no_se_guarda(client, sembrado, app):
    r = client.post(f"/admin/procesos/{SLUG_OFICIAL}/borrador", json={"contenido": {"nodos": [], "flechas": []}})
    assert r.status_code == 302
    with app.app_context():
        assert Circuito.query.filter_by(slug=SLUG_OFICIAL).first().contenido["nodos"]  # no se borró nada


@pytest.mark.parametrize("ruta", RUTAS_GET)
def test_con_sesion_todas_las_pantallas_responden(admin_client, sembrado, ruta):
    assert admin_client.get(ruta).status_code == 200


def test_el_editor_no_tiene_js_en_linea(admin_client, sembrado):
    html = admin_client.get(f"/admin/procesos/{SLUG_HOSPITAL}").get_data(as_text=True)
    assert "onclick=" not in html and "procesos-editor.js" in html
    assert 'id="procesos-datos" nonce=' in html


# ------------------------------------------------------------ carga inicial

def test_semilla_crea_los_dos_circuitos_y_no_pisa(app):
    with app.app_context():
        assert sembrar()
        oficial = Circuito.query.filter_by(slug=SLUG_OFICIAL).first()
        hospital = Circuito.query.filter_by(slug=SLUG_HOSPITAL).first()
        assert oficial.clase == "oficial" and hospital.clase == "hospital"
        assert hospital.contenido == {"nodos": [], "flechas": []}  # el del hospital arranca vacío
        assert len(oficial.versiones) == 1
        oficial.borrador = json.dumps({"nodos": [], "flechas": []})
        db.session.commit()
        assert sembrar() == []  # segunda vez: nada
        assert Circuito.query.filter_by(slug=SLUG_OFICIAL).first().contenido["nodos"] == []


def test_circuito_oficial_solo_con_fuentes_de_la_biblioteca(app):
    """Cada bloque oficial cita documentos que existen en la biblioteca, con
    fragmento; lo que no tiene fuente está marcado como pendiente."""
    docs = recursos.documentos_por_id()
    with app.app_context():
        sembrar()
        rangos = {r.nombre: r.id for r in RangoMonto.query.all()}
    contenido = contenido_oficial(rangos)
    normal, ajustes = logica.normalizar(contenido, "oficial", docs)
    assert ajustes == []
    for n in normal["nodos"]:
        assert n["estado"] != "confirmado_equipo"
        for f in n["fuentes"]:
            assert f["doc"] in docs and f["fragmento"] and f["punto"]
        if not n["fuentes"]:
            assert n["estado"] in ("pendiente_documentacion", "sin_respaldo"), n["titulo"]
    errores = [o for o in logica.revisar(normal, "oficial", {r: {"nombre": "x", "fuente_doc": "a", "estado": "verificado"} for r in rangos.values()}, docs=docs)
               if o["nivel"] == "error"]
    assert errores == []


def test_rangos_2026_copiados_de_la_circular(app):
    with app.app_context():
        sembrar()
        r = {x.nombre: x for x in RangoMonto.query.all()}
    assert float(r["Encuadre: contratación directa por monto"].maximo) == 5850000
    assert float(r["Encuadre: licitación o concurso privado"].maximo) == 58500000
    assert r["Encuadre: licitación o concurso público"].maximo is None
    assert all(x.fuente_doc == "circ-scygb-1-2026" and x.estado == "verificado" for x in r.values())


# -------------------------------------------------------------------- reglas

def test_documentado_sin_fuente_verificada_baja_a_pendiente():
    c = {"nodos": [_nodo("a", estado="documentado", fuentes=[{"doc": "circ-ug-7-2026", "verificada": False}])], "flechas": []}
    normal, ajustes = logica.normalizar(c, "hospital")
    assert normal["nodos"][0]["estado"] == "pendiente_documentacion" and ajustes


def test_en_el_oficial_no_se_usa_confirmado_por_el_equipo():
    c = {"nodos": [_nodo("a", estado="confirmado_equipo")], "flechas": []}
    normal, ajustes = logica.normalizar(c, "oficial")
    assert normal["nodos"][0]["estado"] == "pendiente_documentacion" and ajustes
    normal_h, ajustes_h = logica.normalizar(c, "hospital")
    assert normal_h["nodos"][0]["estado"] == "confirmado_equipo" and not ajustes_h


def test_no_se_guardan_fuentes_inventadas():
    c = {"nodos": [_nodo("a", fuentes=[{"doc": "documento-que-no-existe", "verificada": True},
                                       {"url": "javascript:alert(1)", "titulo": "x", "verificada": True},
                                       {"url": "https://www.santafe.gob.ar/x.pdf", "titulo": "Doc", "pagina": "3", "verificada": True}])],
         "flechas": []}
    normal, _ = logica.normalizar(c, "hospital")
    assert normal["nodos"][0]["fuentes"] == [{"doc": "", "url": "https://www.santafe.gob.ar/x.pdf", "titulo": "Doc", "emisor": "",
                                              "fecha": "", "punto": "", "pagina": "3", "capitulo": "", "fragmento": "",
                                              "verificada": True}]


def test_ids_repetidos_se_rechazan():
    with pytest.raises(logica.ContenidoInvalido):
        logica.normalizar({"nodos": [_nodo("a"), _nodo("a")], "flechas": []}, "hospital")


# ----------------------------------------------------------------- revisión

def test_revision_detecta_los_huecos():
    c, _ = logica.normalizar({
        "nodos": [_nodo("i", "inicio"), _nodo("d", "decision"), _nodo("a"), _nodo("suelto"),
                  _nodo("e", "error"), _nodo("doc", "documento")],
        "flechas": [_flecha("f1", "i", "d"), _flecha("f2", "d", "a"), _flecha("f3", "a", "fantasma"),
                    _flecha("f4", "a", "doc", rango=99)],
    }, "hospital")
    msgs = " | ".join(o["mensaje"] for o in logica.revisar(c, "hospital", {}))
    assert "bifurcación incompleta" in msgs
    assert "Flecha sin destino" in msgs
    assert "no está conectado" in msgs           # «suelto»
    assert "error sin actividad asociada" in msgs
    assert "documento sin origen" in msgs
    assert "actividad sin responsable" in msgs
    assert "rango de montos que ya no existe" in msgs
    assert "no tiene un bloque de Fin" in msgs


def test_revision_oficial_pide_respaldo():
    c, _ = logica.normalizar({"nodos": [_nodo("a", estado="pendiente_confirmacion")], "flechas": []}, "oficial")
    assert any("sin respaldo documental" in o["mensaje"] for o in logica.revisar(c, "oficial", {}))


def test_revision_avisa_borrado_con_fuentes():
    anterior = {"nodos": [_nodo("a", titulo="Paso con fuente", fuentes=[{"doc": "circ-ug-7-2026", "verificada": True}])], "flechas": []}
    obs = logica.revisar({"nodos": [], "flechas": []}, "hospital", {}, anterior)
    assert any("Paso con fuente" in o["mensaje"] for o in obs)


def test_cambios_entre_versiones():
    a = {"nodos": [_nodo("a", titulo="Viejo"), _nodo("b")], "flechas": [_flecha("f", "a", "b")]}
    b = {"nodos": [_nodo("a", titulo="Nuevo"), _nodo("c")], "flechas": []}
    cambios = logica.cambios_entre(a, b)
    acciones = sorted(c["accion"] for c in cambios)
    assert acciones == ["agregado", "eliminado", "flecha eliminada", "modificado"]
    mod = next(c for c in cambios if c["accion"] == "modificado")
    assert "Viejo" in mod["antes"] and "Nuevo" in mod["despues"]


# ---------------------------------------------------------- guardado y versiones

def _contenido_simple():
    return {"nodos": [_nodo("i", "inicio", titulo="Llega el pedido"), _nodo("a", titulo="Compras revisa")],
            "flechas": [_flecha("f1", "i", "a")]}


def test_autoguardado_y_version(admin_client, sembrado, app):
    url = f"/admin/procesos/{SLUG_HOSPITAL}"
    r = admin_client.post(url + "/borrador", json={"contenido": _contenido_simple()})
    assert r.status_code == 200 and r.get_json()["ok"]
    with app.app_context():
        c = Circuito.query.filter_by(slug=SLUG_HOSPITAL).first()
        assert len(c.contenido["nodos"]) == 2 and not c.versiones  # el autoguardado no crea versiones
    r = admin_client.post(url + "/version", json={"contenido": _contenido_simple(), "motivo": "Reunión 1", "importante": True})
    j = r.get_json()
    assert j["numero"] == 1 and j["cambios"] == 3
    r = admin_client.post(url + "/version", json={"contenido": _contenido_simple(), "motivo": "Sin cambios"})
    assert r.get_json()["sin_cambios"]  # no se crea una versión vacía
    with app.app_context():
        v = CircuitoVersion.query.join(Circuito).filter(Circuito.slug == SLUG_HOSPITAL).one()
        assert v.motivo == "Reunión 1" and v.importante


def test_recuperar_version_no_borra_historia(admin_client, sembrado, app):
    url = f"/admin/procesos/{SLUG_HOSPITAL}"
    admin_client.post(url + "/version", json={"contenido": _contenido_simple(), "motivo": "v1"})
    otro = _contenido_simple()
    otro["nodos"][1]["titulo"] = "Compras revisa y firma"
    admin_client.post(url + "/version", json={"contenido": otro, "motivo": "v2"})
    admin_client.post(url + "/borrador", json={"contenido": {"nodos": [], "flechas": []}})  # cambio sin versión
    r = admin_client.post(url + "/version/1/recuperar", data={"motivo": "volver"})
    assert r.status_code == 302
    with app.app_context():
        c = Circuito.query.filter_by(slug=SLUG_HOSPITAL).first()
        assert [v.numero for v in c.versiones] == [1, 2, 3, 4]  # v3 = lo no guardado, v4 = recuperada
        assert c.contenido["nodos"][1]["titulo"] == "Compras revisa"
        assert c.versiones[2].contenido == json.dumps({"nodos": [], "flechas": []}, ensure_ascii=False)
        assert AuditoriaProceso.query.filter_by(accion="versión recuperada").count() == 1


def test_el_servidor_corrige_y_avisa(admin_client, sembrado):
    c = {"nodos": [_nodo("a", estado="confirmado_equipo")], "flechas": []}
    j = admin_client.post(f"/admin/procesos/{SLUG_OFICIAL}/borrador", json={"contenido": c}).get_json()
    assert j["ajustes"] and j["contenido"]["nodos"][0]["estado"] == "pendiente_documentacion"


def test_contenido_invalido_da_400(admin_client, sembrado):
    r = admin_client.post(f"/admin/procesos/{SLUG_HOSPITAL}/borrador", json={"contenido": "nada"})
    assert r.status_code == 400


def test_comentarios_no_cambian_el_circuito(admin_client, sembrado, app):
    with app.app_context():
        antes = Circuito.query.filter_by(slug=SLUG_OFICIAL).first().borrador
    j = admin_client.post(f"/admin/procesos/{SLUG_OFICIAL}/comentarios",
                          json={"elemento": "o12", "tipo": "santa_fe", "texto": "¿Qué pasa si rechaza?"}).get_json()
    assert j["ok"]
    r = admin_client.post(f"/admin/procesos/{SLUG_OFICIAL}/comentarios/{j['comentario']['id']}/resolver", json={})
    assert r.get_json()["resuelto"] is True
    with app.app_context():
        assert Circuito.query.filter_by(slug=SLUG_OFICIAL).first().borrador == antes
        assert ComentarioCircuito.query.filter_by(elemento_id="o12", tipo="santa_fe").count() >= 1


def test_crear_circuito(admin_client, sembrado, app):
    r = admin_client.post("/admin/procesos/nuevo", data={"nombre": "Compra de insumos", "clase": "hospital"})
    assert r.status_code == 302
    with app.app_context():
        assert Circuito.query.filter_by(nombre="Compra de insumos").one().clase == "hospital"


# ------------------------------------------------------------------- montos

def test_rango_sin_fuente_no_queda_verificado(admin_client, sembrado, app):
    r = admin_client.post("/admin/procesos/montos", data={"nombre": "Prueba", "minimo": "1.000", "maximo": "2.000",
                                                           "estado": "verificado", "fuente_doc": ""})
    assert r.status_code == 302
    with app.app_context():
        x = RangoMonto.query.filter_by(nombre="Prueba").one()
        assert x.estado == "pendiente" and float(x.minimo) == 1000 and float(x.maximo) == 2000


def test_discrepancia_de_rangos():
    rs = [{"nombre": "Directa", "minimo": None, "maximo": 5850000}, {"nombre": "directa ", "minimo": None, "maximo": 5000000}]
    assert len(logica.discrepancias_de_rangos(rs)) == 1


# -------------------------------------------------------------- comparación

def test_comparacion_usa_la_correspondencia(admin_client, sembrado):
    c = _contenido_simple()
    c["nodos"][1]["correspondencia"] = {"circuito": SLUG_OFICIAL, "nodo": "o09", "relacion": "difiere", "nota": "Lo hace a mano"}
    admin_client.post(f"/admin/procesos/{SLUG_HOSPITAL}/borrador", json={"contenido": c})
    html = admin_client.get("/admin/procesos/comparar").get_data(as_text=True)
    assert "Compras revisa" in html and "Se hace distinto" in html and "Lo hace a mano" in html
    assert "No relevado todavía" in html


# ------------------------------------------------------------- sugerencias

def test_sugerencias_se_registran_sin_evaluar(admin_client, sembrado, app):
    admin_client.post("/admin/procesos/relevamiento", data={"recurso": "nomenclador", "clase": "funcionalidad",
                                                            "texto": "Buscar por código interno"})
    with app.app_context():
        s = SugerenciaRelevamiento.query.one()
        assert s.estado == "nueva" and s.clase == "funcionalidad"
        sid = s.id
    admin_client.post(f"/admin/procesos/relevamiento/{sid}", data={"estado": "aceptada", "nota": "Prioridad alta"})
    with app.app_context():
        assert db.session.get(SugerenciaRelevamiento, sid).estado == "aceptada"


def test_grafico_de_la_reunion_editable_y_con_fuentes(app, admin_client):
    """El flujo de compras del material de la reunión se carga como circuito
    editable, con carriles, sin errores de revisión y sin datos inventados."""
    from app.procesos.grafico_reunion import SLUG_REUNION, contenido_reunion
    docs = recursos.documentos_por_id()
    with app.app_context():
        sembrar()
        c = Circuito.query.filter_by(slug=SLUG_REUNION).one()
        rangos = {r.id: r.como_dict() for r in RangoMonto.query.all()}
        contenido = c.contenido
    assert len(contenido["carriles"]) == 3
    numeros = {int(n["titulo"].split(" · ")[0]) for n in contenido["nodos"] if n["titulo"][0].isdigit()}
    assert numeros == set(range(1, 22))  # los 21 pasos del gráfico
    assert not [o for o in logica.revisar(contenido, "oficial", rangos, docs=docs) if o["nivel"] == "error"]
    for n in contenido["nodos"]:
        for f in n["fuentes"]:
            assert f["doc"] in docs
    assert admin_client.get(f"/admin/procesos/{SLUG_REUNION}").status_code == 200
