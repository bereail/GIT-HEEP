# Centro de Aprendizaje

Portal centralizado de capacitaciones y soporte interno. Permite agregar
varios **temas** (sistemas o herramientas distintas) sin reescribir código:
cada tema es un conjunto de filas en la base de datos (módulos, tutoriales,
glosario, preguntas frecuentes), cargables desde un panel de administración.

Etapas completadas:
1. Base multi-tema + tema **miHospital** migrado.
2. Panel de administración.
3. Segundo tema, **TIMBÓ (Expedientes)**, cargado de punta a punta (valida
   que el modelo multi-tema funciona con contenido real) + sección "Tengo un
   problema" ampliada con dudas reales de soporte, agrupadas por categoría.
4. Tercer tema, **TIMBÓ Compras** (lado proveedor desde la lista oficial de
   videos + circuito interno de Compras desde los chats de soporte),
   relevamiento de preguntas frecuentes en
   `timboDocumentacion/FAQ_SOPORTE_TIMBO.md` y chatbot más guiado
   (sugerencias para tocar, "¿Te referís a...?", preguntas relacionadas,
   aviso en respuestas sin confirmar y "¿Te sirvió?").

Lo que falta queda listado al final.

## Arquitectura

- **Backend:** Python + Flask + SQLAlchemy + SQLite (pensado para migrar a
  PostgreSQL en producción, según las convenciones del proyecto).
- **Frontend:** HTML server-rendered (Jinja2) + JavaScript vanilla sin build
  step, reutilizando 1:1 el sistema de diseño ya probado en
  `timbo-capacitacion/assets/css/styles.css`.
- **Chatbot y buscador:** 100% locales (sin IA externa, sin costo) — buscan
  por palabras clave sobre el contenido del tema actual, cargado desde la
  base de datos. Es el mismo algoritmo que ya tenía `timbo-capacitacion`,
  portado a Python en `app/services/buscador.py`. El endpoint del chatbot
  está exento de CSRF (como el de vista previa del admin) porque no muta
  ningún dato — si alguna vez pasa a escribir algo, hay que sacarle esa
  excepción.
- **Progreso del usuario:** en `localStorage` del navegador, sin cuentas ni
  login (igual que antes).
- **Panel de administración:** en `/admin`, protegido con una contraseña
  compartida (no es un sistema de usuarios/roles — alcanza para esta etapa,
  una sola persona cargando contenido). CSRF protegido con Flask-WTF.
- **"Tengo un problema" / FAQ:** el modelo `Situacion` cubre pregunta →
  causa → solución → verificado, y ahora además `categoria_libre` (para
  agrupar visualmente sin forzar un tutorial) y `notas_adicionales` (para
  aclaraciones extra, como recomendaciones de cuándo usar cada alternativa
  si hay más de una solución posible).

```
app/
├── models/       # Tema, Categoria, Tutorial, EntradaGlosario, Situacion, Tarea, PasoIntroductorio
├── services/      # buscador.py (búsqueda + chatbot), textutil.py (slugify)
├── ui/            # rutas públicas del portal
├── admin/         # panel de administración (auth.py, routes.py)
├── templates/     # Jinja2 (admin/ aparte del público)
└── static/        # css/js/img (img/<tema_slug>/ por tema)
scripts/
├── exportar_content_js.mjs         # content.js (JS) → JSON (miHospital)
├── importar_mihospital.py          # JSON → base de datos (tema completo)
├── content_timbo_expedientes.json  # contenido ya extraído de las guías HTML
├── importar_timbo_expedientes.py   # JSON → base de datos (tema completo)
├── content_timbo_compras.json      # tema TIMBÓ Compras (videos + chats)
├── importar_timbo_compras.py       # JSON → base de datos (reusa el de expedientes)
└── importar_faq_chats.py           # situaciones de soporte reales → Situacion
```

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

## Cargar el contenido

La primera vez (o para resetear un tema completo a su contenido de origen):

```bash
node scripts/exportar_content_js.mjs > scripts/content_mihospital.json
python scripts/importar_mihospital.py
python scripts/importar_timbo_expedientes.py
python scripts/importar_timbo_compras.py
python scripts/importar_faq_chats.py      # siempre al final: completa los tres temas
```

`importar_mihospital.py` e `importar_timbo_expedientes.py` son
**idempotentes a nivel de tema**: si el tema ya existe, lo borran completo y
lo recrean desde el JSON — también se pierde lo editado a mano desde el
admin para ese tema, así que son para una carga inicial o un reset
intencional, no para correr en cada deploy. `importar_faq_chats.py` es
idempotente a nivel de cada situación (por slug) y no toca el resto del
contenido del tema.

Si le agregás columnas nuevas a algún modelo (como pasó con `Situacion` en
la Etapa 3), `db.create_all()` no altera tablas ya creadas — hay que borrar
`instance/centro_aprendizaje.sqlite3` y volver a correr los scripts de
importación. No hay un sistema de migraciones todavía (Alembic) porque el
esquema no está estabilizado; conviene sumarlo antes de tener datos de
producción que no se puedan recrear desde cero.

## Correr el servidor

```bash
python run.py
```

Sitio público: `http://127.0.0.1:5000/`.
Panel de administración: `http://127.0.0.1:5000/admin` — contraseña por
defecto en desarrollo: `admin123` (variable de entorno `ADMIN_PASSWORD`).

**Antes de desplegar en un servidor real**, definir las variables de
entorno `SECRET_KEY` y `ADMIN_PASSWORD` con valores propios — los que trae
el código son solo para desarrollo local.

## Agregar un tema nuevo

Desde el panel (`/admin` → "+ Nuevo tema") se crea el tema y, desde ahí, sus
módulos, tutoriales, glosario, situaciones ("Tengo un problema") y tareas
("Quiero hacer..."). No hace falta tocar código ni la base de datos a mano.

El cuerpo de un tutorial (bloques de texto/pasos/tips/capturas y las
preguntas del quiz) se edita como JSON en el formulario del tutorial, con
una vista previa en vivo al lado que se renderiza igual que el sitio
público — el editor de admin explica ahí mismo (desplegable "Ver tipos de
bloque...") la forma exacta de cada tipo. Las imágenes se suben aparte, por
tema, desde "🖼 Imágenes" en la página del tema.

Para cargar contenido real desde material externo (guías, chats de
soporte, etc.) que no viene ya estructurado: conviene extraerlo primero a
un JSON con el mismo schema que usan los scripts de `scripts/`, revisarlo
antes de importar, y recién después correr el import — así queda un
registro de qué se cargó y de dónde salió, en vez de tipearlo a mano en el
admin uno por uno. **Nunca** incluir datos personales del material fuente
(nombres, teléfonos, mails, CUIL) en el contenido que termina en la base.

## Qué falta (próximas etapas)

1. Consultas/dudas con estado (tipo mensajería) — para preguntas que no
   tienen todavía una situación cargada en "Tengo un problema".
2. Estadísticas de uso.
3. Buscador global cruzando todos los temas + pulido final de UI/UX.
4. Sistema de migraciones (Alembic) antes de tener datos de producción.
