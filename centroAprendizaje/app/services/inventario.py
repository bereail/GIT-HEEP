"""Inventario de todo el material del centro, con su estado de verificación.

Se arma solo desde el contenido (base y JSON de recursos), así nunca queda
desactualizado. Cada fila tiene un `grupo` común para filtrar:
ok (verificado), parcial, revision (revisión general o didáctico) y pendiente.
"""

import json
import os
import re

from app import recursos
from app.models import Situacion, Tema

GRUPOS = {
    "ok": "✅ Verificado",
    "parcial": "🟡 Verificado en parte",
    "revision": "🔵 Revisión general",
    "pendiente": "⏳ Pendiente o sin confirmar",
}

TIPOS = {
    "leccion": "Lección",
    "video": "Video",
    "pdf": "Guía PDF",
    "documento": "Documento oficial",
    "termino": "Término del Diccionario",
    "algoritmo": "Paso del algoritmo",
    "pregunta": "Respuesta del asistente",
}

_ESTADO_LECCION = {
    "verificada": ("ok", "Verificada frase por frase"),
    "parcial": ("parcial", "Normativa verificada; falta la pantalla"),
    "revision-general": ("revision", "Revisión general"),
    "indice": ("ok", "Índice de fuentes oficiales"),
}

_ESTADO_RECURSO = {
    "confirmado": "ok",
    "didactico": "revision",
    "practica": "pendiente",
    "pendiente": "pendiente",
    "discrepancia": "parcial",
}

_ID_YOUTUBE = re.compile(r"(?:youtu\.be/|v=|embed/)([\w-]{11})")


def _leer_inventario():
    with open(os.path.join(recursos.CARPETA, "inventario.json"), encoding="utf-8") as f:
        return json.load(f)


def _grupo_lectura(lectura):
    lectura = (lectura or "").lower()
    if lectura.startswith(("completa", "texto completo", "subtítulos completos", "circular completa")):
        return "ok"
    if lectura.startswith(("no se pudo", "solo la descripción", "identificados")):
        return "pendiente"
    return "parcial"


def filas():
    datos = _leer_inventario()
    leidos = set(datos.get("videos_leidos", []))
    salida = []

    for tema in Tema.query.order_by(Tema.orden).all():
        por_tema = datos["temas"].get(tema.slug, {})
        propias = datos["lecciones"].get(tema.slug, {})
        for cat in tema.categorias:
            for tut in cat.tutoriales:
                reg = propias.get(tut.slug) or por_tema
                grupo, etiqueta = _ESTADO_LECCION.get(reg.get("estado"), ("pendiente", "Sin registro de verificación"))
                enlace = f"/temas/{tema.slug}/{cat.slug}/{tut.slug}"
                salida.append({
                    "tipo": "leccion", "tema": tema.nombre, "grupo_contenido": cat.titulo, "titulo": tut.titulo,
                    "estado": etiqueta, "grupo": grupo, "fecha": reg.get("fecha", ""), "detalle": reg.get("nota", ""),
                    "enlace": enlace, "fuente": "",
                })
                for b in tut.bloques or []:
                    if b.get("type") == "video" and b.get("url"):
                        m = _ID_YOUTUBE.search(b["url"])
                        vid = m.group(1) if m else ""
                        leido = vid in leidos
                        motivo = datos.get("videos_sin_leer", {}).get(vid, "")
                        salida.append({
                            "tipo": "video", "tema": tema.nombre, "grupo_contenido": cat.titulo, "titulo": b.get("title") or b["url"],
                            "estado": "Leído" if leido else "Sin leer",
                            "grupo": "ok" if leido else "pendiente", "fecha": "",
                            "detalle": f"En la lección «{tut.titulo}»." + (f" {motivo}" if motivo else ""), "enlace": enlace, "fuente": b["url"],
                        })
                    elif b.get("type") == "pdf" and b.get("file"):
                        salida.append({
                            "tipo": "pdf", "tema": tema.nombre, "grupo_contenido": cat.titulo, "titulo": b.get("title") or b["file"],
                            "estado": "Guía oficial", "grupo": "ok", "fecha": "",
                            "detalle": f"En la lección «{tut.titulo}» ({b['file']})", "enlace": enlace, "fuente": "",
                        })

        for s in Situacion.query.filter_by(tema_id=tema.id).order_by(Situacion.orden).all():
            salida.append({
                "tipo": "pregunta", "tema": tema.nombre, "grupo_contenido": s.categoria_libre or "", "titulo": s.situacion,
                "estado": "Confirmada" if s.verificado else "Sin confirmar (se muestra con aviso)",
                "grupo": "ok" if s.verificado else "pendiente", "fecha": "", "detalle": "", "enlace": "", "fuente": "",
            })

    categorias = {c["slug"]: c["titulo"] for c in recursos.biblioteca()["categorias"]}
    for d in recursos.biblioteca()["documentos"]:
        salida.append({
            "tipo": "documento", "tema": ", ".join(d.get("modulos", [])), "grupo_contenido": categorias.get(d.get("categoria"), ""),
            "titulo": d["titulo"], "estado": f"Lectura: {d.get('lectura', '—')}", "grupo": _grupo_lectura(d.get("lectura")),
            "fecha": d.get("fecha", ""), "detalle": f"Vigencia: {d.get('vigencia', '—')}", "enlace": "", "fuente": d.get("url", ""),
        })

    for t in recursos.glosario_completo()["terminos"]:
        estado = t.get("estado", "pendiente")
        salida.append({
            "tipo": "termino", "tema": t.get("sistema") or t.get("modulo", ""), "grupo_contenido": t.get("categoria", ""),
            "titulo": t["termino"], "estado": recursos.ESTADOS.get(estado, ("", estado))[1],
            "grupo": _ESTADO_RECURSO.get(estado, "pendiente"), "fecha": "", "detalle": t.get("sencilla", ""),
            "enlace": "", "fuente": "",
        })

    for clave, n in recursos.algoritmo()["nodos"].items():
        estado = n.get("estado", "confirmado")
        salida.append({
            "tipo": "algoritmo", "tema": "TIMBÓ Compras", "grupo_contenido": "¿Qué camino sigue una compra?",
            "titulo": n.get("titulo", clave), "estado": recursos.ESTADOS.get(estado, ("", estado))[1],
            "grupo": _ESTADO_RECURSO.get(estado, "pendiente"), "fecha": "", "detalle": n.get("ficha", {}).get("verificar", ""),
            "enlace": "", "fuente": "",
        })
    return salida
