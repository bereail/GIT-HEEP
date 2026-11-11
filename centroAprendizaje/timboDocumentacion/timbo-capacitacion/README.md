# TIMBÓ · Campus de capacitación

Plataforma interactiva de capacitación para el sistema hospitalario **TIMBÓ**
(miHospital, Gobierno de Santa Fe). Es un sitio estático — sin backend, sin
build step, sin login — pensado para enseñar a usar el sistema con lecciones
cortas, capturas reales, quizzes y una guía de "¿cómo hago...?" y "¿tengo un
problema?".

La fuente de verdad del contenido es `../MANUAL_USUARIO_MIHOSPITAL.md` y
`../notas_relevamiento.md` (un nivel arriba de esta carpeta). Si algo cambia
en el sistema real, hay que actualizar primero esos documentos y después
`content/content.js`.

## Arquitectura

- **Vanilla HTML/CSS/JS con ES Modules.** Sin frameworks, sin dependencias de
  npm, sin CDN. Elegido así porque el servidor destino (red interna del
  hospital) puede no tener salida a Internet.
- **Routing hash-based** (`#/modulo/pacientes/leccion/buscar-paciente`), para
  poder servir el sitio como archivos estáticos planos, sin configurar
  rewrites en Nginx.
- **Progreso en `localStorage`**, por navegador, sin cuentas de usuario.
- Todo el contenido pedagógico vive en un único archivo de datos
  (`content/content.js`), separado del código que lo renderiza.

```
timbo-capacitacion/
├── index.html              # shell mínimo, carga styles.css y app.js
├── content/
│   └── content.js          # TODA la data: módulos, lecciones, quizzes,
│                            # glosario, tareas, situaciones, ruta guiada
├── assets/
│   ├── css/styles.css      # sistema de diseño completo
│   ├── img/                # capturas de pantalla reales (.jpg)
│   └── js/
│       ├── app.js          # bootstrap: layout, buscador, lightbox, router
│       ├── router.js       # router hash-based
│       ├── views.js        # una función de render por ruta
│       ├── progress.js     # API de progreso sobre localStorage
│       ├── search.js       # indexado y búsqueda de todo el contenido
│       ├── chatbot.js      # asistente de preguntas (ver sección abajo)
│       └── quiz.js         # renderizado/corrección de los 4 tipos de quiz
└── README.md
```

## Cómo correr localmente

Cualquier servidor estático simple sirve. Por ejemplo, desde esta carpeta:

```bash
python -m http.server 8080
```

y abrir `http://localhost:8080/`. **No se puede abrir `index.html` con
doble clic** (`file://`) porque los navegadores bloquean los ES Modules
(`import`/`export`) cargados desde el sistema de archivos directamente — hace
falta un servidor HTTP, aunque sea local.

## Cómo agregar contenido

Todo el contenido pedagógico está en `content/content.js`, organizado en:

- **`MODULES`**: array de módulos. Cada módulo tiene `lessons`, y cada
  lección tiene `blocks` (el cuerpo: texto, pasos, tips, advertencias,
  conceptos, práctica) y `quiz` (preguntas).
- **`GLOSSARY`**, **`SITUATIONS`** (para "¿Tenés un problema?"), **`TASKS`**
  (para "Quiero hacer...") y **`QUICKSTART`** (ruta "primeros 15 minutos").

### Agregar una lección nueva

Copiá el objeto de una lección existente dentro de `lessons` del módulo que
corresponda, cambiá `id` (debe ser único dentro del módulo, sin espacios ni
tildes), `title`, `minutes`, `difficulty`, y completá `blocks`/`quiz`. No
hace falta tocar ningún otro archivo — las vistas, el router, el buscador y
el progreso leen `content.js` dinámicamente.

### Agregar una captura de pantalla

1. Guardar la imagen en `assets/img/` (formato `.jpg`, nombre descriptivo en
   minúsculas con guiones, por ejemplo `nueva-pantalla.jpg`).
2. Referenciarla en un bloque `{ type: 'step', image: 'nueva-pantalla.jpg', ... }`
   — el nombre del archivo solo, sin la ruta `assets/img/` (eso lo agrega la
   vista automáticamente).
3. Completar siempre `alt` (accesibilidad) y `caption`.

**Nunca** usar una captura que muestre nombres reales de pacientes o de
personal del hospital — usar el paciente de prueba "VIRTUAL" o, si no hay
forma de evitarlo, describir la pantalla en texto en vez de capturarla.

### Agregar un esquema ilustrativo (cuando no hay captura real)

Para pantallas sin captura disponible todavía, se puede usar un bloque
`diagram` en vez de (o además de) `image` en un `step`, o como bloque
independiente en `blocks`. Siempre se renderiza con la etiqueta
"🖼 Esquema ilustrativo — no es una captura real", nunca se confunde con una
captura. Si el esquema necesita representar una fila con datos de pacientes,
usar `'◼'` como valor de celda para que se muestre tapada (`redacted-bar`) en
vez de inventar un dato.

```js
{ type: 'diagram', variant: 'table', title, columns: [...], rows: [[...]], note }   // o celda '◼' = tapada
{ type: 'diagram', variant: 'cards', title, items: [{ label, value }], note }
{ type: 'diagram', variant: 'tabs', title, tabs: [...], active: 0, note }
{ type: 'diagram', variant: 'list', title, items: [{ label, hint, tone }], note }   // tone: basico|intermedio|avanzado|verified|unverified|neutral
```

Dentro de un `step`, en vez de `image` se puede pasar `diagram: {...}` con la
misma forma, y se renderiza en el lugar donde iría la captura.

### Agregar una pregunta de quiz

Los 4 tipos soportados, con su forma exacta:

```js
{ type: 'multiple-choice', question, options: [...], correctIndex, explanation }
{ type: 'true-false', question, answer: true|false, explanation }
{ type: 'order-steps', instruction, steps: [...] }        // se mezclan al mostrarse
{ type: 'checklist', title, items: [...] }                 // autoevaluación, no se corrige
```

## Asistente de preguntas (chatbot)

El botón flotante "💬 ¿Tenés una duda?" (abajo a la derecha, en toda
pantalla) es un buscador conversacional **100% local, sin IA externa, sin
backend y sin costo**: reutiliza el mismo índice de `search.js` sobre
`content.js` (glosario, "Tengo un problema", "Quiero hacer...", módulos y
lecciones) y responde con el mejor resultado encontrado, en formato de chat.
Como es parte del mismo sitio estático, **no necesita ningún paso de deploy
aparte** — se sube junto con el resto de la carpeta.

No hace falta tocar `chatbot.js` para que conteste mejor: cuantas más
entradas tenga `GLOSSARY`, `SITUATIONS` y `TASKS` en `content.js`, mejores
respuestas da el asistente, porque usa exactamente el mismo contenido que ya
alimenta el Glosario, "Tengo un problema" y "Quiero hacer...".

El ranking de búsqueda (`search.js`) filtra una lista de palabras muy
frecuentes en preguntas en lenguaje natural (`PALABRAS_VACIAS`: "qué", "es",
"el", "sin", etc.) antes de puntuar, para que una pregunta tipo "¿Qué es el
CIE-10?" no termine matcheando por casualidad con algo que no tiene nada que
ver. Si en el futuro aparece una respuesta rara para una pregunta razonable,
revisar primero si alguna palabra corta de la consulta está "de casualidad"
dentro del texto de otra entrada no relacionada, y sumarla a esa lista.

Si en algún momento se quisiera un chatbot con IA real (respuestas en
lenguaje libre, no solo lo ya cargado en `content.js`), es un cambio de
arquitectura más grande: requiere una API key paga (OpenAI/Anthropic/etc.) y
un backend corriendo en el servidor — ya no sería un sitio 100% estático
como hoy.

## Progreso y privacidad

El progreso (lecciones completadas, resultados de quizzes) se guarda en
`localStorage` del navegador de cada persona — no se envía a ningún
servidor ni se comparte entre dispositivos. "Mi progreso" tiene un botón
para reiniciarlo.

## Deploy

**Pendiente.** Se evaluó el servidor `192.168.7.250` (Ubuntu 20.04) como
destino, pero la auditoría del servidor y el deploy quedaron pospuestos
hasta que se retomen explícitamente. Al hacerlo:

1. Auditar el servidor antes de tocar nada (servicios, puertos, Nginx,
   firewall activos) — no romper nada existente, no exponer el sitio a
   Internet.
2. Copiar esta carpeta (`timbo-capacitacion/`) completa al servidor, por
   ejemplo a `/timbo/`.
3. Servirla como archivos estáticos (Nginx `root` apuntando a la carpeta,
   sin necesidad de rewrites gracias al routing hash-based).
4. No hace falta build ni `npm install`: es HTML/CSS/JS plano.
