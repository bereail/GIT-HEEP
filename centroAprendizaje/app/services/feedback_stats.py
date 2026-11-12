"""Agregación para el panel de Feedback del admin (promedio, distribución
de estrellas, listado filtrable)."""

from sqlalchemy import func

from app.models.feedback import Feedback


def resumen(tema_id=None, tutorial_id=None, categoria=None, desde=None, hasta=None):
    query = Feedback.query
    if tema_id:
        query = query.filter_by(tema_id=tema_id)
    if tutorial_id:
        query = query.filter_by(tutorial_id=tutorial_id)
    if categoria:
        query = query.filter_by(categoria=categoria)
    if desde:
        query = query.filter(Feedback.creado_en >= desde)
    if hasta:
        query = query.filter(Feedback.creado_en <= hasta)

    con_puntuacion = query.filter(Feedback.puntuacion.isnot(None))
    promedio = con_puntuacion.with_entities(func.avg(Feedback.puntuacion)).scalar()

    distribucion = {n: 0 for n in range(1, 6)}
    for puntuacion, cantidad in (
        con_puntuacion.with_entities(Feedback.puntuacion, func.count(Feedback.id))
        .group_by(Feedback.puntuacion)
        .all()
    ):
        distribucion[puntuacion] = cantidad

    return {
        "promedio": round(promedio, 1) if promedio else None,
        "total_valoraciones": con_puntuacion.count(),
        "total_comentarios": query.filter(Feedback.comentario.isnot(None)).count(),
        "distribucion": distribucion,
        "items": query.order_by(Feedback.creado_en.desc()).all(),
    }
