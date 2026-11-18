"""Gestión de procesos y circuitos (solo panel de administración).

Dos clases de circuito, que nunca se mezclan:
- "hospital": cómo trabaja hoy Compras, armado en el relevamiento con el
  personal. Arranca vacío: no se carga ningún paso supuesto.
- "oficial": cómo funciona TIMBÓ según documentación oficial. Cada dato
  lleva su fuente; lo que no está documentado queda pendiente.

El dibujo (bloques y flechas) se guarda como JSON en `borrador` (se
autoguarda) y en cada `CircuitoVersion` (cuando la administradora guarda una
versión). Recuperar una versión crea una versión nueva con ese contenido:
nunca se borra historia.
"""
import json
from datetime import datetime, timezone

from app.extensions import db


def _ahora():
    return datetime.now(timezone.utc)


CLASES_CIRCUITO = {
    "hospital": "Circuito actual del hospital",
    "oficial": "Circuito oficial de TIMBÓ",
}

TIPOS_COMENTARIO = {
    "aclaracion": "Aclaración del personal",
    "otra_version": "Otra forma de hacerlo",
    "duda": "Duda",
    "pendiente": "Información pendiente",
    "observacion": "Observación de la administradora",
    "santa_fe": "Pregunta para Santa Fe",
    "mejora": "Sugerencia de mejora",
    "problema": "Problema recurrente",
}

RECURSOS_SUGERENCIA = {
    "nomenclador": "Nomenclador",
    "proveedores": "Sección para proveedores",
    "centro": "Centro de Aprendizaje",
    "circuito": "Circuito de compras",
    "otro": "Otro",
}

CLASES_SUGERENCIA = {
    "necesidad": "Necesidad detectada",
    "funcionalidad": "Sugerencia de funcionalidad",
    "documentacion": "Documentación solicitada",
    "problema": "Problema recurrente",
    "mejora": "Propuesta de mejora",
    "consulta": "Consulta pendiente",
    "prioritario": "Recurso prioritario",
}

ESTADOS_SUGERENCIA = {
    "nueva": "Sin evaluar",
    "evaluando": "En evaluación",
    "aceptada": "Aceptada",
    "descartada": "Descartada",
}

ESTADOS_RANGO = {
    "verificado": "Verificado con fuente oficial",
    "pendiente": "Pendiente de validación",
    "discrepancia": "Discrepancia entre fuentes",
}


class Circuito(db.Model):
    __tablename__ = "procesos_circuitos"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    nombre = db.Column(db.String(200), nullable=False)
    clase = db.Column(db.String(20), nullable=False)  # hospital | oficial
    descripcion = db.Column(db.Text, nullable=False, default="")
    borrador = db.Column(db.Text, nullable=False, default='{"nodos": [], "flechas": []}')
    borrador_actualizado = db.Column(db.DateTime, default=_ahora)
    creado = db.Column(db.DateTime, default=_ahora)

    versiones = db.relationship("CircuitoVersion", backref="circuito", order_by="CircuitoVersion.numero",
                                cascade="all, delete-orphan")
    comentarios = db.relationship("ComentarioCircuito", backref="circuito", order_by="ComentarioCircuito.creado",
                                  cascade="all, delete-orphan")

    @property
    def contenido(self):
        try:
            datos = json.loads(self.borrador or "{}")
        except ValueError:
            datos = {}
        datos.setdefault("nodos", [])
        datos.setdefault("flechas", [])
        return datos

    @property
    def ultima_version(self):
        return self.versiones[-1] if self.versiones else None

    @property
    def hay_cambios_sin_version(self):
        ultima = self.ultima_version
        if not ultima:
            return bool(self.contenido["nodos"])
        return json.loads(ultima.contenido) != self.contenido


class CircuitoVersion(db.Model):
    __tablename__ = "procesos_versiones"

    id = db.Column(db.Integer, primary_key=True)
    circuito_id = db.Column(db.Integer, db.ForeignKey("procesos_circuitos.id"), nullable=False, index=True)
    numero = db.Column(db.Integer, nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    motivo = db.Column(db.Text, nullable=False, default="")
    usuario = db.Column(db.String(80), nullable=False, default="administradora")
    cambios = db.Column(db.Text, nullable=False, default="[]")  # lista de {elemento, accion, antes, despues}
    importante = db.Column(db.Boolean, nullable=False, default=False)
    creado = db.Column(db.DateTime, default=_ahora)

    @property
    def lista_cambios(self):
        try:
            return json.loads(self.cambios or "[]")
        except ValueError:
            return []


class ComentarioCircuito(db.Model):
    """Comentario asociado a un bloque o flecha. No modifica el procedimiento."""

    __tablename__ = "procesos_comentarios"

    id = db.Column(db.Integer, primary_key=True)
    circuito_id = db.Column(db.Integer, db.ForeignKey("procesos_circuitos.id"), nullable=False, index=True)
    elemento_id = db.Column(db.String(40), nullable=False, default="")  # "" = del circuito entero
    tipo = db.Column(db.String(20), nullable=False, default="observacion")
    texto = db.Column(db.Text, nullable=False)
    resuelto = db.Column(db.Boolean, nullable=False, default=False)
    creado = db.Column(db.DateTime, default=_ahora)


class RangoMonto(db.Model):
    """Rango de importes que cambia el procedimiento o la autorización."""

    __tablename__ = "procesos_rangos"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    minimo = db.Column(db.Numeric(16, 2), nullable=True)   # None = desde 0
    maximo = db.Column(db.Numeric(16, 2), nullable=True)   # None = sin tope
    moneda = db.Column(db.String(10), nullable=False, default="ARS")
    condicion = db.Column(db.Text, nullable=False, default="")
    autorizacion = db.Column(db.Text, nullable=False, default="")
    documentacion = db.Column(db.Text, nullable=False, default="")
    fuente_doc = db.Column(db.String(80), nullable=False, default="")  # id de la biblioteca
    fuente_punto = db.Column(db.String(200), nullable=False, default="")
    vigencia_desde = db.Column(db.Date, nullable=True)
    vigencia_hasta = db.Column(db.Date, nullable=True)
    estado = db.Column(db.String(20), nullable=False, default="pendiente")
    actualizado = db.Column(db.DateTime, default=_ahora, onupdate=_ahora)

    def como_dict(self):
        return {
            "id": self.id, "nombre": self.nombre,
            "minimo": float(self.minimo) if self.minimo is not None else None,
            "maximo": float(self.maximo) if self.maximo is not None else None,
            "moneda": self.moneda, "condicion": self.condicion, "autorizacion": self.autorizacion,
            "documentacion": self.documentacion, "fuente_doc": self.fuente_doc, "fuente_punto": self.fuente_punto,
            "vigencia_desde": self.vigencia_desde.isoformat() if self.vigencia_desde else None,
            "vigencia_hasta": self.vigencia_hasta.isoformat() if self.vigencia_hasta else None,
            "estado": self.estado,
        }


class SugerenciaRelevamiento(db.Model):
    """Respuesta o sugerencia que dio el personal en una reunión. Se registra
    para evaluarla; no se implementa nada automáticamente."""

    __tablename__ = "procesos_sugerencias"

    id = db.Column(db.Integer, primary_key=True)
    recurso = db.Column(db.String(20), nullable=False, default="otro")
    pregunta = db.Column(db.Text, nullable=False, default="")
    texto = db.Column(db.Text, nullable=False)
    clase = db.Column(db.String(20), nullable=False, default="necesidad")
    estado = db.Column(db.String(20), nullable=False, default="nueva")
    nota = db.Column(db.Text, nullable=False, default="")
    reunion = db.Column(db.String(120), nullable=False, default="")
    creado = db.Column(db.DateTime, default=_ahora)


class AuditoriaProceso(db.Model):
    """Registro de cambios que no son versiones del dibujo (montos,
    sugerencias, comentarios, recuperaciones)."""

    __tablename__ = "procesos_auditoria"

    id = db.Column(db.Integer, primary_key=True)
    entidad = db.Column(db.String(40), nullable=False)
    entidad_id = db.Column(db.String(40), nullable=False, default="")
    accion = db.Column(db.String(40), nullable=False)
    antes = db.Column(db.Text, nullable=False, default="")
    despues = db.Column(db.Text, nullable=False, default="")
    motivo = db.Column(db.Text, nullable=False, default="")
    usuario = db.Column(db.String(80), nullable=False, default="administradora")
    creado = db.Column(db.DateTime, default=_ahora)
