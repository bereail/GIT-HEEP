import re
import unicodedata


def slugify(texto):
    """Convierte un título en un slug simple (sin depender de una librería
    externa solo para esto): minúsculas, sin tildes, espacios y símbolos
    cambiados por guiones."""
    texto = unicodedata.normalize("NFD", texto or "")
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = texto.lower().strip()
    texto = re.sub(r"[^a-z0-9]+", "-", texto)
    return texto.strip("-") or "item"


def lineas_a_lista(texto):
    """Convierte un textarea (una entrada por línea) en una lista de
    strings, descartando líneas vacías."""
    if not texto:
        return []
    return [linea.strip() for linea in texto.splitlines() if linea.strip()]
