import re
import secrets

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for

from app import csrf
from app.extensions import db
from app.models import Categoria, Consulta, EquivalenciaArticulo, Feedback, MensajeConsulta, Tema, Tutorial
from app.models.consulta import ESTADOS_CONSULTA, TIPOS_CONSULTA
from app.models.feedback import CATEGORIAS_FEEDBACK
from app.services import buscador, estadisticas, notificaciones

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
    tema_nomenclador = next((t for t in temas if t.equivalencias_articulos), None)
    return render_template("portal_inicio.html", temas=temas, tema_nomenclador=tema_nomenclador)


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
    estadisticas.registrar("vista_modulo", tema=tema, titulo=categoria.titulo)
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

    estadisticas.registrar("vista_tutorial", tema=tema, titulo=tutorial.titulo)

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


@ui_bp.route("/temas/<tema_slug>/equivalencias")
def ver_equivalencias(tema_slug):
    tema = _tema_o_404(tema_slug)
    items = EquivalenciaArticulo.query.filter_by(tema_id=tema.id).order_by(
        EquivalenciaArticulo.nombre_interno
    ).all()
    datos = [
        {
            "nombre": e.nombre_interno,
            "codigo": e.codigo_catalogo or "",
            "bien": e.bien_o_servicio or "",
            "item": e.item_especifico or "",
            "confianza": e.confianza,
            "origen": e.origen or "",
            "notas": e.notas or "",
        }
        for e in items
    ]
    origenes = sorted({e.origen for e in items if e.origen})
    actualizado_en = max((e.creado_en for e in items if e.creado_en), default=None)
    return render_template(
        "equivalencias.html", tema=tema, datos=datos, origenes=origenes, actualizado_en=actualizado_en
    )


@ui_bp.route("/temas/<tema_slug>/progreso")
def ver_progreso(tema_slug):
    tema = _tema_o_404(tema_slug)
    return render_template("progreso.html", tema=tema)


# ------------------------------------------------------- buscador / chatbot --

@ui_bp.route("/buscar.json")
def buscar_global_json():
    consulta = request.args.get("q", "")
    temas = Tema.query.filter_by(activo=True).order_by(Tema.orden).all()
    indice = buscador.construir_indice_global(temas)
    resultados = buscador.buscar(indice, consulta, limite=15)
    if consulta.strip():
        estadisticas.registrar("busqueda_global", consulta=consulta, hubo_resultado=bool(resultados))
    return jsonify([
        {
            "kind": r["kind"], "title": r["title"], "url": r["url"],
            "tema_nombre": r["tema_nombre"], "tema_icono": r["tema_icono"],
        }
        for r in resultados
    ])


@ui_bp.route("/temas/<tema_slug>/buscar.json")
def buscar_json(tema_slug):
    tema = _tema_o_404(tema_slug)
    consulta = request.args.get("q", "")
    indice = buscador.construir_indice(tema)
    resultados = buscador.buscar(indice, consulta)
    if consulta.strip():
        estadisticas.registrar("busqueda", tema=tema, consulta=consulta, hubo_resultado=bool(resultados))
    return jsonify([
        {"kind": r["kind"], "title": r["title"], "url": r["url"]} for r in resultados
    ])


@ui_bp.route("/temas/<tema_slug>/chatbot", methods=["POST"])
@csrf.exempt
def chatbot_responder(tema_slug):
    tema = _tema_o_404(tema_slug)
    consulta = str((request.get_json(silent=True) or {}).get("mensaje", ""))[:300]
    indice = buscador.construir_indice(tema)
    resultados = buscador.buscar_con_puntaje(indice, consulta, limite=8)
    puntaje = resultados[0][0] if resultados else 0

    # ¿La pregunta es claramente de otro sistema? (ej.: "cargar una cirugía"
    # preguntado en TIMBÓ Compras). Solo si allá coincide el doble que acá,
    # para no mandar a otro tema algo que este también responde.
    otro = _buscar_en_otros_temas(tema, consulta, minimo=max(puntaje * 2, CHATBOT_PUNTAJE_MINIMO * 2))
    respondio = bool(otro) or puntaje >= CHATBOT_PUNTAJE_MINIMO
    if consulta.strip():
        estadisticas.registrar("chatbot", tema=tema, consulta=consulta, hubo_resultado=respondio)
    if otro:
        return jsonify({"encontrado": False, "otro_tema": otro})

    if puntaje < CHATBOT_PUNTAJE_MINIMO:
        if resultados:
            # Coincidencia floja: mejor preguntar que adivinar mal.
            return jsonify({"encontrado": False, "quiso_decir": _titulos_distintos(resultados)[:3]})
        return jsonify({"encontrado": False, "sugerencias": buscador.sugerencias_iniciales(tema)})

    mejor = resultados[0][1]
    # Para "También te puede servir": solo lo que también coincide bastante
    # y que no lleve a la misma lección que la respuesta principal.
    relevantes = [par for par in resultados if par[0] >= puntaje * 0.5]
    relacionadas = _titulos_distintos(relevantes, excluir=mejor)[:3]
    respuesta = buscador.armar_respuesta_chatbot(mejor)
    return jsonify({"encontrado": True, **respuesta, "relacionadas": relacionadas})


def _buscar_en_otros_temas(tema, consulta, minimo):
    """Si la pregunta coincide claramente con otro sistema, lo dice en vez
    de contestar "no sé" (ej.: algo de miHospital preguntado en TIMBÓ)."""
    mejor = None
    for otro in Tema.query.filter(Tema.activo.is_(True), Tema.id != tema.id).all():
        resultados = buscador.buscar_con_puntaje(buscador.construir_indice(otro), consulta, limite=1)
        if resultados and resultados[0][0] >= minimo and (not mejor or resultados[0][0] > mejor[0]):
            mejor = (resultados[0][0], otro, resultados[0][1])
    if not mejor:
        return None
    _, otro, entrada = mejor
    return {"tema": otro.nombre, "titulo": entrada["title"], "url": entrada["url"]}


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


@ui_bp.route("/temas/<tema_slug>/chatbot/feedback", methods=["POST"])
@csrf.exempt
def chatbot_feedback(tema_slug):
    # Un 👎 cuenta como pregunta sin respuesta útil, para que aparezca en
    # las estadísticas del admin junto a las que el chatbot no supo.
    tema = _tema_o_404(tema_slug)
    datos = request.get_json(silent=True) or {}
    pregunta = str(datos.get("pregunta", "")).strip()[:190]
    if datos.get("util") is False and pregunta:
        estadisticas.registrar("chatbot", tema=tema, consulta="👎 " + pregunta, hubo_resultado=False)
    return jsonify({"ok": True})


@ui_bp.route("/temas/<tema_slug>/feedback-tutorial", methods=["POST"])
@csrf.exempt
def feedback_tutorial(tema_slug):
    tema = _tema_o_404(tema_slug)
    datos = request.get_json(silent=True) or {}
    titulo = (datos.get("titulo") or "").strip()
    voto = datos.get("voto")
    if titulo and voto in ("si", "no"):
        estadisticas.registrar("feedback_tutorial", tema=tema, titulo=titulo, hubo_resultado=(voto == "si"))
    return jsonify({"ok": True})


# --------------------------------------------------------- consultas ---

def _generar_token():
    while True:
        token = secrets.token_urlsafe(12)
        if not Consulta.query.filter_by(token=token).first():
            return token


@ui_bp.route("/temas/<tema_slug>/consultas/nueva", methods=["GET", "POST"])
def consulta_nueva(tema_slug):
    tema = _tema_o_404(tema_slug)
    contexto = request.args.get("contexto", "")
    tipo_preseleccionado = request.args.get("tipo") if request.args.get("tipo") in TIPOS_CONSULTA else "consulta"
    if request.method == "POST":
        mensaje = (request.form.get("mensaje") or "").strip()
        tipo = request.form.get("tipo", "consulta")
        if not mensaje or tipo not in TIPOS_CONSULTA:
            flash("Contanos tu consulta antes de enviarla.", "error")
            return render_template("consulta_nueva.html", tema=tema, tipos=TIPOS_CONSULTA, valores=request.form, contexto=contexto)

        consulta = Consulta(
            token=_generar_token(),
            tema_id=tema.id,
            tipo=tipo,
            nombre_contacto=(request.form.get("nombre_contacto") or "").strip() or None,
            email=(request.form.get("email") or "").strip() or None,
        )
        db.session.add(consulta)
        db.session.flush()
        db.session.add(MensajeConsulta(consulta_id=consulta.id, autor="usuario", cuerpo=mensaje))
        db.session.commit()
        notificaciones.notificar_nueva_consulta(consulta, mensaje)
        return redirect(url_for("ui.consulta_ver", token=consulta.token, nueva="1"))

    return render_template(
        "consulta_nueva.html", tema=tema, tipos=TIPOS_CONSULTA, valores=None, contexto=contexto,
        tipo_preseleccionado=tipo_preseleccionado,
    )


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
    mensaje = (request.form.get("mensaje") or "").strip()
    if mensaje:
        db.session.add(MensajeConsulta(consulta_id=consulta.id, autor="usuario", cuerpo=mensaje))
        consulta.estado = "abierta"
        db.session.commit()
    return redirect(url_for("ui.consulta_ver", token=token))


# ------------------------------------------------------------- mis consultas --

@ui_bp.route("/mis-consultas")
def mis_consultas():
    """Página que lee del localStorage (con JS) los tokens de las consultas
    que el usuario inició en este navegador, y pide sus datos acá abajo."""
    return render_template("mis_consultas.html")


@ui_bp.route("/mis-consultas.json", methods=["POST"])
@csrf.exempt
def mis_consultas_json():
    tokens = (request.get_json(silent=True) or {}).get("tokens", [])
    if not isinstance(tokens, list) or not tokens:
        return jsonify([])
    tokens = [t for t in tokens if isinstance(t, str)][:100]  # tope defensivo
    consultas = Consulta.query.filter(Consulta.token.in_(tokens)).order_by(Consulta.actualizada_en.desc()).all()
    return jsonify([
        {
            "token": c.token,
            "tema_nombre": c.tema.nombre,
            "tema_icono": c.tema.icono,
            "tipo_label": c.tipo_label,
            "estado": c.estado,
            "estado_label": c.estado_label,
            "actualizada_en": c.actualizada_en.isoformat() if c.actualizada_en else None,
            "ultimo_autor": c.ultimo_mensaje.autor if c.ultimo_mensaje else None,
            "url": url_for("ui.consulta_ver", token=c.token),
        }
        for c in consultas
    ])


# ------------------------------------------------------------------ feedback --

def _opciones_tutoriales_tema(tema):
    opciones = [("", "— General, no es sobre una lección puntual —")]
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


@ui_bp.route("/temas/<tema_slug>/feedback", methods=["GET", "POST"])
def feedback_nuevo(tema_slug):
    tema = _tema_o_404(tema_slug)
    if request.method == "POST":
        puntuacion_raw = request.form.get("puntuacion")
        puntuacion = int(puntuacion_raw) if puntuacion_raw in {"1", "2", "3", "4", "5"} else None
        comentario = (request.form.get("comentario") or "").strip() or None
        nombre = (request.form.get("nombre") or "").strip() or None
        categoria = request.form.get("categoria") or None
        if categoria not in CATEGORIAS_FEEDBACK:
            categoria = None

        if puntuacion is None and not comentario:
            flash("Dejá una puntuación o un comentario antes de enviar.", "error")
            return render_template(
                "feedback_nuevo.html", tema=tema, categorias=CATEGORIAS_FEEDBACK,
                opciones_tutoriales=_opciones_tutoriales_tema(tema), valores=request.form,
            )

        tutorial = _tutorial_desde_valor(tema, request.form.get("tutorial"))
        db.session.add(Feedback(
            tema_id=tema.id,
            tutorial_id=tutorial.id if tutorial else None,
            puntuacion=puntuacion,
            comentario=comentario,
            nombre=nombre,
            categoria=categoria,
        ))
        db.session.commit()
        flash("¡Gracias por tu feedback!", "ok")
        return redirect(url_for("ui.ver_tema", tema_slug=tema.slug))

    return render_template(
        "feedback_nuevo.html", tema=tema, categorias=CATEGORIAS_FEEDBACK,
        opciones_tutoriales=_opciones_tutoriales_tema(tema), valores=None,
    )
