from datetime import datetime, timezone

from app.extensions import db

TIPOS_CONSULTA = {
    "consulta": "Consulta",
    "problema": "Problema",
    "sugerencia": "Sugerencia",
    "solicitud_capacitacion": "Solicitud de nueva capacitación",
}

ESTADOS_CONSULTA = {
    "abierta": "Pendiente",
    "en_revision": "En revisión",
    "respondida": "Respondida",
    "cerrada": "Cerrada",
}


def _ahora():
    return datetime.now(timezone.utc)


class Consulta(db.Model):
    """Una consulta/problema/sugerencia dejada por un usuario sin cuenta ni
    login. Se accede por un token impredecible en la URL (no por id
    secuencial) para que nadie pueda leer la consulta de otra persona
    adivinando o incrementando un número."""

    __tablename__ = "consultas"

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(32), unique=True, nullable=False, index=True)
    tema_id = db.Column(db.Integer, db.ForeignKey("temas.id"), nullable=False)
    tipo = db.Column(db.String(30), nullable=False, default="consulta")
    estado = db.Column(db.String(20), nullable=False, default="abierta")
    nombre_contacto = db.Column(db.String(150))
    email = db.Column(db.String(200))
    creada_en = db.Column(db.DateTime, default=_ahora)
    actualizada_en = db.Column(db.DateTime, default=_ahora, onupdate=_ahora)
    vista_por_admin_en = db.Column(db.DateTime, nullable=True)

    tema = db.relationship("Tema")
    mensajes = db.relationship(
        "MensajeConsulta", backref="consulta", order_by="MensajeConsulta.creado_en", cascade="all, delete-orphan"
    )

    @property
    def tipo_label(self):
        return TIPOS_CONSULTA.get(self.tipo, self.tipo)

    @property
    def estado_label(self):
        return ESTADOS_CONSULTA.get(self.estado, self.estado)

    @property
    def ultimo_mensaje(self):
        return self.mensajes[-1] if self.mensajes else None

    @property
    def no_leida_por_admin(self):
        """True si el último mensaje es del usuario y el admin todavía no
        abrió esta consulta desde que se escribió (o nunca la abrió)."""
        ultimo = self.ultimo_mensaje
        if not ultimo or ultimo.autor != "usuario":
            return False
        if self.vista_por_admin_en is None:
            return True
        return ultimo.creado_en > self.vista_por_admin_en


class MensajeConsulta(db.Model):
    __tablename__ = "mensajes_consulta"

    id = db.Column(db.Integer, primary_key=True)
    consulta_id = db.Column(db.Integer, db.ForeignKey("consultas.id"), nullable=False)
    autor = db.Column(db.String(10), nullable=False)  # "usuario" | "admin"
    cuerpo = db.Column(db.Text, nullable=False)
    creado_en = db.Column(db.DateTime, default=_ahora)
