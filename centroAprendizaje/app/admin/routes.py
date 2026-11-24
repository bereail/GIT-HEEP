import json
import os
from datetime import datetime, timezone

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

from app import csrf, recursos
from app.admin.auth import contrasena_correcta, requiere_admin, sesion_admin_activa
from app.extensions import db
from app.models import (
    Categoria,
    Consulta,
    EntradaGlosario,
    Feedback,
    MensajeConsulta,
    PasoIntroductorio,
    Situacion,
    Tarea,
    Tema,
    Tutorial,
)
from app.models.consulta import ESTADOS_CONSULTA
from app.models.feedback import CATEGORIAS_FEEDBACK
from app.seguridad import ip_cliente, limitador
from app.services import estadisticas, feedback_stats, notificaciones
from app.services.textutil import lineas_a_lista, slugify

admin_bp = Blueprint("admin", __name__, url_prefix="/admin", template_folder="../templates/admin")

EXTENSIONES_PERMITIDAS = {"jpg", "jpeg", "png", "gif", "webp"}


# ------------------------------------------------------------------- auth ---

@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if sesion_admin_activa():
        return redirect(url_for("admin.dashboard"))
    error = None
    if request.method == "POST":
        # Fuerza bruta: 5 intentos fallidos por IP cada 15 minutos.
        clave = f"login-admin:{ip_cliente()}"
        if limitador.bloqueado(clave, 5, 15 * 60):
            error = "Demasiados intentos fallidos. Esperá 15 minutos y probá de nuevo."
            return render_template("admin/login.html", error=error), 429
        if contrasena_correcta(request.form.get("contrasena", "")):
            limitador.limpiar(clave)
            session.clear()  # sesión nueva al entrar (evita fijación de sesión)
            session.permanent = True
            session["admin_autenticado"] = True
            return redirect(url_for("admin.dashboard"))
        limitador.registrar(clave, 15 * 60)
        error = "Contraseña incorrecta."
    return render_template("admin/login.html", error=error)


@admin_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("admin.login"))


# -------------------------------------------------------------- utilidades --

def _tema_o_404(tema_slug):
    tema = Tema.query.filter_by(slug=tema_slug).first()
    if not tema:
        abort(404)
    return tema


def _categoria_o_404(tema, categoria_slug):
    categoria = Categoria.query.filter_by(tema_id=tema.id, slug=categoria_slug).first()
    if not categoria:
        abort(404)
    return categoria


def _tutorial_o_404(categoria, tutorial_slug):
    tutorial = Tutorial.query.filter_by(categoria_id=categoria.id, slug=tutorial_slug).first()
    if not tutorial:
        abort(404)
    return tutorial


def _situacion_o_404(tema, situacion_slug):
    situacion = Situacion.query.filter_by(tema_id=tema.id, slug=situacion_slug).first()
    if not situacion:
        abort(404)
    return situacion


def _tarea_o_404(tema, tarea_slug):
    tarea = Tarea.query.filter_by(tema_id=tema.id, slug=tarea_slug).first()
    if not tarea:
        abort(404)
    return tarea


def _slug_unico(modelo, tema_id, slug_pedido, columna_tema="tema_id", excluir_id=None, **filtros):
    """Si `slug_pedido` ya existe para el mismo tema (o categoría), le agrega
    un sufijo numérico hasta que quede libre."""
    base = slug_pedido
    intento = 1
    while True:
        consulta = modelo.query.filter_by(**{columna_tema: tema_id}, slug=slug_pedido, **filtros)
        if excluir_id is not None:
            consulta = consulta.filter(modelo.id != excluir_id)
        if not consulta.first():
            return slug_pedido
        intento += 1
        slug_pedido = f"{base}-{intento}"


def _mover(items_ordenados, item, delta):
    """Intercambia el campo `orden` de `item` con su vecino inmediato
    (delta=-1 sube, delta=1 baja) y guarda. `items_ordenados` ya debe venir
    ordenado por `orden`."""
    posicion = items_ordenados.index(item)
    vecino_pos = posicion + delta
    if 0 <= vecino_pos < len(items_ordenados):
        vecino = items_ordenados[vecino_pos]
        item.orden, vecino.orden = vecino.orden, item.orden
        db.session.commit()


# ----------------------------------------------------------------- panel ----

@admin_bp.route("/")
@requiere_admin
def dashboard():
    temas = Tema.query.order_by(Tema.orden).all()
    from app.models.revision_nomenclador import ObservacionNomenclador, RevisorNomenclador

    revision = {
        "observaciones": ObservacionNomenclador.query.filter(
            (ObservacionNomenclador.texto != "") | ObservacionNomenclador.validacion.isnot(None)).count(),
        "revisores": RevisorNomenclador.query.filter_by(activo=True).count(),
        "ultima": ObservacionNomenclador.query.order_by(ObservacionNomenclador.actualizado_en.desc()).first(),
    }
    return render_template("admin/dashboard.html", temas=temas, dependencias=_auditoria_dependencias(), revision=revision)


def _auditoria_dependencias():
    """Lo último que dejó la revisión mensual de dependencias del servidor
    (scripts/auditar_dependencias.sh) en instance/auditoria_dependencias.txt:
    la primera línea es la fecha; el resto, la salida de pip-audit."""
    ruta = os.path.join(current_app.instance_path, "auditoria_dependencias.txt")
    try:
        with open(ruta, encoding="utf-8") as f:
            fecha, _, detalle = f.read().partition("\n")
    except OSError:
        return None
    return {"fecha": fecha.strip(), "ok": "No known vulnerabilities found" in detalle, "detalle": detalle.strip()}


# ------------------------------------------------------------ estadísticas --

@admin_bp.route("/estadisticas")
@requiere_admin
def estadisticas_vista():
    temas = Tema.query.order_by(Tema.orden).all()
    tema_actual = _tema_o_404(request.args["tema"]) if request.args.get("tema") else None
    datos = estadisticas.resumen(tema_id=tema_actual.id if tema_actual else None)
    return render_template("admin/estadisticas.html", temas=temas, tema_actual=tema_actual, datos=datos)


# ---------------------------------------------------------------- consultas --

@admin_bp.route("/consultas")
@requiere_admin
def consultas():
    estado_filtro = request.args.get("estado", "abierta")
    query = Consulta.query.order_by(Consulta.actualizada_en.desc())
    if estado_filtro in ESTADOS_CONSULTA:
        query = query.filter_by(estado=estado_filtro)
    todas = query.all()
    return render_template(
        "admin/consultas.html",
        consultas=todas,
        estado_filtro=estado_filtro,
        estados=ESTADOS_CONSULTA,
        cantidad_abiertas=Consulta.query.filter_by(estado="abierta").count(),
        cantidad_no_leidas=sum(1 for c in Consulta.query.all() if c.no_leida_por_admin),
    )


@admin_bp.route("/consultas/<token>")
@requiere_admin
def consulta_detalle(token):
    consulta = Consulta.query.filter_by(token=token).first_or_404()
    consulta.vista_por_admin_en = datetime.now(timezone.utc)
    db.session.commit()
    return render_template("admin/consulta_detalle.html", consulta=consulta)


@admin_bp.route("/consultas/<token>/responder", methods=["POST"])
@requiere_admin
def consulta_responder(token):
    consulta = Consulta.query.filter_by(token=token).first_or_404()
    mensaje = (request.form.get("mensaje") or "").strip()
    if mensaje:
        db.session.add(MensajeConsulta(consulta_id=consulta.id, autor="admin", cuerpo=mensaje))
        consulta.estado = "respondida"
        consulta.vista_por_admin_en = datetime.now(timezone.utc)
        db.session.commit()
        if notificaciones.notificar_respuesta_consulta(consulta, mensaje):
            flash("Respuesta enviada y notificada por mail.", "ok")
        else:
            flash("Respuesta enviada.", "ok")
    return redirect(url_for("admin.consulta_detalle", token=token))


@admin_bp.route("/consultas/<token>/estado", methods=["POST"])
@requiere_admin
def consulta_cambiar_estado(token):
    consulta = Consulta.query.filter_by(token=token).first_or_404()
    nuevo_estado = request.form.get("estado")
    if nuevo_estado in ESTADOS_CONSULTA:
        consulta.estado = nuevo_estado
        db.session.commit()
        flash(f"Consulta marcada como \"{ESTADOS_CONSULTA[nuevo_estado]}\".", "ok")
    return redirect(request.referrer or url_for("admin.consultas"))


# ------------------------------------------------------------------ feedback --

@admin_bp.route("/feedback")
@requiere_admin
def feedback():
    temas = Tema.query.order_by(Tema.orden).all()
    tema_actual = _tema_o_404(request.args["tema"]) if request.args.get("tema") else None
    categoria_filtro = request.args.get("categoria") or None
    if categoria_filtro not in CATEGORIAS_FEEDBACK:
        categoria_filtro = None
    puntuacion_filtro = request.args.get("puntuacion")
    puntuacion_filtro = int(puntuacion_filtro) if puntuacion_filtro in {"1", "2", "3", "4", "5"} else None

    datos = feedback_stats.resumen(tema_id=tema_actual.id if tema_actual else None, categoria=categoria_filtro)
    items = datos["items"]
    if puntuacion_filtro:
        items = [f for f in items if f.puntuacion == puntuacion_filtro]

    return render_template(
        "admin/feedback.html",
        temas=temas,
        tema_actual=tema_actual,
        categorias=CATEGORIAS_FEEDBACK,
        categoria_filtro=categoria_filtro,
        puntuacion_filtro=puntuacion_filtro,
        datos=datos,
        items=items,
    )


@admin_bp.route("/feedback/<int:feedback_id>/revisar", methods=["POST"])
@requiere_admin
def feedback_revisar(feedback_id):
    item = Feedback.query.get_or_404(feedback_id)
    item.revisado = not item.revisado
    db.session.commit()
    return redirect(request.referrer or url_for("admin.feedback"))


@admin_bp.route("/consultas/<token>/cerrar", methods=["POST"])
@requiere_admin
def consulta_cerrar(token):
    consulta = Consulta.query.filter_by(token=token).first_or_404()
    consulta.estado = "cerrada"
    db.session.commit()
    flash("Consulta cerrada.", "ok")
    return redirect(url_for("admin.consultas"))


# ------------------------------------------------------------------ temas --

@admin_bp.route("/temas/nuevo", methods=["GET", "POST"])
@requiere_admin
def tema_nuevo():
    if request.method == "POST":
        slug = slugify(request.form.get("slug") or request.form["nombre"])
        if Tema.query.filter_by(slug=slug).first():
            flash(f"Ya existe un tema con el slug '{slug}'.", "error")
            return render_template("admin/tema_form.html", tema=None, valores=request.form)
        tema = Tema(
            slug=slug,
            nombre=request.form["nombre"],
            nombre_completo=request.form.get("nombre_completo"),
            organizacion=request.form.get("organizacion"),
            icono=request.form.get("icono") or "🧭",
            descripcion=request.form.get("descripcion"),
            alcance=request.form.get("alcance"),
            recomendaciones=lineas_a_lista(request.form.get("recomendaciones")),
            quickstart_titulo=request.form.get("quickstart_titulo"),
            quickstart_intro=request.form.get("quickstart_intro"),
            quickstart_cierre=request.form.get("quickstart_cierre"),
            orden=int(request.form.get("orden") or 0),
            activo=bool(request.form.get("activo")),
        )
        db.session.add(tema)
        db.session.commit()
        flash(f"Tema '{tema.nombre}' creado.", "ok")
        return redirect(url_for("admin.tema_detalle", tema_slug=tema.slug))
    return render_template("admin/tema_form.html", tema=None, valores=None)


@admin_bp.route("/temas/<tema_slug>")
@requiere_admin
def tema_detalle(tema_slug):
    tema = _tema_o_404(tema_slug)
    return render_template("admin/tema_detalle.html", tema=tema)


@admin_bp.route("/temas/<tema_slug>/editar", methods=["GET", "POST"])
@requiere_admin
def tema_editar(tema_slug):
    tema = _tema_o_404(tema_slug)
    if request.method == "POST":
        tema.nombre = request.form["nombre"]
        tema.nombre_completo = request.form.get("nombre_completo")
        tema.organizacion = request.form.get("organizacion")
        tema.icono = request.form.get("icono") or "🧭"
        tema.descripcion = request.form.get("descripcion")
        tema.alcance = request.form.get("alcance")
        tema.recomendaciones = lineas_a_lista(request.form.get("recomendaciones"))
        tema.quickstart_titulo = request.form.get("quickstart_titulo")
        tema.quickstart_intro = request.form.get("quickstart_intro")
        tema.quickstart_cierre = request.form.get("quickstart_cierre")
        tema.orden = int(request.form.get("orden") or 0)
        tema.activo = bool(request.form.get("activo"))
        db.session.commit()
        flash("Tema actualizado.", "ok")
        return redirect(url_for("admin.tema_detalle", tema_slug=tema.slug))
    return render_template("admin/tema_form.html", tema=tema, valores=None)


@admin_bp.route("/temas/<tema_slug>/eliminar", methods=["POST"])
@requiere_admin
def tema_eliminar(tema_slug):
    tema = _tema_o_404(tema_slug)
    db.session.delete(tema)
    db.session.commit()
    flash(f"Tema '{tema.nombre}' eliminado, junto con todo su contenido.", "ok")
    return redirect(url_for("admin.dashboard"))


# -------------------------------------------------------------- categorías --

@admin_bp.route("/temas/<tema_slug>/categorias/nueva", methods=["GET", "POST"])
@requiere_admin
def categoria_nueva(tema_slug):
    tema = _tema_o_404(tema_slug)
    if request.method == "POST":
        slug = _slug_unico(Categoria, tema.id, slugify(request.form.get("slug") or request.form["titulo"]))
        siguiente_orden = max([c.orden for c in tema.categorias], default=-1) + 1
        categoria = Categoria(
            tema_id=tema.id,
            slug=slug,
            titulo=request.form["titulo"],
            icono=request.form.get("icono") or "📁",
            resumen=request.form.get("resumen"),
            audiencia=request.form.get("audiencia"),
            dificultad=request.form.get("dificultad", "basico"),
            orden=siguiente_orden,
        )
        db.session.add(categoria)
        db.session.commit()
        flash(f"Módulo '{categoria.titulo}' creado.", "ok")
        return redirect(url_for("admin.categoria_detalle", tema_slug=tema.slug, categoria_slug=categoria.slug))
    return render_template("admin/categoria_form.html", tema=tema, categoria=None)


@admin_bp.route("/temas/<tema_slug>/categorias/<categoria_slug>")
@requiere_admin
def categoria_detalle(tema_slug, categoria_slug):
    tema = _tema_o_404(tema_slug)
    categoria = _categoria_o_404(tema, categoria_slug)
    return render_template("admin/categoria_detalle.html", tema=tema, categoria=categoria)


@admin_bp.route("/temas/<tema_slug>/categorias/<categoria_slug>/editar", methods=["GET", "POST"])
@requiere_admin
def categoria_editar(tema_slug, categoria_slug):
    tema = _tema_o_404(tema_slug)
    categoria = _categoria_o_404(tema, categoria_slug)
    if request.method == "POST":
        categoria.titulo = request.form["titulo"]
        categoria.icono = request.form.get("icono") or "📁"
        categoria.resumen = request.form.get("resumen")
        categoria.audiencia = request.form.get("audiencia")
        categoria.dificultad = request.form.get("dificultad", "basico")
        db.session.commit()
        flash("Módulo actualizado.", "ok")
        return redirect(url_for("admin.categoria_detalle", tema_slug=tema.slug, categoria_slug=categoria.slug))
    return render_template("admin/categoria_form.html", tema=tema, categoria=categoria)


@admin_bp.route("/temas/<tema_slug>/categorias/<categoria_slug>/eliminar", methods=["POST"])
@requiere_admin
def categoria_eliminar(tema_slug, categoria_slug):
    tema = _tema_o_404(tema_slug)
    categoria = _categoria_o_404(tema, categoria_slug)
    db.session.delete(categoria)
    db.session.commit()
    flash(f"Módulo '{categoria.titulo}' eliminado.", "ok")
    return redirect(url_for("admin.tema_detalle", tema_slug=tema.slug))


@admin_bp.route("/temas/<tema_slug>/categorias/<categoria_slug>/mover/<direccion>", methods=["POST"])
@requiere_admin
def categoria_mover(tema_slug, categoria_slug, direccion):
    tema = _tema_o_404(tema_slug)
    categoria = _categoria_o_404(tema, categoria_slug)
    _mover(tema.categorias, categoria, -1 if direccion == "subir" else 1)
    return redirect(url_for("admin.tema_detalle", tema_slug=tema.slug))


# -------------------------------------------------------------- tutoriales --

def _textos_json(tutorial, valores):
    """Texto a mostrar en los textarea de 'Bloques' y 'Quiz': lo que el
    usuario tenía tipeado si el POST falló, el JSON ya guardado si se está
    editando, o una lista vacía si es un tutorial nuevo."""
    if valores is not None:
        return valores.get("bloques", "[]"), valores.get("quiz", "[]")
    if tutorial is not None:
        return (
            json.dumps(tutorial.bloques or [], ensure_ascii=False, indent=2),
            json.dumps(tutorial.quiz or [], ensure_ascii=False, indent=2),
        )
    return "[]", "[]"


@admin_bp.route("/temas/<tema_slug>/categorias/<categoria_slug>/tutoriales/nuevo", methods=["GET", "POST"])
@requiere_admin
def tutorial_nuevo(tema_slug, categoria_slug):
    tema = _tema_o_404(tema_slug)
    categoria = _categoria_o_404(tema, categoria_slug)
    if request.method == "POST":
        ok, bloques, quiz = _leer_json_tutorial(request.form)
        if not ok:
            bloques_texto, quiz_texto = _textos_json(None, request.form)
            return render_template(
                "admin/tutorial_form.html", tema=tema, categoria=categoria, tutorial=None,
                valores=request.form, bloques_texto=bloques_texto, quiz_texto=quiz_texto,
            )
        slug = _slug_unico(Tutorial, categoria.id, slugify(request.form.get("slug") or request.form["titulo"]), columna_tema="categoria_id")
        siguiente_orden = max([t.orden for t in categoria.tutoriales], default=-1) + 1
        tutorial = Tutorial(
            categoria_id=categoria.id,
            slug=slug,
            titulo=request.form["titulo"],
            minutos=int(request.form.get("minutos") or 5),
            dificultad=request.form.get("dificultad", "basico"),
            orden=siguiente_orden,
            bloques=bloques,
            quiz=quiz,
        )
        db.session.add(tutorial)
        db.session.commit()
        flash(f"Tutorial '{tutorial.titulo}' creado.", "ok")
        return redirect(url_for("admin.categoria_detalle", tema_slug=tema.slug, categoria_slug=categoria.slug))
    bloques_texto, quiz_texto = _textos_json(None, None)
    return render_template(
        "admin/tutorial_form.html", tema=tema, categoria=categoria, tutorial=None,
        valores=None, bloques_texto=bloques_texto, quiz_texto=quiz_texto,
    )


@admin_bp.route("/temas/<tema_slug>/categorias/<categoria_slug>/tutoriales/<tutorial_slug>/editar", methods=["GET", "POST"])
@requiere_admin
def tutorial_editar(tema_slug, categoria_slug, tutorial_slug):
    tema = _tema_o_404(tema_slug)
    categoria = _categoria_o_404(tema, categoria_slug)
    tutorial = _tutorial_o_404(categoria, tutorial_slug)
    if request.method == "POST":
        ok, bloques, quiz = _leer_json_tutorial(request.form)
        if not ok:
            bloques_texto, quiz_texto = _textos_json(tutorial, request.form)
            return render_template(
                "admin/tutorial_form.html", tema=tema, categoria=categoria, tutorial=tutorial,
                valores=request.form, bloques_texto=bloques_texto, quiz_texto=quiz_texto,
            )
        tutorial.titulo = request.form["titulo"]
        tutorial.minutos = int(request.form.get("minutos") or 5)
        tutorial.dificultad = request.form.get("dificultad", "basico")
        tutorial.bloques = bloques
        tutorial.quiz = quiz
        db.session.commit()
        flash("Tutorial actualizado.", "ok")
        return redirect(url_for("admin.categoria_detalle", tema_slug=tema.slug, categoria_slug=categoria.slug))
    bloques_texto, quiz_texto = _textos_json(tutorial, None)
    return render_template(
        "admin/tutorial_form.html", tema=tema, categoria=categoria, tutorial=tutorial,
        valores=None, bloques_texto=bloques_texto, quiz_texto=quiz_texto,
    )


@admin_bp.route("/temas/<tema_slug>/categorias/<categoria_slug>/tutoriales/<tutorial_slug>/eliminar", methods=["POST"])
@requiere_admin
def tutorial_eliminar(tema_slug, categoria_slug, tutorial_slug):
    tema = _tema_o_404(tema_slug)
    categoria = _categoria_o_404(tema, categoria_slug)
    tutorial = _tutorial_o_404(categoria, tutorial_slug)
    db.session.delete(tutorial)
    db.session.commit()
    flash(f"Tutorial '{tutorial.titulo}' eliminado.", "ok")
    return redirect(url_for("admin.categoria_detalle", tema_slug=tema.slug, categoria_slug=categoria.slug))


@admin_bp.route("/temas/<tema_slug>/categorias/<categoria_slug>/tutoriales/<tutorial_slug>/mover/<direccion>", methods=["POST"])
@requiere_admin
def tutorial_mover(tema_slug, categoria_slug, tutorial_slug, direccion):
    tema = _tema_o_404(tema_slug)
    categoria = _categoria_o_404(tema, categoria_slug)
    tutorial = _tutorial_o_404(categoria, tutorial_slug)
    _mover(categoria.tutoriales, tutorial, -1 if direccion == "subir" else 1)
    return redirect(url_for("admin.categoria_detalle", tema_slug=tema.slug, categoria_slug=categoria.slug))


def _leer_json_tutorial(formulario):
    """Valida los dos textarea de JSON (bloques y quiz) del formulario de
    tutorial. Devuelve (ok, bloques, quiz); si ok=False ya se encargó de
    mostrar el error con flash."""
    try:
        bloques = json.loads(formulario.get("bloques") or "[]")
        if not isinstance(bloques, list):
            raise ValueError("los bloques deben ser una lista")
    except (json.JSONDecodeError, ValueError) as err:
        flash(f"El JSON de 'Bloques' no es válido: {err}", "error")
        return False, None, None
    try:
        quiz = json.loads(formulario.get("quiz") or "[]")
        if not isinstance(quiz, list):
            raise ValueError("el quiz debe ser una lista")
    except (json.JSONDecodeError, ValueError) as err:
        flash(f"El JSON de 'Quiz' no es válido: {err}", "error")
        return False, None, None
    return True, bloques, quiz


@admin_bp.route("/tutoriales/previsualizar", methods=["POST"])
@csrf.exempt
@requiere_admin
def tutorial_previsualizar():
    """Devuelve el HTML renderizado de una lista de bloques, para la vista
    previa en vivo del editor. No modifica nada — por eso está exento de
    CSRF (igual sigue exigiendo la sesión de administrador)."""
    datos = request.get_json(silent=True) or {}
    try:
        bloques = json.loads(datos.get("bloques") or "[]")
        if not isinstance(bloques, list):
            raise ValueError
    except (json.JSONDecodeError, ValueError, TypeError):
        return jsonify({"error": "JSON inválido"}), 400
    tema_slug = datos.get("tema_slug", "")
    img_base = url_for("static", filename=f"img/{tema_slug}")
    html = render_template("admin/_previsualizacion.html", bloques=bloques, img_base=img_base)
    return jsonify({"html": html})


# --------------------------------------------------------------- glosario --

@admin_bp.route("/temas/<tema_slug>/glosario/nueva", methods=["GET", "POST"])
@requiere_admin
def glosario_nueva(tema_slug):
    tema = _tema_o_404(tema_slug)
    if request.method == "POST":
        entrada = EntradaGlosario(
            tema_id=tema.id,
            termino=request.form["termino"],
            definicion=request.form["definicion"],
            modulo=request.form.get("modulo"),
            uso=request.form.get("uso"),
        )
        db.session.add(entrada)
        db.session.commit()
        flash(f"Término '{entrada.termino}' agregado al glosario.", "ok")
        return redirect(url_for("admin.tema_detalle", tema_slug=tema.slug))
    return render_template("admin/glosario_form.html", tema=tema, entrada=None)


@admin_bp.route("/temas/<tema_slug>/glosario/<int:entrada_id>/editar", methods=["GET", "POST"])
@requiere_admin
def glosario_editar(tema_slug, entrada_id):
    tema = _tema_o_404(tema_slug)
    entrada = EntradaGlosario.query.filter_by(tema_id=tema.id, id=entrada_id).first_or_404()
    if request.method == "POST":
        entrada.termino = request.form["termino"]
        entrada.definicion = request.form["definicion"]
        entrada.modulo = request.form.get("modulo")
        entrada.uso = request.form.get("uso")
        db.session.commit()
        flash("Término actualizado.", "ok")
        return redirect(url_for("admin.tema_detalle", tema_slug=tema.slug))
    return render_template("admin/glosario_form.html", tema=tema, entrada=entrada)


@admin_bp.route("/temas/<tema_slug>/glosario/<int:entrada_id>/eliminar", methods=["POST"])
@requiere_admin
def glosario_eliminar(tema_slug, entrada_id):
    tema = _tema_o_404(tema_slug)
    entrada = EntradaGlosario.query.filter_by(tema_id=tema.id, id=entrada_id).first_or_404()
    db.session.delete(entrada)
    db.session.commit()
    flash("Término eliminado.", "ok")
    return redirect(url_for("admin.tema_detalle", tema_slug=tema.slug))


# ------------------------------------------------------------- situaciones --

def _opciones_tutoriales(tema):
    """[(valor, etiqueta), ...] para el <select> de tutorial vinculado."""
    opciones = [("", "— Ninguno —")]
    for categoria in tema.categorias:
        for tutorial in categoria.tutoriales:
            opciones.append((f"{categoria.slug}/{tutorial.slug}", f"{categoria.titulo} → {tutorial.titulo}"))
    return opciones


def _tutorial_desde_valor(tema, valor):
    if not valor:
        return None
    categoria_slug, _, tutorial_slug = valor.partition("/")
    categoria = Categoria.query.filter_by(tema_id=tema.id, slug=categoria_slug).first()
    if not categoria:
        return None
    return Tutorial.query.filter_by(categoria_id=categoria.id, slug=tutorial_slug).first()


@admin_bp.route("/temas/<tema_slug>/situaciones/nueva", methods=["GET", "POST"])
@requiere_admin
def situacion_nueva(tema_slug):
    tema = _tema_o_404(tema_slug)
    if request.method == "POST":
        tutorial = _tutorial_desde_valor(tema, request.form.get("tutorial"))
        slug = _slug_unico(Situacion, tema.id, slugify(request.form.get("slug") or request.form["situacion"]))
        siguiente_orden = max([s.orden for s in tema.situaciones], default=-1) + 1
        situacion = Situacion(
            tema_id=tema.id,
            slug=slug,
            situacion=request.form["situacion"],
            descripcion=request.form.get("descripcion"),
            causa=request.form.get("causa"),
            solucion=request.form.get("solucion"),
            notas_adicionales=request.form.get("notas_adicionales"),
            categoria_libre=request.form.get("categoria_libre") or None,
            tutorial_id=tutorial.id if tutorial else None,
            verificado=bool(request.form.get("verificado")),
            orden=siguiente_orden,
        )
        db.session.add(situacion)
        db.session.commit()
        flash("Situación agregada.", "ok")
        return redirect(url_for("admin.tema_detalle", tema_slug=tema.slug))
    return render_template(
        "admin/situacion_form.html", tema=tema, situacion=None, opciones_tutoriales=_opciones_tutoriales(tema)
    )


@admin_bp.route("/temas/<tema_slug>/situaciones/<situacion_slug>/editar", methods=["GET", "POST"])
@requiere_admin
def situacion_editar(tema_slug, situacion_slug):
    tema = _tema_o_404(tema_slug)
    situacion = _situacion_o_404(tema, situacion_slug)
    if request.method == "POST":
        tutorial = _tutorial_desde_valor(tema, request.form.get("tutorial"))
        situacion.situacion = request.form["situacion"]
        situacion.descripcion = request.form.get("descripcion")
        situacion.causa = request.form.get("causa")
        situacion.solucion = request.form.get("solucion")
        situacion.notas_adicionales = request.form.get("notas_adicionales")
        situacion.categoria_libre = request.form.get("categoria_libre") or None
        situacion.tutorial_id = tutorial.id if tutorial else None
        situacion.verificado = bool(request.form.get("verificado"))
        db.session.commit()
        flash("Situación actualizada.", "ok")
        return redirect(url_for("admin.tema_detalle", tema_slug=tema.slug))
    valor_actual = f"{situacion.tutorial.categoria.slug}/{situacion.tutorial.slug}" if situacion.tutorial else ""
    return render_template(
        "admin/situacion_form.html",
        tema=tema,
        situacion=situacion,
        opciones_tutoriales=_opciones_tutoriales(tema),
        valor_actual=valor_actual,
    )


@admin_bp.route("/temas/<tema_slug>/situaciones/<situacion_slug>/eliminar", methods=["POST"])
@requiere_admin
def situacion_eliminar(tema_slug, situacion_slug):
    tema = _tema_o_404(tema_slug)
    situacion = _situacion_o_404(tema, situacion_slug)
    db.session.delete(situacion)
    db.session.commit()
    flash("Situación eliminada.", "ok")
    return redirect(url_for("admin.tema_detalle", tema_slug=tema.slug))


@admin_bp.route("/temas/<tema_slug>/situaciones/<situacion_slug>/mover/<direccion>", methods=["POST"])
@requiere_admin
def situacion_mover(tema_slug, situacion_slug, direccion):
    tema = _tema_o_404(tema_slug)
    situacion = _situacion_o_404(tema, situacion_slug)
    _mover(tema.situaciones, situacion, -1 if direccion == "subir" else 1)
    return redirect(url_for("admin.tema_detalle", tema_slug=tema.slug))


# ------------------------------------------------------------------ tareas --

@admin_bp.route("/temas/<tema_slug>/tareas/nueva", methods=["GET", "POST"])
@requiere_admin
def tarea_nueva(tema_slug):
    tema = _tema_o_404(tema_slug)
    if request.method == "POST":
        tutorial = _tutorial_desde_valor(tema, request.form.get("tutorial"))
        if not tutorial:
            flash("Elegí un tutorial para vincular esta tarea.", "error")
            return render_template(
                "admin/tarea_form.html", tema=tema, tarea=None, opciones_tutoriales=_opciones_tutoriales(tema)
            )
        slug = _slug_unico(Tarea, tema.id, slugify(request.form.get("slug") or request.form["pregunta"]))
        siguiente_orden = max([t.orden for t in tema.tareas], default=-1) + 1
        tarea = Tarea(
            tema_id=tema.id,
            slug=slug,
            pregunta=request.form["pregunta"],
            keywords=lineas_a_lista(request.form.get("keywords")),
            tutorial_id=tutorial.id,
            orden=siguiente_orden,
        )
        db.session.add(tarea)
        db.session.commit()
        flash("Tarea agregada.", "ok")
        return redirect(url_for("admin.tema_detalle", tema_slug=tema.slug))
    return render_template(
        "admin/tarea_form.html", tema=tema, tarea=None, opciones_tutoriales=_opciones_tutoriales(tema)
    )


@admin_bp.route("/temas/<tema_slug>/tareas/<tarea_slug>/editar", methods=["GET", "POST"])
@requiere_admin
def tarea_editar(tema_slug, tarea_slug):
    tema = _tema_o_404(tema_slug)
    tarea = _tarea_o_404(tema, tarea_slug)
    if request.method == "POST":
        tutorial = _tutorial_desde_valor(tema, request.form.get("tutorial"))
        if not tutorial:
            flash("Elegí un tutorial para vincular esta tarea.", "error")
            return render_template(
                "admin/tarea_form.html", tema=tema, tarea=tarea, opciones_tutoriales=_opciones_tutoriales(tema)
            )
        tarea.pregunta = request.form["pregunta"]
        tarea.keywords = lineas_a_lista(request.form.get("keywords"))
        tarea.tutorial_id = tutorial.id
        db.session.commit()
        flash("Tarea actualizada.", "ok")
        return redirect(url_for("admin.tema_detalle", tema_slug=tema.slug))
    valor_actual = f"{tarea.tutorial.categoria.slug}/{tarea.tutorial.slug}"
    return render_template(
        "admin/tarea_form.html",
        tema=tema,
        tarea=tarea,
        opciones_tutoriales=_opciones_tutoriales(tema),
        valor_actual=valor_actual,
    )


@admin_bp.route("/temas/<tema_slug>/tareas/<tarea_slug>/eliminar", methods=["POST"])
@requiere_admin
def tarea_eliminar(tema_slug, tarea_slug):
    tema = _tema_o_404(tema_slug)
    tarea = _tarea_o_404(tema, tarea_slug)
    db.session.delete(tarea)
    db.session.commit()
    flash("Tarea eliminada.", "ok")
    return redirect(url_for("admin.tema_detalle", tema_slug=tema.slug))


@admin_bp.route("/temas/<tema_slug>/tareas/<tarea_slug>/mover/<direccion>", methods=["POST"])
@requiere_admin
def tarea_mover(tema_slug, tarea_slug, direccion):
    tema = _tema_o_404(tema_slug)
    tarea = _tarea_o_404(tema, tarea_slug)
    _mover(tema.tareas, tarea, -1 if direccion == "subir" else 1)
    return redirect(url_for("admin.tema_detalle", tema_slug=tema.slug))


# ------------------------------------------------------- pasos (quickstart) --

@admin_bp.route("/temas/<tema_slug>/quickstart/nuevo", methods=["POST"])
@requiere_admin
def paso_nuevo(tema_slug):
    tema = _tema_o_404(tema_slug)
    tutorial = _tutorial_desde_valor(tema, request.form.get("tutorial"))
    situacion_slug = request.form.get("situacion")
    situacion = _situacion_o_404(tema, situacion_slug) if situacion_slug else None
    siguiente_orden = max([p.orden for p in tema.pasos_introductorios], default=-1) + 1
    paso = PasoIntroductorio(
        tema_id=tema.id,
        orden=siguiente_orden,
        titulo=request.form["titulo"],
        descripcion=request.form.get("descripcion"),
        tutorial_id=tutorial.id if tutorial else None,
        situacion_id=situacion.id if situacion else None,
    )
    db.session.add(paso)
    db.session.commit()
    flash("Paso agregado a la ruta guiada.", "ok")
    return redirect(url_for("admin.tema_detalle", tema_slug=tema.slug))


@admin_bp.route("/temas/<tema_slug>/quickstart/<int:paso_id>/eliminar", methods=["POST"])
@requiere_admin
def paso_eliminar(tema_slug, paso_id):
    tema = _tema_o_404(tema_slug)
    paso = PasoIntroductorio.query.filter_by(tema_id=tema.id, id=paso_id).first_or_404()
    db.session.delete(paso)
    db.session.commit()
    flash("Paso eliminado.", "ok")
    return redirect(url_for("admin.tema_detalle", tema_slug=tema.slug))


@admin_bp.route("/temas/<tema_slug>/quickstart/<int:paso_id>/mover/<direccion>", methods=["POST"])
@requiere_admin
def paso_mover(tema_slug, paso_id, direccion):
    tema = _tema_o_404(tema_slug)
    paso = PasoIntroductorio.query.filter_by(tema_id=tema.id, id=paso_id).first_or_404()
    _mover(tema.pasos_introductorios, paso, -1 if direccion == "subir" else 1)
    return redirect(url_for("admin.tema_detalle", tema_slug=tema.slug))


# ----------------------------------------------------------------- imágenes --

# Primeros bytes de cada formato: la extensión sola no alcanza (un .png puede
# ser en realidad un HTML o un script).
_FIRMAS_IMAGEN = {
    "jpg": (bytes.fromhex("ffd8ff"),),
    "jpeg": (bytes.fromhex("ffd8ff"),),
    "png": (bytes.fromhex("89504e470d0a1a0a"),),
    "gif": (b"GIF87a", b"GIF89a"),
}


def _es_imagen_real(archivo, extension):
    cabecera = archivo.stream.read(12)
    archivo.stream.seek(0)
    if extension == "webp":
        return cabecera[:4] == b"RIFF" and cabecera[8:12] == b"WEBP"
    return any(cabecera.startswith(f) for f in _FIRMAS_IMAGEN[extension])


def _carpeta_imagenes(tema):
    carpeta = os.path.join(current_app.static_folder, "img", tema.slug)
    os.makedirs(carpeta, exist_ok=True)
    return carpeta


@admin_bp.route("/temas/<tema_slug>/imagenes", methods=["GET", "POST"])
@requiere_admin
def imagenes(tema_slug):
    tema = _tema_o_404(tema_slug)
    carpeta = _carpeta_imagenes(tema)
    if request.method == "POST":
        archivo = request.files.get("archivo")
        if not archivo or not archivo.filename:
            flash("Elegí un archivo para subir.", "error")
        else:
            nombre = secure_filename(archivo.filename)
            extension = nombre.rsplit(".", 1)[-1].lower() if "." in nombre else ""
            if extension not in EXTENSIONES_PERMITIDAS or not _es_imagen_real(archivo, extension):
                flash("Solo se permiten imágenes JPG, PNG, GIF o WEBP.", "error")
            else:
                archivo.save(os.path.join(carpeta, nombre))
                flash(f"Imagen '{nombre}' subida. Usá ese nombre en el campo 'image' del bloque.", "ok")
        return redirect(url_for("admin.imagenes", tema_slug=tema.slug))
    archivos = sorted(os.listdir(carpeta)) if os.path.isdir(carpeta) else []
    return render_template("admin/imagenes.html", tema=tema, archivos=archivos)


@admin_bp.route("/temas/<tema_slug>/imagenes/<nombre>/eliminar", methods=["POST"])
@requiere_admin
def imagen_eliminar(tema_slug, nombre):
    tema = _tema_o_404(tema_slug)
    ruta = os.path.join(_carpeta_imagenes(tema), secure_filename(nombre))
    if os.path.isfile(ruta):
        os.remove(ruta)
        flash(f"Imagen '{nombre}' eliminada.", "ok")
    return redirect(url_for("admin.imagenes", tema_slug=tema.slug))


# ----------------------------------------------------------------- recursos --
# Roles, glosario, biblioteca y circuito. Los datos están en app/recursos/*.json
# y las plantillas en templates/recursos/, compartidas con el sitio público.

def _contexto_recursos():
    return {"estados": recursos.ESTADOS, "docs": recursos.documentos_por_id(),
            "layout": "admin/base_admin.html", "prefijo": "admin.", "ocultos": frozenset(), "oficial": lambda estado: True,
            "revisado_al": recursos.revisado_al()}


def _glosario_completo():
    return recursos.glosario_completo()


@admin_bp.route("/recursos/flujos")
@requiere_admin
def recursos_flujos():
    """Todas las bifurcaciones del algoritmo y, para cada camino, sus pasos."""
    alg = recursos.algoritmo()
    nodos = alg["nodos"]
    decisiones, flujos, caminos = [], [], {alg["inicio"]: []}
    pendientes = [alg["inicio"]]
    while pendientes:  # recorrido en orden desde el inicio, con el camino a cada nodo
        actual = pendientes.pop(0)
        nodo = nodos[actual]
        salidas = [(o["va"], (nodo["titulo"], o["texto"])) for o in nodo.get("opciones", [])]
        if nodo.get("siguiente"):
            salidas.append((nodo["siguiente"], None))
        if nodo["tipo"] == "decision":
            decisiones.append(actual)
        if nodo.get("pasos"):
            flujos.append({"id": actual, "camino": caminos[actual]})
        for destino, eleccion in salidas:
            if destino not in caminos:
                caminos[destino] = caminos[actual] + ([eleccion] if eleccion else [])
                pendientes.append(destino)
    return render_template("recursos/flujos.html", algoritmo=alg, decisiones=decisiones, flujos=flujos,
                           **_contexto_recursos())


@admin_bp.route("/recursos")
@requiere_admin
def recursos_inicio():
    return render_template(
        "recursos/inicio.html", roles=recursos.roles(), biblioteca=recursos.biblioteca(), circuito=recursos.circuito(),
        glosario=_glosario_completo(), **_contexto_recursos(),
    )


@admin_bp.route("/recursos/roles")
@requiere_admin
def recursos_roles():
    return render_template(
        "recursos/roles.html", roles=recursos.roles(), circuito=recursos.circuito(),
        glosario=_glosario_completo(), **_contexto_recursos(),
    )


@admin_bp.route("/recursos/roles/ficha")
@requiere_admin
def recursos_ficha_roles():
    # Hoja A4 para que la jefatura anote a quién le asigna cada rol.
    return render_template("recursos/ficha_roles.html", **_contexto_recursos())


@admin_bp.route("/recursos/grafico")
@requiere_admin
def recursos_grafico():
    from app.recursos import grafico
    return render_template("recursos/grafico.html", grafico=grafico.armar(recursos.algoritmo()), **_contexto_recursos())


@admin_bp.route("/recursos/proveedores")
@requiere_admin
def recursos_proveedores():
    return render_template("recursos/proveedores.html", p=recursos.herramientas()["proveedores"], **_contexto_recursos())


@admin_bp.route("/recursos/glosario")
@requiere_admin
def recursos_glosario():
    return render_template("recursos/glosario.html", glosario=_glosario_completo(), **_contexto_recursos())


@admin_bp.route("/recursos/biblioteca")
@requiere_admin
def recursos_biblioteca():
    return render_template(
        "recursos/biblioteca.html", biblioteca=recursos.biblioteca(), glosario=_glosario_completo(),
        **_contexto_recursos(),
    )


@admin_bp.route("/recursos/simulador")
@requiere_admin
def recursos_simulador():
    return render_template(
        "recursos/simulador.html", simulador=recursos.simulador(), docs_min=recursos.docs_minimos(), **_contexto_recursos(),
    )


@admin_bp.route("/recursos/algoritmo")
@requiere_admin
def recursos_algoritmo():
    return render_template(
        "recursos/algoritmo.html", algoritmo=recursos.algoritmo(), docs_min=recursos.docs_minimos(), **_contexto_recursos(),
    )


@admin_bp.route("/recursos/explicame")
@requiere_admin
def recursos_explicame():
    alg = recursos.algoritmo()
    nodo_id = request.args.get("etapa")
    if nodo_id not in alg["nodos"]:
        nodo_id = "c-pliego"
    nodos = [(i, n) for i, n in alg["nodos"].items() if n["tipo"] != "decision" or i == nodo_id]
    return render_template(
        "recursos/explicame.html", algoritmo=alg, nodos=nodos, nodo_id=nodo_id,
        preguntas=recursos.capacitacion()["explicame"], ejemplo=alg["ejemplos"]["insumos"]["texto"], **_contexto_recursos(),
    )


@admin_bp.route("/recursos/<clave>")
@requiere_admin
def recursos_herramienta(clave):
    if clave not in recursos.HERRAMIENTAS:
        abort(404)
    seccion = recursos.HERRAMIENTAS[clave][0]
    return render_template(
        "recursos/herramienta.html", clave=clave, h=recursos.herramientas()[seccion],
        iconos={k: v[1] for k, v in recursos.HERRAMIENTAS.items()}, **_contexto_recursos(),
    )


# ------------------------------------------------- centro de capacitación --
# Privado: guía de la capacitadora, presentación y material para participantes.

@admin_bp.route("/capacitacion")
@requiere_admin
def capacitacion_inicio():
    return render_template(
        "admin/capacitacion_inicio.html", cap=recursos.capacitacion(), roles=recursos.roles(),
        glosario=_glosario_completo(), biblioteca=recursos.biblioteca(), **_contexto_recursos(),
    )


@admin_bp.route("/capacitacion/algoritmo")
@requiere_admin
def capacitacion_algoritmo():
    return render_template(
        "recursos/algoritmo.html", algoritmo=recursos.algoritmo(), docs_min=recursos.docs_minimos(),
        **_contexto_recursos(),
    )


@admin_bp.route("/capacitacion/modo-capacitadora")
@requiere_admin
def capacitacion_modo():
    temas = recursos.capacitacion()["temas_capacitadora"]
    tema = next((t for t in temas if t["slug"] == request.args.get("tema")), temas[0])
    return render_template(
        "admin/capacitacion_modo.html", temas=temas, tema=tema, algoritmo=recursos.algoritmo(), **_contexto_recursos(),
    )


@admin_bp.route("/capacitacion/primera-clase")
@requiere_admin
def capacitacion_primera_clase():
    return render_template(
        "admin/capacitacion_primera_clase.html", cap=recursos.capacitacion(), roles=recursos.roles(),
        circuito=recursos.circuito(), glosario=_glosario_completo(), **_contexto_recursos(),
    )


@admin_bp.route("/capacitacion/participantes")
@requiere_admin
def capacitacion_participantes():
    return render_template("admin/capacitacion_participantes.html", cap=recursos.capacitacion(), **_contexto_recursos())


@admin_bp.route("/capacitacion/archivos/<nombre>")
@requiere_admin
def capacitacion_archivo(nombre):
    permitidos = {a["nombre"] for a in recursos.capacitacion()["primera_clase"]["archivos"]}
    if nombre not in permitidos:
        abort(404)
    return send_from_directory(recursos.ARCHIVOS, nombre, as_attachment=True)


@admin_bp.route("/capacitacion/administrador-local")
@requiere_admin
def curso_admin_local():
    return render_template("admin/curso_admin_local.html", curso=recursos.curso_admin_local())


@admin_bp.route("/capacitacion/administrador-local/<nombre>")
@requiere_admin
def curso_admin_local_archivo(nombre):
    curso = recursos.curso_admin_local()
    permitidos = {curso["programa"]["archivo"]} | {m["archivo"] for mod in curso["modulos"]
                                                   for m in mod.get("materiales", []) if m["tipo"] in ("pdf", "video")}
    if nombre not in permitidos:
        abort(404)
    return send_from_directory(os.path.join(recursos.ARCHIVOS, "admin-local"), nombre)


# ------------------------------------------------- revisión del nomenclador --

# Resultado de cada ítem amarillo: "si", "no", "duda" o "pendiente" (sin
# respuesta). Si dos revisores respondieron distinto, va a "duda": necesita
# una segunda mirada.
RESULTADOS_REVISION = {"si": "Confirmados", "no": "No coinciden", "duda": "Con dudas", "pendiente": "Sin revisar"}
FILTROS_REVISION = ("todos", *RESULTADOS_REVISION, "con")


def _metricas_revision(filas, conteo, dias=14):
    """Avance y gráficos simples del panel de revisión (solo lectura)."""
    from collections import Counter, defaultdict
    from datetime import datetime, timedelta, timezone

    from app.models.revision_nomenclador import hora_ar

    total = conteo["todos"]
    revisados = total - conteo.get("pendiente", 0)
    # Por persona: nadie tiene una lista asignada, así que su total son los
    # amarillos de las bodegas donde trabajó (las que tienen al menos 5 de sus
    # respuestas, o la que más tiene).
    amarillos_por_bodega = Counter(f["item"].bodega or "—" for f in filas)
    hechos = defaultdict(Counter)
    ultima = {}
    for f in filas:
        for o in f["observaciones"]:
            if o.validacion:
                nombre = o.revisor.nombre
                hechos[nombre][f["item"].bodega or "—"] += 1
                momento = o.actualizado_en or o.creado_en
                if momento and (nombre not in ultima or momento > ultima[nombre]):
                    ultima[nombre] = momento
    personas = []
    for nombre, por_bodega in hechos.items():
        bodegas = [b for b, n in por_bodega.items() if n >= 5] or [por_bodega.most_common(1)[0][0]]
        hechas = sum(por_bodega[b] for b in bodegas)
        total_p = sum(amarillos_por_bodega[b] for b in bodegas)
        personas.append({"nombre": nombre, "bodegas": sorted(bodegas), "hechos": sum(por_bodega.values()),
                         "total": total_p, "faltan": max(total_p - hechas, 0),
                         "pct": round(100 * hechas / total_p) if total_p else 0,
                         "ultima": hora_ar(ultima.get(nombre), "%d/%m/%Y") if ultima.get(nombre) else ""})
    personas.sort(key=lambda p: -p["hechos"])
    por_persona = Counter({p["nombre"]: p["hechos"] for p in personas})
    hoy = datetime.now(timezone.utc)
    claves = [hora_ar(hoy - timedelta(days=d), "%d/%m") for d in range(dias - 1, -1, -1)]
    por_dia = Counter(hora_ar(o.actualizado_en or o.creado_en, "%d/%m") for f in filas for o in f["observaciones"]
                      if o.validacion)
    serie = [(k, por_dia.get(k, 0)) for k in claves]
    ultimos7 = sum(n for _, n in serie[-7:])
    ritmo = ultimos7 / 7
    return {
        "total": total, "revisados": revisados, "faltan": total - revisados,
        "pct": round(100 * revisados / total) if total else 0,
        "reparto": [(k, conteo.get(k, 0), round(100 * conteo.get(k, 0) / total, 1) if total else 0)
                    for k in ("si", "no", "duda", "pendiente")],
        "personas": personas,
        "por_persona": por_persona.most_common(), "max_persona": max(por_persona.values(), default=1),
        "serie": serie, "max_dia": max((n for _, n in serie), default=0) or 1,
        "ritmo": round(ritmo), "dias_restantes": round((total - revisados) / ritmo) if ritmo else None,
    }


def _resultado_item(revisiones):
    respuestas = {o.validacion for o in revisiones if o.validacion}
    if not respuestas:
        return "pendiente"
    return respuestas.pop() if len(respuestas) == 1 else "duda"


def _datos_revision(revisor_id=None):
    """Ítems en amarillo con sus revisiones (de todos los revisores, o de uno
    solo si se pasa `revisor_id`) y su resultado, y las revisiones de ítems
    que ya no están en amarillo (cambiaron de estado o de nombre en el CSV)."""
    from app.models import EquivalenciaArticulo
    from app.models.revision_nomenclador import ObservacionNomenclador, clave_item
    from app.revision.routes import items_amarillos

    por_clave = {}
    consulta = ObservacionNomenclador.query
    if revisor_id is not None:
        consulta = consulta.filter_by(revisor_id=revisor_id)
    for o in consulta.order_by(ObservacionNomenclador.actualizado_en.desc()):
        if o.texto or o.validacion:
            por_clave.setdefault(o.clave_item, []).append(o)
    amarillos = items_amarillos()
    claves_amarillas = {c for c, _ in amarillos}
    filas = []
    for c, e in amarillos:
        revisiones = por_clave.get(c, [])
        filas.append({"clave": c, "item": e, "observaciones": revisiones, "resultado": _resultado_item(revisiones),
                      "desacuerdo": len({o.validacion for o in revisiones if o.validacion}) > 1})
    estado_actual = {clave_item(e.nombre_interno): e.confianza for e in EquivalenciaArticulo.query}
    huerfanas = [o for c, lista in por_clave.items() if c not in claves_amarillas for o in lista]
    return filas, huerfanas, estado_actual


@admin_bp.route("/nomenclador/revision")
@requiere_admin
def nomenclador_revision():
    from app.models.revision_nomenclador import VALIDACIONES, RevisorNomenclador

    filas, huerfanas, estado_actual = _datos_revision()
    filtro = request.args.get("filtro", "todos")
    if filtro not in FILTROS_REVISION:
        filtro = "todos"
    conteo = {clave: sum(1 for f in filas if f["resultado"] == clave) for clave in RESULTADOS_REVISION}
    conteo["todos"] = len(filas)
    conteo["con"] = sum(1 for f in filas if any(o.texto for o in f["observaciones"]))
    metricas = _metricas_revision(filas, conteo)
    if filtro == "con":
        filas = [f for f in filas if any(o.texto for o in f["observaciones"])]
    elif filtro != "todos":
        filas = [f for f in filas if f["resultado"] == filtro]
    por_pagina = 10
    paginas = max(1, -(-len(filas) // por_pagina))
    pagina = min(max(request.args.get("pagina", 1, type=int), 1), paginas)
    total_filas = len(filas)
    filas = filas[(pagina - 1) * por_pagina:pagina * por_pagina]
    return render_template(
        "admin/nomenclador_revision.html", filas=filas, huerfanas=huerfanas, estado_actual=estado_actual,
        pagina=pagina, paginas=paginas, total_filas=total_filas, metricas=metricas,
        filtro=filtro, conteo=conteo, revisores=RevisorNomenclador.query.order_by(RevisorNomenclador.nombre).all(),
        enlace_nuevo=session.pop("enlace_revision_nuevo", None), resultados=RESULTADOS_REVISION,
        validaciones=VALIDACIONES,
    )


def _nuevo_enlace(revisor):
    """Genera un token nuevo (el anterior deja de servir) y deja el enlace en
    la sesión para mostrarlo una sola vez: en la base solo queda el hash."""
    import secrets

    from app.models.revision_nomenclador import hash_token

    token = secrets.token_urlsafe(32)
    revisor.token_hash = hash_token(token)
    session["enlace_revision_nuevo"] = {
        "nombre": revisor.nombre, "url": url_for("revision.acceso", _external=True) + "#" + token}


@admin_bp.route("/nomenclador/revisores", methods=["POST"])
@requiere_admin
def revisor_crear():
    from app.models.revision_nomenclador import RevisorNomenclador

    nombre = (request.form.get("nombre") or "").strip()[:100]
    if not nombre:
        flash("Escribí el nombre de la persona.", "error")
        return redirect(url_for("admin.nomenclador_revision"))
    revisor = RevisorNomenclador(nombre=nombre, token_hash="", activo=True)
    _nuevo_enlace(revisor)
    db.session.add(revisor)
    db.session.commit()
    flash(f"Acceso creado para {nombre}.", "ok")
    return redirect(url_for("admin.nomenclador_revision"))


@admin_bp.route("/nomenclador/revisores/<int:revisor_id>/enlace", methods=["POST"])
@requiere_admin
def revisor_enlace(revisor_id):
    from app.models.revision_nomenclador import RevisorNomenclador

    revisor = db.session.get(RevisorNomenclador, revisor_id) or abort(404)
    _nuevo_enlace(revisor)
    revisor.activo = True
    db.session.commit()
    flash(f"Enlace nuevo para {revisor.nombre}: el anterior ya no funciona.", "ok")
    return redirect(url_for("admin.nomenclador_revision"))


@admin_bp.route("/nomenclador/revisores/<int:revisor_id>/estado", methods=["POST"])
@requiere_admin
def revisor_estado(revisor_id):
    from app.models.revision_nomenclador import RevisorNomenclador

    revisor = db.session.get(RevisorNomenclador, revisor_id) or abort(404)
    revisor.activo = not revisor.activo
    db.session.commit()
    flash(f"Acceso de {revisor.nombre} {'activado' if revisor.activo else 'dado de baja'}.", "ok")
    return redirect(url_for("admin.nomenclador_revision"))


@admin_bp.route("/nomenclador/revision/exportar")
@requiere_admin
def nomenclador_revision_exportar():
    """Excel con toda la revisión, de todos los revisores (o de uno solo, con
    ?revisor=<id>), en cuatro hojas según el resultado de cada ítem (y una
    quinta con las revisiones de ítems que ya no están en amarillo, si las
    hay). Una fila por revisión."""
    from flask import Response

    import re

    from app.models.revision_nomenclador import (
        COLOR_EXCEL, VALIDACIONES, RevisorNomenclador, clave_item, codigo_hospital, hora_ar,
    )
    from app.revision.routes import bodegas_por_clave, descripcion_timbo
    from app.services import xlsx

    revisor = None
    if request.args.get("revisor"):
        revisor = db.session.get(RevisorNomenclador, request.args.get("revisor", type=int) or 0) or abort(404)
    filas, huerfanas, estado_actual = _datos_revision(revisor.id if revisor else None)
    bodegas_map = bodegas_por_clave()

    def versiones(o):
        return " | ".join(f"{hora_ar(h.guardado_en)}: [{VALIDACIONES.get(h.validacion, 'sin respuesta')}] {h.texto}".rstrip()
                          for h in o.historial)

    encabezados = ["Código interno", "Código de artículo", "Bodega/centro de pedido", "Descripción original",
                   "Código TIMBÓ", "Descripción TIMBÓ", "Resultado", "Observación", "Revisor/a",
                   "Fecha de revisión", "Versiones anteriores"]
    anchos = [12, 16, 26, 42, 14, 50, 26, 42, 18, 17, 40]
    hojas = {clave: [] for clave in RESULTADOS_REVISION}
    colores = {clave: [] for clave in RESULTADOS_REVISION}  # cada fila, del color de su respuesta
    for f in filas:
        e = f["item"]
        base = [e.codigo_interno or codigo_hospital(e.notas), e.codigo_articulo or "",
                ", ".join(sorted(bodegas_map.get(f["clave"], ()))), e.nombre_interno, e.codigo_catalogo or "",
                descripcion_timbo(e)]
        if not f["observaciones"]:
            hojas[f["resultado"]].append(base + ["Sin revisar", "", "", "", ""])
            colores[f["resultado"]].append(COLOR_EXCEL[None])
        for o in f["observaciones"]:
            resultado = VALIDACIONES.get(o.validacion, "Sin responder")
            if f["desacuerdo"]:
                resultado += " (hay respuestas distintas)"
            hojas[f["resultado"]].append(base + [resultado, o.texto, o.revisor.nombre, hora_ar(o.actualizado_en),
                                                 versiones(o)])
            colores[f["resultado"]].append(COLOR_EXCEL[o.validacion])
    libro = [(nombre, encabezados, hojas[clave], anchos, colores[clave]) for clave, nombre in
             (("si", "COINCIDENCIAS"), ("no", "NO COINCIDEN"), ("duda", "DUDAS"), ("pendiente", "SIN REVISAR"))]
    if huerfanas:
        estados = {"alta": "Ahora en verde", "sin_match": "Ahora en rojo"}
        libro.append(("YA NO EN AMARILLO", ["Estado actual"] + encabezados[3:4] + encabezados[6:], [
            [estados.get(estado_actual.get(o.clave_item), "Ya no está en el nomenclador"), o.nombre_item,
             VALIDACIONES.get(o.validacion, "Sin responder"), o.texto, o.revisor.nombre, hora_ar(o.actualizado_en),
             versiones(o)] for o in huerfanas], [24, 42, 22, 42, 18, 17, 40],
            [COLOR_EXCEL[o.validacion] for o in huerfanas]))
    quien = "_" + (re.sub(r"[^a-z0-9]+", "-", clave_item(revisor.nombre)).strip("-") or str(revisor.id)) if revisor else ""
    nombre = f"revision_nomenclador{quien}_{hora_ar(datetime.now(timezone.utc), '%Y-%m-%d')}.xlsx"
    return Response(xlsx.libro(libro), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f'attachment; filename="{nombre}"', "Cache-Control": "no-store"})


# ------------------------------------------------------------- búsquedas --

def _filtros_busquedas():
    periodo = request.args.get("periodo", "30")
    tipo = request.args.get("tipo", "todas")
    if periodo not in estadisticas.PERIODOS:
        periodo = "30"
    if tipo not in estadisticas.TIPOS_FILTRO:
        tipo = "todas"
    return periodo, tipo, request.args.get("sin") == "1"


@admin_bp.route("/busquedas")
@requiere_admin
def busquedas():
    from sqlalchemy import func

    from app.models import EventoUso

    periodo, tipo, sin = _filtros_busquedas()
    q = estadisticas.consulta_busquedas(periodo, tipo, sin)
    total = q.count()
    sin_resultado = q.filter(EventoUso.hubo_resultado.is_(False)).count()
    pagina = max(1, request.args.get("pagina", 1, type=int))
    por_pagina = 100
    eventos = q.order_by(EventoUso.creado_en.desc()).offset((pagina - 1) * por_pagina).limit(por_pagina).all()
    repetidas = (q.with_entities(EventoUso.consulta, func.count(EventoUso.id))
                 .group_by(EventoUso.consulta).order_by(func.count(EventoUso.id).desc()).limit(15).all())
    return render_template(
        "admin/busquedas.html", eventos=eventos, total=total, sin_resultado=sin_resultado, repetidas=repetidas,
        periodo=periodo, tipo=tipo, sin=sin, pagina=pagina, paginas=max(1, -(-total // por_pagina)),
        periodos=estadisticas.PERIODOS, origen=estadisticas.origen_busqueda,
    )


@admin_bp.route("/busquedas/exportar")
@requiere_admin
def busquedas_exportar():
    import csv
    import io

    from flask import Response

    from app.models import EventoUso
    from app.models.revision_nomenclador import hora_ar

    periodo, tipo, sin = _filtros_busquedas()
    salida = io.StringIO()
    w = csv.writer(salida, delimiter=";")
    w.writerow(["Fecha y hora", "Dónde", "Qué escribió", "¿Encontró resultado?"])
    for e in estadisticas.consulta_busquedas(periodo, tipo, sin).order_by(EventoUso.creado_en.desc()):
        w.writerow([hora_ar(e.creado_en), estadisticas.origen_busqueda(e), e.consulta,
                    "Sí" if e.hubo_resultado else ("No" if e.hubo_resultado is False else "")])
    nombre = f"busquedas_{periodo}_{tipo}{'_sin-resultado' if sin else ''}_{hora_ar(datetime.now(timezone.utc), '%Y-%m-%d')}.csv"
    return Response("﻿" + salida.getvalue(), mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{nombre}"'})


def _inventario_filtrado():
    from app.services import inventario
    from app.services.textutil import slugify as _norm

    tipo = request.args.get("tipo", "")
    grupo = request.args.get("grupo", "")
    tema = request.args.get("tema", "")
    texto = request.args.get("q", "").strip()
    todas = inventario.filas()
    filas = [f for f in todas
             if (not tipo or f["tipo"] == tipo) and (not grupo or f["grupo"] == grupo)
             and (not tema or tema in f["tema"])
             and (not texto or _norm(texto) in _norm(f"{f['titulo']} {f['detalle']} {f['grupo_contenido']}"))]
    return todas, filas, {"tipo": tipo, "grupo": grupo, "tema": tema, "q": texto}


@admin_bp.route("/inventario")
@requiere_admin
def inventario_vista():
    from collections import Counter

    from app.services import inventario

    todas, filas, filtros = _inventario_filtrado()
    por_grupo = Counter(f["grupo"] for f in todas)
    por_tipo = {t: Counter(f["grupo"] for f in todas if f["tipo"] == t) for t in inventario.TIPOS}
    return render_template(
        "admin/inventario.html", filas=filas, total=len(todas), filtros=filtros, por_grupo=por_grupo, por_tipo=por_tipo,
        tipos=inventario.TIPOS, grupos=inventario.GRUPOS, temas=[t.nombre for t in Tema.query.order_by(Tema.orden)],
    )


@admin_bp.route("/inventario/exportar")
@requiere_admin
def inventario_exportar():
    import csv
    import io

    from flask import Response

    from app.models.revision_nomenclador import hora_ar
    from app.services import inventario

    _, filas, _ = _inventario_filtrado()
    salida = io.StringIO()
    w = csv.writer(salida, delimiter=";")
    w.writerow(["Tipo", "Tema", "Módulo o grupo", "Título", "Estado", "Grupo de estado", "Fecha", "Detalle", "Fuente oficial", "Dónde verlo"])
    for f in filas:
        w.writerow([inventario.TIPOS[f["tipo"]], f["tema"], f["grupo_contenido"], f["titulo"], f["estado"],
                    inventario.GRUPOS[f["grupo"]], f["fecha"], f["detalle"], f["fuente"],
                    (request.host_url.rstrip("/") + f["enlace"]) if f["enlace"] else ""])
    nombre = f"inventario_{hora_ar(datetime.now(timezone.utc), '%Y-%m-%d')}.csv"
    return Response("﻿" + salida.getvalue(), mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{nombre}"'})


# Llaves de la revisión por servicio: sus rutas se registran sobre admin_bp.
from app.admin import servicios  # noqa: E402,F401

# Diagnóstico de pérdida de datos (solo local): ídem.
from app.admin import diagnostico  # noqa: E402,F401

# Comparación final subiendo archivos a mano (solo local): ídem.
from app.admin import comparar_manual  # noqa: E402,F401
