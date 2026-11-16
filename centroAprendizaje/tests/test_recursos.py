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
    herramientas = tuple(f"/recursos/{c}" for c in recursos.HERRAMIENTAS)
    for url in ("/recursos", "/recursos/roles", "/recursos/glosario", "/recursos/biblioteca", "/recursos/algoritmo",
                "/recursos/simulador", "/recursos/aprender", "/recursos/explicame", "/recursos/explicame?etapa=d-monto",
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
