"""Revisión de artículos por servicio, en línea, con llave de acceso.

Es un circuito aparte de la revisión de Farmacia (`revision_nomenclador.py`):
tablas propias, llaves propias y pantallas propias. No se toca nada de aquel.

- Cada llave es de un servicio y tiene asignadas una o más bodegas. Quien
  entra con la llave ve solo los artículos de esas bodegas: el filtro sale
  siempre de la llave guardada en el servidor, nunca del pedido.
- La asignación de bodegas la decide la administración; queda registrada
  (qué, cuándo) en `llaves_servicio_registro`.
- Las respuestas se vinculan por llave + código interno del artículo, no por
  el `id` de `equivalencias_articulos`, que `importar_equivalencias.py` borra
  y recarga en cada deploy. Un artículo que está en dos bodegas de la misma
  llave se responde una sola vez.
- Cada respuesta guarda quién la dio (`persona`). Si cambia, la versión
  anterior queda en el historial.
"""
from datetime import datetime, timezone

from app.extensions import db


def _ahora():
    return datetime.now(timezone.utc)


# Mismos resultados que la planilla descargable (`static/js/revision_servicio.js`).
RESULTADOS_SERVICIO = {
    "no_necesario": "No se usa",
    "otro_servicio": "No es de este servicio",
    "no_corresponde": "No corresponde",
    "aclaracion": "Requiere aclaración",
    "correcto": "Correcto / corresponde",
}
TIPOS_NECESIDAD = {"farmacia": "Medicamento o descartable de Farmacia", "otro": "Otro bien o servicio", "no_se": "No sé"}
# Qué hacer con un artículo cuyo código propuesto no corresponde (se decide en
# la revisión final). «No se usa» no es una decisión: pasa a ese resultado.
DECISIONES = {"agregar": "Hay que agregarlo al nomenclador", "codigo": "Se sabe el código correcto",
              "general": "Es un ítem general de TIMBÓ: el detalle va en la observación"}
CATALOGO_NECESIDAD = {"no_busque": "Todavía no lo busqué", "no_esta": "Lo busqué y no está", "esta": "Lo busqué y sí está"}


class LlaveServicio(db.Model):
    """Acceso de un servicio. Del enlace solo se guarda el hash."""

    __tablename__ = "llaves_servicio"

    id = db.Column(db.Integer, primary_key=True)
    servicio = db.Column(db.String(120), nullable=False)
    token_hash = db.Column(db.String(64), nullable=False, unique=True, index=True)
    activo = db.Column(db.Boolean, nullable=False, default=True)
    creado_en = db.Column(db.DateTime, default=_ahora)
    ultimo_acceso = db.Column(db.DateTime)
    finalizado_en = db.Column(db.DateTime)  # el servicio marcó "Terminé"; se borra si vuelve a cambiar algo
    finalizado_por = db.Column(db.String(160))
    # El servicio envió la revisión: desde ahí no puede cambiar nada (solo el
    # administrador puede reabrirla). Nada se borra.
    enviado_en = db.Column(db.DateTime)
    enviado_por = db.Column(db.String(160))

    bodegas = db.relationship("LlaveBodega", back_populates="llave", cascade="all, delete-orphan",
                              order_by="LlaveBodega.bodega")
    revisiones = db.relationship("RevisionArticuloServicio", back_populates="llave")
    necesidades = db.relationship("NecesidadServicio", back_populates="llave", order_by="NecesidadServicio.creado_en")
    registro = db.relationship("RegistroLlaveServicio", back_populates="llave",
                               order_by="RegistroLlaveServicio.en.desc()")

    @property
    def nombres_bodegas(self):
        return [b.bodega for b in self.bodegas]


class LlaveBodega(db.Model):
    __tablename__ = "llaves_servicio_bodegas"
    __table_args__ = (db.UniqueConstraint("llave_id", "bodega", name="uq_llave_bodega"),)

    id = db.Column(db.Integer, primary_key=True)
    llave_id = db.Column(db.Integer, db.ForeignKey("llaves_servicio.id"), nullable=False, index=True)
    bodega = db.Column(db.String(120), nullable=False)
    asignada_en = db.Column(db.DateTime, default=_ahora)

    llave = db.relationship("LlaveServicio", back_populates="bodegas")


class RegistroLlaveServicio(db.Model):
    """Qué se hizo con cada llave: creación, bodegas asignadas o quitadas,
    enlace nuevo, baja, finalización."""

    __tablename__ = "llaves_servicio_registro"

    id = db.Column(db.Integer, primary_key=True)
    llave_id = db.Column(db.Integer, db.ForeignKey("llaves_servicio.id"), nullable=False, index=True)
    accion = db.Column(db.String(80), nullable=False)
    detalle = db.Column(db.Text, nullable=False, default="")
    en = db.Column(db.DateTime, nullable=False, default=_ahora)

    llave = db.relationship("LlaveServicio", back_populates="registro")


class RevisionArticuloServicio(db.Model):
    """La respuesta de un servicio sobre un artículo de sus bodegas."""

    __tablename__ = "revisiones_servicio"
    __table_args__ = (db.UniqueConstraint("llave_id", "codigo_interno", name="uq_revision_servicio_articulo"),)

    id = db.Column(db.Integer, primary_key=True)
    llave_id = db.Column(db.Integer, db.ForeignKey("llaves_servicio.id"), nullable=False, index=True)
    codigo_interno = db.Column(db.String(40), nullable=False, index=True)
    nombre_item = db.Column(db.String(300), nullable=False)  # cómo se llamaba al responder
    codigo_propuesto = db.Column(db.String(40), nullable=False, default="")  # el que se estaba evaluando
    resultado = db.Column(db.String(20))  # ver RESULTADOS_SERVICIO; None = solo observación
    observacion = db.Column(db.Text, nullable=False, default="")
    decision = db.Column(db.String(20))  # ver DECISIONES; solo si resultado = no_corresponde
    codigo_correcto = db.Column(db.String(40), nullable=False, default="")
    # Ítem general (decision = general): qué escribir en la observación al pedirlo en TIMBÓ.
    detalle_timbo = db.Column(db.String(300), nullable=False, default="")
    persona = db.Column(db.String(160), nullable=False)
    creado_en = db.Column(db.DateTime, default=_ahora)
    actualizado_en = db.Column(db.DateTime, default=_ahora)

    llave = db.relationship("LlaveServicio", back_populates="revisiones")
    historial = db.relationship("RevisionServicioHistorial", back_populates="revision",
                                order_by="RevisionServicioHistorial.guardado_en.desc()")


class RevisionServicioHistorial(db.Model):
    __tablename__ = "revisiones_servicio_historial"

    id = db.Column(db.Integer, primary_key=True)
    revision_id = db.Column(db.Integer, db.ForeignKey("revisiones_servicio.id"), nullable=False, index=True)
    resultado = db.Column(db.String(20))
    observacion = db.Column(db.Text, nullable=False, default="")
    decision = db.Column(db.String(20))
    codigo_correcto = db.Column(db.String(40), nullable=False, default="")
    detalle_timbo = db.Column(db.String(300), nullable=False, default="")
    codigo_propuesto = db.Column(db.String(40), nullable=False, default="")
    persona = db.Column(db.String(160), nullable=False)
    guardado_en = db.Column(db.DateTime, nullable=False)

    revision = db.relationship("RevisionArticuloServicio", back_populates="historial")


class NecesidadServicio(db.Model):
    """Artículo que el servicio necesita y no está en su lista. Al quitarlo
    queda marcado (`quitada_en`), no se borra."""

    __tablename__ = "necesidades_servicio"

    id = db.Column(db.Integer, primary_key=True)
    llave_id = db.Column(db.Integer, db.ForeignKey("llaves_servicio.id"), nullable=False, index=True)
    descripcion = db.Column(db.String(300), nullable=False)
    presentacion = db.Column(db.String(200), nullable=False, default="")
    uso = db.Column(db.String(300), nullable=False, default="")
    tipo = db.Column(db.String(20), nullable=False, default="")  # ver TIPOS_NECESIDAD
    catalogo = db.Column(db.String(20), nullable=False, default="no_busque")  # ver CATALOGO_NECESIDAD
    codigo_catalogo = db.Column(db.String(40), nullable=False, default="")
    observaciones = db.Column(db.Text, nullable=False, default="")
    persona = db.Column(db.String(160), nullable=False)
    creado_en = db.Column(db.DateTime, default=_ahora)
    actualizado_en = db.Column(db.DateTime, default=_ahora)
    quitada_en = db.Column(db.DateTime)

    llave = db.relationship("LlaveServicio", back_populates="necesidades")


class ActualizacionCatalogo(db.Model):
    """Cada corrida de la comparación diaria con el Catálogo WEB
    (`scripts/actualizar_catalogo.py`). Nunca se borra: es el historial."""

    __tablename__ = "actualizaciones_catalogo"

    id = db.Column(db.Integer, primary_key=True)
    en = db.Column(db.DateTime, nullable=False, default=_ahora)
    estado = db.Column(db.String(20), nullable=False)  # ok / error / alerta
    mensaje = db.Column(db.Text, nullable=False, default="")
    archivo = db.Column(db.String(200), nullable=False, default="")  # copia del catálogo de ese día
    items = db.Column(db.Integer, nullable=False, default=0)
    nuevos = db.Column(db.Integer, nullable=False, default=0)
    quitados = db.Column(db.Integer, nullable=False, default=0)
    cambiados = db.Column(db.Integer, nullable=False, default=0)
    no_utilizar = db.Column(db.Integer, nullable=False, default=0)
    afectados = db.Column(db.Integer, nullable=False, default=0)  # artículos del hospital con un código que cambió
    respuestas = db.Column(db.Integer, nullable=False, default=0)  # cuántas respuestas había (control de pérdida)
    detalle = db.Column(db.Text, nullable=False, default="{}")  # JSON con las listas
