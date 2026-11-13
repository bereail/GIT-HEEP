from app.extensions import db


class Tema(db.Model):
    """Un sistema o herramienta sobre el que existe una capacitación completa
    (por ejemplo, miHospital o TIMBÓ-expedientes). Agregar un tema nuevo no
    requiere código nuevo: alcanza con crear filas en esta tabla y en las que
    cuelgan de ella."""

    __tablename__ = "temas"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(60), unique=True, nullable=False)
    nombre = db.Column(db.String(120), nullable=False)
    nombre_completo = db.Column(db.String(200))
    organizacion = db.Column(db.String(200))
    icono = db.Column(db.String(8), default="🧭")
    descripcion = db.Column(db.Text)
    alcance = db.Column(db.Text)
    recomendaciones = db.Column(db.JSON, default=list)

    quickstart_titulo = db.Column(db.String(200))
    quickstart_intro = db.Column(db.Text)
    quickstart_cierre = db.Column(db.Text)

    orden = db.Column(db.Integer, default=0)
    activo = db.Column(db.Boolean, default=True)

    categorias = db.relationship(
        "Categoria", backref="tema", order_by="Categoria.orden", cascade="all, delete-orphan"
    )
    entradas_glosario = db.relationship(
        "EntradaGlosario", backref="tema", order_by="EntradaGlosario.termino", cascade="all, delete-orphan"
    )
    situaciones = db.relationship(
        "Situacion", backref="tema", order_by="Situacion.orden", cascade="all, delete-orphan"
    )
    tareas = db.relationship("Tarea", backref="tema", order_by="Tarea.orden", cascade="all, delete-orphan")
    pasos_introductorios = db.relationship(
        "PasoIntroductorio",
        backref="tema",
        order_by="PasoIntroductorio.orden",
        cascade="all, delete-orphan",
    )
    equivalencias_articulos = db.relationship(
        "EquivalenciaArticulo",
        backref="tema",
        order_by="EquivalenciaArticulo.nombre_interno",
        cascade="all, delete-orphan",
    )
