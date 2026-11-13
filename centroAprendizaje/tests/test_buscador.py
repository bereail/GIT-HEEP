"""Reglas del buscador del chatbot que no dependen del contenido real."""

from app.services import buscador


def _entrada(kind, title, texto, peso=2, **extra):
    return {"kind": kind, "title": title, "texto": buscador.normalizar(texto), "peso": peso, **extra}


def _primero(indice, consulta, **kwargs):
    resultados = buscador.buscar_con_puntaje(indice, consulta, **kwargs)
    return resultados[0][1]["title"] if resultados else None


def test_palabra_entera_le_gana_a_pedazo_de_otra():
    indice = [
        _entrada("Leccion", "Sistema de turnos", "sistema de turnos"),
        _entrada("Glosario", "SIN", "sin sistema de informacion normativa", peso=1),
    ]
    assert _primero(indice, "¿Qué es el SIN?") == "SIN"


def test_articulo_del_nomenclador_solo_si_coincide_entero():
    indice = [
        _entrada("Nomenclador", "Sistema de aspiración cerrado", "sistema de aspiracion cerrado", peso=1.5),
        _entrada("Nomenclador", "Guantes de látex", "guantes de latex", peso=1.5),
        _entrada("Tarea", "¿Cómo hago una compra?", "como hago una compra comprar", peso=3),
    ]
    assert _primero(indice, "se cayó el sistema") is None
    assert _primero(indice, "quiero comprar guantes") == "Guantes de látex"


def test_frase_clave_entera_en_la_pregunta_suma():
    indice = [
        _entrada("Tarea", "¿Cómo subo un archivo?", "como subo un archivo subir archivo", peso=3),
        _entrada(
            "Tarea", "¿Cómo archivo un expediente?", "guarda temporal archivo un expediente", peso=3,
            frases=["archivo un expediente"],
        ),
    ]
    assert _primero(indice, "cómo archivo un expediente") == "¿Cómo archivo un expediente?"


def test_ignora_el_nombre_del_sistema():
    indice = [
        _entrada("Tarea", "¿Cómo entro a TIMBÓ?", "como entro a timbo entrar", peso=3),
        _entrada("Tarea", "¿Cómo hago un pase?", "enviar el expediente pase", peso=3),
    ]
    assert _primero(indice, "cómo hago un pase en timbo", ignorar={"timbo"}) == "¿Cómo hago un pase?"


def test_saludos_y_agradecimientos():
    assert buscador.respuesta_de_charla("Hola!")
    assert buscador.respuesta_de_charla("muchas gracias")
    assert buscador.respuesta_de_charla("hola, ¿cómo hago un pase a otra oficina?") is None
    assert buscador.respuesta_de_charla("cómo hago un pase") is None
