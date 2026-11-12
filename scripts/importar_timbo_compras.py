"""Importa el tema TIMBÓ Compras a la base de datos.

Lee `scripts/content_timbo_compras.json`, armado a partir de:
- la lista oficial de videos "Timbó Compras" de YouTube (lado proveedor:
  requisitos, ingresar, ofertar, consultas, subsanaciones e impugnaciones);
- las consultas reales de soporte del grupo de Compras del hospital
  (decisorios, vista al Tribunal de Cuentas, SIN y publicación), que además
  carga `importar_faq_chats.py` como situaciones de "Tengo un problema".

Usa el mismo importador que TIMBÓ (Expedientes), así que también es
idempotente a nivel de tema: si "timbo-compras" ya existe, se borra y se
recrea desde el JSON.

Uso: python scripts/importar_timbo_compras.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from importar_timbo_expedientes import importar

RUTA_JSON = os.path.join(os.path.dirname(__file__), "content_timbo_compras.json")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        importar(RUTA_JSON, orden_tema=2)
