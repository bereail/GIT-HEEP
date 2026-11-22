"""Comparación diaria con el Catálogo WEB de TIMBÓ (catálogo oficial de la
Provincia). La corre `scripts/actualizar_catalogo.py` todos los días.

Qué hace, en orden, sin borrar nunca nada:
1. Copia la base (por las dudas) en instance/copias_catalogo/.
2. Baja el catálogo completo. Si la descarga falla o viene rara (formato
   distinto, muchos menos ítems que la vez anterior), NO se usa: queda la
   copia anterior y la corrida queda registrada como error.
3. Guarda la copia del día en instance/catalogo/ (nunca pisa una anterior).
4. La compara con la copia anterior: ítems nuevos, quitados, con el texto
   cambiado y los que pasaron a «NO UTILIZAR».
5. Busca qué artículos del hospital usan un código que ya no existe o que
   ahora es «NO UTILIZAR» (en el nomenclador y en las respuestas de los
   servicios): esos se marcan para revisar de nuevo, sin tocar la respuesta.
6. Controla que no haya bajado la cantidad de respuestas guardadas (señal de
   pérdida de datos) y deja todo en `actualizaciones_catalogo`.

La base de compras del hospital ya no cambia: solo se actualiza el catálogo.
"""
import csv
import glob
import io
import json
import os
import sqlite3
import urllib.request
from datetime import datetime, timezone

from app.extensions import db

URL_CATALOGO = "https://www.santafe.gob.ar/gestionesdecompras/site/output.php?a=catalogo.get_csv"
COLUMNAS = ["Rubro / Especie", "Sub-Rubro / Familia", "Código Bien o Servicio / Elemento", "Bien o Servicio / Elemento",
            "Objeto del Gasto", "Código Ítem", "Ítem Específico", "Cód. Sistema Externo"]
MINIMO_ITEMS = 10000          # el catálogo tiene ~17.800 ítems
CAIDA_MAXIMA = 0.10           # más de 10 % menos que la vez anterior → no se usa
COPIAS_BASE_A_GUARDAR = 14


def carpeta_catalogo(instancia):
    return os.path.join(instancia, "catalogo")


def leer_catalogo(texto):
    """{código ítem: (texto, no_utilizar)} a partir del CSV del Catálogo WEB.
    Lanza ValueError si el formato no es el esperado."""
    texto = texto.lstrip("﻿")
    lector = csv.reader(io.StringIO(texto), delimiter="|", quotechar='"')
    encabezado = next(lector, None)
    if not encabezado or [c.strip() for c in encabezado[:len(COLUMNAS)]] != COLUMNAS:
        raise ValueError("El catálogo vino con otras columnas: " + "|".join(encabezado or [])[:200])
    items = {}
    for fila in lector:
        if len(fila) < 7 or not fila[5].strip():
            continue
        # Espacios y saltos de línea dentro del texto no cuentan como cambio
        # (al bajarlo vienen en formato Windows y al leer la copia guardada, no).
        bien, item = " ".join(fila[3].split()), " ".join(fila[6].split())
        items[fila[5].strip()] = (f"{bien} — {item}", "NO UTILIZAR" in (bien + " " + item).upper())
    return items


def _orden_copia(ruta):
    """catalogo_AAAAMMDD-HHMMSS[-N].csv → (fecha, N): la más nueva queda última."""
    nombre = os.path.basename(ruta)[len("catalogo_"):-len(".csv")]
    n = nombre.split("-")
    return (n[0] + n[1] if len(n) > 1 else n[0], int(n[2]) if len(n) > 2 and n[2].isdigit() else 1)


def ultima_copia(instancia):
    archivos = sorted(glob.glob(os.path.join(carpeta_catalogo(instancia), "catalogo_*.csv")), key=_orden_copia)
    return archivos[-1] if archivos else None


_cache = {"ruta": None, "mtime": None, "items": {}}


def marca_en_curso(instancia):
    os.makedirs(carpeta_catalogo(instancia), exist_ok=True)
    ruta = os.path.join(carpeta_catalogo(instancia), ".en_curso")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(str(os.getpid()))
    return ruta


def en_curso(instancia, minutos=20):
    """Hay una actualización corriendo (la marca tiene menos de 20 minutos:
    si quedó de una corrida que se cortó, después de eso se ignora)."""
    import time
    ruta = os.path.join(carpeta_catalogo(instancia), ".en_curso")
    return os.path.exists(ruta) and time.time() - os.path.getmtime(ruta) < minutos * 60


def ultima_actualizacion():
    """La última corrida que dejó una copia del catálogo (para mostrar «el
    catálogo que estás viendo es del …»)."""
    from app.models.revision_servicio import ActualizacionCatalogo
    return (ActualizacionCatalogo.query.filter(ActualizacionCatalogo.estado != "error", ActualizacionCatalogo.archivo != "")
            .order_by(ActualizacionCatalogo.en.desc()).first())


def catalogo_vigente(instancia):
    """El último catálogo guardado (en memoria mientras no cambie el archivo)."""
    ruta = ultima_copia(instancia)
    if not ruta:
        return {}
    mtime = os.path.getmtime(ruta)
    if _cache["ruta"] != ruta or _cache["mtime"] != mtime:
        with open(ruta, encoding="utf-8") as f:
            _cache.update(ruta=ruta, mtime=mtime, items=leer_catalogo(f.read()))
    return _cache["items"]


def aviso_codigo(codigo, catalogo):
    """Texto de aviso si un código ya no sirve según el catálogo vigente."""
    if not codigo or not catalogo:
        return ""
    dato = catalogo.get(codigo)
    if dato is None:
        return f"El código {codigo} ya no figura en el Catálogo WEB: revisalo de nuevo."
    if dato[1]:
        return f"El código {codigo} ahora figura como «NO UTILIZAR» en el Catálogo WEB: revisalo de nuevo."
    return ""


def comparar(anterior, nuevo):
    nuevos = sorted(set(nuevo) - set(anterior))
    quitados = sorted(set(anterior) - set(nuevo))
    cambiados = sorted(c for c in set(nuevo) & set(anterior) if nuevo[c][0] != anterior[c][0])
    no_utilizar = sorted(c for c in nuevo if nuevo[c][1] and not anterior.get(c, ("", False))[1] and c in anterior)
    return {"nuevos": nuevos, "quitados": quitados, "cambiados": cambiados, "no_utilizar": no_utilizar}


def ruta_libre(ruta):
    """La misma ruta, o con -2, -3… si ya existe: nunca se pisa un archivo."""
    base, ext = os.path.splitext(ruta)
    n, candidata = 1, ruta
    while os.path.exists(candidata):
        n += 1
        candidata = f"{base}-{n}{ext}"
    return candidata


def copiar_base(ruta_base, instancia, ahora):
    destino_dir = os.path.join(instancia, "copias_catalogo")
    os.makedirs(destino_dir, exist_ok=True)
    destino = ruta_libre(os.path.join(destino_dir, f"antes-del-catalogo-{ahora:%Y%m%d-%H%M%S}.sqlite3"))
    origen, copia = sqlite3.connect(ruta_base), sqlite3.connect(destino)
    with copia:
        origen.backup(copia)
    copia.close()
    origen.close()
    try:
        os.chmod(destino, 0o600)
    except OSError:
        pass
    for viejo in sorted(glob.glob(os.path.join(destino_dir, "antes-del-catalogo-*.sqlite3")))[:-COPIAS_BASE_A_GUARDAR]:
        os.remove(viejo)
    return destino


def descargar(url=URL_CATALOGO, intentos=3, espera=20):
    import time
    ultimo = None
    for n in range(intentos):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "CentroAprendizaje-HEEP"}), timeout=180) as r:
                return r.read().decode("utf-8")
        except Exception as e:  # noqa: BLE001 — se registra y se reintenta
            ultimo = e
            if n + 1 < intentos:
                time.sleep(espera)
    raise RuntimeError(f"No se pudo bajar el catálogo: {ultimo}")


def contar_respuestas():
    from app.models import ObservacionNomenclador
    from app.models.revision_servicio import NecesidadServicio, RevisionArticuloServicio
    return (RevisionArticuloServicio.query.count() + NecesidadServicio.query.count()
            + ObservacionNomenclador.query.count())


def afectados(catalogo):
    """Artículos del hospital (nomenclador y respuestas de servicios) con un
    código que hoy no existe o es «NO UTILIZAR»."""
    from app.models import EquivalenciaArticulo
    from app.models.revision_servicio import LlaveServicio, RevisionArticuloServicio
    vistos, lista = set(), []
    for e in EquivalenciaArticulo.query.filter(EquivalenciaArticulo.codigo_catalogo.isnot(None),
                                               EquivalenciaArticulo.confianza != "sin_match"):
        aviso = aviso_codigo(e.codigo_catalogo, catalogo)
        if aviso and (e.codigo_interno, e.codigo_catalogo) not in vistos:
            vistos.add((e.codigo_interno, e.codigo_catalogo))
            lista.append({"codigo_interno": e.codigo_interno or "", "articulo": e.nombre_interno,
                          "codigo": e.codigo_catalogo, "donde": "nomenclador", "aviso": aviso})
    nombres = {ll.id: ll.servicio for ll in LlaveServicio.query}
    for r in RevisionArticuloServicio.query.filter(RevisionArticuloServicio.resultado.isnot(None)):
        codigo = r.codigo_correcto or (r.codigo_propuesto if r.resultado == "correcto" else "")
        aviso = aviso_codigo(codigo, catalogo)
        if aviso:
            lista.append({"codigo_interno": r.codigo_interno, "articulo": r.nombre_item, "codigo": codigo,
                          "donde": f"respuesta de {nombres.get(r.llave_id, '?')}", "aviso": aviso})
    return lista


_VACIAS = {"de", "del", "la", "las", "el", "los", "con", "sin", "para", "por", "x", "y", "en", "un", "una", "tipo"}


def _palabras(texto):
    import unicodedata
    t = unicodedata.normalize("NFKD", str(texto or "").lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return {w for w in "".join(c if c.isalnum() else " " for c in t).split() if len(w) >= 3 and w not in _VACIAS}


def resumen_servicios():
    """Por servicio: cuántos hay que cargar, ya están, no se revisaron y quedan
    fuera (mismo criterio que la planilla final). También devuelve la lista de
    lo que hay que cargar, para buscarlo entre los ítems nuevos del catálogo."""
    from app.models.revision_servicio import LlaveServicio
    from app.services import llaves_servicio as ls
    resumen, cargar = {}, []
    for ll in LlaveServicio.query.order_by(LlaveServicio.servicio):
        g = ls.planilla_final(ll)
        resumen[ll.servicio] = {k: len(v) for k, v in g.items()}
        cargar += [(ll.servicio, fila[2], fila[3]) for fila in g["cargar"]]
    return resumen, cargar


def posibles_altas(cargar, nuevos):
    """Artículos que un servicio pidió cargar y que podrían haber aparecido
    entre los ítems nuevos del catálogo (por palabras en común). Es solo una
    sugerencia: lo confirma una persona."""
    nuevos_p = [(c, t, _palabras(t)) for c, t in nuevos]
    lista = []
    for servicio, codigo_interno, articulo in cargar:
        p = _palabras(articulo)
        if len(p) < 2:
            continue
        mejor = max(((len(p & q) / len(p), c, t) for c, t, q in nuevos_p if len(p & q) >= 2), default=None)
        if mejor and mejor[0] >= 0.6:
            lista.append({"servicio": servicio, "codigo_interno": codigo_interno, "articulo": articulo,
                          "codigo": mejor[1], "item": mejor[2]})
    return lista


def actualizar(instancia, ruta_base, texto=None):
    """Una corrida completa. `texto` permite pasar el CSV ya bajado (pruebas).
    Devuelve el registro `ActualizacionCatalogo` guardado."""
    from app.models.revision_servicio import ActualizacionCatalogo

    ahora = datetime.now()
    registro = ActualizacionCatalogo(en=datetime.now(timezone.utc), estado="ok")
    try:
        copiar_base(ruta_base, instancia, ahora)
        texto = texto if texto is not None else descargar()
        nuevo = leer_catalogo(texto)
        anterior_ruta = ultima_copia(instancia)
        anterior = {}
        if anterior_ruta:
            with open(anterior_ruta, encoding="utf-8") as f:
                anterior = leer_catalogo(f.read())
        if len(nuevo) < MINIMO_ITEMS or (anterior and len(nuevo) < len(anterior) * (1 - CAIDA_MAXIMA)):
            raise ValueError(f"El catálogo bajado tiene {len(nuevo)} ítems (antes {len(anterior)}): parece incompleto, "
                             "no se usa. Queda el anterior.")
        os.makedirs(carpeta_catalogo(instancia), exist_ok=True)
        archivo = ruta_libre(os.path.join(carpeta_catalogo(instancia), f"catalogo_{ahora:%Y%m%d-%H%M%S}.csv"))
        with open(archivo, "w", encoding="utf-8", newline="") as f:
            f.write(texto.lstrip("﻿"))
        dif = comparar(anterior, nuevo) if anterior else {"nuevos": [], "quitados": [], "cambiados": [], "no_utilizar": []}
        lista = afectados(nuevo)
        resumen, cargar = resumen_servicios()
        altas = posibles_altas(cargar, [(c, nuevo[c][0]) for c in dif["nuevos"]])
        registro.archivo = os.path.basename(archivo)
        registro.items = len(nuevo)
        registro.nuevos, registro.quitados = len(dif["nuevos"]), len(dif["quitados"])
        registro.cambiados, registro.no_utilizar = len(dif["cambiados"]), len(dif["no_utilizar"])
        registro.afectados = len(lista)
        registro.detalle = json.dumps({
            "nuevos": [[c, nuevo[c][0]] for c in dif["nuevos"][:500]],
            "quitados": [[c, anterior[c][0]] for c in dif["quitados"][:500]],
            "cambiados": [[c, anterior[c][0], nuevo[c][0]] for c in dif["cambiados"][:500]],
            "no_utilizar": [[c, nuevo[c][0]] for c in dif["no_utilizar"][:500]],
            "afectados": lista[:2000],
            "resumen_servicios": resumen,
            "posibles_altas": altas[:500],
        }, ensure_ascii=False)
        registro.mensaje = ("Primera copia del catálogo: desde mañana se comparan los cambios." if not anterior
                            else "Catálogo actualizado.")
    except Exception as e:  # noqa: BLE001 — cualquier falla queda registrada, nada se pisa
        registro.estado = "error"
        registro.mensaje = str(e)[:2000]
    registro.respuestas = contar_respuestas()
    previo = (ActualizacionCatalogo.query.filter(ActualizacionCatalogo.respuestas > 0)
              .order_by(ActualizacionCatalogo.en.desc()).first())
    if previo and registro.respuestas < previo.respuestas:
        registro.estado = "alerta"
        registro.mensaje = (f"¡Atención! Hay {registro.respuestas} respuestas guardadas y la vez anterior había "
                            f"{previo.respuestas}. Revisar la copia de la base. " + registro.mensaje)
    db.session.add(registro)
    db.session.commit()
    return registro
