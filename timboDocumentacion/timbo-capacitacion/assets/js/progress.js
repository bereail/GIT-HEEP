// progress.js — API de progreso sobre localStorage. Sin backend, sin login:
// todo el estado vive en el navegador de quien usa la capacitación.

const STORAGE_KEY = 'timbo-campus-progreso-v1';

function cargarEstado() {
  try {
    const crudo = localStorage.getItem(STORAGE_KEY);
    if (!crudo) return { lecciones: {}, quizzes: {} };
    const datos = JSON.parse(crudo);
    return {
      lecciones: datos.lecciones || {},
      quizzes: datos.quizzes || {},
    };
  } catch {
    return { lecciones: {}, quizzes: {} };
  }
}

function guardarEstado(estado) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(estado));
  } catch {
    // localStorage no disponible (modo privado estricto, cuota llena, etc.):
    // la app sigue funcionando, solo no persiste el progreso entre sesiones.
  }
}

function claveLeccion(moduleId, lessonId) {
  return `${moduleId}/${lessonId}`;
}

export function estaLeccionCompleta(moduleId, lessonId) {
  const estado = cargarEstado();
  return Boolean(estado.lecciones[claveLeccion(moduleId, lessonId)]);
}

export function marcarLeccion(moduleId, lessonId, completa) {
  const estado = cargarEstado();
  const clave = claveLeccion(moduleId, lessonId);
  if (completa) {
    estado.lecciones[clave] = { completadaEn: new Date().toISOString() };
  } else {
    delete estado.lecciones[clave];
  }
  guardarEstado(estado);
}

export function guardarResultadoQuiz(moduleId, lessonId, correctas, total) {
  const estado = cargarEstado();
  estado.quizzes[claveLeccion(moduleId, lessonId)] = { correctas, total, en: new Date().toISOString() };
  guardarEstado(estado);
}

export function obtenerResultadoQuiz(moduleId, lessonId) {
  const estado = cargarEstado();
  return estado.quizzes[claveLeccion(moduleId, lessonId)] || null;
}

export function progresoDeModulo(modulo) {
  if (!modulo.lessons.length) return 0;
  const estado = cargarEstado();
  const completas = modulo.lessons.filter((l) => estado.lecciones[claveLeccion(modulo.id, l.id)]).length;
  return Math.round((completas / modulo.lessons.length) * 100);
}

export function progresoTotal(modulos) {
  const total = modulos.reduce((acc, m) => acc + m.lessons.length, 0);
  if (!total) return 0;
  const estado = cargarEstado();
  const completas = modulos.reduce(
    (acc, m) => acc + m.lessons.filter((l) => estado.lecciones[claveLeccion(m.id, l.id)]).length,
    0
  );
  return Math.round((completas / total) * 100);
}

export function leccionesCompletadas(modulos) {
  const estado = cargarEstado();
  const resultado = [];
  for (const modulo of modulos) {
    for (const leccion of modulo.lessons) {
      if (estado.lecciones[claveLeccion(modulo.id, leccion.id)]) {
        resultado.push({
          moduleId: modulo.id,
          moduleTitle: modulo.title,
          lessonId: leccion.id,
          lessonTitle: leccion.title,
          completadaEn: estado.lecciones[claveLeccion(modulo.id, leccion.id)].completadaEn,
        });
      }
    }
  }
  resultado.sort((a, b) => (a.completadaEn < b.completadaEn ? 1 : -1));
  return resultado;
}

export function reiniciarProgreso() {
  guardarEstado({ lecciones: {}, quizzes: {} });
}
