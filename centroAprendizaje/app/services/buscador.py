"""Buscador y chatbot local del portal.

Es un puerto fiel del algoritmo ya probado en
`timboDocumentacion/timbo-capacitacion/assets/js/search.js` y `chatbot.js`:
búsqueda por coincidencia de palabras sobre un índice en memoria, sin IA
externa, sin costo y sin conexión a internet. La única diferencia es que el
índice ahora se construye por tema a partir de la base de datos en vez de un
único archivo `content.js` fijo — así cada tema tiene su propio buscador y
las respuestas nunca se mezclan entre sistemas distintos.
"""

import difflib
import re
import unicodedata

from flask import url_for
from markupsafe import escape

from app.models import Categoria, EntradaGlosario, EquivalenciaArticulo, Situacion, Tarea, Tutorial

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

# Cómo dice la gente las cosas → cómo están escritas en el contenido. Solo
# se usan si la palabra original no aparece en ningún lado.
SINONIMOS = {
    "licitacion": "proceso", "licitaciones": "proceso", "licitar": "proceso",
    "insumo": "articulo", "insumos": "articulo", "producto": "articulo", "productos": "articulo",
    "tcp": "tribunal", "contrasena": "clave", "password": "clave",
    "ayuda": "mesa de ayuda", "telefono": "mesa de ayuda", "contacto": "mesa de ayuda",
    "comprar": "compra", "compramos": "compra",
}

_PIDE_DEFINICION = re.compile(r"^(que es|que son|que significa|que quiere decir)(?: |$)")

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

    if tema.equivalencias_articulos:
        # Entrada sintetica con peso alto para preguntas en lenguaje natural
        # sobre el Nomenclador en si ("no encuentro el articulo", "como pido
        # un articulo nuevo"). Sin esto, esas consultas no matchean ningun
        # nombre de articulo puntual y terminan ganando por una entrada de
        # Glosario sin relacion (ej. SIPAF, que menciona "articulos" de paso).
        entradas.append({
            "kind": "NomencladorAyuda",
            "title": "No encuentro un artículo / ¿qué nombre usa TIMBÓ?",
            "subtitle": "Nomenclador de artículos",
            "url": url_for("ui.ver_equivalencias", tema_slug=tema.slug),
            "texto": normalizar(
                "no encuentro el articulo no aparece no esta el articulo en el catalogo "
                "como se llama como busco como pido un articulo en timbo "
                "nombre correcto del articulo nomenclador equivalencia codigo "
                "pedir alta de un articulo articulo nuevo falta un articulo que no esta"
            ),
            "peso": 4,
            "ref": tema,
        })

    for equivalencia in tema.equivalencias_articulos:
        # Solo nombre/bien/item especifico: las notas son texto libre largo
        # y meterlas ensuciaria el ranking con coincidencias de palabras
        # sueltas sin relacion real con lo que se busca.
        texto = " ".join(filter(None, [
            equivalencia.nombre_interno, equivalencia.bien_o_servicio, equivalencia.item_especifico,
        ]))
        entradas.append({
            "kind": "Nomenclador",
            "title": equivalencia.nombre_interno,
            "subtitle": equivalencia.bien_o_servicio or "Todavía no se encontró en el catálogo oficial",
            "url": url_for("ui.ver_equivalencias", tema_slug=tema.slug),
            "texto": normalizar(texto),
            "peso": 1.5,
            "ref": equivalencia,
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


def _vocabulario(indice):
    return {p for entrada in indice for p in entrada["texto"].split() if len(p) >= 4}


def _corregir_palabras(indice, palabras):
    """Para cada palabra que no aparece en ningún lado: primero prueba un
    sinónimo y, si no, la palabra del contenido más parecida (errores de
    tipeo como "ofetar" o "inpugnar")."""
    textos = [entrada["texto"] for entrada in indice]
    vocabulario = None
    corregidas = []
    for palabra in palabras:
        if any(v in t for t in textos for v in _variantes(palabra)):
            corregidas.append(palabra)
            continue
        if palabra in SINONIMOS:
            corregidas.append(SINONIMOS[palabra])
            continue
        if len(palabra) >= 4:
            if vocabulario is None:
                vocabulario = _vocabulario(indice)
            parecidas = difflib.get_close_matches(palabra, vocabulario, n=1, cutoff=0.8)
            if parecidas:
                corregidas.append(parecidas[0])
                continue
        corregidas.append(palabra)
    return corregidas


def buscar_con_puntaje(indice, consulta, limite=12):
    """Devuelve pares (puntaje, entrada), para que el chatbot pueda
    distinguir una coincidencia clara de una adivinanza."""
    q = normalizar(consulta).strip()
    if not q:
        return []
    todas_las_palabras = [p for p in q.split() if p]
    palabras_especificas = [p for p in todas_las_palabras if p not in PALABRAS_VACIAS]
    # Si la consulta es solo palabras vacías ("qué es"), mejor buscar con
    # todo antes que no encontrar nada.
    palabras = palabras_especificas if palabras_especificas else todas_las_palabras
    palabras = _corregir_palabras(indice, palabras)
    # "¿Qué es X?" pide una definición: el glosario tiene que ganarle a la
    # lección que menciona el término.
    pide_definicion = bool(_PIDE_DEFINICION.match(q))

    resultados = []
    for entrada in indice:
        texto = entrada["texto"]
        titulo = normalizar(entrada["title"])
        score = 0
        for palabra in palabras:
            if any(variante in texto for variante in _variantes(palabra)):
                score += 2 if texto.startswith(palabra) else 1
                if palabra in titulo:
                    score += 1
                # Desempata a favor de la palabra entera: "adjudico" tiene
                # que preferir "adjudico" antes que "preadjudico".
                if re.search(r"\b" + re.escape(palabra) + r"\b", texto):
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
    "Quiero hacer..." y mitad "Tengo un problema"."""
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


def _pasos_html(tutorial: Tutorial):
    """Los pasos de la lección, plegados, para resolver sin salir del chat."""
    pasos = [b.get("explanation", "") for b in (tutorial.bloques or []) if b.get("type") == "step"]
    pasos = [p for p in pasos if p]
    if len(pasos) < 2:
        return ""
    items = "".join(f"<li>{escape(p)}</li>" for p in pasos)
    return (
        f'<details class="chatbot-msg__mas"><summary>Ver los {len(pasos)} pasos</summary>'
        f'<ol class="chatbot-msg__pasos">{items}</ol></details>'
    )


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
        html += _pasos_html(tarea.tutorial)
        return {
            "html": html,
            "url": _url_tutorial(tarea.tutorial),
            "link_texto": f"Ver el paso a paso ({tarea.tutorial.minutos} min) →",
        }

    if kind == "NomencladorAyuda":
        return {
            "html": (
                "<b>¿No encontrás un artículo?</b><br>"
                "Buscalo en el Nomenclador: te decimos con qué nombre pedirlo en TIMBÓ "
                "o, si todavía no está en el catálogo, cómo solicitar que lo agreguen."
            ),
            "url": entrada["url"],
            "link_texto": "Ir al Nomenclador de artículos →",
        }

    if kind == "Nomenclador":
        equivalencia: EquivalenciaArticulo = ref
        html = f"<b>{escape(equivalencia.nombre_interno)}</b>"
        if equivalencia.confianza == "sin_match":
            html += "<br>Todavía no está en el catálogo oficial — hay que pedir que lo agreguen."
        else:
            partes = " — ".join(filter(None, [equivalencia.bien_o_servicio, equivalencia.item_especifico]))
            html += f"<br>Buscalo en TIMBÓ como: {escape(partes)}"
            if equivalencia.codigo_catalogo:
                html += f" <code>{escape(equivalencia.codigo_catalogo)}</code>"
            if equivalencia.confianza == "dudosa":
                html += "<br><small>Es lo más parecido que encontramos, confirmá antes de usarlo.</small>"
        return {
            "html": html,
            "url": url_for("ui.ver_equivalencias", tema_slug=equivalencia.tema.slug),
            "link_texto": "Ver en el Nomenclador de artículos →",
        }

    if kind == "Leccion":
        tutorial: Tutorial = ref
        resumen = primer_bloque_de_texto(tutorial)
        html = f"<b>{escape(tutorial.titulo)}</b>"
        if resumen:
            html += f"<br>{escape(resumen)}"
        html += _pasos_html(tutorial)
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
