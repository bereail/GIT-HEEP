"""Página de Búsquedas del panel y estadísticas sin contaminar por pruebas."""
from datetime import datetime, timedelta, timezone

from app.extensions import db
from app.models import EventoUso, Tema
from app.services import estadisticas


def _evento(tipo, consulta, resultado, dias_atras=0, tema=None):
    db.session.add(EventoUso(tipo=tipo, consulta=consulta, hubo_resultado=resultado, tema_id=tema,
                             creado_en=(datetime.now(timezone.utc) - timedelta(days=dias_atras)).replace(tzinfo=None)))


def test_pagina_busquedas_filtros_y_exportar(app, admin_client):
    with app.app_context():
        tema = Tema.query.first().id
        _evento("busqueda_global", "guantes", True)
        _evento("busqueda", "jeringa", False, tema=tema)
        _evento("chatbot", "como firmo", True, tema=tema)
        _evento("chatbot", "👎 no entiendo", False, tema=tema)
        _evento("busqueda_global", "vieja", True, dias_atras=40)
        db.session.commit()
    html = admin_client.get("/admin/busquedas").get_data(as_text=True)
    for texto in ("guantes", "jeringa", "como firmo", "Buscador general", "Buscador de Demo", "Asistente de Demo", "No me sirvió"):
        assert texto in html, texto
    assert "vieja" not in html  # fuera de los últimos 30 días
    assert "vieja" in admin_client.get("/admin/busquedas?periodo=todo").get_data(as_text=True)
    html = admin_client.get("/admin/busquedas?sin=1").get_data(as_text=True)
    assert "jeringa" in html and "guantes" not in html
    html = admin_client.get("/admin/busquedas?tipo=asistente").get_data(as_text=True)
    assert "como firmo" in html and "jeringa" not in html
    r = admin_client.get("/admin/busquedas/exportar?periodo=todo")
    texto = r.get_data(as_text=True)
    assert "attachment" in r.headers["Content-Disposition"] and texto.startswith("﻿")
    assert "guantes" in texto and "vieja" in texto and ";No" in texto
    assert app.test_client().get("/admin/busquedas").status_code == 302  # sin login


def test_las_pruebas_no_registran_estadisticas(app):
    client = app.test_client()
    app.config["REGISTRAR_ESTADISTICAS"] = False
    try:
        client.get("/buscar.json?q=guantes")
        with app.app_context():
            assert EventoUso.query.count() == 0
    finally:
        app.config["REGISTRAR_ESTADISTICAS"] = True
    client.get("/buscar.json?q=guantes")
    with app.app_context():
        assert EventoUso.query.count() == 1


def test_robots_y_controles_automaticos_no_cuentan(app):
    from app.models import EventoUso as E
    app.config["REGISTRAR_ESTADISTICAS"] = True
    try:
        cliente = app.test_client()
        with app.app_context():
            antes = E.query.count()
        for ua in ("Mozilla/5.0 (compatible; GPTBot/1.2)", "curl/8.4.0", "Mozilla/5.0 HeadlessChrome/120.0", ""):
            cliente.get("/buscar.json?q=guantes", headers={"User-Agent": ua})
        with app.app_context():
            assert E.query.count() == antes
        cliente.get("/buscar.json?q=guantes", headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0) Chrome/157.0 Safari/537.36"})
        with app.app_context():
            assert E.query.count() == antes + 1
    finally:
        app.config["REGISTRAR_ESTADISTICAS"] = True
    assert estadisticas.es_automatico("Mozilla/5.0 (compatible; ClaudeBot/1.0)")
