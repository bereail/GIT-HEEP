"""Lógica de la revisión por servicio con llave (ver `models/revision_servicio.py`).

La usan la pantalla del servicio (`app/servicio/routes.py`) y el panel
(`app/admin/servicios.py`). Nada de esto toca la revisión de Farmacia.
"""
import hashlib
import json
import secrets
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from app.extensions import db
from app.models import EquivalenciaArticulo, Tema
from app.models.revision_servicio import (
    CATALOGO_NECESIDAD, DECISIONES, RESULTADOS_SERVICIO, TIPOS_NECESIDAD, LlaveBodega, LlaveServicio, NecesidadServicio,
    RegistroLlaveServicio, RevisionArticuloServicio, RevisionServicioHistorial,
)
from app.services import revision_servicio

TEMA_NOMENCLADOR = "timbo-compras"
LARGO_OBSERVACION = 2000
# Diferencia entre servicios = uno dice que el código corresponde y otro que
# no. «No se usa» o «aclaración» no cuentan: cada servicio usa cosas distintas.
RESULTADOS_EN_CONFLICTO = {"correcto", "no_corresponde"}


def ahora():
    return datetime.now(timezone.utc)


def hash_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def iso(momento):
    if not momento:
        return None
    if momento.tzinfo is None:
        momento = momento.replace(tzinfo=timezone.utc)
    return momento.isoformat(timespec="seconds")


def hora_ar(momento, formato="%d/%m/%Y %H:%M"):
    if not momento:
        return ""
    if momento.tzinfo is None:
        momento = momento.replace(tzinfo=timezone.utc)
    return momento.astimezone(timezone(timedelta(hours=-3))).strftime(formato)


def tema_nomenclador():
    return Tema.query.filter_by(slug=TEMA_NOMENCLADOR).first()


def bodegas_asignables(tema):
    """Bodegas que se pueden asignar a una llave, con su cantidad de
    artículos. Farmacia y Laboratorio quedan afuera (Farmacia tiene su propia
    revisión)."""
    if not tema:
        return []
    filas = (EquivalenciaArticulo.query.with_entities(EquivalenciaArticulo.bodega, db.func.count(EquivalenciaArticulo.id))
             .filter(EquivalenciaArticulo.tema_id == tema.id, EquivalenciaArticulo.bodega.isnot(None))
             .group_by(EquivalenciaArticulo.bodega).all())
    return sorted(((b, n) for b, n in filas if b and b not in revision_servicio.BODEGAS_EXCLUIDAS), key=lambda x: x[0])


def registrar(llave, accion, detalle=""):
    db.session.add(RegistroLlaveServicio(llave=llave, accion=accion, detalle=detalle, en=ahora()))


# ------------------------------------------------------------- llaves ---

def nuevo_token(llave):
    token = secrets.token_urlsafe(32)
    llave.token_hash = hash_token(token)
    return token


def llave_por_token(token):
    if not (20 <= len(token or "") <= 200):
        return None
    llave = LlaveServicio.query.filter_by(token_hash=hash_token(token)).first()
    if llave and llave.activo and secrets.compare_digest(llave.token_hash, hash_token(token)):
        return llave
    return None


def asignar_bodegas(llave, bodegas, validas):
    """Deja la llave con exactamente esas bodegas (solo las válidas) y
    registra qué se agregó y qué se sacó. Las respuestas no se borran: si una
    bodega vuelve, sus respuestas vuelven a verse."""
    nuevas = sorted({b for b in bodegas if b in validas})
    actuales = {b.bodega: b for b in llave.bodegas}
    agregadas = [b for b in nuevas if b not in actuales]
    sacadas = [b for b in actuales if b not in nuevas]
    for b in sacadas:
        llave.bodegas.remove(actuales[b])
    for b in agregadas:
        llave.bodegas.append(LlaveBodega(bodega=b, asignada_en=ahora()))
    if agregadas:
        registrar(llave, "bodegas asignadas", ", ".join(agregadas))
    if sacadas:
        registrar(llave, "bodegas quitadas", ", ".join(sacadas) + " (sus respuestas se conservan)")
    return agregadas, sacadas


# ----------------------------------------------- artículos de una llave ---

def items_de(llave, tema=None):
    """Artículos que ve la llave: siempre salen de las bodegas guardadas en
    el servidor, nunca de lo que mande el navegador."""
    tema = tema or tema_nomenclador()
    if not tema:
        return [], []
    return revision_servicio.armar_items(tema, llave.nombres_bodegas)


def item_de(llave, codigo, tema=None):
    """Un artículo de las bodegas de la llave (o None si no es suyo). Es lo
    que usa cada clic: no arma la lista entera (en MANTENIMIENTO son 6 mil)."""
    tema = tema or tema_nomenclador()
    bodegas = [b for b in llave.nombres_bodegas if b not in revision_servicio.BODEGAS_EXCLUIDAS]
    if not tema or not bodegas or not codigo:
        return None
    e = (EquivalenciaArticulo.query
         .filter(EquivalenciaArticulo.tema_id == tema.id, EquivalenciaArticulo.bodega.in_(bodegas),
                 EquivalenciaArticulo.codigo_interno == codigo)
         .order_by(EquivalenciaArticulo.id).first())
    return revision_servicio._item(e) if e else None


def codigos_de(llave, tema=None):
    tema = tema or tema_nomenclador()
    bodegas = [b for b in llave.nombres_bodegas if b not in revision_servicio.BODEGAS_EXCLUIDAS]
    if not tema or not bodegas:
        return set()
    return {c for (c,) in EquivalenciaArticulo.query.with_entities(EquivalenciaArticulo.codigo_interno)
            .filter(EquivalenciaArticulo.tema_id == tema.id, EquivalenciaArticulo.bodega.in_(bodegas),
                    EquivalenciaArticulo.codigo_interno.isnot(None)).distinct()}


def avance(llave, tema=None):
    """Mismo criterio que la pantalla del servicio: revisado = todo lo que no
    cae en «falta» (los de «Ya están en TIMBÓ» sin tocar cuentan, porque el
    servicio solo los mira; «no sé» o «no coincide» sin decidir, no)."""
    items, _ = items_de(llave, tema)
    por_id = {r.codigo_interno: r for r in llave.revisiones}
    cuenta = defaultdict(int)
    revisados = solo_mirar = 0
    for item in items:
        r = por_id.get(item["id"])
        if clasificar(item, r)[0] != "falta":
            revisados += 1
        if r and r.resultado:
            cuenta[r.resultado] += 1
        elif item["s"] == 3:
            solo_mirar += 1
    return {"total": len(items), "respondidos": revisados, "por_resultado": dict(cuenta),
            "solo_mirar": solo_mirar, "necesidades": sum(1 for n in llave.necesidades if not n.quitada_en)}


# ------------------------------------------------------------ respuestas ---

# Qué decisiones valen para cada resultado.
DECISIONES_POR_RESULTADO = {"no_corresponde": {"agregar", "codigo"}, "correcto": {"general"}}


def guardar_respuesta(llave, item, resultado, observacion, persona, decision=None, codigo_correcto="", detalle_timbo=""):
    """Crea o cambia la respuesta de la llave sobre un artículo. La versión
    anterior va al historial. Cualquier cambio reabre la revisión si estaba
    terminada. Decisiones: «no corresponde» → agregar / código correcto;
    «correcto» → ítem general (código + detalle para la observación).
    Devuelve la respuesta (o None si no había nada que guardar)."""
    if decision not in DECISIONES_POR_RESULTADO.get(resultado, set()):
        decision = None
    if decision not in ("codigo", "general"):
        codigo_correcto = ""
    if decision != "general":
        detalle_timbo = ""
    r = RevisionArticuloServicio.query.filter_by(llave_id=llave.id, codigo_interno=item["id"]).first()
    momento = ahora()
    if r:
        if (r.resultado, r.observacion, r.decision, r.codigo_correcto or "", r.detalle_timbo or "") == (
                resultado, observacion, decision, codigo_correcto, detalle_timbo):
            return r
        db.session.add(RevisionServicioHistorial(
            revision_id=r.id, resultado=r.resultado, observacion=r.observacion, decision=r.decision,
            codigo_correcto=r.codigo_correcto or "", detalle_timbo=r.detalle_timbo or "",
            codigo_propuesto=r.codigo_propuesto, persona=r.persona, guardado_en=r.actualizado_en or momento))
        r.resultado, r.observacion, r.persona, r.actualizado_en = resultado, observacion, persona, momento
        r.decision, r.codigo_correcto, r.detalle_timbo = decision, codigo_correcto, detalle_timbo
        r.nombre_item, r.codigo_propuesto = item["n"], item.get("cp") or ""
    elif resultado or observacion:
        r = RevisionArticuloServicio(llave_id=llave.id, codigo_interno=item["id"], nombre_item=item["n"],
                                     codigo_propuesto=item.get("cp") or "", resultado=resultado,
                                     observacion=observacion, decision=decision, codigo_correcto=codigo_correcto,
                                     detalle_timbo=detalle_timbo,
                                     persona=persona, creado_en=momento, actualizado_en=momento)
        db.session.add(r)
    else:
        return None
    reabrir_si_terminada(llave, persona)
    return r


def reabrir_si_terminada(llave, persona):
    if llave.finalizado_en:
        llave.finalizado_en = None
        llave.finalizado_por = None
        registrar(llave, "revisión reabierta", f"por un cambio de {persona}")


def estado_cliente(llave, codigos):
    """Lo ya guardado, en el formato del JS de la planilla."""
    respuestas = {}
    for r in llave.revisiones:
        if r.codigo_interno in codigos and (r.resultado or r.observacion):
            respuestas[r.codigo_interno] = {"r": r.resultado, "obs": r.observacion, "t": iso(r.actualizado_en),
                                            "dec": r.decision, "cod": r.codigo_correcto or "",
                                            "det": r.detalle_timbo or "",
                                            "persona": r.persona, "hist": []}
    return {"servicio": llave.servicio, "respuestas": respuestas, "necesidades": necesidades_cliente(llave),
            "finalizado": iso(llave.finalizado_en), "inicio": None, "modificado": None}


# ----------------------------------------------------------- necesidades ---

CAMPOS_NECESIDAD = {"d": ("descripcion", 300), "p": ("presentacion", 200), "u": ("uso", 300),
                    "cod": ("codigo_catalogo", 40), "obs": ("observaciones", LARGO_OBSERVACION)}


def necesidad_a_dict(n):
    return {"id": str(n.id), "d": n.descripcion, "p": n.presentacion, "u": n.uso, "tipo": n.tipo, "cat": n.catalogo,
            "cod": n.codigo_catalogo, "obs": n.observaciones, "creado": iso(n.creado_en), "t": iso(n.actualizado_en),
            "baja": bool(n.quitada_en), "persona": n.persona, "hist": []}


def necesidades_cliente(llave):
    return {str(n.id): necesidad_a_dict(n) for n in llave.necesidades}


def limpiar_necesidad(datos):
    """Valida lo que manda el formulario. Devuelve (campos, error)."""
    campos = {}
    for clave, (columna, largo) in CAMPOS_NECESIDAD.items():
        valor = str(datos.get(clave) or "").strip()
        if len(valor) > largo:
            return None, f"Máximo {largo} caracteres."
        campos[columna] = valor
    if not campos["descripcion"]:
        return None, "Escribí la descripción del artículo."
    tipo = datos.get("tipo") or ""
    catalogo = datos.get("cat") or "no_busque"
    if tipo not in ("", *TIPOS_NECESIDAD) or catalogo not in CATALOGO_NECESIDAD:
        return None, "Datos inválidos."
    campos["tipo"], campos["catalogo"] = tipo, catalogo
    if catalogo != "esta":
        campos["codigo_catalogo"] = ""
    return campos, ""


def guardar_necesidad(llave, id_necesidad, campos, persona):
    """Crea o edita. La versión anterior queda en el registro de la llave."""
    momento = ahora()
    if id_necesidad:
        n = NecesidadServicio.query.filter_by(id=id_necesidad, llave_id=llave.id).first()
        if not n:
            return None
        antes = {c: getattr(n, c) for c in campos}
        if antes == campos:
            return n
        for c, v in campos.items():
            setattr(n, c, v)
        n.persona, n.actualizado_en = persona, momento
        registrar(llave, "artículo necesario editado", f"{persona} · antes: {json.dumps(antes, ensure_ascii=False)}")
    else:
        n = NecesidadServicio(llave_id=llave.id, persona=persona, creado_en=momento, actualizado_en=momento, **campos)
        db.session.add(n)
        registrar(llave, "artículo necesario agregado", f"{persona} · {campos['descripcion']}")
    reabrir_si_terminada(llave, persona)
    return n


def baja_necesidad(llave, id_necesidad, quitar, persona):
    n = NecesidadServicio.query.filter_by(id=id_necesidad, llave_id=llave.id).first()
    if not n:
        return None
    if bool(n.quitada_en) != quitar:
        n.quitada_en = ahora() if quitar else None
        n.actualizado_en = ahora()
        registrar(llave, "artículo necesario quitado" if quitar else "artículo necesario vuelto a poner",
                  f"{persona} · {n.descripcion}")
        reabrir_si_terminada(llave, persona)
    return n


# ------------------------------------------------------- planilla final ---

ENCABEZADOS_FINAL = ["Servicio", "Qué hay que hacer", "Código interno", "Descripción", "Bodegas", "Código propuesto",
                     "Código a usar", "Detalle para la observación en TIMBÓ", "Tipo", "Catálogo WEB", "Observación",
                     "Respondió", "Fecha"]
ANCHOS_FINAL = [22, 34, 12, 44, 22, 14, 14, 40, 26, 20, 40, 22, 17]


# Los grupos de la revisión final y de la planilla final, en este orden.
GRUPOS_FINALES = (
    ("cargar", "HAY QUE CARGAR EN CATALOGO WEB"),
    ("estan", "YA ESTAN EN TIMBO"),
    ("falta", "NO SE REVISARON"),
    ("fuera", "QUEDAN FUERA"),
)


def clasificar(item, r):
    """En qué grupo final cae un artículo según su respuesta, y qué hacer."""
    if not r or not r.resultado:
        if item["s"] == 3:   # ya están en TIMBÓ: el servicio solo los mira
            return "estan", "Ya está en TIMBÓ con el código propuesto"
        return "falta", "Sin revisar"
    if r.resultado == "no_necesario":
        return "fuera", "Ya no se usa"
    if r.resultado == "otro_servicio":
        return "fuera", "No es de este servicio: está mal asignado a la bodega"
    if r.resultado == "aclaracion":
        return "falta", "Requiere aclaración"
    if r.resultado == "correcto":
        if r.decision == "general":
            return "estan", "Usar el ítem general: poner el detalle en la observación"
        if item["s"] == 1:
            return "cargar", "Pedir el alta: no está en el catálogo"
        return "estan", "Usar el código propuesto"
    if r.decision == "agregar":
        return "cargar", "Pedir el alta: el código propuesto es otro artículo"
    if r.decision == "codigo":
        return "estan", "Usar el código que indicó el servicio"
    return "falta", "No coincide: falta decidir si se agrega o qué código va"


def planilla_final(llave, tema=None):
    """Todo lo de la llave separado en los grupos finales: lo que hay que
    cargar en el Catálogo WEB (pedir el alta), lo que ya está en TIMBÓ (con el
    código a usar), lo que queda fuera y lo que falta. Los artículos que el
    servicio cargó porque no estaban van a «cargar»."""
    items, _ = items_de(llave, tema)
    respuestas = {r.codigo_interno: r for r in llave.revisiones}
    grupos = {g: [] for g, _ in GRUPOS_FINALES}
    for i in sorted(items, key=lambda x: x["n"].lower()):
        r = respuestas.get(i["id"])
        grupo, accion = clasificar(i, r)
        codigo_a_usar = ""
        if grupo == "estan" and r:
            codigo_a_usar = r.codigo_correcto or r.codigo_propuesto or i.get("cp", "")
        grupos[grupo].append([llave.servicio, accion, i["id"], i["n"], ", ".join(i.get("b", [])), i.get("cp", ""),
                              codigo_a_usar, (r.detalle_timbo or "") if r else "", "", "", r.observacion if r else "",
                              r.persona if r else "", hora_ar(r.actualizado_en) if r else ""])
    for n in llave.necesidades:
        if not n.quitada_en:
            grupos["cargar"].append([llave.servicio, "Pedir el alta: lo cargó el servicio (no estaba en su lista)", "",
                                     n.descripcion + (f" — {n.presentacion}" if n.presentacion else ""), "", "",
                                     n.codigo_catalogo, "", TIPOS_NECESIDAD.get(n.tipo, ""),
                                     CATALOGO_NECESIDAD.get(n.catalogo, ""), n.observaciones, n.persona,
                                     hora_ar(n.actualizado_en)])
    return grupos


def libro_planilla_final(grupos):
    """Hojas del Excel de la planilla final (una por grupo)."""
    colores = {"cargar": "verde", "estan": "azul", "falta": "amarillo", "fuera": "rojo"}
    return [(nombre, ENCABEZADOS_FINAL, grupos[g], ANCHOS_FINAL, [colores[g]] * len(grupos[g]) if colores[g] else None)
            for g, nombre in GRUPOS_FINALES]


def sin_decidir(llave, tema=None):
    """«No corresponde» sin decisión: falta decir si se agrega o qué código va."""
    codigos = codigos_de(llave, tema)
    return [r for r in llave.revisiones
            if r.resultado == "no_corresponde" and not r.decision and r.codigo_interno in codigos]


# ------------------------------------------------------------- panel ---

def diferencias_entre_servicios():
    """Artículos donde un servicio dijo «corresponde» y otro «no corresponde»."""
    por_codigo = defaultdict(list)
    for r in RevisionArticuloServicio.query.filter(RevisionArticuloServicio.resultado.in_(RESULTADOS_EN_CONFLICTO)):
        por_codigo[r.codigo_interno].append(r)
    return [lista for lista in por_codigo.values()
            if len({r.resultado for r in lista}) > 1 and len({r.llave_id for r in lista}) > 1]




# --------------------------------------------- traer respuestas de Farmacia ---

FARMACIA_A_SERVICIO = {"si": "correcto", "no": "no_corresponde", "duda": "aclaracion"}


def importar_de_farmacia(llave, revisor, tema=None):
    """Copia a la llave las respuestas que una persona dejó en la revisión de
    Farmacia (/revision/), para no empezar de cero. Solo LEE las tablas de
    Farmacia. Se vinculan por el nombre del artículo (así guarda Farmacia) y
    solo para artículos de las bodegas de la llave. Nunca pisa una respuesta
    que la llave ya tenga. Sí → Correcto, No → No corresponde (falta decidir
    si se agrega o qué código va), Dudas → Requiere aclaración."""
    from app.models.revision_nomenclador import ObservacionNomenclador, clave_item

    items, _ = items_de(llave, tema)
    por_nombre = defaultdict(list)
    for i in items:
        por_nombre[clave_item(i["n"])].append(i)
    ya = {r.codigo_interno for r in llave.revisiones if r.resultado or r.observacion}
    persona = f"{revisor.nombre} (traído de la revisión de Farmacia)"
    cuenta = {"traidas": 0, "ya_tenian": 0, "fuera_de_sus_bodegas": 0}
    for o in ObservacionNomenclador.query.filter_by(revisor_id=revisor.id):
        if not (o.validacion or o.texto):
            continue
        destino = por_nombre.get(o.clave_item)
        if not destino:
            cuenta["fuera_de_sus_bodegas"] += 1
            continue
        for item in destino:
            if item["id"] in ya:
                cuenta["ya_tenian"] += 1
                continue
            guardar_respuesta(llave, item, FARMACIA_A_SERVICIO.get(o.validacion), o.texto or "", persona)
            ya.add(item["id"])
            cuenta["traidas"] += 1
    registrar(llave, "respuestas traídas de la revisión de Farmacia",
              f"de {revisor.nombre}: {cuenta['traidas']} traídas, {cuenta['ya_tenian']} ya tenían respuesta "
              f"(no se tocaron), {cuenta['fuera_de_sus_bodegas']} de artículos de otras bodegas")
    return cuenta
