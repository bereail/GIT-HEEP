"""Endurecimiento de seguridad: secretos, cookies, encabezados HTTP y límites
de pedidos. Se aplica desde `create_app`.

Lo que no se puede hacer desde la app (HSTS en nginx, ocultar la versión de
nginx, límites compartidos entre procesos) está anotado en
`timboDocumentacion/AUDITORIA_SEGURIDAD.md`.
"""

import hmac
import logging
import os
import secrets
import threading
import time
from functools import wraps

from flask import abort, g, request
from werkzeug.middleware.proxy_fix import ProxyFix

log = logging.getLogger(__name__)

# Valores que solo valen en desarrollo local (run.py los define a propósito).
_SECRET_KEY_DESARROLLO = "clave-de-desarrollo-cambiar-en-produccion"


def configurar_secretos(app):
    """SECRET_KEY y ADMIN_PASSWORD salen de variables de entorno.

    Si faltan, la app NO usa valores conocidos: genera una SECRET_KEY al azar
    (las sesiones no sobreviven a un reinicio) y deja el panel sin contraseña
    válida, o sea, nadie puede entrar. Así un servidor mal configurado queda
    cerrado en vez de abierto con "admin123". Los scripts de importación
    también crean la app y no necesitan estos valores.
    """
    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key:
        log.warning("Falta SECRET_KEY: se usa una clave al azar (las sesiones no sobreviven a un reinicio).")
        secret_key = secrets.token_hex(32)
    app.config["SECRET_KEY"] = secret_key

    contrasena = os.environ.get("ADMIN_PASSWORD")
    if not contrasena:
        log.warning("Falta ADMIN_PASSWORD: el panel de administración queda cerrado.")
    elif len(contrasena) < 12:
        log.warning("ADMIN_PASSWORD tiene menos de 12 caracteres: conviene una más larga.")
    app.config["ADMIN_PASSWORD"] = contrasena or None


def contrasena_admin_correcta(app, contrasena):
    esperada = app.config.get("ADMIN_PASSWORD")
    if not esperada or not contrasena:
        return False
    # Comparación en tiempo constante: no deja adivinar la clave midiendo demoras.
    return hmac.compare_digest(contrasena.encode("utf-8"), esperada.encode("utf-8"))


def configurar_cookies(app):
    # En local (http://127.0.0.1) la cookie no puede ser Secure o no se guarda.
    seguro = os.environ.get("COOKIE_SEGURA", "1") != "0"
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=seguro,
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=8 * 60 * 60,  # la sesión del panel dura una jornada
    )


def configurar_proxy(app):
    """Detrás de nginx: confiar en un solo proxy para saber la IP real y si
    el pedido llegó por HTTPS (lo usan el límite de pedidos y HSTS)."""
    if os.environ.get("DETRAS_DE_PROXY", "1") != "0":
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)


def _politica_contenido(nonce):
    return "; ".join([
        "default-src 'self'",
        f"script-src 'self' 'nonce-{nonce}'",
        "style-src 'self' 'unsafe-inline'",  # hay estilos en atributos style=""
        "img-src 'self' data:",
        "font-src 'self'",
        "connect-src 'self'",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    ])


def configurar_encabezados(app):
    @app.before_request
    def _nonce():
        g.csp_nonce = secrets.token_urlsafe(16)

    @app.context_processor
    def _nonce_en_plantillas():
        return {"csp_nonce": getattr(g, "csp_nonce", "")}

    @app.after_request
    def _encabezados(respuesta):
        h = respuesta.headers
        h.setdefault("Content-Security-Policy", _politica_contenido(getattr(g, "csp_nonce", "")))
        h.setdefault("X-Content-Type-Options", "nosniff")
        h.setdefault("X-Frame-Options", "DENY")
        h.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        h.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        h.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        if request.is_secure:
            h.setdefault("Strict-Transport-Security", "max-age=31536000")
        # Las páginas del panel y las de una consulta (con token) no se guardan en caché.
        if request.path.startswith("/admin") or request.path.startswith("/consultas/"):
            h["Cache-Control"] = "no-store"
        return respuesta


class LimitadorEnMemoria:
    """Ventana deslizante por clave (IP + acción). Vive en la memoria de cada
    proceso: con varios workers de gunicorn el límite real se multiplica por
    la cantidad de workers. Sirve contra fuerza bruta y spam básico; el límite
    compartido va en nginx (ver AUDITORIA_SEGURIDAD.md)."""

    def __init__(self):
        self._eventos = {}
        self._candado = threading.Lock()

    def _vigentes(self, clave, ventana, ahora):
        eventos = [t for t in self._eventos.get(clave, []) if ahora - t < ventana]
        self._eventos[clave] = eventos
        return eventos

    def bloqueado(self, clave, maximo, ventana):
        with self._candado:
            return len(self._vigentes(clave, ventana, time.monotonic())) >= maximo

    def registrar(self, clave, ventana):
        with self._candado:
            ahora = time.monotonic()
            self._vigentes(clave, ventana, ahora).append(ahora)
            if len(self._eventos) > 10000:  # tope para no crecer sin fin
                self._eventos = {k: v for k, v in self._eventos.items() if v}

    def limpiar(self, clave):
        with self._candado:
            self._eventos.pop(clave, None)

    def reiniciar(self):
        with self._candado:
            self._eventos.clear()


limitador = LimitadorEnMemoria()


def ip_cliente():
    return request.remote_addr or "desconocida"


def limitar(accion, maximo, ventana_segundos, por=None):
    """Decorador: más de `maximo` pedidos POST en la ventana → 429. Cuenta por
    dirección IP, o por lo que devuelva `por()` (p. ej. la llave del servicio:
    en el hospital muchas PCs salen a internet con la misma IP)."""
    def decorador(vista):
        @wraps(vista)
        def envoltorio(*args, **kwargs):
            if request.method == "POST":
                quien = (por() if por else None) or ip_cliente()
                clave = f"{accion}:{quien}"
                if limitador.bloqueado(clave, maximo, ventana_segundos):
                    abort(429)
                limitador.registrar(clave, ventana_segundos)
            return vista(*args, **kwargs)
        return envoltorio
    return decorador


def aplicar(app):
    configurar_secretos(app)
    configurar_cookies(app)
    configurar_proxy(app)
    configurar_encabezados(app)
