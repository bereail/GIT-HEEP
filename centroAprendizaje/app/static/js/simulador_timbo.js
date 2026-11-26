/* Simulador de TIMBÓ (Bandeja de trámites) para practicar.
   Las pantallas copian lo relevado en TIMBÓ el 25/11/2026; lo que no se pudo ver
   queda marcado «no relevado» en vez de inventarse. Todo se guarda en este
   navegador (localStorage): nada sale de la PC. */
(function () {
  "use strict";

  var D = JSON.parse(document.getElementById("sim-datos").textContent);
  var TRAMITE_MMT = "Gestión Directa - Por Monto Menor al Tope - Compras y Contrataciones";
  var CLAVE = "simTimbo.v1";

  // ------------------------------------------------------------ utilidades
  function h(t) {
    return String(t == null ? "" : t).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function $(sel, raiz) { return (raiz || document).querySelector(sel); }
  function sinTildes(t) { return t.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase(); }
  function hoy() {
    var d = new Date();
    function dd(n) { return (n < 10 ? "0" : "") + n; }
    return dd(d.getDate()) + "/" + dd(d.getMonth() + 1) + "/" + d.getFullYear() + " " + dd(d.getHours()) + ":" + dd(d.getMinutes());
  }
  function hora() { var d = new Date(); return (d.getHours() < 10 ? "0" : "") + d.getHours() + ":" + (d.getMinutes() < 10 ? "0" : "") + d.getMinutes(); }
  function mezclar(a) {
    a = a.slice();
    for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var t = a[i]; a[i] = a[j]; a[j] = t; }
    return a;
  }

  var ICONOS = {
    menu: "M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z",
    casa: "M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z",
    carpeta: "M9.17 6l2 2H20v10H4V6h5.17M10 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z",
    carpetaDoc: "M20 6h-8l-2-2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm0 12H4V6h5.17l2 2H20v10zm-6-8h-4v6h6v-4l-2-2zm1 5h-4v-4h2.5l1.5 1.5V15z",
    flechas: "M16 17.01V10h-2v7.01h-3L15 21l4-3.99h-3zM9 3L5 6.99h3V14h2V6.99h3L9 3z",
    carpetaPersona: "M20 6h-8l-2-2H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm0 12H4V6h5.17l2 2H20v10zm-5-5c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm-4 4h8v-1c0-1.33-2.67-2-4-2s-4 .67-4 2v1z",
    carpetaAbierta: "M20 6h-8l-2-2H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm0 12H4V8h16v10z",
    articulo: "M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14zM7 7h10v2H7zm0 4h10v2H7zm0 4h7v2H7z",
    actividad: "M20 3H4c-1.1 0-2 .9-2 2v11c0 1.1.9 2 2 2h4v2h8v-2h4c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 13H4V5h16v11zM6 13l3-4 3 3 2-3 4 4H6z",
    cuenta: "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z",
    abajo: "M16.59 8.59L12 13.17 7.41 8.59 6 10l6 6 6-6z",
    derecha: "M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z",
    izquierda: "M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z",
    buscar: "M15.5 14h-.79l-.28-.27A6.47 6.47 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z",
    refrescar: "M17.65 6.35A7.958 7.958 0 0012 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08A5.99 5.99 0 0112 18c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z",
    cerrar: "M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z",
    desplegar: "M7 10l5 5 5-5z",
    replegar: "M7 14l5-5 5 5z",
    calendario: "M19 4h-1V2h-2v2H8V2H6v2H5c-1.11 0-2 .9-2 2v14a2 2 0 002 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V9h14v11zM7 11h5v5H7z",
    agregar: "M13 7h-2v4H7v2h4v4h2v-4h4v-2h-4V7zm-1-5C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z",
    abrir: "M19 19H5V5h7V3H5a2 2 0 00-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2v-7h-2v7zM14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7z",
    doc: "M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z",
    grupo: "M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z",
    campana: "M12 22c1.1 0 2-.9 2-2h-4c0 1.1.89 2 2 2zm6-6v-5c0-3.07-1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z",
    ojo: "M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z",
    editarDoc: "M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h6v-2H6V4h7v5h5v3h2V8l-6-6zm6.3 11.4l1.3 1.3c.2.2.2.5 0 .7l-1 1-2-2 1-1c.2-.2.5-.2.7 0zM14 19.9V22h2.1l5.2-5.2-2.1-2.1L14 19.9z",
    abajoIzq: "M20 5.41L18.59 4 7 15.59V9H5v10h10v-2H8.41z",
    bandejaSalida: "M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5v-3h3.56c.69 1.19 1.97 2 3.45 2s2.75-.81 3.45-2H19v3zm0-5h-4.99c0 1.1-.9 2-2 2s-2-.9-2-2H5V5h14v9zM8 9h2.55v3h2.9V9H16l-4-4z",
    contacto: "M20 0H4v2h16V0zM4 24h16v-2H4v2zM20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm-8 2.75c1.24 0 2.25 1.01 2.25 2.25s-1.01 2.25-2.25 2.25S9.75 10.24 9.75 9 10.76 6.75 12 6.75zM17 17H7v-1.5c0-1.67 3.33-2.5 5-2.5s5 .83 5 2.5V17z",
    organigrama: "M22 11V3h-7v3H9V3H2v8h7V8h2v10h4v3h7v-8h-7v3h-2V8h2v3h7zM7 9H4V5h3v4zm10 6h3v4h-3v-4zm0-10h3v4h-3V5z",
    historial: "M13 3a9 9 0 00-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42A8.954 8.954 0 0013 21a9 9 0 000-18zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z",
    tresPuntos: "M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z",
    flujo: "M17 16l-4-4V8.82C14.16 8.4 15 7.3 15 6c0-1.66-1.34-3-3-3S9 4.34 9 6c0 1.3.84 2.4 2 2.82V12l-4 4H3v5h5v-3.05l4-4.2 4 4.2V21h5v-5h-4z",
    info: "M11 7h2v2h-2zm0 4h2v6h-2zm1-9C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z",
    descargar: "M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z",
    etiqueta: "M21.41 11.58l-9-9C12.05 2.22 11.55 2 11 2H4c-1.1 0-2 .9-2 2v7c0 .55.22 1.05.59 1.42l9 9c.36.36.86.58 1.41.58.55 0 1.05-.22 1.41-.59l7-7c.37-.36.59-.86.59-1.41 0-.55-.23-1.06-.59-1.42zM5.5 7C4.67 7 4 6.33 4 5.5S4.67 4 5.5 4 7 4.67 7 5.5 6.33 7 5.5 7z"
  };
  function ico(nombre, clase) {
    return '<i class="tb-ico ' + (clase || "") + '"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="' + ICONOS[nombre] + '"/></svg></i>';
  }
  function pintarIconos(raiz) {
    (raiz || document).querySelectorAll("i[data-ico]").forEach(function (i) {
      var n = { menu: "menu", cuenta: "cuenta", abajo: "abajo" }[i.dataset.ico];
      if (n) { i.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="' + ICONOS[n] + '"/></svg>'; i.removeAttribute("data-ico"); }
    });
  }

  // ------------------------------------------------------------ estado guardado
  function cargar() {
    try { var s = JSON.parse(localStorage.getItem(CLAVE)); if (s && s.sol) return s; } catch (e) { /* sin almacenamiento */ }
    return { sol: [], docs: [], hist: [], visto: false };
  }
  var S = cargar();
  function guardar() { try { localStorage.setItem(CLAVE, JSON.stringify(S)); } catch (e) { /* modo privado */ } }

  // ------------------------------------------------------------ menú (tal cual el relevado)
  var MENU = [
    { t: "Tablero de Inicio", i: "casa", ir: "#/dashboard" },
    { t: "Expedientes", i: "carpeta", sub: [
      { t: "Solicitud de caratulación", i: "editarDoc", ir: "#/solicitud_caratulacion" },
      { t: "Gestión", i: "carpeta", ir: "#/expedientes" },
      { t: "Consulta", i: "buscar", ir: "#/consulta_ee" }, { t: "Visibilidad", i: "ojo", ir: "#/admin_visibilidad_ee" },
      { t: "Gestión de visualización", i: "carpeta", ir: "#/solicitud_vista_expediente" }] },
    { t: "Documentos oficiales", i: "carpetaDoc", sub: [
      { t: "Gestión", i: "editarDoc", ir: "#/documentos_oficiales" }, { t: "Consulta", i: "buscar", ir: "#/consulta_do" }, { t: "Visibilidad", i: "ojo" }] },
    { t: "Comunicaciones Oficiales", i: "flechas", sub: [
      { t: "Internas", i: "abajoIzq", ir: "#/communications_internas" }, { t: "Externas", i: "bandejaSalida", ir: "#/communications_externas" }] },
    { t: "Lista de destinatarios", i: "carpetaPersona", sub: [
      { t: "Agentes", i: "contacto", ir: "#/users_distribution_list" }, { t: "Ciudadanos", i: "contacto", ir: "#/citizens_distribution_list" }] },
    { t: "Biblioteca de Procedimientos Administrativos", i: "carpetaAbierta", ir: "#/bibloteca_de_procedimientos_administrativos" },
    { t: "Oficinas y Usuarios", i: "carpetaPersona", sub: [
      { t: "Oficinas", i: "organigrama" }, { t: "Consulta de usuarios", i: "buscar", ir: "#/consulta_de_usuarios" }] },
    { t: "Autorregistro", i: "articulo", ir: "#/autorregistro" },
    { t: "RLM", i: "actividad", sub: [
      { t: "Entidades Digitales › Consulta de Apoderamientos", i: "buscar", ir: "#/entity_attorneys_lookup" }] }
  ];
  var menuAbierto = null; // índice del submenú abierto

  function pintarIconosNav() {
    var ruta = location.hash.split("?")[0];
    $("#tb-iconos").innerHTML = MENU.map(function (m, k) {
      var activo = (m.ir && m.ir === ruta) || (m.sub && m.sub.some(function (s) { return s.ir && ruta.indexOf(s.ir) === 0; }));
      return '<li><button type="button" class="' + (activo ? "activo" : "") + '" data-nav="' + k + '" title="' + h(m.t) + '">' + ico(m.i) + "</button></li>";
    }).join("");
  }
  function abrirMenu(k) {
    menuAbierto = (k == null ? null : k);
    $("#tb-menu").hidden = false;
    $("#tb-cortina").hidden = false;
    var cuerpo = $("#tb-menu-cuerpo");
    if (menuAbierto != null && MENU[menuAbierto].sub) {
      var m = MENU[menuAbierto];
      cuerpo.innerHTML = '<div class="tb-submenu"><button type="button" class="tb-menu__volver" data-menu-volver>' + ico("izquierda", "tb-ico--chico") + h(m.t) + "</button>" +
        (m.sub.length ? m.sub.map(function (s, j) {
          return '<button type="button" class="tb-menu__item" data-sub="' + j + '">' + ico(s.i) + h(s.t) + (s.ir ? "" : '<span class="tb-nr">no relevado</span>') + "</button>";
        }).join("") : '<p style="padding:10px 18px;font-size:13px;opacity:.8">Las opciones de este menú no se relevaron todavía.</p>') + "</div>";
    } else {
      var ruta = location.hash.split("?")[0];
      cuerpo.innerHTML = MENU.map(function (m, k2) {
        var activo = m.ir === ruta;
        return '<button type="button" class="tb-menu__item ' + (activo ? "activo" : "") + '" data-item="' + k2 + '">' + ico(m.i) + h(m.t) +
          (m.sub ? ico("derecha", "tb-flecha") : (m.ir ? "" : '<span class="tb-nr">no relevado</span>')) + "</button>";
      }).join("");
    }
  }
  function cerrarMenu() { $("#tb-menu").hidden = true; $("#tb-cortina").hidden = true; menuAbierto = null; }
  function irA(destino, titulo) {
    cerrarMenu();
    if (destino) { location.hash = destino; } else { location.hash = "#/nr/" + encodeURIComponent(titulo); }
  }

  // ------------------------------------------------------------ componentes
  var selAbierto = null, selFiltro = "", selCargados = {};
  function selectHtml(id, valor, opts) {
    opts = opts || {};
    var abierto = selAbierto === id;
    var caja;
    if (valor) {
      caja = '<div class="tb-select__caja ' + (opts.invalido ? "invalido" : "") + '"><span>' + (opts.valorHtml || h(valor)) + '</span><button type="button" class="tb-select__x" data-sel-limpiar="' + id + '" aria-label="close">' + ico("cerrar") + "</button></div>";
    } else {
      caja = '<button type="button" class="tb-select__caja ' + (opts.invalido ? "invalido" : "") + '" data-sel="' + id + '"><span>Seleccione una opción</span>' + ico(abierto ? "replegar" : "desplegar", "tb-ico--chico") + "</button>";
    }
    var lista = "";
    if (abierto && !valor) {
      var todas = opts.opciones || [];
      var f = sinTildes(selFiltro.trim());
      var filtradas = todas.filter(function (o) { return !f || sinTildes(o.v).indexOf(f) >= 0 || sinTildes(o.extra || "").indexOf(f) >= 0; });
      var tope = selCargados[id] || (opts.porPagina || 999);
      var hayMas = filtradas.length > tope;
      lista = '<div class="tb-select__lista"><div class="tb-select__filtro"><input type="text" data-sel-filtro="' + id + '" placeholder="Filtrar opciones para ' + h(opts.etiqueta) + '" value="' + h(selFiltro) + '">' + ico("buscar", "tb-ico--chico") + "</div>" +
        '<div class="tb-select__ops">' + filtradas.slice(0, tope).map(function (o) {
          return '<button type="button" class="tb-select__op" data-sel-op="' + id + '" data-v="' + h(o.v) + '">' + (o.html || h(o.v)) + "</button>";
        }).join("") + (filtradas.length ? "" : '<div class="tb-select__op" style="color:#888">Sin resultados</div>') + "</div>" +
        (hayMas ? '<button type="button" class="tb-select__mas" data-sel-mas="' + id + '">' + ico("refrescar", "tb-ico--chico") + " Cargar más</button>" : "") + "</div>";
    }
    return '<div class="tb-select ' + (opts.clase || "") + '">' + caja + lista + "</div>";
  }
  function encabezadoLista(titulo, conMas) {
    return '<div class="tb-titulo"><h1>' + h(titulo) + '</h1><div class="tb-acciones"><button type="button" class="tb-acciones__link" data-acciones>Acciones ' + ico("abajo", "tb-ico--naranja") + "</button>" +
      (conMas ? '<button type="button" class="tb-mas" data-mas aria-label="add">+</button>' : "") + "</div></div>";
  }
  function pestanas(lista, activa) {
    return '<div class="tb-tabs">' + lista.map(function (t, k) {
      return '<button type="button" class="tb-tab ' + (k === activa ? "activo" : "") + '" data-tab="' + k + '">' + h(t) + (k === activa ? ico("refrescar") : "") + "</button>";
    }).join("") + '<span class="tb-sync">Última sincronización: ' + hora() + "</span></div>";
  }
  function filtros(lista) {
    return '<div class="tb-filtros">' + lista.map(function (f) {
      if (f.chip) return '<div class="tb-filtro tb-filtro--chip"><span style="flex:1;overflow:hidden;white-space:nowrap;text-overflow:ellipsis">' + h(f.chip) + "</span>" + ico("cerrar", "tb-ico--chico") + "</div>";
      if (f.dd) return '<div class="tb-filtro"><span style="flex:1;overflow:hidden;white-space:nowrap;text-overflow:ellipsis">' + h(f.dd) + "</span>" + ico("desplegar", "tb-ico--chico") + "</div>";
      if (f.fecha) return '<div class="tb-filtro"><span style="flex:1">' + h(f.fecha) + "</span>" + ico("calendario", "tb-ico--chico") + "</div>";
      return '<label class="tb-filtro"><input type="text" placeholder="' + h(f.txt) + '" data-filtro-txt>' + ico("buscar", "tb-ico--chico") + "</label>";
    }).join("") + "</div>";
  }
  var VACIO = '<div class="tb-vacio"><div class="tb-vacio__caja" aria-hidden="true"></div>Por el momento, la bandeja está vacía</div>';

  // ------------------------------------------------------------ pantallas de lista
  var tabSol = 0, tabExp = 0, tabDoc = 0, pildora = 0;

  var BANDEJAS = [["editarDoc", "Expedientes - Solicitud de caratulación"], ["carpeta", "Expedientes - Gestión"], ["carpeta", "Expedientes - Gestión de visualización"],
    ["editarDoc", "Documentos oficiales - Gestión"], ["abajoIzq", "Internas"], ["articulo", "Autorregistro"]];
  var bandejaSel = null;
  function vDashboard() {
    var centro = bandejaSel == null
      ? '<div class="tb-tablero__centro"><div><div class="tb-vacio__caja" aria-hidden="true" style="opacity:.6"></div>Seleccioná una bandeja para comenzar a gestionar tus procesos</div></div>'
      : '<div class="tb-panel-bandeja"><h2>' + h(BANDEJAS[bandejaSel][1]) + '</h2><div class="tb-pestana-curso"><b>En curso</b>0 procesos en curso</div>' +
        '<div class="tb-procesos"><div class="tb-procesos__cab">' + ico("organigrama", "tb-ico--naranja") + '<b>Procesos en curso</b><button type="button" class="tb-btn tb-btn--chico" data-aviso="Opciones: Todos (0) · 0 a 30 días (0) · 0 a 60 días (0) · 0 a 90 días (0) · 0 a 180 días (0) · 0 a 365 días (0).">Todos (0) ▾</button></div>' +
        '<div class="tb-procesos__tabla"><span>Nº de proceso</span><span>Fecha de arribo</span><span>Estado</span><span>Permanencia (en días)</span></div>' +
        '<p class="tb-procesos__vacio">No hay instancias disponibles en la bandeja</p><div class="tb-paginador">Items per page: <span class="tb-caja-mini">10 ▾</span> 0 of 0 &nbsp; |‹ ‹ › ›|</div></div></div>';
    return '<div class="tb-titulo"><h1>Tablero de Inicio</h1><span class="tb-actualizar ' + (bandejaSel != null ? "tb-actualizar--on" : "") + '">' + ico("refrescar", "tb-ico--chico") + "Actualizar</span></div>" +
      '<div class="tb-tablero"><div class="tb-bandejas"><h2>Bandejas</h2><label class="tb-filtro"><input type="text" placeholder="Buscar">' + ico("buscar", "tb-ico--chico") + "</label>" +
      '<div class="tb-pildoras"><button type="button" class="tb-pildora ' + (pildora === 0 ? "activo" : "") + '" data-pildora="0">Con procesos en curso (0)</button><button type="button" class="tb-pildora ' + (pildora === 1 ? "activo" : "") + '" data-pildora="1">Todas (6)</button></div>' +
      (pildora === 0 ? '<p style="text-align:center">No hay bandejas con procesos en curso</p>' : BANDEJAS.map(function (b, k) {
        return '<button type="button" class="tb-bandeja ' + (k === bandejaSel ? "activo" : "") + '" data-bandeja="' + k + '"><span class="tb-bandeja__ico">' + ico(b[0]) + "</span><span><b>" + h(b[1]) + "</b>0 procesos en curso</span></button>";
      }).join("")) + "</div>" + centro + "</div>";
  }

  function tarjetaSolicitud(s) {
    return '<article class="tb-tarjeta"><h3>' + h(s.tramite) + '<span class="tb-tarjeta__sim">simulado · el diseño de esta tarjeta no se relevó</span></h3>' +
      '<div class="tb-tarjeta__grilla"><div><b>Fecha</b>' + h(s.fecha) + "</div><div><b>Destino</b>" + h(s.oficina) + "</div><div><b>Motivo</b>" + h(s.motivo) + "</div><div><b>Visibilidad</b>" + h(s.visibilidad) + "</div>" +
      (s.urgente ? "<div><b>Urgente</b>Sí</div>" : "") + "</div></article>";
  }
  function vSolicitudes() {
    var lista = tabSol === 0 ? S.sol : [];
    return encabezadoLista("Solicitud de caratulación", true) + pestanas(["En curso", "Caratuladas", "Rechazadas"], tabSol) +
      filtros([{ txt: "Buscar" }, { dd: "Buscar Etiqueta" }, { dd: "Estadío" }, { dd: "Ordenar por" }, { fecha: "Desde" }, { fecha: "Hasta" }]) +
      (lista.length ? '<div class="tb-tarjetas">' + lista.slice().reverse().map(tarjetaSolicitud).join("") + "</div>" : VACIO);
  }
  function vExpedientes() {
    return encabezadoLista("Gestión", false) + pestanas(["Asignados", "Gestión", "Guarda temporal", "Archivo", "Gestión por jerarquía"], tabExp) +
      filtros([{ txt: "Buscar Nro. de Expediente:" }, { dd: "Buscar Etiqueta:" }, { txt: "Buscar Tema:" }, { txt: "Buscar Motivo:" }, { txt: "Buscar Asignado:" }, { chip: "Fecha de creación - Más reciente" }, { fecha: "Desde" }, { fecha: "Hasta" }]) +
      VACIO + '<p class="sim-nota" style="max-width:640px;margin:20px auto">En el relevamiento esta bandeja estaba vacía, así que todavía no se copió cómo se ve un expediente por dentro (actuaciones, vincular, pase). Se va a sumar con los manuales oficiales.</p>';
  }
  function tarjetaDoc(d) {
    return '<article class="tb-tarjeta"><h3>' + h(d.tipo) + '<span class="tb-tarjeta__sim">simulado</span></h3><div class="tb-tarjeta__num">Número de proceso: ' + h(d.numero) + "</div>" +
      '<div class="tb-tarjeta__grilla"><div>' + ico("calendario", "tb-ico--chico") + " " + h(d.fecha) + "</div><div><b>Iniciado por:</b>" + h(D.usuario.nombre) + "</div><div><b>Referencia:</b>— <small>(se carga en un paso no relevado)</small></div><div><b>Usuario Productor:</b>" + h(d.productor) + "</div></div>" +
      '<div class="tb-tarjeta__pie"><span class="tb-etq">+ ' + ico("etiqueta", "tb-ico--chico") + '</span><span class="tb-estadio">Estadío: no relevado</span></div>' +
      '<button type="button" class="tb-tarjeta__menu" data-doc-menu="' + h(d.numero) + '" aria-label="more_vert">' + ico("tresPuntos") + "</button></article>";
  }
  function vDocumentos() {
    var lista = tabDoc === 1 ? S.docs : [];
    return encabezadoLista("Gestión", true) + pestanas(["Pendientes", "Iniciados por mi", "Aprobados", "Rechazados", "Tramitados por mi"], tabDoc) +
      filtros([{ txt: "Buscar Referencia" }, { dd: "Buscar Tipo de Documento Oficial" }, { dd: "Buscar Estadío" }, { chip: "Fecha de creación - Más reciente" }, { dd: "Buscar Etiqueta:" }, { fecha: "Desde" }, { fecha: "Hasta" }]) +
      (lista.length ? '<div class="tb-tarjetas">' + lista.slice().reverse().map(tarjetaDoc).join("") + "</div>" : VACIO);
  }
  function vNoRelevado(titulo) {
    return '<div class="tb-titulo"><h1>' + h(titulo) + '</h1></div><div class="tb-tabs"></div><div class="sim-nota" style="max-width:620px;margin:40px auto">' +
      "<b>Pantalla todavía no relevada.</b> Para no inventar nada, el simulador solo copia lo que se vio en TIMBÓ. Esta parte se suma cuando se releve (con tu sesión o con un manual oficial).</div>";
  }

  // ------------------------------------------------------------ formulario: solicitud de caratulación
  var F = null; // estado del formulario abierto
  function nuevoFormSol() {
    return { tipo: "", urgente: false, tramite: "", sup: "", inf: "", telefono: "", motivo: "", visibilidad: "Público", responsables: [], relacionado: false, plataforma: "", intento: false, vioGuia: false, cambios: false };
  }
  function oficinaInf() {
    var l = (D.oficinas_inferiores[F.sup] || []);
    for (var i = 0; i < l.length; i++) if (l[i].nombre === F.inf) return l[i];
    return null;
  }
  function vFormSol() {
    var o = '<div class="tb-form-cab"><button type="button" data-volver>' + ico("izquierda", "tb-ico--chico") + 'Formulario Solicitud de Caratulación</button></div><div class="tb-form">' +
      '<div class="tb-fila"><div><span class="tb-label">La solicitud es para:</span>' +
      '<label class="tb-radio"><input type="radio" name="tipo" value="Interno" ' + (F.tipo === "Interno" ? "checked" : "") + ">Interno</label>" +
      '<label class="tb-radio"><input type="radio" name="tipo" value="Externo" ' + (F.tipo === "Externo" ? "checked" : "") + ">Externo</label></div>";
    if (F.tipo) o += '<div><span class="tb-label">¿Es Urgente?</span><label class="tb-toggle"><input type="checkbox" data-urgente ' + (F.urgente ? "checked" : "") + ">" + (F.urgente ? "Si" : "No") + "</label></div>";
    o += "</div>";
    if (F.tipo === "Externo") {
      return o.replace('value="Externo" checked>Externo</label>',
        'value="Externo" checked>Externo</label><div style="margin-left:34px"><span class="tb-req">*</span>' +
        '<label class="tb-radio"><input type="radio" name="persona" value="física">Persona física</label>' +
        '<label class="tb-radio"><input type="radio" name="persona" value="jurídica">Persona jurídica</label></div>') +
        '<p class="sim-nota" style="margin-top:30px">Los campos que siguen en una solicitud <b>Externa</b> (persona física o jurídica) no se pudieron relevar todavía. Para practicar el circuito, elegí <b>Interno</b>.</p></div>';
    }
    if (F.tipo !== "Interno") return o + "</div>";
    var tramites = D.tramites.map(function (t) { return { v: t.nombre }; });
    var req = function (campo) { return F.intento && !campo; };
    o += '<div class="tb-sub">Datos de Caratulación</div><div class="tb-campo"><span class="tb-label">Código del Trámite<span class="tb-req">*</span></span>' +
      '<div class="tb-campo--fila">' + selectHtml("tramite", F.tramite, { opciones: tramites, etiqueta: "Código del Trámite", porPagina: 5, clase: "tb-select--corto", invalido: req(F.tramite) }) +
      (F.tramite && guiaDe(F.tramite) ? '<button type="button" class="tb-btn-borde" data-guia>Guía de Proceso</button>' : "") + "</div>" +
      (req(F.tramite) ? '<p class="tb-error">Este campo es requerido</p>' : "") + "</div>";
    if (!F.tramite) return o + "</div>";
    o += '<div class="tb-campo"><span class="tb-label">Oficina de Nivel Superior<span class="tb-req">*</span></span>' +
      selectHtml("sup", F.sup, { opciones: D.oficinas_superiores.map(function (s) { return { v: s }; }), etiqueta: "Oficina de Nivel Superior", invalido: req(F.sup) }) +
      (req(F.sup) ? '<p class="tb-error">Este campo es requerido</p>' : "") + "</div>";
    var infs = D.oficinas_inferiores[F.sup];
    o += '<div class="tb-campo"><span class="tb-label">Oficina de Nivel Inferior<span class="tb-req">*</span></span>' +
      selectHtml("inf", F.inf, { opciones: (infs || []).map(function (s) { return { v: s.nombre }; }), etiqueta: "Oficina de Nivel Inferior", invalido: req(F.inf) }) +
      (req(F.inf) || (selAbierto === "inf" && !F.inf) ? '<p class="tb-error">Este campo es requerido</p>' : "") +
      (F.sup && !infs ? '<p class="sim-nota">Las oficinas de este organismo no se relevaron. Para practicar, elegí «MS - Ministerio de Salud».</p>' : "") +
      (infs && selAbierto === "inf" ? '<p class="sim-fuente">Simulador: solo figuran las oficinas cuyo comportamiento se pudo ver.</p>' : "") + "</div>";
    var of = oficinaInf();
    if (!of) return o + "</div>";
    if (!of.codigo) return o + '<p class="tb-error tb-error--grande">La Oficina seleccionada no posee Código de Identificación.</p></div>';
    o += '<div class="tb-oficina"><p>Oficina: <a href="#" data-nada>' + h(of.nombre) + ". " + ico("abrir", "tb-ico--naranja") + "</a></p><p>Oficina Inmediatamente Superior: " + h(of.superior) + ".</p><p>Dirección: " + h(of.direccion) + ".</p><p>Teléfono: " + h(of.telefono) + ".</p></div>" +
      '<div class="tb-sub" style="margin-top:20px">Información del Iniciador</div><div class="tb-grilla3">' +
      '<div><span class="tb-label">Nombre y Apellido / Oficina<span class="tb-req">*</span></span><input class="tb-input" value="' + h(D.usuario.nombre) + '" readonly></div>' +
      '<div><span class="tb-label">Email<span class="tb-req">*</span></span><input class="tb-input" value="' + h(D.usuario.email) + '" readonly></div>' +
      '<div><span class="tb-label">Teléfono</span><input class="tb-input" data-campo="telefono" value="' + h(F.telefono) + '"></div></div>' +
      '<div class="tb-sub" style="margin:30px 0 8px">Motivo</div><span class="tb-req" style="display:block;margin:0 0 10px">*</span>' +
      '<textarea class="tb-textarea ' + (req(F.motivo.trim()) ? "invalido" : "") + '" data-campo="motivo">' + h(F.motivo) + "</textarea>" +
      (req(F.motivo.trim()) ? '<p class="tb-error">Este campo es requerido</p>' : "") +
      '<span class="tb-label" style="margin-top:22px">Tipo de Visibilidad:<span class="tb-req">*</span></span>' +
      '<label class="tb-radio"><input type="radio" name="vis" value="Público" ' + (F.visibilidad === "Público" ? "checked" : "") + ">Público</label>" +
      '<label class="tb-radio"><input type="radio" name="vis" value="Reservado" ' + (F.visibilidad === "Reservado" ? "checked" : "") + ">Reservado</label>" +
      '<div class="tb-sub" style="margin-top:34px">Responsables</div><div class="tb-tabla"><div class="tb-tabla__cab">Usuario</div>' +
      (F.responsables.length ? F.responsables.map(function (r, k) {
        return '<div class="tb-tabla__fila"><span>' + h(r) + '</span><button type="button" class="tb-select__x" data-quitar-resp="' + k + '">' + ico("cerrar") + "</button></div>";
      }).join("") : '<div class="tb-tabla__fila tb-tabla__fila--vacia">Aún no has agregado ningún registro</div>') + "</div>" +
      '<div class="tb-link-agregar"><button type="button" data-agregar-resp>' + ico("agregar", "tb-ico--naranja") + "Agregar responsable</button></div>" +
      '<span class="tb-label" style="margin-top:4px">¿Desea agregar un Expediente Relacionado?</span><label class="tb-toggle"><input type="checkbox" data-relacionado ' + (F.relacionado ? "checked" : "") + ">" + (F.relacionado ? "Si" : "No") + "</label>";
    if (F.relacionado) {
      o += '<div class="tb-sub">Expediente Relacionado</div><span class="tb-label">Plataforma :<span class="tb-req">*</span></span>' +
        '<label class="tb-radio"><input type="radio" name="plat" value="Timbó" ' + (F.plataforma === "Timbó" ? "checked" : "") + ">Timbó</label>" +
        '<label class="tb-radio"><input type="radio" name="plat" value="Otra Plataforma" ' + (F.plataforma === "Otra Plataforma" ? "checked" : "") + ">Otra Plataforma</label>" +
        (F.plataforma ? '<p class="sim-nota">Los campos que siguen al elegir la plataforma no se relevaron todavía.</p>' : "") +
        (req(F.plataforma) ? '<p class="tb-error">Este campo es requerido</p>' : "");
    }
    return o + '<div class="tb-guardar"><button type="button" class="tb-btn" data-guardar-sol>Guardar</button></div></div>';
  }
  function guiaDe(tramite) {
    for (var i = 0; i < D.tramites.length; i++) if (D.tramites[i].nombre === tramite) return D.tramites[i].guia;
    return null;
  }
  function guardarSol() {
    F.intento = true;
    var faltan = !F.tramite || !F.sup || !F.inf || !F.motivo.trim() || (F.relacionado && !F.plataforma);
    if (faltan) { render(); return; }
    if (F.relacionado) { avisoSim("El expediente relacionado no se puede completar en el simulador (sus campos no se relevaron). Apagá «¿Desea agregar un Expediente Relacionado?» para seguir."); return; }
    var s = { tramite: F.tramite, oficina: F.inf, motivo: F.motivo.trim(), visibilidad: F.visibilidad, urgente: F.urgente, fecha: hoy() };
    S.sol.push(s); guardar();
    var resultado = ejercicioActivo === "caratula" ? evaluarCaratula() : null;
    F = null; tabSol = 0;
    location.hash = "#/solicitud_caratulacion";
    modal('<div class="tb-confirmar" style="width:420px;text-align:left"><h2>Solicitud guardada (simulación)</h2><p>En TIMBÓ real, la pantalla que aparece después de «Guardar» no se relevó. Según la <b>Guía de Proceso</b> oficial, el paso siguiente lo hace la <b>Mesa de Entradas de la Jurisdicción: «Caratular»</b> (paso 2).</p>' +
      '<button type="button" class="tb-btn" data-cerrar-modal>Entendido</button></div>');
    if (resultado) mostrarResultado(resultado);
  }

  // ------------------------------------------------------------ formulario: documento oficial
  function nuevoFormDoc() { return { productor: "", tipo: "", mensaje: "", intento: false, cambios: false }; }
  function tipoDoc(nombre) { for (var i = 0; i < D.tipos_documento.length; i++) if (D.tipos_documento[i].nombre === nombre) return D.tipos_documento[i]; return null; }
  function htmlTipo(t) {
    return ico("doc", "tb-ico--doc") + "<span>" + h(t.nombre) + "</span><small>" + h(t.sigla) + "</small>" + (t.conjunta ? ico("grupo") : "") + ico("campana");
  }
  function vFormDoc() {
    var req = function (c) { return F.intento && !c; };
    var t = tipoDoc(F.tipo);
    var o = '<div class="tb-form-cab"><button type="button" data-volver>' + ico("izquierda", "tb-ico--chico") + 'Formulario Documentos Oficiales</button></div><div class="tb-form">' +
      '<div class="tb-campo"><span class="tb-label">Usuario Productor<span class="tb-req">*</span></span>' +
      selectHtml("productor", F.productor, { opciones: [D.usuario.nombre].concat(D.usuarios_practica).map(function (u) { return { v: u }; }), etiqueta: "Usuario Productor", clase: "tb-select--total", invalido: req(F.productor) }) +
      (req(F.productor) ? '<p class="tb-error">Este campo es requerido</p>' : "") + "</div>" +
      '<div class="tb-campo"><span class="tb-label">Tipo de Documento<span class="tb-req">*</span></span>' +
      selectHtml("tipodoc", F.tipo, { opciones: D.tipos_documento.map(function (x) { return { v: x.nombre, extra: x.sigla, html: htmlTipo(x) }; }), etiqueta: "Tipo de Documento", clase: "tb-select--total",
        valorHtml: t ? '<span style="display:flex;align-items:center;gap:14px">' + htmlTipo(t) + "</span>" : "", invalido: req(F.tipo) }) +
      (req(F.tipo) ? '<p class="tb-error">Este campo es requerido</p>' : "") + "</div>" +
      (t && t.descripcion ? "<p>Descripción: " + h(t.descripcion) + "</p>" : "") +
      '<span class="tb-label" style="margin-top:20px">Mensaje para el Productor del Documento</span><textarea class="tb-textarea" data-campo="mensaje">' + h(F.mensaje) + "</textarea>" +
      '<div class="tb-sub">Archivos de trabajo (No formarán parte del documento)</div><div class="tb-tabla"><div class="tb-tabla__cab">Archivo de Trabajo</div><div class="tb-tabla__fila tb-tabla__fila--vacia">Aún no has agregado ningún registro</div></div>' +
      '<div class="tb-link-agregar"><button type="button" data-agregar-archivo>' + ico("agregar", "tb-ico--naranja") + "Agregar archivo</button></div>" +
      '<div class="tb-guardar" style="margin-top:14px"><button type="button" class="tb-btn" data-guardar-doc>Guardar</button></div></div>';
    return o;
  }
  function guardarDoc() {
    F.intento = true;
    if (!F.productor || !F.tipo) { render(); return; }
    var d = { tipo: F.tipo, productor: F.productor, mensaje: F.mensaje.trim(), fecha: hoy(), numero: "SDO-PRACTICA-" + String(S.docs.length + 1).padStart(4, "0") };
    S.docs.push(d); guardar();
    var resultado = ejercicioActivo === "cd01" ? evaluarCd01(d) : null;
    F = null; tabDoc = 1;
    location.hash = "#/documentos_oficiales";
    modal('<div class="tb-confirmar" style="width:420px;text-align:left"><h2>Documento iniciado (simulación)</h2><p>Lo vas a ver en la pestaña <b>«Iniciados por mi»</b>. En TIMBÓ real, después lo produce el <b>Usuario Productor</b> y se firma; esas pantallas no se relevaron todavía.</p>' +
      '<button type="button" class="tb-btn" data-cerrar-modal>Entendido</button></div>');
    if (resultado) mostrarResultado(resultado);
  }

  // ------------------------------------------------------------ modales
  function modal(html) { var m = $("#tb-modal"); m.innerHTML = html; m.hidden = false; }
  function cerrarModal() { var m = $("#tb-modal"); m.hidden = true; m.innerHTML = ""; }
  function avisoSim(texto) { modal('<div class="tb-confirmar" style="width:380px"><p>' + h(texto) + '</p><button type="button" class="tb-btn" data-cerrar-modal>OK</button></div>'); }
  function confirmarDescartar() {
    modal('<div class="tb-confirmar"><h2>¿Desea volver y descartar los cambios realizados?</h2><p>Esta acción no se puede deshacer.</p>' +
      '<button type="button" class="tb-btn tb-btn--gris" data-cerrar-modal>Cancelar</button><button type="button" class="tb-btn tb-btn--rojo" data-descartar>Descartar</button></div>');
  }
  function modalResponsable() {
    modal('<div class="tb-dialogo"><h2>Edición de Responsable</h2><span class="tb-label">Usuario<span class="tb-req">*</span></span>' +
      '<select class="tb-input" id="sim-resp"><option value="">Seleccione una opción</option>' + D.usuarios_practica.map(function (u) { return "<option>" + h(u) + "</option>"; }).join("") + "</select>" +
      '<p class="sim-fuente">Simulador: usuarios de práctica inventados.</p><div class="tb-dialogo__botones"><button type="button" class="tb-btn tb-btn--gris" data-cerrar-modal>Cancelar</button><button type="button" class="tb-btn" data-agregar-resp-ok>Agregar</button></div></div>');
  }
  // Guía de Proceso oficial de un procedimiento (clave de D.guias), con el formato del PDF de TIMBÓ.
  function visorGuia(clave) {
    var g = D.guias[clave || "gd-monto-menor-tope"];
    if (F) F.vioGuia = true;
    var pagoMostrado = false;
    var p = g.pasos.map(function (x) {
      var esquema = "";
      if (g.esquema_paso3 && x.n === 3) {
        esquema = "<table><tr><th>Tipo</th><th>Documento</th><th>Referencia</th></tr>" + g.esquema_paso3.map(function (r) { return "<tr><td>" + r.map(h).join("</td><td>") + "</td></tr>"; }).join("") + "</table>";
      } else if (x.esquema && x.esquema.length) {
        esquema = '<p class="tb-pdf__esquema"><b>Esquema:</b> ' + x.esquema.map(h).join(" · ") + "</p>";
      }
      var titulo = "";
      if (x.etapa === "pago" && !pagoMostrado) { pagoMostrado = true; titulo = "<h3>Gestión de Pago</h3>"; }
      return titulo + '<li value="' + x.n + '"><b>[' + h(x.area) + "] - " + h(x.nombre) + ".</b> " + h(x.texto) +
        (x.items.length ? "<ul>" + x.items.map(function (i) { return "<li>" + h(i) + "</li>"; }).join("") + "</ul>" : "") + (x.nota ? "<p>" + h(x.nota) + "</p>" : "") + esquema + "</li>";
    }).join("");
    modal('<div class="tb-visor"><div class="tb-visor__cab"><span>' + h(g.titulo) + '</span><button type="button" data-cerrar-modal aria-label="clear">' + ico("cerrar") + "</button></div>" +
      '<div class="tb-visor__cuerpo"><div class="tb-pdf"><div class="tb-pdf__logo">timbó</div><div class="tb-pdf__cinta">Procedimientos Administrativos Digitales</div><div><h2>' + h(g.encabezado) + "</h2></div>" +
      g.intro.map(function (t) { return "<p>" + h(t) + "</p>"; }).join("") + (g.nota_previa ? "<p>" + h(g.nota_previa) + "</p>" : "") +
      "<h3>Paso a Paso</h3><ol>" + p + "</ol>" + (g.contacto.length ? "<h3>Información de contacto</h3>" + g.contacto.map(function (t) { return "<p>" + h(t) + "</p>"; }).join("") : "") +
      '<p class="sim-fuente">Simulador: texto transcripto de la Guía de Proceso oficial de TIMBÓ (25/11/2026), sin la marca de agua personal.</p></div></div></div>');
  }

  // ------------------------------------------------------------ ejercicios y evaluación
  var EJERCICIOS = [
    { id: "caratula", titulo: "1. Pedir la carátula de una compra directa", nivel: "Pantallas",
      consigna: "El servicio de Informática necesita comprar 2 mouses y el monto está por debajo del tope de la compra directa. Pedí la carátula del expediente: Expedientes › Solicitud de caratulación › «+».",
      pistas: ["El tema del trámite lo dice el paso 1 de la Guía de Proceso.", "Si la oficina elegida no tiene «Código de Identificación», TIMBÓ no te deja seguir.", "Antes de guardar podés abrir la «Guía de Proceso» para ver el circuito completo."] },
    { id: "cd01", titulo: "2. Iniciar el CD-01 como Documento Oficial", nivel: "Pantallas",
      consigna: "Para la misma compra, iniciá la «Solicitud de contratación directa» (CD-01) desde Documentos oficiales › Gestión › «+».",
      pistas: ["La Guía de Proceso dice que el CD-01 se puede generar desde el módulo de Documentos Oficiales.", "Usuario Productor y Tipo de Documento son obligatorios."] },
    { id: "quien", titulo: "3. Circuito completo: ¿quién hace cada paso?", nivel: "Evaluación · elegís el procedimiento",
      consigna: "Todos los pasos del procedimiento, de la carátula al final. Elegí qué área hace cada uno." },
    { id: "docs", titulo: "4. ¿En qué paso va cada documento?", nivel: "Evaluación · elegís el procedimiento",
      consigna: "Para cada documento, elegí en qué paso de la Guía de Proceso se incorpora al expediente." },
    { id: "orden", titulo: "5. Ordená los pasos", nivel: "Evaluación · elegís el procedimiento",
      consigna: "Los pasos están mezclados. Elegí el número de orden de cada uno según la Guía de Proceso." }
  ];
  var ejercicioActivo = null, panelVista = "inicio", quiz = null, plegado = false, quizPendiente = null;
  function nombreGuia(k) { return D.guias[k].titulo; }

  function registrar(id, puntos, total) {
    S.hist.push({ ej: id, fecha: hoy(), puntos: puntos, total: total }); guardar();
  }
  function evaluarCaratula() {
    var ultimo = S.sol[S.sol.length - 1];
    var checks = [
      { ok: ultimo.tramite === TRAMITE_MMT, t: "Código del Trámite: «" + TRAMITE_MMT + "»", f: "Guía de Proceso, paso 1: «Solicitar carátula… bajo tema “Compras y Contrataciones - Gestión Directa - por Monto Menor al Tope”»." },
      { ok: true, t: "Oficina con Código de Identificación", f: "Regla del sistema: sin código, TIMBÓ muestra «La Oficina seleccionada no posee Código de Identificación.» y no deja seguir." },
      { ok: !!ultimo.motivo, t: "Motivo cargado", f: "Campo obligatorio del formulario." }
    ];
    var extra = [{ ok: !!(F && F.vioGuia), t: "Abriste la Guía de Proceso (recomendado, no suma puntos)" }];
    var pts = checks.filter(function (c) { return c.ok; }).length;
    registrar("caratula", pts, checks.length);
    return { id: "caratula", checks: checks, extra: extra, pts: pts, total: checks.length };
  }
  function evaluarCd01(d) {
    var checks = [
      { ok: d.tipo === "CD01-Solicitud de contratación directa", t: "Tipo de Documento: «CD01-Solicitud de contratación directa»", f: "Guía de Proceso: «Los archivos CD-01 “Solicitud de Contratación Directa”… pueden ser generados a partir del módulo de Documentos Oficiales»." },
      { ok: !!d.productor, t: "Usuario Productor elegido", f: "Campo obligatorio del formulario." }
    ];
    var pts = checks.filter(function (c) { return c.ok; }).length;
    registrar("cd01", pts, checks.length);
    return { id: "cd01", checks: checks, extra: [], pts: pts, total: checks.length };
  }
  function mostrarResultado(r) {
    panelVista = { resultado: r };
    pintarPanel(true);
  }

  function nuevoQuiz(id, clave) {
    var g = D.guias[clave], base = { id: id, guia: clave, resp: {}, corregido: false };
    if (id === "quien") {
      var areas = [];
      g.pasos.forEach(function (p) { if (areas.indexOf(p.area) < 0) areas.push(p.area); });
      base.preguntas = g.pasos.map(function (p) { return { titulo: "Paso " + p.n + " · " + p.nombre, correcta: p.area, detalle: p.texto }; });
      base.opciones = mezclar(areas);
      return base;
    }
    if (id === "orden") {
      base.preguntas = mezclar(g.pasos).map(function (p) { return { titulo: "[" + p.area + "] " + p.nombre, correcta: String(p.n), detalle: p.texto }; });
      base.opciones = g.pasos.map(function (p) { return String(p.n); });
      return base;
    }
    var docs = [];
    g.pasos.forEach(function (p) {
      p.items.forEach(function (i) {
        var t = i.replace(/\s*\(Referencia sugerida.*$/, "").replace(/\s*-\s*\(Recurso.*$/, "").replace(/^\d+(\.\d+|\.[a-z])+\.\s*/, "");
        if (t.length > 3) docs.push({ titulo: t, correcta: "Paso " + p.n + " · " + p.nombre, detalle: "[" + p.area + "]" });
      });
    });
    base.preguntas = mezclar(docs).slice(0, 12);
    base.opciones = g.pasos.filter(function (p) { return p.items.length; }).map(function (p) { return "Paso " + p.n + " · " + p.nombre; });
    return base;
  }
  // Procedimientos que sirven para cada ejercicio (el 4 necesita documentos en al menos dos pasos).
  function guiasPara(id) {
    return Object.keys(D.guias).filter(function (k) {
      var pasos = D.guias[k].pasos;
      return id !== "docs" || pasos.filter(function (p) { return p.items.length; }).length >= 2;
    });
  }
  function htmlElegirGuia() {
    var ej = EJERCICIOS.filter(function (e) { return e.id === quizPendiente; })[0];
    return "<h3>" + h(ej.titulo) + "</h3><p>¿Con qué procedimiento querés practicar? Todos salen de su Guía de Proceso oficial.</p>" +
      guiasPara(quizPendiente).map(function (k) {
        return '<button type="button" class="sim-ej" data-quiz-guia="' + k + '"><b>' + h(nombreGuia(k)) + "</b><small>" + D.guias[k].pasos.length + " pasos</small></button>";
      }).join("") + '<button type="button" class="sim-boton sim-boton--claro" data-panel-inicio>Volver</button>';
  }
  function htmlQuiz() {
    var q = quiz, ej = EJERCICIOS.filter(function (e) { return e.id === q.id; })[0];
    var bien = 0;
    var cuerpo = q.preguntas.map(function (p, k) {
      var r = q.resp[k] || "";
      var estado = q.corregido ? (r === p.correcta ? "ok" : "mal") : "";
      if (estado === "ok") bien++;
      return '<div class="sim-quiz__paso ' + estado + '"><b>' + h(p.titulo) + '</b><select data-quiz="' + k + '" ' + (q.corregido ? "disabled" : "") + '><option value="">Elegí…</option>' +
        q.opciones.map(function (o) { return "<option" + (o === r ? " selected" : "") + ">" + h(o) + "</option>"; }).join("") + "</select>" +
        (q.corregido && estado === "mal" ? '<small>Correcto: <b>' + h(p.correcta) + "</b></small>" : "") +
        (q.corregido ? '<br><small>' + h(p.detalle) + "</small>" : "") + "</div>";
    }).join("");
    return "<h3>" + h(ej.titulo) + "</h3><p><b>" + h(nombreGuia(q.guia)) + "</b> · <a href=\"#\" data-ver-guia=\"" + q.guia + "\">ver la guía</a></p><p>" + h(ej.consigna) + "</p>" +
      (q.corregido ? '<div class="sim-nota ' + (bien === q.preguntas.length ? "sim-nota--ok" : "") + '"><span class="sim-puntaje">' + bien + " / " + q.preguntas.length + "</span></div>" : "") + cuerpo +
      (q.corregido ? '<button type="button" class="sim-boton" data-quiz-guia="' + q.guia + '" data-quiz-id="' + q.id + '">Hacerlo de nuevo</button>' : '<button type="button" class="sim-boton" data-corregir>Corregir</button>') +
      '<button type="button" class="sim-boton sim-boton--claro" data-panel-inicio>Volver</button>' +
      '<p class="sim-fuente">Fuente: Guía de Proceso «' + h(nombreGuia(q.guia)) + '» (TIMBÓ, Biblioteca de Procedimientos Administrativos).</p>';
  }
  function pintarPanel(abrir) {
    var p = $("#sim-panel");
    if (abrir) p.hidden = false;
    p.classList.toggle("sim-panel--abajo", !!ejercicioActivo && panelVista === "ejercicio");
    var o = '<h2>🎯 Práctica<button type="button" data-sim="panel" aria-label="Cerrar">✕</button></h2>';
    if (panelVista && panelVista.resultado) {
      var r = panelVista.resultado;
      o += '<div class="sim-nota ' + (r.pts === r.total ? "sim-nota--ok" : "sim-nota--mal") + '"><span class="sim-puntaje">' + r.pts + " / " + r.total + "</span></div><ul class=\"sim-chk\">" +
        r.checks.concat(r.extra).map(function (c) { return '<li class="' + (c.ok ? "ok" : "mal") + '">' + h(c.t) + (c.f ? "<small>" + h(c.f) + "</small>" : "") + "</li>"; }).join("") + "</ul>" +
        '<button type="button" class="sim-boton" data-ej="' + r.id + '">Hacerlo de nuevo</button><button type="button" class="sim-boton sim-boton--claro" data-panel-inicio>Otros ejercicios</button>';
    } else if (panelVista === "quiz" && quiz) {
      o += htmlQuiz();
    } else if (panelVista === "elegirGuia") {
      o += htmlElegirGuia();
    } else if (ejercicioActivo && plegado) {
      var ejp = EJERCICIOS.filter(function (e) { return e.id === ejercicioActivo; })[0];
      o = '<h2>🎯 ' + h(ejp.titulo) + '<button type="button" data-desplegar aria-label="Ver consigna" title="Ver consigna">▴</button></h2>';
    } else if (ejercicioActivo) {
      var ej = EJERCICIOS.filter(function (e) { return e.id === ejercicioActivo; })[0];
      o = '<h2>🎯 Práctica<button type="button" data-plegar aria-label="Plegar" title="Plegar">▾</button></h2>';
      o += "<h3>" + h(ej.titulo) + "</h3><p>" + h(ej.consigna) + "</p>" + (ej.pistas ? '<details><summary>Pistas</summary><ul>' + ej.pistas.map(function (x) { return "<li>" + h(x) + "</li>"; }).join("") + "</ul></details>" : "") +
        '<p><small>Cuando toques «Guardar» te muestro el puntaje.</small></p><button type="button" class="sim-boton sim-boton--claro" data-panel-inicio>Cancelar ejercicio</button>';
    } else {
      o += "<p>Elegí un ejercicio. Los de <b>Pantallas</b> se hacen en el simulador; los de <b>Evaluación</b> se responden acá.</p>" +
        EJERCICIOS.map(function (e) { return '<button type="button" class="sim-ej" data-ej="' + e.id + '"><b>' + h(e.titulo) + "</b><small>" + h(e.nivel) + "</small></button>"; }).join("") +
        '<p class="sim-fuente">Relevado de TIMBÓ el ' + h(D.relevado_al.split("-").reverse().join("/")) + ". Todo queda en este navegador.</p>";
      if (S.hist.length) {
        o += "<h3>Tus resultados</h3><ol class=\"sim-historial\" reversed>" + S.hist.slice(-8).reverse().map(function (x) {
          var partes = x.ej.split(":"), e = EJERCICIOS.filter(function (y) { return y.id === partes[0]; })[0];
          var cual = partes[1] && D.guias[partes[1]] ? " (" + nombreGuia(partes[1]) + ")" : "";
          return "<li>" + h((e ? e.titulo : x.ej) + cual) + ": <b>" + x.puntos + "/" + x.total + "</b> <small>" + h(x.fecha) + "</small></li>";
        }).join("") + "</ol>";
      }
      o += '<button type="button" class="sim-boton sim-boton--claro" data-reiniciar>Vaciar bandejas de práctica</button>';
    }
    p.innerHTML = o;
  }
  function empezarEjercicio(id) {
    if (id === "quien" || id === "docs" || id === "orden") { quizPendiente = id; panelVista = "elegirGuia"; ejercicioActivo = null; quiz = null; pintarPanel(true); return; }
    ejercicioActivo = id; panelVista = "ejercicio"; quiz = null; plegado = false;
    location.hash = "#/dashboard";
    pintarPanel(true);
  }

  // ------------------------------------------------------------ pantallas relevadas el 25/11 (segunda tanda)
  // Formularios «simples»: guardan sus valores en G y comparten validación y avisos.
  var G = null;
  function nuevoG(id) { return { id: id, v: {}, intento: false, buscado: false }; }
  function hoyISO(dias) { var d = new Date(); d.setDate(d.getDate() + (dias || 0)); return d.toISOString().slice(0, 10); }
  function gv(k) { return G.v[k] == null ? "" : G.v[k]; }
  function gReq(k) { return G.intento && !String(gv(k)).trim(); }
  function errReq(k) { return gReq(k) ? '<p class="tb-error">Este campo es requerido</p>' : ""; }
  function gTexto(k, label, req, extra) {
    return '<div class="tb-campo"><span class="tb-label">' + h(label) + (req ? '<span class="tb-req">*</span>' : "") + (extra || "") + "</span>" +
      '<input class="tb-input ' + (req && gReq(k) ? "invalido" : "") + '" data-g="' + k + '" value="' + h(gv(k)) + '"></div>' + (req ? errReq(k) : "");
  }
  function gFecha(k, label, req) {
    return '<div class="tb-campo"><span class="tb-label">' + h(label) + (req ? '<span class="tb-req">*</span>' : "") + "</span>" +
      '<div class="tb-fecha"><input type="date" class="tb-input" data-g="' + k + '" value="' + h(gv(k)) + '">' +
      (gv(k) ? '<button type="button" class="tb-select__x" data-g-limpiar="' + k + '" aria-label="Limpiar fecha">' + ico("cerrar") + "</button>" : "") + "</div></div>";
  }
  function gSelect(k, label, req, opciones, clase) {
    return '<div class="tb-campo"><span class="tb-label">' + h(label) + (req ? '<span class="tb-req">*</span>' : "") + "</span>" +
      selectHtml("g:" + k, gv(k), { opciones: opciones.map(function (o) { return { v: o }; }), etiqueta: label, clase: clase || "", invalido: req && gReq(k) }) + (req ? errReq(k) : "") + "</div>";
  }
  function gLupa(k, label, req) {
    return '<div class="tb-campo"><span class="tb-label">' + h(label) + (req ? '<span class="tb-req">*</span>' : "") + "</span>" +
      '<div class="tb-lupa"><input class="tb-input ' + (req && gReq(k) ? "invalido" : "") + '" data-g="' + k + '" value="' + h(gv(k)) + '"><button type="button" class="tb-lupa__btn" data-g-buscar>' + ico("buscar", "tb-ico--naranja") + "</button></div>" +
      (req ? errReq(k) : "") + "</div>";
  }
  function tablaVacia(cols) {
    return '<div class="tb-tabla tb-tabla--cols"><div class="tb-tabla__cab tb-tabla__cab--cols">' + cols.map(function (c) { return "<span>" + h(c) + "</span>"; }).join("") +
      '</div><div class="tb-tabla__fila tb-tabla__fila--vacia">Aún no has agregado ningún registro</div></div>' +
      '<div class="tb-paginas"><span>Anterior</span><b>1</b><span>Siguiente</span></div>';
  }
  function tituloLinea(t) { return '<div class="tb-titulo tb-titulo--linea"><h1>' + h(t) + "</h1></div>"; }
  var NOTA_PAPEL = '<p class="tb-nota-papel">Los expedientes generados en formato papel se podrán consultar desde: <a href="https://www.santafe.gov.ar/expedientes-web/" target="_blank" rel="noopener">https://www.santafe.gov.ar/expedientes-web/</a></p>';

  function vConsultaEE() {
    var t = gv("tipo"), o = tituloLinea("Consulta") + '<div class="tb-form tb-form--corto">' + gSelect("tipo", "Tipo de búsqueda", true, D.consulta_ee_tipos, "tb-select--chico");
    if (t === "Numero de Expediente") {
      o += gLupa("nro", "Nro de Expediente", true);
      if (G.buscado && gv("nro")) o += '<p class="sim-nota">En TIMBÓ, con un número que no existe, el campo queda gris y no muestra resultado. El simulador no tiene expedientes reales.</p>';
    } else if (t) {
      o += '<div class="tb-grilla4">' + gFecha("desde", "Desde", true) + gFecha("hasta", "Hasta", true) +
        gSelect("tramite", "Trámite", false, D.tramites.map(function (x) { return x.nombre; })) + gTexto("motivo", "Motivo", false) + "</div>";
      if (G.buscado && (!gv("desde") || !gv("hasta"))) o += '<p class="tb-error tb-error--grande">Debe completar el rango de fechas donde encontrar los expedientes</p>';
      o += '<button type="button" class="tb-btn-borde" data-g-buscar>Buscar</button>';
      if (G.buscado && gv("desde") && gv("hasta")) o += tablaVacia(["Nro. de EE", "Iniciador", "Trámite", "Motivo"]);
    }
    return o + NOTA_PAPEL + "</div>";
  }
  function vVisibilidadEE() {
    return tituloLinea("Visibilidad") + '<div class="tb-form tb-form--corto">' + gLupa("nro", "Buscar Expediente", false) +
      (G.buscado ? '<p class="sim-nota">Lo que muestra TIMBÓ al buscar acá no se relevó (con el usuario relevado no había expedientes).</p>' : "") + "</div>";
  }
  function vGestionVis() {
    return encabezadoLista("Gestión de visualización", true) + pestanas(["En Curso", "Finalizadas", "Vistas Compartidas"], 0) +
      filtros([{ txt: "Buscar" }, { dd: "Buscar Etiqueta" }, { dd: "Estadío" }, { chip: "Fecha de creación - Más reciente" }, { fecha: "Desde" }, { fecha: "Hasta" }]) + VACIO;
  }
  function vNuevoTramite(lista, base) {
    return '<div class="tb-form-cab"><button type="button" data-ir="' + base + '">' + ico("izquierda", "tb-ico--chico") + 'Nuevo Trámite</button></div>' +
      '<div class="tb-nuevo"><label class="tb-filtro tb-nuevo__buscar"><input type="text" placeholder="Buscar">' + ico("buscar", "tb-ico--chico") + "</label>" +
      '<p class="tb-nuevo__cuenta">' + lista.length + " trámites disponibles</p>" + lista.map(function (t, k) {
        return '<button type="button" class="tb-nuevo__fila" data-ir="' + base + "/form/" + (k + 1) + '"><span class="tb-punto"></span>' + h(t) + '<span class="tb-nuevo__iniciar">Iniciar ' + ico("derecha", "tb-ico--chico") + "</span></button>";
      }).join("") + "</div>";
  }
  function cabForm(t) { return '<div class="tb-form-cab"><button type="button" data-volver>' + ico("izquierda", "tb-ico--chico") + h(t) + "</button></div>"; }
  function vVistaForm1() {
    return cabForm("Formulario Gestión de visualización de expedientes") + '<div class="tb-form"><div class="tb-sub" style="margin-top:20px">Búsqueda de Expediente</div>' +
      gLupa("nro", "Numero de Expediente", true) + (G.buscado && gv("nro") ? '<p class="sim-nota">Lo que sigue después de buscar un expediente no se relevó.</p>' : "") + "</div>";
  }
  function vVistaForm2() {
    var filtrosK = ["nro", "tema", "motivo", "solicitante", "fdesde", "fhasta", "ofcar", "ofact"];
    var hayFiltro = filtrosK.some(function (k) { return String(gv(k)).trim(); });
    if (gv("inicio") === "") G.v.inicio = hoyISO(0);
    return cabForm("Formulario Compartir Vista de Expediente") + '<div class="tb-form"><div class="tb-sub" style="margin-top:10px">Datos del Iniciador</div>' +
      '<div class="tb-grilla4"><div><span class="tb-label">Nombre</span><input class="tb-input tb-input--gris" value="USUARIO DE" readonly></div><div><span class="tb-label">Apellido</span><input class="tb-input tb-input--gris" value="PRÁCTICA" readonly></div>' +
      '<div><span class="tb-label">Email</span><input class="tb-input tb-input--gris" value="' + h(D.usuario.email) + '" readonly></div><div><span class="tb-label">Oficina</span><input class="tb-input tb-input--gris" value="Oficina de práctica" readonly></div></div>' +
      '<div class="tb-sub">Filtros de Búsqueda</div><div class="tb-grilla4">' + gTexto("nro", "Número de Expediente") + gTexto("tema", "Tema/Código de Trámite") + gTexto("motivo", "Motivo") + gTexto("solicitante", "Solicitante") +
      gFecha("fdesde", "Fecha de Modificación (Desde)") + gFecha("fhasta", "Fecha de Modificación (Hasta)") +
      gSelect("ofcar", "Oficina Caratuladora Superior", false, D.oficinas_superiores) + gSelect("ofact", "Oficina Actual Superior", false, D.oficinas_superiores) + "</div>" +
      (G.buscado && !hayFiltro ? '<p class="tb-error">Debe indicar algún filtro para la búsqueda de EE</p>' : "") +
      '<div class="tb-derecha"><button type="button" class="tb-btn-borde" data-g-buscar>Buscar</button></div>' +
      '<p class="tb-ok">El límite de expedientes por búsqueda es de 1000. El límite para seleccionar es de 500.</p>' +
      (G.buscado && hayFiltro ? '<p class="tb-error tb-error--grande">No se han encontrado expedientes.</p>' : "") +
      '<div class="tb-sub">Expedientes</div>' + tablaVacia(["Número de Expediente", "Tema", "Motivo", "Solicitante", "Oficina Caratuladora", "Oficina Actual", "Fecha de Modificación"]) +
      '<div class="tb-sub">Expedientes Seleccionados</div>' + tablaVacia(["Número de Expediente", "Tema", "Motivo", "Solicitante", "Oficina Caratuladora", "Oficina Actual", "Fecha de Modificación"]) +
      '<div class="tb-derecha"><button type="button" class="tb-btn-borde" data-nada-sim>Reiniciar Selección</button></div>' +
      '<div class="tb-sub">Agregar Destinatarios</div>' + gSelect("dest", "Agregar Destinatarios Desde:", true, ["Usuarios", "Lista de Agentes", "Oficina", "Lista de Ciudadanos", "Ciudadanos"], "tb-select--chico") +
      (gv("dest") ? '<p class="sim-nota">Lo que se completa después de elegir «' + h(gv("dest")) + '» no se relevó.</p>' : "") +
      '<div class="tb-derecha"><button type="button" class="tb-btn-borde" data-nada-sim>Reiniciar Selección</button></div>' +
      '<div class="tb-sub">Fechas de Visualización</div><div class="tb-grilla4">' + gFecha("inicio", "Fecha de Inicio de Visualización", true) + gFecha("fin", "Fecha de Fin de Visualización", true) + "</div>" + errReq("fin") +
      '<div class="tb-guardar"><button type="button" class="tb-btn" data-g-guardar="dest,fin">Guardar</button></div></div>';
  }
  function vConsultaDO() {
    var t = gv("tipo"), o = tituloLinea("Consulta") + '<div class="tb-form tb-form--corto">' + gSelect("tipo", "Tipo de búsqueda", true, D.consulta_do_tipos, "tb-select--chico");
    if (t === "Documentos Firmados por Mi" || t === "Documentos Firmados por Mi Repartición") {
      if (gv("desde") === "" && !G.vDesde) { G.v.desde = hoyISO(-15); G.v.hasta = hoyISO(0); G.vDesde = true; }
      o += '<div class="tb-grilla4">' + gFecha("desde", "Desde", true) + gFecha("hasta", "Hasta", true) +
        '<div class="tb-campo"><span class="tb-label">Filtrar por Tipo de Actuación</span><div class="tb-select__caja"><span>' + h(D.tipos_actuacion.join(", ")) + '</span>' + ico("cerrar", "tb-ico--rojo") + "</div></div></div>" +
        '<button type="button" class="tb-btn-borde" data-g-buscar>Buscar</button>' +
        (G.buscado ? tablaVacia(["Nro. de DO", "Nro. de Proceso", "Usuario Protocolizador", "Referencia", "Fecha", "Firmantes", "Responsables"]) : "");
    } else if (t) {
      o += '<p class="sim-nota">Los campos de la búsqueda «' + h(t) + '» no se relevaron todavía.</p>';
    }
    return o + "</div>";
  }
  function vInternas() {
    return '<div class="tb-titulo"><h1>Internas</h1></div><div class="tb-tabs">' + ["Recibidas (0)", "Enviadas (0)", "Eliminadas (0)"].map(function (t, k) {
      return '<button type="button" class="tb-tab ' + (k === 0 ? "activo" : "") + '">' + t + "</button>"; }).join("") + "</div>" +
      filtros([{ txt: "Buscar" }, { fecha: "Desde" }, { fecha: "Hasta" }]) +
      '<div class="tb-filtros" style="padding-top:0"><button type="button" class="tb-pildora activo">Todos (0)</button><button type="button" class="tb-pildora">No Leídos (0)</button></div>' + VACIO;
  }
  function vExternas() {
    return '<div class="tb-titulo"><h1>Externas</h1></div><div class="tb-tabs">' + ["Enviadas (0)", "No Entregadas (0)", "Archivadas (0)"].map(function (t, k) {
      return '<button type="button" class="tb-tab ' + (k === 0 ? "activo" : "") + '">' + t + "</button>"; }).join("") + "</div>" +
      filtros([{ txt: "N° de Proceso" }, { txt: "CUIL/CUIT destinatario" }, { dd: "Tipo de remitente" }, { txt: "Remitente" }, { dd: "Proceso" }, { fecha: "Desde" }, { fecha: "Hasta" }]) +
      '<p class="sim-fuente" style="padding:0 16px">«Tipo de remitente»: Usuario | Oficina. «Proceso»: Documentos Oficiales | Compras y Contrataciones.</p>' + VACIO;
  }
  function vListas(titulo, base) {
    return '<div class="tb-titulo"><h1>' + h(titulo) + '</h1></div><div class="tb-listas"><label class="tb-filtro"><input type="text" placeholder="Filtrar listas">' + ico("buscar", "tb-ico--chico") +
      '</label><button type="button" class="tb-btn" data-ir="' + base + '/nueva">+ Nueva lista</button></div>' + VACIO;
  }
  function vNuevaLista(base) {
    var t = gv("tipo");
    return '<div class="tb-form-cab"><button type="button" data-ir="' + base + '">' + ico("izquierda", "tb-ico--chico") + "Volver</button></div>" +
      '<div class="tb-form tb-form--corto"><div class="tb-sub" style="margin-top:6px">Creación de nueva lista</div>' + gSelect("tipo", "Seleccionar tipo de creación", true, ["Nueva lista", "Importar lista"], "tb-select--chico") +
      (t === "Nueva lista" ? gTexto("nombre", "Nombre de nueva lista") + '<button type="button" class="tb-btn" data-aviso="En el simulador no se crean listas. Lo que pasa después de «+ Nueva lista» no se relevó.">+ Nueva lista</button>' : "") +
      (t === "Importar lista" ? '<div class="tb-campo"><span class="tb-label">Importar lista</span><button type="button" class="tb-btn-borde" data-aviso="En el simulador no se suben archivos.">Examinar</button></div><button type="button" class="tb-btn" data-aviso="Lo que pasa al importar no se relevó.">+ Importar lista</button>' : "") + "</div>";
  }
  var bibPagina = 0;
  function vBiblioteca() {
    var f = sinTildes(gv("texto").trim());
    var lista = D.biblioteca.filter(function (b) { return !f || sinTildes(b.nombre + " " + b.descripcion).indexOf(f) >= 0; });
    var paginas = Math.max(1, Math.ceil(lista.length / 10));
    if (bibPagina >= paginas) bibPagina = 0;
    return '<div class="tb-titulo"><h1>Biblioteca de Procedimientos Administrativos</h1></div><div class="tb-filtros tb-filtros--bib">' +
      '<div class="tb-select tb-select--chico"><div class="tb-select__caja"><span>Tipo de Trámite</span>' + ico("desplegar", "tb-ico--chico") + "</div></div>" +
      '<div class="tb-select tb-select--chico"><div class="tb-select__caja"><span>ComprasYContrataciones</span>' + ico("cerrar", "tb-ico--rojo") + "</div></div>" +
      '<label class="tb-filtro"><input type="text" placeholder="Buscar" data-g="texto" value="' + h(gv("texto")) + '">' + ico("buscar", "tb-ico--chico") + '</label><button type="button" class="tb-btn-borde" data-g-buscar>Buscar</button></div>' +
      '<p class="sim-fuente" style="padding:0 16px">Simulador: solo se copiaron los 20 procedimientos con la palabra clave «ComprasYContrataciones».</p>' +
      '<div class="tb-bib"><div class="tb-bib__fila tb-bib__fila--cab"><span>Nombre</span><span>Descripción</span><span>Tipo Trámite</span><span>Palabras Clave Relacionadas</span><span></span></div>' +
      lista.slice(bibPagina * 10, bibPagina * 10 + 10).map(function (b) {
        return '<div class="tb-bib__fila"><span>' + h(b.nombre) + "</span><span>" + h(b.descripcion) + "</span><span>" + h(b.tipo) + '</span><span><span class="tb-bib__n">1</span></span>' +
          '<button type="button" class="tb-tarjeta__menu" data-bib-menu="' + h(b.nombre) + '" aria-label="Abrir menú">' + ico("tresPuntos") + "</button></div>";
      }).join("") + '</div><div class="tb-paginas"><button type="button" data-bib-pag="' + (bibPagina - 1) + '"' + (bibPagina === 0 ? " disabled" : "") + ">Anterior</button>" +
      Array.from({ length: paginas }, function (_, k) { return '<button type="button" data-bib-pag="' + k + '" class="' + (k === bibPagina ? "activo" : "") + '">' + (k + 1) + "</button>"; }).join("") +
      '<button type="button" data-bib-pag="' + (bibPagina + 1) + '"' + (bibPagina >= paginas - 1 ? " disabled" : "") + ">Siguiente</button></div>";
  }
  function previsualizarBib(nombre) {
    var b = D.biblioteca.filter(function (x) { return x.nombre === nombre; })[0];
    if (!b) return;
    var g = b.guia;
    if (g.indexOf("guia:") === 0) { visorGuia(g.slice(5)); return; }
    var cuerpo;
    if (g.indexOf("generica:") === 0) {
      var gen = D.guias_genericas[g.split(":")[1]];
      cuerpo = '<div class="tb-pdf__logo">timbó</div><h3>' + h(gen.titulo) + "</h3>" + gen.texto.map(function (t) { return "<p>" + h(t) + "</p>"; }).join("") +
        "<p><b>Asunto:</b> Especificar el “Nombre del Proceso Administrativo/Trámite”</p><p><b>Cuerpo:</b> Se deben describir los siguientes aspectos:</p><ol type=\"a\">" +
        gen.pedido.map(function (t) { return "<li>" + h(t) + "</li>"; }).join("") + "</ol>";
    } else {
      var n = g.indexOf("paginas:") === 0 ? g.split(":")[1] : "?";
      cuerpo = '<div class="tb-pdf__logo">timbó</div><p class="sim-nota">La guía oficial de este procedimiento tiene <b>' + h(n) + " páginas</b>. Todavía no se transcribió al simulador (solo se transcribió la de «Gestión Directa - Por Monto Menor al Tope»).</p>";
    }
    modal('<div class="tb-visor"><div class="tb-visor__cab"><span>' + h(b.nombre) + '</span><button type="button" data-cerrar-modal aria-label="clear">' + ico("cerrar") + '</button></div><div class="tb-visor__cuerpo"><div class="tb-pdf">' + cuerpo + "</div></div></div>");
  }
  function vConsultaUsuarios() {
    var corto = G.buscado && String(gv("usuario")).trim().length < 3;
    return tituloLinea("Consulta de usuarios") + '<div class="tb-form"><div class="tb-grilla4">' +
      gTexto("usuario", "Usuario", false, ' <span title="help" class="tb-ayuda">?</span>') + gSelect("rep", "Repartición de Nivel Superior", false, D.oficinas_superiores) +
      '<div class="tb-campo"><span class="tb-label">&nbsp;</span><button type="button" class="tb-btn-borde" data-g-buscar>Buscar</button></div></div>' +
      '<p class="' + (corto ? "tb-error" : "tb-ayuda-txt") + '">El campo de texto "Usuario" debe tener mínimamente 3 caracteres para realizar la búsqueda.</p>' +
      '<div class="tb-sub">Listado de usuarios</div>' + tablaVacia(["Nombre y Apellido", "CUIL", "Correo electrónico", "Oficinas a las que pertenece"]) + "</div>";
  }
  function vAutorregistro() {
    return encabezadoLista("Autorregistro", true) + pestanas(["En Curso", "Aprobadas", "Rechazadas"], 0) +
      filtros([{ txt: "Buscar usuario" }, { txt: "Buscar por Cargo" }, { fecha: "Modificado Desde" }, { fecha: "Modificado Hasta" }, { fecha: "Desde" }, { fecha: "Hasta" }]) + VACIO;
  }
  function vAutorregistroForm() {
    return cabForm("Formulario Autorregistro de Usuario") + '<div class="tb-form"><div class="tb-sub" style="margin-top:10px">Datos del Usuario</div><div class="tb-grilla4">' +
      gTexto("cuil", "CUIL", true) + gTexto("nombre", "Nombre", true) + gTexto("apellido", "Apellido", true) + gTexto("email", "Email", true) + "</div>" +
      '<div class="tb-sub">Seleccionar Oficina</div>' + gSelect("sup", "Oficina de Nivel Superior", true, D.oficinas_superiores) +
      '<p class="tb-ayuda-txt">Deberá seleccionar una oficina de nivel inferior. Si no se encuentra, comuníquese con el área informática de su dependencia.</p>' +
      (gv("sup") ? '<p class="sim-nota">El selector de oficina de nivel inferior que aparece después no se relevó en esta pantalla.</p>' : "") +
      '<span class="tb-label" style="margin-top:18px">Observaciones</span><textarea class="tb-textarea" data-g="obs">' + h(gv("obs")) + "</textarea>" +
      '<p class="tb-ayuda-txt">Se enviará este formulario al evaluador local de oficinas para confirmación.</p>' +
      '<div class="tb-guardar"><button type="button" class="tb-btn" data-g-guardar="cuil,nombre,apellido,email,sup">Guardar</button></div></div>';
  }
  function vApoderamientos() {
    return tituloLinea("Consulta de Apoderamientos") + '<div class="tb-form tb-form--corto">' + gSelect("tipo", "Tipo de busqueda", true, ["Búsqueda por entidad", "Búsqueda por apoderado"], "tb-select--chico") +
      (gv("tipo") ? '<p class="sim-nota">Los campos de «' + h(gv("tipo")) + '» no se relevaron todavía.</p>' : "") + "</div>";
  }
  function historialDoc(numero) {
    var d = S.docs.filter(function (x) { return x.numero === numero; })[0];
    if (!d) return;
    modal('<div class="tb-historial"><h2>Historial</h2><div class="tb-historial__item"><b>' + h(D.usuario.nombre) + "</b> " + h(d.fecha) +
      '<p>Completó el formulario</p><p>Realizó la acción: <b>Enviar a Producir</b></p></div><p class="sim-fuente">Simulado con los textos reales del historial de un documento oficial. En TIMBÓ, después siguen «Enviar a Firmar» y «Notificar firmante», y el estadío pasa a «Firmar Documento Oficial».</p>' +
      '<div class="tb-historial__pie"><span>' + h(d.numero) + '</span><button type="button" class="tb-btn tb-btn--chico" data-cerrar-modal>Cerrar</button></div></div>');
  }
  function menuFlotante(btn, items) {
    cerrarFlotante();
    var r = btn.getBoundingClientRect(), m = document.createElement("div");
    m.className = "tb-flotante"; m.id = "tb-flotante";
    m.style.top = (r.bottom + 4) + "px"; m.style.left = Math.max(8, r.right - 190) + "px";
    m.innerHTML = items.map(function (it, k) { return '<button type="button" data-flot="' + k + '">' + ico(it[0]) + h(it[1]) + "</button>"; }).join("");
    m._items = items;
    document.body.appendChild(m);
  }
  function cerrarFlotante() { var m = document.getElementById("tb-flotante"); if (m) m.remove(); }

  // ------------------------------------------------------------ render
  function render() {
    var ruta = location.hash.split("?")[0] || "#/dashboard";
    var v = $("#tb-vista"), html;
    if (ruta === "#/solicitud_caratulacion/create") { if (!F || F.clase !== "sol") { F = nuevoFormSol(); F.clase = "sol"; } html = vFormSol(); }
    else if (ruta === "#/documentos_oficiales/create") { if (!F || F.clase !== "doc") { F = nuevoFormDoc(); F.clase = "doc"; } html = vFormDoc(); }
    else {
      F = null;
      if (!G || G.id !== ruta) G = nuevoG(ruta);
      var RUTAS = {
        "#/consulta_ee": vConsultaEE, "#/admin_visibilidad_ee": vVisibilidadEE, "#/solicitud_vista_expediente": vGestionVis,
        "#/solicitud_vista_expediente/create": function () { return vNuevoTramite(["Solicitud vista de expediente", "Compartir Vista de Expediente"], "#/solicitud_vista_expediente"); },
        "#/solicitud_vista_expediente/form/1": vVistaForm1, "#/solicitud_vista_expediente/form/2": vVistaForm2,
        "#/consulta_do": vConsultaDO, "#/communications_internas": vInternas, "#/communications_externas": vExternas,
        "#/users_distribution_list": function () { return vListas("Agentes", "#/users_distribution_list"); },
        "#/citizens_distribution_list": function () { return vListas("Ciudadanos", "#/citizens_distribution_list"); },
        "#/users_distribution_list/nueva": function () { return vNuevaLista("#/users_distribution_list"); },
        "#/citizens_distribution_list/nueva": function () { return vNuevaLista("#/citizens_distribution_list"); },
        "#/bibloteca_de_procedimientos_administrativos": vBiblioteca, "#/consulta_de_usuarios": vConsultaUsuarios,
        "#/autorregistro": vAutorregistro,
        "#/autorregistro/create": function () { return vNuevoTramite(["Autorregistro de usuarios"], "#/autorregistro"); },
        "#/autorregistro/form/1": vAutorregistroForm, "#/entity_attorneys_lookup": vApoderamientos
      };
      if (RUTAS[ruta]) html = RUTAS[ruta]();
      else if (ruta === "#/solicitud_caratulacion") html = vSolicitudes();
      else if (ruta === "#/expedientes") html = vExpedientes();
      else if (ruta === "#/documentos_oficiales") html = vDocumentos();
      else if (ruta.indexOf("#/nr/") === 0) html = vNoRelevado(decodeURIComponent(ruta.slice(5)));
      else html = vDashboard();
    }
    var foco = document.activeElement && document.activeElement.dataset ? document.activeElement.dataset : {};
    v.innerHTML = html;
    pintarIconosNav();
    if (foco.selFiltro) { var inp = $('[data-sel-filtro="' + foco.selFiltro + '"]'); if (inp) { inp.focus(); inp.setSelectionRange(inp.value.length, inp.value.length); } }
    else if (selAbierto) { var i2 = $('[data-sel-filtro="' + selAbierto + '"]'); if (i2) i2.focus(); }
  }

  function elegir(id, valor) {
    selAbierto = null; selFiltro = "";
    if (id.indexOf("g:") === 0) { G.v[id.slice(2)] = valor; if (id === "g:tipo") { G.buscado = false; G.intento = false; } render(); return; }
    F.cambios = true;
    if (id === "tramite") F.tramite = valor;
    else if (id === "sup") { F.sup = valor; F.inf = ""; }
    else if (id === "inf") F.inf = valor;
    else if (id === "productor") F.productor = valor;
    else if (id === "tipodoc") F.tipo = valor;
    render();
  }
  function limpiar(id) {
    if (id.indexOf("g:") === 0) { G.v[id.slice(2)] = ""; if (id === "g:tipo") { G = nuevoG(G.id); } render(); return; }
    F.cambios = true;
    if (id === "tramite") { F.tramite = ""; F.sup = ""; F.inf = ""; }
    else if (id === "sup") { F.sup = ""; F.inf = ""; }
    else if (id === "inf") F.inf = "";
    else if (id === "productor") F.productor = "";
    else if (id === "tipodoc") F.tipo = "";
    render();
  }

  // ------------------------------------------------------------ eventos
  document.addEventListener("click", function (e) {
    // Con un ejercicio en curso, el panel se pliega al usar las pantallas para no tapar nada.
    if (ejercicioActivo && !plegado && panelVista === "ejercicio" && e.target.closest(".tb-app")) { plegado = true; pintarPanel(false); }
    if (!e.target.closest("#tb-flotante")) cerrarFlotante();
    var b = e.target.closest("button, a, [data-sel]");
    if (!b) {
      if (selAbierto && !e.target.closest(".tb-select")) { selAbierto = null; selFiltro = ""; render(); }
      return;
    }
    var ds = b.dataset;
    if (ds.sim === "menu") { if ($("#tb-menu").hidden) abrirMenu(null); else cerrarMenu(); return; }
    if (ds.sim === "panel") { var p = $("#sim-panel"); if (p.hidden) pintarPanel(true); else p.hidden = true; return; }
    if (ds.nav != null) { var m = MENU[+ds.nav]; if (m.sub) abrirMenu(+ds.nav); else irA(m.ir, m.t); return; }
    if (ds.item != null) { var mi = MENU[+ds.item]; if (mi.sub) abrirMenu(+ds.item); else irA(mi.ir, mi.t); return; }
    if (ds.sub != null) { var s = MENU[menuAbierto].sub[+ds.sub]; irA(s.ir, MENU[menuAbierto].t + " · " + s.t); return; }
    if (ds.menuVolver != null) { abrirMenu(null); return; }
    if (ds.ir) { G = null; location.hash = ds.ir; return; }
    if (ds.aviso) { avisoSim(ds.aviso); return; }
    if (ds.nadaSim != null) { avisoSim("En el simulador no hay expedientes para seleccionar."); return; }
    if (ds.bandeja != null) { bandejaSel = +ds.bandeja; render(); return; }
    if (ds.gLimpiar) { G.v[ds.gLimpiar] = ""; render(); return; }
    if (ds.gBuscar != null) { G.buscado = true; render(); return; }
    if (ds.gGuardar) {
      G.intento = true;
      var faltan = ds.gGuardar.split(",").filter(function (k) { return !String(gv(k)).trim(); });
      render();
      if (!faltan.length) avisoSim("Formulario completo. En el simulador no se envía: lo que pasa en TIMBÓ después de «Guardar» no se relevó.");
      return;
    }
    if (ds.bibPag != null) { bibPagina = +ds.bibPag; render(); return; }
    if (ds.bibMenu) { var nb = ds.bibMenu; menuFlotante(b, [["ojo", "Previsualizar", function () { previsualizarBib(nb); }], ["descargar", "Descargar", function () { avisoSim("En el simulador no se descargan archivos. En TIMBÓ, «Descargar» baja el PDF de la guía."); }]]); return; }
    if (ds.docMenu) {
      var nd = ds.docMenu;
      menuFlotante(b, [["flujo", "Ver Flujo", function () { modal('<div class="tb-confirmar" style="width:420px"><h2>Flujo</h2><p>En el relevamiento, «Ver Flujo» se quedó en «CARGANDO» (Versión: 2.0.2). Su contenido no se pudo ver.</p><button type="button" class="tb-btn" data-cerrar-modal>OK</button></div>'); }],
        ["info", "Guía de proceso", function () { avisoSim("La guía de proceso de este tipo de documento no se relevó."); }],
        ["ojo", "Previsualizar", function () { avisoSim("La previsualización del documento no se relevó."); }],
        ["historial", "Historial", function () { historialDoc(nd); }]]);
      return;
    }
    if (ds.flot != null) { var mf = document.getElementById("tb-flotante"); var acc = mf._items[+ds.flot][2]; cerrarFlotante(); acc(); return; }
    if (ds.usuario != null) { menuFlotante(b, [["cuenta", "Cerrar sesión", function () { avisoSim("En el simulador no hay sesión que cerrar. En TIMBÓ, este menú solo tiene «Cerrar sesión»."); }]]); return; }
    if (ds.tab != null) {
      var r = location.hash.split("?")[0];
      if (r === "#/solicitud_caratulacion") tabSol = +ds.tab; else if (r === "#/expedientes") tabExp = +ds.tab; else tabDoc = +ds.tab;
      render(); return;
    }
    if (ds.pildora != null) { pildora = +ds.pildora; render(); return; }
    if (ds.mas != null) { var r2 = location.hash.split("?")[0]; F = null; location.hash = r2 + "/create"; return; }
    if (ds.acciones != null) { avisoSim(location.hash.indexOf("expedientes") >= 0 ? "Acciones › Gestionar Etiquetas (la pantalla de etiquetas no se relevó)." : "El menú «Acciones» de esta bandeja no se relevó."); return; }
    if (ds.volver != null) { confirmarDescartar(); return; }
    if (ds.descartar != null) { cerrarModal(); F = null; G = null; location.hash = location.hash.split("?")[0].replace(/\/(create|form|nueva)(\/.*)?$/, ""); return; }
    if (ds.cerrarModal != null) { cerrarModal(); return; }
    if (ds.sel) { selAbierto = selAbierto === ds.sel ? null : ds.sel; selFiltro = ""; render(); return; }
    if (ds.selOp) { elegir(ds.selOp, ds.v); return; }
    if (ds.selLimpiar) { limpiar(ds.selLimpiar); return; }
    if (ds.selMas) { selCargados[ds.selMas] = (selCargados[ds.selMas] || 5) + 30; render(); return; }
    if (ds.guia != null) { visorGuia(guiaDe(F.tramite)); return; }
    if (ds.agregarResp != null) { modalResponsable(); return; }
    if (ds.agregarRespOk != null) { var u = $("#sim-resp").value; if (!u) { $("#sim-resp").classList.add("invalido"); return; } if (F.responsables.indexOf(u) < 0) F.responsables.push(u); F.cambios = true; cerrarModal(); render(); return; }
    if (ds.quitarResp != null) { F.responsables.splice(+ds.quitarResp, 1); render(); return; }
    if (ds.agregarArchivo != null) { avisoSim("En el simulador no se suben archivos: los «Archivos de trabajo» no forman parte del documento."); return; }
    if (ds.guardarSol != null) { guardarSol(); return; }
    if (ds.guardarDoc != null) { guardarDoc(); return; }
    if (ds.nada != null) { e.preventDefault(); return; }
    if (ds.ej) { empezarEjercicio(ds.ej); return; }
    if (ds.quizGuia) { if (ds.quizId) quizPendiente = ds.quizId; quiz = nuevoQuiz(quizPendiente, ds.quizGuia); panelVista = "quiz"; pintarPanel(true); $("#sim-panel").scrollTop = 0; return; }
    if (ds.verGuia) { e.preventDefault(); visorGuia(ds.verGuia); return; }
    if (ds.plegar != null) { plegado = true; pintarPanel(false); return; }
    if (ds.desplegar != null) { plegado = false; pintarPanel(true); return; }
    if (ds.panelInicio != null) { ejercicioActivo = null; panelVista = "inicio"; quiz = null; pintarPanel(true); return; }
    if (ds.corregir != null) {
      quiz.corregido = true;
      var bien = quiz.preguntas.filter(function (q, k) { return quiz.resp[k] === q.correcta; }).length;
      registrar(quiz.id + ":" + quiz.guia, bien, quiz.preguntas.length);
      pintarPanel(true); $("#sim-panel").scrollTop = 0; return;
    }
    if (ds.reiniciar != null) { S.sol = []; S.docs = []; guardar(); render(); avisoSim("Listo: las bandejas de práctica quedaron vacías. Tus resultados se conservan."); return; }
  });
  $("#tb-cortina").addEventListener("click", cerrarMenu);
  document.addEventListener("input", function (e) {
    var t = e.target;
    if (t.dataset.selFiltro) { selFiltro = t.value; render(); return; }
    if (t.dataset.campo && F) { F[t.dataset.campo] = t.value; F.cambios = true; return; }
    if (t.dataset.g && G) { G.v[t.dataset.g] = t.value; return; }
  });
  document.addEventListener("change", function (e) {
    var t = e.target;
    if (t.dataset.quiz != null) { quiz.resp[+t.dataset.quiz] = t.value; return; }
    if (t.dataset.g && G && t.type === "date") { G.v[t.dataset.g] = t.value; render(); return; }
    if (!F) return;
    if (t.name === "tipo") { F.tipo = t.value; F.cambios = true; render(); }
    else if (t.name === "vis") { F.visibilidad = t.value; }
    else if (t.name === "plat") { F.plataforma = t.value; render(); }
    else if (t.dataset.urgente != null) { F.urgente = t.checked; F.cambios = true; render(); }
    else if (t.dataset.relacionado != null) { F.relacionado = t.checked; F.plataforma = ""; render(); }
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") { if (!$("#tb-modal").hidden) cerrarModal(); else if (selAbierto) { selAbierto = null; render(); } else cerrarMenu(); }
  });
  window.addEventListener("hashchange", function () { cerrarMenu(); selAbierto = null; render(); });

  pintarIconos();
  if (!location.hash) location.hash = "#/dashboard";
  render();
  if (!S.visto) { S.visto = true; guardar(); pintarPanel(true); }
})();
