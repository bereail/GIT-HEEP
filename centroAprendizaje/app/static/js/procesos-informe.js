// procesos-informe.js — botón de imprimir del informe (sin JS en línea por la CSP).
document.addEventListener('click', (ev) => {
  if (ev.target.closest('[data-imprimir]')) window.print();
});
