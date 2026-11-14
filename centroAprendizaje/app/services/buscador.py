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
    "quien", "quién",
}

# Cómo dice la gente las cosas → cómo están escritas en el contenido. Solo
# se usan si la palabra original no aparece en ningún lado.
SINONIMOS = {
    "licitacion": "proceso", "licitaciones": "proceso", "licitar": "proceso",
    "insumo": "articulo", "insumos": "articulo", "producto": "articulo", "productos": "articulo",
    "tcp": "tribunal", "contrasena": "clave", "password": "clave",
    "ayuda": "mesa de ayuda", "telefono": "mesa de ayuda", "contacto": "mesa de ayuda",
    "comprar": "compra", "compramos": "compra",
    "hablo": "hablar", "llamo": "llamar", "escribo": "escribir", "archivar": "archivo",
}

_PIDE_DEFINICION = re.compile(r"^(que es|que son|que significa|que quiere decir)(?: |$)")
_ARTICULOS = re.compile(r"^(?:(?:el|la|los|las|un|una|lo)\s+)*")

# Palabras de "pedir un artículo" que no son el artículo en sí: no cuentan
# para decidir si la pregunta es por un artículo del Nomenclador.
_PALABRAS_DE_PEDIDO = {
    "compra", "comprar", "pedir", "pido", "busco", "buscar", "conseguir", "encuentro",
    "encontrar", "articulo", "articulos", "nombre", "codigo", "catalogo", "timbo",
}

# Cuánto vale cada palabra según cómo aparece: entera ("pase" en "hacer un
# pase") vale más que al principio de otra ("expediente" en "expedientes"),
# y mucho más que perdida adentro de otra ("sin" en "sistema").
_VALOR_ENTERA = 1.5
_VALOR_PREFIJO = 1
_VALOR_ADENTRO = 0.3

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
            # Las palabras clave están elegidas a mano: cuentan como título.
            "claves": normalizar(f"{tarea.pregunta} {' '.join(tarea.keywords or [])}"),
            "frases": [normalizar(k) for k in (tarea.keywords or []) if " " in k.strip()],
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
                "como se llama como busco como pido un articulo "
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


def _valor_en(texto, palabra):
    """Cuánto vale `palabra` (o su singular) en `texto`: entera, al principio
    de otra palabra, adentro de otra, o nada."""
    mejor = 0
    for variante in _variantes(palabra):
        if variante not in texto:
            continue
        if re.search(r"\b" + re.escape(variante) + r"\b", texto):
            return _VALOR_ENTERA
        if re.search(r"\b" + re.escape(variante), texto):
            mejor = max(mejor, _VALOR_PREFIJO)
        else:
            mejor = max(mejor, _VALOR_ADENTRO)
    return mejor


def buscar_con_puntaje(indice, consulta, limite=12, ignorar=(), premiar_titulo_exacto=True):
    """Devuelve pares (puntaje, entrada), para que el chatbot pueda
    distinguir una coincidencia clara de una adivinanza. `ignorar`: palabras
    que no aportan en este índice (el nombre del propio sistema: "timbo"
    aparece en todo el contenido de TIMBÓ). `premiar_titulo_exacto`: apagarlo
    al comparar con otros temas, para que "documento embebido" no se vaya a
    otro sistema solo porque allá hay un término con ese nombre exacto."""
    q = normalizar(consulta).strip()
    if not q:
        return []
    todas_las_palabras = [p for p in q.split() if p]
    palabras_especificas = [p for p in todas_las_palabras if p not in PALABRAS_VACIAS]
    if any(p not in ignorar for p in palabras_especificas):
        palabras_especificas = [p for p in palabras_especificas if p not in ignorar]
    # Si la consulta es solo palabras vacías ("qué es"), mejor buscar con
    # todo antes que no encontrar nada.
    palabras = palabras_especificas if palabras_especificas else todas_las_palabras
    originales = set(palabras)
    palabras = _corregir_palabras(indice, palabras)
    # "¿Qué es X?" pide una definición: el glosario tiene que ganarle a la
    # lección que menciona el término.
    definicion = _PIDE_DEFINICION.match(q)
    pide_definicion = bool(definicion)
    termino_pedido = _ARTICULOS.sub("", q[definicion.end():].strip()) if definicion else ""
    if termino_pedido and not palabras_especificas:
        # "¿Qué es el SIN?": "sin" es palabra vacía, pero acá es lo que se pregunta.
        palabras = termino_pedido.split()
    palabras_de_articulo = [p for p in palabras if p not in _PALABRAS_DE_PEDIDO]

    resultados = []
    for entrada in indice:
        texto = entrada["texto"]
        titulo = normalizar(entrada["title"])
        claves = entrada.get("claves", titulo)
        score = 0
        encontradas = set()
        for palabra in palabras:
            valor = _valor_en(texto, palabra)
            if not valor:
                continue
            encontradas.add(palabra)
            score += valor
            if texto.startswith(palabra):
                score += 1
            if _valor_en(claves, palabra) >= _VALOR_PREFIJO:
                score += 1
        # Una palabra clave de varias palabras ("archivo un expediente",
        # "no puedo entrar") que aparece entera en la pregunta es la señal
        # más clara de qué se quiere.
        for frase in entrada.get("frases", ()):
            if re.search(r"\b" + re.escape(frase) + r"\b", q):
                score += 3
        if entrada["kind"] == "Nomenclador" and not set(palabras_de_articulo) <= encontradas:
            # Un artículo responde solo si coincide todo lo que no es "pedir":
            # "se cayó el sistema" no es una pregunta por un "Sistema de aspiración".
            continue
        if entrada["kind"] == "Nomenclador" and palabras_de_articulo and set(palabras_de_articulo) <= originales:
            # Coincide el artículo completo: es justo lo que se busca
            # ("quiero comprar guantes" → los guantes, no "cómo hacer una compra").
            # No si la palabra vino de corregir un error de tipeo ("receta" → "recta").
            score += 3
        # El término puede estar al principio ("SIN") o como sigla al final
        # ("Sistema de Información Normativa (SIN)").
        termino = re.escape(termino_pedido)
        if termino_pedido and entrada["kind"] == "Glosario" and (
            re.match(termino + r"\b", titulo) or re.search(r"\b" + termino + "$", titulo)
        ):
            score += 10
        if score > 0:
            # Una sugerencia del chatbot manda el título exacto: tiene que
            # ganar siempre, aunque otra entrada comparta más palabras.
            if premiar_titulo_exacto and titulo == q:
                score += 100
            peso = entrada["peso"]
            if pide_definicion and entrada["kind"] == "Glosario":
                peso *= 4
            resultados.append((score * peso, entrada))

    resultados.sort(key=lambda par: par[0], reverse=True)
    return resultados[:limite]


def buscar(indice, consulta, limite=12):
    return [entrada for _, entrada in buscar_con_puntaje(indice, consulta, limite)]


_CHARLA = [
    (re.compile(r"^(hola|buen dia|buenos dias|buenas tardes|buenas noches|buenas|hey|que tal)\b"),
     "¡Hola! Contame tu duda con tus palabras, o tocá una de estas:"),
    (re.compile(r"^(gracias|muchas gracias|mil gracias|genial|perfecto|buenisimo|joya|ok|dale|listo)\b"),
     "¡De nada! Si tenés otra duda, escribila acá abajo."),
    (re.compile(r"^(chau|adios|hasta luego|nos vemos)\b"),
     "¡Chau! Cuando necesites, acá estoy."),
]


def respuesta_de_charla(consulta):
    """Saludos y agradecimientos cortos: se responden amablemente en vez de
    buscarlos en el contenido. Si después del saludo viene una pregunta
    ("hola, cómo hago un pase"), no es charla."""
    q = normalizar(consulta).strip()
    if not q or len(q.split()) > 4:
        return None
    for patron, respuesta in _CHARLA:
        if patron.match(q):
            return respuesta
    return None


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


def _video_html(tutorial: Tutorial):
    """Link al video oficial más corto de la lección, para verlo sin buscarlo."""
    videos = [b for b in (tutorial.bloques or []) if b.get("type") == "video" and b.get("url")]
    if not videos:
        return ""
    video = min(videos, key=lambda b: b.get("minutos") or 999)
    minutos = f" ({video['minutos']} min)" if video.get("minutos") else ""
    return (
        f'<a class="chatbot-msg__video" href="{escape(video["url"])}" target="_blank" rel="noopener">'
        f"▶ Ver el video oficial{minutos}</a>"
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
        html += _pasos_html(tarea.tutorial) + _video_html(tarea.tutorial)
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
        html += _pasos_html(tutorial) + _video_html(tutorial)
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
