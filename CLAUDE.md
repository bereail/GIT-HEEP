# Centro de Aprendizaje — memoria del proyecto

Contexto para retomar el trabajo desde cualquier PC. El detalle técnico está
en `README.md`; acá va lo que no se deduce del código.

## Qué es

Portal de capacitación y soporte interno para hospitales de Santa Fe.
Es multi-tema, y hoy tiene tres temas: **miHospital**, **TIMBÓ (Expedientes)** y
**TIMBÓ Compras**. Flask + SQLite, sin build step, y chatbot 100% local por
palabras clave (`app/services/buscador.py`), sin IA externa.

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

## Estado (2026-11-11)

Hecho:
- Tema TIMBÓ Compras (`scripts/content_timbo_compras.json`), con 3
  módulos y 10 lecciones. El lado proveedor sale de la lista de videos
  oficial. La gestión interna del hospital (decisorios, Tribunal de Cuentas,
  SIN, publicación) sale de los chats.
- Relevamiento de preguntas frecuentes de los chats:
  `timboDocumentacion/FAQ_SOPORTE_TIMBO.md`.
- Chatbot con sugerencias para tocar, "¿Te referís a...?", preguntas
  relacionadas, "¿Te sirvió?", reinicio y aviso de "sin confirmar".
- Bloque de tutorial nuevo `{"type": "video", "url", "title", "minutos"}`.

Pendiente (ver también la sección 3 de FAQ_SOPORTE_TIMBO.md):
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
4. `app/ui/routes.py` tiene rutas de "consultas" que usan los templates
   `consulta_nueva.html` y `consulta_ver.html`, y esos templates todavía no
   existen. Por eso el chatbot, cuando algo no sirve, manda a "Tengo un
   problema" y no a "dejar consulta".
5. Siguientes etapas del README: estadísticas, buscador global y Alembic.
