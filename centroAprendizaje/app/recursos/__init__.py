"""Recursos de consulta (roles, glosario, biblioteca, circuito).

Viven en archivos JSON de esta carpeta, aparte del contenido público de la
base: hoy solo se ven en /admin (borrador para revisar). Cada dato lleva un
estado de verificación y las fuentes oficiales por id de la biblioteca.
"""

import json
import os
import unicodedata
from functools import lru_cache

CARPETA = os.path.dirname(__file__)

ESTADOS = {
    "confirmado": ("✅", "Confirmado", "Lo dice una fuente oficial"),
    "didactico": ("📘", "Didáctico", "Explicación nuestra a partir de lo confirmado"),
    "practica": ("💬", "Práctica informada", "Lo informó soporte; no es norma"),
    "pendiente": ("⏳", "Pendiente", "No hay fuente oficial que lo diga"),
    "discrepancia": ("⚠️", "Discrepancia", "Dos fuentes oficiales dicen cosas distintas"),
}


def _leer(nombre):
    with open(os.path.join(CARPETA, nombre), encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=None)
def biblioteca():
    return _leer("biblioteca.json")


@lru_cache(maxsize=None)
def roles():
    return _leer("roles.json")


@lru_cache(maxsize=None)
def circuito():
    return _leer("circuito.json")


def documentos_por_id():
    return {d["id"]: d for d in biblioteca()["documentos"]}


def _clave_orden(texto):
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sin_tildes.lower()


def glosario_completo():
    """Glosario curado más el de todos los temas del sitio (incluido miHospital)."""
    from app.models import Tema

    del_portal = [
        {"termino": e.termino, "definicion": e.definicion, "modulo": t.nombre + (f" · {e.modulo}" if e.modulo else ""), "tema": t.nombre}
        for t in Tema.query.filter_by(activo=True).order_by(Tema.orden).all() for e in t.entradas_glosario
    ]
    return glosario(del_portal)


def glosario(terminos_del_portal=()):
    """Términos curados (con fuente) más los del glosario público, que quedan
    como pendientes de trazabilidad hasta revisarlos uno por uno."""
    datos = _leer("glosario.json")
    terminos = list(datos["terminos"])
    vistos = {_clave_orden(t["termino"]).split(" (")[0] for t in terminos}
    for t in terminos_del_portal:
        clave = _clave_orden(t["termino"]).split(" (")[0]
        if clave in vistos:
            continue
        vistos.add(clave)
        del_manual = t.get("tema") == "miHospital"  # el manual de miHospital es fuente oficial
        terminos.append({
            "termino": t["termino"], "categoria": t.get("tema") or "Del portal (sin revisar)", "sencilla": t["definicion"],
            "tecnica": "", "ejemplo": "", "modulo": t["modulo"], "estado": "confirmado" if del_manual else "pendiente",
            "fuentes": [],
            "nota": "Del manual de miHospital." if del_manual else "Del glosario del tema. Todavía no tiene la fuente oficial revisada.",
        })
    terminos.sort(key=lambda t: _clave_orden(t["termino"]))
    for t in terminos:
        # Letra del índice sin tilde: "Área" va con la A.
        t["letra"] = next((c for c in _clave_orden(t["termino"]) if c.isalnum()), "#").upper()
    categorias = datos["categorias"] + sorted({t["categoria"] for t in terminos} - set(datos["categorias"]))
    return {"terminos": terminos, "categorias": categorias}


@lru_cache(maxsize=None)
def capacitacion():
    return _leer("capacitacion.json")


ARCHIVOS = os.path.join(CARPETA, "archivos")


def curso_admin_local():
    # Copia del curso de Administrador Local de Timbó del Aula Virtual (solo
    # en /admin). Los PDF están en archivos/admin-local y se bajan con sesión.
    return _leer("curso_admin_local.json")


@lru_cache(maxsize=None)
def algoritmo():
    return _leer("algoritmo.json")


def docs_minimos():
    """Lo justo de cada documento para citar fuentes desde JavaScript."""
    return {d["id"]: {"titulo": d["titulo"], "url": d["url"], "vigencia": d.get("vigencia", "")} for d in biblioteca()["documentos"]}


# Herramientas prácticas: clave en la URL → (sección del JSON, ícono, título corto).
def topes():
    """Frases que, al pasar el mouse, muestran el tope de la Circular SCyGB
    01/2026. Salen de la misma tabla que la página "Montos y topes"."""
    filas = {f["que"]: f["monto"] for f in herramientas()["montos"]["encuadre"]}
    fuente = "Circular SCyGB N° 01/2026"
    return [
        {"frases": ["monto menor al tope", "gestión directa por monto", "compra directa por monto",
                    "contratación directa por monto", "directa por monto"],
         "texto": f"Contratación directa por monto: {filas['Contratación directa por monto'].lower()} en 2026 ({fuente})."},
        {"frases": ["licitación o concurso privado", "licitaciones privadas", "licitación privada", "concurso privado"],
         "texto": f"Licitación o concurso privado: {filas['Licitación o concurso privado'].lower()} en 2026 ({fuente})."},
        {"frases": ["licitación o concurso público", "licitaciones públicas", "licitación pública", "concurso público"],
         "texto": f"Licitación o concurso público: {filas['Licitación o concurso público'].lower()} en 2026 ({fuente})."},
        {"frases": ["concurso de precios"],
         "texto": f"Concurso de precios para locación de inmuebles: "
                  f"{filas['Concurso de precios para locación de inmuebles (art. 140, punto 2, Ley 12.510)'].lower()} en 2026 ({fuente})."},
    ]


def enlaces_oficiales():
    """Formularios y documentos que, al nombrarse en el sitio, se vuelven un
    link oficial (regla de la usuaria: todo formulario con su link)."""
    docs = documentos_por_id()
    timbo = "https://tramites.santafe.gob.ar/"
    return [
        {"frases": ["Timbó Compras: Alta de bienes y servicios CAByS", "Formulario Timbo Compras (CAByS)", "formulario CAByS"],
         "url": timbo,
         "texto": "Se crea dentro de TIMBÓ: Documentos oficiales → Nuevo Documento Oficial → tipo \"Timbó Compras: Alta de bienes y servicios CAByS\" (Res. SCyGB 292/2026). Tocá para entrar a TIMBÓ."},
        {"frases": ["CD-01", "CD-02", "CD-03", "CD-04", "CD01", "CD02", "CD03", "CD04"],
         "url": timbo,
         "texto": "Formulario de compra directa: se crea dentro de TIMBÓ, en Documentos oficiales (video oficial \"Compras Directas\"). Tocá para entrar a TIMBÓ."},
        {"frases": ["Pliego Único de Bases y Condiciones Generales", "Pliego Único"],
         "url": docs["pliego-unico-2026"]["url"],
         "texto": "Pliego Único de Bases y Condiciones Generales (anexo del Dec. 287/2026). Tocá para abrir el PDF oficial."},
    ]


def revisado_al():
    """Fecha en que se consultó la normativa oficial, como dd/mm/aaaa."""
    a, m, d = biblioteca()["consultado"].split("-")
    return f"{d}/{m}/{a}"


# Ocultos por ahora en el sitio público (pedido del 16/11/2026); en /admin siguen.
OCULTOS_PUBLICO = frozenset({"simulador", "checklists"})

# En el sitio público solo va lo verificado contra documentación oficial
# (regla de la usuaria, 16/11/2026). Una discrepancia se muestra porque las
# dos fuentes son oficiales; lo pendiente, didáctico o "de práctica" queda en /admin.
ESTADOS_PUBLICOS = frozenset({"confirmado", "discrepancia"})


def es_publico(estado):
    return estado is None or estado in ESTADOS_PUBLICOS


def glosario_publico(datos):
    """El diccionario sin términos no verificados ni ejemplos didácticos."""
    terminos = [{k: v for k, v in t.items() if k != "ejemplo"} for t in datos["terminos"] if es_publico(t.get("estado"))]
    usadas = {t["categoria"] for t in terminos}
    return {"terminos": terminos, "categorias": [c for c in datos["categorias"] if c in usadas]}


def algoritmo_publico():
    """El algoritmo sin las etapas pendientes ni los ejemplos didácticos."""
    import copy

    datos = copy.deepcopy(algoritmo())
    fuera = {i for i, n in datos["nodos"].items() if not es_publico(n.get("estado"))}
    for i in fuera:
        del datos["nodos"][i]
    for n in datos["nodos"].values():
        n.pop("opciones_ejemplo", None)
        if "pasos" in n:
            n["pasos"] = [p for p in n["pasos"] if p not in fuera]
        if "opciones" in n:
            n["opciones"] = [o for o in n["opciones"] if o.get("va") not in fuera]
        if "ficha" in n:
            n["ficha"]["fuentes"] = [f for f in n["ficha"].get("fuentes", []) if f.get("tipo") != "ejemplo"]
    for r in datos["ramas"]:
        if "nodos" in r:
            r["nodos"] = [x for x in r["nodos"] if x not in fuera]
    datos["ejemplos"] = {}
    return datos

HERRAMIENTAS = {
    "montos": ("montos", "💲", "Montos y topes 2026"),
    "plazos": ("plazos", "🗓️", "Plazos"),
    "a-quien-preguntar": ("a_quien", "🧭", "¿A quién le pregunto?"),
    "modelos": ("modelos", "✉️", "Modelos de mensajes"),
    "checklists": ("checklists", "✅", "Checklists"),
    "estados": ("estados", "🚦", "Estados del proceso"),
    "sistemas": ("sistemas", "🔀", "¿Qué se hace en cada sistema?"),
}


@lru_cache(maxsize=None)
def herramientas():
    return _leer("herramientas.json")


@lru_cache(maxsize=None)
def simulador():
    return _leer("simulador.json")


@lru_cache(maxsize=None)
def simulador_timbo():
    # Réplica de pantallas de TIMBÓ (Bandeja de trámites) relevadas el
    # 25/11/2026 + la Guía de Proceso oficial. Solo en /admin.
    return _leer("simulador_timbo.json")


@lru_cache(maxsize=None)
def curso_timbo():
    # Copia del curso oficial «Timbó, paso a paso» del Aula Virtual (texto,
    # PDF y preguntas tal cual); los PDF están en static/docs/timbo-paso-a-paso.
    return _leer("curso_timbo.json")


def indice_busqueda():
    """Entradas de Recursos para el buscador global del portal: páginas,
    preguntas de "Explicame", términos del diccionario y normativa."""
    from flask import url_for

    from app.services.buscador import normalizar

    def entrada(kind, titulo, subtitulo, url, texto, peso):
        return {"kind": kind, "title": titulo, "subtitle": subtitulo, "url": url, "texto": normalizar(texto),
                "peso": peso, "ref": None, "tema_nombre": "Recursos", "tema_icono": "📚"}

    paginas = [
        ("Roles: quién hace qué", "recursos_roles", {}, "roles gestor supervisor evaluador permisos usuario rol quien hace que"),
        ("Diccionario de Compras Públicas", "recursos_glosario", {}, "diccionario glosario terminos siglas significado"),
        ("Normativa y fuentes oficiales", "recursos_biblioteca", {}, "normativa biblioteca circulares resoluciones decretos leyes fuentes"),
        ("¿Qué camino sigue una compra?", "recursos_algoritmo", {}, "algoritmo camino circuito procedimiento diagrama etapas compra"),
        ("Explicame este paso", "recursos_explicame", {}, "explicame dudas preguntas frecuentes etapa"),
        ("Aprendé Compras Públicas desde cero", "recursos_aprender", {}, "aprender desde cero curso introduccion compras publicas"),
    ] + [(titulo, "recursos_herramienta", {"clave": clave}, titulo)
         for clave, (_, _, titulo) in HERRAMIENTAS.items() if clave not in OCULTOS_PUBLICO]
    indice = [entrada("Recurso", t, "", url_for("ui." + e, **kw), f"{t} {extra}", 2) for t, e, kw, extra in paginas]
    for p in capacitacion()["explicame"]:
        indice.append(entrada("Pregunta", p["q"], p["a"], url_for("ui.recursos_explicame", etapa=p["nodo"]),
                              f"{p['q']} {p['palabras']}", 2.5))
    for t in glosario_publico(glosario())["terminos"]:
        indice.append(entrada("Diccionario", t["termino"], t["sencilla"], url_for("ui.recursos_glosario", q=t["termino"]),
                              f"{t['termino']} {t['sencilla']}", 1.5))
    for d in biblioteca()["documentos"]:
        indice.append(entrada("Normativa", d["titulo"], d.get("tema", ""), url_for("ui.recursos_biblioteca"),
                              f"{d['titulo']} {d.get('tema', '')}", 1))
    return indice
