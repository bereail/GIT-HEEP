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
from datetime import datetime, timedelta, timezone

from app.extensions import db


def _ahora():
    return datetime.now(timezone.utc)


def hora_ar(momento, formato="%d/%m/%Y %H:%M"):
    """Fecha guardada en UTC (SQLite la devuelve sin zona) → hora de Argentina."""
    if not momento:
        return ""
    if momento.tzinfo is None:
        momento = momento.replace(tzinfo=timezone.utc)
    return momento.astimezone(timezone(timedelta(hours=-3))).strftime(formato)


def clave_item(nombre_interno):
    """Identificador estable de un ítem: el nombre interno en minúsculas, sin
    tildes y con los espacios normalizados."""
    sin_tildes = unicodedata.normalize("NFKD", nombre_interno or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", sin_tildes).strip().lower()


# Respuesta a "¿Son realmente el mismo artículo?". Las observaciones viejas
# no tienen respuesta (None): cuentan como "sin revisar".
VALIDACIONES = {"si": "Sí, son equivalentes", "no": "No, son diferentes", "duda": "Tengo dudas"}
# Color de cada fila en los Excel según la respuesta (como en la pantalla).
COLOR_EXCEL = {"si": "verde", "no": "rojo", "duda": "naranja", None: "gris"}


def codigo_hospital(notas):
    """El código interno del hospital, que el nomenclador guarda en las notas
    como "[cod. interno 412]". Si no está, devuelve ""."""
    m = re.search(r"\[cod\.? interno ([^\]]+)\]", notas or "", re.I)
    return m.group(1).strip() if m else ""


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
    """La revisión de un ítem por un revisor: la respuesta (sí / no / dudas) y
    una observación opcional. Una por revisor y por ítem; si la cambia, la
    versión anterior queda en el historial."""

    __tablename__ = "observaciones_nomenclador"
    __table_args__ = (db.UniqueConstraint("revisor_id", "clave_item", name="uq_observacion_revisor_item"),)

    id = db.Column(db.Integer, primary_key=True)
    revisor_id = db.Column(db.Integer, db.ForeignKey("revisores_nomenclador.id"), nullable=False, index=True)
    clave_item = db.Column(db.String(300), nullable=False, index=True)
    nombre_item = db.Column(db.String(300), nullable=False)  # cómo se llamaba el ítem al comentarlo
    texto = db.Column(db.Text, nullable=False)  # opcional: puede quedar ""
    validacion = db.Column(db.String(10))  # ver VALIDACIONES; None = sin responder
    creado_en = db.Column(db.DateTime, default=_ahora)
    actualizado_en = db.Column(db.DateTime, default=_ahora)

    revisor = db.relationship("RevisorNomenclador", back_populates="observaciones")
    historial = db.relationship("ObservacionHistorial", back_populates="observacion",
                                order_by="ObservacionHistorial.guardado_en.desc()")


class ObservacionHistorial(db.Model):
    """Versiones anteriores de una revisión (respuesta, texto y cuándo se guardó)."""

    __tablename__ = "observaciones_nomenclador_historial"

    id = db.Column(db.Integer, primary_key=True)
    observacion_id = db.Column(db.Integer, db.ForeignKey("observaciones_nomenclador.id"), nullable=False, index=True)
    texto = db.Column(db.Text, nullable=False)
    validacion = db.Column(db.String(10))
    guardado_en = db.Column(db.DateTime, nullable=False)

    observacion = db.relationship("ObservacionNomenclador", back_populates="historial")
