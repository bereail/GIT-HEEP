// app.js — bootstrap de la aplicación: arma el layout (sidebar, topbar,
// buscador, lightbox, toast) e inicializa el router.

import { MODULES, GLOSSARY, SITUATIONS, TASKS } from '../../content/content.js';
import * as progreso from './progress.js';
import { construirIndice, buscar } from './search.js';
import { initChatbot } from './chatbot.js';
import { ruta, rutaNoEncontrada, navegar, iniciarRouter } from './router.js';
import {
  vistaHome,
  vistaQuickstart,
  vistaModulos,
  vistaModulo,
  vistaLeccion,
  vistaTareas,
  vistaProblemas,
  vistaGlosario,
  vistaProgreso,
  vistaNoEncontrada,
} from './views.js';

const app = document.getElementById('app');

app.innerHTML = `
  <div class="shell">
    <header class="topbar">
      <button type="button" class="topbar__menu-btn" id="btn-menu" aria-label="Abrir menú">☰</button>
      <a class="topbar__brand" href="#/">
        <span class="topbar__brand-mark">T</span>
        <span>TIMBÓ · Campus</span>
      </a>
      <div class="topbar__search">
        <div class="input-wrap">
          <span class="input-wrap__icon">🔎</span>
          <input class="input" id="input-buscar-global" type="text" placeholder="Buscar en toda la capacitación..." aria-label="Buscar" />
        </div>
      </div>
      <div class="topbar__spacer"></div>
      <button type="button" class="topbar__search-btn" id="btn-buscar-movil" aria-label="Buscar">🔎</button>
    </header>

    <aside class="sidebar" id="sidebar"></aside>
    <div class="sidebar-scrim" id="sidebar-scrim"></div>

    <main class="content" id="main-content" tabindex="-1"></main>
  </div>

  <div class="search-overlay" id="search-overlay">
    <div class="search-modal">
      <div class="search-modal__input-row">
        <div class="input-wrap">
          <span class="input-wrap__icon">🔎</span>
          <input class="input" id="input-buscar-modal" type="text" placeholder="¿Cómo busco...? ¿Cómo cargo...?" aria-label="Buscar" />
        </div>
      </div>
      <div class="search-modal__results" id="resultados-busqueda"></div>
    </div>
  </div>

  <div class="lightbox-overlay" id="lightbox-overlay">
    <button type="button" class="lightbox-close" id="lightbox-close" aria-label="Cerrar">×</button>
    <img id="lightbox-img" src="" alt="" />
  </div>

  <div class="toast" id="toast"></div>
`;

const main = document.getElementById('main-content');
const sidebar = document.getElementById('sidebar');
const sidebarScrim = document.getElementById('sidebar-scrim');
const searchOverlay = document.getElementById('search-overlay');
const inputBuscarGlobal = document.getElementById('input-buscar-global');
const inputBuscarModal = document.getElementById('input-buscar-modal');
const resultadosBusqueda = document.getElementById('resultados-busqueda');
const lightboxOverlay = document.getElementById('lightbox-overlay');
const lightboxImg = document.getElementById('lightbox-img');
const toastEl = document.getElementById('toast');

// ------------------------------------------------------------------ sidebar --

function renderSidebar() {
  const rutaHash = window.location.hash || '#/';
  const esActiva = (href) => (rutaHash === href ? 'is-active' : '');

  sidebar.innerHTML = `
    <div class="sidebar__section-title">Capacitación</div>
    <a class="nav-link ${esActiva('#/')}" href="#/"><span class="nav-link__icon">🏠</span>Inicio</a>
    <a class="nav-link ${esActiva('#/quickstart')}" href="#/quickstart"><span class="nav-link__icon">🚀</span>Primeros 15 minutos</a>
    <a class="nav-link ${esActiva('#/tareas')}" href="#/tareas"><span class="nav-link__icon">🔎</span>Quiero hacer...</a>
    <a class="nav-link ${esActiva('#/problemas')}" href="#/problemas"><span class="nav-link__icon">🩹</span>Tengo un problema</a>
    <a class="nav-link ${esActiva('#/glosario')}" href="#/glosario"><span class="nav-link__icon">📖</span>Glosario</a>
    <a class="nav-link ${esActiva('#/progreso')}" href="#/progreso"><span class="nav-link__icon">📊</span>Mi progreso</a>

    <div class="sidebar__section-title">Módulos</div>
    ${MODULES.map((m) => {
      const href = `#/modulo/${m.id}`;
      const pct = progreso.progresoDeModulo(m);
      const activo = rutaHash === href || rutaHash.startsWith(`${href}/`);
      return `<a class="nav-link ${activo ? 'is-active' : ''}" href="${href}">
        <span class="nav-link__icon">${m.icon}</span>${m.title}
        <span class="nav-link__progress">${pct}%</span>
      </a>`;
    }).join('')}
  `;
}

// ------------------------------------------------------------------- rutas --

ruta('/', () => { vistaHome(main); afterRender(); });
ruta('/quickstart', () => { vistaQuickstart(main); afterRender(); });
ruta('/modulos', () => { vistaModulos(main); afterRender(); });
ruta('/modulo/:id', (p) => { vistaModulo(main, p); afterRender(); });
ruta('/modulo/:id/leccion/:lessonId', (p) => { vistaLeccion(main, p); afterRender(); });
ruta('/tareas', () => { vistaTareas(main); afterRender(); });
ruta('/problemas', () => { vistaProblemas(main); afterRender(); });
ruta('/glosario', () => { vistaGlosario(main); afterRender(); });
ruta('/progreso', () => { vistaProgreso(main); afterRender(); });
rutaNoEncontrada(() => { vistaNoEncontrada(main); afterRender(); });

function afterRender() {
  renderSidebar();
  main.focus();
  main.scrollTop = 0;
  window.scrollTo(0, 0);
  cerrarSidebarMovil();
}

// ------------------------------------------------------- acciones globales --

document.body.addEventListener('click', (ev) => {
  const togglerLeccion = ev.target.closest('.js-toggle-leccion');
  if (togglerLeccion) {
    const { module: moduleId, lesson: lessonId } = togglerLeccion.dataset;
    const yaHecha = progreso.estaLeccionCompleta(moduleId, lessonId);
    progreso.marcarLeccion(moduleId, lessonId, !yaHecha);
    mostrarToast(!yaHecha ? 'Lección marcada como completada.' : 'Lección marcada como pendiente.');
    const hallazgo = window.location.hash.match(/^#\/modulo\/([^/]+)\/leccion\/([^/]+)/);
    if (hallazgo) vistaLeccion(main, { id: hallazgo[1], lessonId: hallazgo[2] });
    renderSidebar();
    return;
  }

  const imagen = ev.target.closest('.lightbox-trigger');
  if (imagen) {
    abrirLightbox(imagen.dataset.src, imagen.dataset.alt);
  }
});

window.addEventListener('timbo:toast', (ev) => mostrarToast(ev.detail));
window.addEventListener('timbo:progreso-cambio', () => renderSidebar());

// ---------------------------------------------------------------- toast ----

let toastTimeout = null;
function mostrarToast(texto) {
  toastEl.textContent = texto;
  toastEl.classList.add('is-open');
  clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => toastEl.classList.remove('is-open'), 2600);
}

// -------------------------------------------------------------- lightbox ---

function abrirLightbox(src, alt) {
  lightboxImg.src = src;
  lightboxImg.alt = alt || '';
  lightboxOverlay.classList.add('is-open');
}
function cerrarLightbox() {
  lightboxOverlay.classList.remove('is-open');
}
document.getElementById('lightbox-close').addEventListener('click', cerrarLightbox);
lightboxOverlay.addEventListener('click', (ev) => { if (ev.target === lightboxOverlay) cerrarLightbox(); });
document.addEventListener('keydown', (ev) => { if (ev.key === 'Escape') { cerrarLightbox(); cerrarBusqueda(); } });

// --------------------------------------------------------------- búsqueda --

const indiceBusqueda = construirIndice({ MODULES, GLOSSARY, SITUATIONS, TASKS });
initChatbot({ indice: indiceBusqueda, MODULES, SITUATIONS, TASKS });

function abrirBusqueda() {
  searchOverlay.classList.add('is-open');
  inputBuscarModal.value = '';
  renderResultadosBusqueda('');
  setTimeout(() => inputBuscarModal.focus(), 60);
}
function cerrarBusqueda() {
  searchOverlay.classList.remove('is-open');
}

function renderResultadosBusqueda(consulta) {
  if (!consulta.trim()) {
    resultadosBusqueda.innerHTML = `<div class="search-empty">Escribí para buscar lecciones, tareas, glosario o problemas frecuentes.</div>`;
    return;
  }
  const resultados = buscar(indiceBusqueda, consulta);
  if (!resultados.length) {
    resultadosBusqueda.innerHTML = `<div class="search-empty">Sin resultados para "${consulta}".</div>`;
    return;
  }
  resultadosBusqueda.innerHTML = resultados
    .map(
      (r) => `<a class="search-result" href="${r.hash}">
        <div class="search-result__kind">${r.kind}</div>
        <div class="search-result__title">${r.title}</div>
      </a>`
    )
    .join('');
}

inputBuscarGlobal.addEventListener('focus', abrirBusqueda);
inputBuscarGlobal.addEventListener('click', abrirBusqueda);
document.getElementById('btn-buscar-movil').addEventListener('click', abrirBusqueda);
inputBuscarModal.addEventListener('input', () => renderResultadosBusqueda(inputBuscarModal.value));
searchOverlay.addEventListener('click', (ev) => { if (ev.target === searchOverlay) cerrarBusqueda(); });
resultadosBusqueda.addEventListener('click', (ev) => { if (ev.target.closest('.search-result')) cerrarBusqueda(); });

// -------------------------------------------------------------- sidebar móvil --

function abrirSidebarMovil() {
  sidebar.classList.add('is-open');
}
function cerrarSidebarMovil() {
  sidebar.classList.remove('is-open');
}
document.getElementById('btn-menu').addEventListener('click', abrirSidebarMovil);
sidebarScrim.addEventListener('click', cerrarSidebarMovil);

// --------------------------------------------------------------------- init --

renderSidebar();
iniciarRouter();
