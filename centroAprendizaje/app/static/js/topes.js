// topes.js — al pasar el mouse (o tocar) sobre "monto menor al tope",
// "licitación privada", "concurso público", etc., muestra el tope del año
// según la Circular SCyGB 01/2026. Los textos vienen del servidor
// (recursos.topes), la misma tabla que la página "Montos y topes".
(function () {
  const datos = document.getElementById('topes-datos');
  const zona = document.getElementById('main-content') || document.querySelector('main');
  if (!datos || !zona || /\/recursos\/montos$/.test(location.pathname)) return;
  const topes = JSON.parse(datos.textContent);
  const porFrase = new Map();
  topes.forEach((t) => t.frases.forEach((f) => porFrase.set(f.toLowerCase(), t.texto)));
  // Las frases largas primero, para que "licitación o concurso privado" gane a "concurso privado".
  const frases = Array.from(porFrase.keys()).sort((a, b) => b.length - a.length)
    .map((f) => f.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  const LETRA = 'A-Za-z0-9ÁÉÍÓÚáéíóúÑñÜü';
  const patron = new RegExp('(^|[^' + LETRA + '])(' + frases.join('|') + ')(?![' + LETRA + '])', 'i');

  const nodos = [];
  const walker = document.createTreeWalker(zona, NodeFilter.SHOW_TEXT, {
    acceptNode: (n) => (n.parentElement.closest('a, button, summary, script, style, textarea, input, select, .tope, .rec-fuentes, [data-sin-topes]')
      ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT),
  });
  while (walker.nextNode()) nodos.push(walker.currentNode);
  nodos.forEach((nodo) => {
    let actual = nodo;
    // Puede haber más de una frase en el mismo texto.
    for (let m = actual.nodeValue.match(patron); m; m = actual.nodeValue.match(patron)) {
      const inicio = m.index + m[1].length;
      const frase = actual.splitText(inicio);
      actual = frase.splitText(m[2].length);
      const marca = document.createElement('span');
      marca.className = 'tope';
      marca.tabIndex = 0;
      marca.dataset.tope = porFrase.get(m[2].toLowerCase());
      marca.setAttribute('aria-label', m[2] + '. ' + marca.dataset.tope);
      marca.textContent = frase.nodeValue;
      frase.replaceWith(marca);
    }
  });
})();
