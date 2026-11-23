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
            self.datos[codigo] = (p, medida(texto), fila[2], palabras(fila[3]) | set(_pares(fila[3])))
            for w in p:
                self.indice[w].add(codigo)
        self.vocabulario = [w for w in self.indice if len(w) >= 6]
        self._parecidas = {}

    def parecidas(self, w):
        """Palabras del catálogo escritas casi igual (errores de tipeo:
        SABOREAUD / SABOUROD, MARGENTA / MAGENTA). Solo palabras largas."""
        if len(w) < 6:
            return set()
        if w not in self._parecidas:
            import difflib
            self._parecidas[w] = {v for v in difflib.get_close_matches(w, self.vocabulario, n=5, cutoff=0.8)
                                  if v != w and v[:3] == w[:3]}   # tienen que empezar igual
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
            q, mq, _, en_elemento = self.datos[c]
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
            lista.append((len(cubiertas) / len(p), m <= mq or not mq, len(q - p), c, del_elemento))
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


def objeto_del_gasto(texto):
    """«2.9.6.0 Repuestos y accesor.» → inciso, principal, parcial, subparcial."""
    m = re.match(r"\s*(\d+)\.(\d+)\.(\d+)\.(\d+)", texto or "")
    return list(m.groups()) if m else ["", "", "", ""]


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
    filas = [{"codigo": f[2], "nombre": f[3], "accion": f[1], "propuesto": f[5], "observacion": f[10],
              "repetido_con": []} for f in grupos["cargar"]]
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
            "grupos": grupos_genericos,
            "ya_estan": len(grupos["estan"]), "fuera": len(grupos["fuera"]), "falta": len(grupos["falta"])}


# Mismo orden que el formulario «Solicitud de alta de bien o servicio» de TIMBÓ.
ENCABEZADOS = ["Control", "Rubro / especie (sugerido)", "Subrubro / familia (sugerido)", "Elemento (sugerido)",
               "Nombre o descripción / ítem específico", "Inciso", "Partida principal", "Partida parcial",
               "Partida subparcial", "Unidad de medida", "Marca", "Aporta documentación", "Código del hospital",
               "Sugerencia tomada del ítem", "Parecidos en el Catálogo WEB", "Posible repetido con",
               "Qué respondió el servicio", "Observación del servicio", "N° de trámite (SDO)", "Estado del pedido"]
ANCHOS = [34, 24, 26, 30, 44, 8, 9, 9, 10, 14, 14, 12, 14, 16, 60, 36, 34, 34, 22, 18]


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
    return [("PARA PEDIR EL ALTA", ENCABEZADOS, filas, ANCHOS, colores),
            ("SE PUEDEN PEDIR COMO UNO", ["Nombre genérico sugerido", "Cuántos", "Artículos que junta",
                                         "Códigos del hospital", "¿Ya existe en el Catálogo WEB?"], agrupados,
             [30, 9, 80, 24, 70], ["azul" if g["existentes"] else "verde" for g in resultado["grupos"]]),
            ("YA ESTÁN - REVISAR CÓDIGO", ["Código del hospital", "Artículo", "Código en TIMBÓ", "Aviso"], estan,
             [14, 44, 16, 44], ["amarillo"] * len(estan)),
            ("CÓMO SE HIZO", ["Dato", "Valor"], como, [40, 90], None)]
