"""Revisión final v3.1 (maqueta + tablas). No toca el Centro.

    python fuente/v31.py
"""
from html import escape as h
from pathlib import Path

import v3
from v3 import (AQUI, AZUL, AZUL_F, BEIGE, BEIGE_F, ESTADO, ETAPA_DE, ETAPAS, GRIS, GRIS_F, LINEA, N, NAVY, OF, OK, OK_F,
                PEND, PEND_F, ROJO, TEAL, TEAL_F, TXT, SUB, VIOLETA, VIOLETA_F, caja_detalle, chip, chip_estado, cuenta,
                marco, panel_general, seccion, svg, t)

FECHA = "18/11/2026"

# ------------------------------------------------------------- fuentes
# id: (documento, emisor, fecha/vigencia, url-doc de la biblioteca, lectura)
FUENTES = [
    ("Ley 12.510 (arts. 116, 117, 118, 132, 133, 134)", "Legislatura de Santa Fe", "Vigente, con modificatorias", "ley-12510", "Leída hoy: arts. 116 a 118 (pág. 40-41), 132 a 134 (pág. 43)"),
    ("Decreto 1104/16 (arts. 116, 121, 132, 133)", "Poder Ejecutivo", "2016; arts. 121, 132.3, 132.4 y 133 no modificados por el Dec. 287/2026", "dec-1104-2016", "Leído hoy: arts. 116 (pág. 17-18), 121 (pág. 20), 132 (pág. 26), 133 (pág. 27)"),
    ("Decreto 287/2026 (art. 2) y Pliego Único", "Poder Ejecutivo", "23/02/2026", "dec-287-2026", "Leído hoy: art. 2 (modifica arts. 123, 130, 131.3, 132.1, 139, 142); Pliego 4.3, 5.1 a 5.6, 6.9 a 6.13, 10.1.3"),
    ("Circular SCyGB 01/2026 (Ley de Presupuesto 14.424, art. 36)", "Subsecretaría de Contrataciones y Gestión de Bienes", "05/01/2026 · ejercicio 2026", "circ-scygb-1-2026", "Leída completa"),
    ("Circular SCyGB 03/2026", "SCyGB", "15/04/2026 · dirigida a la Administración Pública Central", "circ-scygb-3-2026", "Leída completa"),
    ("Circular SCyGB 04/2026", "SCyGB", "19/05/2026 · dirigida a la Administración Pública Central", "circ-scygb-4-2026", "Leída completa"),
    ("Res. ME 73/2026", "Ministerio de Economía", "07/04/2026 · Administración Pública Central", "res-me-73-2026", "Leída completa"),
    ("Decreto 287/2026, art. 123 (etapa múltiple)", "Poder Ejecutivo", "23/02/2026 · reemplaza el texto 2016 del art. 123", "dec-287-2026", "Leído hoy (pág. 3)"),
    ("Circular UG TIMBÓ 2/2025", "Unidad de Gestión TIMBÓ", "07/07/2025", "circ-ug-2-2025", "Leída (pto 2)"),
    ("Circulares UG TIMBÓ 1, 3, 7 y 8/2026", "Unidad de Gestión TIMBÓ", "1/2026 · 3/2026 (Salud desde 01/04/2026) · 7/2026 (05/05/2026) · 8/2026 (08/07/2026)", "circ-ug-7-2026", "Leídas completas"),
    ("Circulares UG TIMBÓ 9, 10 y 11/2026", "Unidad de Gestión TIMBÓ", "9/2026 · 10/2026 (prórroga al 18/08/2026) · 11/2026 (18/08/2026)", "circ-ug-9-2026", "Leídas completas"),
    ("Decreto 1247/08 (tope de la directa por monto)", "Poder Ejecutivo", "—", "", "NO LEÍDO: no está en la biblioteca"),
]

# --------------------------------------------- bloques nuevos (12) y cambios
NUEVOS = [
    # id, etapa, tipo, título, estado, hallazgo, aplica a, momento, actor, documento/actuación, obligatorio, fuente
    ("n01", "4", "actividad", "SIN y vista al Tribunal de Cuentas del acto que aprueba el pliego", "documentado", "F1",
     "Todos los actos administrativos, con y sin efecto hacendal", "Después de firmado el acto",
     "Direcciones Generales de Despacho (carga en el SIN) · áreas con funciones de Despacho (visualización)",
     "Acto cargado en el SIN y enviado por correo · expediente compartido con «Gestión de Visualización»",
     "Obligatorio («deberán»). El expediente sigue su curso (UG 9, art. 5)",
     "Circ. UG 11/2026, arts. 1 y 2 (pág. 2) · Circ. UG 9/2026, arts. 3 a 5 (pág. 2)"),
    ("n02", "6", "excepcion", "Vista e impugnación de las ofertas", "documentado", "F2",
     "Licitaciones y concursos regidos por el Pliego Único", "2 días hábiles después de la apertura (Pliego) · período fijado en el cronograma (TIMBÓ Compras)",
     "Oferentes impugnan · Evaluador recibe (UG 7, pto 10) · autoridad competente resuelve junto con la adjudicación",
     "Formulario de impugnación en TIMBÓ Compras + garantía: 3 % de la oferta del impugnante o lo que fije el PBCP",
     "Condicional: solo si algún oferente impugna",
     "Pliego Único 4.3 (pág. 31) y 10.1.3 (pág. 62) · Circ. UG 7/2026, ptos 10, 20 y 20.1 (págs. 3 a 5)"),
    ("n03", "5", "actividad", "Difusión de licitación o concurso privado: al menos 5 invitaciones e Internet", "documentado", "F3",
     "Licitación o concurso privado", "Invitaciones con al menos 5 días corridos antes de la presentación de ofertas",
     "Jurisdicción o Entidad contratante (quién en el hospital: a relevar)",
     "Constancia de las invitaciones en el expediente (o justificación de la imposibilidad) · difusión en Internet",
     "Obligatorio para privado. Si las invitaciones automáticas de TIMBÓ Compras (UG 7, pto 15) cuentan como «medio fehaciente»: a confirmar",
     "Dec. 1104/16, art. 121.1 (pág. 20) · Circ. UG 7/2026, pto 15 (pág. 4)"),
    ("n04", "5", "pendiente", "¿Uno o dos diarios? (discrepancia)", "pendiente_confirmacion", "F4",
     "Licitación o concurso público", "Publicación del llamado",
     "Jurisdicción o Entidad · Secretaría de Comunicación (aviso oficial, Circ. SCyGB 04/2026)",
     "Aviso en Boletín Oficial (2 días) y en diarios",
     "Pendiente: Dec. 1104/16 art. 132.3 dice «dos diarios»; la nota modelo de la Circ. SCyGB 04/2026 (más reciente, de rango inferior) dice «un (1) diario»",
     "Dec. 1104/16, art. 132.3 (pág. 26) · Dec. 287/2026, art. 2 (solo modifica el 132.1) · Circ. SCyGB 04/2026, Anexo II (pág. 4)"),
    ("n05", "8", "actividad", "Publicar el acto de adjudicación en Internet", "documentado", "F5",
     "Licitación y concurso público (para privado: a confirmar)", "Después del acto de adjudicación",
     "Jurisdicción o Entidad (quién en el hospital: a relevar)",
     "Anuncio en el sitio web de contrataciones · constancia en el expediente",
     "Obligatorio en públicos",
     "Ley 12.510, art. 132 (pág. 43) · Dec. 1104/16, art. 132.4 (pág. 26)"),
    ("n06", "9", "actividad", "Perfeccionamiento del contrato: notificación, orden de compra y garantía", "documentado", "F6",
     "Licitaciones y concursos regidos por el Pliego Único", "Notificación dentro de 10 días hábiles del acto · orden de compra o contrato dentro del plazo del PBCP o 10 días corridos · garantía de fiel cumplimiento dentro de 5 días",
     "Jurisdicción notifica · adjudicatario suscribe o recibe la orden de compra e integra la garantía",
     "Notificación fehaciente · instrumento contractual u orden de compra · garantía de fiel cumplimiento",
     "Obligatorio. En qué sistema se emite la orden de compra: a relevar",
     "Pliego Único 5.4 y 5.6 (pág. 38)"),
    ("n07", "9", "excepcion", "No formaliza o no integra la garantía: se deja sin efecto la adjudicación", "documentado", "F6",
     "Licitaciones y concursos (Pliego Único)", "Si vencen los plazos de 5.6",
     "Jurisdicción o Entidad contratante",
     "Ejecución de la garantía de mantenimiento de oferta · puede adjudicar al siguiente en el orden de mérito, previa verificación",
     "Condicional", "Pliego Único 5.6 (pág. 38)"),
    ("n08", "7", "excepcion", "Empate: mejora de precios y, si persiste, sorteo", "documentado", "F7",
     "Todos los procedimientos de selección (mejora) · licitaciones y concursos (empate)", "Durante la evaluación",
     "Evaluadores generan el subtrámite de mejora (UG 7, pto 10) · sorteo con acta, notificado a los oferentes",
     "Subtrámite de mejora en TIMBÓ Compras · acta de sorteo (dónde se labra: a relevar)",
     "Condicional: solo si hay ofertas admisibles al mismo precio. Mejora: a quienes estén hasta 5 % por encima del menor precio",
     "Pliego Único 5.3 (pág. 37) · Ley 12.510, art. 133 (pág. 43) · Dec. 1104/16, art. 133.1 (pág. 27)"),
    ("n09", "8", "excepcion", "Revocación del llamado", "documentado", "F7",
     "Licitaciones y concursos (Pliego Único)", "En cualquier momento antes del perfeccionamiento del contrato",
     "Autoridad competente, con decisión fundada",
     "Acto de revocación · devolución de la garantía de mantenimiento de oferta",
     "Condicional. Si es el acto «sin efecto» que carga el Supervisor (UG 7, pto 10): a confirmar",
     "Pliego Único 5.5 (pág. 38) · Circ. UG 7/2026, pto 10 (pág. 3)"),
    ("n10", "6", "excepcion", "Vicio en el procedimiento: se puede dejar sin efecto", "documentado", "F7",
     "Licitaciones y concursos (Pliego Único)", "En la instancia de vista e impugnación de ofertas",
     "Jurisdicción o Entidad licitante", "Acto que deja sin efecto (sin derecho a indemnización)",
     "Condicional", "Pliego Único 4.3 (pág. 31)"),
    ("n11", "7", "excepcion", "Desierto o fracasado: puede seguir por contratación directa (rama B)", "documentado", "F7",
     "Licitación o concurso", "Cuando no hubo ofertas o todas fueron declaradas inadmisibles",
     "Quién lo declara: no establecido en estas fuentes (a confirmar)",
     "Contratación directa por desierto en TIMBÓ Compras, con las mismas condiciones del llamado",
     "Condicional (la ley dice «puede contratarse»)",
     "Ley 12.510, art. 116 c ap. 3 (pág. 40) · Dec. 1104/16, art. 116 c ap. 3 (pág. 18) · Circ. UG 8/2026, arts. 3 y 4 (págs. 1-2)"),
    ("n12", "7", "observacion", "Una sola oferta no impide adjudicar si se ajusta al pliego", "documentado", "F7",
     "Licitaciones y concursos (Pliego Único)", "Evaluación y adjudicación", "—", "—", "Regla (no es un camino aparte)",
     "Pliego Único 5.2 (pág. 37)"),
]
CAMBIOS = [
    ("f45", "Flecha Adjudicación → Tribunal de Cuentas", "«Si corresponde control de legalidad» (alternativa)",
     "«Todos los actos (Circ. UG 11/2026)» (normal)", "F1"),
    ("f18 · f39", "Flechas hacia los controles de la URC", "Camino normal (obligatorio)",
     "«Si aplica al hospital (a confirmar)» (alternativa)", "F8"),
    ("f28 · o18", "Publicación en portal y aviso oficial", "Aplica a todos; «al menos 10 días corridos»",
     "Solo licitación o concurso público · 10 días corridos (20 si es internacional)", "F3"),
    ("o31", "Vista al Tribunal de Cuentas", "Condición: «EE con efecto hacendal sujetos a control preventivo»",
     "Todos los actos, con y sin efecto hacendal; carga en el SIN por Despacho", "F1"),
    ("o16", "Acto que aprueba el pliego", "Ubicación: expediente", "Ubicación: «¿Dónde se firma? a relevar» (lo carga el Supervisor en TIMBÓ Compras)", "F10"),
]
NUEVAS_FLECHAS = [
    ("o16", "n01", "Todos los actos (UG 11)", "normal"), ("n01", "o17", "El expediente sigue su curso (UG 9, art. 5)", "normal"),
    ("o16", "n03", "Si es privado", "alternativa"), ("n03", "o20", "≥ 5 días corridos antes de la presentación", "normal"),
    ("o21", "n02", "Si algún oferente impugna", "alternativa"), ("n02", "o30", "Se resuelven con la adjudicación (4.3)", "normal"),
    ("n02", "n10", "Si se detecta un vicio", "alternativa"),
    ("o22", "n08", "Si hay empate", "alternativa"), ("n08", "o24", "Mejora de precios", "normal"),
    ("o22", "n11", "Sin ofertas o todas inadmisibles", "alternativa"), ("n11", "o06", "Directa por desierto (mismas condiciones)", "normal"),
    ("o30", "n05", "Si es público", "normal"),
    ("o32", "n06", "", "normal"), ("n06", "o33", "", "normal"),
    ("n06", "n07", "Si no formaliza o no integra la garantía", "rechazo"), ("n07", "o30", "Puede adjudicar al siguiente en el orden de mérito", "retorno"),
]
# Nota: n04 (pendiente) y n09 (revocación, «en cualquier momento») no se conectan: no hay fuente que fije a qué paso.

HALLAZGOS_PEND = [
    ("¿La Res. ME 73/2026 y las Circ. SCyGB 03 y 04/2026 alcanzan a los hospitales?", "Dirigidas a la Administración Pública Central", "Santa Fe (SCyGB / mesa de ayuda)"),
    ("¿Uno o dos diarios para la licitación pública?", "Dec. 1104/16 art. 132.3 vs. Circ. SCyGB 04/2026", "Santa Fe (SCyGB)"),
    ("¿Las invitaciones de TIMBÓ Compras cuentan como «medio fehaciente» para las 5 invitaciones del privado?", "Dec. 1104/16 art. 121.1 vs. UG 7 pto 15", "Santa Fe (UG TIMBÓ)"),
    ("¿La publicación de la adjudicación en Internet alcanza al privado?", "Ley 132 y Dec. 132.4 hablan de públicos", "Santa Fe (SCyGB)"),
    ("¿Quién es el «equivalente» del Subsecretario de Administración en el hospital y de quién es la «Resolución» del 2.º tramo?", "Circ. SCyGB 01/2026", "Hospital / Santa Fe"),
    ("¿Qué dice el Decreto 1247/08 sobre el tope de la directa?", "No está en la biblioteca", "Conseguir el texto"),
    ("Orden entre Jurisdicción comitente y Supervisor; entre cronograma y control URC", "UG 7 define roles, no el orden", "Santa Fe (UG TIMBÓ)"),
    ("Qué sigue después de un rechazo del Supervisor", "UG 7 pto 10 solo dice «aprueba o rechaza»", "Santa Fe (UG TIMBÓ)"),
    ("Dónde se firma el acto que aprueba el pliego", "UG 7 pto 10: el Supervisor lo carga", "Santa Fe / Compras"),
    ("¿El acto «sin efecto» del Supervisor es el de revocación?", "UG 7 pto 10 vs. Pliego 5.5", "Santa Fe (UG TIMBÓ)"),
    ("¿Quién declara desierta la licitación?", "No surge de las fuentes leídas", "Santa Fe / Compras"),
    ("¿Cómo encaja la etapa múltiple (la selecciona la Unidad Rectora) con un hospital que gestiona por expediente?", "Dec. 1104 art. 123 (texto Dec. 287/2026) + Circ. UG 8/2026", "Santa Fe (SCyGB)"),
    ("Pasos de la compra directa (rama A)", "Hay video oficial en la biblioteca, sin verificar", "Verificar el video"),
    ("Recepción, factura y pago: sistema, oficina y soporte (papel/digital)", "Pliego 6.9 a 6.13 no lo dice", "Compras del hospital"),
]

# ----------------------------------------------------- soporte documental
SOPORTE = [
    ("Formularios del pliego (PBCP)", "TIMBÓ Compras", "Digital nativo, firmado electrónicamente por los usuarios", "Se incorpora solo al expediente", "UG 7 ptos 7 y 12"),
    ("Pliego en PDF para el control de la URC", "Expediente electrónico", "Digital (PDF incorporado al expediente)", "—", "SCyGB 03/2026"),
    ("Acto que aprueba el pliego / adjudica", "Firma: a relevar · carga: TIMBÓ Compras · SIN", "Firmado (tipo de firma: a relevar)", "Disponible en el proceso publicado; SIN", "UG 7 ptos 10 y 16 · UG 11"),
    ("Ofertas", "TIMBÓ Compras", "PDF (hasta 5 MB recomendado); lo material (muestras) se entrega en papel o físico", "Válidas solo en «Oferta presentada»", "UG 7 ptos 3 y 18"),
    ("Acta de apertura y cuadro comparativo", "TIMBÓ Compras", "Digital, generado y firmado automáticamente", "Se incorporan solos al expediente", "UG 7 ptos 7 y 19"),
    ("Constancia de publicación en diarios", "Expediente electrónico", "Documentación no generada por el módulo: se incorpora al expediente (si es copia digitalizada: no se dice)", "Original en papel: a relevar", "UG 7 pto 8"),
    ("Ofertas de etapa múltiple", "Papel (sobres cerrados) + copia opcional en pendrive", "Papel original válido y vinculante; prevalece el papel", "El papel NO se digitaliza; queda en custodia; el expediente deja constancia", "UG 8 arts. 7 y 8"),
    ("Informe de preadjudicación", "TIMBÓ Compras", "Digital, firmado por los evaluadores en orden", "Se incorpora al expediente; se notifica al domicilio digital", "UG 7 pto 22"),
    ("Certificado de recepción definitiva", "No dice (a relevar)", "«Original y dos (2) copias»", "Original al SAF que tramita pagos · duplicado al adjudicatario · triplicado queda en recepción", "Pliego 6.11"),
    ("Facturas", "No dice (a relevar)", "No dice (a relevar)", "Se presentan con la orden de compra y el duplicado del certificado", "Pliego 6.12"),
    ("Notificaciones a oferentes", "Domicilio digital (ID Ciudadana)", "Electrónica, con constancia automática", "—", "UG 7 pto 5 y glosario"),
]

# -------------------------------------------------- roles y responsables
ROLES = [
    # actuación, inicia/confecciona, revisa/controla, autoriza/firma, carga en sistema, recibe/notificado, fuente
    ("Instancia y formularios del PBCP", "Gestor (rol TIMBÓ)", "Jurisdicción comitente (rol TIMBÓ)", "Supervisor aprueba o rechaza los formularios", "Gestor", "—", "UG 7 pto 10"),
    ("Control de pliegos", "—", "URC (si aplica: a confirmar)", "—", "Pase del expediente", "—", "SCyGB 03 · Res. ME 73"),
    ("Cronograma y nómina", "Supervisor", "—", "—", "Supervisor", "Proveedores de la nómina (invitación)", "UG 7 ptos 10 y 15"),
    ("Acto que aprueba el pliego y autoriza el llamado", "No establecido (a relevar)", "—", "Autoridad competente según monto", "Supervisor", "Publicado con el proceso", "UG 7 pto 10 y 16 · SCyGB 01"),
    ("SIN y vista al TCP de cada acto", "—", "TCP (control)", "—", "Direcciones Generales de Despacho (SIN)", "TCP", "UG 11 arts. 1-2 · UG 9 art. 4"),
    ("Circulares", "Gestor", "—", "—", "Gestor", "Todos los participantes", "UG 7 ptos 10 y 17"),
    ("Evaluación, subtrámites y preadjudicación", "Evaluadores", "—", "Firman el informe en orden", "Evaluadores", "Oferentes (domicilio digital)", "UG 7 ptos 10, 21 y 22"),
    ("Impugnaciones", "Oferentes", "Comisión evaluadora (informe de mérito)", "Autoridad competente resuelve con la adjudicación", "Oferentes (formulario)", "Evaluador recibe", "UG 7 pto 10 · Pliego 5.1"),
    ("Adjudicación", "No establecido (a relevar)", "—", "Autoridad competente según monto", "Supervisor", "Oferentes (dentro de 10 días hábiles)", "UG 7 pto 10 · Pliego 5.4"),
    ("Recepción definitiva", "Responsables designados por la jurisdicción", "—", "Certifican", "—", "Original: SAF · duplicado: adjudicatario", "Pliego 6.10-6.11"),
]
INCOMPATIBILIDAD = "Única incompatibilidad documentada: la recepción definitiva no debe recaer, salvo imposibilidad material, en quienes intervinieron en la adjudicación (Pliego 6.10). No se agrega ninguna otra."

MONTOS = [
    ("Contratación directa por monto", "Hasta $5.850.000", "Circ. SCyGB 01/2026 (05/01/2026) · Ley 12.510 art. 116 c.1 · tope reglamentario: Dec. 1247/08 (no leído)", "2026"),
    ("Concurso de precios para locación de inmuebles", "Hasta $29.250.000", "Circ. SCyGB 01/2026 · Ley 12.510 art. 140 pto 2", "2026"),
    ("Licitación o concurso privado", "Hasta $58.500.000", "Ley 14.424 (Presupuesto 2026), art. 36, citada en la Circ. SCyGB 01/2026 · Dec. 1104/16 art. 116 a.1 (pág. 17)", "2026"),
    ("Licitación o concurso público", "Más de $58.500.000 (regla general)", "Ley 12.510 art. 116 (pág. 40) · Circ. SCyGB 01/2026", "2026"),
    ("Aprobación hasta $5.850.000", "Resolución del Subsecretario de Administración o su equivalente", "Circ. SCyGB 01/2026", "2026"),
    ("Aprobación de $5.850.000 a $29.250.000", "Resolución (no dice de quién)", "Circ. SCyGB 01/2026", "2026"),
    ("Aprobación de $29.250.000 a $58.500.000", "Resolución conjunta con el Ministerio de Economía", "Circ. SCyGB 01/2026", "2026"),
    ("Aprobación de más de $58.500.000", "Decreto", "Circ. SCyGB 01/2026", "2026"),
    ("Cómo se calcula el monto", "Total estimado, incluidas las prórrogas; el procedimiento es válido si la adjudicación supera hasta un 20 % el tope", "Dec. 1104/16 art. 116 (pág. 17)", "Vigente"),
    ("Garantía de impugnación", "3 % de la oferta del impugnante o lo que fije el PBCP", "Pliego Único 10.1.3 (pág. 62)", "2026"),
    ("Directa por urgencia", "Al menos 3 cotizaciones (o documentar la imposibilidad); informes técnicos y legales; autoriza el funcionario según el monto", "Dec. 1104/16 art. 116 c ap. 2 (pág. 18) · Circ. UG 8/2026 art. 4 (mín. 3 proveedores)", "Vigente"),
]


# ------------------------------------------------------- maquetas
def contar_prop():
    out = {}
    for b in NUEVOS:
        out[b[1]] = out.get(b[1], 0) + 1
    return {k: [None] * v for k, v in out.items()}


v3.PROPUESTOS = contar_prop()


def detalle_etapa4():
    X, W, s = caja_detalle()
    s.append(f'<rect x="{X}" y="90" width="{W}" height="92" rx="18" fill="{TEAL_F}"/><rect x="{X}" y="160" width="{W}" height="22" fill="{TEAL_F}"/>')
    s.append(f'<circle cx="{X + 52}" cy="136" r="26" fill="{NAVY}"/>' + t(X + 52, 144, "4", 22, 700, "#fff", "middle"))
    s.append(t(X + 92, 130, "Aprobar y autorizar el llamado", 24, 700, TXT))
    s.append(t(X + 92, 156, "◀ viene de 3 · Armar el pliego      sigue en 5 · Publicar ▶", 13, 500, SUB))
    s.append(chip(X + W - 24, 112, "En TIMBÓ · parte a relevar", TEAL, "#fff", 12, False, 28, anchor="end")[0])
    y = 212
    y = seccion(s, X, y, "💡", "Qué se hace")
    s.append(t(X + 28, y, "Con el pliego aprobado, se arman el cronograma y la nómina, se hacen los controles que correspondan y la", 13.5, 400, TXT))
    s.append(t(X + 28, y + 19, "autoridad firma el acto que aprueba el pliego y autoriza el llamado. Ese acto va al SIN y al Tribunal de Cuentas.", 13.5, 400, TXT))
    y += 44
    y = seccion(s, X, y, "👥", "Quién hace qué (roles del sistema y responsabilidades del organismo)")
    cols = [("Actuación", 250), ("Confecciona", 150), ("Revisa / controla", 150), ("Autoriza / firma", 165), ("Carga en el sistema", 120)]
    x = X + 28
    for nom, w in cols:
        s.append(t(x, y, nom, 11.5, 700, SUB))
        x += w
    y += 8
    filas = [
        ("Cronograma y nómina", "Supervisor ●", "—", "—", "Supervisor ●", "documentado"),
        ("Control de pliegos", "—", "URC ? si aplica", "—", "pase del EE", "pendiente_confirmacion"),
        ("Acto que aprueba el pliego", "a relevar", "—", "Autoridad según monto ■", "Supervisor ●", "documentado"),
        ("SIN y vista al TCP del acto  NUEVO", "—", "TCP ■", "—", "Despacho ■", "documentado"),
    ]
    for act, a, b, c, d, est in filas:
        s.append(f'<rect x="{X + 24}" y="{y}" width="{W - 48}" height="34" rx="8" fill="{"#f8fafc" if "NUEVO" not in act else AZUL_F}" stroke="{LINEA}"/>')
        vals = [act.replace("  NUEVO", ""), a, b, c, d]
        x = X + 32
        for (nom, w), v in zip(cols, vals):
            col = TEAL if "●" in v else (BEIGE if "relevar" in v else (PEND if "?" in v else TXT))
            s.append(t(x, y + (18 if "NUEVO" in act and nom == "Actuación" else 22), v, 12.2, 700 if nom == "Actuación" else 500, col))
            x += w
        if "NUEVO" in act:
            s.append(t(X + 32, y + 33, "+ a sumar (F1)", 9.5, 700, AZUL))
        y += 38
    s.append(t(X + 28, y + 6, "● rol de TIMBÓ (Circ. UG 7/2026, pto 10)   ■ autoridad u organismo (Circ. SCyGB 01/2026 · UG 9 y 11/2026)   «a relevar»: no lo dice la norma", 11.5, 500, SUB))
    y += 30
    y = seccion(s, X, y, "📄", "Documentos y soporte")
    docs = [("Pliego en PDF para la URC", "Expediente electrónico", "digital"),
            ("Informe de control de la URC", "Expediente electrónico", "digital · «orden o documento informativo»"),
            ("Acto que aprueba y autoriza", "Firma: ¿dónde? a relevar · lo carga el Supervisor en TIMBÓ Compras · SIN", "firmado"),
            ("Cronograma y nómina", "TIMBÓ Compras", "digital")]
    for nom, donde, sop in docs:
        s.append(t(X + 28, y, "• " + nom, 13, 700, TXT))
        s.append(t(X + 250, y, donde, 12.5, 500, BEIGE if "relevar" in donde else TEAL))
        s.append(t(X + W - 28, y, sop, 12, 400, SUB, "end"))
        y += 20
    y += 8
    y = seccion(s, X, y, "☰", "Pasos y decisiones (3 bloques actuales + 1 a sumar)")
    for num, tit, sub, est in [("1", "Control de pliegos de la URC (estado «Aprobar contratación»)", "si aplica al hospital", "pendiente_confirmacion"),
                               ("2", "Cronograma de fechas y nómina de proveedores", "orden respecto de la URC: no documentado", "documentado"),
                               ("3", "Acto que aprueba el pliego y autoriza el llamado", "sin informe de la URC no se aprueba ni publica (si aplica)", "documentado"),
                               ("+", "SIN y vista al Tribunal de Cuentas del acto", "el expediente sigue su curso", "documentado")]:
        s.append(f'<circle cx="{X + 42}" cy="{y}" r="11" fill="{AZUL if num == "+" else NAVY}"/>' + t(X + 42, y + 4.5, num, 11, 700, "#fff", "middle"))
        s.append(t(X + 62, y + 5, tit, 13.5, 700, TXT))
        s.append(t(X + 62, y + 22, sub, 11.5, 400, SUB))
        s.append(chip_estado(X + W - 28, y - 10, est, 10.5))
        y += 38
    y = seccion(s, X, y, "↯", "Si algo sale distinto")
    s.append(t(X + 28, y, "• La URC no da su informe → el proceso no puede aprobarse ni publicarse (Circ. SCyGB 03/2026; si aplica)", 12.8, 400, TXT))
    s.append(t(X + 28, y + 18, "• Revocación del llamado → en cualquier momento antes del contrato (Pliego 5.5)  + a sumar", 12.8, 400, TXT))
    y += 44
    y = seccion(s, X, y, "📚", "Fuentes")
    s.append(t(X + 28, y, "🔗 Circ. UG 7/2026 · ptos 10, 14, 16 · pág. 3-4   ·   Circ. SCyGB 03/2026 · pág. 1   ·   Res. ME 73/2026 · art. 2 · pág. 3", 12.5, 600, "#2456c7", "start", 'text-decoration="underline"'))
    s.append(t(X + 28, y + 19, "🔗 Circ. SCyGB 01/2026 · aprobación por monto · pág. 1   ·   Circ. UG 11/2026 · arts. 1-2 · pág. 2   ·   Circ. UG 9/2026 · arts. 3-5 · pág. 2", 12.5, 600, "#2456c7", "start", 'text-decoration="underline"'))
    y += 34
    c = cuenta(ETAPAS[3][3])
    s.append(f'<rect x="{X + 24}" y="{y}" width="{W - 48}" height="46" rx="12" fill="{PEND_F}" stroke="{PEND}" stroke-width="1.4"/>')
    s.append(t(X + 40, y + 19, "Estado: " + "  ·  ".join(f"{ESTADO[k][0]} {v} {ESTADO[k][1].lower()}" for k, v in c.items()) + "  ·  +1 a sumar (documentado)", 12.8, 700, TXT))
    s.append(t(X + 40, y + 37, "❓ ¿La URC controla al hospital?   ❓ ¿Quién es la «autoridad según monto» en el hospital?   ❓ ¿Dónde se firma el acto?", 12, 500, PEND))
    return s


def detalle_decision31():
    X, W, s = caja_detalle()
    s.append(f'<rect x="{X}" y="90" width="{W}" height="92" rx="18" fill="{VIOLETA_F}"/><rect x="{X}" y="160" width="{W}" height="22" fill="{VIOLETA_F}"/>')
    s.append(f'<rect x="{X + 34}" y="118" width="36" height="36" rx="6" fill="{VIOLETA}" transform="rotate(45 {X + 52} 136)"/>' + t(X + 52, 142, "2", 18, 700, "#fff", "middle"))
    s.append(t(X + 92, 130, "¿Qué procedimiento corresponde?", 24, 700, TXT))
    s.append(t(X + 92, 156, "Regla general: licitación o concurso público; lo demás es excepción (Ley 12.510, art. 116 · pág. 40)", 13, 500, SUB))
    y = 200
    s.append(f'<rect x="{X + 24}" y="{y}" width="{W - 48}" height="40" rx="10" fill="#f8fafc" stroke="{LINEA}"/>')
    s.append(t(X + 40, y + 25, "💲 Se compara el total estimado, con prórrogas; vale si la adjudicación supera hasta 20 % el tope (Dec. 1104/16 art. 116 · pág. 17)", 12.5, 600, TXT))
    y += 52
    alts = [
        ("A", "Contratación directa", "Por monto: hasta $5.850.000 (Circ. SCyGB 01/2026; tope del Dec. 1247/08: no leído) · o por causal (art. 116 c, ap. 4 a 8)",
         "📍 Expediente electrónico (Circ. UG 2/2025) · no va por TIMBÓ Compras", "◌ Pasos: pendientes de documentación", PEND, True),
        ("B", "Directa por urgencia o desierto", "Urgencia: ≥ 3 cotizaciones, informes técnicos y legales (Dec. 1104 art. 116 c.2) · Desierto: sin ofertas o todas inadmisibles (c.3)",
         "📍 TIMBÓ Compras, con flexibilizaciones y mín. 3 invitados (Circ. UG 8/2026) · sigue en la etapa 3", "✔ Documentado", OK, False),
        ("C", "Licitación o concurso, de simple sobre", "Privado hasta $58.500.000: ≥ 5 invitaciones (Dec. 1104 art. 121) · Público más de $58.500.000: Boletín Oficial y diarios (art. 132.3)",
         "📍 TIMBÓ Compras, obligatorio en Salud desde el 1/4/2026 (Circ. UG 3/2026) · camino principal", "✔ Documentado · ? 1 discrepancia (diarios)", OK, False),
        ("D", "Etapa múltiple", "Evaluación en 2 o más fases con preselecciones sucesivas; la selecciona la Unidad Rectora (Dec. 1104 art. 123, texto del Dec. 287/2026)",
         "📍 Expediente + Documentos Oficiales; ofertas en sobres de papel (Circ. UG 8/2026) · sigue en la etapa 8", "✔ Documentado", OK, False),
    ]
    for letra, tit, linea, donde, estado, col, punt in alts:
        principal = letra == "C"
        s.append(f'<rect x="{X + 24}" y="{y}" width="{W - 48}" height="132" rx="14" fill="#fff" stroke="{VIOLETA}" stroke-width="{3 if principal else 1.5}" filter="url(#s)"/>')
        s.append(f'<circle cx="{X + 58}" cy="{y + 32}" r="20" fill="{VIOLETA}"/>' + t(X + 58, y + 39, letra, 18, 700, "#fff", "middle"))
        s.append(t(X + 92, y + 32, tit, 18, 700, TXT))
        s.append(t(X + 92, y + 58, linea, 12.3, 400, TXT))
        s.append(t(X + 92, y + 82, donde, 12.5, 600, TEAL))
        s.append(chip(X + 92, y + 94, estado, col if not ("?" in estado) else PEND, PEND_F if punt else OK_F, 11, punt, 22)[0])
        s.append(chip(X + W - 48, y + 92, "Ver recorrido ›", VIOLETA, "#fff", 13, False, 28, anchor="end")[0])
        y += 144
    s.append(t(X + 28, y + 6, "Montos 2026 (Ley de Presupuesto 14.424). Quién aprueba cada tramo: tabla «Montos y autoridades» de la revisión.", 12.3, 400, SUB))
    return s


def detalle_etapa7_31():
    s = v3.detalle_etapa7()
    # reemplaza la sección «Si algo sale distinto» por la versión con bloques a sumar: se agrega aviso
    X = 684
    s.append(f'<rect x="{X + 24}" y="1004" width="1" height="1" fill="none"/>')
    return s


def maquetas():
    sub = "Circuito oficial de TIMBÓ · solo con fuente · revisión " + FECHA
    return [
        ("A · Vista general + detalle de la etapa 4 (roles, documentos y soporte)", svg(marco("oficial", sub) + panel_general("4") + detalle_etapa4())),
        ("B · Alternativas A, B, C y D (al tocar la decisión 2)", svg(marco("oficial", sub) + panel_general("2") + detalle_decision31())),
        ("C · Detalle de la etapa 7 (pasos, decisiones y excepciones)", svg(marco("oficial", sub) + panel_general("7") + v3.detalle_etapa7())),
        ("D · Hospital y comparación", svg(marco("comparar", "El hospital se completa en la reunión · la comparación no juzga") + panel_general("7", "hospital") + v3.detalle_comparacion())),
    ]


# ------------------------------------------------------------- HTML
def tabla(cabeza, filas):
    th = "".join(f"<th>{h(c)}</th>" for c in cabeza)
    tr = "".join("<tr>" + "".join(f"<td>{h(str(c))}</td>" for c in f) + "</tr>" for f in filas)
    return f"<div class='tabla'><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>"


def html(figs):
    tit = {n["id"]: n["titulo"] for n in OF["nodos"]}
    tit.update({b[0]: b[3] for b in NUEVOS})
    actuales = [(n["id"], n["titulo"], n["tipo"], n["estado"].replace("_", " "), len(n["fuentes"]),
                 ETAPA_DE.get(n["id"], "—"), next((c[3] for c in CAMBIOS if n["id"] in c[0]), "Sin cambios"))
                for n in OF["nodos"]]
    nuevos = [(b[0], b[1], b[3], b[4].replace("_", " "), b[5], b[6], b[7], b[8], b[9], b[10], b[11]) for b in NUEVOS]
    flechas = [(f"(nueva {i})", tit[a], tit[b], et, tp) for i, (a, b, et, tp) in enumerate(NUEVAS_FLECHAS, 1)]
    figuras = "".join(f"<section><h2>{h(ti)}</h2><div class='fig'>{s}</div></section>" for ti, s in figs)
    seguras = [b for b in NUEVOS if b[4] == "documentado" and "a confirmar" not in b[10].lower()]
    validar = [b for b in NUEVOS if b not in seguras]
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Circuito de compras · revisión v3.1</title>
<style>
body{{margin:0;background:#f6f7f9;color:#1f2937;font:15px/1.5 "Segoe UI",system-ui,Arial,sans-serif}}
main{{max-width:1280px;margin:0 auto;padding:24px 16px 60px}}
section{{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:20px 22px;margin-top:18px}}
h1{{margin:0 0 4px;font-size:26px}} h2{{margin:0 0 8px;font-size:20px}}
.fig{{border:1px solid #e2e8f0;border-radius:12px;overflow:auto}} .fig svg{{display:block;width:100%;height:auto;min-width:1000px}}
table{{border-collapse:collapse;width:100%;font-size:13px}} th,td{{border-bottom:1px solid #e2e8f0;padding:6px 8px;text-align:left;vertical-align:top}}
th{{background:#f8fafc}} .tabla{{overflow-x:auto}} .ok{{color:#1b7a45;font-weight:700}} .warn{{color:#b85400;font-weight:700}}
nav a{{margin-right:12px}}
</style></head><body><main>
<h1>Circuito de compras · revisión final v3.1</h1>
<p>Fuentes releídas el {FECHA}. <b>Nada está aplicado en el Centro</b>: maqueta, tablas y propuestas para aprobar.</p>
<nav><a href="#nuevos">Bloques nuevos</a><a href="#cambios">Cambios</a><a href="#actuales">Bloques actuales</a><a href="#fuentes">Fuentes</a><a href="#montos">Montos</a><a href="#soporte">Soporte</a><a href="#roles">Roles</a><a href="#pend">Pendientes</a><a href="#reco">Recomendación</a></nav>
{figuras}
<section id="nuevos"><h2>1. Bloques nuevos propuestos: 12 (F1 a F7)</h2>
<p><b>Aclaración:</b> la v3 decía «6 bloques» porque contaba F1 a F6 y mostraba F7 (excepciones) solo como texto. Ahora F7 también son bloques. F8 a F13 no agregan bloques: cambian etiquetas o quedan pendientes.</p>
{tabla(["Id", "Etapa", "Bloque", "Estado", "Hallazgo", "Aplica a", "Momento", "Actor", "Documento / actuación", "Obligatorio o condicional", "Fuente (apartado · página)"], nuevos)}
<p>Flechas nuevas ({len(NUEVAS_FLECHAS)}). n04 (discrepancia) y n09 (revocación, «en cualquier momento») no se conectan: ninguna fuente fija a qué paso.</p>
{tabla(["", "Desde", "Hasta", "Condición", "Tipo"], flechas)}</section>
<section id="cambios"><h2>2. Cambios a elementos existentes (sin borrar nada)</h2>
{tabla(["Elemento", "Qué es", "Hoy", "Propuesta", "Hallazgo"], CAMBIOS)}</section>
<section id="actuales"><h2>3. Bloques actuales del circuito oficial</h2>
<p class="ok">{len(OF['nodos'])} bloques y {len(OF['flechas'])} flechas: todos se conservan con su texto, estado, fuentes, comentarios e historial. Después de aprobar: {len(OF['nodos']) + len(NUEVOS)} bloques y {len(OF['flechas']) + len(NUEVAS_FLECHAS)} flechas.</p>
{tabla(["Id", "Bloque", "Tipo", "Estado", "Fuentes", "Etapa", "Cambio propuesto"], actuales)}</section>
<section id="fuentes"><h2>4. Fuentes normativas</h2>
{tabla(["Documento", "Emisor", "Fecha y vigencia", "Id en la biblioteca", "Lectura"], FUENTES)}</section>
<section id="montos"><h2>5. Montos y autoridades 2026</h2>
<p>No se encontró contradicción entre fuentes en los montos. Lo que no se pudo verificar: el Dec. 1247/08 (base del tope de la directa) y quién es el «equivalente» en el hospital.</p>
{tabla(["Concepto", "Valor", "Fuente", "Vigencia"], MONTOS)}</section>
<section id="soporte"><h2>6. Soporte documental (criterio transversal)</h2>
<p>Cuatro lugares: <b>papel</b> · <b>expediente electrónico</b> · <b>TIMBÓ Compras</b> · <b>portal</b> (de Compras / del proveedor). Un escaneo no reemplaza al original salvo que una norma lo diga; la única regla explícita es la de la etapa múltiple: el papel no se digitaliza y queda en custodia (UG 8, art. 8).</p>
{tabla(["Documento", "Dónde", "Tipo de soporte", "Circulación / archivo", "Fuente"], SOPORTE)}</section>
<section id="roles"><h2>7. Roles y responsabilidades</h2>
<p>Separa los <b>roles de TIMBÓ</b> (Gestor, Supervisor, Evaluador, Jurisdicción comitente, Oferente) de las <b>responsabilidades del organismo</b> (autoridad competente, Despacho, URC, TCP, responsables de recepción). «No establecido» = ninguna fuente lo dice.</p>
{tabla(["Actuación", "Inicia / confecciona", "Revisa / controla", "Autoriza / firma", "Carga en el sistema", "Recibe / se notifica", "Fuente"], ROLES)}
<p>{h(INCOMPATIBILIDAD)}</p></section>
<section id="pend"><h2>8. Pendientes de confirmación</h2>
{tabla(["Pregunta", "Por qué", "A quién"], HALLAZGOS_PEND)}</section>
<section id="reco"><h2>9. Recomendación</h2>
<p class="ok">Se puede implementar con seguridad (texto oficial claro, sin condición dudosa):</p>
<ul><li>Las 9 etapas y los dos paneles (es reorganización visual: no cambia datos).</li>
{''.join(f"<li>{h(b[0])} · {h(b[3])} ({h(b[11])})</li>" for b in seguras)}
<li>Cambios f45 y o31 (UG 11/2026) y la etiqueta de f28/o18 (público, Dec. 1104 art. 132.3).</li></ul>
<p class="warn">Requiere validación antes de presentarlo como regla:</p>
<ul>{''.join(f"<li>{h(b[0])} · {h(b[3])}: {h(b[10])}</li>" for b in validar)}
<li>f18 / f39 (URC «si aplica») y o16 (dónde se firma): dependen de las respuestas de Santa Fe; mientras tanto, quedan como pendientes visibles.</li></ul>
</section>
</main></body></html>"""


if __name__ == "__main__":
    figs = maquetas()
    for i, (_, s) in enumerate(figs):
        (AQUI / f"v31_{'ABCD'[i]}.svg").write_text(s, encoding="utf-8")
    (AQUI / "revision_v31.html").write_text(html(figs), encoding="utf-8")
    print("nuevos", len(NUEVOS), "flechas nuevas", len(NUEVAS_FLECHAS), "cambios", len(CAMBIOS))
