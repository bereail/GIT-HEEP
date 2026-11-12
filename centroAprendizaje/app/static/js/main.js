// main.js — glue de la aplicación server-rendered: sidebar móvil, buscador
// global (fetch al backend), lightbox, toast, y el toggle de "lección
// completada". El HTML de cada página lo arma Flask/Jinja; este script solo
// agrega la interactividad liviana, igual que hacía app.js en la versión
// 100% estática.

import { initChatbot } from './chatbot.js';
import * as progreso from './progreso.js';

const temaSlug = document.body.dataset.temaSlug || null;
const temaNombre = document.body.dataset.temaNombre || '';

const sidebar = document.getElementById('sidebar');
const sidebarScrim = document.getElementById('sidebar-scrim');
const searchOverlay = document.getElementById('search-overlay');
const inputBuscarGlobal = document.getElementById('input-buscar-global');
const inputBuscarModal = document.getElementById('input-buscar-modal');
const resultadosBusqueda = document.getElementById('resultados-busqueda');
const lightboxOverlay = document.getElementById('lightbox-overlay');
const lightboxImg = document.getElementById('lightbox-img');
const toastEl = document.getElementById('toast');

// ---------------------------------------------------------------- toast ----

let toastTimeout = null;
function mostrarToast(texto) {
  if (!toastEl) return;
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
if (lightboxOverlay) {
  document.getElementById('lightbox-close').addEventListener('click', cerrarLightbox);
  lightboxOverlay.addEventListener('click', (ev) => {
    if (ev.target === lightboxOverlay) cerrarLightbox();
  });
}

// --------------------------------------------------------------- búsqueda --

function abrirBusqueda() {
  if (!searchOverlay) return;
  searchOverlay.classList.add('is-open');
  inputBuscarModal.value = '';
  renderResultadosBusqueda('');
  setTimeout(() => inputBuscarModal.focus(), 60);
}
function cerrarBusqueda() {
  if (searchOverlay) searchOverlay.classList.remove('is-open');
}

async function renderResultadosBusqueda(consulta) {
  if (!consulta.trim()) {
    resultadosBusqueda.innerHTML = temaSlug
      ? '<div class="search-empty">Escribí para buscar tutoriales, tareas, glosario o problemas frecuentes.</div>'
      : '<div class="search-empty">Escribí para buscar en todas las capacitaciones.</div>';
    return;
  }
  const url = temaSlug
    ? `/temas/${temaSlug}/buscar.json?q=${encodeURIComponent(consulta)}`
    : `/buscar.json?q=${encodeURIComponent(consulta)}`;
  let resultados = [];
  try {
    const resp = await fetch(url);
    resultados = await resp.json();
  } catch {
    resultadosBusqueda.innerHTML = '<div class="search-empty">No se pudo buscar en este momento.</div>';
    return;
  }
  if (!resultados.length) {
    resultadosBusqueda.innerHTML = `<div class="search-empty">Sin resultados para "${consulta}".</div>`;
    return;
  }
  resultadosBusqueda.innerHTML = resultados
    .map(
      (r) => `<a class="search-result" href="${r.url}">
        <div class="search-result__kind">${r.kind}${r.tema_nombre ? ` · ${r.tema_icono} ${r.tema_nombre}` : ''}</div>
        <div class="search-result__title">${r.title}</div>
      </a>`
    )
    .join('');
}

let temporizadorBusqueda = null;
function buscarConDebounce(consulta) {
  clearTimeout(temporizadorBusqueda);
  temporizadorBusqueda = setTimeout(() => renderResultadosBusqueda(consulta), 300);
}

if (inputBuscarGlobal) {
  inputBuscarGlobal.addEventListener('focus', abrirBusqueda);
  inputBuscarGlobal.addEventListener('click', abrirBusqueda);
}
const btnBuscarMovil = document.getElementById('btn-buscar-movil');
if (btnBuscarMovil) btnBuscarMovil.addEventListener('click', abrirBusqueda);
if (inputBuscarModal) inputBuscarModal.addEventListener('input', () => buscarConDebounce(inputBuscarModal.value));
if (searchOverlay) {
  searchOverlay.addEventListener('click', (ev) => {
    if (ev.target === searchOverlay) cerrarBusqueda();
  });
}
if (resultadosBusqueda) {
  resultadosBusqueda.addEventListener('click', (ev) => {
    if (ev.target.closest('.search-result')) cerrarBusqueda();
  });
}

document.addEventListener('keydown', (ev) => {
  if (ev.key === 'Escape') {
    cerrarLightbox();
    cerrarBusqueda();
  }
});

// -------------------------------------------------------------- sidebar móvil --

function abrirSidebarMovil() {
  if (sidebar) sidebar.classList.add('is-open');
}
function cerrarSidebarMovil() {
  if (sidebar) sidebar.classList.remove('is-open');
}
const btnMenu = document.getElementById('btn-menu');
if (btnMenu) btnMenu.addEventListener('click', abrirSidebarMovil);
if (sidebarScrim) sidebarScrim.addEventListener('click', cerrarSidebarMovil);

// ------------------------------------------------- acciones sobre el contenido --

document.body.addEventListener('click', (ev) => {
  const togglerTutorial = ev.target.closest('.js-toggle-tutorial');
  if (togglerTutorial) {
    const { categoria: categoriaSlug, tutorial: tutorialSlug } = togglerTutorial.dataset;
    const yaHecho = progreso.estaTutorialCompleto(temaSlug, categoriaSlug, tutorialSlug);
    progreso.marcarTutorial(temaSlug, categoriaSlug, tutorialSlug, !yaHecho);
    mostrarToast(!yaHecho ? 'Tutorial marcado como completado.' : 'Tutorial marcado como pendiente.');
    togglerTutorial.classList.toggle('is-done', !yaHecho);
    togglerTutorial.querySelector('span').textContent = !yaHecho ? '✓' : '○';
    togglerTutorial.lastChild.textContent = !yaHecho ? ' Tutorial completado' : ' Marcar como completado';
    pintarProgresoEnPagina();
    return;
  }

  const imagen = ev.target.closest('.lightbox-trigger');
  if (imagen) abrirLightbox(imagen.dataset.src, imagen.dataset.alt);

  const votoFeedback = ev.target.closest('.js-feedback-tutorial');
  if (votoFeedback) {
    const barra = votoFeedback.closest('.feedback-bar');
    const { voto } = votoFeedback.dataset;
    const { titulo } = barra.dataset;
    fetch(`/temas/${temaSlug}/feedback-tutorial`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ titulo, voto }),
    }).catch(() => {});
    barra.querySelectorAll('.js-feedback-tutorial').forEach((b) => (b.disabled = true));
    mostrarToast(voto === 'si' ? '¡Gracias por tu feedback!' : 'Gracias, lo vamos a revisar.');
  }
});

// ---------------------------------------------------------- barras de progreso --
// Cualquier elemento con [data-progreso-categoria] recalcula su ancho de barra
// de progreso leyendo localStorage (no viene del servidor porque el progreso
// es privado de cada navegador).

function pintarProgresoEnPagina() {
  if (!temaSlug) return;
  document.querySelectorAll('[data-progreso-categoria]').forEach((el) => {
    const categoria = JSON.parse(el.dataset.progresoCategoria);
    const pct = progreso.progresoDeCategoria(temaSlug, categoria);
    const fill = el.querySelector('.progress-bar__fill');
    const label = el.querySelector('[data-progreso-label]');
    if (fill) fill.style.width = `${pct}%`;
    if (label) label.textContent = `${pct}%`;
  });
  document.querySelectorAll('[data-tutorial-check]').forEach((el) => {
    const { categoria, tutorial } = el.dataset;
    if (progreso.estaTutorialCompleto(temaSlug, categoria, tutorial)) {
      el.closest('.lesson-row')?.classList.add('is-done');
    }
  });
  const totalEl = document.querySelector('[data-progreso-total]');
  if (totalEl) {
    const categorias = JSON.parse(totalEl.dataset.progresoTotal);
    const pct = progreso.progresoTotal(temaSlug, categorias);
    const fill = totalEl.querySelector('.progress-bar__fill');
    const label = totalEl.querySelector('[data-progreso-label]');
    if (fill) fill.style.width = `${pct}%`;
    if (label) label.textContent = `${pct}% completado`;
  }
}
pintarProgresoEnPagina();

// --------------------------------------------------------------------- init --

if (temaSlug) {
  initChatbot({ temaSlug, nombreTema: temaNombre });
}
