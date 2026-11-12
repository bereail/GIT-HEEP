"""Importa el contenido del tema TIMBÓ-expedientes a la base de datos.

Lee `scripts/content_timbo_expedientes.json` (contenido extraído a mano de
`timboDocumentacion/guia_usuarios.html` y `guia_capacitadora.html`, que no
tenían una estructura de datos reutilizable como el content.js de
miHospital) y lo vuelca a las tablas del portal.

Es idempotente: si el tema "timbo-expedientes" ya existe, lo borra primero
(con cascade a todo lo que depende de él) y lo vuelve a crear desde el
JSON, igual que `importar_mihospital.py`.

Uso (desde la raíz del proyecto, con el entorno virtual activado):
    python scripts/importar_timbo_expedientes.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import Categoria, EntradaGlosario, PasoIntroductorio, Situacion, Tarea, Tema, Tutorial

RUTA_JSON = os.path.join(os.path.dirname(__file__), "content_timbo_expedientes.json")


def importar(ruta_json=RUTA_JSON, orden_tema=1):
    """Vuelca un JSON de contenido (mismo schema que
    content_timbo_expedientes.json) a la base. Lo reutiliza
    `importar_timbo_compras.py` para su propio JSON."""
    with open(ruta_json, encoding="utf-8") as f:
        datos = json.load(f)

    info_tema = datos["tema"]

    existente = Tema.query.filter_by(slug=info_tema["slug"]).first()
    if existente:
        db.session.delete(existente)
        db.session.commit()

    tema = Tema(
        slug=info_tema["slug"],
        nombre=info_tema["nombre"],
        nombre_completo=info_tema.get("nombre_completo"),
        organizacion=info_tema.get("organizacion"),
        icono=info_tema.get("icono") or "🧭",
        descripcion=info_tema.get("descripcion"),
        alcance=info_tema.get("alcance"),
        recomendaciones=info_tema.get("recomendaciones", []),
        quickstart_titulo=info_tema.get("quickstart_titulo"),
        quickstart_intro=info_tema.get("quickstart_intro"),
        quickstart_cierre=info_tema.get("quickstart_cierre"),
        orden=orden_tema,
    )
    db.session.add(tema)
    db.session.flush()

    tutorial_id_por_clave = {}  # (categoria_slug, tutorial_slug) -> tutorial.id

    for orden_cat, categoria_datos in enumerate(datos["categorias"]):
        categoria = Categoria(
            tema_id=tema.id,
            slug=categoria_datos["slug"],
            titulo=categoria_datos["titulo"],
            icono=categoria_datos.get("icono") or "📁",
            resumen=categoria_datos.get("resumen"),
            audiencia=categoria_datos.get("audiencia"),
            dificultad=categoria_datos.get("dificultad", "basico"),
            orden=orden_cat,
        )
        db.session.add(categoria)
        db.session.flush()

        for orden_tut, tutorial_datos in enumerate(categoria_datos["tutoriales"]):
            tutorial = Tutorial(
                categoria_id=categoria.id,
                slug=tutorial_datos["slug"],
                titulo=tutorial_datos["titulo"],
                minutos=tutorial_datos.get("minutos", 5),
                dificultad=tutorial_datos.get("dificultad", "basico"),
                orden=orden_tut,
                bloques=tutorial_datos.get("bloques", []),
                quiz=tutorial_datos.get("quiz", []),
            )
            db.session.add(tutorial)
            db.session.flush()
            tutorial_id_por_clave[(categoria_datos["slug"], tutorial_datos["slug"])] = tutorial.id

    for termino in datos.get("glosario", []):
        db.session.add(EntradaGlosario(
            tema_id=tema.id,
            termino=termino["termino"],
            definicion=termino["definicion"],
            modulo=termino.get("modulo"),
            uso=termino.get("uso"),
        ))

    situacion_id_por_slug = {}
    for orden, situacion_datos in enumerate(datos.get("situaciones", [])):
        clave = (situacion_datos.get("tutorial_categoria_slug"), situacion_datos.get("tutorial_slug"))
        tutorial_id = tutorial_id_por_clave.get(clave) if clave[0] else None
        fila = Situacion(
            tema_id=tema.id,
            slug=situacion_datos["slug"],
            situacion=situacion_datos["situacion"],
            descripcion=situacion_datos.get("descripcion"),
            causa=situacion_datos.get("causa"),
            solucion=situacion_datos.get("solucion"),
            notas_adicionales=situacion_datos.get("notas_adicionales"),
            categoria_libre=situacion_datos.get("categoria_libre"),
            tutorial_id=tutorial_id,
            verificado=situacion_datos.get("verificado", True),
            orden=orden,
        )
        db.session.add(fila)
        db.session.flush()
        situacion_id_por_slug[situacion_datos["slug"]] = fila.id

    for orden, tarea_datos in enumerate(datos.get("tareas", [])):
        clave = (tarea_datos.get("tutorial_categoria_slug"), tarea_datos.get("tutorial_slug"))
        tutorial_id = tutorial_id_por_clave.get(clave)
        if tutorial_id is None:
            print(f"⚠️  Tarea '{tarea_datos['slug']}' apunta a un tutorial inexistente {clave}, se omite.")
            continue
        db.session.add(Tarea(
            tema_id=tema.id,
            slug=tarea_datos["slug"],
            pregunta=tarea_datos["pregunta"],
            keywords=tarea_datos.get("keywords", []),
            tutorial_id=tutorial_id,
            orden=orden,
        ))

    for orden, paso_datos in enumerate(datos.get("quickstart_steps", [])):
        clave = (paso_datos.get("tutorial_categoria_slug"), paso_datos.get("tutorial_slug"))
        tutorial_id = tutorial_id_por_clave.get(clave) if clave[0] else None
        situacion_id = situacion_id_por_slug.get(paso_datos.get("situacion_slug"))
        db.session.add(PasoIntroductorio(
            tema_id=tema.id,
            orden=orden,
            titulo=paso_datos["titulo"],
            descripcion=paso_datos.get("descripcion"),
            tutorial_id=tutorial_id,
            situacion_id=situacion_id,
        ))

    db.session.commit()

    total_tutoriales = sum(len(c["tutoriales"]) for c in datos["categorias"])
    print(f"Tema '{tema.nombre}' importado: "
          f"{len(datos['categorias'])} categorías, "
          f"{total_tutoriales} tutoriales, "
          f"{len(datos.get('glosario', []))} términos de glosario, "
          f"{len(datos.get('situaciones', []))} situaciones, "
          f"{len(datos.get('tareas', []))} tareas.")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        importar()
