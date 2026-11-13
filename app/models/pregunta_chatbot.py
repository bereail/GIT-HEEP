from datetime import datetime, timezone

from app.extensions import db

MOTIVOS_PREGUNTA = {
    "sin_respuesta": "No encontró nada",
    "dudosa": "No estaba seguro (ofreció opciones)",
    "no_sirvio": "Respondió, pero tocaron 👎",
}


def _ahora():
    return datetime.now(timezone.utc)


class PreguntaChatbot(db.Model):
    """Pregunta que el chatbot no supo responder bien. Sirve para saber qué
    contenido falta: se agrupa por texto normalizado y se cuenta cuántas
    veces apareció, sin guardar quién preguntó."""

    __tablename__ = "preguntas_chatbot"
    __table_args__ = (
        db.UniqueConstraint("tema_id", "texto_normalizado", "motivo", name="uq_pregunta_chatbot"),
    )

    id = db.Column(db.Integer, primary_key=True)
    tema_id = db.Column(db.Integer, db.ForeignKey("temas.id"), nullable=False)
    texto = db.Column(db.String(300), nullable=False)
    texto_normalizado = db.Column(db.String(300), nullable=False)
    motivo = db.Column(db.String(20), nullable=False)
    veces = db.Column(db.Integer, nullable=False, default=1)
    resuelta = db.Column(db.Boolean, nullable=False, default=False)
    primera_vez = db.Column(db.DateTime, default=_ahora)
    ultima_vez = db.Column(db.DateTime, default=_ahora)

    tema = db.relationship("Tema")

    @property
    def motivo_label(self):
        return MOTIVOS_PREGUNTA.get(self.motivo, self.motivo)

    @classmethod
    def registrar(cls, tema, texto, texto_normalizado, motivo):
        texto = texto.strip()[:300]
        texto_normalizado = texto_normalizado.strip()[:300]
        if not texto_normalizado:
            return
        fila = cls.query.filter_by(tema_id=tema.id, texto_normalizado=texto_normalizado, motivo=motivo).first()
        if fila:
            fila.veces += 1
            fila.ultima_vez = _ahora()
            fila.resuelta = False
        else:
            db.session.add(cls(tema_id=tema.id, texto=texto, texto_normalizado=texto_normalizado, motivo=motivo))
        db.session.commit()
