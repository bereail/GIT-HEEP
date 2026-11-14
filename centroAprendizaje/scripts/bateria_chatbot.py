"""Batería de preguntas reales para afinar el chatbot.

Le hace cada pregunta al chatbot de la base local (la de `instance/`, así
que antes hay que correr los importadores) y compara la respuesta con lo
esperado. No es un test automático: el resultado depende del contenido.

    python scripts/bateria_chatbot.py          # solo las que fallan
    python scripts/bateria_chatbot.py -v       # todas
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from app.services.buscador import normalizar  # noqa: E402

MH, EX, CO = "mihospital", "timbo-expedientes", "timbo-compras"

# (tema, pregunta, parte del título esperado). "OTRO:<tema>" = tiene que
# derivar a ese tema; "CHARLA" = saludo; None = no debería responder directo.
PREGUNTAS = [
    # miHospital
    (MH, "cómo busco un paciente", "buscar un paciente"),
    (MH, "no puedo entrar", "ingresar"),
    (MH, "cargar una cirugía", "nueva cirugia"),
    (MH, "ver la ocupación de camas", "ocupacion"),
    (MH, "turnos de consultorio", "turnos|agenda"),
    (MH, "qué es el CIE-10", "cie"),
    (MH, "altas del día", "altas"),
    (MH, "lista de espera quirófano", "lista de espera"),
    (MH, "cómo pido el permiso de administrador local", "administrador"),
    (MH, "youtube está bloqueado", "youtube"),
    (MH, "cómo hago un pase en timbo", "OTRO:" + EX),
    (MH, "internar un paciente", "ocupacion|internacion"),
    (MH, "agenda de un médico", "profesionales"),
    (MH, "hola", "CHARLA"),
    # TIMBÓ (Expedientes)
    (EX, "cómo hago un pase", "pase"),
    (EX, "cómo abro un expediente", "abrir un expediente"),
    (EX, "cómo pido una carátula", "caratula"),
    (EX, "subir un archivo", "subir un archivo"),
    (EX, "cómo firmo un documento", "firmar"),
    (EX, "olvidé mi contraseña", "contrasena"),
    (EX, "cómo busco un expediente", "buscar un expediente"),
    (EX, "qué es un documento oficial", "documento oficial"),
    (EX, "corregir un documento que subí mal", "subsanar"),
    (EX, "me equivoqué de documento", "subsanar|equivocado"),
    (EX, "poner un expediente en guarda temporal", "guarda"),
    (EX, "cómo archivo un expediente", "archiv"),
    (EX, "necesito ver un expediente de otra oficina", "vista"),
    (EX, "cómo le doy vista al tribunal de cuentas", "vista"),
    (EX, "cómo pido una licencia", "licencia"),
    (EX, "firmador digital", "firmador"),
    (EX, "crear mi ID ciudadana", "id ciudadana"),
    (EX, "qué es timbo", "que es timbo"),
    (EX, "atención virtual", "atencion virtual"),
    (EX, "un ciudadano mandó un trámite por atención virtual", "revisar solicitudes"),
    (EX, "rechazar un documento del ciudadano", "solicitudes"),
    (EX, "generar expediente desde atención virtual", "finalizar, generar"),
    (EX, "enviar aviso al ciudadano", "trabajar el expediente"),
    (EX, "cómo hago una resolución", "resolucion"),
    (EX, "protocolizar", "protocoliz"),
    (EX, "mandar una comunicación oficial", "comunicacion"),
    (EX, "notificar a un ciudadano", "comunicable"),
    (EX, "hacer una nota", "nota"),
    (EX, "firma conjunta", "documento oficial"),
    (EX, "tomar un expediente", "tomar"),
    (EX, "vincular un documento oficial", "ya firmado"),
    (EX, "fusionar expedientes", "fusionar"),
    (EX, "rendir un subsidio", "subsidio"),
    (EX, "no me deja firmar", "firm"),
    (EX, "qué es el SIN", "sin"),
    (EX, "documento embebido", "embebido"),
    (EX, "subir un pdf como documento oficial", "importado"),
    (EX, "cargar una cirugía", "OTRO:" + MH),
    (EX, "gracias", "CHARLA"),
    # TIMBÓ Compras
    (CO, "cómo hago una compra", "compra"),
    (CO, "quiero comprar guantes", "guantes"),
    (CO, "cómo oferto", "presentar la oferta"),
    (CO, "cómo presento una oferta", "oferta"),
    (CO, "impugnar", "impugna"),
    (CO, "subsanar una oferta", "subsanar"),
    (CO, "hacer una consulta sobre el pliego", "consulta"),
    (CO, "cómo me inscribo como proveedor", "proveedor"),
    (CO, "qué es el RUPC", "rupc"),
    (CO, "compra directa", "compra directa"),
    (CO, "cómo hago el CD-01", "generar el formulario"),
    (CO, "formulario cd01", "cd-01"),
    (CO, "decisorio preventivo", "decisorio"),
    (CO, "correr vista al tribunal de cuentas", "tribunal"),
    (CO, "publicar en el portal", "publicar"),
    (CO, "qué procedimiento corresponde según el monto", "monto"),
    (CO, "montos 2026", "monto"),
    (CO, "urgencia", "urgencia"),
    (CO, "el proceso quedó desierto", "desierto"),
    (CO, "armar el pliego", "pliego"),
    (CO, "evaluar ofertas", "evaluar"),
    (CO, "preadjudicar", "preadjudicar"),
    (CO, "adjudicar", "adjudicar y cerrar"),
    (CO, "después de adjudicar", "despues de adjudicar"),
    (CO, "el artículo no está en el catálogo", "articulo"),
    (CO, "pedir el alta de un artículo", "articulo"),
    (CO, "usuarios del SIN", "sin"),
    (CO, "no puedo cargar artículos", "articulo"),
    (CO, "notificar a un proveedor", "proveedor"),
    (CO, "no me deja firmar", "firmar"),
    (CO, "cómo subo un archivo", "OTRO:" + EX),
    (CO, "qué es el supervisor", "supervisor"),
    (CO, "pago de una compra directa", "compra directa|armar el expediente"),
    (CO, "buscar un paciente", "OTRO:" + MH),
    (CO, "chau", "CHARLA"),
]


def _titulo(datos):
    if datos.get("charla"):
        return "CHARLA"
    if datos.get("otro_tema"):
        return "OTRO:" + datos["otro_tema"]["tema"]
    if datos.get("encontrado"):
        m = re.search(r"<b>(.*?)</b>", datos.get("html", ""))
        return m.group(1) if m else datos.get("html", "")[:60]
    if datos.get("quiso_decir"):
        return "¿Te referís a...? " + " | ".join(datos["quiso_decir"])
    return "(sin respuesta)"


def main():
    detalle = "-v" in sys.argv
    app = create_app()
    cliente = app.test_client()
    with app.app_context():
        from app.models import Tema
        nombres = {t.slug: t.nombre for t in Tema.query.all()}
    fallas = 0
    for tema, pregunta, esperado in PREGUNTAS:
        datos = cliente.post(f"/temas/{tema}/chatbot", json={"mensaje": pregunta}).get_json()
        titulo = _titulo(datos)
        if esperado and esperado.startswith("OTRO:"):
            ok = titulo == "OTRO:" + nombres[esperado[5:]]
        elif esperado == "CHARLA":
            ok = titulo == "CHARLA"
        elif esperado is None:
            ok = not datos.get("encontrado")
        else:
            # "a|b": vale cualquiera de las dos.
            ok = datos.get("encontrado") and any(normalizar(e) in normalizar(titulo) for e in esperado.split("|"))
        fallas += not ok
        if detalle or not ok:
            print(f"{'OK ' if ok else 'MAL'} [{tema}] {pregunta!r} → {titulo}")
    print(f"\n{len(PREGUNTAS) - fallas}/{len(PREGUNTAS)} bien")


if __name__ == "__main__":
    main()
