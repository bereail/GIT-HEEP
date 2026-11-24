"""Comparación final subiendo archivos a mano (solo en local, ver
`diagnostico._solo_local`): para cuando se quiere probar todo el circuito
con el Catálogo WEB y la planilla de revisión ya bajados, sin depender de la
base en vivo ni de la descarga automática del catálogo. Solo LEE los
archivos subidos: no toca la base ni el servidor real.

El resultado de «Comparar» se guarda un rato en memoria (no en la base: es
solo para que el botón «Generar la planilla» de más abajo, en el POST
siguiente, no tenga que pedir los archivos de nuevo). Se pierde si se
reinicia `python run.py`, o pasados 30 minutos: no es grave, se vuelve a
subir y comparar.
"""
import secrets
import time
from datetime import datetime

from flask import flash, render_template, request

from app.admin.auth import requiere_admin
from app.admin.diagnostico import _solo_local
from app.admin.routes import admin_bp
from app.services import control_altas

_VENCE_SEGUNDOS = 30 * 60
_guardados = {}  # token: (momento, servicio, resultado)


def _limpiar_viejos():
    limite = time.monotonic() - _VENCE_SEGUNDOS
    for token in [t for t, (momento, _, _) in _guardados.items() if momento < limite]:
        del _guardados[token]


@admin_bp.route("/comparar-manual", methods=["GET", "POST"])
@requiere_admin
def comparar_manual():
    _solo_local()
    _limpiar_viejos()
    resultado, token, servicio = None, None, (request.form.get("servicio") or "").strip()

    if request.method == "POST" and request.form.get("accion") == "comparar":
        servicio = servicio or "servicio"
        archivo_catalogo = request.files.get("catalogo")
        archivo_excel = request.files.get("excel")
        if not archivo_catalogo or not archivo_catalogo.filename:
            flash("Subí el archivo del Catálogo WEB (CSV).", "error")
        elif not archivo_excel or not archivo_excel.filename:
            flash("Subí el Excel de «Revisión final automática» (sin aprobar).", "error")
        else:
            try:
                catalogo = control_altas.leer_catalogo_subido(archivo_catalogo.read())
                filas_entrada = control_altas.filas_desde_excel(archivo_excel.read())
                if not filas_entrada:
                    flash("El Excel no tiene ninguna fila en «PARA PEDIR EL ALTA».", "error")
                else:
                    resultado = control_altas.comparar(filas_entrada, catalogo, archivo_catalogo.filename)
                    token = secrets.token_urlsafe(8)
                    _guardados[token] = (time.monotonic(), servicio, resultado)
            except ValueError as e:
                flash(str(e), "error")
            except Exception:  # noqa: BLE001 — archivo raro: un mensaje claro y nada más
                flash("No pude leer alguno de los dos archivos: ¿son el Catálogo WEB (CSV) y el Excel correctos?", "error")

    elif request.method == "POST" and request.form.get("accion") == "generar":
        token = request.form.get("token") or ""
        guardado = _guardados.get(token)
        if not guardado:
            flash("Esta comparación ya venció o se reinició la app: subí los archivos de nuevo.", "error")
        else:
            _, servicio, resultado = guardado
            nombre = (request.form.get("aprobado_por") or "").strip()
            if len(nombre) < 3:
                flash("Para bajar la planilla de carga, escribí tu nombre y apellido (arriba de todo, en «Generar»).", "error")
            else:
                from flask import Response

                from app.services import xlsx
                extra = {}
                for f in resultado["filas"]:
                    if f["estado"] not in control_altas.ESTADOS_PARA_CARGAR:
                        continue
                    clave = control_altas.clave_fila(f)
                    extra[clave] = {
                        "unidad": (request.form.get(f"unidad__{clave}") or "").strip(),
                        "marca": (request.form.get(f"marca__{clave}") or "").strip(),
                        "aporta": request.form.get(f"aporta__{clave}") or "No",
                        "sdo": (request.form.get(f"sdo__{clave}") or "").strip(),
                        "cargada": bool(request.form.get(f"cargada__{clave}")),
                        "rubro": (request.form.get(f"rubro__{clave}") or "").strip(),
                        "subrubro": (request.form.get(f"subrubro__{clave}") or "").strip(),
                        "elemento": (request.form.get(f"elemento__{clave}") or "").strip(),
                        "inciso": (request.form.get(f"inciso__{clave}") or "").strip(),
                        "principal": (request.form.get(f"principal__{clave}") or "").strip(),
                        "parcial": (request.form.get(f"parcial__{clave}") or "").strip(),
                        "subparcial": (request.form.get(f"subparcial__{clave}") or "").strip(),
                    }
                fecha = datetime.now().strftime("%d/%m/%Y %H:%M") + " — PRUEBA LOCAL, no es una aprobación oficial"
                return Response(
                    xlsx.libro(control_altas.libro_carga(resultado, servicio, nombre, fecha, extra=extra)),
                    mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f'attachment; filename="prueba-carga-{servicio}.xlsx"'})

    return render_template("admin/comparar_manual.html", resultado=resultado, token=token, estados=control_altas.ESTADOS,
                           orden=control_altas.ORDEN_ESTADOS, para_cargar=control_altas.ESTADOS_PARA_CARGAR,
                           servicio=servicio, objeto_del_gasto=control_altas.objeto_del_gasto)
