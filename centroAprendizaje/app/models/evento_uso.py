from datetime import datetime, timezone

from app.extensions import db


def _ahora():
    return datetime.now(timezone.utc)


class EventoUso(db.Model):
    """Registro anónimo de uso del portal: qué se mira, qué se busca y qué
    feedback dejan sobre una lección. Sirve para armar las estadísticas del
    admin. No guarda IP ni ningún dato que identifique a quien lo generó."""

    __tablename__ = "eventos_uso"

    id = db.Column(db.Integer, primary_key=True)
    tema_id = db.Column(db.Integer, db.ForeignKey("temas.id"), nullable=True, index=True)
    tipo = db.Column(db.String(30), nullable=False, index=True)
    titulo = db.Column(db.String(200))
    consulta = db.Column(db.String(200))
    hubo_resultado = db.Column(db.Boolean)
    creado_en = db.Column(db.DateTime, default=_ahora, index=True)

    tema = db.relationship("Tema")
