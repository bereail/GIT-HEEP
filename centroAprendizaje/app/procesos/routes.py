"""Gestión de procesos y circuitos: /admin/procesos.

Todo exige la sesión del panel (`requiere_admin`). Las personas de Compras
participan mirando la pantalla proyectada: no tienen acceso de edición.
"""
import json
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for

from app import recursos
from app.admin.auth import requiere_admin
from app.extensions import db
from app.models import (
    AuditoriaProceso,
    Circuito,
    CircuitoVersion,
    ComentarioCircuito,
    RangoMonto,
    SugerenciaRelevamiento,
)
from app.models.proceso import (
    CLASES_CIRCUITO,
    CLASES_SUGERENCIA,
    ESTADOS_RANGO,
    ESTADOS_SUGERENCIA,
    RECURSOS_SUGERENCIA,
    TIPOS_COMENTARIO,
)
from app.procesos import logica
from app.seguridad import limitar
from app.services.textutil import slugify

procesos_bp = Blueprint("procesos", __name__, url_prefix="/admin/procesos", template_folder="../templates/admin/procesos")


def _circuito_o_404(slug):
    c = Circuito.query.filter_by(slug=slug).first()
    if not c:
        abort(404)
    return c


def _rangos_dict():
    return {r.id: r.como_dict() for r in RangoMonto.query.order_by(RangoMonto.id).all()}


def _comentarios_por_elemento(circuito):
    salida = {}
    for c in circuito.comentarios:
        salida.setdefault(c.elemento_id, []).append(c)
    return salida


def _revision(circuito, contenido=None):
    contenido = contenido if contenido is not None else circuito.contenido
    anterior = json.loads(circuito.ultima_version.contenido) if circuito.ultima_version else None
    return logica.revisar(contenido, circuito.clase, _rangos_dict(), anterior,
                          comentarios_por_elemento=_comentarios_por_elemento(circuito))


def _auditar(entidad, entidad_id, accion, antes="", despues="", motivo=""):
    db.session.add(AuditoriaProceso(entidad=entidad, entidad_id=str(entidad_id), accion=accion,
                                    antes=antes if isinstance(antes, str) else json.dumps(antes, ensure_ascii=False),
                                    despues=despues if isinstance(despues, str) else json.dumps(despues, ensure_ascii=False),
                                    motivo=motivo))


def _catalogos():
    docs = recursos.documentos_por_id()
    return {
        "tipos": {k: {"icono": v[0], "nombre": v[1], "ayuda": v[2]} for k, v in logica.TIPOS_BLOQUE.items()},
        "estados": {k: {"nombre": v[0], "color": v[1], "ayuda": v[2]} for k, v in logica.ESTADOS.items()},
        "soportes": logica.SOPORTES,
        "sistemas": logica.SISTEMAS,
        "tipos_flecha": logica.TIPOS_FLECHA,
        "funciones": logica.FUNCIONES_RESPONSABLE,
        "relaciones": logica.RELACIONES,
        "tipos_comentario": TIPOS_COMENTARIO,
        "documentos": [{"id": d["id"], "titulo": d["titulo"], "emisor": d.get("emisor", ""), "fecha": d.get("fecha", ""),
                        "url": d.get("url", "")} for d in docs.values()],
    }


# ------------------------------------------------------------------ inicio --

@procesos_bp.route("/")
@requiere_admin
def inicio():
    circuitos = Circuito.query.order_by(Circuito.clase, Circuito.nombre).all()
    resumen = {}
    for c in circuitos:
        obs = _revision(c)
        resumen[c.id] = {"nodos": len(c.contenido["nodos"]), "errores": sum(o["nivel"] == "error" for o in obs),
                         "avisos": sum(o["nivel"] == "aviso" for o in obs)}
    return render_template("procesos/inicio.html", circuitos=circuitos, resumen=resumen, clases=CLASES_CIRCUITO,
                           sugerencias=SugerenciaRelevamiento.query.count(), rangos=RangoMonto.query.count())


@procesos_bp.route("/nuevo", methods=["POST"])
@requiere_admin
def nuevo():
    nombre = (request.form.get("nombre") or "").strip()[:200]
    clase = request.form.get("clase")
    if not nombre or clase not in CLASES_CIRCUITO:
        flash("Poné un nombre y elegí si es del hospital o el oficial de TIMBÓ.", "error")
        return redirect(url_for("procesos.inicio"))
    base = slugify(nombre)[:100] or "circuito"
    slug, i = base, 2
    while Circuito.query.filter_by(slug=slug).first():
        slug, i = f"{base}-{i}", i + 1
    c = Circuito(slug=slug, nombre=nombre, clase=clase, descripcion=(request.form.get("descripcion") or "").strip()[:2000])
    db.session.add(c)
    db.session.flush()
    _auditar("circuito", c.id, "creado", despues=nombre)
    db.session.commit()
    return redirect(url_for("procesos.editor", slug=slug))


@procesos_bp.route("/<slug>/datos", methods=["POST"])
@requiere_admin
def editar_datos(slug):
    c = _circuito_o_404(slug)
    nombre = (request.form.get("nombre") or "").strip()[:200]
    if not nombre:
        flash("El circuito necesita un nombre.", "error")
        return redirect(url_for("procesos.editor", slug=slug))
    antes = {"nombre": c.nombre, "descripcion": c.descripcion}
    c.nombre, c.descripcion = nombre, (request.form.get("descripcion") or "").strip()[:2000]
    _auditar("circuito", c.id, "datos editados", antes, {"nombre": c.nombre, "descripcion": c.descripcion})
    db.session.commit()
    flash("Datos del circuito guardados.", "ok")
    return redirect(url_for("procesos.editor", slug=slug))


# ------------------------------------------------------------------ editor --

def _datos_editor(c, contenido, solo_lectura=False, version=None):
    comentarios = [{"id": x.id, "elemento": x.elemento_id, "tipo": x.tipo, "texto": x.texto, "resuelto": x.resuelto,
                    "fecha": x.creado.isoformat() if x.creado else ""} for x in c.comentarios]
    oficiales = {}
    if c.clase == "hospital":
        for o in Circuito.query.filter_by(clase="oficial").all():
            oficiales[o.slug] = {"nombre": o.nombre,
                                 "nodos": [{"id": n["id"], "titulo": n["titulo"]} for n in o.contenido["nodos"]]}
    return {
        "circuito": {"slug": c.slug, "nombre": c.nombre, "clase": c.clase, "descripcion": c.descripcion},
        "contenido": contenido, "comentarios": comentarios, "rangos": list(_rangos_dict().values()),
        "catalogos": _catalogos(), "oficiales": oficiales, "solo_lectura": solo_lectura,
        "version": version,
        "urls": {
            "borrador": url_for("procesos.guardar_borrador", slug=c.slug),
            "version": url_for("procesos.guardar_version", slug=c.slug),
            "comentario": url_for("procesos.comentar", slug=c.slug),
            "resolver": url_for("procesos.resolver_comentario", slug=c.slug, comentario_id=0),
            "revisar": url_for("procesos.revisar", slug=c.slug),
        },
    }


@procesos_bp.route("/<slug>")
@requiere_admin
def editor(slug):
    c = _circuito_o_404(slug)
    return render_template("procesos/editor.html", c=c, clases=CLASES_CIRCUITO,
                           datos=_datos_editor(c, c.contenido), revision=_revision(c))


def _json_o_400():
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        abort(400)
    return datos


@procesos_bp.route("/<slug>/borrador", methods=["POST"])
@requiere_admin
@limitar("procesos-borrador", 600, 300)
def guardar_borrador(slug):
    """Autoguardado: guarda el dibujo tal como está, sin crear versión."""
    c = _circuito_o_404(slug)
    try:
        contenido, ajustes = logica.normalizar(_json_o_400().get("contenido"), c.clase)
    except logica.ContenidoInvalido as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    c.borrador = json.dumps(contenido, ensure_ascii=False)
    c.borrador_actualizado = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify({"ok": True, "ajustes": ajustes, "contenido": contenido if ajustes else None,
                    "revision": _revision(c, contenido), "guardado": c.borrador_actualizado.isoformat()})


@procesos_bp.route("/<slug>/version", methods=["POST"])
@requiere_admin
@limitar("procesos-version", 120, 300)
def guardar_version(slug):
    """Guarda una versión con su motivo y la lista de cambios respecto de la
    anterior. Si no cambió nada, no crea una versión vacía."""
    c = _circuito_o_404(slug)
    datos = _json_o_400()
    try:
        contenido, ajustes = logica.normalizar(datos.get("contenido"), c.clase)
    except logica.ContenidoInvalido as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    anterior = json.loads(c.ultima_version.contenido) if c.ultima_version else None
    cambios = logica.cambios_entre(anterior, contenido)
    c.borrador = json.dumps(contenido, ensure_ascii=False)
    c.borrador_actualizado = datetime.now(timezone.utc)
    if not cambios:
        db.session.commit()
        return jsonify({"ok": True, "sin_cambios": True, "ajustes": ajustes, "revision": _revision(c, contenido)})
    numero = (c.ultima_version.numero + 1) if c.ultima_version else 1
    v = CircuitoVersion(circuito_id=c.id, numero=numero, contenido=c.borrador,
                        motivo=str(datos.get("motivo") or "").strip()[:1000],
                        importante=bool(datos.get("importante")),
                        cambios=json.dumps(cambios, ensure_ascii=False))
    db.session.add(v)
    db.session.commit()
    return jsonify({"ok": True, "numero": numero, "cambios": len(cambios), "ajustes": ajustes,
                    "revision": _revision(c, contenido)})


@procesos_bp.route("/<slug>/revisar")
@requiere_admin
def revisar(slug):
    c = _circuito_o_404(slug)
    return jsonify({"revision": _revision(c)})


# -------------------------------------------------------------- comentarios --

@procesos_bp.route("/<slug>/comentarios", methods=["POST"])
@requiere_admin
@limitar("procesos-comentario", 300, 300)
def comentar(slug):
    c = _circuito_o_404(slug)
    datos = _json_o_400()
    texto = str(datos.get("texto") or "").strip()[:4000]
    tipo = datos.get("tipo") if datos.get("tipo") in TIPOS_COMENTARIO else "observacion"
    if not texto:
        return jsonify({"ok": False, "error": "Escribí el comentario."}), 400
    x = ComentarioCircuito(circuito_id=c.id, elemento_id=str(datos.get("elemento") or "")[:40], tipo=tipo, texto=texto)
    db.session.add(x)
    db.session.flush()
    _auditar("comentario", x.id, "agregado", despues=texto, motivo=f"{c.slug} / {x.elemento_id}")
    db.session.commit()
    return jsonify({"ok": True, "comentario": {"id": x.id, "elemento": x.elemento_id, "tipo": x.tipo, "texto": x.texto,
                                               "resuelto": False, "fecha": x.creado.isoformat()}})


@procesos_bp.route("/<slug>/comentarios/<int:comentario_id>/resolver", methods=["POST"])
@requiere_admin
def resolver_comentario(slug, comentario_id):
    c = _circuito_o_404(slug)
    x = ComentarioCircuito.query.filter_by(id=comentario_id, circuito_id=c.id).first_or_404()
    x.resuelto = not x.resuelto
    _auditar("comentario", x.id, "resuelto" if x.resuelto else "reabierto", despues=x.texto)
    db.session.commit()
    return jsonify({"ok": True, "resuelto": x.resuelto})


# ---------------------------------------------------------------- versiones --

@procesos_bp.route("/<slug>/historial")
@requiere_admin
def historial(slug):
    c = _circuito_o_404(slug)
    auditoria = AuditoriaProceso.query.filter(
        ((AuditoriaProceso.entidad == "circuito") & (AuditoriaProceso.entidad_id == str(c.id)))
        | ((AuditoriaProceso.entidad == "comentario") & AuditoriaProceso.motivo.like(f"{c.slug} /%"))
    ).order_by(AuditoriaProceso.creado.desc()).all()
    return render_template("procesos/historial.html", c=c, versiones=list(reversed(c.versiones)), auditoria=auditoria)


@procesos_bp.route("/<slug>/version/<int:numero>")
@requiere_admin
def ver_version(slug, numero):
    c = _circuito_o_404(slug)
    v = CircuitoVersion.query.filter_by(circuito_id=c.id, numero=numero).first_or_404()
    return render_template("procesos/editor.html", c=c, clases=CLASES_CIRCUITO, v=v,
                           datos=_datos_editor(c, json.loads(v.contenido), solo_lectura=True, version=numero),
                           revision=[])


@procesos_bp.route("/<slug>/version/<int:numero>/recuperar", methods=["POST"])
@requiere_admin
def recuperar_version(slug, numero):
    """Recuperar = crear una versión nueva con el contenido de la vieja. La
    versión actual queda en el historial."""
    c = _circuito_o_404(slug)
    v = CircuitoVersion.query.filter_by(circuito_id=c.id, numero=numero).first_or_404()
    contenido = json.loads(v.contenido)
    anterior_borrador = c.contenido
    ultima = json.loads(c.ultima_version.contenido) if c.ultima_version else None
    if ultima != anterior_borrador:
        # El borrador tenía cambios sin versión: se guardan antes de pisarlos.
        db.session.add(CircuitoVersion(circuito_id=c.id, numero=c.ultima_version.numero + 1 if c.ultima_version else 1,
                                       contenido=c.borrador, motivo="Cambios sin guardar antes de recuperar la "
                                                                    f"versión {numero}",
                                       cambios=json.dumps(logica.cambios_entre(ultima, anterior_borrador), ensure_ascii=False)))
        db.session.flush()
        db.session.refresh(c)
    nuevo_numero = c.ultima_version.numero + 1
    db.session.add(CircuitoVersion(circuito_id=c.id, numero=nuevo_numero, contenido=v.contenido, importante=True,
                                   motivo=f"Recuperada la versión {numero}. " + (request.form.get("motivo") or "").strip()[:500],
                                   cambios=json.dumps(logica.cambios_entre(anterior_borrador, contenido), ensure_ascii=False)))
    c.borrador = v.contenido
    c.borrador_actualizado = datetime.now(timezone.utc)
    _auditar("circuito", c.id, "versión recuperada", despues=f"versión {numero} → nueva versión {nuevo_numero}")
    db.session.commit()
    flash(f"Se recuperó la versión {numero} como versión {nuevo_numero}. Lo anterior sigue en el historial.", "ok")
    return redirect(url_for("procesos.editor", slug=slug))


# ------------------------------------------------------------- exportación --

@procesos_bp.route("/<slug>/informe")
@requiere_admin
def informe(slug):
    c = _circuito_o_404(slug)
    docs = recursos.documentos_por_id()
    contenido = c.contenido
    fuentes = {n["id"]: [x for x in (logica.enlace_fuente(f, docs) for f in n["fuentes"]) if x] for n in contenido["nodos"]}
    return render_template("procesos/informe.html", c=c, contenido=contenido, fuentes=fuentes, revision=_revision(c),
                           comentarios=_comentarios_por_elemento(c), tipos=logica.TIPOS_BLOQUE, estados=logica.ESTADOS,
                           soportes=logica.SOPORTES, sistemas=logica.SISTEMAS, funciones=logica.FUNCIONES_RESPONSABLE,
                           tipos_comentario=TIPOS_COMENTARIO, rangos=_rangos_dict(), tipos_flecha=logica.TIPOS_FLECHA,
                           datos=_datos_editor(c, contenido, solo_lectura=True), versiones=list(reversed(c.versiones)))


@procesos_bp.route("/<slug>/exportar.json")
@requiere_admin
def exportar_json(slug):
    c = _circuito_o_404(slug)
    salida = {"circuito": {"nombre": c.nombre, "clase": c.clase, "descripcion": c.descripcion},
              "contenido": c.contenido,
              "comentarios": [{"elemento": x.elemento_id, "tipo": x.tipo, "texto": x.texto, "resuelto": x.resuelto}
                              for x in c.comentarios],
              "exportado": datetime.now(timezone.utc).isoformat()}
    respuesta = jsonify(salida)
    respuesta.headers["Content-Disposition"] = f'attachment; filename="{c.slug}.json"'
    return respuesta


# -------------------------------------------------------------- comparación --

@procesos_bp.route("/comparar")
@requiere_admin
def comparar():
    hospitales = Circuito.query.filter_by(clase="hospital").order_by(Circuito.nombre).all()
    oficiales = Circuito.query.filter_by(clase="oficial").order_by(Circuito.nombre).all()
    h = Circuito.query.filter_by(slug=request.args.get("hospital"), clase="hospital").first() or (hospitales[0] if hospitales else None)
    o = Circuito.query.filter_by(slug=request.args.get("oficial"), clase="oficial").first() or (oficiales[0] if oficiales else None)
    filas_oficial, filas_hospital = [], []
    if h and o:
        hn, on = h.contenido["nodos"], o.contenido["nodos"]
        por_oficial = {}
        for n in hn:
            corr = n.get("correspondencia") or {}
            if corr.get("circuito") == o.slug and corr.get("nodo"):
                por_oficial.setdefault(corr["nodo"], []).append(n)
        ids_oficiales = {n["id"] for n in on}
        for n in on:
            if n["tipo"] in ("observacion",):
                continue
            filas_oficial.append({"oficial": n, "hospital": por_oficial.get(n["id"], [])})
        for n in hn:
            corr = n.get("correspondencia") or {}
            vinculado = corr.get("circuito") == o.slug and corr.get("nodo") in ids_oficiales
            filas_hospital.append({"nodo": n, "relacion": corr.get("relacion") or ("" if vinculado else "sin_relacion"),
                                   "oficial": next((x for x in on if vinculado and x["id"] == corr.get("nodo")), None),
                                   "nota": corr.get("nota", "")})
    return render_template("procesos/comparar.html", hospitales=hospitales, oficiales=oficiales, h=h, o=o,
                           filas_oficial=filas_oficial, filas_hospital=filas_hospital, estados=logica.ESTADOS,
                           soportes=logica.SOPORTES, sistemas=logica.SISTEMAS, relaciones=logica.RELACIONES,
                           tipos=logica.TIPOS_BLOQUE)


# ------------------------------------------------------------------- montos --

def _decimal(valor):
    valor = (valor or "").strip().replace("$", "").replace(" ", "")
    if not valor:
        return None
    # "5.850.000" o "5850000" o "5.850.000,50"
    valor = valor.replace(".", "").replace(",", ".")
    try:
        d = Decimal(valor)
    except InvalidOperation:
        raise ValueError("Importe inválido")
    if d < 0:
        raise ValueError("Importe negativo")
    return d


def _fecha(valor):
    valor = (valor or "").strip()
    return date.fromisoformat(valor) if valor else None


@procesos_bp.route("/montos", methods=["GET", "POST"])
@requiere_admin
def montos():
    docs = recursos.documentos_por_id()
    editar = db.session.get(RangoMonto, request.args.get("editar", type=int)) if request.args.get("editar") else None
    if request.method == "POST":
        r = db.session.get(RangoMonto, request.form.get("id", type=int)) if request.form.get("id") else RangoMonto()
        if r is None:
            abort(404)
        antes = r.como_dict() if r.id else {}
        try:
            r.nombre = (request.form.get("nombre") or "").strip()[:200]
            r.minimo = _decimal(request.form.get("minimo"))
            r.maximo = _decimal(request.form.get("maximo"))
            r.vigencia_desde = _fecha(request.form.get("vigencia_desde"))
            r.vigencia_hasta = _fecha(request.form.get("vigencia_hasta"))
        except ValueError:
            flash("Revisá los importes y las fechas.", "error")
            return redirect(url_for("procesos.montos"))
        if not r.nombre:
            flash("El rango necesita un nombre.", "error")
            return redirect(url_for("procesos.montos"))
        if r.minimo is not None and r.maximo is not None and r.minimo > r.maximo:
            flash("El importe mínimo no puede ser mayor que el máximo.", "error")
            return redirect(url_for("procesos.montos"))
        r.moneda = (request.form.get("moneda") or "ARS").strip()[:10]
        r.condicion = (request.form.get("condicion") or "").strip()[:2000]
        r.autorizacion = (request.form.get("autorizacion") or "").strip()[:2000]
        r.documentacion = (request.form.get("documentacion") or "").strip()[:2000]
        fuente = request.form.get("fuente_doc") or ""
        r.fuente_doc = fuente if fuente in docs else ""
        r.fuente_punto = (request.form.get("fuente_punto") or "").strip()[:200]
        estado = request.form.get("estado")
        r.estado = estado if estado in ESTADOS_RANGO else "pendiente"
        if r.estado == "verificado" and not r.fuente_doc:
            r.estado = "pendiente"
            flash("Un rango sin fuente documental no puede quedar como verificado: quedó pendiente.", "error")
        if not r.id:
            db.session.add(r)
        db.session.flush()
        _auditar("rango", r.id, "editado" if antes else "creado", antes, r.como_dict(),
                 motivo=(request.form.get("motivo") or "").strip()[:500])
        db.session.commit()
        flash("Rango guardado.", "ok")
        return redirect(url_for("procesos.montos"))
    rangos = RangoMonto.query.order_by(RangoMonto.nombre).all()
    dicts = [r.como_dict() for r in rangos]
    historial = AuditoriaProceso.query.filter_by(entidad="rango").order_by(AuditoriaProceso.creado.desc()).limit(50).all()
    return render_template("procesos/montos.html", rangos=rangos, docs=docs, estados=ESTADOS_RANGO, editar=editar,
                           discrepancias=logica.discrepancias_de_rangos(dicts), historial=historial)


# ------------------------------------------------------------- relevamiento --

PRESENTACION = {
    "nomenclador": {
        "objetivo": "Facilitar la consulta, identificación y comparación de artículos y sus equivalencias.",
        "endpoint": "nomenclador",
        "preguntas": ["¿Les resulta útil?", "¿Qué información agregarían?",
                      "¿Qué dificultades encuentran al buscar productos?", "¿Qué información les gustaría ver?",
                      "¿Qué otras funcionalidades necesitarían?"],
    },
    "proveedores": {
        "objetivo": "Reunir lo que un proveedor necesita para participar: requisitos, inscripción y guías oficiales.",
        "endpoint": "ui.recursos_proveedores",
        "preguntas": ["¿Qué documentación debería estar disponible?", "¿Qué consultas hacen habitualmente los proveedores?",
                      "¿Qué información necesitan encontrar?", "¿Qué dificultades se repiten?",
                      "¿Qué recursos ayudarían a comunicarse con los proveedores?"],
    },
    "centro": {
        "objetivo": "Reunir en un solo lugar recursos de consulta, documentación, procedimientos, instructivos y "
                    "herramientas.",
        "endpoint": "ui.portal_inicio",
        "preguntas": ["¿Qué documentación consultan más?", "¿Qué información les cuesta encontrar?",
                      "¿Qué procedimientos necesitarían explicados paso a paso?", "¿Qué consultas se repiten?",
                      "¿Qué información serviría a otros sectores?", "¿Qué recursos les facilitarían el trabajo diario?"],
    },
}


def _url_segura(endpoint):
    try:
        if endpoint == "nomenclador":
            from app.models import EquivalenciaArticulo, Tema
            tema = Tema.query.join(EquivalenciaArticulo, EquivalenciaArticulo.tema_id == Tema.id).first()
            return url_for("ui.ver_equivalencias", tema_slug=tema.slug) if tema else ""
        return url_for(endpoint)
    except Exception:  # noqa: BLE001 — si la ruta no existe, la tarjeta va sin enlace
        return ""


@procesos_bp.route("/relevamiento", methods=["GET", "POST"])
@requiere_admin
def relevamiento():
    if request.method == "POST":
        texto = (request.form.get("texto") or "").strip()[:4000]
        if not texto:
            flash("Escribí la respuesta o sugerencia.", "error")
            return redirect(url_for("procesos.relevamiento") + "#registrar")
        recurso = request.form.get("recurso")
        clase = request.form.get("clase")
        s = SugerenciaRelevamiento(
            recurso=recurso if recurso in RECURSOS_SUGERENCIA else "otro",
            pregunta=(request.form.get("pregunta") or "").strip()[:500], texto=texto,
            clase=clase if clase in CLASES_SUGERENCIA else "necesidad",
            reunion=(request.form.get("reunion") or "").strip()[:120])
        db.session.add(s)
        db.session.flush()
        _auditar("sugerencia", s.id, "registrada", despues=texto)
        db.session.commit()
        flash("Registrado. Queda «Sin evaluar» hasta que decidas qué hacer.", "ok")
        return redirect(url_for("procesos.relevamiento", recurso=s.recurso) + "#registrar")
    filtro_estado = request.args.get("estado") or ""
    filtro_recurso = request.args.get("recurso_filtro") or ""
    q = SugerenciaRelevamiento.query
    if filtro_estado in ESTADOS_SUGERENCIA:
        q = q.filter_by(estado=filtro_estado)
    if filtro_recurso in RECURSOS_SUGERENCIA:
        q = q.filter_by(recurso=filtro_recurso)
    tarjetas = {k: dict(v, url=_url_segura(v["endpoint"])) for k, v in PRESENTACION.items()}
    return render_template("procesos/relevamiento.html", sugerencias=q.order_by(SugerenciaRelevamiento.creado.desc()).all(),
                           tarjetas=tarjetas, recursos_s=RECURSOS_SUGERENCIA, clases_s=CLASES_SUGERENCIA,
                           estados_s=ESTADOS_SUGERENCIA, filtro_estado=filtro_estado, filtro_recurso=filtro_recurso,
                           recurso_activo=request.args.get("recurso") or "nomenclador")


@procesos_bp.route("/relevamiento/<int:sugerencia_id>", methods=["POST"])
@requiere_admin
def evaluar_sugerencia(sugerencia_id):
    s = db.session.get(SugerenciaRelevamiento, sugerencia_id) or abort(404)
    antes = {"estado": s.estado, "clase": s.clase, "nota": s.nota}
    if request.form.get("estado") in ESTADOS_SUGERENCIA:
        s.estado = request.form["estado"]
    if request.form.get("clase") in CLASES_SUGERENCIA:
        s.clase = request.form["clase"]
    if "nota" in request.form:
        s.nota = request.form["nota"].strip()[:2000]
    _auditar("sugerencia", s.id, "evaluada", antes, {"estado": s.estado, "clase": s.clase, "nota": s.nota})
    db.session.commit()
    flash("Sugerencia actualizada.", "ok")
    return redirect(url_for("procesos.relevamiento") + f"#s{s.id}")
