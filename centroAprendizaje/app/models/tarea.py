from app.extensions import db


class Tarea(db.Model):
    """Una entrada de "Quiero hacer...": una pregunta en lenguaje cotidiano
    que apunta a un tutorial. El título, nivel y duración que se muestran se
    toman del tutorial vinculado (no se duplican acá) para no desincronizar
    dos copias del mismo dato."""

    __tablename__ = "tareas"
    __table_args__ = (db.UniqueConstraint("tema_id", "slug", name="uq_tarea_slug_por_tema"),)

    id = db.Column(db.Integer, primary_key=True)
    tema_id = db.Column(db.Integer, db.ForeignKey("temas.id"), nullable=False)
    slug = db.Column(db.String(80), nullable=False)
    pregunta = db.Column(db.String(250), nullable=False)
    keywords = db.Column(db.JSON, default=list)
    tutorial_id = db.Column(db.Integer, db.ForeignKey("tutoriales.id"), nullable=False)
    orden = db.Column(db.Integer, default=0)

    tutorial = db.relationship("Tutorial")
