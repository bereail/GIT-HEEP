"""Carga las situaciones de "Tengo un problema" extraídas de dos chats reales
de soporte (grupos de WhatsApp de Sectorial/Contrataciones), repartidas
entre los temas mihospital, timbo-expedientes y timbo-compras. El detalle
de qué salió de cada chat (y qué quedó sin resolver) está en
`timboDocumentacion/FAQ_SOPORTE_TIMBO.md`.

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
        "solucion": (
            '1) Terminá y aprobá el curso "TIMBÓ paso a paso". '
            "2) Avisá que lo aprobaste: tu referente lo pide por iTop con Apellido y nombres, CUIL y los permisos solicitados. "
            '3) Te matriculan en el curso de "Administrador Local" y te llega un mail. '
            "4) Al terminar ese curso, mandá un mail a la casilla de TIMBÓ Salud para que quede registrado."
        ),
        "notas_adicionales": "Los tiempos de matriculación dependen de la oficina de Capacitación, no del área de soporte técnico — si tarda unos días, no es un error, es la demora habitual del circuito administrativo.",
        "categoria_libre": "Accesos y permisos",
        "verificado": True,
        "tutorial": ("primeros-pasos", "roles-y-permisos"),
    },
    {
        "slug": "vencio-periodo-inscripcion-adm-local",
        "situacion": 'Me dice "Ya no puede matricularse, el período finalizó" en el curso de Administrador Local',
        "descripcion": "Intentás inscribirte al curso de Administrador Local y el aula virtual no te deja.",
        "causa": 'Al curso de Administrador Local no se inscribe uno mismo: te matriculan después de aprobar "TIMBÓ paso a paso".',
        "solucion": 'Primero terminá y aprobá "TIMBÓ paso a paso" y avisale a tu referente. Cuando te matriculen te llega un mail; recién ahí vas a poder entrar al curso.',
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
        "notas_adicionales": (
            "El perfil 3 hay que pedirlo por cada usuario y es temporal; descargar y compartir en red local es más trabajo una sola vez, pero después queda disponible para todos. "
            "Lista de videos de TIMBÓ Compras: https://www.youtube.com/playlist?list=PLJKcMr5XTsSe33vph6nNpxnZpu8D3RsBE — "
            "Pendiente: se propuso alojar los videos en un servidor propio; quedó para plantearlo a Formación Laboral, sin respuesta todavía."
        ),
        "categoria_libre": "Capacitación y videos",
        "verificado": True,
    },
]

SITUACIONES_TIMBO_EXPEDIENTES = [
    {
        "slug": "numeracion-fecha-documento-oficial",
        "situacion": "Firmé un documento oficial (decisorio) y no tiene número ni fecha — ¿hay que agregarlo?",
        "descripcion": "Después de firmar un decisorio, el documento no muestra numeración ni fecha.",
        "causa": "TIMBÓ le pone número y fecha recién cuando firma la última persona de la cadena de firmas.",
        "solucion": (
            "No lo edites: si se toca un documento firmado, se rompe la firma. "
            "Si todavía no tiene número, falta alguna firma: cuando firme el último, se numera y se fecha solo."
        ),
        "notas_adicionales": "En algunos hospitales el decisorio lleva además una numeración propia de Secretaría de Dirección. En el chat de soporte no quedó confirmado cómo se combinan las dos: consultalo con tu referente.",
        "categoria_libre": "Documentos oficiales y decisorios",
        "verificado": True,
        "tutorial": ("documentos-oficiales", "crear-documento-oficial"),
    },
    {
        "slug": "archivar-o-desestimar-documento-oficial",
        "situacion": "¿Cómo se archiva o desestima un documento oficial que no sirve?",
        "descripcion": "Se generó un documento oficial que no se va a usar y se busca cómo descartarlo.",
        "solucion": "No hace falta archivarlo ni desestimarlo: una vez firmado por todos queda creado tal cual. Si no sirve, simplemente no lo uses ni lo vincules.",
        "categoria_libre": "Documentos oficiales y decisorios",
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
        "situacion": 'Quiero cargar algo en el SIN para dar vista al Tribunal de Cuentas, pero no aparece la pestaña "comenzar una carga"',
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
        "solucion": "Es el mismo link que lleva a la gestión en Timbó. La publicación se hace por Timbó, por correo electrónico y con la carga en el SIN (Circular N° 04/2026).",
        "notas_adicionales": "Circular N° 04/2026: https://compras.santafe.gob.ar/wp-content/uploads/sites/87/2026/05/CIRCULAR-004-26.pdf",
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
        "solucion": 'Hay una guía oficial para buscar en el nomenclador SIPAF y pedir los artículos que faltan ("Guía de Uso – Búsqueda Nomenclador SIPAF y Solicitud de Artículos Faltantes"), y otra con los 4 pasos para solicitar artículos. Pedíselas a tu referente.',
        "notas_adicionales": "Las guías se compartieron como PDF en el grupo de soporte; todavía no están cargadas en este portal.",
        "categoria_libre": "Artículos y disponibilidad",
        "verificado": True,
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

# Situaciones que antes vivían en timbo-expedientes y ahora pertenecen a
# timbo-compras: se borran del tema viejo para que no queden duplicadas.
MOVIDAS_DE_EXPEDIENTES = [s["slug"] for s in SITUACIONES_TIMBO_COMPRAS]


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


def _borrar_situaciones(tema_slug, slugs):
    tema = Tema.query.filter_by(slug=tema_slug).first()
    if not tema:
        return
    Situacion.query.filter(Situacion.tema_id == tema.id, Situacion.slug.in_(slugs)).delete(synchronize_session=False)
    db.session.commit()


def importar():
    _borrar_situaciones("timbo-expedientes", MOVIDAS_DE_EXPEDIENTES)
    n1 = _cargar_situaciones("mihospital", SITUACIONES_MIHOSPITAL)
    n2 = _cargar_situaciones("timbo-expedientes", SITUACIONES_TIMBO_EXPEDIENTES)
    n3 = _cargar_situaciones("timbo-compras", SITUACIONES_TIMBO_COMPRAS)
    print(f"Cargadas {n1} situaciones en miHospital, {n2} en TIMBÓ (Expedientes) y {n3} en TIMBÓ Compras.")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        importar()
