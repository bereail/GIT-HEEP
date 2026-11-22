"""Revisión de artículos por servicio, en línea, con llave de acceso.

Aparte de la revisión de Farmacia (`/revision/`): otra sesión, otras tablas.

Seguridad (igual criterio que el acceso de Farmacia):
- El enlace es /servicio/acceso#<token>: el token va después del "#" y lo
  manda `servicio_acceso.js` por POST, con CSRF. En la base solo está el hash.
- Lo que se ve y lo que se puede responder sale SIEMPRE de las bodegas de la
  llave guardadas en el servidor; un código de otra bodega se rechaza.
- La llave se controla en cada pedido: la baja es inmediata.
- Cada respuesta queda a nombre de la persona que entró (nombre y apellido
  que escribe al entrar) y de la llave.
"""
from flask import Blueprint, Response, abort, current_app, jsonify, make_response, redirect, render_template, request, session, url_for
from flask_wtf.csrf import generate_csrf

from app.extensions import db
from app.models.revision_servicio import DECISIONES, RESULTADOS_SERVICIO, LlaveServicio
from app.seguridad import limitar
from app.services import catalogo_diario
from app.services import llaves_servicio as ls
from app.services import xlsx

servicio_bp = Blueprint("servicio", __name__, url_prefix="/servicio", template_folder="../templates")


def _por_llave():
    """Para los límites de pedidos: cada servicio cuenta aparte (no por IP)."""
    llave_id = session.get("llave_servicio_id")
    return f"llave-{llave_id}" if llave_id else None


@servicio_bp.app_context_processor
def _enlace_duda():
    def url_duda():
        llave_id = session.get("llave_servicio_id")
        llave = db.session.get(LlaveServicio, llave_id) if llave_id else None
        contexto = "Revisión de artículos" + (f" · {llave.servicio}" if llave else "")
        return url_for("ui.consulta_nueva", tema_slug="timbo-compras", contexto=contexto)
    return {"url_duda": url_duda}


def _llave_actual():
    llave_id = session.get("llave_servicio_id")
    if not llave_id:
        return None
    llave = db.session.get(LlaveServicio, llave_id)
    if not llave or not llave.activo:
        session.pop("llave_servicio_id", None)
        session.pop("persona_servicio", None)
        return None
    return llave


def _persona(llave):
    datos = session.get("persona_servicio") or {}
    return datos.get("nombre") if datos.get("llave") == llave.id else None


@servicio_bp.route("/acceso", methods=["GET"])
def acceso():
    return render_template("servicio/acceso.html")


@servicio_bp.route("/acceso", methods=["POST"])
@limitar("servicio-acceso", 60, 900)
def acceso_validar():
    llave = ls.llave_por_token((request.form.get("token") or "").strip())
    if not llave:
        session.pop("llave_servicio_id", None)
        return render_template("servicio/acceso.html", invalido=True), 403
    if session.get("llave_servicio_id") != llave.id:
        session.pop("persona_servicio", None)
    session["llave_servicio_id"] = llave.id
    session.permanent = True
    llave.ultimo_acceso = ls.ahora()
    db.session.commit()
    return redirect(url_for("servicio.revision"))


@servicio_bp.route("/instructivo")
def instructivo():
    """Instructivo de una página para los servicios (no muestra datos)."""
    return render_template("servicio/instructivo.html")


@servicio_bp.route("/tutorial")
def tutorial():
    """Tutorial con un ejemplo: video + pasos con capturas (no muestra datos
    de nadie: las capturas son de una llave de prueba)."""
    import json
    import os
    carpeta = os.path.join(current_app.static_folder, "img", "tutorial_servicio")
    try:
        with open(os.path.join(carpeta, "pasos.json"), encoding="utf-8") as f:
            pasos = json.load(f)
    except OSError:
        pasos = []
    hay_video = os.path.exists(os.path.join(current_app.static_folder, "video", "tutorial_servicio.mp4"))
    return render_template("servicio/tutorial.html", pasos=pasos, hay_video=hay_video)


@servicio_bp.route("/salir")
def salir():
    session.pop("llave_servicio_id", None)
    session.pop("persona_servicio", None)
    return render_template("servicio/acceso.html", salio=True)


@servicio_bp.route("/persona", methods=["POST"])
@limitar("servicio-persona", 120, 600)
def persona():
    llave = _llave_actual()
    if not llave:
        return redirect(url_for("servicio.acceso"))
    nombre = " ".join((request.form.get("nombre") or "").split())[:80]
    apellido = " ".join((request.form.get("apellido") or "").split())[:80]
    if not nombre or not apellido:
        return render_template("servicio/persona.html", llave=llave, error=True, nombre=nombre, apellido=apellido), 400
    session["persona_servicio"] = {"llave": llave.id, "nombre": f"{nombre} {apellido}"}
    return redirect(url_for("servicio.revision"))


@servicio_bp.route("/cambiar-persona")
def cambiar_persona():
    session.pop("persona_servicio", None)
    return redirect(url_for("servicio.revision"))


@servicio_bp.route("/")
def revision():
    llave = _llave_actual()
    if not llave:
        return redirect(url_for("servicio.acceso"))
    quien = _persona(llave)
    if not quien:
        return render_template("servicio/persona.html", llave=llave)
    tema = ls.tema_nomenclador()
    items, filas = ls.items_de(llave, tema)
    codigos = {i["id"] for i in items}
    catalogo = catalogo_diario.catalogo_vigente(current_app.instance_path)
    for i in items:
        aviso = catalogo_diario.aviso_codigo(i.get("cp"), catalogo)
        if aviso:
            i["cc"] = aviso  # el catálogo cambió: revisar de nuevo (la respuesta no se toca)
    actualizado = max((e.creado_en for e in filas if e.creado_en), default=None)
    datos = {
        "formato": "revision-servicio-en-linea/1",
        "bodega": ", ".join(llave.nombres_bodegas),
        "versionDatos": "",
        "nomencladorActualizado": actualizado.strftime("%Y-%m-%d") if actualizado else "",
        "generado": "",
        "secciones": {str(s): sum(1 for i in items if i["s"] == s) for s in (1, 2, 3)},
        "items": items,
        "estado": ls.estado_cliente(llave, codigos),
        "servidor": {
            "csrf": generate_csrf(),
            "urlRespuesta": url_for("servicio.guardar_respuesta"),
            "urlNecesidad": url_for("servicio.guardar_necesidad"),
            "urlNecesidadQuitar": url_for("servicio.quitar_necesidad"),
            "urlFinalizar": url_for("servicio.finalizar"),
            "urlEnviar": url_for("servicio.enviar"),
            "enviado": ls.iso(llave.enviado_en),
            "enviadoPor": llave.enviado_por or "",
            "urlPlanillaFinal": url_for("servicio.planilla_final"),
        },
    }
    act = catalogo_diario.ultima_actualizacion()
    return render_template("servicio/revision.html", llave=llave, persona=quien, datos=datos, total=len(items),
                           catalogo_al=ls.hora_ar(act.en) if act else "")


def _contexto_post():
    """Llave + persona + JSON del pedido, o aborta."""
    llave = _llave_actual()
    if not llave:
        abort(403)
    quien = _persona(llave)
    if not quien:
        abort(403)
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        abort(400)
    if llave.enviado_en:
        abort(make_response(*_enviada(llave)))
    return llave, quien, datos


def _enviada(llave):
    """Respuesta 409: la revisión ya se envió y no se puede cambiar."""
    return jsonify({"ok": False, "enviado": ls.iso(llave.enviado_en),
                    "error": "La revisión ya se envió y no se puede cambiar. Si hace falta, pedí que la reabran."}), 409


@servicio_bp.route("/respuesta", methods=["POST"])
@limitar("servicio-respuesta", 900, 600, por=_por_llave)
def guardar_respuesta():
    llave, quien, datos = _contexto_post()
    codigo = str(datos.get("codigo") or "")
    item = ls.item_de(llave, codigo)
    if not item:
        abort(404)  # no es de las bodegas de esta llave
    resultado = datos.get("resultado") or None
    if resultado not in (None, *RESULTADOS_SERVICIO):
        abort(400)
    observacion = str(datos.get("observacion") or "").strip()
    if len(observacion) > ls.LARGO_OBSERVACION:
        return jsonify({"ok": False, "error": f"Máximo {ls.LARGO_OBSERVACION} caracteres."}), 400
    decision = datos.get("decision") or None
    if decision not in (None, *DECISIONES):
        abort(400)
    codigo_correcto = str(datos.get("codigo_correcto") or "").strip()[:40]
    detalle_timbo = str(datos.get("detalle_timbo") or "").strip()[:300]
    r = ls.guardar_respuesta(llave, item, resultado, observacion, quien, decision, codigo_correcto, detalle_timbo)
    db.session.commit()
    return jsonify({"ok": True, "t": ls.iso(r.actualizado_en) if r else None, "finalizado": ls.iso(llave.finalizado_en)})


@servicio_bp.route("/necesidad", methods=["POST"])
@limitar("servicio-necesidad", 300, 600, por=_por_llave)
def guardar_necesidad():
    llave, quien, datos = _contexto_post()
    campos, error = ls.limpiar_necesidad(datos)
    if error:
        return jsonify({"ok": False, "error": error}), 400
    id_necesidad = datos.get("id")
    if id_necesidad is not None and not str(id_necesidad).isdigit():
        abort(400)
    n = ls.guardar_necesidad(llave, int(id_necesidad) if id_necesidad else None, campos, quien)
    if not n:
        abort(404)
    db.session.commit()
    return jsonify({"ok": True, "id": str(n.id), "necesidades": ls.necesidades_cliente(llave)})


@servicio_bp.route("/necesidad/quitar", methods=["POST"])
@limitar("servicio-necesidad", 300, 600, por=_por_llave)
def quitar_necesidad():
    llave, quien, datos = _contexto_post()
    if not str(datos.get("id") or "").isdigit():
        abort(400)
    if not ls.baja_necesidad(llave, int(datos["id"]), bool(datos.get("quitar")), quien):
        abort(404)
    db.session.commit()
    return jsonify({"ok": True, "necesidades": ls.necesidades_cliente(llave)})


@servicio_bp.route("/planilla-final.xlsx")
def planilla_final():
    """La planilla final del servicio de la sesión: lo que hay que cargar en
    el nomenclador. No recibe parámetros: solo puede ser la propia."""
    llave = _llave_actual()
    if not llave or not _persona(llave):
        abort(403)
    contenido = xlsx.libro(ls.libro_planilla_final(ls.planilla_final(llave)))
    nombre = f"planilla_final_{ls.hora_ar(ls.ahora(), '%Y-%m-%d')}.xlsx"
    return Response(contenido, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f'attachment; filename="{nombre}"', "Cache-Control": "no-store"})


# Nombre y explicación de cada bloque de la copia, en el orden de la planilla.
GRUPOS_COPIA = (
    ("cargar", "Hay que cargar en TIMBÓ", "Se pide que los carguen."),
    ("estan", "Ya están en TIMBÓ", "No hay que hacer nada."),
    ("falta", "No se revisaron", "Sin respuesta o con dudas."),
    ("fuera", "Quedan fuera", "No se usan o no son del servicio: no se van a poder pedir."),
)


@servicio_bp.route("/copia")
def copia():
    """Copia de solo lectura de la revisión (lo enviado, o el borrador si
    todavía no se envió), para imprimir o guardar en PDF. Solo la propia."""
    llave = _llave_actual()
    if not llave or not _persona(llave):
        return redirect(url_for("servicio.acceso"))
    return render_template("servicio/copia.html", llave=llave, grupos=ls.planilla_final(llave),
                           grupos_info=GRUPOS_COPIA, hora_ar=ls.hora_ar)


@servicio_bp.route("/finalizar", methods=["POST"])
@limitar("servicio-finalizar", 60, 600, por=_por_llave)
def finalizar():
    llave, quien, datos = _contexto_post()
    if datos.get("reabrir"):
        if llave.finalizado_en:
            llave.finalizado_en, llave.finalizado_por = None, None
            ls.registrar(llave, "revisión reabierta", quien)
    else:
        observaciones = str(datos.get("observaciones") or "").strip()[:4000]
        llave.finalizado_en, llave.finalizado_por = ls.ahora(), quien
        ls.registrar(llave, "revisión terminada", quien + (f" · observaciones: {observaciones}" if observaciones else ""))
    db.session.commit()
    return jsonify({"ok": True, "finalizado": ls.iso(llave.finalizado_en)})


@servicio_bp.route("/enviar", methods=["POST"])
@limitar("servicio-finalizar", 60, 600, por=_por_llave)
def enviar():
    """Envío definitivo: deja la revisión cerrada (no se borra nada)."""
    llave, quien, datos = _contexto_post()
    if not datos.get("confirmo"):
        abort(400)
    ahora = ls.ahora()
    if not llave.finalizado_en:
        llave.finalizado_en, llave.finalizado_por = ahora, quien
    llave.enviado_en, llave.enviado_por = ahora, quien
    ls.registrar(llave, "revisión enviada", quien)
    db.session.commit()
    return jsonify({"ok": True, "enviado": ls.iso(llave.enviado_en), "enviadoPor": llave.enviado_por,
                    "finalizado": ls.iso(llave.finalizado_en)})
