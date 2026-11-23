"""Control final antes de pedir altas: encuentra lo que ya existe, lo que
apareció después del envío y los repetidos. Solo lee."""
import os
import time
from datetime import datetime, timezone
from types import SimpleNamespace

from app.services import catalogo_diario as cd
from app.services import control_altas as ca
from app.services import llaves_servicio as ls

ENC = '"' + '"|"'.join(cd.COLUMNAS) + '"\n'


def csv_catalogo(items):
    """items: {código: (bien, ítem)}"""
    return "﻿" + ENC + "".join(f'"19 - INFORMATICA"|"19.1 - EQUIPOS"|19.1.5|"{b}"|"4.3.6"|{c}|"{i}"|\n'
                                for c, (b, i) in items.items())


def guardar(carpeta, nombre, items, momento):
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, nombre)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(csv_catalogo(items))
    os.utime(ruta, (momento, momento))
    return ruta


def fila(codigo, nombre, propuesto="", grupo_accion="Pedir el alta: no está en el catálogo"):
    return ["INFORMATICA", grupo_accion, codigo, nombre, "INFORMATICA", propuesto, "", "", "", "", "", "Ana", ""]


VIEJO = {"19.1.5.1": ("PENDRIVE", "PENDRIVE 16 GB"), "19.1.5.2": ("MOUSE", "MOUSE OPTICO USB"),
         "19.1.5.3": ("TECLADO", "TECLADO USB NO UTILIZAR")}


def test_palabras_separa_numeros_y_saca_tildes():
    assert ca.palabras("PenDrive 32GB") == {"pendrive"} and ca.medida("PenDrive 32GB") == {"32", "gb"}
    assert ca.palabras("Cámaras de seguridad") == {"camara", "seguridad"}
    assert ca.medida("Cable 2 mts") == ca.medida("cable 2 metros") == {"2", "metro"}
    assert ca.objeto_del_gasto("2.9.6.0 Repuestos y accesor.") == ["2", "9", "6", "0"]


def test_pen_drive_separado_y_otra_medida():
    catalogo = {"19.1.143.3": ["19 - INF", "19.1 - EQ", "19.1.143", "PEN DRIVE", "2.9.6.0 Rep.", "19.1.143.3", "PEN DRIVE 8 GB.", ""]}
    hallados = ca.Buscador(catalogo).buscar("PENDRIVE 16GB")
    assert hallados[0]["codigo"] == "19.1.143.3" and hallados[0]["pct"] == 100 and not hallados[0]["misma_medida"]
    assert not ca._repetidos("Patchcord Cat 6 1.5", "Patchcord Cat 6 2.5")
    assert ca._repetidos("FUENTE ALIMENTACIO ATX 550W", "fuente atx 550w o superior")


def test_control_clasifica_y_no_toca_nada(tmp_path, monkeypatch):
    inst = str(tmp_path)
    carpeta = cd.carpeta_catalogo(inst)
    envio = datetime(2026, 11, 23, 10, 0)
    antes = envio.replace(tzinfo=timezone.utc).timestamp() - 3600
    guardar(carpeta, "catalogo_20261123-060000.csv", VIEJO, antes)
    nuevo = dict(VIEJO, **{"19.1.5.9": ("PENDRIVE", "PENDRIVE 32 GB")})
    guardar(carpeta, "catalogo_20261123-120000.csv", nuevo, time.time())

    grupos = {"cargar": [fila("1", "PenDrive 32GB"), fila("2", "Mouse óptico USB"), fila("3", "Cable HDMI 2 metros"),
                         fila("4", "Cable HDMI 2 mts"), fila("5", "10 x 20")],
              "estan": [["INFORMATICA", "Usar el código propuesto", "6", "Teclado", "", "19.1.5.3", "19.1.5.3"] + [""] * 6,
                        ["INFORMATICA", "Usar el código propuesto", "7", "Fax", "", "19.1.5.77", "19.1.5.77"] + [""] * 6,
                        ["INFORMATICA", "Usar el código propuesto", "8", "Mouse", "", "19.1.5.2", "19.1.5.2"] + [""] * 6],
              "fuera": [], "falta": []}
    monkeypatch.setattr(ls, "planilla_final", lambda llave, tema=None: grupos)
    monkeypatch.setattr(ls, "items_de", lambda llave, tema=None: ([], []))
    llave = SimpleNamespace(enviado_en=envio, servicio="INFORMATICA", revisiones=[], nombres_bodegas=["INFORMATICA"])

    r = ca.control(llave, inst)
    estado = {f["codigo"]: f["estado"] for f in r["filas"]}
    assert estado == {"1": "aparecio", "2": "puede_existir", "3": "repetido", "4": "repetido", "5": "sin_buscar"}
    assert r["nuevos"] == 1 and r["comparado_con"] == "catalogo_20261123-060000.csv"
    pend = next(f for f in r["filas"] if f["codigo"] == "1")
    assert pend["parecidos"][0]["codigo"] == "19.1.5.9" and pend["parecidos"][0]["nuevo"]
    assert pend["sugerencia"]["rubro"] == "19 - INFORMATICA"
    # Los «NO UTILIZAR» nunca se sugieren; en «ya están» se avisan.
    assert all(p["codigo"] != "19.1.5.3" for f in r["filas"] for p in f["parecidos"])
    assert {e["codigo"] for e in r["revisar_estan"]} == {"6", "7"}
    hojas = ca.libro(r, "INFORMATICA")
    assert [h[0] for h in hojas] == ["PARA PEDIR EL ALTA", "REVISAR (POSIBLES ERRORES)", "SE PUEDEN PEDIR COMO UNO",
                                    "YA ESTÁN - REVISAR CÓDIGO", "CÓMO SE HIZO"]
    assert all(len(f) == len(ca.ENCABEZADOS) for f in hojas[0][2])


def test_pantalla_del_control_y_excel(admin_client, app, tmp_path, monkeypatch):
    from app.extensions import db
    from app.models.revision_servicio import LlaveServicio

    with app.app_context():
        llave = LlaveServicio(servicio="INFORMATICA", token_hash="x" * 64, enviado_en=datetime(2026, 11, 23, 10, 0),
                              enviado_por="Ana Paz")
        db.session.add(llave)
        db.session.commit()
        llave_id = llave.id
    monkeypatch.setattr(cd, "carpeta_catalogo", lambda instancia: str(tmp_path / "catalogo"))
    r = admin_client.get(f"/admin/servicios/{llave_id}/control-altas")
    assert r.status_code == 302   # sin copia del catálogo: vuelve al panel con un aviso
    guardar(str(tmp_path / "catalogo"), "catalogo_20261123-060000.csv", VIEJO, time.time())
    grupos = {"cargar": [fila("2", "Mouse óptico USB")], "estan": [], "fuera": [], "falta": []}
    monkeypatch.setattr(ls, "planilla_final", lambda llave, tema=None: grupos)
    monkeypatch.setattr(ls, "items_de", lambda llave, tema=None: ([], []))
    r = admin_client.get(f"/admin/servicios/{llave_id}/control-altas")
    assert r.status_code == 200 and "Puede que ya exista" in r.get_data(as_text=True)
    r = admin_client.get(f"/admin/servicios/{llave_id}/control-altas?xlsx=1")
    assert r.status_code == 200 and r.data[:2] == b"PK"


def test_control_solo_para_admin(client):
    assert client.get("/admin/servicios/1/control-altas").status_code in (302, 401, 403)


def test_agrupa_parecidos_en_un_generico():
    catalogo = {"19.1.36.74": ["19 - INF", "19.1 - EQ", "19.1.36", "TINTA PARA IMPRESORA DE PC", "2.9.6.0 Rep.", "19.1.36.74",
                               "CARTUCHO EPSON NEGRO", ""]}
    filas = [{"nombre": n, "codigo": str(i)} for i, n in enumerate(
        ["CARTUCHO EPSON 133 NEGRO", "CARTUCHO EPSON 135 NEGRO", "Cartucho Epson C65 negro", "Mouse USB"])]
    grupos = ca.agrupar(filas, ca.Buscador(catalogo), catalogo)
    assert len(grupos) == 1 and len(grupos[0]["miembros"]) == 3
    assert grupos[0]["nombre"] == "CARTUCHO EPSON NEGRO"
    assert grupos[0]["existentes"][0]["codigo"] == "19.1.36.74"


def test_aprobar_guarda_la_planilla_y_lo_registra(admin_client, app, tmp_path, monkeypatch):
    from app.extensions import db
    from app.models.revision_servicio import LlaveServicio

    with app.app_context():
        llave = LlaveServicio(servicio="INFORMATICA", token_hash="y" * 64, enviado_en=datetime(2026, 11, 23, 10, 0),
                              enviado_por="Ana Paz")
        db.session.add(llave)
        db.session.commit()
        llave_id = llave.id
    monkeypatch.setattr(cd, "carpeta_catalogo", lambda instancia: str(tmp_path / "catalogo"))
    guardar(str(tmp_path / "catalogo"), "catalogo_20261123-060000.csv", VIEJO, time.time())
    grupos = {"cargar": [fila("2", "Mouse óptico USB"), fila("9", "Impresora térmica de etiquetas")],
              "estan": [], "fuera": [], "falta": []}
    monkeypatch.setattr(ls, "planilla_final", lambda llave, tema=None: grupos)
    monkeypatch.setattr(ls, "items_de", lambda llave, tema=None: ([], []))
    monkeypatch.setattr(app, "instance_path", str(tmp_path))
    url = f"/admin/servicios/{llave_id}/aprobar-altas"
    assert admin_client.post(url, data={"nombre": ""}).status_code == 302          # sin nombre no aprueba
    assert not (tmp_path / "altas").exists()
    r = admin_client.post(url, data={"nombre": "Berenice Solohaga"})
    assert r.status_code == 200 and r.data[:2] == b"PK"
    guardadas = os.listdir(tmp_path / "altas")
    assert len(guardadas) == 1
    admin_client.post(url, data={"nombre": "Berenice Solohaga"})
    assert len(os.listdir(tmp_path / "altas")) == 2                                 # nunca pisa
    assert admin_client.get(f"/admin/servicios/altas/{guardadas[0]}").status_code == 200
    assert admin_client.get("/admin/servicios/altas/..%2Finstance.xlsx").status_code == 404
    with app.app_context():
        ll = db.session.get(LlaveServicio, llave_id)
        assert sum(1 for g in ll.registro if g.accion == "revisión final aprobada") == 2


def test_libro_de_carga_va_en_el_orden_del_formulario():
    resultado = {"catalogo": "c.csv", "filas": [
        {"estado": "limpio", "nombre": "Impresora térmica", "codigo": "9", "parecidos": [], "repetido_con": [],
         "sugerencia": {"rubro": "19 - INFORMATICA", "subrubro": "19.1 - EQUIPOS", "elemento": "19.1.106 IMPRESORA",
                        "objeto": "4.3.6.0 Equipo", "desde": "19.1.106.1"}},
        {"estado": "puede_existir", "nombre": "Mouse", "codigo": "2", "parecidos": [{"texto": "19.1.5.2 — MOUSE"}],
         "repetido_con": [], "sugerencia": None}]}
    hojas = ca.libro_carga(resultado, "INFORMATICA", "Ana Paz", "23/11/2026")
    assert [h[0] for h in hojas] == ["PASO A PASO", "GRILLA PARA CARGAR", "NO SE CARGAN", "APROBACIÓN"]
    grilla = hojas[1][2]
    assert len(grilla) == 1 and grilla[0][1:5] == ["19", "19.1", "19.1.106 IMPRESORA", "Impresora térmica — Cód. externo: 9"]
    assert grilla[0][5:9] == ["4", "3", "6", "0"]
    assert hojas[2][2][0][0] == "Mouse"


def test_inconsistencias_detecta_contradicciones_y_huerfanos():
    from datetime import datetime as dt
    def item(id_, n, cp="", ob=None, s=2):
        return {"id": id_, "n": n, "cp": cp, "dn": "X — PROCESADOR", "ob": ob, "s": s}
    def resp(res, dec=None, fecha=dt(2026, 11, 23)):
        return SimpleNamespace(resultado=res, decision=dec, actualizado_en=fecha, codigo_correcto="", codigo_propuesto="1.1")
    items = [item("1", "PC MINI INTEL I3", cp="19.1.3.2"), item("2", "PC MINI INTEL I3", cp="19.1.3.2"),
             item("3", "Agar sangre", ob=["INFORMATICA"])]
    respuestas = {"1": resp("no_necesario"), "2": resp("correcto"), "3": resp("otro_servicio")}
    llave = SimpleNamespace(nombres_bodegas=["INFORMATICA"])
    avisos = {a["tipo"]: a for a in ca.inconsistencias(llave, items, respuestas, {"cargar": []}, None)}
    assert "contradiccion" in avisos and "pantalla_anterior" in avisos and "huerfano" in avisos
