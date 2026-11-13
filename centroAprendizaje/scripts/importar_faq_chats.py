"""Carga las situaciones de "Tengo un problema" extraídas de chats reales
de soporte (grupos de WhatsApp de Sectorial/Contrataciones), repartidas
entre los temas mihospital, timbo-expedientes y timbo-compras. Las de
timbo-compras se agregan también acá aunque varias ya existan (con otra
redacción) en timbo-expedientes: son públicos distintos (gestión interna
vs. proveedor) y no se borra nada del tema existente.

Los chats originales tenían números de teléfono y nombres de personas
reales — ninguno de esos datos entra acá, solo la duda y la solución ya
redactadas en lenguaje neutro.

Es idempotente a nivel de cada situación: si ya existe una con el mismo
(tema, slug), se reemplaza; el resto del contenido del tema no se toca.

Uso: python scripts/importar_faq_chats.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import Categoria, Situacion, Tema, Tutorial

SITUACIONES_MIHOSPITAL = [
    {
        "slug": "pedir-permisos-admin-local",
        "situacion": "¿Cómo pido los permisos de Administrador Local de TIMBÓ?",
        "descripcion": "Necesitás permisos de Administrador Local y no sabés cómo tramitarlos.",
        "causa": "Los permisos de Administrador Local no se piden directamente: hay un circuito de capacitación previo obligatorio.",
        "solucion": 'Primero hay que terminar y aprobar el curso "TIMBÓ paso a paso". Recién después te habilitan (matriculan) en el curso de "Administrador Local". Al aprobarlo, se pide el permiso por iTop indicando Apellido y nombres, CUIL y los permisos solicitados. Cuando te lo otorgan, te llega un mail.',
        "notas_adicionales": "Los tiempos de matriculación dependen de la oficina de Capacitación, no del área de soporte técnico — si tarda unos días, no es un error, es la demora habitual del circuito administrativo.",
        "categoria_libre": "Accesos y permisos",
        "verificado": True,
        "tutorial": ("primeros-pasos", "roles-y-permisos"),
    },
    {
        "slug": "vencio-periodo-inscripcion-adm-local",
        "situacion": 'Terminé el curso "Paso a paso" pero no me deja matricularme en el curso de Administrador Local',
        "descripcion": 'El curso "Paso a paso" figura aprobado, pero la inscripción al curso de Administrador Local no está disponible.',
        "causa": "El período de inscripción al curso de Administrador Local se abre por tandas en el aula virtual — puede estar cerrado en ese momento.",
        "solucion": "No hay nada para hacer del lado del usuario: hay que esperar a que se habilite una nueva matriculación. Vas a recibir un mail avisándote cuando te matriculen.",
        "categoria_libre": "Accesos y permisos",
        "verificado": True,
    },
    {
        "slug": "consultar-promotor-innovacion",
        "situacion": "¿Quién es el Promotor de Innovación de mi hospital?",
        "descripcion": "Necesitás saber quién es el referente de innovación pública de tu efector.",
        "solucion": "Hay un listado oficial por efector acá: https://www.santafe.gob.ar/ms/innovacion-publica/promotores-innovacion/",
        "categoria_libre": "Accesos y permisos",
        "verificado": True,
    },
    {
        "slug": "youtube-bloqueado-capacitaciones",
        "situacion": "Los videos de capacitación están en YouTube, pero en mi hospital el acceso a YouTube está bloqueado",
        "descripcion": "La red del hospital bloquea YouTube por política de seguridad, y ahí están alojados los videos de las capacitaciones de TIMBÓ.",
        "causa": "Las capacitaciones se publican en una lista de reproducción de YouTube, algo independiente de las políticas de bloqueo de cada red hospitalaria.",
        "solucion": (
            "Hay dos alternativas, según lo que te convenga:\n\n"
            "Opción rápida: pedile a tu área de sistemas que te habilite temporalmente el \"perfil 3\" en el proxy (SCAI) — da acceso mientras dura la capacitación.\n\n"
            "Opción más prolija: bajar los videos de la lista de reproducción oficial y subirlos a un recurso compartido de la red del hospital, para que cualquiera los vea sin necesitar acceso directo a YouTube."
        ),
        "notas_adicionales": "El perfil 3 hay que pedirlo por cada usuario y es temporal; descargar y compartir en red local es más trabajo una sola vez, pero después queda disponible para todos sin gestionar accesos individuales.",
        "categoria_libre": "Capacitación y videos",
        "verificado": True,
    },
]

SITUACIONES_TIMBO_EXPEDIENTES = [
    {
        "slug": "numeracion-fecha-documento-oficial",
        "situacion": "Firmé un documento oficial (decisorio) y no tiene número ni fecha — ¿hay que agregarlo?",
        "descripcion": "Después de firmar un decisorio, el documento no muestra numeración ni fecha.",
        "causa": "Se puede pensar que falta completar esos datos a mano, pero no es así.",
        "solucion": "No hace falta agregar nada aparte: la numeración y la fecha se completan automáticamente junto con el resto del documento cuando éste queda armado.",
        "categoria_libre": "Documentos oficiales y decisorios",
        "verificado": True,
        "tutorial": ("documentos-oficiales", "crear-documento-oficial"),
    },
    {
        "slug": "decisorio-preventivo-vs-definitivo",
        "situacion": "¿Qué decisorio corresponde: preventivo o definitivo, y qué hay que vincular en Timbó Compras?",
        "descripcion": "No queda claro cuándo usar el decisorio preventivo y cuándo el definitivo, ni qué hay que vincular en Timbó Compras.",
        "causa": "El circuito de aprobación de compras pasa dos veces por un decisorio: uno antes de la intervención del Tribunal de Cuentas y otro después.",
        "solucion": (
            "Para correr vista al Tribunal de Cuentas se envía el pliego, el expediente, el pedido, las notas y el decisorio "
            "preventivo (con la afectación presupuestaria) — se llama \"preventivo\" porque se manda previamente. "
            "En Timbó Compras hay que vincular el Documento Oficial que aprueba el pliego para poder pasar a la siguiente etapa del circuito. "
            "Una vez que el Tribunal de Cuentas aprueba, corresponde subir el decisorio definitivo al expediente y a Timbó Compras."
        ),
        "categoria_libre": "Documentos oficiales y decisorios",
        "verificado": True,
        "tutorial": ("expedientes", "vincular-documento-oficial"),
    },
    {
        "slug": "archivar-o-desestimar-documento-oficial",
        "situacion": "¿Cómo se archiva o desestima un documento oficial?",
        "descripcion": "Se busca la forma de archivar o desestimar un documento oficial ya cargado.",
        "solucion": "Una vez que el documento oficial queda firmado por todos los firmantes, se considera creado y cerrado tal cual quedó — no corresponde usar la opción de archivar o desestimar después de ese punto.",
        "categoria_libre": "Documentos oficiales y decisorios",
        "verificado": True,
    },
    {
        "slug": "link-publicacion-portal-compras",
        "situacion": "¿Dónde consigo el link para publicar la gestión en el portal de compras?",
        "descripcion": "No se sabe qué link hay que buscar para publicar una gestión de contratación en el portal.",
        "solucion": (
            "No hay que buscar un link aparte: es el mismo link que lleva a la gestión en Timbó. "
            "La publicación se hace a través de Timbó, por correo electrónico, y además se carga en el sistema SIN, "
            "según el procedimiento que establece la Circular N° 04/2026 de la Subsecretaría de Contrataciones y Gestión de Bienes."
        ),
        "notas_adicionales": "Circular N° 04/2026 (procedimiento para publicar gestiones de contrataciones): https://compras.santafe.gob.ar/wp-content/uploads/sites/87/2026/05/CIRCULAR-004-26.pdf",
        "categoria_libre": "Publicación en el portal de compras",
        "verificado": True,
    },
    {
        "slug": "no-aparece-pestana-comenzar-carga-sin",
        "situacion": 'Quiero cargar un acto en el SIN para el Tribunal de Cuentas, pero no aparece la pestaña "comenzar una carga"',
        "descripcion": "Al entrar al sistema SIN para iniciar la carga que corre vista al Tribunal de Cuentas, no se encuentra la opción esperada.",
        "causa": "No hay una causa confirmada todavía en el material disponible.",
        "solucion": 'No verificado todavía: se compartió un instructivo ("Carga y Edición SIN.pdf") y un link a la normativa, pero no coincidían exactamente con lo que hacía falta resolver. Si te pasa esto, consultá directamente con tu referente de Contrataciones.',
        "categoria_libre": "Sistema SIN y Tribunal de Cuentas",
        "verificado": False,
    },
    {
        "slug": "no-abre-link-sin",
        "situacion": "No nos abre el link del sistema SIN",
        "descripcion": "Al hacer clic en el link de acceso al SIN, la página no carga.",
        "causa": "El acceso al SIN es exclusivo de los usuarios habilitados específicamente, y además requiere entrar desde una computadora conectada a la red institucional — no funciona desde cualquier dispositivo o red.",
        "solucion": "Confirmá que tu usuario esté habilitado para el SIN y que estés conectado desde una computadora de la red del hospital (no desde una red externa o un celular).",
        "categoria_libre": "Sistema SIN y Tribunal de Cuentas",
        "verificado": True,
        "tutorial": ("actos-administrativos", "protocolizar-y-publicar"),
    },
    {
        "slug": "alta-usuarios-sin",
        "situacion": "¿Cómo damos de alta a más usuarios para cargar en el SIN, en vez de depender siempre de los mismos?",
        "descripcion": "Pocas personas están habilitadas para cargar en el SIN y hace falta sumar más usuarios.",
        "solucion": (
            "Hay que completar una planilla con los datos de los usuarios responsables de la carga de actos administrativos "
            "(indicando si alguno no tiene correo oficial) y enviarla al área de Contrataciones y Gestión de Bienes / "
            "Secretaría de Tecnologías para la Gestión. Con esa información se genera un ticket interno para crear los usuarios en el SIN."
        ),
        "notas_adicionales": "El trámite puede demorar varios días. Mientras se gestiona el alta, conviene seguir usando los usuarios ya habilitados para no perder el plazo de la vista al Tribunal de Cuentas.",
        "categoria_libre": "Sistema SIN y Tribunal de Cuentas",
        "verificado": True,
        "tutorial": ("actos-administrativos", "protocolizar-y-publicar"),
    },
    {
        "slug": "timbo-compras-caido-por-sipaf",
        "situacion": "No puedo cargar artículos en Timbó Compras",
        "descripcion": "El módulo de Compras no deja cargar artículos nuevos.",
        "causa": "Puede deberse a una caída del sistema SIPAF, un sistema provincial del que depende indirectamente el módulo de Compras — no es necesariamente un problema de tu usuario ni de tu configuración.",
        "solucion": "Antes de pedir soporte, confirmá con tu referente si hay un aviso de caída de SIPAF. En ese caso no hay nada para resolver del lado del usuario: hay que esperar a que se restablezca el servicio.",
        "categoria_libre": "Disponibilidad del sistema",
        "verificado": True,
    },
]

SITUACIONES_TIMBO_COMPRAS = [
    {
        "slug": "decisorio-preventivo-vs-definitivo",
        "situacion": "¿Qué decisorio corresponde: preventivo o definitivo, y qué hay que vincular en Timbó Compras?",
        "descripcion": "No queda claro cuándo usar el decisorio preventivo y cuándo el definitivo, ni qué hay que vincular en Timbó Compras.",
        "causa": "El circuito de aprobación de compras pasa dos veces por un decisorio: uno antes de la intervención del Tribunal de Cuentas y otro después.",
        "solucion": (
            "Antes del Tribunal de Cuentas va el preventivo (con la afectación), junto con el pliego, el expediente, el pedido y las notas. "
            "En Timbó Compras se vincula el Documento Oficial que aprueba el pliego para pasar a la etapa siguiente. "
            "Después de la vista, se sube el decisorio definitivo al expediente y a Timbó Compras."
        ),
        "categoria_libre": "Decisorios y Tribunal de Cuentas",
        "verificado": True,
        "tutorial": ("gestion-interna", "circuito-decisorio"),
    },
    {
        "slug": "quien-corre-vista-tcp",
        "situacion": "¿La vista al Tribunal de Cuentas la corremos desde Compras o la hace Mesa de Entradas?",
        "descripcion": "No está claro qué área tiene que correr la vista del expediente.",
        "solucion": "Lo decide cada hospital: puede hacerlo Compras o Mesa de Entradas.",
        "categoria_libre": "Decisorios y Tribunal de Cuentas",
        "verificado": True,
        "tutorial": ("gestion-interna", "vista-tribunal-de-cuentas"),
    },
    {
        "slug": "no-aparece-pestana-comenzar-carga-sin",
        "situacion": 'Quiero cargar un acto en el SIN para el Tribunal de Cuentas, pero no aparece la pestaña "comenzar una carga"',
        "descripcion": "Al entrar al sistema SIN para iniciar la carga que corre vista al Tribunal de Cuentas, no se encuentra la opción esperada.",
        "causa": "Lo más probable es que el usuario no esté habilitado para cargar en el SIN (la opción solo la ven los usuarios habilitados).",
        "solucion": "Confirmá que tu usuario esté habilitado para el SIN y que entres desde una computadora de la red institucional. Si igual no aparece, consultá con tu referente de Contrataciones.",
        "notas_adicionales": 'Sin confirmar: en el chat se compartió el instructivo "Carga y Edición SIN" y el link app.santafe.gov.ar/normativa, pero la pantalla no coincidía con el instructivo y no quedó resuelto.',
        "categoria_libre": "Sistema SIN",
        "verificado": False,
        "tutorial": ("gestion-interna", "vista-tribunal-de-cuentas"),
    },
    {
        "slug": "no-abre-link-sin",
        "situacion": "No nos abre el link del sistema SIN",
        "descripcion": "Al hacer clic en el link de acceso al SIN, la página no carga.",
        "causa": "El SIN solo funciona para usuarios habilitados y desde una computadora conectada a la red institucional.",
        "solucion": "Confirmá que tu usuario esté habilitado y que estés en una computadora de la red del hospital (no desde el celular ni desde otra red).",
        "categoria_libre": "Sistema SIN",
        "verificado": True,
        "tutorial": ("gestion-interna", "vista-tribunal-de-cuentas"),
    },
    {
        "slug": "alta-usuarios-sin",
        "situacion": "¿Cómo damos de alta a más usuarios para cargar en el SIN?",
        "descripcion": "Pocas personas están habilitadas para cargar en el SIN y hace falta sumar más usuarios.",
        "solucion": (
            "Completá la planilla de datos con las personas que van a cargar actos administrativos (indicá si alguien no tiene correo oficial) "
            "y enviala por correo a la Subsecretaría de Contrataciones y Gestión de Bienes. Ellos piden el alta por iTop a la STG."
        ),
        "notas_adicionales": "Tarda varios días. Mientras tanto, usá los usuarios ya habilitados para no perder el plazo de la vista al Tribunal de Cuentas.",
        "categoria_libre": "Sistema SIN",
        "verificado": True,
        "tutorial": ("gestion-interna", "alta-usuarios-sin"),
    },
    {
        "slug": "link-publicacion-portal-compras",
        "situacion": "¿Dónde consigo el link para publicar la gestión en el portal de compras?",
        "descripcion": "Ya cargaste la nómina de oferentes y la fecha de publicación, y no sabés qué link poner en el portal.",
        "solucion": (
            "No hay que copiar ningún link a mano. En el portal web, pestaña \"Expedientes\", cargá el número de expediente de Timbó "
            "y marcá \"Marcar para que se genere enlace con TIMBO\" y \"expediente principal\": así se genera el botón OFERTAR. "
            "En \"Lugar de presentación de las ofertas\" va la leyenda con https://gestionvirtual.santafe.gob.ar."
        ),
        "notas_adicionales": (
            "Además se pide el aviso oficial por mail a avisosoficiales@santafe.gob.ar con 3 días de anticipación. "
            "Circular N° 04/2026: https://compras.santafe.gob.ar/wp-content/uploads/sites/87/2026/05/CIRCULAR-004-26.pdf"
        ),
        "categoria_libre": "Publicación en el portal",
        "verificado": True,
        "tutorial": ("gestion-interna", "publicar-en-portal"),
    },
    {
        "slug": "timbo-compras-caido-por-sipaf",
        "situacion": "No puedo cargar artículos en Timbó Compras",
        "descripcion": "El módulo de Compras no deja cargar artículos nuevos.",
        "causa": "Suele ser una caída de SIPAF, el sistema provincial del que depende el nomenclador de artículos. No es un problema de tu usuario.",
        "solucion": "Preguntá a tu referente si hay aviso de caída de SIPAF. Si la hay, solo queda esperar a que vuelva el servicio.",
        "categoria_libre": "Artículos y disponibilidad",
        "verificado": True,
    },
    {
        "slug": "articulo-no-esta-en-nomenclador",
        "situacion": "El artículo que necesito no aparece en el nomenclador",
        "descripcion": "Buscás un artículo para el pedido y no lo encontrás.",
        "solucion": (
            "Primero buscalo en el catálogo web con palabras clave y sinónimos. Si no está, pedí el alta con el Documento Oficial "
            "\"Timbó Compras: Alta de bienes y servicios CAByS\" (Res. SCyGB 292/2026)."
        ),
        "notas_adicionales": 'También existen las guías "Búsqueda Nomenclador SIPAF y Solicitud de Artículos Faltantes" y "Guía en cuatro pasos para solicitar artículos".',
        "categoria_libre": "Artículos y disponibilidad",
        "verificado": True,
        "tutorial": ("gestion-interna", "pedir-alta-articulo"),
    },
    {
        "slug": "documentos-salen-en-html",
        "situacion": "Los documentos de Timbó Compras salen en HTML y hay que pasarlos a PDF",
        "descripcion": "Para subirlos a otro lado hay que convertirlos, con varios pasos extra.",
        "solucion": "Por ahora no hay otra opción: hay que convertirlos. Se pidió a Sistemas que el módulo los genere directamente en PDF.",
        "notas_adicionales": "Pedido abierto, sin respuesta todavía.",
        "categoria_libre": "Artículos y disponibilidad",
        "verificado": False,
    },
]


def _tutorial_id(tema, clave):
    if not clave:
        return None
    categoria_slug, tutorial_slug = clave
    categoria = Categoria.query.filter_by(tema_id=tema.id, slug=categoria_slug).first()
    if not categoria:
        return None
    tutorial = Tutorial.query.filter_by(categoria_id=categoria.id, slug=tutorial_slug).first()
    return tutorial.id if tutorial else None


def _cargar_situaciones(tema_slug, situaciones_datos):
    tema = Tema.query.filter_by(slug=tema_slug).first()
    if not tema:
        print(f"⚠️  Tema '{tema_slug}' no existe todavía — importalo antes de correr este script.")
        return 0

    siguiente_orden = max([s.orden for s in tema.situaciones], default=-1) + 1
    cargadas = 0
    for datos in situaciones_datos:
        existente = Situacion.query.filter_by(tema_id=tema.id, slug=datos["slug"]).first()
        if existente:
            db.session.delete(existente)
            db.session.flush()

        situacion = Situacion(
            tema_id=tema.id,
            slug=datos["slug"],
            situacion=datos["situacion"],
            descripcion=datos.get("descripcion"),
            causa=datos.get("causa"),
            solucion=datos.get("solucion"),
            notas_adicionales=datos.get("notas_adicionales"),
            categoria_libre=datos.get("categoria_libre"),
            tutorial_id=_tutorial_id(tema, datos.get("tutorial")),
            verificado=datos.get("verificado", True),
            orden=siguiente_orden,
        )
        db.session.add(situacion)
        siguiente_orden += 1
        cargadas += 1

    db.session.commit()
    return cargadas


def importar():
    n1 = _cargar_situaciones("mihospital", SITUACIONES_MIHOSPITAL)
    n2 = _cargar_situaciones("timbo-expedientes", SITUACIONES_TIMBO_EXPEDIENTES)
    n3 = _cargar_situaciones("timbo-compras", SITUACIONES_TIMBO_COMPRAS)
    print(f"Cargadas {n1} situaciones en miHospital, {n2} en TIMBÓ (Expedientes) y {n3} en TIMBÓ Compras.")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        importar()
