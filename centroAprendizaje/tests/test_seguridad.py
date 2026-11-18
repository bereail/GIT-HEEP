"""Pruebas de seguridad: acceso al panel, sesión, CSRF, XSS, inyección,
IDOR, límites de pedidos, subida de archivos, encabezados y errores.

Cada test prueba el comportamiento real con el cliente de Flask (no solo
mira el código). El detalle de la auditoría está en
timboDocumentacion/AUDITORIA_SEGURIDAD.md.
"""

import io
import os
import re
import shutil

import pytest

from app import create_app
from app.extensions import db
from app.models import Consulta, Tema

XSS = '<script>alert("xss")</script><img src=x onerror=alert(1)>'
SQLI = "' OR 1=1; DROP TABLE consultas; --"


def _nueva_consulta(client, mensaje="Hola"):
    r = client.post("/temas/demo/consultas/nueva", data={"tipo": "consulta", "mensaje": mensaje})
    assert r.status_code == 302
    return r.headers["Location"].split("/consultas/")[1].split("?")[0]


# --------------------------------------------------------------- panel ---

def _rutas_admin(app):
    """Todas las rutas del panel menos el login, con valores de prueba."""
    rutas = []
    for regla in app.url_map.iter_rules():
        if not regla.rule.startswith("/admin") or regla.endpoint in ("admin.login", "static"):
            continue
        url = re.sub(r"<(int:)?(\w+)>", lambda m: "1" if m.group(1) or "id" in m.group(2) else "x", regla.rule)
        for metodo in sorted(regla.methods - {"HEAD", "OPTIONS"}):
            rutas.append((metodo, url, regla.endpoint))
    return rutas


def test_todas_las_rutas_del_panel_piden_sesion(app, client):
    rutas = _rutas_admin(app)
    assert len(rutas) > 30  # que el recorrido no quede vacío por error
    for metodo, url, endpoint in rutas:
        r = client.open(url, method=metodo)
        assert r.status_code == 302 and r.headers["Location"].endswith("/admin/login"), (metodo, url, endpoint, r.status_code)


def test_contrasena_incorrecta_no_abre_sesion(client):
    r = client.post("/admin/login", data={"contrasena": "otra"})
    assert r.status_code == 200 and "incorrecta" in r.get_data(as_text=True)
    assert client.get("/admin/").status_code == 302


def test_fuerza_bruta_bloquea_el_login_aunque_despues_acierte(client):
    for _ in range(5):
        client.post("/admin/login", data={"contrasena": "mal"})
    r = client.post("/admin/login", data={"contrasena": "test-admin-pass"})
    assert r.status_code == 429
    assert client.get("/admin/").status_code == 302


def test_login_correcto_renueva_la_sesion_y_logout_la_borra(client):
    with client.session_transaction() as s:
        s["dato_previo"] = "fijado-por-un-atacante"
    client.post("/admin/login", data={"contrasena": "test-admin-pass"})
    with client.session_transaction() as s:
        assert s.get("admin_autenticado") is True
        assert "dato_previo" not in s  # no hay fijación de sesión
    assert client.get("/admin/logout").status_code == 405  # salir solo por POST (con CSRF)
    client.post("/admin/logout")
    assert client.get("/admin/").status_code == 302


def test_sin_variable_de_entorno_no_hay_contrasena_por_defecto(monkeypatch, tmp_path):
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)
    app = create_app(test_config={
        "TESTING": True, "WTF_CSRF_ENABLED": False, "SESSION_COOKIE_SECURE": False,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'x.sqlite3'}",
    })
    assert app.config["ADMIN_PASSWORD"] is None
    assert app.config["SECRET_KEY"] != "clave-de-desarrollo-cambiar-en-produccion"
    c = app.test_client()
    for intento in ("admin123", "", "None"):
        c.post("/admin/login", data={"contrasena": intento})
        assert c.get("/admin/").status_code == 302
    with app.app_context():
        db.engine.dispose()


def test_cookies_de_sesion_seguras_por_defecto(monkeypatch, tmp_path):
    monkeypatch.delenv("COOKIE_SEGURA", raising=False)
    app = create_app(test_config={"SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'x.sqlite3'}"})
    assert app.config["SESSION_COOKIE_SECURE"] is True
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"
    with app.app_context():
        db.engine.dispose()


# ---------------------------------------------------------------- CSRF ---

@pytest.fixture()
def app_con_csrf(tmp_path):
    app = create_app(test_config={
        "TESTING": True, "ADMIN_PASSWORD": "test-admin-pass", "SESSION_COOKIE_SECURE": False,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'csrf.sqlite3'}",
    })
    with app.app_context():
        db.create_all()
        db.session.add(Tema(slug="demo", nombre="Demo", orden=0))
        db.session.commit()
    yield app
    with app.app_context():
        db.engine.dispose()


def test_formularios_sin_token_csrf_se_rechazan(app_con_csrf):
    c = app_con_csrf.test_client()
    assert c.post("/admin/login", data={"contrasena": "test-admin-pass"}).status_code == 400
    assert c.post("/temas/demo/consultas/nueva", data={"tipo": "consulta", "mensaje": "x"}).status_code == 400
    assert c.post("/temas/demo/feedback", data={"puntuacion": "5"}).status_code == 400


def test_login_con_token_csrf_funciona(app_con_csrf):
    c = app_con_csrf.test_client()
    html = c.get("/admin/login").get_data(as_text=True)
    token = re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)
    r = c.post("/admin/login", data={"contrasena": "test-admin-pass", "csrf_token": token})
    assert r.status_code == 302 and r.headers["Location"].endswith("/admin/")


# ----------------------------------------------------------------- XSS ---

def test_consulta_con_codigo_se_muestra_escapada(client, admin_client):
    token = _nueva_consulta(client, XSS)
    for url in (f"/consultas/{token}", f"/admin/consultas/{token}"):
        html = (admin_client if url.startswith("/admin") else client).get(url).get_data(as_text=True)
        assert "<script>alert" not in html and "onerror=alert" not in html.replace("onerror=alert(1)&gt;", "")
        assert "&lt;script&gt;" in html


def test_chatbot_no_devuelve_html_de_la_pregunta(client):
    for pregunta in (XSS, "como hago " + XSS):
        datos = client.post("/temas/demo/chatbot", json={"mensaje": pregunta}).get_json()
        crudo = repr(datos)
        assert "<script>" not in crudo and "<img src=x" not in crudo


def test_busqueda_y_feedback_no_reflejan_html(client, admin_client):
    r = client.get("/temas/demo/buscar.json", query_string={"q": XSS})
    assert r.status_code == 200 and "<script>" not in r.get_data(as_text=True)
    client.post("/temas/demo/feedback", data={"categoria": "sugerencia", "comentario": XSS})
    html = admin_client.get("/admin/feedback").get_data(as_text=True)
    assert "<script>alert" not in html


def test_contexto_en_la_url_no_inyecta_html(client):
    html = client.get("/temas/demo/consultas/nueva", query_string={"contexto": XSS}).get_data(as_text=True)
    assert "<script>alert" not in html


# ------------------------------------------------- inyección e IDOR ------

def test_inyeccion_sql_no_rompe_ni_filtra(client, app):
    assert client.post("/temas/demo/chatbot", json={"mensaje": SQLI}).status_code == 200
    assert client.get("/temas/demo/buscar.json", query_string={"q": SQLI}).status_code == 200
    assert client.get("/consultas/' OR '1'='1").status_code == 404
    r = client.post("/mis-consultas.json", json={"tokens": ["' OR 1=1 --", "%"]})
    assert r.get_json() == []
    with app.app_context():
        assert db.session.query(Consulta).count() == 0  # la tabla sigue ahí


def test_consulta_ajena_no_se_ve_sin_su_token(client):
    token = _nueva_consulta(client)
    assert len(token) >= 16  # 96 bits al azar: no se adivina
    assert client.get(f"/consultas/{token[:-1]}x").status_code == 404
    assert client.post(f"/consultas/{token[:-1]}x/responder", data={"mensaje": "hola"}).status_code == 404
    assert client.post("/mis-consultas.json", json={"tokens": ["otro"]}).get_json() == []


def test_entradas_raras_no_dan_error_500(client):
    for cuerpo in (None, "texto", {"mensaje": None}, {"mensaje": 123}, {"mensaje": "x" * 50000}, {"tokens": "no-lista"}):
        r = client.post("/temas/demo/chatbot", json=cuerpo) if cuerpo is not None else client.post("/temas/demo/chatbot")
        assert r.status_code < 500, cuerpo
        r = client.post("/mis-consultas.json", json=cuerpo if isinstance(cuerpo, dict) else None)
        assert r.status_code < 500, cuerpo
    assert client.get("/temas/no-existe/").status_code == 404


# ---------------------------------------------------- límites de pedidos --

def test_spam_de_consultas_se_frena(client):
    for _ in range(5):
        _nueva_consulta(client)
    r = client.post("/temas/demo/consultas/nueva", data={"tipo": "consulta", "mensaje": "otra"})
    assert r.status_code == 429


def test_spam_al_chatbot_se_frena(client):
    codigos = [client.post("/temas/demo/chatbot", json={"mensaje": "hola"}).status_code for _ in range(61)]
    assert codigos[:60] == [200] * 60 and codigos[60] == 429


# --------------------------------------------------------- subida de archivos

@pytest.fixture()
def carpeta_demo(app):
    carpeta = os.path.join(app.static_folder, "img", "demo")
    yield carpeta
    shutil.rmtree(carpeta, ignore_errors=True)


def test_solo_se_suben_imagenes_reales(admin_client, carpeta_demo):
    falsos = {
        "pagina.png": b"<html><script>alert(1)</script></html>",
        "script.js": b"alert(1)",
        "dibujo.svg": b"<svg onload=alert(1)></svg>",
        "foto.jpg.html": b"\xff\xd8\xff\xe0 <script>",
    }
    for nombre, contenido in falsos.items():
        admin_client.post("/admin/temas/demo/imagenes", data={"archivo": (io.BytesIO(contenido), nombre)},
                          content_type="multipart/form-data")
    assert not os.listdir(carpeta_demo)
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 30
    admin_client.post("/admin/temas/demo/imagenes", data={"archivo": (io.BytesIO(png), "../../evil.png")},
                      content_type="multipart/form-data")
    assert os.listdir(carpeta_demo) == ["evil.png"]  # el "../../" se descarta


def test_borrar_imagen_no_sale_de_la_carpeta(admin_client, app, carpeta_demo):
    os.makedirs(carpeta_demo, exist_ok=True)
    afuera = os.path.join(app.static_folder, "img", "no-borrar.txt")
    with open(afuera, "w") as f:
        f.write("x")
    try:
        admin_client.post("/admin/temas/demo/imagenes/..%2Fno-borrar.txt/eliminar")
        admin_client.post("/admin/temas/demo/imagenes/../no-borrar.txt/eliminar")
        assert os.path.exists(afuera)
    finally:
        os.remove(afuera)


def test_archivo_demasiado_grande_se_rechaza(admin_client, carpeta_demo):
    grande = b"\x89PNG\r\n\x1a\n" + b"\x00" * (9 * 1024 * 1024)
    r = admin_client.post("/admin/temas/demo/imagenes", data={"archivo": (io.BytesIO(grande), "g.png")},
                          content_type="multipart/form-data")
    assert r.status_code == 413


# --------------------------------------------------- encabezados y errores

def test_encabezados_de_seguridad(client, admin_client):
    r = client.get("/")
    h = r.headers
    assert h["X-Content-Type-Options"] == "nosniff"
    assert h["X-Frame-Options"] == "DENY"
    assert "frame-ancestors 'none'" in h["Content-Security-Policy"]
    assert "unsafe-inline" not in h["Content-Security-Policy"].split("script-src")[1].split(";")[0]
    assert h["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert admin_client.get("/admin/").headers["Cache-Control"] == "no-store"


def test_cada_script_en_linea_lleva_el_nonce_de_la_respuesta(client):
    for url in ("/temas/demo/tareas", "/temas/demo/problemas", "/temas/demo/categorias/modulo-1/tutoriales/leccion-1",
                "/mis-consultas", "/temas/demo/feedback"):
        r = client.get(url)
        nonce = re.search(r"'nonce-([^']+)'", r.headers["Content-Security-Policy"]).group(1)
        html = r.get_data(as_text=True)
        for etiqueta in re.findall(r"<script[^>]*>", html):
            assert "src=" in etiqueta or f'nonce="{nonce}"' in etiqueta, (url, etiqueta)
        assert not re.search(r"\son[a-z]+=\"", html), url  # sin manejadores en línea


def test_error_interno_no_muestra_detalles(tmp_path):
    app = create_app(test_config={"SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'e.sqlite3'}"})

    @app.route("/_explotar")
    def _explotar():
        raise RuntimeError("detalle-secreto-del-servidor")

    r = app.test_client().get("/_explotar")
    assert r.status_code == 500
    html = r.get_data(as_text=True)
    assert "detalle-secreto" not in html and "Traceback" not in html
    with app.app_context():
        db.engine.dispose()
