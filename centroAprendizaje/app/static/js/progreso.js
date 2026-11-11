// progreso.js — progreso del usuario en localStorage, por navegador, sin
// cuentas ni backend (igual que en timbo-capacitacion/assets/js/progress.js).
// La única diferencia es que la clave de cada tutorial ahora incluye el
// tema, porque un mismo navegador puede estar usando varios temas distintos
// del portal.

const STORAGE_KEY = 'centro-aprendizaje-progreso-v1';

function cargarEstado() {
  try {
    const crudo = localStorage.getItem(STORAGE_KEY);
    if (!crudo) return { tutoriales: {}, quizzes: {} };
    const datos = JSON.parse(crudo);
    return {
      tutoriales: datos.tutoriales || {},
      quizzes: datos.quizzes || {},
    };
  } catch {
    return { tutoriales: {}, quizzes: {} };
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

function clave(temaSlug, categoriaSlug, tutorialSlug) {
  return `${temaSlug}/${categoriaSlug}/${tutorialSlug}`;
}

export function estaTutorialCompleto(temaSlug, categoriaSlug, tutorialSlug) {
  const estado = cargarEstado();
  return Boolean(estado.tutoriales[clave(temaSlug, categoriaSlug, tutorialSlug)]);
}

export function marcarTutorial(temaSlug, categoriaSlug, tutorialSlug, completo) {
  const estado = cargarEstado();
  const k = clave(temaSlug, categoriaSlug, tutorialSlug);
  if (completo) {
    estado.tutoriales[k] = { completadoEn: new Date().toISOString() };
  } else {
    delete estado.tutoriales[k];
  }
  guardarEstado(estado);
}

export function guardarResultadoQuiz(temaSlug, categoriaSlug, tutorialSlug, correctas, total) {
  const estado = cargarEstado();
  estado.quizzes[clave(temaSlug, categoriaSlug, tutorialSlug)] = { correctas, total, en: new Date().toISOString() };
  guardarEstado(estado);
}

export function obtenerResultadoQuiz(temaSlug, categoriaSlug, tutorialSlug) {
  const estado = cargarEstado();
  return estado.quizzes[clave(temaSlug, categoriaSlug, tutorialSlug)] || null;
}

// `categorias` = [{ slug, tutoriales: [{ slug }, ...] }, ...] del tema actual
// (se embebe en la página como JSON — ver base.html).

export function progresoDeCategoria(temaSlug, categoria) {
  if (!categoria.tutoriales.length) return 0;
  const estado = cargarEstado();
  const completos = categoria.tutoriales.filter(
    (t) => estado.tutoriales[clave(temaSlug, categoria.slug, t.slug)]
  ).length;
  return Math.round((completos / categoria.tutoriales.length) * 100);
}

export function progresoTotal(temaSlug, categorias) {
  const total = categorias.reduce((acc, c) => acc + c.tutoriales.length, 0);
  if (!total) return 0;
  const estado = cargarEstado();
  const completos = categorias.reduce(
    (acc, c) => acc + c.tutoriales.filter((t) => estado.tutoriales[clave(temaSlug, c.slug, t.slug)]).length,
    0
  );
  return Math.round((completos / total) * 100);
}

export function tutorialesCompletados(temaSlug, categorias) {
  const estado = cargarEstado();
  const resultado = [];
  for (const categoria of categorias) {
    for (const tutorial of categoria.tutoriales) {
      const entrada = estado.tutoriales[clave(temaSlug, categoria.slug, tutorial.slug)];
      if (entrada) {
        resultado.push({
          categoriaSlug: categoria.slug,
          categoriaTitulo: categoria.titulo,
          tutorialSlug: tutorial.slug,
          tutorialTitulo: tutorial.titulo,
          completadoEn: entrada.completadoEn,
        });
      }
    }
  }
  resultado.sort((a, b) => (a.completadoEn < b.completadoEn ? 1 : -1));
  return resultado;
}

export function reiniciarProgreso() {
  guardarEstado({ tutoriales: {}, quizzes: {} });
}
