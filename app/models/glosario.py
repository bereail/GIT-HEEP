from app.extensions import db


class EntradaGlosario(db.Model):
    __tablename__ = "entradas_glosario"

    id = db.Column(db.Integer, primary_key=True)
    tema_id = db.Column(db.Integer, db.ForeignKey("temas.id"), nullable=False)
    termino = db.Column(db.String(150), nullable=False)
    definicion = db.Column(db.Text, nullable=False)
    modulo = db.Column(db.String(150))
    uso = db.Column(db.Text)
