// views.js — una función de render por ruta. Reciben el elemento <main> donde
// montar el contenido y, si corresponde, los parámetros de la ruta.
// No hay lógica de router ni de progreso acá: solo arman HTML/DOM a partir de
// content.js y de lo que progress.js reporta.

import { MODULES, GLOSSARY, SITUATIONS, TASKS, QUICKSTART, SYSTEM_INFO } from '../../content/content.js';
import * as progreso from './progress.js';
import { renderizarQuiz } from './quiz.js';

const IMG_BASE = 'assets/img/';

function e(texto) {
  const div = document.createElement('div');
  div.textContent = texto == null ? '' : String(texto);
  return div.innerHTML;
}

function badgeDificultad(dificultad) {
  const mapa = { basico: ['🟢', 'Básico'], intermedio: ['🟡', 'Intermedio'], avanzado: ['🔴', 'Avanzado'] };
  const [icono, texto] = mapa[dificultad] || ['⚪', dificultad];
  return `<span class="badge badge--${dificultad}">${icono} ${texto}</span>`;
}

// ------------------------------------------------------------ diagramas ---
// Esquemas ilustrativos para pantallas sin captura real disponible (nunca se
// presentan como si fueran una captura — ver diagram__badge). Si el esquema
// necesita mostrar una fila "tipo paciente", se usa un `redacted-bar` en vez
// de un dato inventado, igual que en el manual publicado.

function celdaDiagrama(valor) {
  return valor === '◼' ? '<span class="redacted-bar" aria-hidden="true"></span>' : e(valor);
}

function renderDiagrama(d) {
  let cuerpo = '';
  if (d.variant === 'cards') {
    cuerpo = `<div class="diagram-cards">${d.items
      .map((it) => `<div class="diagram-card"><div class="diagram-card__value">${e(it.value)}</div><div class="diagram-card__label">${e(it.label)}</div></div>`)
      .join('')}</div>`;
  } else if (d.variant === 'tabs') {
    cuerpo = `<div class="diagram-tabs">${d.tabs
      .map((t, i) => `<span class="diagram-tab ${i === d.active ? 'is-active' : ''}">${e(t)}</span>`)
      .join('')}</div>`;
  } else if (d.variant === 'list') {
    cuerpo = `<div class="diagram-list">${d.items
      .map(
        (it) => `<div class="diagram-list-item">
          <span class="diagram-list-item__label">${e(it.label)}</span>
          ${it.hint ? `<span class="badge badge--${it.tone || 'neutral'}">${e(it.hint)}</span>` : ''}
        </div>`
      )
      .join('')}</div>`;
  } else if (d.variant === 'table') {
    cuerpo = `<div class="table-wrap"><table class="data-table">
      <thead><tr>${d.columns.map((c) => `<th>${e(c)}</th>`).join('')}</tr></thead>
      <tbody>${d.rows.map((fila) => `<tr>${fila.map((celda) => `<td>${celdaDiagrama(celda)}</td>`).join('')}</tr>`).join('')}</tbody>
    </table></div>`;
  }
  return `<div class="diagram">
    <div class="diagram__badge">🖼 Esquema ilustrativo — no es una captura real</div>
    ${d.title ? `<div class="diagram__title">${e(d.title)}</div>` : ''}
    ${cuerpo}
    ${d.note ? `<div class="diagram__note">${e(d.note)}</div>` : ''}
  </div>`;
}

function hallarModulo(id) {
  return MODULES.find((m) => m.id === id);
}
function hallarLeccion(moduleId, lessonId) {
  const modulo = hallarModulo(moduleId);
  if (!modulo) return null;
  const leccion = modulo.lessons.find((l) => l.id === lessonId);
  return leccion ? { modulo, leccion } : null;
}

function aplanarLecciones() {
  const lista = [];
  for (const modulo of MODULES) {
    for (const leccion of modulo.lessons) {
      lista.push({ moduleId: modulo.id, moduleTitle: modulo.title, lessonId: leccion.id, lessonTitle: leccion.title });
    }
  }
  return lista;
}

function breadcrumbs(items) {
  const partes = items.map((it, i) => {
    const esUltimo = i === items.length - 1;
    const contenido = esUltimo || !it.href ? e(it.label) : `<a href="${it.href}">${e(it.label)}</a>`;
    return i === 0 ? contenido : `<span class="sep">/</span>${contenido}`;
  });
  return `<nav class="breadcrumbs" aria-label="Ruta de navegación">${partes.join('')}</nav>`;
}

// ---------------------------------------------------------------- bloques --

function renderBloque(bloque) {
  switch (bloque.type) {
    case 'text':
      return `<p>${e(bloque.text)}</p>`;
    case 'prereq':
      return `<p class="step__meta-row"><b>Antes de empezar, necesitás:</b></p><ul class="prereq-list">${bloque.items
        .map((it) => `<li>${e(it)}</li>`)
        .join('')}</ul>`;
    case 'concepts':
      return `<div class="concepts-list">${bloque.items
        .map((it) => `<div class="concepts-list__item"><span class="concepts-list__term">${e(it.term)}:</span> ${e(it.def)}</div>`)
        .join('')}</div>`;
    case 'tip':
      return `<div class="callout callout--tip"><span class="callout__icon">💡</span><div>${e(bloque.text)}</div></div>`;
    case 'warning':
      return `<div class="callout callout--warning"><span class="callout__icon">⚠️</span><div>${e(bloque.text)}</div></div>`;
    case 'practice':
      return `<div class="callout callout--practice"><span class="callout__icon">🧪</span><div><b>Probá vos mismo:</b> ${e(bloque.text)}</div></div>`;
    case 'diagram':
      return renderDiagrama(bloque);
    case 'step':
      return `<div class="step">
        <div class="step__number">${bloque.number}</div>
        <div class="step__body">
          <p class="step__explanation">${e(bloque.explanation)}</p>
          ${bloque.image ? `
            <button type="button" class="step__image lightbox-trigger" data-src="${IMG_BASE}${e(bloque.image)}" data-alt="${e(bloque.alt)}">
              <img src="${IMG_BASE}${e(bloque.image)}" alt="${e(bloque.alt)}" loading="lazy" />
            </button>
            <div class="step__caption">${e(bloque.caption)} — clic para ampliar</div>
          ` : bloque.diagram ? `
            ${renderDiagrama(bloque.diagram)}
          ` : ''}
          <div class="step__meta">
            ${bloque.lookFor ? `<div class="step__meta-row"><b>Qué mirar:</b> ${e(bloque.lookFor)}</div>` : ''}
            ${bloque.doThis ? `<div class="step__meta-row"><b>Qué hacer:</b> ${e(bloque.doThis)}</div>` : ''}
          </div>
        </div>
      </div>`;
    default:
      return '';
  }
}

// ------------------------------------------------------------------ home --

export function vistaHome(main) {
  const total = progreso.progresoTotal(MODULES);
  main.innerHTML = `
    <div class="hero">
      <div class="hero__eyebrow">${e(SYSTEM_INFO.name)} · Campus de capacitación</div>
      <h1>${e(SYSTEM_INFO.fullName)}</h1>
      <p class="hero__desc">${e(SYSTEM_INFO.description)}</p>
    </div>

    <div class="section">
      <div class="progress-bar"><div class="progress-bar__fill" style="width:${total}%"></div></div>
      <div class="progress-ring-label">Progreso general: ${total}%</div>
    </div>

    <div class="card-grid">
      <a class="card card-link" href="#/quickstart">
        <span class="home-card__icon">🚀</span>
        <div class="home-card__title">Empezar desde cero</div>
        <div class="home-card__desc">Ruta guiada de 15 minutos para conocer lo básico.</div>
      </a>
      <a class="card card-link" href="#/modulos">
        <span class="home-card__icon">🧭</span>
        <div class="home-card__title">Explorar módulos</div>
        <div class="home-card__desc">Recorré el contenido completo módulo por módulo.</div>
      </a>
      <a class="card card-link" href="#/tareas">
        <span class="home-card__icon">🔎</span>
        <div class="home-card__title">Quiero hacer algo</div>
        <div class="home-card__desc">Buscá por tarea: "¿Cómo busco...?", "¿Cómo cargo...?".</div>
      </a>
      <a class="card card-link" href="#/problemas">
        <span class="home-card__icon">🩹</span>
        <div class="home-card__title">Tengo un problema</div>
        <div class="home-card__desc">Situaciones frecuentes y cómo resolverlas.</div>
      </a>
      <a class="card card-link" href="#/glosario">
        <span class="home-card__icon">📖</span>
        <div class="home-card__title">Glosario</div>
        <div class="home-card__desc">Términos del sistema, explicados en simple.</div>
      </a>
      <a class="card card-link" href="#/progreso">
        <span class="home-card__icon">📊</span>
        <div class="home-card__title">Mi progreso</div>
        <div class="home-card__desc">Lecciones completadas y resultados de quizzes.</div>
      </a>
    </div>

    <div class="section">
      <h2 class="section__title">Antes de empezar</h2>
      ${SYSTEM_INFO.recommendations.map((r) => `<div class="callout callout--warning"><span class="callout__icon">⚠️</span><div>${e(r)}</div></div>`).join('')}
    </div>
  `;
}

// ------------------------------------------------------------- quickstart --

export function vistaQuickstart(main) {
  main.innerHTML = `
    ${breadcrumbs([{ label: 'Inicio', href: '#/' }, { label: QUICKSTART.title }])}
    <div class="hero">
      <div class="hero__eyebrow">Ruta guiada</div>
      <h1>${e(QUICKSTART.title)}</h1>
      <p class="hero__desc">${e(QUICKSTART.intro)}</p>
    </div>
    <div class="lesson-list">
      ${QUICKSTART.steps
        .map((paso) => {
          let href = '#/';
          let hecho = false;
          if (paso.moduleId && paso.lessonId) {
            href = `#/modulo/${paso.moduleId}/leccion/${paso.lessonId}`;
            hecho = progreso.estaLeccionCompleta(paso.moduleId, paso.lessonId);
          } else if (paso.situationId) {
            href = '#/problemas';
          }
          return `<a class="lesson-row ${hecho ? 'is-done' : ''}" href="${href}">
            <span class="lesson-row__check" aria-hidden="true">✓</span>
            <span class="sr-only">${hecho ? 'Completado. ' : ''}</span>
            <span class="lesson-row__title">${paso.step}. ${e(paso.title)}</span>
          </a>`;
        })
        .join('')}
    </div>
    <div class="callout callout--tip"><span class="callout__icon">💡</span><div>${e(QUICKSTART.outro)}</div></div>
  `;
}

// --------------------------------------------------------------- módulos --

const FILTROS_DIFICULTAD = [
  { id: 'todas', label: 'Todas' },
  { id: 'basico', label: '🟢 Básico' },
  { id: 'intermedio', label: '🟡 Intermedio' },
  { id: 'avanzado', label: '🔴 Avanzado' },
];

function tarjetasModulos(lista) {
  return lista.length
    ? lista
        .map((m) => {
          const pct = progreso.progresoDeModulo(m);
          return `<a class="card card-link module-card" href="#/modulo/${m.id}">
            <div class="module-card__head"><span class="module-card__icon">${m.icon}</span><span class="module-card__title">${e(m.title)}</span></div>
            <div class="module-card__summary">${e(m.summary)}</div>
            <div class="module-card__meta">${badgeDificultad(m.difficulty)} <span>${m.lessons.length} lecciones</span></div>
            <div class="progress-bar progress-bar--sm" style="margin-top:12px"><div class="progress-bar__fill" style="width:${pct}%"></div></div>
          </a>`;
        })
        .join('')
    : `<div class="empty-state"><div class="empty-state__icon">🧭</div>Ningún módulo tiene esa dificultad.</div>`;
}

export function vistaModulos(main) {
  main.innerHTML = `
    ${breadcrumbs([{ label: 'Inicio', href: '#/' }, { label: 'Módulos' }])}
    <div class="hero"><h1>Módulos</h1><p class="hero__desc">Todo el contenido de TIMBÓ, organizado como en el sistema real.</p></div>
    <div class="module-filter-bar" role="group" aria-label="Filtrar módulos por dificultad">
      ${FILTROS_DIFICULTAD.map(
        (f) => `<button type="button" class="filter-chip ${f.id === 'todas' ? 'is-active' : ''}" data-dificultad="${f.id}">${f.label}</button>`
      ).join('')}
    </div>
    <div class="card-grid" id="grid-modulos">${tarjetasModulos(MODULES)}</div>
  `;

  const barra = main.querySelector('.module-filter-bar');
  const grid = main.querySelector('#grid-modulos');
  barra.addEventListener('click', (ev) => {
    const boton = ev.target.closest('.filter-chip');
    if (!boton) return;
    barra.querySelectorAll('.filter-chip').forEach((b) => b.classList.toggle('is-active', b === boton));
    const { dificultad } = boton.dataset;
    grid.innerHTML = tarjetasModulos(dificultad === 'todas' ? MODULES : MODULES.filter((m) => m.difficulty === dificultad));
  });
}

export function vistaModulo(main, { id }) {
  const modulo = hallarModulo(id);
  if (!modulo) return vistaNoEncontrada(main);
  const pct = progreso.progresoDeModulo(modulo);
  main.innerHTML = `
    ${breadcrumbs([{ label: 'Inicio', href: '#/' }, { label: 'Módulos', href: '#/modulos' }, { label: modulo.title }])}
    <div class="hero">
      <div class="hero__eyebrow">${modulo.icon} Módulo</div>
      <h1>${e(modulo.title)}</h1>
      <p class="hero__desc">${e(modulo.summary)}</p>
      <p class="text-muted"><b>Para quién:</b> ${e(modulo.audience)}</p>
      ${badgeDificultad(modulo.difficulty)}
    </div>
    <div class="section">
      <div class="progress-bar"><div class="progress-bar__fill" style="width:${pct}%"></div></div>
      <div class="progress-ring-label">${pct}% completado</div>
    </div>
    <div class="section">
      <h2 class="section__title">Lecciones</h2>
      <div class="lesson-list">
        ${modulo.lessons
          .map((l) => {
            const hecho = progreso.estaLeccionCompleta(modulo.id, l.id);
            return `<a class="lesson-row ${hecho ? 'is-done' : ''}" href="#/modulo/${modulo.id}/leccion/${l.id}">
              <span class="lesson-row__check" aria-hidden="true">✓</span>
              <span class="sr-only">${hecho ? 'Completada. ' : ''}</span>
              <span class="lesson-row__title">${e(l.title)}</span>
              <span class="lesson-row__meta">${l.minutes} min · ${badgeDificultad(l.difficulty)}</span>
            </a>`;
          })
          .join('')}
      </div>
    </div>
  `;
}

// --------------------------------------------------------------- lección --

export function vistaLeccion(main, { id, lessonId }) {
  const hallazgo = hallarLeccion(id, lessonId);
  if (!hallazgo) return vistaNoEncontrada(main);
  const { modulo, leccion } = hallazgo;

  const plano = aplanarLecciones();
  const indiceActual = plano.findIndex((x) => x.moduleId === id && x.lessonId === lessonId);
  const anterior = plano[indiceActual - 1];
  const siguiente = plano[indiceActual + 1];

  const hecha = progreso.estaLeccionCompleta(id, lessonId);
  const resultadoQuiz = progreso.obtenerResultadoQuiz(id, lessonId);
  const tieneQuiz = leccion.quiz && leccion.quiz.some((p) => p.type !== 'checklist');

  main.innerHTML = `
    ${breadcrumbs([
      { label: 'Inicio', href: '#/' },
      { label: 'Módulos', href: '#/modulos' },
      { label: modulo.title, href: `#/modulo/${modulo.id}` },
      { label: leccion.title },
    ])}
    <div class="hero">
      <div class="hero__eyebrow">${modulo.icon} ${e(modulo.title)}</div>
      <h1>${e(leccion.title)}</h1>
      <div>${badgeDificultad(leccion.difficulty)} <span class="badge badge--neutral">⏱ ${leccion.minutes} min</span></div>
    </div>

    <div class="section" id="bloques-leccion">
      ${leccion.blocks.map(renderBloque).join('')}
    </div>

    ${leccion.quiz && leccion.quiz.length ? `
      <div class="section">
        <h2 class="section__title">✅ Comprobá lo aprendido</h2>
        <div class="quiz-panel" id="quiz-mount"></div>
      </div>
    ` : ''}

    <div class="lesson-complete-bar">
      <button type="button" class="checkbox-pill js-toggle-leccion ${hecha ? 'is-done' : ''}" data-module="${modulo.id}" data-lesson="${leccion.id}">
        <span>${hecha ? '✓' : '○'}</span> ${hecha ? 'Lección completada' : 'Marcar como completada'}
      </button>
      ${resultadoQuiz ? `<span class="text-muted">Último resultado del quiz: ${resultadoQuiz.correctas}/${resultadoQuiz.total}</span>` : ''}
    </div>

    <div class="lesson-nav">
      ${anterior ? `<a class="btn btn--ghost" href="#/modulo/${anterior.moduleId}/leccion/${anterior.lessonId}">← ${e(anterior.lessonTitle)}</a>` : '<span></span>'}
      ${siguiente ? `<a class="btn btn--primary" href="#/modulo/${siguiente.moduleId}/leccion/${siguiente.lessonId}">${e(siguiente.lessonTitle)} →</a>` : `<a class="btn btn--primary" href="#/modulo/${modulo.id}">Volver al módulo</a>`}
    </div>
  `;

  if (tieneQuiz || (leccion.quiz && leccion.quiz.length)) {
    const mount = main.querySelector('#quiz-mount');
    if (mount) {
      renderizarQuiz(mount, leccion.quiz, (correctas, totalEval) => {
        if (totalEval > 0) progreso.guardarResultadoQuiz(modulo.id, leccion.id, correctas, totalEval);
      });
    }
  }
}

// --------------------------------------------------------------- tareas --

function listaTareasHTML(items) {
  return items.length
    ? items
        .map(
          (t) => `<a class="lesson-row" href="#/modulo/${t.moduleId}/leccion/${t.lessonId}">
            <span class="lesson-row__title">${e(t.question)}</span>
            <span class="lesson-row__meta">${badgeDificultad(t.level)} · ${t.minutes} min</span>
          </a>`
        )
        .join('')
    : `<div class="empty-state"><div class="empty-state__icon">🔎</div>No encontramos una tarea que coincida. Probá con otras palabras.</div>`;
}

export function vistaTareas(main) {
  main.innerHTML = `
    ${breadcrumbs([{ label: 'Inicio', href: '#/' }, { label: 'Quiero hacer...' }])}
    <div class="hero"><h1>¿Qué querés hacer?</h1><p class="hero__desc">Elegí la tarea que necesitás y te llevamos directo al procedimiento.</p></div>
    <div class="input-wrap" style="margin-bottom:18px;max-width:480px">
      <span class="input-wrap__icon">🔎</span>
      <input class="input" id="filtro-tareas" type="text" placeholder="Filtrar tareas..." />
    </div>
    <div class="lesson-list" id="lista-tareas">${listaTareasHTML(TASKS)}</div>
  `;

  const input = main.querySelector('#filtro-tareas');
  const lista = main.querySelector('#lista-tareas');
  input.addEventListener('input', () => {
    const query = input.value.trim().toLowerCase();
    const items = query
      ? TASKS.filter((t) => `${t.question} ${(t.keywords || []).join(' ')}`.toLowerCase().includes(query))
      : TASKS;
    lista.innerHTML = listaTareasHTML(items);
  });
  input.focus();
}

// ------------------------------------------------------------- problemas --

export function vistaProblemas(main) {
  main.innerHTML = `
    ${breadcrumbs([{ label: 'Inicio', href: '#/' }, { label: 'Tengo un problema' }])}
    <div class="hero"><h1>¿Tenés un problema?</h1><p class="hero__desc">Elegí la situación que te pasó. Si algo no está verificado todavía, te lo decimos con claridad.</p></div>
    ${SITUATIONS.map((s, i) => `
      <div class="card situation-card">
        <div class="situation-card__head">
          <span class="situation-card__title">${e(s.situation)}</span>
          <span class="badge badge--${s.verified ? 'verified' : 'unverified'}">${s.verified ? '✓ Verificado' : '🟡 No verificado'}</span>
        </div>
        <div class="situation-card__desc">${e(s.description)}</div>
        <div class="situation-card__label">Causa</div>
        <div class="situation-card__text">${e(s.cause)}</div>
        <div class="situation-card__label">Qué hacer</div>
        <div class="situation-card__text">${e(s.solution)}</div>
        ${s.goesTo ? `<div style="margin-top:12px"><a class="btn btn--ghost btn--sm" href="#/modulo/${s.goesTo.moduleId}/leccion/${s.goesTo.lessonId}">Ir al procedimiento →</a></div>` : ''}
      </div>
    `).join('')}
  `;
}

// -------------------------------------------------------------- glosario --

function letraDeTermino(term) {
  const letra = term.match(/[A-ZÁÉÍÓÚÑ]/i);
  return letra ? letra[0].toUpperCase() : '#';
}

export function vistaGlosario(main) {
  const ordenado = GLOSSARY.slice().sort((a, b) => a.term.localeCompare(b.term, 'es'));
  const letras = [...new Set(ordenado.map((t) => letraDeTermino(t.term)))];

  main.innerHTML = `
    ${breadcrumbs([{ label: 'Inicio', href: '#/' }, { label: 'Glosario' }])}
    <div class="hero"><h1>Glosario</h1><p class="hero__desc">Términos que vas a encontrar en todo TIMBÓ, ordenados de la A a la Z.</p></div>
    <nav class="glossary-jump" aria-label="Ir a la letra">
      ${letras.map((l) => `<a href="#letra-${l}">${l}</a>`).join('')}
    </nav>
    <div class="glossary-grid">
      ${ordenado
        .map((t, i) => {
          const esPrimeraDeLetra = i === 0 || letraDeTermino(ordenado[i - 1].term) !== letraDeTermino(t.term);
          return `<div class="card glossary-item"${esPrimeraDeLetra ? ` id="letra-${letraDeTermino(t.term)}"` : ''}>
            <div class="glossary-item__term">${e(t.term)}</div>
            <div class="glossary-item__def">${e(t.definition)}</div>
            <div class="glossary-item__meta">${e(t.module)} — ${e(t.usage)}</div>
          </div>`;
        })
        .join('')}
    </div>
  `;
}

// -------------------------------------------------------------- progreso --

export function vistaProgreso(main) {
  const total = progreso.progresoTotal(MODULES);
  const completadas = progreso.leccionesCompletadas(MODULES);

  main.innerHTML = `
    ${breadcrumbs([{ label: 'Inicio', href: '#/' }, { label: 'Mi progreso' }])}
    <div class="hero"><h1>Mi progreso</h1><p class="hero__desc">Guardado en este navegador — no se comparte con nadie más.</p></div>

    <div class="section">
      <div class="progress-bar"><div class="progress-bar__fill" style="width:${total}%"></div></div>
      <div class="progress-ring-label">${total}% del contenido completado</div>
    </div>

    <div class="section">
      <h2 class="section__title">Por módulo</h2>
      ${MODULES.map((m) => {
        const pct = progreso.progresoDeModulo(m);
        return `<div style="margin-bottom:14px">
          <div style="display:flex;justify-content:space-between;font-size:13.5px;margin-bottom:4px">
            <span>${m.icon} ${e(m.title)}</span><span class="text-muted">${pct}%</span>
          </div>
          <div class="progress-bar progress-bar--sm"><div class="progress-bar__fill" style="width:${pct}%"></div></div>
        </div>`;
      }).join('')}
    </div>

    <div class="section">
      <h2 class="section__title">Lecciones completadas</h2>
      ${completadas.length
        ? `<div class="lesson-list">${completadas
            .map(
              (c) => `<a class="lesson-row is-done" href="#/modulo/${c.moduleId}/leccion/${c.lessonId}">
                <span class="lesson-row__check" aria-hidden="true">✓</span>
                <span class="lesson-row__title">${e(c.lessonTitle)}</span>
                <span class="lesson-row__meta">${e(c.moduleTitle)}</span>
              </a>`
            )
            .join('')}</div>`
        : `<div class="empty-state"><div class="empty-state__icon">📭</div>Todavía no completaste ninguna lección.</div>`}
    </div>

    <div class="section">
      <button type="button" class="btn btn--subtle" id="btn-reiniciar-progreso">Reiniciar todo mi progreso</button>
    </div>
  `;

  main.querySelector('#btn-reiniciar-progreso').addEventListener('click', () => {
    progreso.reiniciarProgreso();
    vistaProgreso(main);
    window.dispatchEvent(new CustomEvent('timbo:toast', { detail: 'Progreso reiniciado.' }));
    window.dispatchEvent(new CustomEvent('timbo:progreso-cambio'));
  });
}

// -------------------------------------------------------------- 404 -------

export function vistaNoEncontrada(main) {
  main.innerHTML = `
    <div class="empty-state">
      <div class="empty-state__icon">🧭</div>
      <p>No encontramos esa página.</p>
      <a class="btn btn--primary" href="#/">Volver al inicio</a>
    </div>
  `;
}
