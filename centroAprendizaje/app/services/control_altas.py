"""Control final antes de pedir las altas en el Catálogo WEB (solo admin).

Toma lo que un servicio dejó en «Hay que cargar» y lo vuelve a mirar contra
la última copia guardada del Catálogo WEB, para no pedir el alta de algo que
ya existe ni pedir dos veces lo mismo. Solo LEE: no cambia respuestas.

Se compara por PALABRAS (sin tildes, plurales ni mayúsculas; «PEN DRIVE» =
«PENDRIVE»); los números y unidades (16 GB, 500 GR) no cuentan para decir
que se parece, pero sí para decir si es la misma medida. Cada artículo queda
en un estado (el primero que aplique):
- «apareció»: un ítem dado de alta DESPUÉS del envío tiene sus mismas
  palabras y medida → probablemente ya no haga falta pedirlo.
- «puede existir»: un ítem tiene sus mismas palabras y medida → mirarlo.
- «posible repetido»: otro artículo de la lista es casi igual y con la misma
  medida → si es el mismo, pedirlo una sola vez.
- «otra medida»: existe con esas palabras pero en otra medida o capacidad
  (PEN DRIVE 8 GB y el servicio pide 16 GB) → pedir el alta en ese elemento.
- «limpio»: nada parecido → para pedir el alta.
Rubro, subrubro, elemento y objeto del gasto salen del ítem más parecido
(si cubre al menos la mitad de las palabras) y van como SUGERENCIA a confirmar. Además revisa los
«Ya están en TIMBÓ»: si el código a usar dejó de existir o es «NO UTILIZAR».
La planilla sigue el orden del formulario «Solicitud de alta de bien o
servicio» de TIMBÓ.
"""
import csv
import glob
import io
import os
import re
import unicodedata
from collections import defaultdict

from app.services import catalogo_diario as cd
from app.services import llaves_servicio as ls

UMBRAL = 0.6          # parte de las palabras del artículo que tiene que estar en el ítem
MAX_PARECIDOS = 3

ESTADOS = {
    "aparecio": ("Apareció en el catálogo después del envío: probablemente ya no haya que pedirlo", "azul"),
    "puede_existir": ("Puede que ya exista: mirá los parecidos antes de pedirlo", "amarillo"),
    "repetido": ("Posible repetido en la lista: si es el mismo, pedirlo una sola vez", "naranja"),
    "otra_medida": ("Existe en otra medida o capacidad: pedir el alta dentro de ese elemento", "verde"),
    "sin_buscar": ("Nombre muy corto para buscarlo solo: revisalo a mano", "gris"),
    "limpio": ("No se encontró nada parecido: para pedir el alta", "verde"),
}
ORDEN_ESTADOS = ("aparecio", "puede_existir", "repetido", "otra_medida", "sin_buscar", "limpio")

_VACIAS = cd._VACIAS | {"unidad", "unidades", "uni", "cada", "marca", "modelo", "aprox", "superior", "minimo",
                        "de", "la", "el", "en", "lo", "al", "su", "es", "le", "se", "no", "si", "o", "a", "e"}
# Abreviaturas de unidades que se escriben de muchas formas.
_UNIDADES = {"mts": "metro", "mt": "metro", "mtrs": "metro", "mtr": "metro", "metros": "metro", "m": "metro",
             "lts": "litro", "lt": "litro", "ltr": "litro", "litros": "litro", "l": "litro",
             "grs": "gramo", "gr": "gramo", "g": "gramo", "gramos": "gramo", "kgs": "kg", "kilo": "kg", "kilos": "kg",
             "cms": "cm", "uds": "unidad", "und": "unidad", "un": "unidad", "w": "watt", "watts": "watt"}
# Medidas: cuentan para «misma medida», no para «se parece».
_MEDIDAS = {"metro", "litro", "gramo", "kg", "cm", "mm", "ml", "cc", "mg", "gb", "tb", "mb", "watt", "pulgada"}


def _tokens(texto):
    t = unicodedata.normalize("NFKD", str(texto or "").lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"(\d)([a-z])", r"\1 \2", re.sub(r"([a-z])(\d)", r"\1 \2", t))
    t = re.sub(r"(\d)[.,](\d)", r"\1_\2", t)          # 1.5 / 1,5 → un solo número
    t = "".join(c if c.isalnum() or c == "_" else " " for c in t)
    salida = []
    for w in t.split():
        w = _UNIDADES.get(w, w)
        if len(w) > 5 and w.endswith("es") and w[-3] in "nlrdz":   # bidones → bidon
            w = w[:-2]
        elif len(w) > 4 and w.endswith("s") and not w[-2].isdigit():   # plural simple
            w = w[:-1]
        salida.append(w)
    return salida


def _es_numero(w):
    return w.replace("_", "").isdigit()


def palabras(texto):
    """Palabras que dicen QUÉ es (sin números, medidas ni palabras vacías)."""
    return {w for w in _tokens(texto) if len(w) >= 2 and not _es_numero(w) and w not in _MEDIDAS and w not in _VACIAS}


def medida(texto):
    """Números y unidades («16 gb», «500 gramo»): para saber si es la misma medida."""
    return {w for w in _tokens(texto) if _es_numero(w) or w in _MEDIDAS}


def _pares(texto):
    """Pares de palabras seguidas escritas juntas: {«pendrive»: {pen, drive}}."""
    t = [w for w in _tokens(texto) if w.isalpha() and len(w) >= 2]
    return {a + b: {a, b} for a, b in zip(t, t[1:])}


def leer_completo(ruta):
    """{código ítem: fila con las 8 columnas} de una copia guardada."""
    with open(ruta, encoding="utf-8") as f:
        texto = f.read().lstrip("﻿")
    lector = csv.reader(io.StringIO(texto), delimiter="|", quotechar='"')
    next(lector, None)
    items = {}
    for fila in lector:
        if len(fila) >= 7 and fila[5].strip():
            fila = [" ".join(c.split()) for c in fila] + [""] * (8 - len(fila))
            items[fila[5]] = fila[:8]
    return items


def copia_anterior_a(instancia, momento):
    """La copia del catálogo más nueva guardada antes de `momento` (UTC, como
    se guarda en la base). Se compara por la fecha del archivo: el nombre usa
    la hora local de la máquina. Si no hay ninguna anterior, la más vieja."""
    from datetime import timezone
    archivos = sorted(glob.glob(os.path.join(cd.carpeta_catalogo(instancia), "catalogo_*.csv")), key=os.path.getmtime)
    if not archivos or not momento:
        return None
    limite = (momento if momento.tzinfo else momento.replace(tzinfo=timezone.utc)).timestamp()
    anteriores = [a for a in archivos if os.path.getmtime(a) <= limite]
    return anteriores[-1] if anteriores else archivos[0]


class Buscador:
    """Índice de palabras del catálogo (sin los «NO UTILIZAR»)."""

    def __init__(self, catalogo):
        self.datos = {}
        self.indice = defaultdict(set)
        for codigo, fila in catalogo.items():
            texto = f"{fila[3]} {fila[6]}"
            if "NO UTILIZAR" in texto.upper():
                continue
            p = palabras(texto) | set(_pares(texto))
            self.datos[codigo] = (p, medida(texto), fila[2], palabras(fila[3]) | set(_pares(fila[3])), palabras(texto))
            for w in p:
                self.indice[w].add(codigo)
        # Para los tipeos: palabras largas agrupadas por sus 3 primeras letras
        # (solo se compara con las que empiezan igual: mucho más rápido).
        self.vocabulario = defaultdict(list)
        for w in self.indice:
            if len(w) >= 6:
                self.vocabulario[w[:3]].append(w)
        self._parecidas = {}

    def parecidas(self, w):
        """Palabras del catálogo escritas casi igual (errores de tipeo:
        SABOREAUD / SABOUROD, MARGENTA / MAGENTA). Solo palabras largas."""
        if len(w) < 6:
            return set()
        if w not in self._parecidas:
            import difflib
            self._parecidas[w] = set(difflib.get_close_matches(w, self.vocabulario.get(w[:3], []), n=5, cutoff=0.8)) - {w}
        return self._parecidas[w]

    def buscar(self, nombre):
        """Ítems con al menos una palabra en común: qué parte de las palabras
        del artículo cubren y si es la misma medida. Del más parecido al menos.
        None si el nombre no tiene palabras para buscar."""
        p = palabras(nombre)
        if not any(len(w) >= 3 for w in p):
            return None   # solo siglas cortas (CD, SD): se revisa a mano
        m = medida(nombre)
        pares = {j: partes & p for j, partes in _pares(nombre).items() if partes & p}
        variantes = {w: self.parecidas(w) for w in p}
        candidatos = set()
        for w in p | set(pares) | set().union(*variantes.values()):
            candidatos |= self.indice.get(w, set())
        lista = []
        for c in candidatos:
            q, mq, _, en_elemento, solas = self.datos[c]
            cubiertas = {w for w in p if w in q or variantes[w] & q}
            for junta, partes in pares.items():
                if junta in q:
                    cubiertas |= partes
            # Al menos una palabra de verdad en común (no «pro», «cd»…).
            if not any(len(w) >= 4 for w in cubiertas):
                continue
            # Misma medida, o un ítem genérico (sin medida) que puede servir.
            # Cuántas de sus palabras están en el NOMBRE DEL ELEMENTO: IMPRESORA
            # EPSON va con «IMPRESORA MULTIFUNCION», no con «TINTA PARA IMPRESORA».
            del_elemento = len({w for w in p if w in en_elemento}
                               | {w for j, partes in pares.items() if j in en_elemento for w in partes})
            puntaje = len(cubiertas) / len(p)
            # Ítem GENÉRICO: todas sus palabras están en el artículo («CABLE UTP»
            # para «Cable utp Furukawa Interior Gigalan Cat 6»): puede servir.
            juntas_art = {w for j, partes in pares.items() for w in partes if j in q}
            if len(solas) >= 2 and solas <= (p | juntas_art) and not mq:
                puntaje = 1.0
            lista.append((puntaje, m <= mq or not mq, len(q - p), c, del_elemento))
        # A igual parecido, primero el elemento con más ítems parecidos (PEN
        # DRIVE de informática antes que PEN DRIVE PARA ELECCIONES).
        por_elemento = defaultdict(int)
        for x in lista:
            por_elemento[self.datos[x[3]][2]] += 1
        lista.sort(key=lambda x: (-x[0], not x[1], -x[4], -por_elemento[self.datos[x[3]][2]], x[2], x[3]))
        return [{"codigo": c, "pct": round(100 * s), "misma_medida": mm} for s, mm, _, c, _ in lista]


def _texto_item(fila):
    return f"{fila[5]} — {fila[3]} / {fila[6]}"


def _repetidos(a, b):
    """Dos artículos de la lista que podrían ser el mismo: misma medida y
    mismas palabras (o una sola de diferencia)."""
    if medida(a) != medida(b):
        return False
    pa, pb = palabras(a), palabras(b)
    if not pa or not pb:
        return False
    chico, grande = sorted((pa, pb), key=len)
    return (len(chico & grande) / len(chico | grande) >= 0.8
            or (chico <= grande and len(grande - chico) <= 1 and len(chico) >= 2))


def _clave(texto):
    """Palabras de verdad (4+ letras) y pares juntos, para agrupar."""
    return {w for w in palabras(texto) if len(w) >= 4} | set(_pares(texto))


def agrupar(filas, buscador, catalogo):
    """Artículos de la lista que se podrían pedir como UNO genérico (varios
    cartuchos Epson → «CARTUCHO EPSON»): comparten al menos 2 palabras de
    verdad. El nombre genérico son las palabras que tienen la mayoría, en el
    orden del primero. Si el catálogo ya tiene ese genérico, se avisa: puede
    usarse como ítem general (con el detalle en la observación) sin pedir alta."""
    claves = [_clave(f["nombre"]) for f in filas]
    padre = list(range(len(filas)))

    def raiz(i):
        while padre[i] != i:
            padre[i] = padre[padre[i]]
            i = padre[i]
        return i
    for a in range(len(filas)):
        for b in range(a + 1, len(filas)):
            if len(claves[a] & claves[b]) >= 2:
                padre[raiz(a)] = raiz(b)
    juntos = defaultdict(list)
    for i in range(len(filas)):
        juntos[raiz(i)].append(i)
    grupos = []
    for miembros in juntos.values():
        if len(miembros) < 2:
            continue
        cuenta = defaultdict(int)
        for i in miembros:
            for w in palabras(filas[i]["nombre"]):
                cuenta[w] += 1
        mayoria = {w for w, n in cuenta.items() if n >= max(2, (len(miembros) * 6 + 9) // 10) and len(w) >= 3}
        orden = []
        for i in miembros:
            for w in _tokens(filas[i]["nombre"]):
                if w in mayoria and w not in orden:
                    orden.append(w)
        nombre = " ".join(orden).upper() or filas[miembros[0]]["nombre"]
        existentes = [{"codigo": h["codigo"], "texto": _texto_item(catalogo[h["codigo"]]), "pct": h["pct"]}
                      for h in (buscador.buscar(nombre) or []) if h["pct"] == 100][:MAX_PARECIDOS]
        grupos.append({"nombre": nombre, "miembros": [filas[i]["nombre"] for i in sorted(miembros)],
                       "codigos": [filas[i]["codigo"] for i in sorted(miembros)], "existentes": existentes})
    grupos.sort(key=lambda g: (-len(g["miembros"]), g["nombre"]))
    return grupos


# Bodegas que no dicen de qué servicio es un artículo (están en casi todos).
BODEGAS_GENERALES = {"FARMACIA", "DEPOSITO", "IMPRENTA", "COMPRAS"}
# Desde esta fecha la pantalla pregunta primero por el artículo del hospital.
PANTALLA_DOS_PREGUNTAS = "2026-11-24"


def _normal(texto):
    return " ".join(sorted(palabras(texto) | medida(texto)))


def inconsistencias(llave, items, respuestas, grupos, buscador):
    """Fallas posibles en la revisión de un servicio. Solo avisa: decide una
    persona. Cada aviso: {tipo, titulo, ayuda, filas: [(artículo, detalle)]}."""
    from app.services.llaves_servicio import clasificar
    avisos = []
    grupo_de = {}
    for i in items:
        grupo_de[i["id"]] = clasificar(i, respuestas.get(i["id"]))[0]
    por_id = {i["id"]: i for i in items}
    mios = set(llave.nombres_bodegas)

    def agregar(tipo, titulo, ayuda, filas):
        if filas:
            avisos.append({"tipo": tipo, "titulo": titulo, "ayuda": ayuda, "filas": filas})

    # 1. Mismo artículo (mismo nombre) con respuestas que no cierran.
    por_nombre = defaultdict(list)
    for i in items:
        por_nombre[_normal(i["n"])].append(i)
    filas = []
    for lista in por_nombre.values():
        destinos = {grupo_de[i["id"]] for i in lista} - {"falta"}
        if len(lista) > 1 and len(destinos) > 1:
            filas.append((lista[0]["n"], " · ".join(f"cód. {i['id']}: {_GRUPO_TEXTO[grupo_de[i['id']]]}" for i in lista)))
    agregar("contradiccion", "Mismo artículo con respuestas distintas",
            "Tienen el mismo nombre pero uno quedó para pedir y otro fuera (o al revés). Revisá cuál vale.", filas)

    # 2. Quedan fuera, pero se parecen mucho a algo que el servicio sí usa.
    usados = _Indice([i for i in items if grupo_de[i["id"]] in ("cargar", "estan")])
    filas = []
    for i in items:
        if grupo_de[i["id"]] != "fuera":
            continue
        parecido = usados.parecido(i["n"])
        if parecido:
            filas.append((i["n"], f"Quedó fuera, pero «{parecido['n']}» sí se usa"))
    agregar("fuera_parecido", "Quedó fuera algo parecido a lo que sí usan",
            "Puede estar bien (otro modelo que ya no se compra) o ser un error: si lo usan, hay que corregirlo.", filas)

    # 3. Respondido con la pantalla anterior: «Ya no se usa» / «No es de nuestro
    # servicio» cuando la tarjeta mostraba el artículo de TIMBÓ (caso PC MINI).
    filas = []
    for i in items:
        r = respuestas.get(i["id"])
        if (r and r.resultado in ("no_necesario", "otro_servicio") and i.get("cp")
                and r.actualizado_en and r.actualizado_en.strftime("%Y-%m-%d") < PANTALLA_DOS_PREGUNTAS):
            filas.append((i["n"], f"«{_GRUPO_TEXTO['fuera']}» — la tarjeta mostraba «{(i.get('dn') or '').split(' — ')[-1]}» de TIMBÓ"))
    agregar("pantalla_anterior", "Quedaron fuera con la pantalla anterior",
            "Se respondieron cuando la tarjeta podía confundir el artículo del hospital con el de TIMBÓ. "
            "Confirmá que de verdad no los usan.", filas)

    # 4. Lo van a pedir, pero también figura en bodegas de otros servicios.
    filas = []
    for i in items:
        # También los de «Ya están en TIMBÓ» sin tocar: el servicio solo los
        # miraba y podían ser de otro (caso de los de laboratorio en Informática).
        if grupo_de[i["id"]] in ("cargar", "estan") and (respuestas.get(i["id"]) or i["s"] == 3):
            otras = set(i.get("ob") or []) - BODEGAS_GENERALES - mios
            if otras:
                filas.append((i["n"], "También figura en " + ", ".join(sorted(otras))))
    agregar("otro_servicio", "Lo usan, pero también es de otro servicio",
            "Puede ser compartido (está bien) o haber quedado en la lista por error.", filas)

    # 5. «No es de nuestro servicio» y no está en la bodega de ningún otro.
    filas = []
    for i in items:
        r = respuestas.get(i["id"])
        if r and r.resultado == "otro_servicio" and not (set(i.get("ob") or []) - BODEGAS_GENERALES - mios):
            filas.append((i["n"], "No figura en la bodega de ningún otro servicio"))
    agregar("huerfano", "«No es de nuestro servicio», pero nadie más lo tiene",
            "Si ningún servicio lo pide, desaparece. Hay que avisar a Compras a qué servicio va.", filas)

    # 6. Para pedir el alta, pero parecido a algo que ya está en TIMBÓ en el mismo servicio.
    estan = _Indice([i for i in items if grupo_de[i["id"]] == "estan"])
    filas = []
    for f in grupos["cargar"]:
        par = estan.parecido(f[3])
        if par:
            r = respuestas.get(par["id"])
            codigo = (r.codigo_correcto or r.codigo_propuesto) if r else par.get("cp", "")
            filas.append((f[3], f"Parecido a «{par['n']}», que ya está en TIMBÓ con {codigo or par.get('cp', '')}"))
    agregar("como_otro", "Para pedir el alta, pero parecido a algo que ya está en TIMBÓ",
            "Quizás sirva el mismo código (como ítem general, con el detalle en la observación).", filas)

    # 7. Corregidos por el servicio en «Ya están en TIMBÓ» (el código propuesto
    # era otra cosa, como «PC DE ESCRITORIO» → ESCRITORIO, un mueble).
    filas = []
    for i in items:
        r = respuestas.get(i["id"])
        if i["s"] == 3 and r and r.resultado in ("no_corresponde", "otro_servicio"):
            que = "No es lo mismo: pasa a pedir el alta" if r.resultado == "no_corresponde" else "No es de este servicio"
            filas.append((i["n"], f"{que} · TIMBÓ proponía {i.get('cp', '')} «{(i.get('dn') or '').split(' — ')[-1]}»"))
    agregar("corregido_estan", "Corregidos en «Ya están en TIMBÓ»",
            "El servicio dijo que el código que parecía seguro no corresponde. Confirmalo antes de pedir.", filas)
    return avisos


class _Indice:
    """Artículos indexados por palabra, para buscar «el primero que comparte al
    menos 2 palabras y el 60 % de las del buscado» sin comparar con todos."""

    def __init__(self, items):
        self.items = items
        self.claves = [_clave(i["n"]) for i in items]
        self.por_palabra = defaultdict(list)
        for n, k in enumerate(self.claves):
            for w in k:
                self.por_palabra[w].append(n)

    def parecido(self, nombre):
        k = _clave(nombre)
        cuenta = defaultdict(int)
        for w in k:
            for n in self.por_palabra.get(w, ()):
                cuenta[n] += 1
        buenos = sorted(n for n, c in cuenta.items() if c >= 2 and c >= 0.6 * len(k))
        return self.items[buenos[0]] if buenos else None


_GRUPO_TEXTO = {"cargar": "Hay que cargar", "estan": "Ya está en TIMBÓ", "fuera": "Queda fuera", "falta": "Sin revisar"}


def objeto_del_gasto(texto):
    """«2.9.6.0 Repuestos y accesor.» → inciso, principal, parcial, subparcial."""
    m = re.match(r"\s*(\d+)\.(\d+)\.(\d+)\.(\d+)", texto or "")
    return list(m.groups()) if m else ["", "", "", ""]


def _comparar_nucleo(filas_entrada, catalogo, buscador, nuevos=frozenset()):
    """El corazón de la comparación: para cada artículo a pedir, busca contra
    el catálogo (ya leído e indexado) y decide su estado. No necesita llave
    ni base: lo usan tanto `control()` (con los datos de la llave) como
    `comparar()` (con archivos subidos a mano, ver `comparar_subido`)."""
    filas = [dict(f, repetido_con=[]) for f in filas_entrada]
    for a in range(len(filas)):
        for b in range(a + 1, len(filas)):
            if _repetidos(filas[a]["nombre"], filas[b]["nombre"]):
                filas[a]["repetido_con"].append(filas[b]["nombre"])
                filas[b]["repetido_con"].append(filas[a]["nombre"])

    for f in filas:
        hallados = buscador.buscar(f["nombre"])
        cerca = [h for h in hallados or [] if h["pct"] >= 100 * UMBRAL]
        iguales = [h for h in cerca if h["misma_medida"]]
        if hallados is None:
            f["estado"] = "sin_buscar"
        elif any(h["codigo"] in nuevos for h in iguales):
            f["estado"] = "aparecio"
        elif iguales:
            f["estado"] = "puede_existir"
        elif f["repetido_con"]:
            f["estado"] = "repetido"
        elif cerca:
            f["estado"] = "otra_medida"
        else:
            f["estado"] = "limpio"
        f["parecidos"] = [{"codigo": h["codigo"], "texto": _texto_item(catalogo[h["codigo"]]), "pct": h["pct"],
                           "nuevo": h["codigo"] in nuevos, "misma_medida": h["misma_medida"]}
                          for h in (iguales or cerca)[:MAX_PARECIDOS]]
        # Sugerencia para la grilla: el ítem más parecido, si cubre al menos
        # la mitad de las palabras. El código que proponía TIMBÓ no se usa: el
        # servicio dijo que es otra cosa.
        mejor = hallados[0] if hallados and hallados[0]["pct"] >= 50 else None
        base = catalogo.get(mejor["codigo"]) if mejor else None
        f["sugerencia"] = ({"rubro": base[0], "subrubro": base[1], "elemento": f"{base[2]} {base[3]}",
                            "objeto": base[4], "desde": base[5], "pct": mejor["pct"] if mejor else None}
                           if base else None)
    filas.sort(key=lambda f: (ORDEN_ESTADOS.index(f["estado"]), f["nombre"].lower()))
    grupos_genericos = agrupar(filas, buscador, catalogo)
    return filas, grupos_genericos


def comparar(filas_entrada, catalogo, catalogo_nombre=""):
    """Igual que `control()`, pero sin llave ni base: para un Catálogo WEB y
    una lista de artículos a pedir ([{codigo, nombre, accion, propuesto,
    observacion}, ...]) ya leídos de archivos subidos a mano. No tiene forma
    de saber qué apareció en el catálogo DESPUÉS de un envío puntual (no hay
    fecha de envío) ni los avisos que dependen de toda la revisión del
    servicio (ésos solo salen de `control()`, con la base real)."""
    buscador = Buscador(catalogo)
    filas, grupos_genericos = _comparar_nucleo(filas_entrada, catalogo, buscador)
    cuenta = {k: sum(1 for f in filas if f["estado"] == k) for k in ORDEN_ESTADOS}
    return {"catalogo": catalogo_nombre, "catalogo_items": len(catalogo), "comparado_con": "", "nuevos": 0,
            "filas": filas, "cuenta": cuenta, "revisar_estan": [], "grupos": grupos_genericos, "avisos": [],
            "ya_estan": 0, "fuera": 0, "falta": 0}


def control(llave, instancia, tema=None):
    """Devuelve el resultado del control para una llave (ver el docstring)."""
    vigente = cd.ultima_copia(instancia)
    if not vigente:
        return None
    catalogo = leer_completo(vigente)
    buscador = Buscador(catalogo)
    anterior = copia_anterior_a(instancia, llave.enviado_en)
    nuevos = set(catalogo) - set(leer_completo(anterior)) if anterior and anterior != vigente else set()

    grupos = ls.planilla_final(llave, tema)
    filas_entrada = [{"codigo": f[2], "nombre": f[3], "accion": f[1], "propuesto": f[5], "observacion": f[10]}
                     for f in grupos["cargar"]]
    filas, grupos_genericos = _comparar_nucleo(filas_entrada, catalogo, buscador, nuevos)
    items, _ = ls.items_de(llave, tema)
    respuestas = {r.codigo_interno: r for r in llave.revisiones}
    avisos = inconsistencias(llave, items, respuestas, grupos, buscador)

    revisar_estan = []
    for f in grupos["estan"]:
        codigo = f[6]
        if not codigo:
            continue
        dato = catalogo.get(codigo)
        if dato is None:
            aviso = "El código ya no figura en el Catálogo WEB"
        elif "NO UTILIZAR" in f"{dato[3]} {dato[6]}".upper():
            aviso = "El código ahora figura como «NO UTILIZAR»"
        else:
            continue
        revisar_estan.append({"codigo": f[2], "nombre": f[3], "codigo_timbo": codigo, "aviso": aviso})

    cuenta = {k: sum(1 for f in filas if f["estado"] == k) for k in ORDEN_ESTADOS}
    return {"catalogo": os.path.basename(vigente), "catalogo_items": len(catalogo),
            "comparado_con": os.path.basename(anterior) if anterior and anterior != vigente else "",
            "nuevos": len(nuevos), "filas": filas, "cuenta": cuenta, "revisar_estan": revisar_estan,
            "grupos": grupos_genericos, "avisos": avisos,
            "ya_estan": len(grupos["estan"]), "fuera": len(grupos["fuera"]), "falta": len(grupos["falta"])}


# Mismo orden que el formulario «Solicitud de alta de bien o servicio» de TIMBÓ.
ENCABEZADOS = ["Control", "Rubro / especie (sugerido)", "Subrubro / familia (sugerido)", "Elemento (sugerido)",
               "Nombre o descripción / ítem específico", "Inciso", "Partida principal", "Partida parcial",
               "Partida subparcial", "Unidad de medida", "Marca", "Aporta documentación", "Código del hospital",
               "Sugerencia tomada del ítem", "Parecidos en el Catálogo WEB", "Posible repetido con",
               "Qué respondió el servicio", "Observación del servicio", "N° de trámite (SDO)", "Estado del pedido"]
ANCHOS = [34, 24, 26, 30, 44, 8, 9, 9, 10, 14, 14, 12, 14, 16, 60, 36, 34, 34, 22, 18]


def filas_desde_excel(datos):
    """Lee la hoja «PARA PEDIR EL ALTA» de un Excel ya generado por `libro()`
    (el de «Revisión final automática», sin aprobar) y arma la lista de
    artículos a pedir para `comparar()`. `datos` son los bytes del archivo."""
    import io as _io

    import openpyxl
    wb = openpyxl.load_workbook(_io.BytesIO(datos), data_only=True)
    if "PARA PEDIR EL ALTA" not in wb.sheetnames:
        raise ValueError("No es un Excel de «Revisión final automática»: falta la hoja «PARA PEDIR EL ALTA».")
    ws = wb["PARA PEDIR EL ALTA"]
    filas = []
    for fila in ws.iter_rows(min_row=2, values_only=True):
        nombre = (fila[4] or "").strip() if len(fila) > 4 else ""
        if not nombre:
            continue
        filas.append({"codigo": (fila[12] or "").strip() if len(fila) > 12 else "", "nombre": nombre,
                      "accion": "", "propuesto": "", "observacion": (fila[17] or "") if len(fila) > 17 else ""})
    return filas


def leer_catalogo_subido(datos):
    """Catálogo WEB a partir de los bytes de un CSV subido a mano (mismo
    formato que descarga `/admin/servicios/catalogo/descargar`). `leer_completo`
    espera una ruta de archivo: lo escribimos en un temporal y lo borramos
    enseguida."""
    import os as _os
    import tempfile
    texto = datos.decode("utf-8-sig")
    fd, ruta = tempfile.mkstemp(suffix=".csv")
    try:
        with _os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(texto)
        return leer_completo(ruta)
    finally:
        _os.remove(ruta)


def libro(resultado, servicio):
    filas, colores = [], []
    for f in resultado["filas"]:
        s = f["sugerencia"] or {}
        filas.append([ESTADOS[f["estado"]][0], s.get("rubro", ""), s.get("subrubro", ""), s.get("elemento", ""),
                      f["nombre"]] + objeto_del_gasto(s.get("objeto", "")) + ["", "", "", f["codigo"],
                      s.get("desde", ""),
                      " | ".join(f"{p['texto']} ({p['pct']} %{', NUEVO' if p['nuevo'] else ''}"
                                 f"{'' if p['misma_medida'] else ', otra medida'})" for p in f["parecidos"]),
                      " | ".join(f["repetido_con"]), f["accion"], f["observacion"], "", ""])
        colores.append(ESTADOS[f["estado"]][1])
    estan = [[r["codigo"], r["nombre"], r["codigo_timbo"], r["aviso"]] for r in resultado["revisar_estan"]]
    como = [["Servicio", servicio], ["Catálogo WEB usado", resultado["catalogo"]],
            ["Ítems en el catálogo", resultado["catalogo_items"]],
            ["Comparado con (antes del envío)", resultado["comparado_con"] or "—"],
            ["Ítems nuevos desde el envío", resultado["nuevos"]]]
    como += [[ESTADOS[k][0], resultado["cuenta"][k]] for k in ORDEN_ESTADOS]
    como += [["Importante", "Rubro, subrubro, elemento y objeto del gasto (inciso y partidas) son SUGERENCIAS "
                            "tomadas del ítem más parecido: confirmalos antes de pedir el alta."],
             ["Importante", "Unidad de medida, marca y documentación los completás vos. El código del hospital "
                            "va como código externo (a confirmar con la Unidad Rectora)."]]
    agrupados = [[g["nombre"], len(g["miembros"]), " | ".join(g["miembros"]), ", ".join(g["codigos"]),
                  " | ".join(f"{e['texto']}" for e in g["existentes"]) or "No: habría que pedir el alta del genérico"]
                 for g in resultado["grupos"]]
    revisar = [[a["titulo"], art, det] for a in resultado["avisos"] for art, det in a["filas"]]
    return [("PARA PEDIR EL ALTA", ENCABEZADOS, filas, ANCHOS, colores),
            ("REVISAR (POSIBLES ERRORES)", ["Qué revisar", "Artículo", "Detalle"], revisar, [44, 50, 70],
             ["amarillo"] * len(revisar)),
            ("SE PUEDEN PEDIR COMO UNO", ["Nombre genérico sugerido", "Cuántos", "Artículos que junta",
                                         "Códigos del hospital", "¿Ya existe en el Catálogo WEB?"], agrupados,
             [30, 9, 80, 24, 70], ["azul" if g["existentes"] else "verde" for g in resultado["grupos"]]),
            ("YA ESTÁN - REVISAR CÓDIGO", ["Código del hospital", "Artículo", "Código en TIMBÓ", "Aviso"], estan,
             [14, 44, 16, 44], ["amarillo"] * len(estan)),
            ("CÓMO SE HIZO", ["Dato", "Valor"], como, [40, 90], None)]


# ----------------------------------------------- planilla de carga aprobada ---
# Paso a paso del Formulario Timbó Compras (CAByS), tal como lo indica la «Guía
# de Uso: Procedimiento de Búsqueda en Nomenclador TIMBÓ y Solicitud de
# Artículos Faltantes» (rev1) y el Anexo I de la norma.
URL_NORMA = "https://www.santafe.gov.ar/normativa/item.php?id=369305&cod=72930e70e764e81edafb5c3c72169792"
PASO_A_PASO = [
    ("Antes", "", "Esta planilla ya pasó la revisión final automática y la aprobación. Solo van los artículos GENERALES "
                  "(fuera del área Farmacia). Medicamentos y descartables de Farmacia se piden a la Dirección Provincial de Farmacia (SUFYD)."),
    ("PASO 1", "1", "Ingresar a la plataforma de gestión digital TIMBÓ."),
    ("PASO 1", "2", "Seleccionar el módulo Documentos oficiales, apartado Gestión."),
    ("PASO 1", "3", "Presionar el botón Nuevo Documento Oficial."),
    ("PASO 1", "3a", "Usuario Productor (*): seleccionar la opción que corresponda."),
    ("PASO 1", "3b", "Tipo de Documento (*): elegir «Timbó Compras: Alta de bienes y servicios CAByS»."),
    ("PASO 1", "3c", "Mensaje para el Productor: {referencia}"),
    ("PASO 1", "3d", "Hacer clic en Guardar para generar el formulario inicial."),
    ("PASO 1", "3e", "Ir a la bandeja de Pendientes: buscar el número de SDO en estado «Producir Documento Oficial», "
                     "tocar los tres puntitos y elegir Documento oficial. Anotá el N° de SDO en la hoja GRILLA."),
    ("PASO 2", "4", "Fecha (*): la fecha de la solicitud (DD/MM/AAAA)."),
    ("PASO 2", "5", "Jurisdicción/Oficina (*): nombre completo del organismo que pide el alta."),
    ("PASO 2", "6", "Solicitante (*): nombre y apellido de quien confecciona la solicitud."),
    ("PASO 2", "7", "Email de contacto (*): correo institucional (ahí llega la notificación)."),
    ("PASO 2", "8", "Teléfono: interno o línea directa."),
    ("PASO 3", "9", "En Bienes y servicios, clic en «+ Nueva línea» (una vez por cada fila de la hoja GRILLA)."),
    ("PASO 3", "10", "Copiar cada columna de la fila en su campo, en este orden: Rubro/especie, Subrubro/familia, Elemento, "
                     "Nombre o descripción/ítem específico (*), Objeto del gasto (Inciso, Partida principal, parcial y subparcial), "
                     "Unidad de medida, Marca (o guiones), Aporta documentación (Sí/No)."),
    ("PASO 3", "10*", "Hospitales: el código externo va OBLIGATORIAMENTE en «Nombre o descripción». En la grilla ya está agregado "
                      "como «Cód. externo: …» (qué código usar está a confirmar con la Unidad Rectora)."),
    ("PASO 3", "11", "Presionar Agregar. Marcar la fila como «cargada» en la hoja GRILLA."),
    ("PASO 4", "12-14", "Lugares de entrega: solo si también se pide un lugar de entrega nuevo; si no, dejarlo vacío."),
    ("PASO 4", "Guardar", "Presionar Guardar: aparece «Éxito al guardar el formulario como borrador»."),
    ("PASO 4", "15", "Referencia: {referencia}"),
    ("PASO 4", "16", "Destinatario: Carolina Retamar y/o Maximiliano Sodero."),
    ("PASO 4", "17", "Adjuntar documentos (si en alguna fila se puso «Sí»): «+ Subir documento»."),
    ("PASO 4", "18", "Firma conjunta: tiene que firmarlo la persona responsable del área."),
    ("PASO 5", "19-22", "Acciones → Enviar a Firmar → comentario (ej.: «Envío para su firma») → Continuar → Confirmar."),
    ("PASO 6", "", "La persona responsable busca el formulario en su bandeja de Pendientes, elige EVALUAR y firma."),
    ("Después", "", "La Unidad Rectora Central evalúa y, si lo aprueba, asigna el código en el catálogo SIPAF y avisa por email. "
                    "Anotá el código nuevo en la hoja GRILLA."),
    ("Norma", "", URL_NORMA),
]

ESTADOS_PARA_CARGAR = ("limpio", "otra_medida", "repetido", "sin_buscar")
ENCABEZADOS_GRILLA = ["N°", "Rubro / especie", "Subrubro / familia", "Elemento", "Nombre o descripción / ítem específico (*)",
                      "Inciso", "Partida principal", "Partida parcial", "Partida subparcial", "Unidad de medida", "Marca",
                      "Aporta documentación", "Control", "N° de SDO", "¿Cargada?", "Código asignado por la Unidad Rectora"]
ANCHOS_GRILLA = [5, 10, 11, 30, 52, 8, 9, 9, 10, 14, 12, 12, 34, 18, 10, 18]


def _codigo(texto):
    """«19 - INFORMATICA» → «19»; «19.1 - EQUIPOS…» → «19.1»."""
    return (texto or "").split(" - ")[0].strip()


def clave_fila(f):
    """Identificador estable de una fila de `resultado["filas"]" para guardar
    ediciones manuales (unidad, marca, ¿cargada?, etc.): el código del
    hospital si lo tiene, si no el nombre."""
    return f["codigo"] or f["nombre"]


def libro_carga(resultado, servicio, aprobado_por, fecha, extra=None):
    """Excel listo para cargar en el Formulario Timbó Compras (CAByS).
    `extra` (opcional): {clave_fila(f): {unidad, marca, aporta, cargada, sdo,
    rubro, subrubro, elemento, inciso, principal, parcial, subparcial}} con lo
    que se haya completado o corregido a mano (ver `/admin/comparar-manual`).
    Lo que venga en `extra` manda por sobre la sugerencia automática."""
    extra = extra or {}
    referencia = f"Alta de bienes para el Hospital — servicio {servicio}"
    pasos = [[a, b, c.format(referencia=f"«{referencia}»")] for a, b, c in PASO_A_PASO]
    grilla, colores, ya_existen = [], [], []
    vistos_repetidos = set()
    for f in resultado["filas"]:
        if f["estado"] not in ESTADOS_PARA_CARGAR:
            ya_existen.append([f["nombre"], f["codigo"], ESTADOS[f["estado"]][0],
                               " | ".join(p["texto"] for p in f["parecidos"])])
            continue
        if f["estado"] == "repetido":
            clave = tuple(sorted([f["nombre"]] + f["repetido_con"]))
            if clave in vistos_repetidos:
                ya_existen.append([f["nombre"], f["codigo"], "Repetido: se pide una sola vez (ver la otra fila)", ""])
                continue
            vistos_repetidos.add(clave)
        s = f["sugerencia"] or {}
        e = extra.get(clave_fila(f), {})
        objeto_auto = objeto_del_gasto(s.get("objeto", ""))
        rubro = _codigo(e.get("rubro")) or _codigo(s.get("rubro"))
        subrubro = _codigo(e.get("subrubro")) or _codigo(s.get("subrubro"))
        elemento = e.get("elemento") or s.get("elemento", "")
        objeto = [e.get("inciso") or objeto_auto[0], e.get("principal") or objeto_auto[1],
                 e.get("parcial") or objeto_auto[2], e.get("subparcial") or objeto_auto[3]]
        completo = bool(rubro and subrubro and elemento)
        nombre = f["nombre"] + (f" — Cód. externo: {f['codigo']}" if f["codigo"] else "")
        grilla.append([len(grilla) + 1, rubro, subrubro, elemento, nombre] + objeto +
                      [e.get("unidad", ""), e.get("marca", ""), e.get("aporta", "No"),
                       ESTADOS[f["estado"]][0] + ("" if completo else " — sin rubro/subrubro/elemento: completar"),
                       e.get("sdo", ""), "Sí" if e.get("cargada") else "", ""])
        colores.append("verde" if completo else "amarillo")
    portada = [["Servicio", servicio], ["Aprobado por", aprobado_por], ["Fecha de aprobación", fecha],
               ["Catálogo WEB usado", resultado["catalogo"]], ["Filas para cargar", len(grilla)],
               ["No se cargan (ya existen o repetidos)", len(ya_existen)],
               ["Importante", "Rubro, subrubro, elemento y objeto del gasto son sugerencias del ítem más parecido del "
                              "Catálogo WEB: confirmalos al cargar. Unidad de medida y marca, completalas vos."]]
    return [("PASO A PASO", ["Paso", "N°", "Qué hacer"], pasos, [10, 8, 120], None),
            ("GRILLA PARA CARGAR", ENCABEZADOS_GRILLA, grilla, ANCHOS_GRILLA, colores),
            ("NO SE CARGAN", ["Artículo", "Código del hospital", "Por qué", "Qué hay en el Catálogo WEB"], ya_existen,
             [46, 14, 50, 90], ["azul"] * len(ya_existen)),
            ("APROBACIÓN", ["Dato", "Valor"], portada, [36, 90], None)]
