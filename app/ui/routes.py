import re
import secrets

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for

from app import csrf
from app.extensions import db
from app.models import Categoria, Consulta, MensajeConsulta, Tema, Tutorial
from app.models.consulta import ESTADOS_CONSULTA, TIPOS_CONSULTA
from app.services import buscador

_PRIMERA_LETRA = re.compile(r"[A-ZÁÉÍÓÚÑ]", re.IGNORECASE)

# Por debajo de este puntaje (ver buscador.buscar_con_puntaje) el chatbot no
# responde directo: ofrece opciones "¿Te referís a...?". Equivale a una sola
# palabra que coincide apenas por su raíz.
CHATBOT_PUNTAJE_MINIMO = 2


def _letra_de_termino(termino):
    m = _PRIMERA_LETRA.search(termino)
    return m.group(0).upper() if m else "#"

ui_bp = Blueprint("ui", __name__, template_folder="../templates")


def _tema_o_404(tema_slug):
    tema = Tema.query.filter_by(slug=tema_slug, activo=True).first()
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


# ---------------------------------------------------------------- portal ----

@ui_bp.route("/")
def portal_inicio():
    temas = Tema.query.filter_by(activo=True).order_by(Tema.orden).all()
    return render_template("portal_inicio.html", temas=temas)


# ------------------------------------------------------------------ tema ----

@ui_bp.route("/temas/<tema_slug>/")
def ver_tema(tema_slug):
    tema = _tema_o_404(tema_slug)
    return render_template("tema_inicio.html", tema=tema)


@ui_bp.route("/temas/<tema_slug>/quickstart")
def ver_quickstart(tema_slug):
    tema = _tema_o_404(tema_slug)
    return render_template("quickstart.html", tema=tema)


# -------------------------------------------------------------- categorías --

@ui_bp.route("/temas/<tema_slug>/categorias")
def ver_categorias(tema_slug):
    tema = _tema_o_404(tema_slug)
    return render_template("categorias.html", tema=tema)


@ui_bp.route("/temas/<tema_slug>/categorias/<categoria_slug>")
def ver_categoria(tema_slug, categoria_slug):
    tema = _tema_o_404(tema_slug)
    categoria = _categoria_o_404(tema, categoria_slug)
    return render_template("categoria.html", tema=tema, categoria=categoria)


@ui_bp.route("/temas/<tema_slug>/categorias/<categoria_slug>/tutoriales/<tutorial_slug>")
def ver_tutorial(tema_slug, categoria_slug, tutorial_slug):
    tema = _tema_o_404(tema_slug)
    categoria = _categoria_o_404(tema, categoria_slug)
    tutorial = _tutorial_o_404(categoria, tutorial_slug)

    tutoriales_planos = [
        (c.slug, t.slug, t.titulo)
        for c in tema.categorias
        for t in c.tutoriales
    ]
    indice_actual = next(
        (i for i, (cs, ts, _) in enumerate(tutoriales_planos) if cs == categoria.slug and ts == tutorial.slug),
        -1,
    )
    anterior = tutoriales_planos[indice_actual - 1] if indice_actual > 0 else None
    siguiente = (
        tutoriales_planos[indice_actual + 1]
        if 0 <= indice_actual < len(tutoriales_planos) - 1
        else None
    )

    return render_template(
        "tutorial.html",
        tema=tema,
        categoria=categoria,
        tutorial=tutorial,
        anterior=anterior,
        siguiente=siguiente,
    )


# ------------------------------------------------------------------ otras ---

@ui_bp.route("/temas/<tema_slug>/tareas")
def ver_tareas(tema_slug):
    tema = _tema_o_404(tema_slug)
    return render_template("tareas.html", tema=tema)


@ui_bp.route("/temas/<tema_slug>/problemas")
def ver_problemas(tema_slug):
    tema = _tema_o_404(tema_slug)
    grupos = []  # [(categoria_libre_o_None, [situaciones]), ...], en orden de aparición
    indice_por_grupo = {}
    for situacion in tema.situaciones:
        clave = situacion.categoria_libre
        if clave not in indice_por_grupo:
            indice_por_grupo[clave] = len(grupos)
            grupos.append((clave, []))
        grupos[indice_por_grupo[clave]][1].append(situacion)
    # Las situaciones sin categoría van primero, tal como se veían antes de
    # tener categorías (no se les fuerza una etiqueta que no tienen).
    grupos.sort(key=lambda g: (g[0] is not None, indice_por_grupo[g[0]]))
    return render_template("problemas.html", tema=tema, grupos=grupos)


@ui_bp.route("/temas/<tema_slug>/glosario")
def ver_glosario(tema_slug):
    tema = _tema_o_404(tema_slug)
    ordenado = sorted(tema.entradas_glosario, key=lambda t: t.termino.lower())
    letras = sorted({_letra_de_termino(t.termino) for t in ordenado})
    primera_de_letra = {
        t.id for i, t in enumerate(ordenado)
        if i == 0 or _letra_de_termino(ordenado[i - 1].termino) != _letra_de_termino(t.termino)
    }
    return render_template(
        "glosario.html",
        tema=tema,
        entradas=ordenado,
        letras=letras,
        primera_de_letra=primera_de_letra,
        letra_de_termino=_letra_de_termino,
    )


@ui_bp.route("/temas/<tema_slug>/progreso")
def ver_progreso(tema_slug):
    tema = _tema_o_404(tema_slug)
    return render_template("progreso.html", tema=tema)


# ------------------------------------------------------- buscador / chatbot --

@ui_bp.route("/temas/<tema_slug>/buscar.json")
def buscar_json(tema_slug):
    tema = _tema_o_404(tema_slug)
    consulta = request.args.get("q", "")
    indice = buscador.construir_indice(tema)
    resultados = buscador.buscar(indice, consulta)
    return jsonify([
        {"kind": r["kind"], "title": r["title"], "url": r["url"]} for r in resultados
    ])


@ui_bp.route("/temas/<tema_slug>/chatbot", methods=["POST"])
@csrf.exempt
def chatbot_responder(tema_slug):
    tema = _tema_o_404(tema_slug)
    consulta = (request.get_json(silent=True) or {}).get("mensaje", "")
    indice = buscador.construir_indice(tema)
    resultados = buscador.buscar_con_puntaje(indice, consulta, limite=8)
    if not resultados:
        return jsonify({"encontrado": False, "sugerencias": buscador.sugerencias_iniciales(tema)})

    puntaje, mejor = resultados[0]
    if puntaje < CHATBOT_PUNTAJE_MINIMO:
        # Coincidencia floja: mejor preguntar que adivinar mal.
        return jsonify({"encontrado": False, "quiso_decir": _titulos_distintos(resultados)[:3]})

    # Para "También te puede servir": solo lo que también coincide bastante
    # (si no, son botones de relleno) y que no lleve a la misma lección que
    # la respuesta principal.
    relevantes = [par for par in resultados if par[0] >= puntaje * 0.5]
    relacionadas = _titulos_distintos(relevantes, excluir=mejor)[:3]

    respuesta = buscador.armar_respuesta_chatbot(mejor)
    return jsonify({"encontrado": True, **respuesta, "relacionadas": relacionadas})


def _destino(entrada):
    # Las tareas y lecciones que apuntan a la misma lección son lo mismo para
    # quien pregunta; problemas y glosario comparten página pero no contenido.
    if entrada["kind"] in ("Tarea", "Leccion", "Modulo"):
        return entrada["url"]
    return entrada["title"]


def _titulos_distintos(resultados, excluir=None):
    vistos = {_destino(excluir)} if excluir else set()
    titulos = []
    for _, entrada in resultados:
        destino = _destino(entrada)
        if destino in vistos or entrada["title"] in titulos:
            continue
        vistos.add(destino)
        titulos.append(entrada["title"])
    return titulos


@ui_bp.route("/temas/<tema_slug>/chatbot/sugerencias")
def chatbot_sugerencias(tema_slug):
    tema = _tema_o_404(tema_slug)
    return jsonify(buscador.sugerencias_iniciales(tema))


# --------------------------------------------------------- consultas ---

# Tope para que un mensaje pegado por error (o a propósito) no llene la base.
LARGO_MAXIMO_MENSAJE = 4000


def _generar_token():
    while True:
        token = secrets.token_urlsafe(12)
        if not Consulta.query.filter_by(token=token).first():
            return token


@ui_bp.route("/temas/<tema_slug>/consultas/nueva", methods=["GET", "POST"])
def consulta_nueva(tema_slug):
    tema = _tema_o_404(tema_slug)
    if request.method == "POST":
        mensaje = (request.form.get("mensaje") or "").strip()
        tipo = request.form.get("tipo", "consulta")
        if not mensaje or tipo not in TIPOS_CONSULTA:
            flash("Contanos tu consulta antes de enviarla.", "error")
            return render_template("consulta_nueva.html", tema=tema, tipos=TIPOS_CONSULTA, valores=request.form)
        if len(mensaje) > LARGO_MAXIMO_MENSAJE:
            flash(f"El mensaje es muy largo: acortalo a {LARGO_MAXIMO_MENSAJE} caracteres.", "error")
            return render_template("consulta_nueva.html", tema=tema, tipos=TIPOS_CONSULTA, valores=request.form)

        consulta = Consulta(
            token=_generar_token(),
            tema_id=tema.id,
            tipo=tipo,
            nombre_contacto=(request.form.get("nombre_contacto") or "").strip()[:150] or None,
        )
        db.session.add(consulta)
        db.session.flush()
        db.session.add(MensajeConsulta(consulta_id=consulta.id, autor="usuario", cuerpo=mensaje))
        db.session.commit()
        return redirect(url_for("ui.consulta_ver", token=consulta.token, nueva="1"))

    # El chatbot manda la última pregunta en ?mensaje= para no tener que
    # escribirla de nuevo.
    return render_template("consulta_nueva.html", tema=tema, tipos=TIPOS_CONSULTA, valores=request.args)


@ui_bp.route("/consultas/<token>")
def consulta_ver(token):
    consulta = Consulta.query.filter_by(token=token).first_or_404()
    return render_template(
        "consulta_ver.html",
        consulta=consulta,
        tema=consulta.tema,
        es_nueva=request.args.get("nueva") == "1",
    )


@ui_bp.route("/consultas/<token>/responder", methods=["POST"])
def consulta_responder(token):
    consulta = Consulta.query.filter_by(token=token).first_or_404()
    mensaje = (request.form.get("mensaje") or "").strip()[:LARGO_MAXIMO_MENSAJE]
    if mensaje and consulta.estado != "cerrada":
        db.session.add(MensajeConsulta(consulta_id=consulta.id, autor="usuario", cuerpo=mensaje))
        consulta.estado = "abierta"
        db.session.commit()
    return redirect(url_for("ui.consulta_ver", token=token))
