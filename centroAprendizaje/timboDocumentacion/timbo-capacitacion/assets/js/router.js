// router.js — router hash-based simple. No necesita configuración en el
// servidor (sirve sobre archivos estáticos planos, sin rewrites de Nginx).

const rutas = [];

export function ruta(patron, manejador) {
  // patron tipo "/modulo/:id/leccion/:lessonId" -> regex con grupos nombrados
  const nombresParams = [];
  const regexStr = patron
    .split('/')
    .map((segmento) => {
      if (segmento.startsWith(':')) {
        nombresParams.push(segmento.slice(1));
        return '([^/]+)';
      }
      return segmento.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    })
    .join('/');
  rutas.push({ regex: new RegExp(`^${regexStr}$`), nombresParams, manejador });
}

function rutaActual() {
  const hash = window.location.hash || '#/';
  return hash.slice(1) || '/';
}

function resolver() {
  const path = rutaActual().split('?')[0];
  for (const r of rutas) {
    const match = path.match(r.regex);
    if (match) {
      const params = {};
      r.nombresParams.forEach((nombre, i) => {
        params[nombre] = decodeURIComponent(match[i + 1]);
      });
      r.manejador(params);
      return;
    }
  }
  const noEncontrado = rutas.find((r) => r.esNotFound);
  if (noEncontrado) noEncontrado.manejador({});
}

export function rutaNoEncontrada(manejador) {
  rutas.push({ esNotFound: true, manejador });
}

export function navegar(hash) {
  if (window.location.hash === hash) {
    resolver();
  } else {
    window.location.hash = hash;
  }
}

export function iniciarRouter() {
  window.addEventListener('hashchange', resolver);
  resolver();
}
