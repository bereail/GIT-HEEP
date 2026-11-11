// exportar_content_js.mjs — convierte content.js (ES Modules, la fuente de
// verdad del tema miHospital en timbo-capacitacion) a un único JSON, para
// que el script de importación en Python lo pueda leer sin tener que
// transcribir a mano casi 800 líneas de contenido (con el riesgo de errores
// que eso implica). Se ejecuta una sola vez por actualización de contenido,
// no en cada arranque del servidor.
//
// Uso: node scripts/exportar_content_js.mjs > scripts/content_mihospital.json

import { pathToFileURL } from "node:url";
import path from "node:path";

const ruta = path.resolve(
  "timboDocumentacion/timbo-capacitacion/content/content.js"
);

const modulo = await import(pathToFileURL(ruta).href);

const datos = {
  SYSTEM_INFO: modulo.SYSTEM_INFO,
  GLOSSARY: modulo.GLOSSARY,
  MODULES: modulo.MODULES,
  QUICKSTART: modulo.QUICKSTART,
  SITUATIONS: modulo.SITUATIONS,
  TASKS: modulo.TASKS,
};

process.stdout.write(JSON.stringify(datos, null, 2));
