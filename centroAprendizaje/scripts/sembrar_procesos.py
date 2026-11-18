"""Carga inicial de la gestión de procesos (/admin/procesos).

Crea solo lo que falta y NUNCA pisa lo existente: el circuito oficial de
TIMBÓ (armado con fragmentos de documentos oficiales), el circuito del
hospital vacío y los rangos de montos 2026. Se puede correr en cada deploy.

Uso: python scripts/sembrar_procesos.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.procesos.semilla import sembrar

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        hecho = sembrar()
        print("Procesos: " + (", ".join(hecho) if hecho else "nada para crear (ya estaba todo)."))
