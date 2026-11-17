"""Revisión del nomenclador: acceso individual con enlace privado para
validar, ítem por ítem, las equivalencias en amarillo (sí / no / dudas, con
una observación opcional).

Seguridad:
- El enlace es /revision/acceso#<token>. El token va después del "#", así
  que el navegador no lo manda en la URL (no queda en logs ni en el
  historial del servidor): lo envía revision.js por POST, con CSRF.
- En la base solo se guarda el hash del token. El acceso se revoca desde el
  panel (activo = False) y se controla en cada pedido.
- La sesión de revisión es una clave aparte (`revisor_id`): no da acceso al
  panel, que exige `admin_autenticado`.
- Solo se aceptan revisiones para ítems que hoy están en amarillo, y
  siempre a nombre del revisor de la sesión (nunca del pedido).
- La descarga "mis revisiones" sale solo de la sesión: no recibe ningún
  identificador, así que no hay forma de pedir lo de otra persona.
- Nada de esto modifica el nomenclador: las respuestas se guardan aparte.
"""
import hmac
import re
from datetime import datetime, timezone

from flask import Blueprint, Response, abort, jsonify, redirect, render_template, request, session, url_for

from app.extensions import db
from app.models import EquivalenciaArticulo, Tema
from app.models.revision_nomenclador import (
    COLOR_EXCEL, VALIDACIONES, ObservacionHistorial, ObservacionNomenclador, RevisorNomenclador, clave_item, codigo_hospital,
    hash_token, hora_ar,
)
from app.services import xlsx
from app.seguridad import limitar

revision_bp = Blueprint("revision", __name__, url_prefix="/revision", template_folder="../templates")

TEMA_NOMENCLADOR = "timbo-compras"
LARGO_MAXIMO = 2000


def _ahora():
    return datetime.now(timezone.utc)


def _revisor_actual():
    """El revisor de la sesión, solo si sigue activo (así la baja es inmediata)."""
    revisor_id = session.get("revisor_id")
    if not revisor_id:
        return None
    revisor = db.session.get(RevisorNomenclador, revisor_id)
    if not revisor or not revisor.activo:
        session.pop("revisor_id", None)
        return None
    return revisor


def items_amarillos():
    """Ítems "dudosa" del nomenclador, uno por clave (el CSV tiene un nombre repetido)."""
    tema = Tema.query.filter_by(slug=TEMA_NOMENCLADOR).first()
    if not tema:
        return []
    por_clave = {}
    for e in (EquivalenciaArticulo.query.filter_by(tema_id=tema.id, confianza="dudosa")
              .order_by(EquivalenciaArticulo.nombre_interno)):
        por_clave.setdefault(clave_item(e.nombre_interno), e)
    return [(clave, e) for clave, e in por_clave.items()]


def bodegas_por_clave():
    """Bodegas (centros de pedido) que piden cada ítem en amarillo. Un mismo
    nombre puede repetirse en varias bodegas (es el mismo artículo del
    catálogo igual), por eso acá sí se juntan todas, no solo la primera."""
    tema = Tema.query.filter_by(slug=TEMA_NOMENCLADOR).first()
    if not tema:
        return {}
    resultado = {}
    for e in EquivalenciaArticulo.query.filter_by(tema_id=tema.id, confianza="dudosa"):
        if e.bodega:
            resultado.setdefault(clave_item(e.nombre_interno), set()).add(e.bodega)
    return resultado


@revision_bp.route("/acceso", methods=["GET"])
def acceso():
    return render_template("revision/acceso.html")


@revision_bp.route("/acceso", methods=["POST"])
@limitar("revision-acceso", 10, 900)
def acceso_validar():
    token = (request.form.get("token") or "").strip()
    revisor = None
    if 20 <= len(token) <= 200:
        candidato = RevisorNomenclador.query.filter_by(token_hash=hash_token(token)).first()
        if candidato and candidato.activo and hmac.compare_digest(candidato.token_hash, hash_token(token)):
            revisor = candidato
    if not revisor:
        session.pop("revisor_id", None)
        return render_template("revision/acceso.html", invalido=True), 403
    session["revisor_id"] = revisor.id
    session.permanent = True
    revisor.ultimo_acceso = _ahora()
    db.session.commit()
    return redirect(url_for("revision.nomenclador"))


@revision_bp.route("/salir")
def salir():
    session.pop("revisor_id", None)
    return render_template("revision/acceso.html", salio=True)


def nota_visible(notas):
    """La nota del ítem sin lo técnico, igual que en el nomenclador público."""
    n = re.sub(r"\[cod\.? interno [^\]]+\]\s*", "", notas or "", flags=re.I)
    n = re.sub(r"^match automatico por palabras clave, revisar antes de usar\.?", "", n, flags=re.I)
    n = re.sub(r"^match automatico por palabras clave,?\s*(pero\s*)?", "", n, flags=re.I)
    n = re.sub(r"^(revision manual|encontrado en segunda busqueda):\s*", "", n, flags=re.I).strip()
    return n[:1].upper() + n[1:]


def descripcion_timbo(e):
    return " — ".join(x for x in (e.bien_o_servicio, e.item_especifico) if x)


@revision_bp.route("/")
def nomenclador():
    revisor = _revisor_actual()
    if not revisor:
        return redirect(url_for("revision.acceso"))
    propias = {o.clave_item: o for o in ObservacionNomenclador.query.filter_by(revisor_id=revisor.id)}
    bodegas_map = bodegas_por_clave()
    items = []
    for clave, e in items_amarillos():
        o = propias.get(clave)
        bodegas = sorted(bodegas_map.get(clave, ()))
        items.append({
            "clave": clave, "nombre": e.nombre_interno,
            "codigo_hospital": e.codigo_interno or codigo_hospital(e.notas),
            "codigo": e.codigo_catalogo or "", "timbo": descripcion_timbo(e), "nota": nota_visible(e.notas),
            "bodegas": bodegas,
            "validacion": o.validacion if o else None, "observacion": o.texto if o else "",
            "actualizado": hora_ar(o.actualizado_en) if o else "",
        })
    todas_las_bodegas = sorted({b for lista in bodegas_map.values() for b in lista})
    return render_template("revision/nomenclador.html", revisor=revisor, items=items,
                           revisados=sum(1 for i in items if i["validacion"]), validaciones=VALIDACIONES,
                           bodegas=todas_las_bodegas)


@revision_bp.route("/observacion", methods=["POST"])
@limitar("revision-observacion", 600, 600)
def guardar_observacion():
    """Guarda la respuesta y/o la observación de un ítem. Lo que no viene en
    el pedido queda como estaba (así se puede mandar solo una de las dos)."""
    revisor = _revisor_actual()
    if not revisor:
        abort(403)
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        abort(400)
    clave = str(datos.get("clave") or "")
    item = dict(items_amarillos()).get(clave)
    if not item:
        # Solo los ítems que hoy están en amarillo admiten revisiones.
        abort(404)

    obs = ObservacionNomenclador.query.filter_by(revisor_id=revisor.id, clave_item=clave).first()
    texto = obs.texto if obs else ""
    validacion = obs.validacion if obs else None
    if "texto" in datos:
        texto = str(datos.get("texto") or "").strip()
        if len(texto) > LARGO_MAXIMO:
            return jsonify({"ok": False, "error": f"Máximo {LARGO_MAXIMO} caracteres."}), 400
    if "validacion" in datos:
        validacion = datos.get("validacion") or None
        if validacion not in (None, *VALIDACIONES):
            abort(400)

    ahora = _ahora()
    if obs and obs.texto == texto and obs.validacion == validacion:
        pass
    elif obs:
        db.session.add(ObservacionHistorial(observacion_id=obs.id, texto=obs.texto, validacion=obs.validacion,
                                            guardado_en=obs.actualizado_en or ahora))
        # Si borra el texto, la revisión queda pero el historial se conserva.
        obs.texto, obs.validacion, obs.actualizado_en, obs.nombre_item = texto, validacion, ahora, item.nombre_interno
        db.session.commit()
    elif texto or validacion:
        obs = ObservacionNomenclador(revisor_id=revisor.id, clave_item=clave, nombre_item=item.nombre_interno,
                                     texto=texto, validacion=validacion, creado_en=ahora, actualizado_en=ahora)
        db.session.add(obs)
        db.session.commit()
    else:
        return jsonify({"ok": True, "texto": "", "validacion": None, "actualizado": ""})
    return jsonify({"ok": True, "texto": obs.texto, "validacion": obs.validacion,
                    "actualizado": hora_ar(obs.actualizado_en)})


@revision_bp.route("/mis-revisiones.xlsx")
def exportar_mias():
    """Excel con lo que revisó la persona de la sesión: solo ítems en
    amarillo y solo sus respuestas, en una hoja por resultado y cada fila
    del color de su respuesta. No recibe parámetros a propósito."""
    revisor = _revisor_actual()
    if not revisor:
        abort(403)
    propias = {o.clave_item: o for o in ObservacionNomenclador.query.filter_by(revisor_id=revisor.id)}
    bodegas_map = bodegas_por_clave()
    hojas = {"si": [], "no": [], "duda": [], None: []}
    for clave, e in items_amarillos():
        o = propias.get(clave)
        if o and (o.validacion or o.texto):
            hojas[o.validacion].append([
                e.codigo_interno or codigo_hospital(e.notas), e.codigo_articulo or "",
                ", ".join(sorted(bodegas_map.get(clave, ()))), e.nombre_interno, e.codigo_catalogo or "",
                descripcion_timbo(e), VALIDACIONES.get(o.validacion, "Sin responder"), o.texto,
                hora_ar(o.actualizado_en),
            ])
    encabezados = ["Código interno", "Código de artículo", "Bodega/centro de pedido", "Descripción hospital",
                   "Código TIMBÓ", "Descripción TIMBÓ", "Validación", "Observación", "Fecha de revisión"]
    anchos = [12, 16, 26, 45, 14, 55, 22, 45, 17]
    nombres = [("si", "COINCIDENCIAS"), ("no", "NO COINCIDEN"), ("duda", "DUDAS")]
    if hojas[None]:  # observaciones de antes, sin respuesta
        nombres.append((None, "SIN RESPUESTA"))
    contenido = xlsx.libro([(nombre, encabezados, hojas[v], anchos, [COLOR_EXCEL[v]] * len(hojas[v]))
                            for v, nombre in nombres])
    nombre = f"mis_revisiones_nomenclador_{hora_ar(_ahora(), '%Y-%m-%d')}.xlsx"
    return Response(contenido, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f'attachment; filename="{nombre}"', "Cache-Control": "no-store"})
