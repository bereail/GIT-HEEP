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

## Estado (2026-11-13)

Hecho:
- Tema TIMBÓ Compras (`scripts/content_timbo_compras.json`), con 3
  módulos y 18 lecciones. El lado proveedor sale de la lista de videos
  oficial. La gestión interna del hospital (decisorios, Tribunal de Cuentas,
  SIN, publicación) sale de los chats.
- Relevamiento de preguntas frecuentes de los chats:
  `timboDocumentacion/FAQ_SOPORTE_TIMBO.md`.
- Chatbot con sugerencias para tocar, "¿Te referís a...?", preguntas
  relacionadas, "¿Te sirvió?", reinicio y aviso de "sin confirmar".
- Bloque de tutorial nuevo `{"type": "video", "url", "title", "minutos"}`.
- Lección "Hacer una compra, paso a paso" (Gestión interna): el circuito
  completo del hospital en 10 pasos. Los nombres exactos de los botones del
  lado del hospital NO están relevados (la lección lo avisa): confirmarlos
  con una persona de Compras y ajustar.
- Buscador: "quiero", "necesito", "tengo", etc. son palabras vacías, para
  que no le ganen a la palabra importante de la pregunta.
- "Dejar una consulta": formulario público sin usuario (se sigue por un
  link con token), bandeja en /admin/consultas para responder y cerrar, y
  el "No me sirvió" del chatbot lleva ahí con la pregunta precargada.
- Revisión contra fuentes oficiales (sección 5 de FAQ_SOPORTE_TIMBO.md):
  publicación según Circular 04/2026, vista al TCP con "Gestión de
  Visualización" + SIN (Circ. UG 9 y 11/2026), control de la URC (Circ.
  03/2026), lección nueva de alta de artículos CAByS (Res. 292/2026) y RUPC
  como requisito del proveedor. **Si un chat contradice una circular, manda
  la circular.**
- Lecciones por rol del hospital (Gestor, Supervisor, Evaluador) y de
  notificación a proveedores, armadas con los subtítulos de la lista oficial
  "APP-TimboCompras" (sección 4.1 de FAQ_SOPORTE_TIMBO.md, que también explica
  cómo bajar subtítulos cuando YouTube bloquea la descarga).
- Chatbot: muestra los pasos plegados, tolera errores de tipeo y sinónimos,
  manda al tema correcto si la pregunta es de otro sistema, y guarda lo que no
  supo responder (y los 👎) en /admin/chatbot.
- El tema miHospital se llamaba "TIMBÓ" en su JSON: corregido.
- Al reimportar un tema, las consultas y las preguntas del chatbot pasan al
  tema nuevo (`app/services/importacion.py`).

Pendiente (ver también la sección 3 de FAQ_SOPORTE_TIMBO.md):
1. Leer a fondo las capacitaciones largas (Yp3TIlDxpms, JJExl9hnYbo, y las
   clases 02 y 03 de "APP-TimboCompras") y ver sin subtítulos la Clase 01
   (7rIDyLtWlHM) y Wb4ZRvB3YSo (registro de proveedor).
2. Consultas abiertas en los chats: SIN sin "comenzar una carga",
   numeración de decisorios, documentos HTML→PDF y servidor propio para
   los videos. Cuando haya respuesta, pasar a `verificado: True` en
   `scripts/importar_faq_chats.py`.
3. Confirmar con Compras del hospital si la Circular SCyGB 03/2026 (control
   de la URC) les aplica: está dirigida a la Administración Central.
4. Leer a mano los anexos de la Circular SCyGB 05/2026 (textos para los
   formularios del PBCP, que son imágenes) y armar una lección.
5. Lección de contrataciones directas por urgencia o desierto (Circular UG
   TIMBÓ 8/2026).
6. Siguientes etapas del README: estadísticas, buscador global y Alembic.
