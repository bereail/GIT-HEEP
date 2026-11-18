"""Matriz consolidada v5 (decisiones de la usuaria del 18/11/2026). Local.
    python fuente/matriz_v5.py
"""
from html import escape as h
from pathlib import Path

import matriz_v4 as v4

AQUI = Path(__file__).resolve().parent.parent
FECHA = "18/11/2026"
SCYGB, UG, HOSP, LEER = "SCyGB (Unidad Rectora Central)", "Unidad de Gestión TIMBÓ", "Compras del hospital (relevamiento)", "Lectura pendiente (equipo)"

# id, tema, fuentes (punto · página), tipo, impacto, estado, a quién consultar, pregunta, decisión de la usuaria
MATRIZ = [
    ("D1", "Recorrido de la rama B (urgencia o desierto) en TIMBÓ Compras",
     "Algoritmo público (salta a «ofertas») · Circ. UG 8/2026 arts. 3 y 4 (págs. 1-2) · circuito oficial (entra por el pliego) · Dec. 652/2020 arts. 1 y 3 · Dec. 1104 art. 116 c ap. 2 y 3 (pág. 18)",
     "Diferencia entre representaciones + falta documentación", "Dónde se une B al tronco; si urgencia y desierto recorren lo mismo", "PENDIENTE",
     UG, "En las contrataciones directas por urgencia y por desierto en TIMBÓ Compras, ¿se completan los formularios del pliego particular? ¿Qué etapas del módulo se omiten o se acortan además de lo que dice el art. 4 de la Circ. 8/2026? ¿Es el mismo recorrido para los dos supuestos?",
     "Dejar pendiente hasta verificar"),
    ("D2", "Quién selecciona la etapa múltiple", "Dec. 1104 art. 123, texto del Dec. 287/2026 (pág. 3) · algoritmo público (la elige el organismo)",
     "Texto superado en el proyecto", "Opción de la decisión ◆2", "VERIFICADO", "—", "—",
     "Representar que la selecciona la Unidad Rectora"),
    ("D3", "Pasos de la directa por monto", "Dec. 1247/08 Anexo I (págs. 5 a 8) · Dec. 2175/2022 art. 1 · video oficial QH7zvgZ7sbQ · Circ. UG 2/2025 pto 2 (pág. 8)",
     "Diferencia entre representaciones", "Rama A", "VERIFICADO (secuencia y formularios CD-01 a CD-05) · DOCUMENTADO (detalle operativo digital, video)", "—", "—",
     "Conservar CD-01 a CD-04 como recorrido documentado; verificar contra la normativa antes de validar"),
    ("D4", "Uno o dos diarios en la licitación pública", "Dec. 1104 art. 132.3 (pág. 26, 2016, no modificado) · Circ. SCyGB 04/2026 Anexo II (pág. 4, 19/05/2026) · Dec. 287/2026 art. 2 (solo modifica el 132.1)",
     "Contradicción normativa (decreto vs. nota modelo de circular)", "Publicación del público", "OBSERVADO",
     SCYGB, "La nota modelo de la Circular 04/2026 pide la publicación «por un (1) día en un (1) diario»; el art. 132.3 del Dec. 1104/16 dice «un (1) día en dos diarios». ¿Cuál corresponde aplicar?",
     "Dejar pendiente hasta verificar alcance y vigencia de la Circ. 04/2026"),
    ("D5", "Controles de la URC en el hospital", "Res. ME 73/2026 art. 2 (pág. 3) · Circ. SCyGB 03/2026 (pág. 1): dirigidas a la Administración Pública Central",
     "Alcance no confirmado", "Dos controles del tronco", "PENDIENTE", SCYGB,
     "¿Los controles obligatorios de la URC sobre pliegos y preadjudicación (Res. ME 73/2026, art. 2) alcanzan a los hospitales del Ministerio de Salud?", "—"),
    ("D6", "Las 5 invitaciones del privado", "Dec. 1104 art. 121.1 (pág. 20) · Circ. UG 7/2026 pto 15 (pág. 4)",
     "Alcance no confirmado", "Publicación del privado", "PENDIENTE", f"{UG} / {SCYGB}",
     "¿Las invitaciones que TIMBÓ Compras envía a la nómina cumplen el requisito de «medio fehaciente» del art. 121.1, o hay que acreditarlas aparte en el expediente?", "—"),
    ("D7", "Competencia para aprobar el pliego",
     "Dec. 2233/16 art. 2 (pág. 2): Subsecretario de Coordinación Técnica y Gestión Administrativa o equivalente (o delegado), sin tramos · Circ. SCyGB 01/2026 (pág. 1): «Aprobación de actos licitatorios» por montos · Dec. 2233/16 art. 3: tramos para adjudicación",
     "Contradicción o diferencia de interpretación entre normas", "Actor del acto de la etapa 4", "OBSERVADO", SCYGB,
     "Ver la consulta formal (abajo)", "Conservar las dos referencias; no trasladar los tramos de adjudicación a la aprobación del pliego"),
    ("D8", "Quién adjudica la directa por monto", "Dec. 1247/08 Anexo I (pág. 7, 2008): Disposición del Director del SAF · Dec. 2233/16 art. 3.a (2016) y Circ. SCyGB 01/2026: Subsecretario o equivalente (o delegado)",
     "Fuentes de distinta fecha", "Actor de la rama A", "OBSERVADO", SCYGB,
     "En la directa por monto, ¿el acto de adjudicación lo dicta el Subsecretario de Coordinación Técnica o su equivalente (Dec. 2233/16, art. 3.a), o sigue vigente la disposición del Director del Servicio Administrativo-Financiero que describe el Manual del Dec. 1247/08?",
     "Usar lo más reciente para el análisis; mantener OBSERVADO; el manual es antecedente histórico"),
    ("D9", "Comunicación al Tribunal de Cuentas en la directa", "Dec. 1247/08 Anexo I (pág. 7): copia a la Delegación Fiscal (Res. TCP 007/06, no leída) · Circ. UG 9/2026 art. 3 y UG 11/2026 arts. 1-2 (pág. 2)",
     "Fuentes de distinta fecha", "Rama A", "OBSERVADO", f"{UG} / {SCYGB}",
     "¿La comunicación al TCP de los actos de la directa por monto se hace solo por SIN y «Gestión de Visualización» (Circ. 9 y 11/2026) o se mantiene la copia a la Delegación Fiscal?", "Igual que D8"),
    ("D10", "Soporte de la directa", "Dec. 1247/08 Anexo I (pág. 7): presupuestos por teléfono, fax o correo · Circ. UG 2/2025 pto 2 (pág. 8) y Dec. 2518/25: exclusivamente digital",
     "Fuentes de distinta fecha", "Soporte de la rama A", "OBSERVADO", f"{UG} / {SCYGB}",
     "¿Cómo se incorporan los presupuestos en la gestión directa digital (documento informativo, CD-03, otro)? ¿Sigue el umbral de las habilitaciones para pedir presupuestos sin CD-02?", "Igual que D8"),
    ("D11", "Publicación de la adjudicación en el privado", "Ley 12.510 art. 132 (pág. 43) · Dec. 1104 art. 132.4 (pág. 26): hablan de licitación y concurso público",
     "Alcance no confirmado", "Etapa de adjudicación", "PENDIENTE", SCYGB, "¿La adjudicación de una licitación o concurso privado se publica en el sitio web de contrataciones?", "—"),
    ("D12", "Qué sigue después de un rechazo del Supervisor", "Circ. UG 7/2026 pto 10 (pág. 3)", "Falta documentación", "Salida «Rechazado»",
     "PENDIENTE", UG, "Cuando el Supervisor rechaza un formulario del PBCP, ¿vuelve al Gestor para corregirlo? ¿Queda registro en el expediente?", "—"),
    ("D13", "Orden entre pasos del pliego", "Circ. UG 7/2026 pto 10 (pág. 3); Circ. SCyGB 03/2026 (pág. 1)", "Falta documentación", "Orden en la etapa 4",
     "PENDIENTE", UG, "¿En qué momento revisa la Jurisdicción comitente respecto de la aprobación del Supervisor? ¿El cronograma y la nómina se cargan antes o después del control de la URC?", "—"),
    ("D14", "El algoritmo público y el circuito oficial no coinciden", "algoritmo.json (público) · circuito oficial en /admin/procesos", "Diferencia entre representaciones",
     "Riesgo de enseñar cosas distintas", "PENDIENTE", "—", "—",
     "No modificar algoritmo.json hasta aprobar el circuito; después sincronizar y probar todos sus consumidores"),
    ("D15", "Representación del 20 %", "Dec. 1104 art. 116.1 (pág. 17)", "Error de representación (corregido)", "Decisión ◆3 y adjudicación",
     "VERIFICADO", "—", "—", "Separar cálculo y validez"),
    ("D16", "Intervención de la SCyGB en urgencia y desierto", "Dec. 652/2020 arts. 1 y 3 (págs. 2-3)", "Diferencia entre representaciones (falta en el circuito oficial)",
     "Rama B", "VERIFICADO (la norma) · el recorrido de B sigue PENDIENTE (D1)", "—", "—", "—"),
    ("D17", "Intervención de la SCyGB en ap. 4, 5 y 8", "Disp. 282/16 (PDF escaneado, en la biblioteca)", "Falta lectura", "Rama A2", "PENDIENTE", LEER,
     "Leer la Disp. 282/16 (requiere reconocimiento de texto)", "—"),
    ("D18", "Convenio Marco y régimen de locaciones", "Res. 211/2018 y 101/2019 · Dec. 1178/2025 · Circ. 007 de locaciones", "Falta lectura", "Rama E", "PENDIENTE", LEER,
     "Leer las cuatro normas", "—"),
    ("D19", "Quién declara desierta la licitación", "Ley 116 c.3 (pág. 40) · Dec. 1104 art. 116 c ap. 3 (pág. 18)", "Falta documentación", "Desierto → B",
     "PENDIENTE", SCYGB, "¿Qué autoridad declara desierta o fracasada una licitación o concurso y por qué acto?", "—"),
    ("D20", "«Sin efecto» del Supervisor y revocación del llamado", "Circ. UG 7/2026 pto 10 (pág. 3) · Pliego Único 5.5 (pág. 38)", "Alcance no confirmado", "Excepción de revocación",
     "PENDIENTE", UG, "¿El acto «sin efecto» que carga el Supervisor en TIMBÓ Compras es el de la revocación del llamado del Pliego Único 5.5?", "—"),
]

CONSULTA_D7 = """Nota de consulta — Subsecretaría de Contrataciones y Gestión de Bienes (Unidad Rectora Central)

Ref.: competencia para aprobar el pliego de bases y condiciones particulares en procedimientos tramitados por TIMBÓ Compras.

Al revisar la normativa vigente para representar el circuito de compras de un hospital del Ministerio de Salud, encontramos dos referencias que podrían interpretarse de manera distinta:

1. Decreto N° 2233/16, artículo 2°: los actos de aprobación de los pliegos de bases y condiciones particulares de las contrataciones efectuadas según los arts. 116 y 140 de la Ley N° 12.510 «serán suscriptos por» el Subsecretario de Coordinación Técnica y Gestión Administrativa o su equivalente funcional (o a quien se le haya delegado la facultad), o por el Director Provincial de Contrataciones y Gestión de Bienes en los procedimientos de la Unidad Rectora Central. El artículo no establece tramos por monto.

2. Circular SCyGB N° 01/2026 (5/1/2026), apartado «Aprobación de actos licitatorios»: hasta $5.850.000, resolución del Subsecretario de Administración o su equivalente; entre $5.850.000 y $29.250.000, resolución; entre $29.250.000 y $58.500.000, resolución conjunta con el Ministerio de Economía; más de $58.500.000, decreto. Estos tramos coinciden con los del art. 3° del Decreto N° 2233/16, referido a los actos de adjudicación y/o aprobación de las contrataciones.

Consultamos:
a) ¿El acto que aprueba el pliego y autoriza el llamado (Circular UG TIMBÓ N° 7/2026, punto 10) debe suscribirlo siempre el funcionario del art. 2° del Decreto N° 2233/16, cualquiera sea el monto?
b) ¿Los tramos de la Circular N° 01/2026 se aplican a ese acto, a la adjudicación, o a ambos?
c) En un hospital, ¿qué funcionario es el «equivalente funcional» del Subsecretario de Coordinación Técnica y Gestión Administrativa?

Mientras tanto, el circuito muestra las dos referencias y deja la competencia como OBSERVADA."""

SINCRONIZAR = [
    ("Sitio público: «¿Qué camino sigue una compra?»", "/recursos/algoritmo · algoritmo_publico()"),
    ("Buscador global (índice de Recursos)", "app/recursos/__init__.py (indexación de pasos)"),
    ("«Explicame este paso»", "capacitacion.json → nodos del algoritmo"),
    ("Flujos paso a paso y gráfico SVG (admin)", "/admin/recursos/flujos · /admin/recursos/grafico"),
    ("Capacitación: algoritmo y modo capacitadora", "/admin/capacitacion/algoritmo · /modo-capacitadora"),
    ("Inventario", "app/services/inventario.py"),
    ("Pruebas", "tests/test_recursos.py (fuentes, caminos, sitio público)"),
]


def tabla(cab, filas):
    return v4.tabla(cab, filas)


def html():
    cuenta = {}
    for f in MATRIZ:
        clave = f[5].split(" ")[0]
        cuenta[clave] = cuenta.get(clave, 0) + 1
    resumen = " · ".join(f"{k}: {v}" for k, v in cuenta.items())
    consultas = {}
    for f in MATRIZ:
        if f[6] not in ("—",):
            consultas.setdefault(f[6], []).append(f"{f[0]}: {f[7]}")
    bloques = "".join(f"<h3>{h(k)}</h3><ul>{''.join(f'<li>{h(q)}</li>' for q in v)}</ul>" for k, v in consultas.items())
    esquema = v4.ESQUEMA.replace("[Observado D7: ¿Subsecretario (Dec. 2233 art. 2) o según monto?]",
                                 "[OBSERVADO D7: Dec. 2233 art. 2 (Subsecretario o equivalente) y Circ. SCyGB 01/2026; no se aplican los tramos de adjudicación]")
    esquema = esquema.replace("[Verificado · Dec. 1247/08 · Observado D8-D10]",
                              "[VERIFICADO secuencia · OBSERVADO D8-D10 · Dec. 1247/08 = antecedente histórico]")
    est = "".join(f"<span class='chip' style='border-color:{c};color:{c}'>{h(n.upper())}</span> {h(d)}<br>" for n, c, d in v4.ESTADOS)
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Circuito de compras · matriz consolidada v5</title>
<style>
body{{margin:0;background:#f6f7f9;color:#1f2937;font:15px/1.5 "Segoe UI",system-ui,Arial,sans-serif}}
main{{max-width:1320px;margin:0 auto;padding:24px 16px 60px}}
section{{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:20px 22px;margin-top:18px}}
h1{{margin:0 0 4px;font-size:26px}} h2{{margin:0 0 8px;font-size:20px}} h3{{margin:14px 0 4px;font-size:16px}}
table{{border-collapse:collapse;width:100%;font-size:12.8px}} th,td{{border-bottom:1px solid #e2e8f0;padding:6px 8px;text-align:left;vertical-align:top}}
th{{background:#f8fafc}} .tabla{{overflow-x:auto}} pre{{background:#0f172a;color:#e2e8f0;padding:16px;border-radius:12px;overflow-x:auto;font-size:12.5px;line-height:1.45;white-space:pre}}
.nota{{white-space:pre-wrap;background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:14px;font-size:14px}}
.chip{{display:inline-block;border:1.5px solid;border-radius:999px;padding:0 10px;font-weight:700;font-size:12.5px;margin:2px 4px 2px 0}}
</style></head><body><main>
<h1>Circuito de compras · matriz consolidada v5</h1>
<p>Decisiones de la usuaria del {FECHA}. Las 20 discrepancias son D1 a D20 (D7 a D10 son parte de las 20). Estados: {h(resumen)}.</p>
<section><h2>Estados</h2><p>{est}</p></section>
<section><h2>1. Matriz consolidada (D1 a D20)</h2>
{tabla(["Id", "Tema", "Fuentes (punto · página)", "Tipo", "Impacto en el mapa", "Estado", "Consultar a", "Pregunta", "Decisión de la usuaria"], MATRIZ)}</section>
<section><h2>2. Consulta formal a la SCyGB (D7)</h2><div class="nota">{h(CONSULTA_D7)}</div></section>
<section><h2>3. Consultas agrupadas por destinatario</h2>{bloques}</section>
<section><h2>4. Esquema v5</h2><pre>{h(esquema)}</pre></section>
<section><h2>5. Fuentes por recorrido</h2>
{tabla(["Recorrido", "Qué cubre", "Fuentes (punto · página)", "Estado", "Observaciones"], v4.RECORRIDOS)}</section>
<section><h2>6. Ramas y hallazgos conservados</h2>{tabla(["Elemento", "Estado"], v4.CONSERVADOS)}</section>
<section><h2>7. Biblioteca (aplicado en local)</h2>
{tabla(["Id", "Documento", "Alcance y estado", "Fuente oficial"], [
    ("dec-1247-2008", "Decreto 1247/2008 y Anexo I (Manual de contrataciones directas)", "En vigor según el Dec. 2175/2022; antecedente histórico para el circuito digital (D8 a D10)", "Ficha del SIN (decreto y anexo)"),
    ("dec-2175-2022", "Decreto 2175/2022, art. 1", "Vigente; confirma el uso del procedimiento del Dec. 1247/08 en la directa por monto", "Boletín Oficial del 27/10/2022")])}</section>
<section><h2>8. Sincronización de algoritmo.json (cuando se apruebe el circuito)</h2>
<p>No se modifica todavía. Consumidores a probar después de sincronizar:</p>
{tabla(["Funcionalidad", "Dónde"], SINCRONIZAR)}</section>
</main></body></html>"""


if __name__ == "__main__":
    (AQUI / "matriz_v5.html").write_text(html(), encoding="utf-8")
    print("ok", len(MATRIZ))
