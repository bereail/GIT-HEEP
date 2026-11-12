# Centro de Aprendizaje — memoria del proyecto

Contexto para retomar el trabajo desde cualquier PC. El detalle técnico está
en `README.md`; acá va lo que no se deduce del código.

## Qué es

Portal de capacitación y soporte interno para hospitales de Santa Fe.
Es multi-tema, y hoy tiene tres temas: **miHospital**, **TIMBÓ (Expedientes)**
(con la categoría interna **Licitaciones y Compras**) y **TIMBÓ Compras**
(lado proveedor/oferente). Flask + SQLAlchemy + SQLite (con migraciones
Alembic), y chatbot + buscador global 100% locales por palabras clave
(`app/services/buscador.py`), sin IA externa.

## Cómo levantarlo en una PC nueva

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts/importar_mihospital.py
python scripts/importar_timbo_expedientes.py
python scripts/importar_timbo_compras.py
python scripts/importar_faq_chats.py   # siempre al final
python run.py                          # http://127.0.0.1:5000
```

La base (`instance/*.sqlite3`) no está en git: se recrea con los scripts.
Para cambios de esquema se usa Flask-Migrate (`flask db migrate` / `flask db upgrade`),
no hace falta borrar la base para eso.

## Criterios de la usuaria (respetarlos siempre)

- El chatbot y los tutoriales tienen que ser **muy prácticos, intuitivos y
  fáciles**: completos pero sin saturar. Van respuestas cortas, y lo extra se
  pone en "Ver más" o en botones para tocar, no en párrafos largos.
- Escribir en español rioplatense (voseo), con lenguaje simple.
- **Nunca** cargar datos personales de los chats de soporte (nombres,
  teléfonos, correos, CUIL). Los exports de WhatsApp en
  `timboDocumentacion/historialWp/` están en `.gitignore` por eso: no se
  suben. Si hacen falta en otra PC, se copian a mano.
- Las respuestas que no quedaron confirmadas van con `verificado: False`
  (el chatbot les muestra un aviso "sin confirmar").
- Antes de subir una captura de pantalla real al repo, revisar que no
  tenga de fondo contenido ajeno al tutorial (otras ventanas, videollamadas,
  nombres de personas, otras sesiones) — recortarla si hace falta.

## Dos líneas de trabajo en paralelo (2026-11-12)

Este proyecto se trabajó un tiempo desde dos PCs distintas, con historias de
git completamente separadas (sin commits en común) y hasta una estructura de
carpetas distinta (todo bajo `centroAprendizaje/` acá vs. en la raíz del repo
en la otra). Se reconciliaron a mano el 2026-11-12, usando esta carpeta como
base: se portó el tema **TIMBÓ Compras** completo (contenido, importador
genérico `importar_timbo_expedientes.importar(ruta_json, orden_tema)`,
situaciones de FAQ y el bloque de tutorial `{"type": "video", ...}`) desde la
otra línea de trabajo, sin tocar el contenido ya verificado de esta. Si
aparece de nuevo una divergencia de git sin commits en común, es probable que
sea por lo mismo: confirmá en qué PC se trabajó antes de asumir que es un
error.

## Estado (2026-11-12)

Hecho:
- Los 3 temas completos (miHospital, TIMBÓ Expedientes con Licitaciones y
  Compras, TIMBÓ Compras).
- Consultas con estado, estadísticas de uso, buscador global, migraciones
  con Alembic.
- Relevamiento de preguntas frecuentes de los chats de soporte:
  `timboDocumentacion/FAQ_SOPORTE_TIMBO.md`.

Pendiente (ver también la sección 3 de FAQ_SOPORTE_TIMBO.md y el README):
1. Ver a mano 3 videos que YouTube no dejó procesar y completar el
   tutorial: Yp3TIlDxpms (49 min), JJExl9hnYbo (35 min) y tSYfZ3yVE58
   (documento embebido). También Wb4ZRvB3YSo (registro de proveedor, sin
   subtítulos).
   Lista: https://www.youtube.com/playlist?list=PLJKcMr5XTsSc5jJV-Uszw7OXCzG3LwG76
2. Consultas abiertas en los chats: SIN sin "comenzar una carga",
   numeración de decisorios, documentos HTML→PDF y servidor propio para
   los videos. Cuando haya respuesta, pasar a `verificado: True` en
   `scripts/importar_faq_chats.py`.
3. Conseguir y cargar las guías PDF de artículos o nomenclador SIPAF.
4. Pulido final de UI/UX.
