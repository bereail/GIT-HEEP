"""Revisión del nomenclador por una persona externa al panel.

La persona entra con un enlace privado (token) y deja observaciones junto a
los ítems en amarillo ("dudosa"). Las observaciones NO tocan la tabla del
nomenclador: se guardan aparte y se vinculan por `clave_item`, que sale del
nombre interno del artículo. No se usa el `id` de `equivalencias_articulos`
porque `importar_equivalencias.py` borra y recarga esa tabla en cada deploy.
"""
import hashlib
import re
import unicodedata
from datetime import datetime, timezone

from app.extensions import db


def _ahora():
    return datetime.now(timezone.utc)


def clave_item(nombre_interno):
    """Identificador estable de un ítem: el nombre interno en minúsculas, sin
    tildes y con los espacios normalizados."""
    sin_tildes = unicodedata.normalize("NFKD", nombre_interno or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", sin_tildes).strip().lower()


def hash_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class RevisorNomenclador(db.Model):
    """Persona habilitada para revisar el nomenclador. Del enlace solo se
    guarda el hash: si se pierde, se genera uno nuevo desde el panel."""

    __tablename__ = "revisores_nomenclador"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    token_hash = db.Column(db.String(64), nullable=False, unique=True, index=True)
    activo = db.Column(db.Boolean, nullable=False, default=True)
    creado_en = db.Column(db.DateTime, default=_ahora)
    ultimo_acceso = db.Column(db.DateTime)

    observaciones = db.relationship("ObservacionNomenclador", back_populates="revisor")


class ObservacionNomenclador(db.Model):
    """Una observación por revisor y por ítem; si la edita, la versión
    anterior queda en el historial."""

    __tablename__ = "observaciones_nomenclador"
    __table_args__ = (db.UniqueConstraint("revisor_id", "clave_item", name="uq_observacion_revisor_item"),)

    id = db.Column(db.Integer, primary_key=True)
    revisor_id = db.Column(db.Integer, db.ForeignKey("revisores_nomenclador.id"), nullable=False, index=True)
    clave_item = db.Column(db.String(300), nullable=False, index=True)
    nombre_item = db.Column(db.String(300), nullable=False)  # cómo se llamaba el ítem al comentarlo
    texto = db.Column(db.Text, nullable=False)
    creado_en = db.Column(db.DateTime, default=_ahora)
    actualizado_en = db.Column(db.DateTime, default=_ahora)

    revisor = db.relationship("RevisorNomenclador", back_populates="observaciones")
    historial = db.relationship("ObservacionHistorial", back_populates="observacion",
                                order_by="ObservacionHistorial.guardado_en.desc()")


class ObservacionHistorial(db.Model):
    """Versiones anteriores de una observación (texto y cuándo se guardó)."""

    __tablename__ = "observaciones_nomenclador_historial"

    id = db.Column(db.Integer, primary_key=True)
    observacion_id = db.Column(db.Integer, db.ForeignKey("observaciones_nomenclador.id"), nullable=False, index=True)
    texto = db.Column(db.Text, nullable=False)
    guardado_en = db.Column(db.DateTime, nullable=False)

    observacion = db.relationship("ObservacionNomenclador", back_populates="historial")
