"""Planilla de revisión de artículos por servicio (bodega / centro de pedido).

Arma, para una bodega, la lista de artículos del nomenclador ordenada en las
tres secciones de la revisión y los datos que necesita la planilla HTML
descargable (`templates/revision_servicio/planilla.html`). Solo lee
`equivalencias_articulos`: no crea tablas ni modifica equivalencias, y no
toca la revisión de Farmacia (`observaciones_nomenclador`).
"""
import hashlib
import json
import os
import re
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone

from app.models import EquivalenciaArticulo
from app.revision.routes import descripcion_timbo, nota_visible

FORMATO = "revision-servicio/1"

# Fuera de esta actividad por decisión de la usuaria (19/11/2026): Farmacia
# tiene su propia revisión en /revision/ y Laboratorio se desestimó.
BODEGAS_EXCLUIDAS = frozenset({"FARMACIA", "LABORATORIO"})

# Orden pedido: 1) faltan cargar, 2) necesitan confirmación, 3) ya existen y
# deben verificarse. Sale del nivel de confianza del cruce automático.
SECCION_POR_CONFIANZA = {"sin_match": 1, "dudosa": 2, "alta": 3}

MOTIVO_POR_CONFIANZA = {
    "sin_match": "La comparación automática no encontró en el Catálogo WEB ningún ítem que corresponda a este artículo.",
    "dudosa": "La comparación automática encontró un ítem parecido en el Catálogo WEB, pero no idéntico.",
    "alta": "La comparación automática encontró un ítem del Catálogo WEB con las mismas palabras clave y los mismos números (medidas, dosis). Igual hay que verificarlo.",
}
# Artículos de la bodega a los que se les propuso el mismo código del Catálogo
# WEB: se muestran juntos en una card, para comparar cuáles corresponden. Más
# de MAX_GRUPO no entran en una card; quedan sueltos, con el aviso.
MAX_GRUPO = 20
MOTIVO_MISMO_CODIGO = "El mismo código se propuso para {n} artículos de esta bodega: puede corresponder a varios, a uno solo o a ninguno."
MOTIVO_NO_UTILIZAR = "El Catálogo WEB marca el código propuesto como «NO UTILIZAR»: confirmar con Compras antes de usarlo."

_CARPETA_STATIC = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")


def bodegas_revisables(bodegas):
    return [b for b in bodegas if b and b not in BODEGAS_EXCLUIDAS]


def es_no_utilizar(e):
    return "NO UTILIZAR" in (e.bien_o_servicio or "").upper() or "NO UTILIZAR" in (e.item_especifico or "").upper()


def _item(e):
    seccion = SECCION_POR_CONFIANZA.get(e.confianza, 2)
    no_utilizar = bool(e.codigo_catalogo) and es_no_utilizar(e)
    if no_utilizar and seccion == 3:
        seccion = 2
    motivos = [MOTIVO_POR_CONFIANZA.get(e.confianza, MOTIVO_POR_CONFIANZA["dudosa"])]
    if no_utilizar:
        motivos.append(MOTIVO_NO_UTILIZAR)
    nota = nota_visible(e.notas)
    item = {
        "id": e.codigo_interno or "",
        "ca": e.codigo_articulo or "",
        "n": e.nombre_interno,
        "s": seccion,
        "m": " ".join(motivos),
        "nota": nota,
        "nu": no_utilizar,
    }
    if e.confianza == "sin_match":
        # En los rojos el cruce igual guarda el "mejor" candidato, que fue
        # descartado: no se muestra como código propuesto.
        item["cp"] = ""
        item["dn"] = ""
        if e.codigo_catalogo:
            item["cd"] = f"{e.codigo_catalogo} — {descripcion_timbo(e)}"
    else:
        item["cp"] = e.codigo_catalogo or ""
        item["dn"] = descripcion_timbo(e)
    return item


def _normal(texto):
    return " ".join(unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower().split())


def _orden(item):
    return (item["s"], _normal(item["n"]), item["id"])


def _agrupar(items):
    """Marca los artículos que comparten código propuesto. En un grupo todos
    van a la sección más temprana de sus miembros, y `dup` señala los que
    además tienen el mismo nombre (posible artículo cargado dos veces)."""
    por_codigo = defaultdict(list)
    for item in items:
        if item["cp"]:
            por_codigo[item["cp"]].append(item)
    for codigo, miembros in por_codigo.items():
        if len(miembros) < 2:
            continue
        aviso = MOTIVO_MISMO_CODIGO.format(n=len(miembros))
        for item in miembros:
            item["m"] = f"{item['m']} {aviso}"
        if len(miembros) > MAX_GRUPO:
            continue
        seccion = min(i["s"] for i in miembros)
        nombres = defaultdict(int)
        for item in miembros:
            nombres[_normal(item["n"])] += 1
        for item in miembros:
            item["g"] = codigo
            item["s"] = seccion
            item["dup"] = nombres[_normal(item["n"])] > 1


def armar_items(tema, bodegas):
    """Artículos de una o más bodegas, uno por código interno, ordenados en
    las tres secciones y agrupados por código propuesto. Cada uno lleva `b`
    (en cuáles de estas bodegas está) y `ob` (en qué otras bodegas del
    nomenclador figura, para avisar que es compartido)."""
    bodegas = [b for b in bodegas if b and b not in BODEGAS_EXCLUIDAS]
    if not bodegas:
        return [], []
    filas = EquivalenciaArticulo.query.filter(
        EquivalenciaArticulo.tema_id == tema.id, EquivalenciaArticulo.bodega.in_(bodegas)).all()
    por_codigo, en_bodegas = {}, defaultdict(set)
    for e in filas:
        clave = e.codigo_interno or f"sin-codigo:{e.id}"
        por_codigo.setdefault(clave, e)
        en_bodegas[clave].add(e.bodega)
    todas = defaultdict(set)
    codigos = [c for c in por_codigo if not c.startswith("sin-codigo:")]
    for i in range(0, len(codigos), 500):
        for cod, bod in (EquivalenciaArticulo.query.with_entities(EquivalenciaArticulo.codigo_interno, EquivalenciaArticulo.bodega)
                         .filter(EquivalenciaArticulo.tema_id == tema.id,
                                 EquivalenciaArticulo.codigo_interno.in_(codigos[i:i + 500]))):
            if bod:
                todas[cod].add(bod)
    items = []
    for clave, e in por_codigo.items():
        item = _item(e)
        item["b"] = sorted(en_bodegas[clave])
        otras = sorted(todas.get(clave, set()) - en_bodegas[clave])
        if otras:
            item["ob"] = otras
        items.append(item)
    _agrupar(items)
    items.sort(key=_orden)
    return items, filas


def armar_planilla(tema, bodega):
    """Datos de la planilla de una bodega, o None si no corresponde."""
    if not bodega or bodega in BODEGAS_EXCLUIDAS:
        return None
    items, filas = armar_items(tema, [bodega])
    if not items:
        return None
    actualizado = max((e.creado_en for e in filas if e.creado_en), default=None)
    huella = hashlib.sha256(json.dumps(items, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    return {
        "formato": FORMATO,
        "bodega": bodega,
        "versionDatos": huella,
        "nomencladorActualizado": actualizado.strftime("%Y-%m-%d") if actualizado else "",
        "generado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "secciones": {str(s): sum(1 for i in items if i["s"] == s) for s in (1, 2, 3)},
        "items": items,
    }


def nombre_archivo(bodega, fecha=None):
    fecha = fecha or datetime.now().strftime("%Y-%m-%d")
    sin_tildes = unicodedata.normalize("NFKD", bodega).encode("ascii", "ignore").decode().lower()
    return f"revision-{re.sub(r'[^a-z0-9]+', '-', sin_tildes).strip('-')}-{fecha}.html"


def recurso_estatico(nombre):
    """CSS / JS de la planilla, que va todo adentro del HTML descargado."""
    with open(os.path.join(_CARPETA_STATIC, nombre), encoding="utf-8") as f:
        return f.read()
