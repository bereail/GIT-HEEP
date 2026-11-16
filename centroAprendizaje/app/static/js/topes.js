// topes.js — dos ayudas sobre el texto del sitio, con datos del servidor:
//  1. Formularios y documentos oficiales (CAByS, CD-01, Pliego Único...) se
//     vuelven un link al sitio oficial, con un cartel de dónde se crean.
//  2. "Monto menor al tope", "licitación privada", etc. muestran el tope del
//     año según la Circular SCyGB 01/2026 al pasar el mouse.
(function () {
  const zona = document.getElementById('main-content') || document.querySelector('main');
  if (!zona) return;
  const LETRA = 'A-Za-z0-9ÁÉÍÓÚáéíóúÑñÜü';
  const SALTEAR = 'a, button, summary, script, style, textarea, input, select, .tope, .rec-fuentes, [data-sin-topes]';

  function leer(id) {
    const el = document.getElementById(id);
    try { return el ? JSON.parse(el.textContent) : []; } catch (e) { return []; }
  }

  function marcar(grupos, crear) {
    const porFrase = new Map();
    grupos.forEach((g) => g.frases.forEach((f) => porFrase.set(f.toLowerCase(), g)));
    if (!porFrase.size) return;
    // Las frases largas primero, para que "licitación o concurso privado" gane a "concurso privado".
    const frases = Array.from(porFrase.keys()).sort((a, b) => b.length - a.length)
      .map((f) => f.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
    const patron = new RegExp('(^|[^' + LETRA + '])(' + frases.join('|') + ')(?![' + LETRA + '])', 'i');
    const nodos = [];
    const walker = document.createTreeWalker(zona, NodeFilter.SHOW_TEXT, {
      acceptNode: (n) => (n.parentElement.closest(SALTEAR) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT),
    });
    while (walker.nextNode()) nodos.push(walker.currentNode);
    nodos.forEach((nodo) => {
      let actual = nodo;
      for (let m = actual.nodeValue.match(patron); m; m = actual.nodeValue.match(patron)) {
        const frase = actual.splitText(m.index + m[1].length);
        actual = frase.splitText(m[2].length);
        const marca = crear(porFrase.get(m[2].toLowerCase()));
        marca.textContent = frase.nodeValue;
        marca.setAttribute('aria-label', frase.nodeValue + '. ' + marca.dataset.tope);
        frase.replaceWith(marca);
      }
    });
  }

  marcar(leer('enlaces-datos'), (g) => {
    const a = document.createElement('a');
    a.className = 'tope enlace-oficial';
    a.href = g.url;
    a.target = '_blank';
    a.rel = 'noopener';
    a.dataset.tope = g.texto;
    return a;
  });
  // Direcciones oficiales escritas como texto (santafe.gob.ar / santafe.gov.ar): se vuelven links.
  const URL_OFICIAL = /(https?:\/\/)?(?:[a-z0-9-]+\.)*santafe\.go[bv]\.ar(?:\/[^\s"'<>()]*[^\s"'<>().,;:])?/i;
  const textos = [];
  const recorrido = document.createTreeWalker(zona, NodeFilter.SHOW_TEXT, {
    acceptNode: (n) => (n.parentElement.closest(SALTEAR) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT),
  });
  while (recorrido.nextNode()) textos.push(recorrido.currentNode);
  textos.forEach((nodo) => {
    let actual = nodo;
    for (let m = actual.nodeValue.match(URL_OFICIAL); m; m = actual.nodeValue.match(URL_OFICIAL)) {
      const trozo = actual.splitText(m.index);
      actual = trozo.splitText(m[0].length);
      const a = document.createElement('a');
      a.href = m[1] ? m[0] : 'https://' + m[0];
      a.target = '_blank';
      a.rel = 'noopener';
      a.textContent = trozo.nodeValue;
      trozo.replaceWith(a);
    }
  });

  if (!/\/recursos\/montos$/.test(location.pathname)) {
    marcar(leer('topes-datos'), (g) => {
      const s = document.createElement('span');
      s.className = 'tope';
      s.tabIndex = 0;
      s.dataset.tope = g.texto;
      return s;
    });
  }
})();
