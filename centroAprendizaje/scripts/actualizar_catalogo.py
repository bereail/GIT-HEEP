"""Comparación diaria con el Catálogo WEB (ver app/services/catalogo_diario.py).

En el servidor la corre cron CADA HORA con `--diario`, como
timbo-capacitaciones (scripts/servidor/instalar_catalogo_diario.sh): solo
trabaja a las 6 de la mañana de Argentina y una vez por día, sin importar en
qué zona horaria esté el servidor. A mano (corre siempre):
    .venv/bin/python scripts/actualizar_catalogo.py
Termina con código 1 si hubo error o alerta (queda registrado en /admin).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from app.services import catalogo_diario  # noqa: E402

HORA_AR = 6

app = create_app()
with app.app_context():
    if "--diario" in sys.argv:
        from datetime import datetime, timedelta, timezone

        from app.models.revision_servicio import ActualizacionCatalogo

        zona = timezone(timedelta(hours=-3))   # Argentina: UTC−3 todo el año (igual que hora_ar)
        ahora_ar = datetime.now(zona)
        if ahora_ar.hour != HORA_AR:
            sys.exit(0)
        ultima = ActualizacionCatalogo.query.filter(ActualizacionCatalogo.estado != "error") \
            .order_by(ActualizacionCatalogo.en.desc()).first()
        if ultima and ultima.en.replace(tzinfo=timezone.utc).astimezone(zona).date() == ahora_ar.date():
            sys.exit(0)   # hoy ya se actualizó
    ruta = app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "", 1)
    # «--ya-marcado»: lo lanzó el panel, que ya dejó la marca de «en curso».
    if "--ya-marcado" not in sys.argv and catalogo_diario.en_curso(app.instance_path):
        print("Ya hay una actualización en curso: no se corre otra.")
        sys.exit(0)
    marca = catalogo_diario.marca_en_curso(app.instance_path)
    try:
        r = catalogo_diario.actualizar(app.instance_path, ruta)
    finally:
        try:
            os.remove(marca)
        except OSError:
            pass
    print(f"{r.en:%Y-%m-%d %H:%M} {r.estado}: {r.mensaje} | ítems {r.items}, nuevos {r.nuevos}, quitados {r.quitados}, "
          f"cambiados {r.cambiados}, NO UTILIZAR {r.no_utilizar}, artículos afectados {r.afectados}, respuestas {r.respuestas}")
    sys.exit(0 if r.estado == "ok" else 1)
