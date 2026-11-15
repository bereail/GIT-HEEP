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
        terminos.append({
            "termino": t["termino"], "categoria": t.get("tema") or "Del portal (sin revisar)", "sencilla": t["definicion"],
            "tecnica": "", "ejemplo": "", "modulo": t["modulo"], "estado": "pendiente", "fuentes": [],
            "nota": "Del glosario del tema. Todavía no tiene la fuente oficial revisada.",
        })
    terminos.sort(key=lambda t: _clave_orden(t["termino"]))
    categorias = datos["categorias"] + sorted({t["categoria"] for t in terminos} - set(datos["categorias"]))
    return {"terminos": terminos, "categorias": categorias}


@lru_cache(maxsize=None)
def capacitacion():
    return _leer("capacitacion.json")


ARCHIVOS = os.path.join(CARPETA, "archivos")


@lru_cache(maxsize=None)
def algoritmo():
    return _leer("algoritmo.json")


def docs_minimos():
    """Lo justo de cada documento para citar fuentes desde JavaScript."""
    return {d["id"]: {"titulo": d["titulo"], "url": d["url"], "vigencia": d.get("vigencia", "")} for d in biblioteca()["documentos"]}


# Herramientas prácticas: clave en la URL → (sección del JSON, ícono, título corto).
HERRAMIENTAS = {
    "plazos": ("plazos", "🗓️", "Plazos"),
    "a-quien-preguntar": ("a_quien", "🧭", "¿A quién le pregunto?"),
    "modelos": ("modelos", "✉️", "Modelos de mensajes"),
    "checklists": ("checklists", "✅", "Checklists"),
    "estados": ("estados", "🚦", "Estados del proceso"),
}


@lru_cache(maxsize=None)
def herramientas():
    return _leer("herramientas.json")
