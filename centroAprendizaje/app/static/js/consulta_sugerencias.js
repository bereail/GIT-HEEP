// Antes de mandar una consulta: muestra lo que ya está respondido en el
// sitio y se parece a lo que la persona está escribiendo.
(function () {
  var campo = document.getElementById("mensaje");
  var caja = document.getElementById("consulta-sugerencias");
  if (!campo || !caja) return;
  var espera = null, ultima = "";

  function texto() {
    // La primera línea «Sobre: …» la pone el sistema: no se busca.
    return campo.value.replace(/^Sobre:.*$/m, "").trim();
  }
  function pintar(resultados) {
    caja.textContent = "";
    if (!resultados.length) { caja.hidden = true; return; }
    var t = document.createElement("p");
    t.className = "consulta-sug__tit";
    t.textContent = "Antes de enviarla, fijate si ya está respondida:";
    caja.appendChild(t);
    resultados.slice(0, 5).forEach(function (r) {
      var a = document.createElement("a");
      a.href = r.url; a.target = "_blank"; a.rel = "noopener";
      a.textContent = (r.tema_icono ? r.tema_icono + " " : "") + r.title;
      caja.appendChild(a);
    });
    var p = document.createElement("p");
    p.className = "consulta-sug__nota";
    p.textContent = "Si ninguna responde tu duda, enviala igual.";
    caja.appendChild(p);
    caja.hidden = false;
  }
  campo.addEventListener("input", function () {
    clearTimeout(espera);
    espera = setTimeout(function () {
      var q = texto();
      if (q.length < 8 || q === ultima) { if (q.length < 8) pintar([]); return; }
      ultima = q;
      fetch("/buscar.json?origen=consulta&q=" + encodeURIComponent(q.slice(0, 200)), { credentials: "same-origin" })
        .then(function (r) { return r.ok ? r.json() : []; })
        .then(pintar, function () { pintar([]); });
    }, 600);
  });
})();
