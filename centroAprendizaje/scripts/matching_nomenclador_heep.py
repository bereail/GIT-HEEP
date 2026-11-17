"""Compara el nomenclador interno completo del HEEP (todas las bodegas)
contra el Catálogo WEB oficial de la Provincia de Santa Fe, y genera
`scripts/equivalencias_articulos.csv` con una fila por artículo interno:
el código/nombre del Catálogo WEB que mejor matchea, un nivel de
confianza (alta / dudosa / sin_match) y la bodega de origen.

Fuentes (no versionadas, carpeta `nomencladorDb/` fuera del repo):
- totalarticulos (1).csv: id, nombre, categoria_id, categoria_nombre,
  bodega_id, bodega_nombre, codigo_articulo. Exportado tal cual de la
  app de compras del HEEP, con alguna descripción partida en varias
  líneas físicas.
- Catalogo_WEB_al_<fecha>.csv: catálogo oficial completo, separado por
  "|", 8 columnas (Rubro/Especie, Sub-Rubro/Familia, Código Bien o
  Servicio, Bien o Servicio/Elemento, Objeto del Gasto, Código Ítem,
  Ítem Específico, Cód. Sistema Externo).

Es 100% automático (sin la revisión manual fila por fila que se hizo en
las tandas anteriores de 1089 artículos): a esta escala (27 mil) no es
viable a mano. Las reglas duras son las mismas que ya habían encontrado
errores reales en las tandas anteriores (ver CLAUDE.md del proyecto):
números como tokens completos, "con"/"sin" nunca de relleno, formas o
vías especiales no intercambiables.

Uso: python scripts/matching_nomenclador_heep.py
"""

import csv
import os
import re
import unicodedata
from collections import Counter, defaultdict
from difflib import SequenceMatcher

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA_FUENTES = os.path.join(os.path.dirname(RAIZ), "nomencladorDb")
ARCHIVO_INTERNO = os.path.join(CARPETA_FUENTES, "totalarticulos (1).csv")
ARCHIVO_CATALOGO = os.path.join(CARPETA_FUENTES, "Catalogo_WEB_al_17112026.csv")
ARCHIVO_SALIDA = os.path.join(RAIZ, "scripts", "equivalencias_articulos.csv")

STOPWORDS = {
    "DE", "DEL", "LA", "EL", "LOS", "LAS", "Y", "O", "A", "EN", "PARA", "POR",
    "X", "UNIDAD", "UNIDADES", "UND", "UN", "UNA", "CAJA", "ENVASE", "PAQUETE",
    "PRESENTACION", "TIPO", "USO", "CON", "SIN",
}
# CON y SIN no son stopwords semánticas (cambian el sentido), pero se
# tratan aparte como bigramas "con_X"/"sin_X": se excluyen del cálculo de
# cobertura general de palabras sueltas para no duplicar su efecto.

FORMAS_VIA = {
    "SL": "SL", "SUBLINGUAL": "SL",
    "LP": "LP_AP", "AP": "LP_AP", "LIBERACION": "LP_AP", "PROLONGADA": "LP_AP",
    "VAG": "VAG", "VAGINAL": "VAG",
    "RECTAL": "RECTAL",
    "OFTAL": "OFTAL", "OFTALMICA": "OFTAL", "OFTALMICO": "OFTAL",
    "NASAL": "NASAL",
    "IV": "IV", "EV": "IV",
    "IM": "IM",
    "SC": "SC",
}

RE_TOKEN = re.compile(r"[A-ZÑ0-9][A-ZÑ0-9.\-/]*")
LONGITUD_RAIZ = 5  # abreviaturas con punto (DESCART.) deben matchear DESCARTABLE


def quitar_tildes(texto):
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalizar(texto):
    texto = quitar_tildes(texto.upper())
    texto = texto.replace('"', " ").replace("'", " ")
    return texto


def tokenizar(texto):
    return RE_TOKEN.findall(normalizar(texto))


def es_numerico(token):
    return any(c.isdigit() for c in token)


def raiz(palabra):
    """Prefijo usado para matchear abreviaturas y plurales: DESCART(.) y
    DESCARTABLE comparten la misma raíz de 5 letras."""
    return palabra.rstrip(".")[:LONGITUD_RAIZ]


def analizar_tokens(texto):
    """Devuelve (raices_clave, tokens_numericos, formas_via, con_sin) de un texto."""
    tokens = tokenizar(texto)
    raices = set()
    numericos = set()
    formas = set()
    con_sin = set()
    previo = None
    for tok_crudo in tokens:
        tok = tok_crudo.rstrip(".")
        if es_numerico(tok):
            numericos.add(tok)
        else:
            if tok in FORMAS_VIA:
                formas.add(FORMAS_VIA[tok])
            if tok not in STOPWORDS and len(tok) >= 3:
                raices.add(raiz(tok))
        if previo in ("CON", "SIN"):
            con_sin.add(f"{previo}_{tok}")
        previo = tok
    return raices, numericos, formas, con_sin


def cargar_catalogo(ruta):
    filas = []
    with open(ruta, encoding="utf-8-sig") as f:
        lector = csv.reader(f, delimiter="|")
        next(lector)  # header
        for r in lector:
            if len(r) < 8:
                continue
            rubro, sub_rubro, _cod_bien, bien, _objeto_gasto, cod_item, item_especifico, _cod_ext = r[:8]
            texto_comparar = f"{bien} {item_especifico}"
            palabras, numericos, formas, con_sin = analizar_tokens(texto_comparar)
            filas.append({
                "rubro_especie": rubro.strip(),
                "sub_rubro_familia": sub_rubro.strip(),
                "bien_o_servicio": bien.strip(),
                "item_especifico": item_especifico.strip(),
                "codigo_catalogo": cod_item.strip(),
                "texto_norm": normalizar(texto_comparar),
                "palabras": palabras,
                "numericos": numericos,
                "formas": formas,
                "con_sin": con_sin,
            })
    return filas


def cargar_internos(ruta):
    """Lee totalarticulos.csv, uniendo líneas de continuación (descripciones
    con salto de línea literal, terminadas en '\\') a la fila anterior."""
    registros = []
    patron_inicio = re.compile(r"^\d+\t")
    with open(ruta, encoding="utf-8") as f:
        lineas = f.readlines()

    def partir(partes):
        """id, nombre, cat_id, cat_nombre, bodega_id, bodega_nombre,
        codigo_articulo. Algunas filas traen 1 o 2 campos vacíos de más,
        siempre justo después del nombre y antes de cat_id: los últimos 5
        campos son siempre cat_id/cat_nombre/bodega_id/bodega_nombre/
        codigo_articulo, lo que venga entre el id y esos últimos 5 es el
        nombre (posiblemente con campos vacíos). Si la fila viene cortada
        (menos de 6 campos después del id: el resto llega en la línea de
        continuación siguiente), se deja todo lo demás vacío por ahora."""
        id_ = partes[0]
        resto = partes[1:]
        if len(resto) >= 6:
            nombre = " ".join(p for p in resto[:-5] if p).strip()
            cat_id, cat_nombre, bodega_id, bodega_nombre, codigo_articulo = resto[-5:]
        else:
            nombre = " ".join(p for p in resto if p).strip()
            cat_id = cat_nombre = bodega_id = bodega_nombre = codigo_articulo = ""
        return [id_, nombre, cat_id, cat_nombre, bodega_id, bodega_nombre, codigo_articulo]

    actuales = None
    for linea in lineas:
        linea = linea.rstrip("\n")
        if patron_inicio.match(linea):
            if actuales is not None:
                registros.append(actuales)
            actuales = partir(linea.split("\t"))
        else:
            # continuación de la descripción del registro anterior: a veces
            # es solo texto suelto, y a veces (3 casos en 27666) el nombre
            # tenía un salto de línea real en el medio y los demás campos
            # vienen pegados a esta misma línea.
            if actuales is not None:
                partes_cont = linea.split("\t")
                actuales[1] = (actuales[1] + " " + partes_cont[0].rstrip("\\").strip()).strip()
                if len(partes_cont) > 1:
                    actuales[2:7] = partir(["_"] + partes_cont)[2:7]
    if actuales is not None:
        registros.append(actuales)

    internos = []
    for id_, nombre, cat_id, cat_nombre, bodega_id, bodega_nombre, codigo_articulo in registros:
        nombre = re.sub(r"\s*\\\s*", " ", nombre).strip()
        if not nombre:
            continue
        internos.append({
            "codigo_interno": id_.strip(),
            "nombre": nombre,
            "categoria_id": cat_id.strip(),
            "categoria_nombre": cat_nombre.strip(),
            "bodega_id": bodega_id.strip(),
            "bodega_nombre": bodega_nombre.strip(),
            "codigo_articulo": codigo_articulo.strip(),
        })
    return internos


def quitar_duplicados_exactos(internos):
    """Si dos artículos internos tienen el mismo nombre (normalizado) y la
    misma bodega, son el mismo artículo cargado dos veces: se deja uno solo
    (el de código interno más bajo) y se descartan los demás."""
    vistos = {}
    unicos = []
    descartados = 0
    for art in internos:
        clave = (normalizar(art["nombre"]), art["bodega_nombre"].upper())
        anterior = vistos.get(clave)
        if anterior is None:
            vistos[clave] = art
            unicos.append(art)
        else:
            descartados += 1
            # conservar el de código interno más bajo
            try:
                nuevo_es_menor = int(art["codigo_interno"]) < int(anterior["codigo_interno"])
            except ValueError:
                nuevo_es_menor = False
            if nuevo_es_menor:
                idx = unicos.index(anterior)
                unicos[idx] = art
                vistos[clave] = art
    return unicos, descartados


def construir_indice(catalogo):
    indice = defaultdict(list)
    for i, fila in enumerate(catalogo):
        for palabra in fila["palabras"]:
            indice[palabra].append(i)
    return indice


UMBRAL_DUDOSA_COBERTURA = 0.4
UMBRAL_DUDOSA_SIMILITUD = 0.32
UMBRAL_ALTA_COBERTURA = 0.9
UMBRAL_ALTA_SIMILITUD = 0.55


def _jaccard_numeros(art_numericos, cand_numericos):
    """Los números (dosis/calibre) son lo que distingue items de una misma
    familia genérica (ej. "AGUJA DESCARTABLE 16/5" vs "...25/6"): pesan
    mucho más que la cobertura de palabras en el desempate."""
    if not art_numericos and not cand_numericos:
        return 1.0, True
    if art_numericos and not cand_numericos:
        return 0.0, False
    if not art_numericos and cand_numericos:
        return 0.5, False
    interseccion = art_numericos & cand_numericos
    union = art_numericos | cand_numericos
    jaccard = len(interseccion) / len(union)
    return jaccard, (art_numericos == cand_numericos)


def mejor_candidato(art_palabras, art_numericos, art_formas, art_con_sin, art_texto_norm,
                     catalogo, indice, tope_candidatos=40):
    conteo = Counter()
    for palabra in art_palabras:
        for i in indice.get(palabra, ()):
            conteo[i] += 1
    if not conteo:
        return None, 0.0, 0.0, False, False

    mejor = None
    mejor_score = -1.0
    mejor_cobertura = 0.0
    mejor_similitud = 0.0
    mejor_num_ok = False
    mejor_forma_ok = False

    for i, _comparten in conteo.most_common(tope_candidatos):
        cand = catalogo[i]
        if art_palabras:
            cobertura = len(art_palabras & cand["palabras"]) / len(art_palabras)
        else:
            cobertura = 0.0
        similitud = SequenceMatcher(None, art_texto_norm, cand["texto_norm"]).ratio()
        jaccard_num, num_ok = _jaccard_numeros(art_numericos, cand["numericos"])
        forma_ok = art_formas == cand["formas"]
        consin_ok = art_con_sin == cand["con_sin"]

        score = cobertura * 0.3 + similitud * 0.3 + jaccard_num * 0.35
        if forma_ok:
            score += 0.025
        if consin_ok:
            score += 0.025

        if score > mejor_score:
            mejor_score = score
            mejor = cand
            mejor_cobertura = cobertura
            mejor_similitud = similitud
            mejor_num_ok = num_ok and consin_ok
            mejor_forma_ok = forma_ok

    return mejor, mejor_cobertura, mejor_similitud, mejor_num_ok, mejor_forma_ok


def clasificar(cobertura, similitud, num_ok, forma_ok):
    if (cobertura >= UMBRAL_ALTA_COBERTURA and similitud >= UMBRAL_ALTA_SIMILITUD
            and num_ok and forma_ok):
        return "alta"
    if cobertura >= UMBRAL_DUDOSA_COBERTURA or similitud >= UMBRAL_DUDOSA_SIMILITUD:
        return "dudosa"
    return "sin_match"


def nota_para(confianza, cand, num_ok, forma_ok):
    if confianza == "alta":
        return "match automático (candidato con cobertura y similitud altas, números y forma/vía coinciden)"
    if confianza == "sin_match":
        return "no se encontró ningún candidato razonable en el catálogo oficial (cobertura y similitud por debajo del mínimo); puede hacer falta pedir la incorporación del ítem"
    motivos = []
    if cand and not num_ok:
        motivos.append("los números/medidas no coinciden exactos")
    if cand and not forma_ok:
        motivos.append("la forma o vía (SL/LP-AP/VAG/rectal/etc.) no coincide")
    if not motivos:
        motivos.append("similitud parcial, confirmar antes de usar")
    return "match automático con dudas: " + "; ".join(motivos)


def main():
    print(f"Cargando catálogo oficial: {ARCHIVO_CATALOGO}")
    catalogo = cargar_catalogo(ARCHIVO_CATALOGO)
    print(f"  {len(catalogo)} ítems del catálogo oficial.")

    print(f"Cargando nomenclador interno del HEEP: {ARCHIVO_INTERNO}")
    internos = cargar_internos(ARCHIVO_INTERNO)
    print(f"  {len(internos)} artículos internos (antes de deduplicar).")

    internos, descartados = quitar_duplicados_exactos(internos)
    print(f"  {descartados} duplicados exactos (mismo nombre y bodega) descartados.")
    print(f"  {len(internos)} artículos internos únicos a comparar.")

    print("Construyendo índice invertido del catálogo...")
    indice = construir_indice(catalogo)

    contadores = Counter()
    filas_salida = []
    for n, art in enumerate(internos, start=1):
        if n % 2000 == 0:
            print(f"  ...{n}/{len(internos)}")
        palabras, numericos, formas, con_sin = analizar_tokens(art["nombre"])
        texto_norm = normalizar(art["nombre"])

        cand, cobertura, similitud, num_ok, forma_ok = mejor_candidato(
            palabras, numericos, formas, con_sin, texto_norm, catalogo, indice
        )
        confianza = clasificar(cobertura, similitud, num_ok, forma_ok)
        contadores[confianza] += 1

        nota = nota_para(confianza, cand, num_ok, forma_ok)
        nota = f"[cod. interno {art['codigo_interno']}] {nota}"

        filas_salida.append({
            "nombre_interno": art["nombre"],
            "codigo_catalogo": cand["codigo_catalogo"] if cand else "",
            "rubro_especie": cand["rubro_especie"] if cand else "",
            "sub_rubro_familia": cand["sub_rubro_familia"] if cand else "",
            "bien_o_servicio": cand["bien_o_servicio"] if cand else "",
            "item_especifico": cand["item_especifico"] if cand else "",
            "confianza": confianza,
            "origen": "Nomenclador interno completo (todas las bodegas)",
            "notas": nota,
            "bodega": art["bodega_nombre"],
            "codigo_articulo": art["codigo_articulo"],
            "codigo_interno": art["codigo_interno"],
        })

    print("Clasificación final:", dict(contadores))

    with open(ARCHIVO_SALIDA, "w", encoding="utf-8", newline="") as f:
        campos = [
            "nombre_interno", "codigo_catalogo", "rubro_especie", "sub_rubro_familia",
            "bien_o_servicio", "item_especifico", "confianza", "origen", "notas", "bodega",
            "codigo_articulo", "codigo_interno",
        ]
        escritor = csv.DictWriter(f, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(filas_salida)

    print(f"Escrito: {ARCHIVO_SALIDA} ({len(filas_salida)} filas)")


if __name__ == "__main__":
    main()
