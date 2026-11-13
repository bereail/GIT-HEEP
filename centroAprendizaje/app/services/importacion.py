"""Ayudas compartidas por los scripts que importan temas.

Los importadores borran el tema y lo vuelven a crear desde el JSON. El
contenido se recrea solo, pero lo que dejaron los usuarios (consultas,
valoraciones y estadísticas) no: apunta al id viejo del tema y, en el caso
de las valoraciones, al id viejo de la lección. Estas funciones lo pasan al
tema nuevo para que no quede huérfano.

Uso en un importador:
    estado = recordar_datos_de_usuarios(existente)   # antes de borrar el tema
    ...crear tema, categorías y tutoriales...
    reasignar_datos_de_usuarios(estado, tema)          # después del flush
"""

from app.models import Categoria, Consulta, Feedback, Tutorial
from app.models.evento_uso import EventoUso


def _lecciones(tema_id):
    filas = (
        Tutorial.query.join(Categoria, Tutorial.categoria_id == Categoria.id)
        .filter(Categoria.tema_id == tema_id)
        .with_entities(Tutorial.id, Categoria.slug, Tutorial.slug)
        .all()
    )
    return {tid: (cslug, tslug) for tid, cslug, tslug in filas}


def recordar_datos_de_usuarios(tema):
    if tema is None:
        return None
    return {"tema_id": tema.id, "lecciones": _lecciones(tema.id)}


def reasignar_datos_de_usuarios(estado, tema_nuevo):
    if not estado:
        return
    viejo = estado["tema_id"]
    if viejo != tema_nuevo.id:
        for modelo in (Consulta, Feedback, EventoUso):
            modelo.query.filter_by(tema_id=viejo).update({"tema_id": tema_nuevo.id}, synchronize_session=False)

    # Las valoraciones de una lección se vuelven a enganchar por slug; si la
    # lección ya no existe, quedan como valoración general del tema.
    nuevos = {clave: tid for tid, clave in _lecciones(tema_nuevo.id).items()}
    for feedback in Feedback.query.filter_by(tema_id=tema_nuevo.id).filter(Feedback.tutorial_id.isnot(None)):
        clave = estado["lecciones"].get(feedback.tutorial_id)
        feedback.tutorial_id = nuevos.get(clave)
