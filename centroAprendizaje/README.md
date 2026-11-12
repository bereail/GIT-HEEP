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
   `timboDocumentacion/FAQ_SOPORTE_TIMBO.md` y bloque de tutorial de tipo
   video.
5. Cuarto tema (categoría), **Licitaciones y Compras** dentro de TIMBÓ
   (Expedientes): circuito interno completo, desde iniciar la contratación
   hasta preadjudicar, con capturas reales del sistema.
6. Consultas/dudas con estado (tipo mensajería, con feedback).
7. Estadísticas de uso.
8. Buscador global cruzando todos los temas.
9. Sistema de migraciones (Alembic).

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
├── importar_timbo_expedientes.py   # JSON → base de datos (reutilizable, orden_tema configurable)
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

Las migraciones de esquema se manejan con **Flask-Migrate / Alembic**
(carpeta `migrations/`): para un cambio de modelo, `flask db migrate -m "..."`
y `flask db upgrade` — ya no se usa `db.create_all()` ni hace falta borrar la
base para aplicar un cambio de columnas.

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

## Deploy en un VPS Linux

`python run.py` es solo para desarrollo local (corre con `debug=True`, sin
TLS ni supervisión). En el servidor real se usa **gunicorn** detrás de
**nginx**, supervisado por **systemd**. Los archivos de referencia están en
`deploy/`:

```
deploy/
├── .env.example                      # variables de entorno (copiar como .env, con valores propios)
├── centro-aprendizaje.service        # unidad de systemd (gunicorn)
└── nginx-centro-aprendizaje.conf     # sitio de nginx (proxy + estáticos)
```

Pasos (asumiendo que el repo se clona en `/opt/centro-aprendizaje`):

```bash
# 1. Usuario de sistema dedicado (no root)
sudo useradd --system --home /opt/centro-aprendizaje --shell /usr/sbin/nologin centroaprendizaje

# 2. Entorno virtual y dependencias
cd /opt/centro-aprendizaje/centroAprendizaje
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 3. Variables de entorno propias (nunca committear este archivo)
cp deploy/.env.example .env
python3 -c "import secrets; print(secrets.token_hex(32))"   # pegar como SECRET_KEY en .env
# completar también ADMIN_PASSWORD en .env

# 4. Base de datos: migraciones + contenido inicial
#
# OJO: la migración baseline (migrations/versions/*_baseline_*.py) tiene
# upgrade() vacío a propósito — asume que el esquema ya existe, porque se
# creó para "sellar" una base de desarrollo que ya tenía las tablas de
# antes de sumar Alembic. En un servidor NUEVO con una base vacía, `flask
# db upgrade` no crea ninguna tabla. Para una base nueva, primero:
export FLASK_APP=run.py
.venv/bin/python -c "
from app import create_app
from app.extensions import db
app = create_app()
with app.app_context():
    db.create_all()
"
.venv/bin/flask db stamp head
# A partir de acá sí, `flask db upgrade` funciona para migraciones futuras.
.venv/bin/python scripts/importar_mihospital.py
.venv/bin/python scripts/importar_timbo_expedientes.py
.venv/bin/python scripts/importar_timbo_compras.py
.venv/bin/python scripts/importar_faq_chats.py

# 5. Permisos (el usuario de systemd necesita escribir instance/)
sudo chown -R centroaprendizaje:centroaprendizaje /opt/centro-aprendizaje

# 6. Servicio systemd
sudo cp deploy/centro-aprendizaje.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now centro-aprendizaje
sudo systemctl status centro-aprendizaje   # debería decir "active (running)"

# 7. nginx (editar server_name antes de copiarlo)
sudo cp deploy/nginx-centro-aprendizaje.conf /etc/nginx/sites-available/centro-aprendizaje
sudo ln -s /etc/nginx/sites-available/centro-aprendizaje /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 8. (opcional) HTTPS, una vez que el sitio ya responde por HTTP
sudo certbot --nginx -d tu-dominio.gob.ar
```

**Para actualizar** una vez deployado (nuevo contenido o código):

```bash
cd /opt/centro-aprendizaje
git pull
cd centroAprendizaje
.venv/bin/pip install -r requirements.txt   # solo si cambiaron dependencias
.venv/bin/flask db upgrade                  # solo si hay migraciones nuevas (base ya existente)
sudo systemctl restart centro-aprendizaje
```

La base (`instance/centro_aprendizaje.sqlite3`) vive solo en el servidor y
no está en git — conviene respaldarla periódicamente (por ejemplo, copiando
el archivo a otro lado con un cron). Si en algún momento crece el tráfico o
hace falta escribir desde varios procesos a la vez, migrar de SQLite a
PostgreSQL es solo cambiar `SQLALCHEMY_DATABASE_URI` gracias a SQLAlchemy —
no hace falta hoy para este volumen de uso.

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

1. Pulido final de UI/UX.
2. Revisar 3 videos de TIMBÓ Compras que YouTube no dejó procesar
   automáticamente y completar ese tutorial a mano (detalle en
   `timboDocumentacion/FAQ_SOPORTE_TIMBO.md`).
3. Resolver las consultas que quedaron abiertas en los chats de soporte
   (SIN sin "comenzar una carga", numeración de decisorios, documentos
   HTML→PDF) y pasar esas situaciones a `verificado: True` en
   `scripts/importar_faq_chats.py` cuando haya respuesta.
4. Conseguir y cargar las guías PDF de artículos / nomenclador SIPAF que
   se compartieron en el chat de soporte pero todavía no están en el portal.
