"""Diagnóstico de pérdida de datos (solo en local — nunca aparece en el
servidor real, ver `_solo_local`). Pensado para mirar una COPIA bajada de la
base de producción antes de arriesgar nada en el servidor: muestra el
historial de `ActualizacionCatalogo.respuestas` (el control de pérdida de la
actualización diaria) y un desglose por servicio y por revisor para encontrar
dónde bajó la cantidad. Solo LEE: no cambia nada.
"""
from flask import abort, current_app, render_template

from app.admin.auth import requiere_admin
from app.admin.routes import admin_bp
from app.extensions import db
from app.models.revision_nomenclador import ObservacionNomenclador, RevisorNomenclador, hora_ar
from app.models.revision_servicio import (
    ActualizacionCatalogo, LlaveServicio, NecesidadServicio, RevisionArticuloServicio,
)


def _solo_local():
    """La app solo corre con debug=True en desarrollo local (`python run.py`,
    ver run.py): en el servidor gunicorn la levanta sin debug, así que esta
    pantalla queda cerrada ahí incluso si alguien pisa el deploy por error."""
    if not current_app.debug:
        abort(404)


@admin_bp.route("/diagnostico")
@requiere_admin
def diagnostico():
    _solo_local()

    corridas = list(reversed(ActualizacionCatalogo.query.order_by(ActualizacionCatalogo.en.desc()).limit(30).all()))
    historial = []
    anterior = None
    for c in corridas:
        historial.append({"c": c, "delta": None if anterior is None else c.respuestas - anterior})
        anterior = c.respuestas
    historial.reverse()

    total_revisiones = RevisionArticuloServicio.query.count()
    total_necesidades = NecesidadServicio.query.count()
    total_observaciones = ObservacionNomenclador.query.count()

    por_servicio = (
        db.session.query(LlaveServicio.servicio, db.func.count(RevisionArticuloServicio.id.distinct()),
                         db.func.count(NecesidadServicio.id.distinct()))
        .outerjoin(RevisionArticuloServicio, RevisionArticuloServicio.llave_id == LlaveServicio.id)
        .outerjoin(NecesidadServicio, NecesidadServicio.llave_id == LlaveServicio.id)
        .group_by(LlaveServicio.id).order_by(LlaveServicio.servicio).all()
    )
    por_revisor = (
        db.session.query(RevisorNomenclador.nombre, db.func.count(ObservacionNomenclador.id))
        .outerjoin(ObservacionNomenclador, ObservacionNomenclador.revisor_id == RevisorNomenclador.id)
        .group_by(RevisorNomenclador.id).order_by(RevisorNomenclador.nombre).all()
    )

    return render_template(
        "admin/diagnostico.html", historial=historial, hora_ar=hora_ar,
        total_revisiones=total_revisiones, total_necesidades=total_necesidades,
        total_observaciones=total_observaciones, total_respuestas=total_revisiones + total_necesidades + total_observaciones,
        por_servicio=por_servicio, por_revisor=por_revisor,
    )
