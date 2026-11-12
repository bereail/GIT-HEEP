"""Aviso por mail cuando llega una consulta nueva desde el portal.

Usa SMTP de Gmail con una App Password (nunca la contraseña real de la
cuenta). Se configura con variables de entorno — si `EMAIL_APP_PASSWORD` no
está definida (como en desarrollo local), simplemente no envía nada: la
consulta igual queda guardada en la base y se puede ver desde el admin.
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


def notificar_nueva_consulta(consulta, mensaje_texto):
    if not APP_PASSWORD:
        return

    enlace_admin = url_for("admin.consulta_detalle", token=consulta.token, _external=True)
    cuerpo = (
        f"Tema: {consulta.tema.nombre}\n"
        f"Tipo: {consulta.tipo_label}\n"
        f"De: {consulta.nombre_contacto or 'Anónimo'}\n\n"
        f"{mensaje_texto}\n\n"
        f"Responder → {enlace_admin}"
    )
    email = EmailMessage()
    email["Subject"] = f"[Centro de Aprendizaje] {consulta.tipo_label} — {consulta.tema.nombre}"
    email["From"] = REMITENTE
    email["To"] = DESTINATARIO
    email.set_content(cuerpo)

    try:
        with smtplib.SMTP(SMTP_SERVIDOR, SMTP_PUERTO, timeout=10) as smtp:
            smtp.starttls()
            smtp.login(REMITENTE, APP_PASSWORD)
            smtp.send_message(email)
    except Exception:
        current_app.logger.exception("No se pudo enviar el aviso por mail de la consulta %s.", consulta.token)
