"""Integridad de los datos de Recursos y del algoritmo de compras.

Los JSON de app/recursos se editan a mano cuando cambia la normativa: estos
tests evitan que quede una flecha a una etapa inexistente o una fuente citada
que no está en la biblioteca.
"""

from app import recursos


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
                          ("capacitacion", recursos.capacitacion()), ("algoritmo", recursos.algoritmo())]:
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
    for url in ("/recursos", "/recursos/roles", "/recursos/glosario", "/recursos/biblioteca"):
        assert anonimo.get(url).status_code == 200, url
    assert anonimo.get("/admin/capacitacion/algoritmo").status_code == 302
    admin = app.test_client()
    admin.post("/admin/login", data={"contrasena": "test-admin-pass"})
    r = admin.get("/admin/capacitacion/algoritmo")
    assert r.status_code == 200 and b"alg-datos" in r.data
