"""Importa el contenido del tema miHospital a la base de datos.

Lee `scripts/content_mihospital.json` (generado con
`node scripts/exportar_content_js.mjs > scripts/content_mihospital.json` a
partir de la fuente de verdad original en
`timboDocumentacion/timbo-capacitacion/content/content.js`) y lo vuelca a las
tablas del portal. Es idempotente: si el tema "mihospital" ya existe, lo
borra primero (con cascade a todo lo que depende de él) y lo vuelve a crear
desde cero, para que el contenido de la base siempre quede igual al del
JSON de origen.

Uso (desde la raíz del proyecto, con el entorno virtual activado):
    python scripts/importar_mihospital.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import Categoria, EntradaGlosario, PasoIntroductorio, Situacion, Tarea, Tema, Tutorial
from app.services.importacion import reasignar_datos_de_usuarios, recordar_datos_de_usuarios

RUTA_JSON = os.path.join(os.path.dirname(__file__), "content_mihospital.json")


def importar():
    with open(RUTA_JSON, encoding="utf-8") as f:
        datos = json.load(f)

    sistema = datos["SYSTEM_INFO"]

    existente = Tema.query.filter_by(slug="mihospital").first()
    estado_usuarios = recordar_datos_de_usuarios(existente)
    if existente:
        db.session.delete(existente)
        db.session.commit()

    tema = Tema(
        slug="mihospital",
        nombre=sistema["name"],
        nombre_completo=sistema["fullName"],
        organizacion=sistema["org"],
        icono="🏥",
        descripcion=sistema["description"],
        alcance=sistema.get("scope"),
        recomendaciones=sistema.get("recommendations", []),
        quickstart_titulo=datos["QUICKSTART"]["title"],
        quickstart_intro=datos["QUICKSTART"]["intro"],
        quickstart_cierre=datos["QUICKSTART"]["outro"],
        orden=0,
    )
    db.session.add(tema)
    db.session.flush()  # para tener tema.id disponible

    categoria_id_por_module_id = {}
    tutorial_id_por_clave = {}  # (moduleId, lessonId) -> tutorial.id

    for orden_cat, modulo in enumerate(datos["MODULES"]):
        categoria = Categoria(
            tema_id=tema.id,
            slug=modulo["id"],
            titulo=modulo["title"],
            icono=modulo["icon"],
            resumen=modulo.get("summary"),
            audiencia=modulo.get("audience"),
            dificultad=modulo.get("difficulty", "basico"),
            orden=orden_cat,
        )
        db.session.add(categoria)
        db.session.flush()
        categoria_id_por_module_id[modulo["id"]] = categoria.id

        for orden_tut, leccion in enumerate(modulo["lessons"]):
            tutorial = Tutorial(
                categoria_id=categoria.id,
                slug=leccion["id"],
                titulo=leccion["title"],
                minutos=leccion.get("minutes", 5),
                dificultad=leccion.get("difficulty", "basico"),
                orden=orden_tut,
                bloques=leccion.get("blocks", []),
                quiz=leccion.get("quiz", []),
            )
            db.session.add(tutorial)
            db.session.flush()
            tutorial_id_por_clave[(modulo["id"], leccion["id"])] = tutorial.id

    for termino in datos["GLOSSARY"]:
        db.session.add(EntradaGlosario(
            tema_id=tema.id,
            termino=termino["term"],
            definicion=termino["definition"],
            modulo=termino.get("module"),
            uso=termino.get("usage"),
        ))

    situacion_id_por_slug = {}
    for orden, situacion in enumerate(datos["SITUATIONS"]):
        va_a = situacion.get("goesTo")
        tutorial_id = tutorial_id_por_clave.get((va_a["moduleId"], va_a["lessonId"])) if va_a else None
        fila = Situacion(
            tema_id=tema.id,
            slug=situacion["id"],
            situacion=situacion["situation"],
            descripcion=situacion.get("description"),
            causa=situacion.get("cause"),
            solucion=situacion.get("solution"),
            tutorial_id=tutorial_id,
            verificado=situacion.get("verified", True),
            orden=orden,
        )
        db.session.add(fila)
        db.session.flush()
        situacion_id_por_slug[situacion["id"]] = fila.id

    for orden, tarea in enumerate(datos["TASKS"]):
        tutorial_id = tutorial_id_por_clave.get((tarea["moduleId"], tarea["lessonId"]))
        if tutorial_id is None:
            print(f"⚠️  Tarea '{tarea['id']}' apunta a una lección inexistente, se omite.")
            continue
        db.session.add(Tarea(
            tema_id=tema.id,
            slug=tarea["id"],
            pregunta=tarea["question"],
            keywords=tarea.get("keywords", []),
            tutorial_id=tutorial_id,
            orden=orden,
        ))

    for orden, paso in enumerate(datos["QUICKSTART"]["steps"]):
        tutorial_id = None
        situacion_id = None
        if paso.get("moduleId") and paso.get("lessonId"):
            tutorial_id = tutorial_id_por_clave.get((paso["moduleId"], paso["lessonId"]))
        elif paso.get("situationId"):
            situacion_id = situacion_id_por_slug.get(paso["situationId"])
        db.session.add(PasoIntroductorio(
            tema_id=tema.id,
            orden=orden,
            titulo=paso["title"],
            descripcion=paso.get("description"),
            tutorial_id=tutorial_id,
            situacion_id=situacion_id,
        ))

    reasignar_datos_de_usuarios(estado_usuarios, tema)
    db.session.commit()

    print(f"Tema '{tema.nombre}' importado: "
          f"{len(datos['MODULES'])} módulos, "
          f"{sum(len(m['lessons']) for m in datos['MODULES'])} tutoriales, "
          f"{len(datos['GLOSSARY'])} términos de glosario, "
          f"{len(datos['SITUATIONS'])} situaciones, "
          f"{len(datos['TASKS'])} tareas.")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        importar()
