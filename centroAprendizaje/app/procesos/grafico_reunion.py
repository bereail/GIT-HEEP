"""El gráfico del flujo de compras del material de la reunión con Compras
(21 pasos en tres carriles), pasado al editor para que sea editable.

Usa las mismas citas oficiales que el circuito oficial (semilla.py). Lo que
hace el hospital y no está en ninguna norma queda «a relevar». Una
diferencia con el gráfico impreso: allá la rama A decía «sigue en 18»; eso
no está documentado, así que acá queda un bloque pendiente.
"""
from app.procesos.semilla import (
    APROBACION, AVISO_ADM_CENTRAL, F, LEY, ME73, P6, P10_EVAL, P10_GESTOR, P10_SUP, PLIEGO, SC1, SC3, SC4, UG2_25, UG3,
    UG7, UG8, UG9, URC_ART2, _n,
)

SLUG_REUNION = "circuito-compra-reunion"
NOMBRE = "Flujo de compras (gráfico de la reunión)"
DESCRIPCION = ("El gráfico de 21 pasos del material de la reunión con Compras, en tres carriles. Cada paso oficial "
               "tiene su fuente; lo que hace el hospital y no está en ninguna norma queda «a relevar».")


def contenido_reunion(rangos):
    EXP, COM, FUERA = "expediente", "compras", "fuera"
    H, X, C, D = 95, 535, 975, 1340  # columnas: hospital/externos, expediente, Compras, etapa múltiple
    RELEVAR = "Quién lo hace en el hospital: a relevar en la reunión."
    URC = "Unidad Rectora Central (Dirección General de Contrataciones y Gestión de Bienes)"
    PEND = "pendiente_documentacion"
    nodos = [
        _n("r01", "inicio", "1 · Necesidad de compra", H, 0, estado=PEND, sistema=FUERA,
           descripcion="La detecta un servicio o área del hospital. " + RELEVAR),
        _n("r02", "actividad", "2 · Solicitud del servicio", H, 140, estado=PEND, sistema=FUERA,
           descripcion="Pedido: qué, cuánto, para cuándo. " + RELEVAR),
        _n("r03", "actividad", "3 · Documentación técnica y administrativa", H, 280, estado=PEND, sistema=FUERA,
           descripcion="Especificaciones y artículo del catálogo; si falta el artículo, alta con el formulario CAByS "
                       "(Res. SCyGB 292/2026). " + RELEVAR,
           fuentes=[{"doc": "res-scygb-292-2026", "punto": "Anexo I", "pagina": "", "capitulo": "", "fragmento": "",
                     "verificada": False}]),
        _n("r04", "actividad", "4 · Inicio del expediente electrónico", X, 420, sistema=EXP, soporte="digital",
           fuentes=[F(UG7, "Punto 11 (Formulario de proceso)", 3,
                      "Para iniciar un proceso de contratación se deberá contar con un número de expediente electrónico de "
                      "TIMBÓ (...)")]),
        _n("r05", "verificacion", "5 · Presupuesto y autorizaciones", X, 560,
           estado="pendiente_confirmacion", sistema=EXP, descripcion=RELEVAR,
           condiciones="La Res. ME 73/2026 es para la Administración Pública Central: confirmar cómo es en el hospital.",
           fuentes=[F(ME73, "Artículo 4°", 3,
                      "La intervención del Ministerio de Economía, sin perjuicio de lo dispuesto en relación con la Unidad "
                      "Rectora Central, solo se realizará a los efectos de la imputación previa y/o autorización del gasto "
                      "de los distintos procedimientos de compras que realicen las distintas Jurisdicciones.")]),
        _n("r05b", "responsable", "Área presupuestaria / administrativa", H, 560, estado=PEND,
           sistema=FUERA, descripcion="¿Quién interviene? A relevar."),
        _n("r06", "decision", "6 · ¿Qué procedimiento corresponde?", X, 720,
           fuentes=[F(LEY, "Artículo 116", 40,
                      "Toda compra o venta por cuenta de la Provincia (...) se debe hacer, por regla general, previa "
                      "licitación o concurso público. No obstante puede contratarse por: a) licitación o concurso privado "
                      "(...) c) contratación directa, en los siguientes casos (...)"),
                    F(SC1, "Encuadre", 1, "Hasta $5.850.000 CONTRATACIÓN DIRECTA POR MONTO. (...) LICITACIÓN O CONCURSO "
                                          "PRIVADO hasta $ 58.500.000. LICITACIÓN O CONCURSO PÚBLICO más de $ 58.500.000.")]),
        _n("rA", "actividad", "A · Directa (por monto o causal)", H, 900,
           sistema=EXP, soporte="digital",
           descripcion="Gestión directa por expediente electrónico (no va por TIMBÓ Compras).",
           fuentes=[F(UG2_25, "Punto 2 (Compras directas)", 8,
                      "Los siguientes incisos para la gestión de compras enmarcadas en el Art. 116° de la Ley 12.510 se "
                      "realizarán de forma exclusivamente digital (...) Gestión directa - Por monto menor al tope; Por "
                      "especialización; Exclusividad; Entre organismos oficiales del Sector Público; Por reparación de "
                      "maquinaria; In situ")]),
        _n("rA2", "pendiente", "Pasos de la gestión directa", H, 1040, estado=PEND, sistema=EXP,
           descripcion="Falta cargarlos con su fuente. Cómo sigue la directa hasta la adjudicación no está documentado "
                       "en las fuentes de este gráfico."),
        _n("rB", "actividad", "B · Directa por urgencia o desierto", X, 900, sistema=COM, soporte="digital",
           condiciones="Mínimo 3 proveedores invitados. Consultas e impugnaciones se pueden reducir u omitir.",
           fuentes=[F(UG8, "Artículo 3°", 1,
                      "La tramitación de las contrataciones directas por urgencia o emergencia, y por procedimiento desierto "
                      "o fracasado, se sustancia íntegramente mediante el Módulo \"TIMBÓ COMPRAS\"."),
                    F(UG8, "Artículo 4°", 2,
                      "b) Plazos: pueden reducirse u omitirse los períodos de consultas e impugnaciones (...) d) "
                      "Invitaciones: la carga mínima es de tres (3) proveedores en el sistema.")]),
        _n("rC", "condicion", "C · Licitación o concurso", C, 900, sistema=COM,
           descripcion="Público o privado, de simple sobre: obligatorio por TIMBÓ Compras desde el 1/4/2026.",
           fuentes=[F(UG3, "Puntos 2 a 4", 1,
                      "(...) Ministerio de Salud. (...) Licitaciones Públicas, Licitaciones Privadas, Concursos Públicos y "
                      "Concursos Privados, bajo la modalidad de \"simple sobre\" (...) a partir del 1 de abril del año en "
                      "curso, la utilización será obligatoria para toda la Administración Pública Provincial.")]),
        _n("rD", "actividad", "D · Etapa múltiple", D, 900, sistema=EXP,
           soporte="papel_y_digital",
           descripcion="Por expediente y Documentos Oficiales; las ofertas se entregan en sobres de papel.",
           fuentes=[F(UG8, "Artículos 5° a 8°", 2,
                      "(...) su sustanciación integral se realiza de forma exclusiva a través de los módulos de Expediente "
                      "Electrónico (EE) y Documentos Oficiales (DO) (...) La recepción de las propuestas (...) se efectúa "
                      "mediante entrega material de sobres físicos cerrados (...)")]),
        _n("r07", "actividad", "7 · Inicio del proceso en TIMBÓ Compras", C, 1080, sistema=COM, soporte="digital",
           responsables=[("responsable", "Gestor", True)], fuentes=[P10_GESTOR]),
        _n("r08", "actividad", "8 · Pliego particular (PBCP)", C, 1220, sistema=COM, soporte="digital",
           responsables=[("responsable", "Gestor", True)],
           condiciones="Al menos 3 evaluadores en el formulario «Evaluadores».",
           fuentes=[P10_GESTOR, F(UG7, "Punto 13 (Comisión de evaluación)", 3,
                                  "Se deberá designar al menos tres (3) evaluadores en el formulario EVALUADORES del pliego "
                                  "de bases y condiciones particulares (...)")]),
        _n("r09", "verificacion", "9 · Revisión y aprobación del pliego", C, 1360, sistema=COM, soporte="digital",
           responsables=[("autoriza", "Supervisor (aprueba o rechaza los formularios)", True),
                         ("revisa", "Jurisdicción comitente", True)],
           fuentes=[P10_SUP, F(UG7, "Punto 10 (Roles) — Jurisdicción comitente", 3,
                               "Jurisdicción comitente: Revisa los pliegos de bases y condiciones particulares.")]),
        _n("r09u", "verificacion", "Control de pliegos de la URC", H, 1360, estado="pendiente_confirmacion", sistema=EXP,
           condiciones=AVISO_ADM_CENTRAL, responsables=[("revisa", URC, False)],
           fuentes=[F(SC3, "Estado: Aprobar contratación", 1,
                      "(...) previo a la emisión del acto administrativo que aprueba la contratación y autoriza el llamado, "
                      "se deberá remitir para el control de los pliegos, el expediente electrónico (...) El proceso de "
                      "contratación no podrá aprobarse ni publicarse sin el correspondiente informe de control de la URC "
                      "(...)"), URC_ART2]),
        _n("r09a", "autorizacion", "Acto: aprueba el pliego y autoriza el llamado", X, 1500, sistema=EXP, soporte="digital",
           responsables=[("autoriza", "Autoridad competente según el monto", False),
                         ("responsable", "Supervisor (lo carga en TIMBÓ Compras)", True)],
           fuentes=[P10_SUP, APROBACION]),
        _n("r10", "actividad", "10 · Publicación del procedimiento", C, 1640, sistema=COM, soporte="digital",
           fuentes=[F(UG7, "Punto 15 (Publicidad y difusión)", 4,
                      "(...) TIMBÓ COMPRAS envía invitaciones a participar de los procesos a los correos detallados en la "
                      "nómina de proveedores."),
                    F(UG7, "Punto 16 (Proceso publicado)", 4,
                      "Los procesos publicados en TIMBÓ COMPRAS se encontrarán disponibles con su correspondiente "
                      "documentación en la bandeja Participar de un proceso (...)")]),
        _n("r10p", "actividad", "Portal web de Compras y aviso oficial", H, 1640, sistema=FUERA, soporte="digital",
           condiciones="La Circular SCyGB 04/2026 está dirigida a la Administración Pública Central.",
           fuentes=[F(SC4, "Anexo I", 2,
                      "Una vez aprobado el pliego en el ecosistema TIMBO se deberá realizar la publicación en el portal Web "
                      "de la Provincia. (...) Se debe seleccionar la opción \"Marcar para que se genere enlace con TIMBO.\" "
                      "y marcar como expediente principal."),
                    F(SC4, "Anexo II", 4,
                      "(...) a la casilla avisosoficiales@santafe.gob.ar (...) con al menos tres (3) días de antelación "
                      "(...)")]),
        _n("r11", "actividad", "11 · Consultas y circulares", C, 1780, sistema=COM, soporte="digital",
           responsables=[("inicia", "Oferente / Proveedor (consulta)", True), ("responsable", "Gestor (circulares)", True)],
           fuentes=[F(UG7, "Punto 17 (Consultas)", 4,
                      "Para efectuar consultas, recibir circulares aclaratorias o modificatorias, el proveedor deberá haber "
                      "participado del proceso. (...)"), P10_GESTOR]),
        _n("r12", "actividad", "12 · Presentación de ofertas", C, 1920, sistema=COM, soporte="digital",
           responsables=[("responsable", "Oferente / Proveedor", True)],
           fuentes=[F(UG7, "Punto 18 (Ofertas)", 4,
                      "Las ofertas se podrán presentar hasta la fecha y hora de apertura (...) Sólo aquellas ofertas que se "
                      "encuentren en estado oferta presentada serán válidas en la apertura electrónica de ofertas.")]),
        _n("r13", "actividad", "13 · Apertura automática", C, 2060, sistema=COM, soporte="digital",
           responsables=[("responsable", "TIMBÓ Compras (automático)", False)],
           fuentes=[F(UG7, "Punto 19 (Apertura de ofertas)", 4,
                      "La apertura de ofertas se efectuará automáticamente en TIMBÓ COMPRAS (...) En forma electrónica y "
                      "automática se generará el acta de apertura de ofertas correspondiente y el cuadro comparativo de "
                      "precios.")]),
        _n("r14", "actividad", "14 · Evaluación de ofertas", C, 2200, sistema=COM, soporte="digital",
           responsables=[("responsable", "Evaluadores", True)], fuentes=[P10_EVAL]),
        _n("r15", "actividad", "15 · Subsanación, aclaración o mejora", C, 2340, sistema=COM, soporte="digital",
           responsables=[("inicia", "Evaluadores", True), ("recibe", "Oferente / Proveedor", True)],
           condiciones="Si el proveedor no responde a tiempo, el subtrámite queda «descartado».",
           fuentes=[F(UG7, "Punto 21 (Subsanación, aclaración y/o mejora)", 5,
                      "Los subtrámites de subsanación, aclaración, mejora de precios y/o documentación complementaria (...) "
                      "Finalizada la fecha y hora límite establecida por el evaluador para cumplimentar con el subtrámite, "
                      "este pasa a estado descartado.")]),
        _n("r16", "actividad", "16 · Informe de preadjudicación", C, 2480, sistema=COM, soporte="digital",
           responsables=[("responsable", "Evaluadores (firman en el orden de «Ordenar evaluadores»)", True)],
           fuentes=[F(UG7, "Punto 22 (Informe de preadjudicación)", 5,
                      "Sobre el informe de preadjudicación actuarán y firmarán aquellos evaluadores designados en el orden "
                      "del formulario Ordenar evaluadores.")]),
        _n("r16u", "verificacion", "Control de la preadjudicación (URC)", H, 2480, estado="pendiente_confirmacion",
           sistema=EXP, condiciones=AVISO_ADM_CENTRAL, responsables=[("revisa", URC, False)],
           fuentes=[F(SC3, "Estado: Cronograma de impugnación", 1,
                      "(...) previo a completar el formulario de cronograma de impugnación que publica y notifica todo lo "
                      "actuado en la evaluación, se deberá remitir el expediente electrónico para el control de lo resuelto "
                      "por la comisión de preadjudicación. (...)"), URC_ART2]),
        _n("r17", "excepcion", "17 · Impugnaciones", C, 2620, sistema=COM, soporte="digital",
           responsables=[("inicia", "Oferente / Proveedor", True), ("recibe", "Evaluador", True)],
           condiciones="Dentro de los 2 días de notificados, con la garantía de impugnación.",
           fuentes=[F(UG7, "Punto 20 (Impugnaciones)", 4,
                      "Las impugnaciones se presentan a través de TIMBÓ COMPRAS, completando el formulario establecido e "
                      "integrando la garantía exigida (...)"),
                    F(PLIEGO, "5.1 Preadjudicación. Publicidad e impugnaciones", 36,
                      "Los oferentes podrán impugnar el informe de preadjudicación dentro de los dos (2) días de "
                      "notificados (...)")]),
        _n("r18", "autorizacion", "18 · Adjudicación por expediente electrónico", X, 2780, sistema=EXP, soporte="digital",
           responsables=[("autoriza", "Autoridad competente según el monto", False),
                         ("responsable", "Supervisor (carga el acto en TIMBÓ Compras)", True)],
           fuentes=[P6, P10_SUP, APROBACION,
                    F(PLIEGO, "5.4 Finalización del procedimiento. Adjudicación", 38,
                      "El dictado del acto de adjudicación, pondrá fin al procedimiento de selección. Deberá ser emitido "
                      "por la autoridad competente (...)")]),
        _n("r18s", "actividad", "SIN y vista al Tribunal de Cuentas", H, 2780, sistema=EXP, soporte="digital",
           sector="Áreas con funciones de Despacho o responsables de los actos registrables",
           fuentes=[F(UG9, "Artículo 3°", 2,
                      "Los Expedientes Electrónicos (EE) con efecto hacendal sujetos al control preventivo de legalidad "
                      "serán puestos a disposición del TCP exclusivamente mediante la herramienta de Gestión de "
                      "Visualización (...)"),
                    F(UG9, "Artículo 4°", 2,
                      "Las áreas con funciones de Despacho o aquellas responsables de la gestión de actos administrativos "
                      "registrables serán responsables de administrar la visualización de los EE."),
                    F(UG9, "Artículo 5°", 2,
                      "La puesta a disposición del TCP no interrumpirá la tramitación administrativa del expediente, el "
                      "cual continuará su curso conforme al procedimiento correspondiente.")]),
        _n("r19", "etapa", "19 · Etapa contractual", X, 2920, sistema=EXP, fuentes=[P6]),
        _n("r20", "actividad", "20 · Recepción de bienes o servicios", H, 3060, descripcion=RELEVAR,
           fuentes=[F(PLIEGO, "6.9 Recepción provisoria", 46,
                      "La recepción de los bienes y servicios tendrá carácter provisional y los recibos o remitos que se "
                      "firmen quedarán sujetos a la recepción definitiva."),
                    F(PLIEGO, "6.10 Recepción definitiva", 46,
                      "La recepción definitiva debe ser otorgada en forma expresa por la Jurisdicción o Entidad contratante "
                      "mediante la emisión de la correspondiente certificación (...)")]),
        _n("r21", "actividad", "21 · Facturación y pago", H, 3200, descripcion=RELEVAR,
           fuentes=[F(PLIEGO, "6.12 Facturación", 48,
                      "Las facturas serán presentadas una vez recibida la documentación de recepción definitiva. (...)"),
                    F(PLIEGO, "6.13 Pagos", 49,
                      "El plazo para el pago de las facturas se fijará en el PBCP y se computará a partir del día siguiente "
                      "a la recepción definitiva de los bienes o servicios correspondientes.")]),
        _n("r99", "fin", "Fin", H, 3340, estado=PEND,
           descripcion="Cuándo se da por cerrado el trámite no está documentado en estas fuentes."),
        _n("rObs", "observacion", "Lo firmado en Compras va solo al expediente", D, 1080, sistema=COM,
           fuentes=[F(UG7, "Punto 7 (Documentación generada del proceso)", 2,
                      "Se incorporan al expediente electrónico relacionado al proceso de contratación, de manera automática "
                      "en las etapas correspondientes.")]),
    ]
    r = rangos.get
    flechas = [
        ("r01", "r02", ""), ("r02", "r03", ""), ("r03", "r04", ""), ("r04", "r05", ""), ("r05", "r06", ""),
        ("r06", "rA", "", "normal", r("Encuadre: contratación directa por monto")),
        ("r06", "rA", "Otra causal de directa (art. 116 inc. c, ap. 4 a 8)", "alternativa", None),
        ("r06", "rB", "Urgencia o emergencia, o desierto (art. 116 inc. c, ap. 2 y 3)", "alternativa", None),
        ("r06", "rC", "", "normal", r("Encuadre: licitación o concurso privado")),
        ("r06", "rC", "", "normal", r("Encuadre: licitación o concurso público")),
        ("r06", "rD", "Etapa múltiple", "alternativa", None),
        ("rA", "rA2", ""),
        ("rB", "r07", "Con las flexibilizaciones del art. 4"), ("rC", "r07", ""),
        ("rD", "r18", "La adjudicación también es Documento Oficial (art. 6)"),
        ("r07", "r08", ""), ("r08", "r09", ""),
        ("r09", "r09u", "Pase del expediente (si aplica)", "alternativa", None),
        ("r09", "r09a", "Aprobado"), ("r09u", "r09a", "Con el informe de la URC"),
        ("r09a", "r10", ""), ("r09a", "r10p", ""),
        ("r10", "r11", "Si hay consultas", "alternativa", None), ("r10", "r12", ""), ("r11", "r12", ""),
        ("r10p", "r12", "Al menos 10 días corridos entre la última publicación y la apertura (art. 132, Circ. SCyGB 04/2026)"),
        ("r12", "r13", ""), ("r13", "r14", ""),
        ("r14", "r15", "Si corresponde", "alternativa", None), ("r14", "r16", ""), ("r15", "r16", ""),
        ("r16", "r16u", "Pase del expediente (si aplica)", "alternativa", None),
        ("r16u", "r18", "Con el informe de la URC", "alternativa", None),
        ("r16", "r17", "Si se presentan", "alternativa", None), ("r16", "r18", ""),
        ("r17", "r18", "Se resuelven junto con la adjudicación (Pliego 5.1)"),
        ("r18", "r18s", "Si corresponde control de legalidad", "alternativa", None),
        ("r18s", "r19", "El expediente sigue su curso (Circ. UG 9/2026, art. 5)"),
        ("r18", "r19", ""), ("r19", "r20", ""), ("r20", "r21", ""), ("r21", "r99", ""),
    ]
    salida = [{"id": f"g{i:02d}", "desde": f[0], "hasta": f[1], "etiqueta": f[2],
               "tipo": f[3] if len(f) > 3 else "normal", "rango": f[4] if len(f) > 4 else None}
              for i, f in enumerate(flechas, 1)]
    carriles = [
        {"titulo": "ÁREAS DEL HOSPITAL Y ORGANISMOS EXTERNOS", "x": -20, "w": 460, "color": "naranja"},
        {"titulo": "EXPEDIENTE ELECTRÓNICO TIMBÓ", "x": 420, "w": 460, "color": "azul"},
        {"titulo": "MÓDULO TIMBÓ COMPRAS", "x": 860, "w": 460, "color": "verde"},
    ]
    return {"nodos": nodos, "flechas": salida, "carriles": carriles}
