"""Registro y agregación de uso del portal (vistas, búsquedas, feedback).

100% anónimo: no se guarda IP ni ningún dato de quien navega, solo qué se
miró, qué se buscó y si encontró algo. Pensado para alimentar la pantalla
de estadísticas del admin, no para analítica de usuarios.
"""

import re

from flask import current_app, has_request_context, request
from sqlalchemy import func

from app.extensions import db
from app.models.evento_uso import EventoUso

TIPOS_BUSQUEDA = ("busqueda", "busqueda_global", "chatbot")


_AUTOMATICO = re.compile(
    r"bot|spider|crawl|slurp|python|requests|curl|wget|go-http|headlesschrome|gptbot|claude|"
    r"bytespider|facebookexternalhit|preview|monitor|scrapy|httpclient|okhttp|java/|libwww",
    re.IGNORECASE,
)


def es_automatico(user_agent):
    """True si el pedido no lo hizo una persona con un navegador."""
    return not user_agent or bool(_AUTOMATICO.search(user_agent))


def registrar(tipo, tema=None, titulo=None, consulta=None, hubo_resultado=None):
    # Las pruebas (p. ej. scripts/bateria_chatbot.py en cada deploy) apagan el
    # registro: si no, sus preguntas se mezclan con las del personal.
    if not current_app.config.get("REGISTRAR_ESTADISTICAS", True):
        return
    # Tampoco cuentan los robots (buscadores, rastreadores de IA) ni los
    # controles automáticos (curl, Chrome sin pantalla): no son personas.
    if es_automatico(request.headers.get("User-Agent", "") if has_request_context() else ""):
        return
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
    feedback_recursos = base.filter_by(tipo="feedback_recurso")
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
        "todas_las_busquedas": _top_por_consulta(busquedas, 100),
        "todas_las_preguntas_chatbot": _top_por_consulta(chatbot, 100),
        "lecciones_con_feedback_negativo": _top_por_titulo(feedback_negativo, 10),
        "recursos_utiles": _top_por_titulo(feedback_recursos.filter_by(hubo_resultado=True), 10),
        "recursos_con_feedback_negativo": _top_por_titulo(feedback_recursos.filter_by(hubo_resultado=False), 10),
    }


# ------------------------------------------------------- página "Búsquedas" --

PERIODOS = {"hoy": "Hoy", "7": "Últimos 7 días", "30": "Últimos 30 días", "todo": "Todo"}
TIPOS_FILTRO = {"todas": TIPOS_BUSQUEDA, "buscador": ("busqueda", "busqueda_global"), "asistente": ("chatbot",)}


def consulta_busquedas(periodo="30", tipo="todas", solo_sin_resultado=False):
    """Búsquedas y preguntas al asistente según los filtros, las más nuevas primero."""
    from datetime import datetime, timedelta, timezone

    q = EventoUso.query.filter(EventoUso.tipo.in_(TIPOS_FILTRO.get(tipo, TIPOS_BUSQUEDA)),
                               EventoUso.consulta.isnot(None))
    ahora = datetime.now(timezone.utc)
    if periodo == "hoy":
        # "Hoy" en hora de Argentina (UTC-3).
        inicio_local = (ahora - timedelta(hours=3)).replace(hour=0, minute=0, second=0, microsecond=0)
        q = q.filter(EventoUso.creado_en >= (inicio_local + timedelta(hours=3)).replace(tzinfo=None))
    elif periodo in ("7", "30"):
        q = q.filter(EventoUso.creado_en >= (ahora - timedelta(days=int(periodo))).replace(tzinfo=None))
    if solo_sin_resultado:
        q = q.filter(EventoUso.hubo_resultado.is_(False))
    return q


def origen_busqueda(evento):
    """Dónde se hizo: buscador general, buscador de un tema o asistente."""
    tema = evento.tema.nombre if evento.tema else ""
    if evento.tipo == "busqueda_global":
        return "Buscador general"
    if evento.tipo == "busqueda":
        return f"Buscador de {tema}".strip()
    if (evento.consulta or "").startswith("👎 "):
        return f"Asistente de {tema} — marcada \"No me sirvió\"".strip()
    return f"Asistente de {tema}".strip()
