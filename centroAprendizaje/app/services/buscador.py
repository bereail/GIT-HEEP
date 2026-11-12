"""Buscador y chatbot local del portal.

Es un puerto fiel del algoritmo ya probado en
`timboDocumentacion/timbo-capacitacion/assets/js/search.js` y `chatbot.js`:
búsqueda por coincidencia de palabras sobre un índice en memoria, sin IA
externa, sin costo y sin conexión a internet. La única diferencia es que el
índice ahora se construye por tema a partir de la base de datos en vez de un
único archivo `content.js` fijo — así cada tema tiene su propio buscador y
las respuestas nunca se mezclan entre sistemas distintos.
"""

import re
import unicodedata

from flask import url_for
from markupsafe import escape

from app.models import Categoria, EntradaGlosario, Situacion, Tarea, Tutorial

# Palabras muy frecuentes en preguntas en lenguaje natural ("¿Qué es el
# CIE-10?") que no aportan nada para encontrar el resultado correcto, pero
# que al ser cortas aparecen "de casualidad" dentro de muchos textos y
# pueden ganarle el ranking a la palabra realmente específica de la consulta.
PALABRAS_VACIAS = {
    "que", "qué", "es", "el", "la", "los", "las", "un", "una", "unos", "unas",
    "de", "del", "en", "con", "para", "por", "como", "cómo", "donde", "dónde",
    "cual", "cuál", "cuales", "cuáles", "y", "o", "a", "se", "mi", "tu", "su",
    "al", "lo", "le", "les", "me", "te", "nos", "sobre", "hay",
    "sin", "mas", "más", "ya", "pero", "si", "no", "ni", "muy", "esta", "está",
}

_PUNTUACION = re.compile(r"[¿?¡!.,;:\"'()]")


def normalizar(texto):
    if not texto:
        return ""
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = _PUNTUACION.sub("", texto)
    return texto


def _url_tutorial(tutorial: Tutorial):
    return url_for(
        "ui.ver_tutorial",
        tema_slug=tutorial.categoria.tema.slug,
        categoria_slug=tutorial.categoria.slug,
        tutorial_slug=tutorial.slug,
    )


def construir_indice(tema):
    """Arma el índice de búsqueda para un único tema. Nunca mezcla contenido
    de otro tema."""
    entradas = []

    for tarea in tema.tareas:
        entradas.append({
            "kind": "Tarea",
            "title": tarea.pregunta,
            "subtitle": tarea.tutorial.titulo,
            "url": _url_tutorial(tarea.tutorial),
            "texto": normalizar(f"{tarea.pregunta} {tarea.tutorial.titulo} {' '.join(tarea.keywords or [])}"),
            "peso": 3,
            "ref": tarea,
        })

    for situacion in tema.situaciones:
        texto_busqueda = " ".join(filter(None, [
            situacion.situacion, situacion.descripcion, situacion.causa,
            situacion.solucion, situacion.categoria_libre,
        ]))
        entradas.append({
            "kind": "Problema",
            "title": situacion.situacion,
            "subtitle": situacion.descripcion,
            "url": url_for("ui.ver_problemas", tema_slug=tema.slug),
            "texto": normalizar(texto_busqueda),
            "peso": 2,
            "ref": situacion,
        })

    for categoria in tema.categorias:
        entradas.append({
            "kind": "Modulo",
            "title": categoria.titulo,
            "subtitle": categoria.resumen,
            "url": url_for("ui.ver_categoria", tema_slug=tema.slug, categoria_slug=categoria.slug),
            "texto": normalizar(f"{categoria.titulo} {categoria.resumen}"),
            "peso": 1.5,
            "ref": categoria,
        })
        for tutorial in categoria.tutoriales:
            entradas.append({
                "kind": "Leccion",
                "title": tutorial.titulo,
                "subtitle": categoria.titulo,
                "url": _url_tutorial(tutorial),
                "texto": normalizar(f"{tutorial.titulo} {categoria.titulo}"),
                "peso": 2,
                "ref": tutorial,
            })

    for termino in tema.entradas_glosario:
        entradas.append({
            "kind": "Glosario",
            "title": termino.termino,
            "subtitle": termino.definicion,
            "url": url_for("ui.ver_glosario", tema_slug=tema.slug),
            "texto": normalizar(f"{termino.termino} {termino.definicion}"),
            "peso": 1,
            "ref": termino,
        })

    return entradas


def construir_indice_global(temas):
    """Índice combinado de varios temas para el buscador global del portal
    (fuera de un tema puntual). Cada entrada conserva el nombre e ícono de
    su tema de origen para mostrarlo junto al resultado."""
    indice = []
    for tema in temas:
        for entrada in construir_indice(tema):
            entrada = dict(entrada, tema_nombre=tema.nombre, tema_icono=tema.icono)
            indice.append(entrada)
    return indice


def _variantes(palabra):
    """La palabra tal cual, más su forma singular aproximada — para que
    "expedientes" encuentre contenido escrito solo en singular
    ("expediente") y viceversa no haga falta, porque la búsqueda ya es por
    substring."""
    variantes = {palabra}
    if palabra.endswith("es") and len(palabra) > 4:
        variantes.add(palabra[:-2])
    elif palabra.endswith("s") and len(palabra) > 3:
        variantes.add(palabra[:-1])
    return variantes


def buscar(indice, consulta, limite=12):
    q = normalizar(consulta).strip()
    if not q:
        return []
    todas_las_palabras = [p for p in q.split() if p]
    palabras_especificas = [p for p in todas_las_palabras if p not in PALABRAS_VACIAS]
    # Si la consulta es solo palabras vacías ("qué es"), mejor buscar con
    # todo antes que no encontrar nada.
    palabras = palabras_especificas if palabras_especificas else todas_las_palabras

    resultados = []
    for entrada in indice:
        score = 0
        for palabra in palabras:
            if any(variante in entrada["texto"] for variante in _variantes(palabra)):
                score += 2 if entrada["texto"].startswith(palabra) else 1
        if score > 0:
            resultados.append((score * entrada["peso"], entrada))

    resultados.sort(key=lambda par: par[0], reverse=True)
    return [entrada for _, entrada in resultados[:limite]]


def primer_bloque_de_texto(tutorial: Tutorial):
    for bloque in tutorial.bloques or []:
        if bloque.get("type") == "text":
            return bloque.get("text", "")
    return ""


def armar_respuesta_chatbot(entrada):
    """Misma lógica que `armarRespuesta` en chatbot.js, pero con las
    entidades reales en `entrada['ref']` en vez de volver a buscarlas por
    título (más simple y sin ambigüedad si dos entradas tienen el mismo
    texto)."""
    kind = entrada["kind"]
    ref = entrada["ref"]

    if kind == "Problema":
        situacion: Situacion = ref
        html = f"<b>{escape(situacion.situacion)}</b><br>{escape(situacion.solucion)}"
        if situacion.tutorial_id:
            return {
                "html": html,
                "url": _url_tutorial(situacion.tutorial),
                "link_texto": "Ver el procedimiento completo →",
            }
        return {
            "html": html,
            "url": url_for("ui.ver_problemas", tema_slug=situacion.tema.slug),
            "link_texto": 'Ver en "Tengo un problema" →',
        }

    if kind == "Glosario":
        termino: EntradaGlosario = ref
        return {
            "html": f"<b>{escape(termino.termino)}:</b> {escape(termino.definicion)}",
            "url": url_for("ui.ver_glosario", tema_slug=termino.tema.slug),
            "link_texto": "Ver en el Glosario →",
        }

    if kind == "Tarea":
        tarea: Tarea = ref
        return {
            "html": f"Para eso, mirá la lección <b>{escape(tarea.tutorial.titulo)}</b> ({tarea.tutorial.minutos} min).",
            "url": _url_tutorial(tarea.tutorial),
            "link_texto": "Ir a la lección →",
        }

    if kind == "Leccion":
        tutorial: Tutorial = ref
        resumen = primer_bloque_de_texto(tutorial)
        html = f"<b>{escape(tutorial.titulo)}</b>"
        if resumen:
            html += f"<br>{escape(resumen)}"
        return {
            "html": html,
            "url": _url_tutorial(tutorial),
            "link_texto": "Ir a la lección →",
        }

    # Módulo u otro tipo genérico
    categoria: Categoria = ref
    html = f"<b>{escape(categoria.titulo)}</b>"
    if categoria.resumen:
        html += f"<br>{escape(categoria.resumen)}"
    return {
        "html": html,
        "url": entrada["url"],
        "link_texto": "Ir →",
    }
