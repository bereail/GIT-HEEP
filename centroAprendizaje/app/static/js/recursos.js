// recursos.js — filtros y glosario emergente de las páginas de Recursos
// (sitio público y panel). Sin JS en línea: lo permite la CSP.

// ------------------------------------------------------------- Recursos --

// Filtro de texto (y categoría) para el glosario y la biblioteca.
(function () {
  const filtro = document.getElementById('rec-filtro');
  if (!filtro) return;
  const categoria = document.getElementById('rec-categoria');
  const items = Array.from(document.querySelectorAll('#rec-terminos [data-filtro]'));
  const vacio = document.getElementById('rec-vacio');
  function aplicar() {
    const q = filtro.value.trim().toLowerCase();
    const cat = categoria ? categoria.value : '';
    let alguno = false;
    items.forEach((el) => {
      const grupo = document.querySelector('.dic-grupos .is-active');
      const soloCompras = grupo && grupo.dataset.grupo === 'compras';
      const ok = (!q || el.dataset.filtro.includes(q)) && (!cat || el.dataset.categoria === cat) && (!soloCompras || el.dataset.grupo !== 'tema');
      el.hidden = !ok;
      alguno = alguno || ok;
    });
    // Letras o secciones que quedaron vacías se esconden.
    document.querySelectorAll('#rec-terminos .rec-letra').forEach((h) => {
      let sig = h.nextElementSibling;
      let visible = false;
      while (sig && !sig.classList.contains('rec-letra')) { if (!sig.hidden) visible = true; sig = sig.nextElementSibling; }
      h.hidden = !visible;
    });
    document.querySelectorAll('#rec-terminos .rec-seccion').forEach((s) => {
      s.hidden = !s.querySelector('[data-filtro]:not([hidden])');
    });
    if (vacio) vacio.hidden = alguno;
    // El término cuyo título coincide con la búsqueda se resalta y queda a la vista.
    items.forEach((el) => el.classList.remove('dic-coincide'));
    if (q.length >= 2) {
      const exacto = items.find((el) => !el.hidden && el.querySelector('h3') && el.querySelector('h3').textContent.toLowerCase().startsWith(q));
      if (exacto) { exacto.classList.add('dic-coincide'); exacto.scrollIntoView({ block: 'nearest' }); }
    }
  }
  filtro.addEventListener('input', aplicar);
  document.querySelectorAll('.dic-grupos [data-grupo]').forEach((b) => b.addEventListener('click', () => {
    document.querySelectorAll('.dic-grupos [data-grupo]').forEach((x) => { x.classList.toggle('is-active', x === b); x.setAttribute('aria-checked', x === b ? 'true' : 'false'); });
    aplicar();
  }));
  // Un término relacionado que está filtrado: se limpian los filtros para mostrarlo.
  document.addEventListener('click', (ev) => {
    const a = ev.target.closest('[data-relacionado]');
    if (!a) return;
    const destino = document.querySelector(a.getAttribute('href'));
    if (destino && destino.hidden) {
      filtro.value = ''; if (categoria) categoria.value = '';
      const todos = document.querySelector('.dic-grupos [data-grupo="todos"]');
      if (destino.dataset.grupo === 'tema' && todos) todos.click(); else aplicar();
    }
    if (destino) { destino.classList.add('dic-resaltado'); setTimeout(() => destino.classList.remove('dic-resaltado'), 1600); }
  });
  // Búsqueda desde otros módulos: ?q=preadjudicación
  const pedido = new URLSearchParams(location.search).get('q');
  if (pedido) filtro.value = pedido;
  if (categoria) categoria.addEventListener('change', aplicar);
  aplicar();
})();

// Glosario sin salir de la pantalla: en las zonas [data-glosario-auto], la
// primera aparición de cada término se vuelve un botón que abre su definición.
(function () {
  const datos = document.getElementById('glosario-defs');
  const pop = document.getElementById('rec-popover');
  if (!datos || !pop) return;
  const terminos = JSON.parse(datos.textContent);
  const porNombre = new Map();
  terminos.forEach((t) => {
    const base = t.termino.split(' (')[0].split(' / ')[0].trim();
    const sigla = (t.termino.match(/\(([^)]+)\)/) || [])[1];
    [base, sigla].forEach((n) => { if (n && n.length >= 3 && !porNombre.has(n.toLowerCase())) porNombre.set(n.toLowerCase(), t); });
  });
  const nombres = Array.from(porNombre.keys()).sort((a, b) => b.length - a.length)
    .map((n) => n.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  if (!nombres.length) return;
  const LETRA = 'A-Za-z0-9_ÁÉÍÓÚáéíóúÑñÜü';
  const patron = new RegExp('(^|[^' + LETRA + '])(' + nombres.join('|') + ')(?![' + LETRA + '])', 'i');

  document.querySelectorAll('[data-glosario-auto]').forEach((zona) => {
    const usados = new Set();
    const walker = document.createTreeWalker(zona, NodeFilter.SHOW_TEXT, {
      acceptNode: (n) => (n.parentElement.closest('a, button, summary, h2, h3, .rec-estado, .rec-fuentes, script') ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT),
    });
    const nodos = [];
    while (walker.nextNode()) nodos.push(walker.currentNode);
    nodos.forEach((nodo) => {
      const m = nodo.nodeValue.match(patron);
      if (!m) return;
      const clave = m[2].toLowerCase();
      if (usados.has(clave)) return;
      usados.add(clave);
      const inicio = m.index + m[1].length;
      const resto = nodo.splitText(inicio);
      resto.splitText(m[2].length);
      const boton = document.createElement('button');
      boton.type = 'button';
      boton.className = 'rec-term';
      boton.dataset.termino = porNombre.get(clave).termino;
      boton.textContent = resto.nodeValue;
      resto.replaceWith(boton);
    });
  });

  const cuerpo = pop.querySelector('.rec-popover__cuerpo');
  const porTermino = new Map(terminos.map((t) => [t.termino, t]));
  function texto(s) { const d = document.createElement('div'); d.textContent = s || ''; return d.innerHTML; }
  document.addEventListener('click', (ev) => {
    const b = ev.target.closest('.rec-term');
    if (b) {
      const t = porTermino.get(b.dataset.termino);
      cuerpo.innerHTML = `<b>${texto(t.termino)}</b><p>${texto(t.sencilla)}</p>${t.tecnica ? `<p class="text-muted">${texto(t.tecnica)}</p>` : ''}<p class="text-muted">📍 ${texto(t.modulo)}</p>`;
      pop.hidden = false;
      const r = b.getBoundingClientRect();
      pop.style.top = `${window.scrollY + r.bottom + 6}px`;
      pop.style.left = `${Math.max(8, Math.min(window.scrollX + r.left, window.scrollX + document.documentElement.clientWidth - pop.offsetWidth - 8))}px`;
      return;
    }
    if (ev.target.closest('.rec-popover__cerrar') || !ev.target.closest('#rec-popover')) pop.hidden = true;
  });
  document.addEventListener('keydown', (ev) => { if (ev.key === 'Escape') pop.hidden = true; });
})();

// Modelos de mensajes: copiar el texto de una plantilla.
document.addEventListener('click', (ev) => {
  const b = ev.target.closest('[data-copiar]');
  if (!b) return;
  const texto = document.getElementById(b.dataset.copiar).textContent;
  const listo = () => { const antes = b.textContent; b.textContent = '✓ Copiado'; setTimeout(() => { b.textContent = antes; }, 1600); };
  if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(texto).then(listo, () => {});
  else {
    const t = document.createElement('textarea');
    t.value = texto; document.body.appendChild(t); t.select();
    try { document.execCommand('copy'); listo(); } catch (e) { /* sin portapapeles */ }
    t.remove();
  }
});

// Checklists por procedimiento: se filtran los controles, se calcula el
// avance y se avisa cuántos obligatorios faltan. Marcas solo en este navegador.
(function () {
  const etapas = document.querySelectorAll('.her-check');
  if (!etapas.length) return;
  const CLAVE = 'checklists-timbo-v2';
  let datos = {};
  try { datos = JSON.parse(localStorage.getItem(CLAVE) || '{}'); } catch (e) { datos = {}; }
  const botones = document.querySelectorAll('.her-proc');
  let proc = (botones[0] && botones[0].dataset.proc) || 'A';
  function guardar() { try { localStorage.setItem(CLAVE, JSON.stringify(datos)); } catch (e) { /* modo privado */ } }
  function marcas() { datos[proc] = datos[proc] || {}; return datos[proc]; }
  function aplicar() {
    const m = marcas();
    let total = 0; let hechas = 0; let faltanOblig = 0;
    etapas.forEach((et) => {
      let t = 0; let h = 0;
      et.querySelectorAll('li[data-procs]').forEach((li) => {
        const visible = li.dataset.procs.split(',').includes(proc);
        li.hidden = !visible;
        const c = li.querySelector('input');
        c.checked = !!m[c.dataset.item];
        if (!visible) return;
        t += 1; if (c.checked) h += 1;
        if (!c.checked && c.dataset.tipo === 'obligatorio') faltanOblig += 1;
      });
      et.hidden = t === 0;
      et.querySelector('.her-check__avance').textContent = t ? `${h} de ${t}` : '';
      et.classList.toggle('her-check--completa', t > 0 && h === t);
      total += t; hechas += h;
    });
    const pct = total ? Math.round((100 * hechas) / total) : 0;
    document.getElementById('her-barra').style.width = pct + '%';
    document.getElementById('her-porcentaje').textContent = pct + '%';
    document.getElementById('her-alerta').textContent = faltanOblig ? `⚠️ Faltan ${faltanOblig} controles obligatorios` : '✔ Sin obligatorios pendientes';
    document.getElementById('her-alerta').classList.toggle('her-alerta--ok', !faltanOblig);
  }
  botones.forEach((b) => b.addEventListener('click', () => {
    proc = b.dataset.proc;
    botones.forEach((x) => { x.classList.toggle('is-active', x === b); x.setAttribute('aria-checked', x === b ? 'true' : 'false'); });
    aplicar();
  }));
  document.querySelectorAll('.her-check input[type=checkbox]').forEach((c) => {
    c.addEventListener('change', () => { marcas()[c.dataset.item] = c.checked; guardar(); aplicar(); });
  });
  const limpiar = document.getElementById('her-limpiar');
  if (limpiar) limpiar.addEventListener('click', () => { datos[proc] = {}; guardar(); aplicar(); });
  const imprimir = document.getElementById('her-imprimir');
  if (imprimir) imprimir.addEventListener('click', () => window.print());
  const pedido = new URLSearchParams(location.search).get('procedimiento');
  if (pedido) { const b = Array.from(botones).find((x) => x.dataset.proc === pedido); if (b) b.click(); else aplicar(); } else aplicar();
})();

// Botones de imprimir genéricos.
document.addEventListener('click', (ev) => { if (ev.target.closest('[data-imprimir]')) window.print(); });
