// algoritmo.js — "¿Qué camino sigue una compra?": recorrido interactivo con
// decisiones, ramas y una ficha por etapa. Los datos vienen de
// app/recursos/algoritmo.json (embebidos en la página como JSON).
(function () {
  const raiz = document.getElementById('alg');
  if (!raiz) return;
  const A = JSON.parse(document.getElementById('alg-datos').textContent);
  const DOCS = JSON.parse(document.getElementById('alg-docs').textContent);
  const N = A.nodos;

  const SISTEMAS = {
    expediente: ['📁', 'Expediente electrónico'],
    compras: ['🛒', 'TIMBÓ Compras'],
    decision: ['◆', 'Decisión o control'],
    externo: ['↗', 'Externo o complementario'],
    organismo: ['🏛️', 'Otro organismo'],
  };
  const TIPOS_FUENTE = { norma: 'NORMA', procedimiento: 'PROCEDIMIENTO OPERATIVO', ejemplo: 'EJEMPLO DIDÁCTICO' };

  const camino = document.getElementById('alg-camino');
  const ficha = document.getElementById('alg-ficha');
  const completo = document.getElementById('alg-completo');
  const banner = document.getElementById('alg-ejemplo');
  let pasos = [A.inicio];
  let ejemplo = null;

  function esc(s) { const d = document.createElement('div'); d.textContent = s == null ? '' : String(s); return d.innerHTML; }

  // Recorrido: desde el nodo de rama se agregan todos sus pasos hasta el final.
  function expandir(lista) {
    const out = [];
    lista.forEach((id) => {
      out.push(id);
      const n = N[id];
      if (n && n.pasos) n.pasos.forEach((p) => out.push(p));
    });
    return out;
  }

  function tarjeta(id, opciones) {
    const n = N[id];
    const s = SISTEMAS[n.sistema] || SISTEMAS.externo;
    const clases = ['alg-nodo', 'alg-nodo--' + n.tipo, 'alg-sis--' + n.sistema];
    if (n.estado === 'pendiente') clases.push('alg-nodo--pendiente');
    let html = `<div class="${clases.join(' ')}" data-nodo="${esc(id)}" tabindex="0" role="button" aria-label="Ver ficha: ${esc(n.titulo)}">`;
    html += `<div class="alg-nodo__forma">`;
    if (n.rama) html += `<span class="alg-nodo__rama">Rama ${esc(n.rama)}</span>`;
    html += `<span class="alg-nodo__titulo">${esc(n.titulo)}</span>`;
    html += `<span class="alg-nodo__meta"><span class="alg-chip">${s[0]} ${esc(s[1])}</span>`;
    if (n.responsable) html += `<span class="alg-chip">👤 ${esc(n.responsable)}</span>`;
    if (n.docs_cortos) html += `<span class="alg-chip">📄 ${esc(n.docs_cortos)}</span>`;
    html += `</span>`;
    if (n.alerta) html += `<span class="alg-alerta">⚠️ ${esc(n.alerta)}</span>`;
    html += `<span class="alg-nodo__ver">Ver ficha →</span></div></div>`;
    if (opciones) html += opciones;
    return html;
  }

  function opcionesDe(id) {
    const n = N[id];
    let html = '<div class="alg-opciones">';
    if (n.pregunta) html += `<p class="alg-pregunta">${esc(n.pregunta)}</p>`;
    if (n.muestra_montos) {
      html += `<div class="alg-montos"><table><thead><tr><th>Monto estimado (${esc(A.montos.vigencia)})</th><th>Procedimiento</th><th>Aprueba</th></tr></thead><tbody>`;
      A.montos.tramos.forEach((t) => { html += `<tr><td>${esc(t.hasta)}</td><td>${esc(t.proc)}</td><td>${esc(t.aprueba)}</td></tr>`; });
      html += `</tbody></table><p>📌 ${esc(A.montos.base)}. ${esc(A.montos.aviso)}</p></div>`;
    }
    if (n.opciones_ejemplo) {
      Object.entries(A.ejemplos).forEach(([clave, e]) => {
        html += `<button type="button" class="alg-opcion" data-ejemplo="${esc(clave)}">${e.icono} ${esc(e.nombre)}</button>`;
      });
    } else {
      (n.opciones || []).forEach((o) => {
        html += `<button type="button" class="alg-opcion" data-va="${esc(o.va)}">${esc(o.texto)}${o.nota ? ` <small>${esc(o.nota)}</small>` : ''}</button>`;
      });
    }
    return html + '</div>';
  }

  function render() {
    const lista = expandir(pasos);
    const ultimo = lista[lista.length - 1];
    camino.innerHTML = lista.map((id, i) => {
      const n = N[id];
      const esUltimo = i === lista.length - 1;
      const abierto = esUltimo && (n.tipo === 'decision' || n.tipo === 'inicio') && !(n.tipo === 'inicio' && ejemplo);
      // Debajo de cada decisión ya respondida, qué se eligió.
      let elegido = '';
      if (!abierto && n.tipo === 'decision') {
        const op = (n.opciones || []).find((o) => o.va === lista[i + 1]);
        if (op) elegido = `<span class="alg-elegido">Respuesta: <b>${esc(op.texto)}</b></span>`;
      } else if (!abierto && n.tipo === 'inicio' && ejemplo) {
        elegido = `<span class="alg-elegido">${A.ejemplos[ejemplo].icono} <b>${esc(A.ejemplos[ejemplo].nombre)}</b></span>`;
      }
      return `<div class="alg-paso">${tarjeta(id, abierto ? opcionesDe(id) : '')}${elegido}</div>`;
    }).join('<div class="alg-flecha" aria-hidden="true"></div>');
    document.getElementById('alg-atras').disabled = pasos.length <= 1 && !ejemplo;
    if (N[ultimo].tipo === 'fin') {
      camino.insertAdjacentHTML('beforeend', '<div class="alg-final">✔ Recorrido completo. Tocá cualquier etapa para ver su ficha.</div>');
    }
    banner.hidden = !ejemplo;
    if (ejemplo) banner.innerHTML = `<b>${A.ejemplos[ejemplo].icono} Ejemplo didáctico:</b> ${esc(A.ejemplos[ejemplo].texto)} <span class="alg-tipo alg-tipo--ejemplo">EJEMPLO DIDÁCTICO</span>`;
  }

  // Conexiones: término del diccionario, escenario del simulador y checklist.
  const TERMINOS = {
    'c-pliego': 'PBCP', 'c-aprobacion': 'Supervisor', 'c-acto': 'Autoridad competente', 'c-tcp': 'Sistema de Información Normativa',
    'c-consultas': 'Circular', 'c-ofertas': 'Oferta presentada', 'c-apertura': 'Apertura', 'c-evaluacion': 'Evaluación',
    'c-preadjudicacion': 'Preadjudicación', 'c-impugnaciones': 'Impugnación', 'c-adjudicacion': 'Adjudicación',
    'fin-contractual': 'Orden de compra', 'd-publicacion': 'Publicación', 'c-invitacion': 'Convocatoria',
    'a-directa': 'Compra directa', 'a-cd01': 'Compra directa', 'b-urgencia': 'Contratación directa por excepción',
    'b-desierto': 'Contratación directa por excepción', 'b-otras': 'Contratación directa por excepción',
    'c-privada': 'Licitación privada', 'd-publica': 'Licitación pública', 'necesidad': 'Requerimiento',
    'e-convenio': 'Convenio marco', 'e-subasta': 'Subasta', 'e-etapa-multiple': 'etapa múltiple', 'd-urc-pliego': 'URC', 'd-urc-preadj': 'URC',
  };
  function procedimientoDe(id) {
    if (/^a-/.test(id)) return 'A';
    if (/^b-/.test(id)) return 'B';
    if (/^d-/.test(id) && id !== 'd-excepcion' && id !== 'd-modalidad' && id !== 'd-monto') return 'D';
    const ruta = expandir(pasos);
    if (ruta.includes('d-publica')) return 'D';
    if (ruta.includes('c-privada')) return 'C';
    if (ruta.some((x) => /^b-/.test(x))) return 'B';
    if (ruta.includes('a-directa')) return 'A';
    return /^c-/.test(id) ? 'C' : null;
  }
  const ESCENARIO = { A: 'oficina', B: 'excepcion', C: 'insumos', D: 'equipamiento' };
  function conexiones(id) {
    const termino = TERMINOS[id];
    const proc = procedimientoDe(id);
    let html = '<h3>Seguí por acá</h3><div class="alg-conexiones">';
    if (termino) html += `<a class="btn btn--ghost btn--sm" href="${raiz.dataset.urlDic}?q=${encodeURIComponent(termino)}">📖 "${esc(termino)}" en el diccionario</a>`;
    if (proc && raiz.dataset.urlSim) html += `<a class="btn btn--ghost btn--sm" href="${raiz.dataset.urlSim}?escenario=${ESCENARIO[proc]}">🎯 Practicar en el simulador</a>`;
    if (proc && raiz.dataset.urlCheck) html += `<a class="btn btn--ghost btn--sm" href="${raiz.dataset.urlCheck}?procedimiento=${proc}">✅ Checklist del procedimiento ${proc}</a>`;
    return html + '</div>';
  }

  function abrirFicha(id) {
    const n = N[id];
    const f = n.ficha || {};
    const s = SISTEMAS[n.sistema] || SISTEMAS.externo;
    const filas = [
      ['Qué sucede', f.que], ['Para qué sirve', f.para], ['Quién interviene', f.quien], ['Sistema', f.sistema],
      ['Documentación', f.docs], ['Qué verificar', f.verificar], ['Qué sigue', f.despues],
    ].filter((x) => x[1]);
    let html = `<div class="alg-ficha__head alg-sis--${esc(n.sistema)}"><span class="alg-chip">${s[0]} ${esc(s[1])}</span>`;
    if (n.estado === 'pendiente') html += ' <span class="rec-estado rec-estado--pendiente">⏳ Pendiente de confirmar</span>';
    html += `<h2>${esc(n.titulo)}</h2></div><dl class="alg-ficha__campos">`;
    filas.forEach(([t, v]) => { html += `<dt>${esc(t)}</dt><dd>${esc(v)}</dd>`; });
    html += '</dl><h3>¿De dónde surge esta información?</h3><ul class="alg-ficha__fuentes">';
    (f.fuentes || []).forEach((r) => {
      const d = DOCS[r.id];
      const tipo = TIPOS_FUENTE[r.tipo] || 'NORMA';
      html += `<li><span class="alg-tipo alg-tipo--${esc(r.tipo || 'norma')}">${tipo}</span> `;
      html += d ? `<a href="${esc(d.url)}" target="_blank" rel="noopener">${esc(d.titulo)}</a>` : esc(r.id);
      if (r.punto) html += ` <span class="text-muted">— ${esc(r.punto)}</span>`;
      if (d && d.vigencia) html += ` <span class="text-muted">· ${esc(d.vigencia)}</span>`;
      html += '</li>';
    });
    html += '</ul>' + conexiones(id);
    ficha.querySelector('.alg-ficha__cuerpo').innerHTML = html;
    ficha.hidden = false;
    ficha.querySelector('.alg-ficha__cerrar').focus();
  }

  function renderCompleto() {
    let html = '<div class="alg-mapa">';
    html += `<div class="alg-mapa__tronco">${['necesidad', 'd-excepcion', 'd-modalidad', 'd-monto'].map((id) => `<button type="button" class="alg-mini alg-mini--${N[id].tipo} alg-sis--${N[id].sistema}" data-nodo="${id}">${esc(N[id].titulo)}</button>`).join('<span class="alg-mini-flecha">↓</span>')}</div>`;
    html += '<div class="alg-mapa__ramas">';
    A.ramas.forEach((r) => {
      const inicios = r.nodo ? [r.nodo] : r.nodos;
      html += `<div class="alg-mapa__rama alg-sis--${r.sistema}"><div class="alg-mapa__letra">${esc(r.letra)}</div><h3>${esc(r.nombre)}</h3>`;
      inicios.forEach((id) => {
        html += `<button type="button" class="alg-mini alg-mini--accion alg-sis--${N[id].sistema}" data-nodo="${id}"><b>${esc(N[id].titulo)}</b></button>`;
        if (r.nodo) (N[id].pasos || []).forEach((p) => {
          html += `<span class="alg-mini-flecha">↓</span><button type="button" class="alg-mini alg-mini--${N[p].tipo} alg-sis--${N[p].sistema} ${N[p].estado === 'pendiente' ? 'alg-nodo--pendiente' : ''}" data-nodo="${p}">${esc(N[p].titulo)}</button>`;
        });
      });
      html += '</div>';
    });
    html += '</div></div>';
    completo.innerHTML = html;
  }

  raiz.addEventListener('click', (ev) => {
    const op = ev.target.closest('.alg-opcion');
    if (op) {
      if (op.dataset.ejemplo) { ejemplo = op.dataset.ejemplo; pasos = [A.inicio, N[A.inicio].siguiente]; }
      else pasos.push(op.dataset.va);
      render();
      const nuevo = camino.querySelector('.alg-paso:last-of-type');
      if (nuevo && nuevo.scrollIntoView) nuevo.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      return;
    }
    const nodo = ev.target.closest('[data-nodo]');
    if (nodo) { abrirFicha(nodo.dataset.nodo); return; }
  });
  raiz.addEventListener('keydown', (ev) => {
    const nodo = ev.target.closest('.alg-nodo');
    if (nodo && (ev.key === 'Enter' || ev.key === ' ')) { ev.preventDefault(); abrirFicha(nodo.dataset.nodo); }
  });
  ficha.addEventListener('click', (ev) => { if (ev.target === ficha || ev.target.closest('.alg-ficha__cerrar')) ficha.hidden = true; });
  document.addEventListener('keydown', (ev) => { if (ev.key === 'Escape') ficha.hidden = true; });

  document.getElementById('alg-reiniciar').addEventListener('click', () => { pasos = [A.inicio]; ejemplo = null; render(); });
  document.getElementById('alg-atras').addEventListener('click', () => {
    if (pasos.length > 2) pasos.pop();
    else { pasos = [A.inicio]; ejemplo = null; }
    render();
  });
  document.getElementById('alg-ver-completo').addEventListener('click', (ev) => {
    const ver = completo.hidden;
    completo.hidden = !ver;
    if (ver && !completo.innerHTML) renderCompleto();
    ev.currentTarget.textContent = ver ? '🧭 Ocultar recorrido completo' : '🗺️ Ver recorrido completo';
    if (ver) completo.scrollIntoView({ behavior: 'smooth' });
  });
  document.getElementById('alg-imprimir').addEventListener('click', () => {
    if (completo.hidden) { if (!completo.innerHTML) renderCompleto(); completo.hidden = false; }
    window.print();
  });
  const verEjemplo = document.getElementById('alg-ver-ejemplo');
  if (verEjemplo) verEjemplo.addEventListener('click', () => {
    if (!ejemplo) { ejemplo = 'insumos'; pasos = [A.inicio, N[A.inicio].siguiente]; render(); }
    banner.scrollIntoView({ behavior: 'smooth', block: 'center' });
  });

  render();
})();
