"""Integridad de los datos de Recursos y del algoritmo de compras.

Los JSON de app/recursos se editan a mano cuando cambia la normativa: estos
tests evitan que quede una flecha a una etapa inexistente o una fuente citada
que no está en la biblioteca.
"""

from pathlib import Path

from app import recursos

RAIZ = Path(__file__).resolve().parent.parent


def _ids_citados(obj):
    if isinstance(obj, dict):
        for clave, valor in obj.items():
            if clave == "fuentes" and isinstance(valor, list):
                for f in valor:
                    yield f["id"] if isinstance(f, dict) else f
            else:
                yield from _ids_citados(valor)
    elif isinstance(obj, list):
        for valor in obj:
            yield from _ids_citados(valor)


def test_todas_las_fuentes_citadas_existen_en_la_biblioteca():
    docs = recursos.documentos_por_id()
    for nombre, datos in [("roles", recursos.roles()), ("circuito", recursos.circuito()),
                          ("capacitacion", recursos.capacitacion()), ("algoritmo", recursos.algoritmo()),
                          ("herramientas", recursos.herramientas()), ("simulador", recursos.simulador()),
                          ("glosario", {"t": recursos.glosario()["terminos"]})]:
        faltan = {i for i in _ids_citados(datos) if i not in docs}
        assert not faltan, f"{nombre} cita fuentes que no están en biblioteca.json: {faltan}"
    for d in recursos.biblioteca()["discrepancias"]:
        assert all(i in docs for i in d["fuentes"])


def test_el_algoritmo_no_tiene_caminos_rotos():
    alg = recursos.algoritmo()
    nodos = alg["nodos"]
    assert alg["inicio"] in nodos
    for id_, n in nodos.items():
        for o in n.get("opciones", []):
            assert o["va"] in nodos, f"{id_} → {o['va']} no existe"
        for p in n.get("pasos", []):
            assert p in nodos, f"{id_} tiene el paso {p}, que no existe"
        if n.get("siguiente"):
            assert n["siguiente"] in nodos
        assert n.get("ficha", {}).get("fuentes"), f"{id_} no dice de dónde surge"


def test_cada_rama_termina_en_un_final():
    alg = recursos.algoritmo()
    nodos = alg["nodos"]
    for rama in alg["ramas"]:
        for inicio in ([rama["nodo"]] if "nodo" in rama else rama["nodos"]):
            pasos = nodos[inicio].get("pasos", [])
            assert pasos and nodos[pasos[-1]]["tipo"] == "fin", f"la rama {rama['letra']} ({inicio}) no termina en un final"


def test_paginas_de_recursos_y_algoritmo(app):
    anonimo = app.test_client()
    herramientas = tuple(f"/recursos/{c}" for c in recursos.HERRAMIENTAS if c not in recursos.OCULTOS_PUBLICO)
    for oculto in recursos.OCULTOS_PUBLICO:
        assert anonimo.get(f"/recursos/{oculto}").status_code == 404, oculto
        assert f"/recursos/{oculto}" not in anonimo.get("/").get_data(as_text=True)
    for url in ("/recursos", "/recursos/roles", "/recursos/glosario", "/recursos/biblioteca", "/recursos/algoritmo",
                "/recursos/aprender", "/recursos/explicame", "/recursos/explicame?etapa=d-monto",
                "/recursos/explicame?etapa=no-existe") + herramientas:
        assert anonimo.get(url).status_code == 200, url
    assert anonimo.get("/recursos/no-existe").status_code == 404
    assert anonimo.get("/admin/capacitacion/algoritmo").status_code == 302
    admin = app.test_client()
    admin.post("/admin/login", data={"contrasena": "test-admin-pass"})
    for url in ("/admin/capacitacion/modo-capacitadora", "/admin/capacitacion/modo-capacitadora?tema=pliego", "/admin/recursos/simulador"):
        assert admin.get(url).status_code == 200, url
    r = admin.get("/admin/capacitacion/algoritmo")
    assert r.status_code == 200 and b"alg-datos" in r.data


def test_simulador_sin_caminos_rotos():
    for esc in recursos.simulador()["escenarios"]:
        ids = {q["id"] for q in esc["preguntas"]}
        for q in esc["preguntas"]:
            assert sum(1 for o in q["opciones"] if o["correcta"]) == 1, f"{esc['slug']}/{q['id']} debe tener una sola correcta"
            for o in q["opciones"]:
                assert o.get("explicacion"), f"{esc['slug']}/{q['id']}: falta explicar una opción"
                if "va" in o:
                    assert o["va"] in ids, f"{esc['slug']}/{q['id']} → {o['va']} no existe"
            assert any(o.get("fuentes") for o in q["opciones"] if o["correcta"]) or esc["slug"] == "ascensores", f"{esc['slug']}/{q['id']}: la respuesta correcta no dice de dónde surge"


def test_diccionario_relacionados_y_modo_capacitadora():
    nombres = {t["termino"] for t in recursos.glosario()["terminos"]}
    for t in recursos.glosario()["terminos"]:
        for r in t.get("relacionados", []):
            assert r in nombres, f"{t['termino']} → {r} no existe en el diccionario"
    nodos = recursos.algoritmo()["nodos"]
    for tema in recursos.capacitacion()["temas_capacitadora"]:
        assert all(n in nodos for n in tema["diagrama"]), tema["slug"]
        assert tema["fuentes"] and tema["ejercicio"]["respuesta"], tema["slug"]


def test_explicame_apunta_a_etapas_que_existen():
    nodos = recursos.algoritmo()["nodos"]
    for p in recursos.capacitacion()["explicame"]:
        assert p["nodo"] in nodos, p["q"]
        assert p["fuentes"], p["q"]


def test_matriz_y_sistemas_completos():
    m = recursos.roles()["matriz"]
    assert all(len(f["celdas"]) == len(m["columnas"]) for f in m["filas"])
    assert {c["sistema"] for c in recursos.herramientas()["sistemas"]["columnas"]} == {"expediente", "compras", "externo"}
    assert any(e["slug"] == "evaluacion-final" and len(e["preguntas"]) >= 12 for e in recursos.simulador()["escenarios"])


def test_garantia_de_impugnacion_segun_pliego_unico():
    # Pliego Único, 10.1.3: 3% de la oferta de quien impugna (el 150% es la
    # contragarantía del anticipo). Tampoco existe un "día de gracia".
    texto = (RAIZ / "scripts" / "content_timbo_compras.json").read_text(encoding="utf-8")
    assert "3% del monto de tu oferta" in texto
    assert "día de gracia" not in texto


def test_buscador_global_encuentra_recursos(app):
    cliente = app.test_client()
    tipos = {r["kind"] for r in cliente.get("/buscar.json?q=preadjudicacion").get_json()}
    assert tipos & {"Diccionario", "Pregunta", "Recurso"}
    urls = [r["url"] for r in cliente.get("/buscar.json?q=roles supervisor").get_json()]
    assert any("/recursos/roles" in u for u in urls)
    assert not any("simulador" in r["url"] or "checklists" in r["url"]
                   for r in cliente.get("/buscar.json?q=simulador checklist").get_json())


def test_valorar_pagina_de_recursos(app):
    from app.models import EventoUso
    cliente = app.test_client()
    assert cliente.post("/recursos/valorar", json={"pagina": "/recursos/roles", "voto": "no"}).status_code == 200
    cliente.post("/recursos/valorar", json={"pagina": "/admin/algo", "voto": "si"})
    cliente.post("/recursos/valorar", json=["no"])
    with app.app_context():
        votos = EventoUso.query.filter_by(tipo="feedback_recurso").all()
        assert [(v.titulo, v.hubo_resultado) for v in votos] == [("/recursos/roles", False)]


def test_favicon(app):
    cliente = app.test_client()
    assert cliente.get("/favicon.ico").status_code == 301
    assert cliente.get("/static/img/favicon.svg").status_code == 200


def test_panel_muestra_la_revision_de_dependencias(app, admin_client):
    import os
    ruta = os.path.join(app.instance_path, "auditoria_dependencias.txt")
    try:
        with open(ruta, "w", encoding="utf-8") as f:
            f.write("01/12/2026\nFound 1 known vulnerability in 1 package\nflask 3.1.3 GHSA-xxxx")
        html = admin_client.get("/admin/").get_data(as_text=True)
        assert "hay librerías con fallas conocidas" in html and "01/12/2026" in html
        with open(ruta, "w", encoding="utf-8") as f:
            f.write("02/12/2026\nNo known vulnerabilities found")
        assert "sin fallas de seguridad conocidas" in admin_client.get("/admin/").get_data(as_text=True)
    finally:
        os.remove(ruta)


def test_ficha_para_asignar_roles(app, admin_client):
    html = app.test_client().get("/recursos/roles/ficha").get_data(as_text=True)
    for rol in ("Gestor", "Supervisor", "Evaluador", "Jurisdicción comitente", "administrador local"):
        assert rol in html
    assert "/recursos/roles/ficha" in app.test_client().get("/recursos/roles").get_data(as_text=True)
    assert admin_client.get("/admin/recursos/roles/ficha").status_code == 200


def test_montos_2026_iguales_a_la_circular(app):
    # Circular SCyGB N° 01/2026: si cambia un monto acá, tiene que cambiar ahí.
    html = app.test_client().get("/recursos/montos").get_data(as_text=True)
    for texto in ("Hasta $5.850.000", "Contratación directa por monto", "Hasta $29.250.000", "Hasta $58.500.000",
                  "Licitación o concurso privado", "Más de $58.500.000", "Licitación o concurso público",
                  "Resolución conjunta con el Ministerio de Economía", "Decreto", "Circular-001-26.pdf"):
        assert texto in html, texto


def test_sitio_publico_solo_muestra_lo_verificado(app):
    # Regla de la usuaria (16/11/2026): nada sin verificar en el sitio público.
    cliente = app.test_client()
    for url in ("/", "/recursos", "/recursos/roles", "/recursos/roles/ficha", "/recursos/glosario", "/recursos/biblioteca",
                "/recursos/algoritmo", "/recursos/explicame", "/recursos/aprender", "/recursos/plazos",
                "/recursos/a-quien-preguntar", "/recursos/montos"):
        html = cliente.get(url).get_data(as_text=True)
        for marca in ("rec-estado--pendiente", "rec-estado--didactico", "rec-estado--practica", "EJEMPLO DIDÁCTICO",
                      '"estado": "pendiente"', '"estado": "didactico"'):
            assert marca not in html, (url, marca)
    # Los modelos de mensajes se ven (pedido de la usuaria): son plantillas, marcadas como didácticas.
    assert cliente.get("/recursos/modelos").status_code == 200


def test_flujos_paso_a_paso_en_el_panel(app, admin_client):
    html = admin_client.get("/admin/recursos/flujos").get_data(as_text=True)
    for texto in ("Gestión directa por monto", "Licitación o concurso público", "Control del pliego (URC)", "flujo-c-privada"):
        assert texto in html, texto
    assert app.test_client().get("/admin/recursos/flujos").status_code in (302, 401)


def test_topes_al_pasar_el_mouse_salen_de_la_circular(app):
    import json
    import re
    html = app.test_client().get("/").get_data(as_text=True)
    datos = json.loads(re.search(r'<script type="application/json" id="topes-datos"[^>]*>(.*?)</script>', html, re.S).group(1))
    textos = " ".join(t["texto"] for t in datos)
    for monto in ("hasta $5.850.000", "hasta $58.500.000", "más de $58.500.000", "hasta $29.250.000"):
        assert monto in textos, monto
    assert "/static/js/topes.js" in html


def test_grafico_de_flujo_solo_en_el_panel(app, admin_client):
    assert app.test_client().get("/recursos/grafico").status_code == 404
    assert "recursos/grafico" not in app.test_client().get("/").get_data(as_text=True)
    html = admin_client.get("/admin/recursos/grafico").get_data(as_text=True)
    assert "<svg" in html and "<polygon" in html  # un diagrama de verdad, con rombos
    for texto in ("Hasta $5.850.000", "Licitación o concurso público", "Convenio Marco", "Etapa contractual", "#flujo-c-privada"):
        assert texto in html, texto


def test_seccion_para_proveedores(app, admin_client):
    html = app.test_client().get("/recursos/proveedores").get_data(as_text=True)
    for texto in ("santafe.gov.ar/proveedores", "ComoCompletarFormulario.pdf", "3% del monto de la oferta", "7% del valor total",
                  "timbocompras@santafe.gob.ar", "Copiar mensaje", "http://localhost/recursos/proveedores"):
        assert texto in html, texto
    assert admin_client.get("/admin/recursos/proveedores").status_code == 200


def test_formularios_con_link_oficial(app):
    import json
    import re
    html = app.test_client().get("/").get_data(as_text=True)
    datos = json.loads(re.search(r'<script type="application/json" id="enlaces-datos"[^>]*>(.*?)</script>', html, re.S).group(1))
    por_frase = {f: d["url"] for d in datos for f in d["frases"]}
    assert por_frase["Timbó Compras: Alta de bienes y servicios CAByS"] == "https://tramites.santafe.gob.ar/"
    assert por_frase["CD-01"] == "https://tramites.santafe.gob.ar/"
    assert por_frase["Pliego Único"].startswith("https://compras.santafe.gob.ar/")
