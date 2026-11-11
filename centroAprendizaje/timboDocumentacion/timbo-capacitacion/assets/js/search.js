// search.js — indexado y búsqueda sobre content.js (módulos, lecciones,
// tareas de "Quiero hacer...", situaciones de "Tengo un problema" y glosario).

function normalizar(texto) {
  return (texto || '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[¿?¡!.,;:"'()]/g, '');
}

// Palabras muy frecuentes en preguntas en lenguaje natural ("¿Qué es el
// CIE-10?") que no aportan nada para encontrar el resultado correcto, pero
// que al ser cortas aparecen "de casualidad" dentro de muchos textos y
// pueden ganarle el ranking a la palabra realmente específica de la consulta.
const PALABRAS_VACIAS = new Set([
  'que', 'qué', 'es', 'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas',
  'de', 'del', 'en', 'con', 'para', 'por', 'como', 'cómo', 'donde', 'dónde',
  'cual', 'cuál', 'cuales', 'cuáles', 'y', 'o', 'a', 'se', 'mi', 'tu', 'su',
  'al', 'lo', 'le', 'les', 'me', 'te', 'nos', 'sobre', 'hay',
  'sin', 'mas', 'más', 'ya', 'pero', 'si', 'no', 'ni', 'muy', 'esta', 'está',
]);

export function construirIndice({ MODULES, TASKS, SITUATIONS, GLOSSARY }) {
  const entradas = [];

  for (const tarea of TASKS) {
    entradas.push({
      kind: 'Tarea',
      title: tarea.question,
      subtitle: tarea.title,
      hash: `#/modulo/${tarea.moduleId}/leccion/${tarea.lessonId}`,
      texto: normalizar(`${tarea.question} ${tarea.title} ${(tarea.keywords || []).join(' ')}`),
      peso: 3,
    });
  }

  for (const situacion of SITUATIONS) {
    entradas.push({
      kind: 'Problema',
      title: situacion.situation,
      subtitle: situacion.description,
      hash: '#/problemas',
      texto: normalizar(`${situacion.situation} ${situacion.description}`),
      peso: 2,
    });
  }

  for (const modulo of MODULES) {
    entradas.push({
      kind: 'Módulo',
      title: modulo.title,
      subtitle: modulo.summary,
      hash: `#/modulo/${modulo.id}`,
      texto: normalizar(`${modulo.title} ${modulo.summary}`),
      peso: 1.5,
    });
    for (const leccion of modulo.lessons) {
      entradas.push({
        kind: 'Lección',
        title: leccion.title,
        subtitle: modulo.title,
        hash: `#/modulo/${modulo.id}/leccion/${leccion.id}`,
        texto: normalizar(`${leccion.title} ${modulo.title}`),
        peso: 2,
      });
    }
  }

  for (const termino of GLOSSARY) {
    entradas.push({
      kind: 'Glosario',
      title: termino.term,
      subtitle: termino.definition,
      hash: '#/glosario',
      texto: normalizar(`${termino.term} ${termino.definition}`),
      peso: 1,
    });
  }

  return entradas;
}

export function buscar(indice, consulta, limite = 12) {
  const q = normalizar(consulta).trim();
  if (!q) return [];
  const todasLasPalabras = q.split(/\s+/).filter(Boolean);
  const palabrasEspecificas = todasLasPalabras.filter((p) => !PALABRAS_VACIAS.has(p));
  // Si la consulta es solo palabras vacías ("qué es"), mejor buscar con todo
  // antes que no encontrar nada.
  const palabras = palabrasEspecificas.length ? palabrasEspecificas : todasLasPalabras;

  const resultados = indice
    .map((entrada) => {
      let score = 0;
      for (const palabra of palabras) {
        if (entrada.texto.includes(palabra)) {
          score += entrada.texto.startsWith(palabra) ? 2 : 1;
        }
      }
      return { entrada, score: score * entrada.peso };
    })
    .filter((r) => r.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, limite)
    .map((r) => r.entrada);

  return resultados;
}
