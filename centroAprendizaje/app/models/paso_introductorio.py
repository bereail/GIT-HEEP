from app.extensions import db


class PasoIntroductorio(db.Model):
    """Un paso de la ruta guiada "Primeros 15 minutos" de un tema. Apunta a
    un tutorial o a una situación; si no apunta a ninguno, es un paso
    puramente informativo (ej. "Conocé el sistema")."""

    __tablename__ = "pasos_introductorios"

    id = db.Column(db.Integer, primary_key=True)
    tema_id = db.Column(db.Integer, db.ForeignKey("temas.id"), nullable=False)
    orden = db.Column(db.Integer, default=0)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    tutorial_id = db.Column(db.Integer, db.ForeignKey("tutoriales.id"), nullable=True)
    situacion_id = db.Column(db.Integer, db.ForeignKey("situaciones.id"), nullable=True)

    tutorial = db.relationship("Tutorial")
    situacion = db.relationship("Situacion")
