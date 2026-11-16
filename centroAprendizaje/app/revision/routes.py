"""Revisión del nomenclador: acceso individual con enlace privado y
observaciones junto a los ítems en amarillo.

Seguridad:
- El enlace es /revision/acceso#<token>. El token va después del "#", así
  que el navegador no lo manda en la URL (no queda en logs ni en el
  historial del servidor): lo envía revision.js por POST, con CSRF.
- En la base solo se guarda el hash del token. El acceso se revoca desde el
  panel (activo = False) y se controla en cada pedido.
- La sesión de revisión es una clave aparte (`revisor_id`): no da acceso al
  panel, que exige `admin_autenticado`.
- Solo se aceptan observaciones para ítems que hoy están en amarillo, y
  siempre a nombre del revisor de la sesión (nunca del pedido).
"""
import hmac
from datetime import datetime, timezone

from flask import Blueprint, abort, jsonify, redirect, render_template, request, session, url_for

from app.extensions import db
from app.models import EquivalenciaArticulo, Tema
from app.models.revision_nomenclador import (
    ObservacionHistorial, ObservacionNomenclador, RevisorNomenclador, clave_item, hash_token, hora_ar,
)
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


@revision_bp.route("/")
def nomenclador():
    revisor = _revisor_actual()
    if not revisor:
        return redirect(url_for("revision.acceso"))
    propias = {o.clave_item: o for o in ObservacionNomenclador.query.filter_by(revisor_id=revisor.id)}
    items = [{
        "clave": clave, "nombre": e.nombre_interno, "codigo": e.codigo_catalogo or "",
        "buscar": " — ".join(x for x in (e.bien_o_servicio, e.item_especifico) if x), "notas": e.notas or "",
        "observacion": propias[clave].texto if clave in propias else "",
        "actualizado": hora_ar(propias[clave].actualizado_en) if clave in propias else "",
    } for clave, e in items_amarillos()]
    return render_template("revision/nomenclador.html", revisor=revisor, items=items,
                           con_observacion=sum(1 for i in items if i["observacion"]))


@revision_bp.route("/observacion", methods=["POST"])
@limitar("revision-observacion", 120, 600)
def guardar_observacion():
    revisor = _revisor_actual()
    if not revisor:
        abort(403)
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        abort(400)
    clave = str(datos.get("clave") or "")
    texto = str(datos.get("texto") or "").strip()
    if len(texto) > LARGO_MAXIMO:
        return jsonify({"ok": False, "error": f"Máximo {LARGO_MAXIMO} caracteres."}), 400
    item = dict(items_amarillos()).get(clave)
    if not item:
        # Solo los ítems que hoy están en amarillo admiten observaciones.
        abort(404)

    obs = ObservacionNomenclador.query.filter_by(revisor_id=revisor.id, clave_item=clave).first()
    ahora = _ahora()
    if obs and obs.texto == texto:
        return jsonify({"ok": True, "texto": texto, "actualizado": hora_ar(obs.actualizado_en)})
    if obs:
        db.session.add(ObservacionHistorial(observacion_id=obs.id, texto=obs.texto, guardado_en=obs.actualizado_en or ahora))
        if texto:
            obs.texto, obs.actualizado_en, obs.nombre_item = texto, ahora, item.nombre_interno
        else:
            # Borrar el texto deja la observación vacía pero conserva el historial.
            obs.texto, obs.actualizado_en = "", ahora
    elif texto:
        obs = ObservacionNomenclador(revisor_id=revisor.id, clave_item=clave, nombre_item=item.nombre_interno,
                                     texto=texto, creado_en=ahora, actualizado_en=ahora)
        db.session.add(obs)
    else:
        return jsonify({"ok": True, "texto": "", "actualizado": ""})
    db.session.commit()
    return jsonify({"ok": True, "texto": obs.texto, "actualizado": hora_ar(obs.actualizado_en)})
