"""Carga inicial de la gestión de procesos. No pisa nada: solo crea lo que
falta.

- Circuito oficial de TIMBÓ (licitación o concurso): armado SOLO con
  fragmentos textuales de documentos oficiales leídos completos el
  17/11/2026, con punto y página del PDF que enlaza la biblioteca. Donde la
  documentación no dice algo (por ejemplo, qué pasa después de que el
  Supervisor rechaza un formulario), hay un bloque "pendiente" en vez de
  completarlo.
- Circuito actual del hospital: vacío. Se arma en las reuniones.
- Rangos de montos 2026: copia de la Circular SCyGB 01/2026.
"""
import json
from datetime import date

from app.extensions import db
from app.models import AuditoriaProceso, Circuito, CircuitoVersion, ComentarioCircuito, RangoMonto
from app.procesos import logica

SLUG_OFICIAL = "oficial-timbo-licitacion"
SLUG_HOSPITAL = "hospital-compras"
FECHA_LECTURA = "17/11/2026"


def F(doc, punto, pagina, fragmento, capitulo=""):
    return {"doc": doc, "punto": punto, "pagina": str(pagina) if pagina else "", "capitulo": capitulo,
            "fragmento": fragmento, "verificada": True}


UG7, UG8, UG3, UG2_25 = "circ-ug-7-2026", "circ-ug-8-2026", "circ-ug-3-2026", "circ-ug-2-2025"
SC1, SC3, SC4, ME73, UG9 = "circ-scygb-1-2026", "circ-scygb-3-2026", "circ-scygb-4-2026", "res-me-73-2026", "circ-ug-9-2026"
LEY, PLIEGO = "ley-12510", "pliego-unico-2026"

P6 = F(UG7, "Punto 6 (Etapas del proceso)", 2,
       "La etapa preparatoria se resuelve por expediente electrónico de TIMBÓ. El pliego de bases y condiciones "
       "particulares, las consultas y circulares, las impugnaciones, el acta de apertura de ofertas, las ofertas "
       "presentadas, la evaluación de ofertas, los trámites de subsanación de defectos, mejora de ofertas, "
       "documentación aclaratoria y/o complementaria y el informe de preadjudicación serán gestionados a través de "
       "TIMBÓ COMPRAS. La adjudicación y etapa contractual serán resueltas por expediente electrónico de TIMBÓ.")
P10_GESTOR = F(UG7, "Punto 10 (Roles) — Gestor", 3,
               "Gestor: Genera la instancia de contratación. Completa los formularios del pliego de bases y condiciones "
               "particulares. Genera circulares.")
P10_SUP = F(UG7, "Punto 10 (Roles) — Supervisor", 3,
            "Supervisor: Aprueba o rechaza los formularios del pliego de bases y condiciones particulares. Confecciona "
            "el cronograma y la nómina de proveedores. Carga los actos administrativos que aprueban el pliego y "
            "autorizan el llamado, los sin efecto y la adjudicación.")
P10_EVAL = F(UG7, "Punto 10 (Roles) — Evaluador", 3,
             "Evaluador: Evalúa las ofertas. Genera los trámites de subsanación de defectos, mejora de precios y "
             "aclaración y/o documentación complementaria. Preselecciona los renglones y oferentes. Organiza a los "
             "evaluadores. Preadjudica. Carga el cronograma de impugnaciones. Recibe las impugnaciones de oferta y "
             "preadjudicación.")
APROBACION = F(SC1, "Aprobación de actos licitatorios", 1,
               "Hasta $ 5.850.000 Por Resolución del Subsecretario de Adm. ó su equivalente. Entre $ 5.850.000 y "
               "$ 29.250.000 Por Resolución. Entre $ 29.250.000 y $ 58.500.000 Por Resolución Conjunta con el M. de "
               "Economía. Más de $ 58.500.000 Por Decreto.")
URC_ART2 = F(ME73, "Artículo 2°", 3,
             "Instrúyase a la Unidad Rectora Central a efectuar los siguientes controles, que revisten el carácter de "
             "obligatorios, sobre las gestiones de Licitación Pública y de Concurso Público que se tramiten en el Módulo "
             "\"TIMBÓ COMPRAS\": 1) Control de pliegos; 2) Control de lo resuelto por la comisión de preadjudicación;")

AVISO_ADM_CENTRAL = ("Está dirigida a las jurisdicciones de la Administración Pública Central. Si alcanza al hospital "
                     "está pendiente de confirmar.")


def _n(nid, tipo, titulo, x, y, estado="documentado", sistema="sin_definir", soporte="sin_definir", fuentes=(),
       descripcion="", responsables=(), sector="", condiciones="", resultado="", documentacion="", **extra):
    nodo = {"id": nid, "tipo": tipo, "titulo": titulo, "x": x, "y": y, "estado": estado, "sistema": sistema,
            "soporte": soporte, "fuentes": list(fuentes), "descripcion": descripcion,
            "responsables": [{"funcion": f, "quien": q, "perfil_timbo": p} for f, q, p in responsables],
            "sector": sector, "condiciones": condiciones, "resultado": resultado, "documentacion": documentacion}
    nodo.update(extra)
    return nodo


def contenido_oficial(rangos):
    """`rangos`: dict nombre → id de RangoMonto, para las flechas por monto."""
    EXP, COM, FUERA = "expediente", "compras", "fuera"
    A, X, C, E = -300, 60, 400, 740  # columnas: directas, expediente, Compras, otros
    nodos = [
        _n("o01", "inicio", "Inicio: etapa preparatoria", X, 0, sistema=EXP, fuentes=[P6]),
        _n("o02", "etapa", "Etapa preparatoria por expediente electrónico", X, 110, sistema=EXP, soporte="digital",
           fuentes=[P6], descripcion="La etapa preparatoria se resuelve por expediente electrónico de TIMBÓ. Qué "
                                     "documentos lleva y quién los arma en el hospital no está documentado acá."),
        _n("o03", "condicion", "Tener el número de expediente electrónico", X, 220, sistema=EXP,
           fuentes=[F(UG7, "Punto 11 (Formulario de proceso)", 3,
                      "Para iniciar un proceso de contratación se deberá contar con un número de expediente electrónico de "
                      "TIMBÓ, siendo entera responsabilidad de los usuarios la información, documentación y/o "
                      "autorizaciones necesarias para iniciar un procedimiento de selección en cumplimiento de la "
                      "normativa vigente.")]),
        _n("o04", "decision", "¿Qué procedimiento corresponde?", X, 340,
           fuentes=[F(LEY, "Artículo 116", 40,
                      "Toda compra o venta por cuenta de la Provincia (...) se debe hacer, por regla general, previa "
                      "licitación o concurso público. No obstante puede contratarse por: a) licitación o concurso privado, "
                      "cuando el valor estimado de la operación no exceda el importe que establezca la Ley de Presupuesto; "
                      "(...) c) contratación directa, en los siguientes casos (...)"),
                    F(SC1, "Encuadre", 1, "Hasta $5.850.000 CONTRATACIÓN DIRECTA POR MONTO. (...) LICITACIÓN O CONCURSO "
                                          "PRIVADO hasta $ 58.500.000. LICITACIÓN O CONCURSO PÚBLICO más de $ 58.500.000.")],
           descripcion="Según el monto estimado y la causal. Los montos son de 2026 (Ley de Presupuesto 14.424)."),
        _n("o05", "actividad", "Gestión directa por expediente", A, 480, sistema=EXP, soporte="digital",
           fuentes=[F(UG2_25, "Punto 2 (Compras directas)", 8,
                      "Los siguientes incisos para la gestión de compras enmarcadas en el Art. 116° de la Ley 12.510 se "
                      "realizarán de forma exclusivamente digital a partir de la fecha de circulación de la presente. "
                      "Compras y contrataciones - Gestión directa - Por monto menor al tope; Por especialización; "
                      "Exclusividad; Entre organismos oficiales del Sector Público; Por reparación de maquinaria; In situ")],
           descripcion="Las compras directas no están en el alcance de TIMBÓ Compras: van por expediente."),
        _n("o05b", "pendiente", "Pasos de la gestión directa", A, 600, estado="pendiente_documentacion", sistema=EXP,
           descripcion="Falta cargar acá los pasos de la compra directa con su fuente. El Centro tiene una lección "
                       "armada con la capacitación oficial en video; pasarla a este circuito cita por cita."),
        _n("o06", "actividad", "Directa por urgencia o desierto en TIMBÓ Compras", C, 480, sistema=COM, soporte="digital",
           fuentes=[F(UG8, "Artículo 3°", 1,
                      "La tramitación de las contrataciones directas por urgencia o emergencia, y por procedimiento desierto "
                      "o fracasado, se sustancia íntegramente mediante el Módulo \"TIMBÓ COMPRAS\"."),
                    F(UG8, "Artículo 4°", 2,
                      "a) Autorización: es suficiente la intervención sistémica de la autoridad competente o la vinculación "
                      "del documento autorizatorio, sin necesidad de acto administrativo formal. b) Plazos: pueden "
                      "reducirse u omitirse los períodos de consultas e impugnaciones (...) d) Invitaciones: la carga "
                      "mínima es de tres (3) proveedores en el sistema.")],
           condiciones="Mínimo 3 proveedores invitados. Consultas e impugnaciones se pueden reducir u omitir."),
        _n("o07", "condicion", "Licitación o concurso de simple sobre: obligatorio por TIMBÓ Compras", X, 480, sistema=COM,
           fuentes=[F(UG3, "Puntos 2 a 4", 1,
                      "La obligatoriedad dispuesta alcanza a los restantes Ministerios (...) Ministerio de Salud. (...) "
                      "Licitaciones Públicas, Licitaciones Privadas, Concursos Públicos y Concursos Privados, bajo la "
                      "modalidad de \"simple sobre\" (...) a partir del 1 de abril del año en curso, la utilización será "
                      "obligatoria para toda la Administración Pública Provincial.")]),
        _n("o08", "actividad", "Etapa múltiple: expediente y Documentos Oficiales", E, 480, sistema=EXP,
           soporte="papel_y_digital",
           fuentes=[F(UG8, "Artículos 5° a 8°", 2,
                      "Hasta que el Módulo \"TIMBÓ COMPRAS\" incorpore la funcionalidad técnica para gestionar "
                      "procedimientos de etapa múltiple, su sustanciación integral se realiza de forma exclusiva a través "
                      "de los módulos de Expediente Electrónico (EE) y Documentos Oficiales (DO) (...) La recepción de las "
                      "propuestas (...) se efectúa mediante entrega material de sobres físicos cerrados (...)")],
           descripcion="Las ofertas se entregan en sobres de papel; las actas y la adjudicación son Documentos Oficiales "
                       "en el expediente."),
        _n("o09", "actividad", "Generar la instancia de contratación", C, 620, sistema=COM, soporte="digital",
           fuentes=[P10_GESTOR], responsables=[("responsable", "Gestor", True)]),
        _n("o10", "actividad", "Completar los formularios del pliego particular (PBCP)", C, 730, sistema=COM,
           soporte="digital", responsables=[("responsable", "Gestor", True)],
           fuentes=[P10_GESTOR, F(UG7, "Punto 12 (Formularios del PByCP)", 3,
                                  "El pliego de bases y condiciones particulares se confecciona completando los "
                                  "formularios estandarizados del TIMBÓ COMPRAS (...)")]),
        _n("o11", "condicion", "Al menos 3 evaluadores en el formulario «Evaluadores»", C, 840, sistema=COM,
           fuentes=[F(UG7, "Punto 13 (Comisión de evaluación)", 3,
                      "Se deberá designar al menos tres (3) evaluadores en el formulario EVALUADORES del pliego de bases y "
                      "condiciones particulares (...) Se podrá asignar un número mayor en el caso de ser necesario por la "
                      "complejidad y cuantía de la contratación o bien para resolver la falta de alguno de ellos (...)")]),
        _n("o13", "verificacion", "Revisión del pliego particular", C, 950, sistema=COM,
           responsables=[("revisa", "Jurisdicción comitente", True)],
           fuentes=[F(UG7, "Punto 10 (Roles) — Jurisdicción comitente", 3,
                      "Jurisdicción comitente: Revisa los pliegos de bases y condiciones particulares.")],
           descripcion="La circular define el rol, pero no en qué momento revisa respecto de la aprobación del Supervisor."),
        _n("o12", "decision", "¿El Supervisor aprueba los formularios?", C, 1070, sistema=COM,
           responsables=[("autoriza", "Supervisor", True)], fuentes=[P10_SUP]),
        _n("o12b", "pendiente", "Qué pasa después de un rechazo", E, 1070, estado="pendiente_documentacion", sistema=COM,
           descripcion="La Circular UG 7/2026 dice que el Supervisor «aprueba o rechaza» los formularios, pero no "
                       "dice cómo sigue el trámite después de un rechazo."),
        _n("o14", "verificacion", "Control de pliegos de la URC (estado «Aprobar contratación»)", X, 1200,
           estado="pendiente_confirmacion", sistema=EXP, soporte="digital", condiciones=AVISO_ADM_CENTRAL,
           responsables=[("revisa", "Unidad Rectora Central (Dirección General de Contrataciones y Gestión de Bienes)", False)],
           fuentes=[F(SC3, "Estado: Aprobar contratación", 1,
                      "En este estado del proceso electrónico, con los formularios del pliego de bases y condiciones "
                      "particulares aprobado por el rol SUPERVISOR, y previo a la emisión del acto administrativo que "
                      "aprueba la contratación y autoriza el llamado, se deberá remitir para el control de los pliegos, el "
                      "expediente electrónico con el Pliego de Bases y Condiciones Particulares en formato pdf incorporado. "
                      "El proceso de contratación no podrá aprobarse ni publicarse sin el correspondiente informe de "
                      "control de la URC (...)"), URC_ART2]),
        _n("o15", "actividad", "Cronograma de fechas y nómina de proveedores", C, 1200, sistema=COM, soporte="digital",
           responsables=[("responsable", "Supervisor", True)],
           fuentes=[P10_SUP, F(UG7, "Punto 14 (Cronograma de fechas y nómina)", 3,
                               "En el cronograma de fechas se determina el día y hora de inicio y fin para realizar las "
                               "acciones durante la etapa de publicación, la apertura de ofertas y el período para presentar "
                               "impugnaciones a las ofertas.")],
           descripcion="La circular no dice en qué orden se hace respecto del control de la URC."),
        _n("o16", "autorizacion", "Acto que aprueba el pliego y autoriza el llamado", X, 1320, sistema=EXP,
           soporte="digital", fuentes=[P10_SUP, APROBACION],
           responsables=[("autoriza", "Autoridad competente según el monto", False),
                         ("responsable", "Supervisor (lo carga en TIMBÓ Compras)", True)],
           condiciones="Quién firma depende del monto (Circular SCyGB 01/2026). Quién es el «equivalente» del "
                       "Subsecretario de Administración en el hospital: a confirmar."),
        _n("o17", "actividad", "Proceso publicado e invitaciones a la nómina", C, 1440, sistema=COM, soporte="digital",
           fuentes=[F(UG7, "Punto 15 (Publicidad y difusión)", 4,
                      "De manera complementaria y supletoria a la publicidad y difusión obligatoria establecida en la "
                      "normativa vigente, TIMBÓ COMPRAS envía invitaciones a participar de los procesos a los correos "
                      "detallados en la nómina de proveedores."),
                    F(UG7, "Punto 16 (Proceso publicado)", 4,
                      "Los procesos publicados en TIMBÓ COMPRAS se encontrarán disponibles con su correspondiente "
                      "documentación en la bandeja Participar de un proceso para todos aquellos interesados que cuenten "
                      "con ID ciudadana.")]),
        _n("o18", "actividad", "Publicación en el portal web y pedido de aviso oficial", E, 1440, sistema=FUERA,
           soporte="digital", condiciones="La Circular SCyGB 04/2026 está dirigida a las jurisdicciones de la "
                                          "Administración Pública Central.",
           fuentes=[F(SC4, "Anexo I", 2,
                      "Una vez aprobado el pliego en el ecosistema TIMBO se deberá realizar la publicación en el portal Web "
                      "de la Provincia. (...) Se debe seleccionar la opción \"Marcar para que se genere enlace con TIMBO.\" "
                      "y marcar como expediente principal. Si no se seleccionan estas opciones, al proveedor no le "
                      "aparecerá el botón de OFERTAR en la publicación web del portal de compras."),
                    F(SC4, "Anexo II", 4,
                      "Se deberá enviar un mail, con una nota que contenga el detalle de la publicación (...) a la casilla "
                      "avisosoficiales@santafe.gob.ar (...) con al menos tres (3) días de antelación (...)")]),
        _n("o19", "actividad", "Consultas y circulares", E, 1560, sistema=COM, soporte="digital",
           responsables=[("inicia", "Oferente / Proveedor (consulta)", True), ("responsable", "Gestor (circulares)", True)],
           fuentes=[F(UG7, "Punto 17 (Consultas)", 4,
                      "Para efectuar consultas, recibir circulares aclaratorias o modificatorias, el proveedor deberá haber "
                      "participado del proceso. Las consultas se efectúan en la bandeja de mis ofertas del TIMBÓ COMPRAS. "
                      "(...) Las consultas enviadas no indicarán el autor de la consulta."), P10_GESTOR]),
        _n("o20", "actividad", "Presentación de ofertas", C, 1600, sistema=COM, soporte="digital",
           responsables=[("responsable", "Oferente / Proveedor", True)],
           fuentes=[F(UG7, "Punto 18 (Ofertas)", 4,
                      "Las ofertas se podrán presentar hasta la fecha y hora de apertura (...) La documentación electrónica "
                      "requerida deberá presentarse en formato PDF, hasta un máximo de 5 MB recomendable. (...) Sólo "
                      "aquellas ofertas que se encuentren en estado oferta presentada serán válidas en la apertura "
                      "electrónica de ofertas.")]),
        _n("o20e", "error", "La oferta no quedó en «Oferta presentada»", E, 1700, sistema=COM,
           fuentes=[F(UG7, "Punto 18 (Ofertas)", 4, "Sólo aquellas ofertas que se encuentren en estado oferta presentada "
                                                    "serán válidas en la apertura electrónica de ofertas.")],
           error={"causa": "El proveedor no confirmó ni envió la oferta antes de la hora de apertura.",
                  "detecta": "", "interviene": "",
                  "resolucion": "No es válida en la apertura electrónica.",
                  "nueva_autorizacion": False, "doc_adicional": False}),
        _n("o21", "actividad", "Apertura automática", C, 1720, sistema=COM, soporte="digital",
           responsables=[("responsable", "TIMBÓ Compras (automático)", False)],
           fuentes=[F(UG7, "Punto 19 (Apertura de ofertas)", 4,
                      "La apertura de ofertas se efectuará automáticamente en TIMBÓ COMPRAS en la hora y fecha establecida "
                      "en el cronograma de fechas. En forma electrónica y automática se generará el acta de apertura de "
                      "ofertas correspondiente y el cuadro comparativo de precios.")]),
        _n("o21d", "documento", "Acta de apertura y cuadro comparativo", E, 1820, sistema=COM, soporte="digital",
           fuentes=[F(UG7, "Punto 19 (Apertura de ofertas)", 4, "En forma electrónica y automática se generará el acta de "
                                                               "apertura de ofertas correspondiente y el cuadro comparativo "
                                                               "de precios."),
                    F(UG7, "Punto 7 (Documentación generada del proceso)", 2,
                      "Todas las etapas del proceso de contratación en TIMBÓ COMPRAS generan documentación oficial firmada "
                      "electrónicamente (...) Se incorporan al expediente electrónico relacionado al proceso de "
                      "contratación, de manera automática en las etapas correspondientes.")],
           documento={"origen": "TIMBÓ Compras (automático)", "completa": "TIMBÓ Compras", "recibe": "", "revisa": "",
                      "autoriza": "", "registra": "Expediente electrónico relacionado (automático)",
                      "archiva": "Expediente electrónico", "continua": "Evaluación de ofertas"}),
        _n("o22", "actividad", "Evaluación de ofertas y preselección", C, 1840, sistema=COM, soporte="digital",
           responsables=[("responsable", "Evaluadores", True)], fuentes=[P10_EVAL]),
        _n("o23", "decision", "¿Hace falta subsanar, aclarar o mejorar?", C, 1960, sistema=COM,
           responsables=[("responsable", "Evaluadores", True)], fuentes=[P10_EVAL]),
        _n("o24", "actividad", "Subtrámite al proveedor: subsanación, aclaración o mejora", E, 2080, sistema=COM,
           soporte="digital", responsables=[("inicia", "Evaluadores", True), ("recibe", "Oferente / Proveedor", True)],
           fuentes=[F(UG7, "Punto 21 (Subsanación, aclaración y/o mejora)", 5,
                      "Los subtrámites de subsanación, aclaración, mejora de precios y/o documentación complementaria que "
                      "se remitan a los oferentes con motivo de la evaluación de las ofertas se encontrarán disponibles en "
                      "su bandeja mis ofertas y serán notificados al domicilio digital. (...) Los subtrámites respondidos "
                      "por el proveedor o descartados se incorporarán automáticamente al expediente electrónico.")]),
        _n("o24x", "excepcion", "Vence el plazo sin respuesta: queda «descartado»", E, 2200, sistema=COM,
           fuentes=[F(UG7, "Punto 21 (Subsanación, aclaración y/o mejora)", 5,
                      "Finalizada la fecha y hora límite establecida por el evaluador para cumplimentar con el subtrámite, "
                      "este pasa a estado descartado.")]),
        _n("o25", "actividad", "Informe de preadjudicación", C, 2200, sistema=COM, soporte="digital",
           responsables=[("responsable", "Evaluadores (firman en el orden de «Ordenar evaluadores»)", True)],
           fuentes=[F(UG7, "Punto 22 (Informe de preadjudicación)", 5,
                      "Sobre el informe de preadjudicación actuarán y firmarán aquellos evaluadores designados en el orden "
                      "del formulario Ordenar evaluadores."),
                    F(PLIEGO, "5.1 Preadjudicación. Publicidad e impugnaciones", 36,
                      "La Comisión Evaluadora (o el órgano que estipule el PBCP) podrá emitir un informe de preadjudicación "
                      "que contemple el análisis de admisibilidad y conveniencia de las mismas y formule una recomendación "
                      "no vinculante de adjudicación para la autoridad competente.")]),
        _n("o26", "verificacion", "Control de la preadjudicación de la URC (estado «Cronograma de impugnación»)", X, 2320,
           estado="pendiente_confirmacion", sistema=EXP, soporte="digital", condiciones=AVISO_ADM_CENTRAL,
           responsables=[("revisa", "Unidad Rectora Central (Dirección General de Contrataciones y Gestión de Bienes)", False)],
           fuentes=[F(SC3, "Estado: Cronograma de impugnación", 1,
                      "En este estado del proceso electrónico, y previo a completar el formulario de cronograma de "
                      "impugnación que publica y notifica todo lo actuado en la evaluación, se deberá remitir el expediente "
                      "electrónico para el control de lo resuelto por la comisión de preadjudicación. El proceso de "
                      "contratación no podrá avanzar al estado preadjudicado sin el correspondiente informe de control de "
                      "la URC (...)"), URC_ART2]),
        _n("o27", "actividad", "Cronograma de impugnación: publica y notifica lo actuado", C, 2440, sistema=COM,
           soporte="digital", responsables=[("responsable", "Evaluador", True)],
           fuentes=[P10_EVAL, F(UG7, "Punto 22 (Informe de preadjudicación)", 5,
                                "(...) para los oferentes, en su formulario de oferta y notificada al domicilio digital, en "
                                "ocasión de pasar el proceso de contratación a estado preadjudicado.")]),
        _n("o28", "decision", "¿Hay impugnaciones a la preadjudicación?", C, 2560, sistema=COM,
           fuentes=[F(UG7, "Punto 20.2 (Impugnaciones al informe de preadjudicación)", 5,
                      "Con el formulario de oferta en estado preadjudicado y con toda la documentación disponible, durante "
                      "la fecha y hora de inicio y fin de impugnación establecida en el cronograma de impugnación o "
                      "publicación de la preadjudicación, los oferentes podrán iniciar la impugnación.")]),
        _n("o29", "excepcion", "Impugnación a la preadjudicación", E, 2680, sistema=COM, soporte="digital",
           responsables=[("inicia", "Oferente / Proveedor", True), ("recibe", "Evaluador", True)],
           condiciones="Dentro de los 2 días de notificados, con la garantía de impugnación.",
           fuentes=[F(UG7, "Punto 20 (Impugnaciones)", 4,
                      "Las impugnaciones se presentan a través de TIMBÓ COMPRAS, completando el formulario establecido e "
                      "integrando la garantía exigida en el pliego de bases y condiciones particulares y la normativa "
                      "vigente aplicable."),
                    F(PLIEGO, "5.1 Preadjudicación. Publicidad e impugnaciones", 36,
                      "Los oferentes podrán impugnar el informe de preadjudicación dentro de los dos (2) días de "
                      "notificados; debiendo para ello, constituir y acompañar la garantía de impugnación pertinente (...)"),
                    F(PLIEGO, "5.1 Preadjudicación. Publicidad e impugnaciones", 37,
                      "La Comisión Evaluadora analizará las impugnaciones y emitirá un informe respecto del mérito de las "
                      "mismas (...) todas las impugnaciones serán resueltas por la autoridad competente para aprobar la "
                      "contratación, en forma simultánea con la adjudicación (...)")]),
        _n("o30", "autorizacion", "Adjudicación por expediente electrónico", X, 2800, sistema=EXP, soporte="digital",
           responsables=[("autoriza", "Autoridad competente según el monto", False),
                         ("responsable", "Supervisor (carga el acto en TIMBÓ Compras)", True)],
           fuentes=[P6, P10_SUP, APROBACION,
                    F(PLIEGO, "5.4 Finalización del procedimiento. Adjudicación", 38,
                      "El dictado del acto de adjudicación, pondrá fin al procedimiento de selección. Deberá ser emitido "
                      "por la autoridad competente, dentro del plazo que establezca el PBCP, y deberá recaer sobre la "
                      "oferta más conveniente. La adjudicación será notificada, dentro de los diez (10) días hábiles "
                      "administrativos posteriores a su dictado, a todos los oferentes (...)")]),
        _n("o31", "actividad", "Vista al Tribunal de Cuentas con «Gestión de Visualización»", A, 2800, sistema=EXP,
           soporte="digital", sector="Áreas con funciones de Despacho o responsables de los actos registrables",
           condiciones="Expedientes con efecto hacendal sujetos al control preventivo de legalidad.",
           fuentes=[F(UG9, "Artículo 3°", 2,
                      "Los Expedientes Electrónicos (EE) con efecto hacendal sujetos al control preventivo de legalidad "
                      "serán puestos a disposición del TCP exclusivamente mediante la herramienta de Gestión de "
                      "Visualización del Módulo Expedientes de la EGD \"TIMBÓ\"."),
                    F(UG9, "Artículo 4°", 2,
                      "Las áreas con funciones de Despacho o aquellas responsables de la gestión de actos administrativos "
                      "registrables serán responsables de administrar la visualización de los EE."),
                    F(UG9, "Artículo 5°", 2,
                      "La puesta a disposición del TCP no interrumpirá la tramitación administrativa del expediente, el "
                      "cual continuará su curso conforme al procedimiento correspondiente.")]),
        _n("o32", "etapa", "Etapa contractual por expediente electrónico", X, 2920, sistema=EXP, fuentes=[P6]),
        _n("o33", "actividad", "Recepción provisoria", X, 3040,
           fuentes=[F(PLIEGO, "6.9 Recepción provisoria", 46,
                      "La recepción de los bienes y servicios tendrá carácter provisional y los recibos o remitos que se "
                      "firmen quedarán sujetos a la recepción definitiva.")],
           descripcion="Si se registra en TIMBÓ o fuera de él no está documentado."),
        _n("o34", "autorizacion", "Recepción definitiva y su certificación", X, 3160,
           responsables=[("responsable", "Responsables que designe la jurisdicción (no quienes intervinieron en la "
                                         "adjudicación, salvo imposibilidad material)", False)],
           fuentes=[F(PLIEGO, "6.10 Recepción definitiva", 46,
                      "La recepción definitiva debe ser otorgada en forma expresa por la Jurisdicción o Entidad contratante "
                      "mediante la emisión de la correspondiente certificación conforme al modelo aprobado por la Unidad "
                      "Rectora Central. Cada Jurisdicción o Entidad designará el o los responsables de la certificación "
                      "(...) esa designación no deberá recaer, salvo imposibilidad material, en quienes hayan intervenido "
                      "en la adjudicación respectiva (...) En caso de designarse una Comisión, ésta deberá estar integrada "
                      "por un máximo de tres (3) miembros.")]),
        _n("o34d", "documento", "Certificado de recepción definitiva", A, 3160,
           descripcion="El Pliego habla de original y dos copias. Si en TIMBÓ es un documento digital no está documentado.",
           fuentes=[F(PLIEGO, "6.11 Certificación de recepción definitiva", 48,
                      "La certificación se extenderá en original y dos (2) copias remitiéndose de inmediato el original al "
                      "Servicio Administrativo Financiero de la Jurisdicción o Entidad respectiva ante la cual se tramitan "
                      "los pagos, el duplicado se entregará al adjudicatario (...) y el triplicado quedará en poder del "
                      "órgano encargado de la recepción.")],
           documento={"origen": "Responsables de la recepción definitiva", "completa": "Responsables de la recepción definitiva",
                      "recibe": "Original: Servicio Administrativo Financiero · Duplicado: adjudicatario", "revisa": "",
                      "autoriza": "", "registra": "", "archiva": "Triplicado: órgano encargado de la recepción",
                      "continua": "Con la factura, para el pago"}),
        _n("o35", "actividad", "Presentación de facturas", X, 3280, responsables=[("responsable", "Adjudicatario", False)],
           fuentes=[F(PLIEGO, "6.12 Facturación", 48,
                      "Las facturas serán presentadas una vez recibida la documentación de recepción definitiva. (...) "
                      "juntamente con la orden de compra y el duplicado de la certificación de recepción definitiva (...)")],
           documentacion="Factura, orden de compra y duplicado del certificado de recepción definitiva."),
        _n("o36", "actividad", "Pago", X, 3400,
           condiciones="No se paga sin el certificado de recepción definitiva (Pliego 6.11).",
           fuentes=[F(PLIEGO, "6.13 Pagos", 49,
                      "El plazo para el pago de las facturas se fijará en el PBCP y se computará a partir del día siguiente a "
                      "la recepción definitiva de los bienes o servicios correspondientes."),
                    F(PLIEGO, "6.11 Certificación de recepción definitiva", 48,
                      "No se efectuará pago alguno por la provisión de bienes o servicios, si en la documentación necesaria "
                      "para tal fin no se adjunta el Certificado de Recepción Definitiva (...)")],
           descripcion="Qué oficina paga y si el trámite va por TIMBÓ no está documentado en estas fuentes."),
        _n("o36e", "error", "Factura o documentación observada", A, 3400,
           fuentes=[F(PLIEGO, "6.13 Pagos", 49, "El plazo para el pago se interrumpe si la documentación o las facturas "
                                                "presentadas fuesen observadas (...)")],
           error={"causa": "La documentación o las facturas presentadas fueron observadas.", "detecta": "", "interviene": "",
                  "resolucion": "El plazo para el pago se interrumpe.", "nueva_autorizacion": False,
                  "doc_adicional": False}),
        _n("o37", "fin", "Fin", X, 3520, fuentes=[], estado="pendiente_documentacion",
           descripcion="Cuándo se da por cerrado el trámite no está documentado en estas fuentes."),
        _n("o40", "observacion", "Lo firmado en TIMBÓ Compras se incorpora solo al expediente", E, 620, sistema=COM,
           fuentes=[F(UG7, "Punto 7 (Documentación generada del proceso)", 2,
                      "Se incorporan al expediente electrónico relacionado al proceso de contratación, de manera automática "
                      "en las etapas correspondientes. Los anexos adjuntos se visualizarán como documentos embebidos en "
                      "formato PDF."),
                    F(UG7, "Punto 8 (Documentación no generada del proceso)", 2,
                      "Toda aquella documentación de respaldo que no sea posible generar automáticamente por TIMBÓ COMPRAS "
                      "(constancia de publicidad en diarios, etc.) deberá incorporarse al expediente electrónico "
                      "relacionado al proceso cuando corresponda.")]),
    ]
    r = rangos.get
    flechas = [
        ("o01", "o02", ""), ("o02", "o03", ""), ("o03", "o04", ""),
        ("o04", "o05", "", "normal", r("Encuadre: contratación directa por monto")),
        ("o04", "o05", "Otra causal de directa (art. 116 inc. c, ap. 4 a 8)", "alternativa", None),
        ("o04", "o06", "Urgencia o emergencia, o desierto (art. 116 inc. c, ap. 2 y 3)", "alternativa", None),
        ("o04", "o07", "", "normal", r("Encuadre: licitación o concurso privado")),
        ("o04", "o07", "", "normal", r("Encuadre: licitación o concurso público")),
        ("o04", "o08", "Etapa múltiple", "alternativa", None),
        ("o05", "o05b", ""),
        ("o06", "o09", "Con las flexibilizaciones del art. 4"),
        ("o07", "o09", ""),
        ("o08", "o30", "La adjudicación también es Documento Oficial (art. 6)"),
        ("o09", "o10", ""), ("o10", "o11", ""),
        ("o11", "o13", "Orden no documentado"),
        ("o13", "o12", ""),
        ("o12", "o14", "Aprueba"),
        ("o12", "o12b", "Rechaza", "rechazo", None),
        ("o12", "o15", "Orden no documentado", "alternativa", None),
        ("o14", "o16", "Con el informe de la URC"),
        ("o15", "o16", ""),
        ("o16", "o17", ""), ("o16", "o18", ""),
        ("o17", "o19", "Si hay consultas", "alternativa", None),
        ("o17", "o20", ""), ("o19", "o20", ""),
        ("o18", "o20", "Al menos 10 días corridos entre la última publicación y la apertura (art. 132, Circ. SCyGB 04/2026)"),
        ("o20", "o20e", "", "incidencia", None),
        ("o20", "o21", ""), ("o21", "o21d", "Genera"), ("o21", "o22", ""),
        ("o22", "o23", ""),
        ("o23", "o24", "Sí"), ("o23", "o25", "No"),
        ("o24", "o24x", "Si no responde a tiempo", "alternativa", None),
        ("o24", "o25", ""), ("o24x", "o25", ""),
        ("o25", "o26", ""), ("o26", "o27", "Con el informe de la URC"),
        ("o27", "o28", ""),
        ("o28", "o29", "Sí"), ("o28", "o30", "No"),
        ("o29", "o30", "Se resuelven junto con la adjudicación (Pliego 5.1)"),
        ("o30", "o31", "Si corresponde control de legalidad", "alternativa", None),
        ("o31", "o32", "El expediente sigue su curso (Circ. UG 9/2026, art. 5)"),
        ("o30", "o32", ""), ("o32", "o33", ""), ("o33", "o34", ""),
        ("o34", "o34d", "Emite"), ("o34", "o35", ""), ("o35", "o36", ""),
        ("o36", "o36e", "", "incidencia", None),
        ("o36", "o37", ""),
    ]
    for n in nodos:  # aire vertical para que la vista detallada no se pise
        n["y"] = round(n["y"] * 1.5)
    salida = []
    for i, f in enumerate(flechas, 1):
        desde, hasta, etiqueta = f[0], f[1], f[2]
        tipo = f[3] if len(f) > 3 else "normal"
        rango = f[4] if len(f) > 4 else None
        salida.append({"id": f"f{i:02d}", "desde": desde, "hasta": hasta, "etiqueta": etiqueta, "tipo": tipo, "rango": rango})
    return {"nodos": nodos, "flechas": salida}


COMENTARIOS_OFICIAL = [
    ("o13", "santa_fe", "¿En qué momento revisa la Jurisdicción comitente: antes o después de la aprobación del Supervisor? "
                        "La Circular UG 7/2026 define el rol pero no el orden."),
    ("o15", "pendiente", "El orden entre el cronograma/nómina y el control de la URC no está documentado."),
    ("o14", "santa_fe", "¿La Res. ME 73/2026 y la Circ. SCyGB 03/2026 (controles de la URC) alcanzan a los hospitales?"),
    ("o16", "pendiente", "Quién firma en el hospital cada tramo de la Circular SCyGB 01/2026 (el «equivalente» del "
                         "Subsecretario de Administración y la «Resolución» del segundo tramo)."),
    ("o12b", "santa_fe", "Después de un rechazo del Supervisor, ¿el formulario vuelve al Gestor? No está documentado."),
]

# Circular SCyGB 01/2026 (5/1/2026), que aplica el art. 36 de la Ley de Presupuesto 14.424.
RANGOS = [
    ("Encuadre: contratación directa por monto", None, 5850000,
     "Hasta $5.850.000. Ley 12.510, art. 116 inc. c ap. 1.", "", "Encuadre"),
    ("Encuadre: concurso de precios para locación de inmuebles", None, 29250000,
     "Hasta $29.250.000. Ley 12.510, art. 140, pto 2.", "", "Encuadre"),
    ("Encuadre: licitación o concurso privado", None, 58500000,
     "Hasta $58.500.000 (Ley 14.424, art. 36; Ley 12.510, art. 116 inc. a). La circular no fija un mínimo.", "", "Encuadre"),
    ("Encuadre: licitación o concurso público", 58500000, None,
     "Más de $58.500.000.", "", "Encuadre"),
    ("Aprobación: hasta $5.850.000", None, 5850000, "Aprobación de actos licitatorios.",
     "Resolución del Subsecretario de Administración o su equivalente (en el hospital: a confirmar)",
     "Aprobación de actos licitatorios"),
    ("Aprobación: de $5.850.000 a $29.250.000", 5850000, 29250000, "Aprobación de actos licitatorios.",
     "Resolución (la circular no dice de quién)", "Aprobación de actos licitatorios"),
    ("Aprobación: de $29.250.000 a $58.500.000", 29250000, 58500000, "Aprobación de actos licitatorios.",
     "Resolución conjunta con el Ministerio de Economía", "Aprobación de actos licitatorios"),
    ("Aprobación: más de $58.500.000", 58500000, None, "Aprobación de actos licitatorios.", "Decreto",
     "Aprobación de actos licitatorios"),
]


def sembrar():
    """Crea lo que falta. Devuelve una lista de lo que hizo."""
    hecho = []
    if RangoMonto.query.count() == 0:
        for nombre, minimo, maximo, condicion, autorizacion, punto in RANGOS:
            db.session.add(RangoMonto(nombre=nombre, minimo=minimo, maximo=maximo, moneda="ARS", condicion=condicion,
                                      autorizacion=autorizacion, documentacion="", fuente_doc="circ-scygb-1-2026",
                                      fuente_punto=punto, vigencia_desde=date(2026, 1, 5), estado="verificado"))
        db.session.flush()
        hecho.append(f"{len(RANGOS)} rangos de montos (Circular SCyGB 01/2026)")
    rangos = {r.nombre: r.id for r in RangoMonto.query.all()}

    if not Circuito.query.filter_by(slug=SLUG_OFICIAL).first():
        contenido, ajustes = logica.normalizar(contenido_oficial(rangos), "oficial")
        if ajustes:
            raise RuntimeError(f"La carga oficial no cumple las reglas: {ajustes}")
        c = Circuito(slug=SLUG_OFICIAL, nombre="Circuito oficial de TIMBÓ: licitación o concurso", clase="oficial",
                     descripcion="Solo lo que dicen los documentos oficiales, con su punto y página. Lo que no está "
                                 "documentado queda pendiente. Fuentes leídas completas el " + FECHA_LECTURA + ".",
                     borrador=json.dumps(contenido, ensure_ascii=False))
        db.session.add(c)
        db.session.flush()
        db.session.add(CircuitoVersion(circuito_id=c.id, numero=1, contenido=c.borrador, importante=True,
                                       motivo="Carga inicial desde documentos oficiales (" + FECHA_LECTURA + ").",
                                       cambios=json.dumps(logica.cambios_entre(None, contenido), ensure_ascii=False)))
        for elemento, tipo, texto in COMENTARIOS_OFICIAL:
            db.session.add(ComentarioCircuito(circuito_id=c.id, elemento_id=elemento, tipo=tipo, texto=texto))
        db.session.add(AuditoriaProceso(entidad="circuito", entidad_id=str(c.id), accion="carga inicial",
                                        despues=c.nombre, motivo="Semilla oficial"))
        hecho.append("circuito oficial de TIMBÓ")

    from app.procesos import grafico_reunion
    if not Circuito.query.filter_by(slug=grafico_reunion.SLUG_REUNION).first():
        contenido, ajustes = logica.normalizar(grafico_reunion.contenido_reunion(rangos), "oficial")
        if ajustes:
            raise RuntimeError(f"El gráfico de la reunión no cumple las reglas: {ajustes}")
        c = Circuito(slug=grafico_reunion.SLUG_REUNION, nombre=grafico_reunion.NOMBRE, clase="oficial",
                     descripcion=grafico_reunion.DESCRIPCION, borrador=json.dumps(contenido, ensure_ascii=False))
        db.session.add(c)
        db.session.flush()
        db.session.add(CircuitoVersion(circuito_id=c.id, numero=1, contenido=c.borrador, importante=True,
                                       motivo="Gráfico del material de la reunión con Compras (" + FECHA_LECTURA + ").",
                                       cambios=json.dumps(logica.cambios_entre(None, contenido), ensure_ascii=False)))
        db.session.add(AuditoriaProceso(entidad="circuito", entidad_id=str(c.id), accion="carga inicial",
                                        despues=c.nombre, motivo="Gráfico de la reunión"))
        hecho.append("flujo de compras de la reunión")

    if not Circuito.query.filter_by(slug=SLUG_HOSPITAL).first():
        c = Circuito(slug=SLUG_HOSPITAL, nombre="Circuito actual de Compras del hospital", clase="hospital",
                     descripcion="Cómo se trabaja hoy, según el relevamiento con el personal de Compras. Arranca "
                                 "vacío: cada paso sale de lo que cuenta el equipo.")
        db.session.add(c)
        db.session.flush()
        db.session.add(AuditoriaProceso(entidad="circuito", entidad_id=str(c.id), accion="creado", despues=c.nombre,
                                        motivo="Circuito vacío para el relevamiento"))
        hecho.append("circuito del hospital (vacío)")
    db.session.commit()
    return hecho
