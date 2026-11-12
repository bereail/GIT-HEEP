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
    session,
    url_for,
)
from werkzeug.utils import secure_filename

from app import csrf
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
        if contrasena_correcta(request.form.get("contrasena", "")):
            session["admin_autenticado"] = True
            return redirect(url_for("admin.dashboard"))
        error = "Contraseña incorrecta."
    return render_template("admin/login.html", error=error)


@admin_bp.route("/logout", methods=["POST"])
def logout():
    session.pop("admin_autenticado", None)
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
    return render_template("admin/dashboard.html", temas=temas)


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
            if extension not in EXTENSIONES_PERMITIDAS:
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
