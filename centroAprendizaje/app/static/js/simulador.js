// simulador.js — Simulador de Compras: escenarios con decisiones ramificadas,
// explicación de cada respuesta con su fuente, puntaje, progreso y "atrás".
(function () {
  const raiz = document.getElementById('sim');
  if (!raiz) return;
  const S = JSON.parse(document.getElementById('sim-datos').textContent);
  const DOCS = JSON.parse(document.getElementById('sim-docs').textContent);
  const vista = document.getElementById('sim-vista');
  let esc = null;      // escenario actual
  let historial = [];  // [{id, elegida}]

  function e(s) { const d = document.createElement('div'); d.textContent = s == null ? '' : String(s); return d.innerHTML; }
  function pregunta(id) { return esc.preguntas.find((q) => q.id === id); }
  function siguiente(q, op) {
    if (op && op.va) return op.va;
    if (q.fin) return null;
    const i = esc.preguntas.indexOf(q);
    return esc.preguntas[i + 1] ? esc.preguntas[i + 1].id : null;
  }
  function fuentes(ids) {
    if (!ids || !ids.length) return '';
    return '<span class="sim-fuentes">¿De dónde surge? ' + ids.map((i) => DOCS[i]
      ? `<a href="${e(DOCS[i].url)}" target="_blank" rel="noopener">${e(DOCS[i].titulo.split(' — ')[0])}</a>` : e(i)).join(' · ') + '</span>';
  }

  function inicio() {
    esc = null; historial = [];
    vista.innerHTML = '<div class="sim-escenarios">' + S.escenarios.map((x) => `
      <button type="button" class="card sim-escenario" data-escenario="${e(x.slug)}">
        <span class="sim-escenario__icono">${x.icono}</span>
        <b>${e(x.titulo)}</b><span>${e(x.caso)}</span>
        <small>${x.preguntas.length} decisiones</small>
      </button>`).join('') + '</div>';
  }

  function render() {
    const respondidas = historial.filter((h) => h.elegida != null);
    const correctas = respondidas.filter((h) => pregunta(h.id).opciones[h.elegida].correcta).length;
    const actual = historial[historial.length - 1];
    const q = pregunta(actual.id);
    let html = `<div class="sim-barra"><button type="button" class="btn btn--ghost btn--sm" id="sim-salir">← Escenarios</button>
      <span class="sim-puntaje">✔ ${correctas} · ✖ ${respondidas.length - correctas}</span>
      <button type="button" class="btn btn--ghost btn--sm" id="sim-atras" ${historial.length <= 1 && actual.elegida == null ? 'disabled' : ''}>↶ Atrás</button></div>`;
    html += `<div class="sim-caso"><span class="sim-escenario__icono">${esc.icono}</span><div><b>${e(esc.titulo)}</b><p>${e(esc.caso)}</p><span class="alg-tipo alg-tipo--ejemplo">EJEMPLO DIDÁCTICO</span></div></div>`;
    html += `<div class="sim-progreso" aria-label="Progreso"><span style="width:${Math.round(100 * respondidas.length / esc.preguntas.length)}%"></span></div>`;
    html += `<div class="card sim-pregunta"><span class="sim-paso">Decisión ${historial.length}</span><h2>${e(q.pregunta)}</h2><div class="sim-opciones">`;
    q.opciones.forEach((op, i) => {
      let clase = 'sim-opcion';
      if (actual.elegida != null) {
        if (op.correcta) clase += ' sim-opcion--bien';
        else if (i === actual.elegida) clase += ' sim-opcion--mal';
      }
      html += `<button type="button" class="${clase}" data-op="${i}" ${actual.elegida != null ? 'disabled' : ''}>${e(op.texto)}</button>`;
    });
    html += '</div>';
    if (actual.elegida != null) {
      const op = q.opciones[actual.elegida];
      const buena = q.opciones.find((o) => o.correcta);
      html += `<div class="sim-explicacion ${op.correcta ? 'sim-explicacion--bien' : 'sim-explicacion--mal'}" role="status">
        <b>${op.correcta ? '✔ Correcto.' : '✖ No es así.'}</b> ${e(op.explicacion)}
        ${!op.correcta && buena ? `<p><b>La respuesta correcta:</b> ${e(buena.texto)}. ${e(buena.explicacion)}</p>` : ''}
        ${fuentes((op.fuentes || []).concat(!op.correcta && buena ? (buena.fuentes || []) : []).filter((v, i, a) => a.indexOf(v) === i))}
      </div>`;
      const sig = siguiente(q, op);
      html += `<div class="sim-acciones"><button type="button" class="btn btn--primary" id="sim-seguir">${sig ? 'Siguiente decisión →' : 'Ver resultado'}</button></div>`;
    }
    html += '</div>';
    vista.innerHTML = html;
  }

  function resultado() {
    const correctas = historial.filter((h) => h.elegida != null && pregunta(h.id).opciones[h.elegida].correcta).length;
    const total = historial.filter((h) => h.elegida != null).length;
    const repasar = historial.filter((h) => h.elegida != null && !pregunta(h.id).opciones[h.elegida].correcta)
      .map((h) => `<li>${e(pregunta(h.id).pregunta)}</li>`).join('');
    vista.innerHTML = `<div class="card sim-resultado">
      <div class="sim-resultado__nota">${correctas}/${total}</div>
      <h2>${correctas === total ? '¡Excelente! Todas las decisiones fueron correctas.' : 'Terminaste el escenario.'}</h2>
      ${repasar ? `<p>Para repasar:</p><ul>${repasar}</ul>` : ''}
      <div class="sim-acciones"><button type="button" class="btn btn--primary" id="sim-repetir">↺ Repetir</button>
      <button type="button" class="btn btn--ghost" id="sim-salir">Elegir otro escenario</button></div></div>`;
  }

  raiz.addEventListener('click', (ev) => {
    const t = ev.target.closest('button');
    if (!t) return;
    if (t.dataset.escenario) { esc = S.escenarios.find((x) => x.slug === t.dataset.escenario); historial = [{ id: esc.preguntas[0].id, elegida: null }]; render(); return; }
    if (t.dataset.op != null) { historial[historial.length - 1].elegida = Number(t.dataset.op); render(); return; }
    if (t.id === 'sim-seguir') {
      const actual = historial[historial.length - 1];
      const q = pregunta(actual.id);
      const sig = siguiente(q, q.opciones[actual.elegida]);
      if (sig) { historial.push({ id: sig, elegida: null }); render(); } else resultado();
      return;
    }
    if (t.id === 'sim-atras') {
      const actual = historial[historial.length - 1];
      if (actual.elegida != null) actual.elegida = null; else if (historial.length > 1) { historial.pop(); historial[historial.length - 1].elegida = null; }
      render(); return;
    }
    if (t.id === 'sim-repetir') { historial = [{ id: esc.preguntas[0].id, elegida: null }]; render(); return; }
    if (t.id === 'sim-salir') { inicio(); }
  });

  // Se puede entrar directo a un escenario con ?escenario=slug (desde otros módulos).
  const pedido = new URLSearchParams(location.search).get('escenario');
  const elegido = pedido && S.escenarios.find((x) => x.slug === pedido);
  if (elegido) { esc = elegido; historial = [{ id: esc.preguntas[0].id, elegida: null }]; render(); } else inicio();
})();
