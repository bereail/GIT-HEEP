from datetime import datetime, timezone

from app.extensions import db


def _ahora():
    return datetime.now(timezone.utc)


NIVELES_CONFIANZA = {
    "alta": "Coincidencia clara",
    "dudosa": "Revisar antes de usar",
    "sin_match": "No se encontró en el catálogo oficial",
}


class EquivalenciaArticulo(db.Model):
    """Diccionario que traduce el nombre con el que un artículo se pide en el
    sistema interno de compras del hospital al código/nombre del Catálogo WEB
    oficial de la Provincia (santafe.gov.ar/gestionesdecompras), que es el que
    hay que usar para cargar la gestión en TIMBÓ Compras.

    Se va alimentando pedido a pedido: la tabla vive en
    `scripts/equivalencias_articulos.csv` (versionada en git) y esta tabla de
    la base se repuebla desde ahí con `scripts/importar_equivalencias.py`,
    igual que el resto del contenido del Centro de Aprendizaje."""

    __tablename__ = "equivalencias_articulos"

    id = db.Column(db.Integer, primary_key=True)
    tema_id = db.Column(db.Integer, db.ForeignKey("temas.id"), nullable=False)

    nombre_interno = db.Column(db.String(300), nullable=False, index=True)
    codigo_catalogo = db.Column(db.String(40))
    rubro_especie = db.Column(db.String(200))
    sub_rubro_familia = db.Column(db.String(200))
    bien_o_servicio = db.Column(db.String(200))
    item_especifico = db.Column(db.String(300))
    confianza = db.Column(db.String(20), default="dudosa")  # ver NIVELES_CONFIANZA
    origen = db.Column(db.String(200))  # ej. "Pedido 1984 - Microbiología"
    notas = db.Column(db.Text)

    creado_en = db.Column(db.DateTime, default=_ahora)

    @property
    def confianza_label(self):
        return NIVELES_CONFIANZA.get(self.confianza, self.confianza)
