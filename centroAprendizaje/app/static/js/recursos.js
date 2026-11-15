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
      const ok = (!q || el.dataset.filtro.includes(q)) && (!cat || el.dataset.categoria === cat);
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
  }
  filtro.addEventListener('input', aplicar);
  if (categoria) categoria.addEventListener('change', aplicar);
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
