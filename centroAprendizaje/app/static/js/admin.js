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
