"""Ayudas compartidas por los scripts que importan temas.

Los importadores borran el tema y lo vuelven a crear desde el JSON. El
contenido se recrea solo, pero lo que dejaron los usuarios (consultas y
preguntas del chatbot) no: hay que pasarlo al tema nuevo para que no quede
apuntando a un id que ya no existe.
"""

from app.extensions import db
from app.models import Consulta, PreguntaChatbot


def reasignar_datos_de_usuarios(tema_id_viejo, tema_id_nuevo):
    if tema_id_viejo is None or tema_id_viejo == tema_id_nuevo:
        return
    for modelo in (Consulta, PreguntaChatbot):
        modelo.query.filter_by(tema_id=tema_id_viejo).update(
            {"tema_id": tema_id_nuevo}, synchronize_session=False
        )
