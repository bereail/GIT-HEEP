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
    # Arranques típicos de pregunta: muchas tareas empiezan con "Quiero..." o
    # "Necesito...", así que le ganaban a la palabra que importa ("comprar").
    "quiero", "quisiera", "necesito", "puedo", "hago", "tengo", "algo",
}

_PUNTUACION = re.compile(r"[¿?¡!.,;:\"'()]")
_PIDE_DEFINICION = re.compile(r"^(que es|que son|que significa|que quiere decir)(?: |$)")


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


def _raiz(palabra):
    """Raíz aproximada para que "impugnar" encuentre "impugnación" o
    "subsanar" encuentre "subsanación", sin depender de un stemmer real."""
    if len(palabra) < 6:
        return None
    return palabra[: max(5, len(palabra) - 3)]


def buscar_con_puntaje(indice, consulta, limite=12):
    """Igual que `buscar`, pero devuelve pares (puntaje, entrada) para que el
    chatbot pueda distinguir una coincidencia clara de una adivinanza."""
    q = normalizar(consulta).strip()
    if not q:
        return []
    todas_las_palabras = [p for p in q.split() if p]
    palabras_especificas = [p for p in todas_las_palabras if p not in PALABRAS_VACIAS]
    # Si la consulta es solo palabras vacías ("qué es"), mejor buscar con
    # todo antes que no encontrar nada.
    palabras = palabras_especificas if palabras_especificas else todas_las_palabras
    # "¿Qué es X?" / "¿Qué significa X?" pide una definición: el glosario
    # tiene que ganarle a la lección que menciona el término.
    pide_definicion = bool(_PIDE_DEFINICION.match(q))

    resultados = []
    for entrada in indice:
        texto = entrada["texto"]
        titulo = normalizar(entrada["title"])
        score = 0
        for palabra in palabras:
            if palabra in texto:
                score += 2 if texto.startswith(palabra) else 1
                if palabra in titulo:
                    score += 1
            else:
                raiz = _raiz(palabra)
                if raiz and raiz in texto:
                    score += 0.5
        if score > 0:
            # Una sugerencia del chatbot manda el título exacto: tiene que
            # ganar siempre, aunque otra entrada comparta más palabras.
            if titulo == q:
                score += 100
            peso = entrada["peso"]
            if pide_definicion and entrada["kind"] == "Glosario":
                peso *= 4
            resultados.append((score * peso, entrada))

    resultados.sort(key=lambda par: par[0], reverse=True)
    return resultados[:limite]


def buscar(indice, consulta, limite=12):
    return [entrada for _, entrada in buscar_con_puntaje(indice, consulta, limite)]


def sugerencias_iniciales(tema, cantidad=4):
    """Preguntas para mostrar como botones al abrir el chatbot: mitad
    "Quiero hacer..." y mitad "Tengo un problema", en el orden del tema
    (las más frecuentes se cargan primero)."""
    tareas = [t.pregunta for t in tema.tareas]
    situaciones = [s.situacion for s in tema.situaciones if s.verificado]
    mitad = cantidad // 2
    elegidas = tareas[:mitad] + situaciones[: cantidad - mitad]
    if len(elegidas) < cantidad:
        resto = [p for p in tareas[mitad:] + situaciones[cantidad - mitad:] if p not in elegidas]
        elegidas += resto[: cantidad - len(elegidas)]
    return elegidas


def primer_bloque_de_texto(tutorial: Tutorial):
    bloques = tutorial.bloques or []
    for bloque in bloques:
        if bloque.get("type") == "text":
            return bloque.get("text", "")
    # Lecciones que arrancan directo con pasos: el primer paso ya sirve de
    # resumen de por dónde empezar.
    for bloque in bloques:
        if bloque.get("type") == "step":
            return bloque.get("explanation", "")
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
        if situacion.notas_adicionales:
            html += (
                '<details class="chatbot-msg__mas"><summary>Ver más</summary>'
                f"{escape(situacion.notas_adicionales)}</details>"
            )
        if not situacion.verificado:
            html = (
                '<span class="chatbot-msg__aviso">⚠️ Respuesta sin confirmar: '
                "consultá con tu referente</span>" + html
            )
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
        resumen = primer_bloque_de_texto(tarea.tutorial)
        html = f"<b>{escape(tarea.tutorial.titulo)}</b>"
        if resumen:
            html += f"<br>{escape(resumen)}"
        return {
            "html": html,
            "url": _url_tutorial(tarea.tutorial),
            "link_texto": f"Ver el paso a paso ({tarea.tutorial.minutos} min) →",
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
            "link_texto": f"Ver el paso a paso ({tutorial.minutos} min) →",
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
