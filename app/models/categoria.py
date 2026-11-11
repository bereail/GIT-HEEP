from app.extensions import db


class Categoria(db.Model):
    """Un módulo dentro de un tema (ej. "Pacientes", "Quirófano"). Agrupa
    tutoriales relacionados."""

    __tablename__ = "categorias"
    __table_args__ = (db.UniqueConstraint("tema_id", "slug", name="uq_categoria_slug_por_tema"),)

    id = db.Column(db.Integer, primary_key=True)
    tema_id = db.Column(db.Integer, db.ForeignKey("temas.id"), nullable=False)
    slug = db.Column(db.String(60), nullable=False)
    titulo = db.Column(db.String(150), nullable=False)
    icono = db.Column(db.String(8), default="📁")
    resumen = db.Column(db.Text)
    audiencia = db.Column(db.Text)
    dificultad = db.Column(db.String(20), default="basico")
    orden = db.Column(db.Integer, default=0)

    tutoriales = db.relationship(
        "Tutorial", backref="categoria", order_by="Tutorial.orden", cascade="all, delete-orphan"
    )
