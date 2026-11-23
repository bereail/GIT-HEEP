"""Panel: llaves de la revisión por servicio (aparte de la revisión de Farmacia).

Se registra sobre `admin_bp` (ver el final de `admin/routes.py`).
"""
import re

from flask import Response, abort, flash, redirect, render_template, request, session, url_for

from app.admin.auth import requiere_admin
from app.admin.routes import admin_bp
from app.extensions import db
from app.models.revision_servicio import (
    CATALOGO_NECESIDAD, RESULTADOS_SERVICIO, TIPOS_NECESIDAD, LlaveServicio,
)
from app.services import llaves_servicio as ls
from app.services import xlsx


def _llave_o_404(llave_id):
    return db.session.get(LlaveServicio, llave_id) or abort(404)


def _mostrar_enlace(llave, token):
    session["enlace_servicio_nuevo"] = {
        "servicio": llave.servicio, "url": url_for("servicio.acceso", _external=True) + "#" + token}


@admin_bp.route("/servicios")
@requiere_admin
def servicios():
    tema = ls.tema_nomenclador()
    llaves = LlaveServicio.query.order_by(LlaveServicio.servicio).all()
    nombres = {ll.id: ll.servicio for ll in llaves}
    llaves_por_bodega = {}
    for ll in llaves:
        if ll.activo:
            for b in ll.nombres_bodegas:
                llaves_por_bodega.setdefault(b, []).append(ll.servicio)
    from app.models.revision_nomenclador import RevisorNomenclador

    import json

    from app.models.revision_servicio import ActualizacionCatalogo

    revisores_farmacia = RevisorNomenclador.query.order_by(RevisorNomenclador.nombre).all()
    corridas = ActualizacionCatalogo.query.order_by(ActualizacionCatalogo.en.desc()).limit(10).all()
    ultima_ok = next((c for c in corridas if c.estado != "error"), None)
    detalle_catalogo = json.loads(ultima_ok.detalle) if ultima_ok else {}
    # La corrida anterior con resumen, para mostrar cuánto cambió de un día al otro.
    anterior = next((c for c in corridas if ultima_ok and c.en < ultima_ok.en and c.estado != "error"
                     and "resumen_servicios" in (c.detalle or "")), None)
    resumen_anterior = json.loads(anterior.detalle).get("resumen_servicios", {}) if anterior else {}
    from datetime import datetime, timedelta, timezone
    from flask import current_app

    from app.services import catalogo_diario
    catalogo_en_curso = catalogo_diario.en_curso(current_app.instance_path)
    atrasado = bool(corridas) and (datetime.now(timezone.utc) - corridas[0].en.replace(tzinfo=timezone.utc)) > timedelta(hours=26)
    return render_template(
        "servicios.html", revisores_farmacia=revisores_farmacia, corridas=corridas, ultima_ok=ultima_ok,
        detalle_catalogo=detalle_catalogo, resumen_anterior=resumen_anterior, atrasado=atrasado, catalogo_en_curso=catalogo_en_curso, llaves=llaves, avances={ll.id: ls.avance(ll, tema) for ll in llaves},
        bodegas=ls.bodegas_asignables(tema), diferencias=ls.diferencias_entre_servicios(), nombres=nombres,
        resultados=RESULTADOS_SERVICIO, llaves_por_bodega=llaves_por_bodega, enlace_nuevo=session.pop("enlace_servicio_nuevo", None), hora_ar=ls.hora_ar,
    )


@admin_bp.route("/servicios", methods=["POST"])
@requiere_admin
def servicio_crear():
    nombre = " ".join((request.form.get("servicio") or "").split())[:120]
    validas = {b for b, _ in ls.bodegas_asignables(ls.tema_nomenclador())}
    elegidas = request.form.getlist("bodegas")
    if not nombre or not any(b in validas for b in elegidas):
        flash("Escribí el nombre del servicio y elegí al menos una bodega.", "error")
        return redirect(url_for("admin.servicios"))
    llave = LlaveServicio(servicio=nombre, token_hash="", activo=True)
    token = ls.nuevo_token(llave)
    db.session.add(llave)
    ls.registrar(llave, "llave creada", nombre)
    ls.asignar_bodegas(llave, elegidas, validas)
    db.session.commit()
    _mostrar_enlace(llave, token)
    flash(f"Llave creada para {nombre}.", "ok")
    return redirect(url_for("admin.servicios"))


@admin_bp.route("/servicios/<int:llave_id>/bodegas", methods=["POST"])
@requiere_admin
def servicio_bodegas(llave_id):
    llave = _llave_o_404(llave_id)
    validas = {b for b, _ in ls.bodegas_asignables(ls.tema_nomenclador())}
    elegidas = request.form.getlist("bodegas")
    if not any(b in validas for b in elegidas):
        flash("La llave tiene que tener al menos una bodega. Para cerrarla, dala de baja.", "error")
        return redirect(url_for("admin.servicios"))
    agregadas, sacadas = ls.asignar_bodegas(llave, elegidas, validas)
    db.session.commit()
    if agregadas or sacadas:
        flash(f"Bodegas de {llave.servicio} actualizadas. Las respuestas de las bodegas quitadas se conservan: "
              "vuelven a verse si se asignan de nuevo.", "ok")
    return redirect(url_for("admin.servicios"))


@admin_bp.route("/servicios/<int:llave_id>/enlace", methods=["POST"])
@requiere_admin
def servicio_enlace(llave_id):
    llave = _llave_o_404(llave_id)
    token = ls.nuevo_token(llave)
    llave.activo = True
    ls.registrar(llave, "enlace nuevo", "el anterior dejó de funcionar")
    db.session.commit()
    _mostrar_enlace(llave, token)
    flash(f"Enlace nuevo para {llave.servicio}: el anterior ya no funciona. Las respuestas no se tocan.", "ok")
    return redirect(url_for("admin.servicios"))


@admin_bp.route("/servicios/<int:llave_id>/estado", methods=["POST"])
@requiere_admin
def servicio_estado(llave_id):
    llave = _llave_o_404(llave_id)
    llave.activo = not llave.activo
    ls.registrar(llave, "llave activada" if llave.activo else "llave dada de baja")
    db.session.commit()
    flash(f"Llave de {llave.servicio} {'activada' if llave.activo else 'dada de baja'}. Las respuestas se conservan.", "ok")
    return redirect(url_for("admin.servicios"))


@admin_bp.route("/servicios/catalogo/actualizar", methods=["POST"])
@requiere_admin
def catalogo_actualizar():
    """Baja el Catálogo WEB y compara ahora (lo mismo que la corrida diaria),
    en segundo plano: tarda alrededor de un minuto."""
    import os
    import subprocess
    import sys

    from flask import current_app

    from app.services import catalogo_diario
    if catalogo_diario.en_curso(current_app.instance_path):
        flash("Ya se está actualizando. Recargá la página en un minuto.", "ok")
        return redirect(url_for("admin.servicios"))
    raiz = os.path.dirname(current_app.root_path)
    os.makedirs(catalogo_diario.carpeta_catalogo(current_app.instance_path), exist_ok=True)
    log = open(os.path.join(catalogo_diario.carpeta_catalogo(current_app.instance_path), "actualizar.log"), "a", encoding="utf-8")
    opciones = {"start_new_session": True} if os.name != "nt" else {}
    catalogo_diario.marca_en_curso(current_app.instance_path)   # desde ya: un segundo clic no lanza otra
    subprocess.Popen([sys.executable, os.path.join(raiz, "scripts", "actualizar_catalogo.py"), "--ya-marcado"], cwd=raiz,
                     stdout=log, stderr=subprocess.STDOUT, **opciones)
    flash("Se está bajando el Catálogo WEB y comparando. Tarda alrededor de un minuto: después recargá la página.", "ok")
    return redirect(url_for("admin.servicios"))


@admin_bp.route("/servicios/catalogo/descargar")
@requiere_admin
def catalogo_descargar():
    """La última copia del Catálogo WEB guardada (CSV separado por «|»)."""
    import os

    from flask import current_app, send_file

    from app.services import catalogo_diario
    ruta = catalogo_diario.ultima_copia(current_app.instance_path) or abort(404)
    return send_file(ruta, mimetype="text/csv", as_attachment=True, download_name=os.path.basename(ruta))


@admin_bp.route("/servicios/<int:llave_id>/control-altas")
@requiere_admin
def servicio_control_altas(llave_id):
    """Control final antes de pedir las altas: vuelve a mirar «Hay que cargar»
    contra la última copia del Catálogo WEB. Solo lee. Con ?xlsx=1, el Excel."""
    from flask import current_app

    from app.services import catalogo_diario, control_altas
    llave = _llave_o_404(llave_id)
    resultado = control_altas.control(llave, current_app.instance_path)
    if resultado is None:
        flash("Todavía no hay ninguna copia del Catálogo WEB: tocá «Actualizar ahora» y probá de nuevo.", "error")
        return redirect(url_for("admin.servicios"))
    if request.args.get("xlsx"):
        nombre = re.sub(r"[^A-Za-z0-9_-]+", "_", llave.servicio) or "servicio"
        return Response(xlsx.libro(control_altas.libro(resultado, llave.servicio)),
                        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        headers={"Content-Disposition": f'attachment; filename="control-altas-{nombre}.xlsx"'})
    act = catalogo_diario.ultima_actualizacion()
    return render_template("admin/control_altas.html", llave=llave, r=resultado, estados=control_altas.ESTADOS, hora_ar=ls.hora_ar,
                           orden=control_altas.ORDEN_ESTADOS, catalogo_al=ls.hora_ar(act.en) if act else "",
                           en_curso=catalogo_diario.en_curso(current_app.instance_path))


@admin_bp.route("/servicios/<int:llave_id>/reabrir", methods=["POST"])
@requiere_admin
def servicio_reabrir(llave_id):
    """Reabre una revisión enviada para que el servicio pueda corregir. Las
    respuestas no se tocan; queda registrado."""
    llave = _llave_o_404(llave_id)
    if llave.enviado_en:
        ls.registrar(llave, "revisión reabierta por el administrador",
                     f"había sido enviada el {ls.hora_ar(llave.enviado_en)} por {llave.enviado_por}")
        llave.enviado_en, llave.enviado_por = None, None
        db.session.commit()
        flash(f"La revisión de {llave.servicio} quedó abierta de nuevo. Las respuestas se conservan.", "ok")
    return redirect(url_for("admin.servicios"))


@admin_bp.route("/servicios/<int:llave_id>/importar-farmacia", methods=["POST"])
@requiere_admin
def servicio_importar_farmacia(llave_id):
    from app.models.revision_nomenclador import RevisorNomenclador

    llave = _llave_o_404(llave_id)
    revisor = db.session.get(RevisorNomenclador, request.form.get("revisor", type=int) or 0) or abort(404)
    cuenta = ls.importar_de_farmacia(llave, revisor)
    db.session.commit()
    flash(f"Se trajeron {cuenta['traidas']} respuestas de {revisor.nombre} a {llave.servicio}. "
          f"{cuenta['ya_tenian']} ya tenían respuesta y no se tocaron; {cuenta['fuera_de_sus_bodegas']} eran de "
          "artículos de otras bodegas. La revisión de Farmacia no se modificó.", "ok")
    return redirect(url_for("admin.servicios"))


@admin_bp.route("/servicios/exportar")
@requiere_admin
def servicios_exportar():
    """Excel de una llave (?llave=<id>) o de todas: una hoja por resultado,
    las que faltan revisar, los artículos que faltan en el nomenclador y las
    diferencias entre servicios."""
    tema = ls.tema_nomenclador()
    if request.args.get("llave"):
        llaves = [_llave_o_404(request.args.get("llave", type=int) or 0)]
    else:
        llaves = LlaveServicio.query.order_by(LlaveServicio.servicio).all()

    encabezados = ["Servicio", "Bodegas", "También figura en", "Código interno", "Código de artículo", "Descripción",
                   "Código propuesto", "Descripción TIMBÓ", "Resultado", "Observación", "Respondió", "Fecha",
                   "Versiones anteriores"]
    anchos = [22, 22, 22, 12, 16, 42, 14, 46, 22, 40, 22, 17, 40]
    hojas = {k: [] for k in ("correcto", "no_corresponde", "aclaracion", "no_necesario", "otro_servicio", "pendiente")}
    necesidades = []

    def versiones(r):
        return " | ".join(f"{ls.hora_ar(h.guardado_en)} {h.persona}: [{RESULTADOS_SERVICIO.get(h.resultado, 'sin resultado')}] "
                          f"{h.observacion}".rstrip() for h in r.historial)

    for llave in llaves:
        items, _ = ls.items_de(llave, tema)
        respuestas = {r.codigo_interno: r for r in llave.revisiones}
        for i in items:
            r = respuestas.get(i["id"])
            base = [llave.servicio, ", ".join(i.get("b", [])), ", ".join(i.get("ob", [])), i["id"], i.get("ca", ""),
                    i["n"], i.get("cp", ""), i.get("dn", "")]
            if r and r.resultado:
                texto = RESULTADOS_SERVICIO[r.resultado]
                if r.decision == "agregar":
                    texto += " → hay que agregarlo"
                elif r.decision == "codigo":
                    texto += f" → código correcto {r.codigo_correcto}"
                elif r.decision == "general":
                    texto += f" → ítem general {r.codigo_correcto or r.codigo_propuesto}: {r.detalle_timbo}"
                elif r.resultado == "no_corresponde":
                    texto += " → sin decidir"
                hojas[r.resultado].append(base + [texto, r.observacion, r.persona,
                                                  ls.hora_ar(r.actualizado_en), versiones(r)])
            else:
                hojas["pendiente"].append(base + ["Sin revisar", r.observacion if r else "", r.persona if r else "",
                                                  ls.hora_ar(r.actualizado_en) if r else "", versiones(r) if r else ""])
        for n in llave.necesidades:
            if not n.quitada_en:
                necesidades.append([llave.servicio, n.descripcion, n.presentacion, n.uso, TIPOS_NECESIDAD.get(n.tipo, ""),
                                    CATALOGO_NECESIDAD.get(n.catalogo, ""), n.codigo_catalogo, n.observaciones,
                                    n.persona, ls.hora_ar(n.actualizado_en)])
    colores = {"correcto": "verde", "no_corresponde": "rojo", "aclaracion": "naranja", "no_necesario": "gris", "otro_servicio": "gris", "pendiente": None}
    libro = [(nombre, encabezados, hojas[k], anchos, [colores[k]] * len(hojas[k]))
             for k, nombre in (("correcto", "CORRECTOS"), ("no_corresponde", "NO CORRESPONDEN"),
                               ("aclaracion", "REQUIEREN ACLARACION"), ("no_necesario", "NO SE USAN"),
                               ("otro_servicio", "NO SON DE ESTE SERVICIO"),
                               ("pendiente", "SIN REVISAR"))]
    finales = [ls.planilla_final(llave, tema) for llave in llaves]
    libro.insert(0, ("YA ESTAN EN TIMBO", ls.ENCABEZADOS_FINAL, [f for g in finales for f in g["estan"]],
                     ls.ANCHOS_FINAL, None))
    libro.insert(0, ("PEDIR EL ALTA EN CATALOGO WEB", ls.ENCABEZADOS_FINAL, [f for g in finales for f in g["cargar"]],
                     ls.ANCHOS_FINAL, None))
    libro.append(("FALTAN EN EL NOMENCLADOR",
                  ["Servicio", "Descripción", "Presentación", "Uso", "Tipo", "Catálogo WEB", "Código en el catálogo",
                   "Observaciones", "Cargó", "Fecha"], necesidades, [22, 40, 22, 30, 26, 22, 16, 40, 22, 17], None))
    ids = {ll.id for ll in llaves}
    nombres = {ll.id: ll.servicio for ll in LlaveServicio.query}
    filas_dif = []
    for lista in ls.diferencias_entre_servicios():
        if any(r.llave_id in ids for r in lista):
            for r in lista:
                filas_dif.append([r.codigo_interno, r.nombre_item, r.codigo_propuesto, nombres.get(r.llave_id, ""),
                                  RESULTADOS_SERVICIO[r.resultado], r.observacion, r.persona, ls.hora_ar(r.actualizado_en)])
    libro.append(("DIFERENCIAS ENTRE SERVICIOS",
                  ["Código interno", "Descripción", "Código propuesto", "Servicio", "Resultado", "Observación",
                   "Respondió", "Fecha"], filas_dif, [12, 42, 14, 22, 22, 40, 22, 17], None))
    quien = ""
    if len(llaves) == 1 and request.args.get("llave"):
        quien = "_" + (re.sub(r"[^a-z0-9]+", "-", llaves[0].servicio.lower()).strip("-") or str(llaves[0].id))
    nombre = f"revision_por_servicio{quien}_{ls.hora_ar(ls.ahora(), '%Y-%m-%d')}.xlsx"
    return Response(xlsx.libro(libro), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f'attachment; filename="{nombre}"', "Cache-Control": "no-store"})

