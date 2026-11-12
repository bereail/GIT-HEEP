from datetime import datetime, timezone

from app.extensions import db

CATEGORIAS_FEEDBACK = {
    "sugerencia": "Sugerencia",
    "positivo": "Aspecto positivo",
    "problema": "Problema detectado",
}


def _ahora():
    return datetime.now(timezone.utc)


class Feedback(db.Model):
    """Una valoración (1-5 estrellas) y/o comentario libre dejado por un
    usuario sin cuenta ni login, sobre un tema o un tutorial puntual.

    La puntuación es independiente del comentario: puede haber una sin la
    otra. Es distinto del botón "¿te sirvió?" (sí/no) que ya existe por
    lección — ese sigue registrándose en EventoUso porque es un evento de
    uso liviano, mientras que esto es contenido (texto) que un admin
    revisa, así que vive en su propia tabla."""

    __tablename__ = "feedbacks"

    id = db.Column(db.Integer, primary_key=True)
    tema_id = db.Column(db.Integer, db.ForeignKey("temas.id"), nullable=False)
    tutorial_id = db.Column(db.Integer, db.ForeignKey("tutoriales.id"), nullable=True)
    puntuacion = db.Column(db.Integer, nullable=True)  # 1-5, independiente del comentario
    comentario = db.Column(db.Text, nullable=True)
    categoria = db.Column(db.String(20), nullable=True)  # ver CATEGORIAS_FEEDBACK
    revisado = db.Column(db.Boolean, default=False, nullable=False)
    creado_en = db.Column(db.DateTime, default=_ahora, index=True)

    tema = db.relationship("Tema")
    tutorial = db.relationship("Tutorial")

    @property
    def categoria_label(self):
        return CATEGORIAS_FEEDBACK.get(self.categoria, self.categoria)
