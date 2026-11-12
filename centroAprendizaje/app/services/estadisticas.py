"""Registro y agregación de uso del portal (vistas, búsquedas, feedback).

100% anónimo: no se guarda IP ni ningún dato de quien navega, solo qué se
miró, qué se buscó y si encontró algo. Pensado para alimentar la pantalla
de estadísticas del admin, no para analítica de usuarios.
"""

from sqlalchemy import func

from app.extensions import db
from app.models.evento_uso import EventoUso

TIPOS_BUSQUEDA = ("busqueda", "busqueda_global", "chatbot")


def registrar(tipo, tema=None, titulo=None, consulta=None, hubo_resultado=None):
    db.session.add(EventoUso(
        tema_id=tema.id if tema else None,
        tipo=tipo,
        titulo=(titulo or "").strip()[:200] or None,
        consulta=(consulta or "").strip()[:200] or None,
        hubo_resultado=hubo_resultado,
    ))
    db.session.commit()


def _top_por_titulo(query, limite):
    filas = (
        query.with_entities(EventoUso.titulo, func.count(EventoUso.id).label("veces"))
        .group_by(EventoUso.titulo)
        .order_by(func.count(EventoUso.id).desc())
        .limit(limite)
        .all()
    )
    return [(titulo, veces) for titulo, veces in filas if titulo]


def _top_por_consulta(query, limite):
    filas = (
        query.with_entities(EventoUso.consulta, func.count(EventoUso.id).label("veces"))
        .group_by(EventoUso.consulta)
        .order_by(func.count(EventoUso.id).desc())
        .limit(limite)
        .all()
    )
    return [(consulta, veces) for consulta, veces in filas if consulta]


def resumen(tema_id=None):
    base = EventoUso.query
    if tema_id:
        base = base.filter_by(tema_id=tema_id)

    vistas_tutorial = base.filter_by(tipo="vista_tutorial")
    vistas_modulo = base.filter_by(tipo="vista_modulo")
    busquedas = base.filter(EventoUso.tipo.in_(("busqueda", "busqueda_global")))
    busquedas_sin_resultado = busquedas.filter_by(hubo_resultado=False)
    chatbot = base.filter_by(tipo="chatbot")
    chatbot_sin_resultado = chatbot.filter_by(hubo_resultado=False)
    feedback = base.filter_by(tipo="feedback_tutorial")
    feedback_negativo = feedback.filter_by(hubo_resultado=False)

    return {
        "total_vistas_tutorial": vistas_tutorial.count(),
        "total_vistas_modulo": vistas_modulo.count(),
        "total_busquedas": busquedas.count(),
        "total_busquedas_sin_resultado": busquedas_sin_resultado.count(),
        "total_chatbot": chatbot.count(),
        "total_chatbot_sin_resultado": chatbot_sin_resultado.count(),
        "total_feedback_positivo": feedback.filter_by(hubo_resultado=True).count(),
        "total_feedback_negativo": feedback_negativo.count(),
        "top_tutoriales": _top_por_titulo(vistas_tutorial, 10),
        "top_modulos": _top_por_titulo(vistas_modulo, 10),
        "busquedas_sin_resultado": _top_por_consulta(busquedas_sin_resultado, 15),
        "chatbot_sin_resultado": _top_por_consulta(chatbot_sin_resultado, 15),
        "lecciones_con_feedback_negativo": _top_por_titulo(feedback_negativo, 10),
    }
