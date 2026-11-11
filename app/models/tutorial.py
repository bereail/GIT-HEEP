from app.extensions import db


class Tutorial(db.Model):
    """Una lección/tutorial puntual (ej. "Buscar un paciente"). `bloques` y
    `quiz` quedan en JSON porque cada bloque es heterogéneo (texto, paso con
    captura, tip, advertencia, concepto, esquema) y así se preserva 1:1 la
    estructura ya validada en timbo-capacitacion/content.js, sin perder
    flexibilidad editorial. El panel de administración (Etapa 2) va a ofrecer
    formularios estructurados por tipo de bloque sobre este mismo campo."""

    __tablename__ = "tutoriales"
    __table_args__ = (db.UniqueConstraint("categoria_id", "slug", name="uq_tutorial_slug_por_categoria"),)

    id = db.Column(db.Integer, primary_key=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey("categorias.id"), nullable=False)
    slug = db.Column(db.String(80), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    minutos = db.Column(db.Integer, default=5)
    dificultad = db.Column(db.String(20), default="basico")
    orden = db.Column(db.Integer, default=0)

    bloques = db.Column(db.JSON, default=list)
    quiz = db.Column(db.JSON, default=list)
