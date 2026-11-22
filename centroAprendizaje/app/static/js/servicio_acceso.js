// servicio_acceso.js — entrada con el enlace privado de un servicio.
// El token viaja en el "#" del enlace (el navegador no lo manda en la URL):
// lo mandamos por POST y lo borramos de la barra de direcciones.
(function () {
  var form = document.getElementById("sv-acceso-form");
  if (!form) return;
  var token = decodeURIComponent((location.hash || "").slice(1));
  history.replaceState(null, "", location.pathname);
  if (token) {
    document.getElementById("sv-token").value = token;
    form.submit();
  } else {
    document.getElementById("sv-acceso-titulo").textContent = "Falta el enlace de acceso";
    document.getElementById("sv-acceso-texto").textContent = "Abrí la revisión desde el enlace o el acceso directo de tu servicio.";
  }
})();
