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
    llave = SimpleNamespace(enviado_en=envio, servicio="INFORMATICA")

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
    assert [h[0] for h in hojas] == ["PARA PEDIR EL ALTA", "SE PUEDEN PEDIR COMO UNO", "YA ESTÁN - REVISAR CÓDIGO",
                                    "CÓMO SE HIZO"]
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
