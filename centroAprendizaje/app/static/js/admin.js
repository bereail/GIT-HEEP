// admin.js — comportamientos del panel sin JS en línea (la CSP lo bloquea).
// <form data-confirmar="¿Seguro?">  → pide confirmación antes de enviar.
// <select data-autoenviar>          → envía el formulario al cambiar.

document.addEventListener('submit', (ev) => {
  const form = ev.target.closest('form[data-confirmar]');
  if (form && !window.confirm(form.dataset.confirmar)) ev.preventDefault();
});

document.addEventListener('change', (ev) => {
  const campo = ev.target.closest('[data-autoenviar]');
  if (campo && campo.form) campo.form.submit();
});

// <button data-acceso-directo="id-del-elemento-con-la-url" data-nombre="..."> → descarga un
// acceso directo de Windows (.url) que abre esa dirección.
document.addEventListener('click', (ev) => {
  const b = ev.target.closest('[data-acceso-directo]');
  if (!b) return;
  const url = document.getElementById(b.dataset.accesoDirecto).textContent.trim();
  const blob = new Blob(['[InternetShortcut]\r\nURL=' + url + '\r\n'], { type: 'application/octet-stream' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = (b.dataset.nombre || 'Acceso') + '.url';
  document.body.appendChild(a);
  a.click();
  setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
});

// <button data-tildar-todos="id-de-lista"> → tilda las casillas de la lista
// que todavía no estaban marcadas como pedidas.
document.addEventListener('click', (ev) => {
  const b = ev.target.closest('[data-tildar-todos]');
  if (!b) return;
  const lista = document.getElementById(b.dataset.tildarTodos);
  if (!lista) return;
  lista.querySelectorAll('input[type=checkbox]:not([data-ya])').forEach((c) => { c.checked = true; });
});
