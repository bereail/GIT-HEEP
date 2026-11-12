"""Avisos por mail del circuito de consultas: a vos cuando llega una
consulta nueva, y al usuario cuando la respondés (si dejó su email).

Usa SMTP de Gmail con una App Password (nunca la contraseña real de la
cuenta). Se configura con variables de entorno — si `EMAIL_APP_PASSWORD` no
está definida (como en desarrollo local), simplemente no envía nada: la
consulta/respuesta igual queda guardada en la base y se puede ver desde el
admin o desde "Mis consultas". Si el envío falla por cualquier motivo, no
revierte nada — ya se guardó antes de intentar mandar el mail.
"""

import os
import smtplib
from email.message import EmailMessage

from flask import current_app, url_for

DESTINATARIO = os.environ.get("CONSULTAS_EMAIL_DESTINO", "berenicesolohaga@gmail.com")
REMITENTE = os.environ.get("EMAIL_REMITENTE", DESTINATARIO)
APP_PASSWORD = os.environ.get("EMAIL_APP_PASSWORD")
SMTP_SERVIDOR = os.environ.get("EMAIL_SMTP_SERVIDOR", "smtp.gmail.com")
SMTP_PUERTO = int(os.environ.get("EMAIL_SMTP_PUERTO", "587"))


def _enviar(destinatario, asunto, cuerpo, log_contexto):
    if not APP_PASSWORD or not destinatario:
        return False

    email = EmailMessage()
    email["Subject"] = asunto
    email["From"] = REMITENTE
    email["To"] = destinatario
    email.set_content(cuerpo)

    try:
        with smtplib.SMTP(SMTP_SERVIDOR, SMTP_PUERTO, timeout=10) as smtp:
            smtp.starttls()
            smtp.login(REMITENTE, APP_PASSWORD)
            smtp.send_message(email)
        return True
    except Exception:
        current_app.logger.exception("No se pudo enviar el mail: %s.", log_contexto)
        return False


def notificar_nueva_consulta(consulta, mensaje_texto):
    enlace_admin = url_for("admin.consulta_detalle", token=consulta.token, _external=True)
    cuerpo = (
        f"Tema: {consulta.tema.nombre}\n"
        f"Tipo: {consulta.tipo_label}\n"
        f"De: {consulta.nombre_contacto or 'Anónimo'}\n\n"
        f"{mensaje_texto}\n\n"
        f"Responder → {enlace_admin}"
    )
    asunto = f"[Centro de Aprendizaje] {consulta.tipo_label} — {consulta.tema.nombre}"
    _enviar(DESTINATARIO, asunto, cuerpo, f"aviso de consulta nueva {consulta.token}")


def notificar_respuesta_consulta(consulta, mensaje_texto):
    """Avisa al usuario que dejó su email que su consulta tiene una
    respuesta nueva. Si no dejó email, no hace nada — la respuesta igual
    queda disponible por el link y por "Mis consultas"."""
    if not consulta.email:
        return False

    enlace = url_for("ui.consulta_ver", token=consulta.token, _external=True)
    cuerpo = (
        f"Te respondimos tu {consulta.tipo_label.lower()} sobre {consulta.tema.nombre}:\n\n"
        f"{mensaje_texto}\n\n"
        f"Ver la conversación completa → {enlace}"
    )
    asunto = f"[Centro de Aprendizaje] Nueva respuesta a tu {consulta.tipo_label.lower()}"
    return _enviar(consulta.email, asunto, cuerpo, f"aviso de respuesta {consulta.token}")
