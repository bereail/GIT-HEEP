from app.extensions import db


class Situacion(db.Model):
    """Una entrada de "¿Tenés un problema?" (troubleshooting)."""

    __tablename__ = "situaciones"
    __table_args__ = (db.UniqueConstraint("tema_id", "slug", name="uq_situacion_slug_por_tema"),)

    id = db.Column(db.Integer, primary_key=True)
    tema_id = db.Column(db.Integer, db.ForeignKey("temas.id"), nullable=False)
    slug = db.Column(db.String(80), nullable=False)
    situacion = db.Column(db.String(250), nullable=False)
    descripcion = db.Column(db.Text)
    causa = db.Column(db.Text)
    solucion = db.Column(db.Text)
    notas_adicionales = db.Column(db.Text)
    categoria_libre = db.Column(db.String(120))
    tutorial_id = db.Column(db.Integer, db.ForeignKey("tutoriales.id"), nullable=True)
    verificado = db.Column(db.Boolean, default=True)
    orden = db.Column(db.Integer, default=0)

    tutorial = db.relationship("Tutorial")
