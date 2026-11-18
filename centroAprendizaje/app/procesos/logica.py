"""Reglas del editor de circuitos: qué se puede guardar, qué se revisa y qué
cambió entre versiones. Todo lo que valida la pantalla se vuelve a validar
acá, porque la pantalla se puede saltear.
"""
import json
import re

from app import recursos

# Tipos de bloque: (ícono, nombre, ayuda corta)
TIPOS_BLOQUE = {
    "inicio": ("▶", "Inicio", "Dónde empieza el circuito"),
    "fin": ("■", "Fin", "Dónde termina"),
    "etapa": ("▭", "Etapa", "Un tramo grande del circuito"),
    "actividad": ("✎", "Actividad", "Una tarea concreta que hace alguien"),
    "decision": ("◆", "Decisión", "Una pregunta con varios caminos"),
    "condicion": ("⧫", "Condición", "Algo que tiene que cumplirse para seguir"),
    "autorizacion": ("✔", "Autorización", "Alguien aprueba o firma"),
    "verificacion": ("🔍", "Verificación", "Alguien revisa o controla"),
    "documento": ("📄", "Documento", "Un papel o archivo y su recorrido"),
    "responsable": ("👤", "Responsable", "Un área, persona o perfil"),
    "error": ("⚠", "Error o incidencia", "Algo que puede salir mal en un paso"),
    "excepcion": ("↯", "Excepción", "Un caso especial que cambia el camino"),
    "observacion": ("💬", "Observación", "Una nota sobre el circuito"),
    "pendiente": ("?", "Pendiente de confirmación", "Algo que todavía no se sabe"),
}

# Estados de validación: (nombre, color de la leyenda, explicación)
ESTADOS = {
    "confirmado_equipo": ("Confirmado por el equipo", "verde", "Lo confirmó el personal en el relevamiento. No es norma."),
    "documentado": ("Documentado con fuente oficial", "azul", "Tiene al menos una fuente oficial verificada."),
    "pendiente_confirmacion": ("Pendiente de confirmación", "amarillo", "Falta que alguien lo confirme."),
    "pendiente_documentacion": ("Pendiente de documentación", "naranja", "No se encontró todavía el documento que lo respalde."),
    "sin_respaldo": ("Sin respaldo documental", "rojo", "No hay documento que lo respalde."),
    "en_revision": ("En revisión", "violeta", "Se está revisando."),
    "observado": ("Observado", "gris", "Tiene una observación abierta."),
}

SOPORTES = {
    "sin_definir": "Sin definir",
    "papel": "En papel",
    "digital": "Digital",
    "papel_y_digital": "Papel y digital",
}

SISTEMAS = {
    "sin_definir": "Sin definir",
    "expediente": "Expediente electrónico TIMBÓ",
    "compras": "TIMBÓ Compras",
    "otro_sistema": "Otro sistema",
    "fuera": "Fuera de los sistemas",
}

TIPOS_FLECHA = {
    "normal": "Sigue",
    "alternativa": "Camino alternativo",
    "retorno": "Vuelve a un paso anterior",
    "rechazo": "Rechazo o devolución",
    "espera": "Queda en espera",
    "incidencia": "Incidencia (error del paso)",
    "digitalizacion": "Digitalización / pasa al sistema",
}

FUNCIONES_RESPONSABLE = {
    "inicia": "Inicia",
    "responsable": "Responsable",
    "recibe": "Recibe",
    "revisa": "Revisa",
    "autoriza": "Autoriza",
    "continua": "Continúa",
}

RELACIONES = {
    "coincide": "Coincide con el paso oficial",
    "difiere": "Se hace distinto",
    "fuera": "Se hace fuera de TIMBÓ",
    "sin_relacion": "Sin paso oficial equivalente",
}

# Carriles de fondo (columnas por sistema o área), solo visuales.
COLORES_CARRIL = ("naranja", "azul", "verde", "violeta", "gris")

CAMPOS_DOCUMENTO = ("origen", "completa", "recibe", "revisa", "autoriza", "registra", "archiva", "continua")
CAMPOS_ERROR = ("causa", "detecta", "interviene", "resolucion")

LARGO_TEXTO = 4000
LARGO_CORTO = 300
MAX_NODOS = 600
MAX_FLECHAS = 1500
_ID = re.compile(r"^[A-Za-z0-9_-]{1,40}$")


class ContenidoInvalido(ValueError):
    pass


def _txt(valor, largo=LARGO_CORTO):
    return str(valor if valor is not None else "").strip()[:largo]


def _num(valor, defecto=0.0):
    try:
        n = float(valor)
    except (TypeError, ValueError):
        return defecto
    if n != n or abs(n) > 1e6:  # NaN o fuera de rango
        return defecto
    return round(n, 1)


def _opcion(valor, opciones, defecto):
    return valor if valor in opciones else defecto


def _fuente(f, docs):
    if not isinstance(f, dict):
        return None
    doc = _txt(f.get("doc"), 80)
    if doc and doc not in docs:
        doc = ""  # nunca se guarda una referencia a un documento que no está en la biblioteca
    url = _txt(f.get("url"), 600)
    if url and not url.startswith(("https://", "http://")):
        url = ""
    salida = {
        "doc": doc, "url": "" if doc else url, "titulo": "" if doc else _txt(f.get("titulo")),
        "emisor": "" if doc else _txt(f.get("emisor")), "fecha": "" if doc else _txt(f.get("fecha"), 40),
        "punto": _txt(f.get("punto")), "pagina": _txt(f.get("pagina"), 10),
        "capitulo": _txt(f.get("capitulo")), "fragmento": _txt(f.get("fragmento"), 1500),
        "verificada": bool(f.get("verificada")),
    }
    if not salida["doc"] and not salida["url"]:
        return None  # una fuente sin documento ni enlace no respalda nada
    if salida["pagina"] and not salida["pagina"].isdigit():
        salida["pagina"] = ""
    return salida


def normalizar(datos, clase, docs=None):
    """Limpia el contenido que manda el editor y aplica las reglas del
    circuito. Devuelve (contenido, ajustes): `ajustes` explica cada cambio
    que hizo el servidor, para mostrarlo en pantalla."""
    if docs is None:
        docs = recursos.documentos_por_id()
    if not isinstance(datos, dict):
        raise ContenidoInvalido("El contenido no tiene el formato esperado.")
    nodos_in, flechas_in = datos.get("nodos") or [], datos.get("flechas") or []
    if not isinstance(nodos_in, list) or not isinstance(flechas_in, list):
        raise ContenidoInvalido("El contenido no tiene el formato esperado.")
    if len(nodos_in) > MAX_NODOS or len(flechas_in) > MAX_FLECHAS:
        raise ContenidoInvalido("El circuito es demasiado grande.")

    ajustes, nodos, vistos = [], [], set()
    for n in nodos_in:
        if not isinstance(n, dict):
            continue
        nid = str(n.get("id") or "")
        if not _ID.match(nid) or nid in vistos:
            raise ContenidoInvalido("Hay bloques con identificador repetido o inválido.")
        vistos.add(nid)
        nodo = {
            "id": nid,
            "tipo": _opcion(n.get("tipo"), TIPOS_BLOQUE, "actividad"),
            "titulo": _txt(n.get("titulo")) or "Sin título",
            "descripcion": _txt(n.get("descripcion"), LARGO_TEXTO),
            "x": _num(n.get("x")), "y": _num(n.get("y")),
            "estado": _opcion(n.get("estado"), ESTADOS, "pendiente_confirmacion"),
            "soporte": _opcion(n.get("soporte"), SOPORTES, "sin_definir"),
            "sistema": _opcion(n.get("sistema"), SISTEMAS, "sin_definir"),
            "sector": _txt(n.get("sector")),
            "documentacion": _txt(n.get("documentacion"), LARGO_TEXTO),
            "resultado": _txt(n.get("resultado"), LARGO_TEXTO),
            "condiciones": _txt(n.get("condiciones"), LARGO_TEXTO),
            "responsables": [],
            "fuentes": [],
        }
        for r in (n.get("responsables") or [])[:20]:
            if isinstance(r, dict) and _txt(r.get("quien")):
                nodo["responsables"].append({
                    "funcion": _opcion(r.get("funcion"), FUNCIONES_RESPONSABLE, "responsable"),
                    "quien": _txt(r.get("quien")),
                    "perfil_timbo": bool(r.get("perfil_timbo")),
                })
        for f in (n.get("fuentes") or [])[:20]:
            fuente = _fuente(f, docs)
            if fuente:
                nodo["fuentes"].append(fuente)
        if nodo["tipo"] == "documento":
            d = n.get("documento") if isinstance(n.get("documento"), dict) else {}
            nodo["documento"] = {c: _txt(d.get(c)) for c in CAMPOS_DOCUMENTO}
        if nodo["tipo"] == "error":
            e = n.get("error") if isinstance(n.get("error"), dict) else {}
            nodo["error"] = {c: _txt(e.get(c), LARGO_TEXTO) for c in CAMPOS_ERROR}
            nodo["error"]["nueva_autorizacion"] = bool(e.get("nueva_autorizacion"))
            nodo["error"]["doc_adicional"] = bool(e.get("doc_adicional"))
        if clase == "hospital":
            c = n.get("correspondencia") if isinstance(n.get("correspondencia"), dict) else {}
            nodo["correspondencia"] = {
                "circuito": _txt(c.get("circuito"), 120), "nodo": _txt(c.get("nodo"), 40),
                "relacion": _opcion(c.get("relacion"), RELACIONES, ""), "nota": _txt(c.get("nota"), LARGO_TEXTO),
            }

        # Reglas que separan lo confirmado de palabra de lo oficial.
        verificadas = [f for f in nodo["fuentes"] if f["verificada"]]
        if nodo["estado"] == "documentado" and not verificadas:
            nodo["estado"] = "pendiente_documentacion"
            ajustes.append({"elemento": nid, "mensaje": f"«{nodo['titulo']}»: «Documentado con fuente oficial» necesita "
                                                         "al menos una fuente verificada. Quedó como pendiente de documentación."})
        if clase == "oficial" and nodo["estado"] == "confirmado_equipo":
            nodo["estado"] = "pendiente_documentacion"
            ajustes.append({"elemento": nid, "mensaje": f"«{nodo['titulo']}»: en el circuito oficial no se usa «Confirmado por "
                                                         "el equipo» (lo dicho en una reunión no es documentación oficial). "
                                                         "Quedó como pendiente de documentación."})
        nodos.append(nodo)

    flechas, vistas = [], set()
    for f in flechas_in:
        if not isinstance(f, dict):
            continue
        fid = str(f.get("id") or "")
        if not _ID.match(fid) or fid in vistas:
            raise ContenidoInvalido("Hay flechas con identificador repetido o inválido.")
        vistas.add(fid)
        rango = f.get("rango")
        flechas.append({
            "id": fid, "desde": _txt(f.get("desde"), 40), "hasta": _txt(f.get("hasta"), 40),
            "etiqueta": _txt(f.get("etiqueta")),
            "tipo": _opcion(f.get("tipo"), TIPOS_FLECHA, "normal"),
            "rango": int(rango) if isinstance(rango, int) or (isinstance(rango, str) and rango.isdigit()) else None,
        })
    carriles = []
    for c in (datos.get("carriles") or [])[:8]:
        if isinstance(c, dict) and _txt(c.get("titulo")):
            carriles.append({"titulo": _txt(c.get("titulo"), 80), "x": _num(c.get("x")),
                             "w": max(100.0, _num(c.get("w"), 400.0)),
                             "color": _opcion(c.get("color"), COLORES_CARRIL, "gris")})
    salida = {"nodos": nodos, "flechas": flechas}
    if carriles:
        salida["carriles"] = carriles
    return salida, ajustes


# ---------------------------------------------------------------- revisión --

def revisar(contenido, clase, rangos=None, contenido_anterior=None, docs=None, comentarios_por_elemento=None):
    """Revisión de integridad. Devuelve una lista de
    {nivel: error|aviso|info, elemento, mensaje}. Nunca declara el circuito
    "completo": solo lista lo que encuentra."""
    if docs is None:
        docs = recursos.documentos_por_id()
    rangos = rangos or {}
    obs = []

    def anotar(nivel, elemento, mensaje):
        obs.append({"nivel": nivel, "elemento": elemento, "mensaje": mensaje})

    nodos = {n["id"]: n for n in contenido["nodos"]}
    entradas = {i: [] for i in nodos}
    salidas = {i: [] for i in nodos}
    for f in contenido["flechas"]:
        ok_desde, ok_hasta = f["desde"] in nodos, f["hasta"] in nodos
        if not ok_desde or not ok_hasta:
            anotar("error", f["id"], "Flecha sin " + ("origen" if not ok_desde else "destino") + ".")
        if ok_desde:
            salidas[f["desde"]].append(f)
        if ok_hasta:
            entradas[f["hasta"]].append(f)
        if f.get("rango") is not None:
            r = rangos.get(f["rango"])
            if not r:
                anotar("error", f["id"], "La flecha usa un rango de montos que ya no existe.")
            elif not r.get("fuente_doc"):
                anotar("error", f["id"], f"Importe sin fuente documental: «{r['nombre']}».")
            elif r.get("estado") != "verificado":
                anotar("aviso", f["id"], f"El rango «{r['nombre']}» está pendiente de validación.")

    if contenido["nodos"] and not any(n["tipo"] == "inicio" for n in contenido["nodos"]):
        anotar("aviso", "", "El circuito no tiene un bloque de Inicio.")
    if contenido["nodos"] and not any(n["tipo"] == "fin" for n in contenido["nodos"]):
        anotar("aviso", "", "El circuito no tiene un bloque de Fin.")

    for nid, n in nodos.items():
        t = f"«{n['titulo']}»"
        ent, sal = entradas[nid], salidas[nid]
        if n["tipo"] not in ("observacion", "responsable") and not ent and not sal:
            anotar("error", nid, f"{t} no está conectado con nada.")
        if n["tipo"] == "inicio" and not sal:
            anotar("error", nid, f"{t}: el inicio no tiene salida.")
        if n["tipo"] == "fin" and not ent:
            anotar("error", nid, f"{t}: el fin no tiene entrada.")
        sigue_por_texto = n["tipo"] == "documento" and n.get("documento", {}).get("continua")
        if n["tipo"] not in ("inicio", "fin", "observacion", "responsable", "error") and ent and not sal and not sigue_por_texto:
            anotar("aviso", nid, f"{t} no tiene salida: el circuito se corta acá.")
        if n["tipo"] == "decision":
            if not sal:
                anotar("error", nid, f"{t}: la decisión no tiene caminos de salida.")
            elif len(sal) < 2:
                anotar("error", nid, f"{t}: bifurcación incompleta (tiene un solo camino).")
            sin_etiqueta = [f for f in sal if not f["etiqueta"] and f.get("rango") is None]
            if sal and sin_etiqueta:
                anotar("aviso", nid, f"{t}: hay caminos sin condición escrita.")
        if n["tipo"] in ("actividad", "autorizacion", "verificacion") and not n["responsables"] and not n["sector"]:
            anotar("aviso", nid, f"{t}: actividad sin responsable.")
        if n["tipo"] == "actividad" and not n["descripcion"]:
            anotar("info", nid, f"{t}: actividad sin descripción.")
        if n["tipo"] == "documento":
            d = n.get("documento", {})
            if not d.get("origen"):
                anotar("aviso", nid, f"{t}: documento sin origen.")
            if not d.get("continua") and not sal:
                anotar("aviso", nid, f"{t}: documento sin destino (no se sabe adónde sigue).")
            if n["soporte"] == "sin_definir":
                anotar("aviso", nid, f"{t}: no dice si el documento está en papel o es digital.")
        if n["tipo"] == "error" and not any(f["tipo"] == "incidencia" for f in ent):
            anotar("error", nid, f"{t}: error sin actividad asociada (falta la flecha «Incidencia» desde el paso donde ocurre).")
        for f in n["fuentes"]:
            if f["doc"] and f["doc"] not in docs:
                anotar("error", nid, f"{t}: cita un documento que no está en la biblioteca.")
        if clase == "oficial" and n["tipo"] not in ("observacion", "pendiente", "inicio", "fin"):
            if not n["fuentes"]:
                if n["estado"] not in ("pendiente_documentacion", "sin_respaldo"):
                    anotar("error", nid, f"{t}: dato oficial sin respaldo documental.")
            elif not any(f["verificada"] for f in n["fuentes"]):
                anotar("aviso", nid, f"{t}: tiene fuentes, pero ninguna está verificada.")
        if n["estado"] in ("pendiente_confirmacion", "pendiente_documentacion", "en_revision", "observado", "sin_respaldo"):
            anotar("info", nid, f"{t}: {ESTADOS[n['estado']][0].lower()}.")

    if contenido_anterior:
        actuales = set(nodos)
        comentarios_por_elemento = comentarios_por_elemento or {}
        for n in contenido_anterior.get("nodos", []):
            if n["id"] in actuales:
                continue
            if n.get("fuentes") or comentarios_por_elemento.get(n["id"]):
                anotar("aviso", "", f"Respecto de la última versión se borró «{n.get('titulo', '')}», que tenía "
                                    "fuentes o comentarios. Si fue sin querer, recuperá la versión anterior.")
    orden = {"error": 0, "aviso": 1, "info": 2}
    obs.sort(key=lambda o: orden[o["nivel"]])
    return obs


def discrepancias_de_rangos(rangos):
    """Rangos con el mismo nombre y distintos valores: no se elige ninguno."""
    por_nombre = {}
    for r in rangos:
        por_nombre.setdefault(r["nombre"].strip().lower(), []).append(r)
    salida = []
    for grupo in por_nombre.values():
        valores = {(r["minimo"], r["maximo"]) for r in grupo}
        if len(grupo) > 1 and len(valores) > 1:
            salida.append(grupo)
    return salida


# ----------------------------------------------------------------- cambios --

_CAMPOS_RESUMEN = ("tipo", "titulo", "descripcion", "estado", "soporte", "sistema", "sector", "documentacion",
                   "resultado", "condiciones", "responsables", "fuentes", "documento", "error", "correspondencia")


def _resumen(n):
    return {k: n.get(k) for k in _CAMPOS_RESUMEN if n.get(k) not in (None, "", [], {})}


def cambios_entre(anterior, nuevo):
    """Lista de cambios elemento por elemento (las posiciones no cuentan como
    cambio de contenido, salvo que sea lo único que cambió)."""
    anterior = anterior or {"nodos": [], "flechas": []}
    cambios = []
    a_n = {n["id"]: n for n in anterior.get("nodos", [])}
    b_n = {n["id"]: n for n in nuevo.get("nodos", [])}
    movidos = 0
    for nid, n in b_n.items():
        if nid not in a_n:
            cambios.append({"elemento": nid, "accion": "agregado", "titulo": n["titulo"], "antes": "",
                            "despues": json.dumps(_resumen(n), ensure_ascii=False)})
            continue
        ra, rb = _resumen(a_n[nid]), _resumen(n)
        if ra != rb:
            campos = sorted(k for k in set(ra) | set(rb) if ra.get(k) != rb.get(k))
            cambios.append({"elemento": nid, "accion": "modificado", "titulo": n["titulo"], "campos": campos,
                            "antes": json.dumps({k: ra.get(k) for k in campos}, ensure_ascii=False),
                            "despues": json.dumps({k: rb.get(k) for k in campos}, ensure_ascii=False)})
        elif (a_n[nid].get("x"), a_n[nid].get("y")) != (n.get("x"), n.get("y")):
            movidos += 1
    for nid, n in a_n.items():
        if nid not in b_n:
            cambios.append({"elemento": nid, "accion": "eliminado", "titulo": n.get("titulo", ""),
                            "antes": json.dumps(_resumen(n), ensure_ascii=False), "despues": ""})
    a_f = {f["id"]: f for f in anterior.get("flechas", [])}
    b_f = {f["id"]: f for f in nuevo.get("flechas", [])}

    def nombre_flecha(f, nodos):
        return f"{nodos.get(f['desde'], {}).get('titulo', '?')} → {nodos.get(f['hasta'], {}).get('titulo', '?')}"

    for fid, f in b_f.items():
        if fid not in a_f:
            cambios.append({"elemento": fid, "accion": "flecha agregada", "titulo": nombre_flecha(f, b_n), "antes": "",
                            "despues": json.dumps(f, ensure_ascii=False)})
        elif a_f[fid] != f:
            cambios.append({"elemento": fid, "accion": "flecha modificada", "titulo": nombre_flecha(f, b_n),
                            "antes": json.dumps(a_f[fid], ensure_ascii=False), "despues": json.dumps(f, ensure_ascii=False)})
    for fid, f in a_f.items():
        if fid not in b_f:
            cambios.append({"elemento": fid, "accion": "flecha eliminada", "titulo": nombre_flecha(f, a_n),
                            "antes": json.dumps(f, ensure_ascii=False), "despues": ""})
    if movidos:
        cambios.append({"elemento": "", "accion": "reubicado", "titulo": f"{movidos} bloque(s) cambiaron de lugar",
                        "antes": "", "despues": ""})
    return cambios


def enlace_fuente(f, docs=None):
    """Datos para mostrar una fuente: título, emisor, fecha y enlace (a la
    página exacta si es un PDF y se conoce la página)."""
    if docs is None:
        docs = recursos.documentos_por_id()
    if f.get("doc"):
        d = docs.get(f["doc"])
        if not d:
            return None
        url = d.get("url", "")
        titulo, emisor, fecha = d.get("titulo", ""), d.get("emisor", ""), d.get("fecha", "")
    else:
        url, titulo, emisor, fecha = f.get("url", ""), f.get("titulo", ""), f.get("emisor", ""), f.get("fecha", "")
    if url.startswith("/"):
        pass  # documento guardado en el propio sitio
    elif not url.startswith(("https://", "http://")):
        url = ""
    if url and f.get("pagina") and ".pdf" in url.lower() and "#" not in url:
        url += f"#page={f['pagina']}"
    return {"titulo": titulo, "emisor": emisor, "fecha": fecha, "url": url, "punto": f.get("punto", ""),
            "pagina": f.get("pagina", ""), "capitulo": f.get("capitulo", ""), "fragmento": f.get("fragmento", ""),
            "verificada": f.get("verificada", False)}
