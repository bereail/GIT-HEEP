/* Planilla de revisión de artículos por servicio (HTML descargable).
 *
 * El trabajo se guarda en tres lugares, de más automático a más seguro:
 *  1. En el navegador (IndexedDB + copia en localStorage), en cada cambio.
 *     Sobrevive a cerrar o recargar, pero se pierde si se borran los datos
 *     de navegación.
 *  2. En un "archivo de trabajo" .json de la PC (File System Access API, solo
 *     Chrome / Edge), reescrito en cada cambio. No depende del navegador.
 *  3. En copias de seguridad que la persona descarga.
 * Cada guardado lleva un número correlativo y la sesión (pestaña) que lo
 * hizo: si otra pestaña, otra PC o una copia vieja tienen respuestas
 * distintas, se avisa y se pregunta antes de pisar nada.
 */
(function () {
  "use strict";

  var DATOS = JSON.parse(document.getElementById("rs-datos").textContent);
  var ITEMS = DATOS.items;
  var POR_ID = new Map(ITEMS.map(function (i) { return [i.id, i]; }));
  var CLAVE = DATOS.bodega + "::" + DATOS.versionDatos;
  var PREFIJO_LS = "centro-revision-servicio::";
  var SESION = Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 8);
  var POR_PAGINA = 15;
  var AVISO_COPIA_CADA = 50;
  var MAX_HISTORIAL = 20;
  var MAX_REGISTRO = 500;
  var FORMATO_ESTADO = "revision-servicio-estado/1";
  var FORMATO_DEVOLUCION = "revision-servicio-devolucion/1";
  var SLUG = DATOS.bodega.normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

  var RESULTADOS = {
    correcto: "Correcto / corresponde",
    no_corresponde: "No corresponde",
    no_necesario: "No necesario",
    aclaracion: "Requiere aclaración"
  };
  var AYUDA = {
    1: { correcto: "Se necesita y no está en el catálogo", no_corresponde: "No es un artículo de este servicio", no_necesario: "El servicio ya no lo usa", aclaracion: "Lo encontré en el catálogo o tengo dudas" },
    2: { correcto: "El código propuesto es este artículo", no_corresponde: "El código propuesto es otro artículo", no_necesario: "El servicio ya no lo usa", aclaracion: "Tengo dudas" },
    3: { correcto: "El código propuesto es este artículo", no_corresponde: "El código propuesto es otro artículo", no_necesario: "El servicio ya no lo usa", aclaracion: "Tengo dudas" }
  };
  var INSTRUCCIONES = {
    1: {
      titulo: "1 · Artículos que faltan cargar",
      texto: "La comparación automática no encontró estos artículos en el Catálogo WEB de la Provincia.",
      pasos: [
        "Buscá el artículo en el Catálogo WEB (santafe.gob.ar/gestionesdecompras → Catálogo) con otras palabras, sinónimos o un término más general.",
        "Si lo encontrás, marcá «Requiere aclaración» y anotá el código en observaciones.",
        "Si no existe y el servicio lo necesita, marcá «Correcto / corresponde».",
        "Si el servicio ya no lo usa, marcá «No necesario». Si no es de este servicio, «No corresponde»."
      ]
    },
    2: {
      titulo: "2 · Artículos que necesitan confirmación",
      texto: "La comparación automática encontró un ítem parecido, pero no idéntico. Que los nombres se parezcan no alcanza: hay que comparar.",
      pasos: [
        "Compará el artículo con el código propuesto: descripción, presentación, unidad de medida, medidas o calibre, concentración o composición, y uso previsto.",
        "Si es el mismo artículo, marcá «Correcto / corresponde».",
        "Si el código propuesto es otra cosa, marcá «No corresponde». Si conocés el código correcto, anotalo en observaciones.",
        "Si el servicio ya no lo usa, «No necesario». Si tenés dudas, «Requiere aclaración» y explicá cuál."
      ]
    },
    3: {
      titulo: "3 · Artículos que ya existen y deben verificarse",
      texto: "La comparación automática encontró un ítem con las mismas palabras clave y los mismos números. Igual hay que verificarlo: puede fallar, por ejemplo, en una medida.",
      pasos: [
        "Verificá que el código propuesto sea exactamente este artículo: presentación, unidad, medidas y características.",
        "Si coincide, «Correcto / corresponde». Si no, «No corresponde» y anotá la diferencia.",
        "Si el servicio ya no lo usa, «No necesario». Si tenés dudas, «Requiere aclaración»."
      ]
    }
  };

  // ------------------------------------------------------------ estado ----
  function ahora() { return new Date().toISOString(); }

  function estadoNuevo() {
    return {
      formato: FORMATO_ESTADO,
      formatoPlanilla: DATOS.formato,
      bodega: DATOS.bodega,
      versionDatos: DATOS.versionDatos,
      generado: DATOS.generado,
      servicio: "", nombre: "", apellido: "", observaciones: "",
      inicio: null, modificado: null, finalizado: null,
      guardado: 0, sesion: SESION,
      ultimaCopia: null, cambiosDesdeCopia: 0,
      respuestas: {}, huerfanas: {}, registro: []
    };
  }

  var estado = estadoNuevo();
  var ui = { seccion: 1, pagina: 0, buscar: "", filtro: "" };
  var persistencia = {
    db: null, navegadorOk: null, navegadorHora: null, persistente: null,
    handle: null, archivoPermiso: false, archivoPausado: false, archivoHora: null, archivoError: "",
    baseLocal: 0, baseArchivo: 0
  };

  function registrar(accion, detalle) {
    estado.registro.push({ t: ahora(), accion: accion, detalle: detalle || "", sesion: SESION });
    if (estado.registro.length > MAX_REGISTRO) estado.registro.splice(0, estado.registro.length - MAX_REGISTRO);
  }

  function respuesta(id) { return estado.respuestas[id] || null; }
  function revisado(id) { var r = respuesta(id); return !!(r && r.r); }

  // ------------------------------------------------------ almacenamiento ---
  function abrirDB() {
    return new Promise(function (resolver, rechazar) {
      if (!window.indexedDB) { rechazar(new Error("sin IndexedDB")); return; }
      var pedido = indexedDB.open("centro-revision-servicio", 1);
      pedido.onupgradeneeded = function () {
        var db = pedido.result;
        if (!db.objectStoreNames.contains("estados")) db.createObjectStore("estados");
        if (!db.objectStoreNames.contains("archivos")) db.createObjectStore("archivos");
      };
      pedido.onsuccess = function () { resolver(pedido.result); };
      pedido.onerror = function () { rechazar(pedido.error); };
    });
  }
  function idb(almacen, modo, operacion) {
    return new Promise(function (resolver, rechazar) {
      if (!persistencia.db) { rechazar(new Error("sin base")); return; }
      var tx = persistencia.db.transaction(almacen, modo);
      var pedido = operacion(tx.objectStore(almacen));
      tx.oncomplete = function () { resolver(pedido && pedido.result); };
      tx.onerror = function () { rechazar(tx.error); };
      tx.onabort = function () { rechazar(tx.error); };
    });
  }
  function idbLeer(almacen, clave) { return idb(almacen, "readonly", function (s) { return s.get(clave); }); }
  function idbGuardar(almacen, clave, valor) { return idb(almacen, "readwrite", function (s) { return s.put(valor, clave); }); }
  function idbClaves(almacen) { return idb(almacen, "readonly", function (s) { return s.getAllKeys(); }); }

  function lsLeer(clave) {
    try { var t = localStorage.getItem(PREFIJO_LS + clave); return t ? JSON.parse(t) : null; } catch (e) { return null; }
  }
  function lsGuardar(clave, texto) {
    try { localStorage.setItem(PREFIJO_LS + clave, texto); return true; } catch (e) { return false; }
  }
  function lsClaves() {
    var r = [];
    try { for (var i = 0; i < localStorage.length; i++) { var k = localStorage.key(i); if (k.indexOf(PREFIJO_LS) === 0) r.push(k.slice(PREFIJO_LS.length)); } } catch (e) { /* sin acceso */ }
    return r;
  }

  // Mientras se tipea, localStorage se actualiza al instante con el mismo
  // número de guardado que IndexedDB todavía tiene sin ese texto: ante un
  // empate gana la versión modificada más tarde.
  function masNuevo(a, b) {
    if (!a) return b; if (!b) return a;
    if ((b.guardado || 0) !== (a.guardado || 0)) return (b.guardado || 0) > (a.guardado || 0) ? b : a;
    return (b.modificado || "") > (a.modificado || "") ? b : a;
  }

  async function leerGuardadoLocal(clave) {
    var deIdb = null;
    try { deIdb = await idbLeer("estados", clave); } catch (e) { deIdb = null; }
    return masNuevo(deIdb || null, lsLeer(clave));
  }

  // Los guardados van en fila, uno por vez, para que nunca se crucen.
  var cola = Promise.resolve();
  var temporizadorTexto = null;
  var temporizadorArchivo = null;
  var hayCambiosSinGuardar = false;

  function guardar(inmediato) {
    hayCambiosSinGuardar = true;
    clearTimeout(temporizadorTexto);
    if (inmediato) {
      cola = cola.then(guardarLocal).catch(function () {});
    } else {
      // Mientras se escribe, la copia en localStorage es inmediata (sincrónica)
      // y el resto espera a que se deje de tipear.
      lsGuardar(CLAVE, JSON.stringify(estado));
      temporizadorTexto = setTimeout(function () { cola = cola.then(guardarLocal).catch(function () {}); }, 500);
    }
  }

  async function guardarLocal() {
    var otro = await leerGuardadoLocal(CLAVE);
    if (otro && otro.sesion !== SESION && (otro.guardado || 0) > persistencia.baseLocal) {
      conflictoCon(otro, "otra pestaña o ventana de este navegador");
      return;
    }
    estado.guardado = Math.max(estado.guardado || 0, otro ? otro.guardado || 0 : 0) + 1;
    estado.sesion = SESION;
    var texto = JSON.stringify(estado);
    var okIdb = false;
    try { await idbGuardar("estados", CLAVE, JSON.parse(texto)); okIdb = true; } catch (e) { okIdb = false; }
    var okLs = lsGuardar(CLAVE, texto);
    persistencia.navegadorOk = okIdb || okLs;
    persistencia.navegadorHora = new Date();
    persistencia.baseLocal = estado.guardado;
    hayCambiosSinGuardar = false;
    if (canal) { try { canal.postMessage({ sesion: SESION, guardado: estado.guardado }); } catch (e) { /* nada */ } }
    if (persistencia.persistente === null && navigator.storage && navigator.storage.persist) {
      try { persistencia.persistente = await navigator.storage.persist(); } catch (e) { persistencia.persistente = false; }
    }
    programarArchivo();
    pintarGuardado();
  }

  // --------------------------------------------------- archivo de trabajo --
  var hayApiArchivos = typeof window.showSaveFilePicker === "function";

  function programarArchivo() {
    if (!persistencia.handle || !persistencia.archivoPermiso || persistencia.archivoPausado) return;
    clearTimeout(temporizadorArchivo);
    temporizadorArchivo = setTimeout(function () { cola = cola.then(escribirArchivo).catch(function () {}); }, 1000);
  }

  async function leerArchivo(handle) {
    var archivo = await handle.getFile();
    var texto = await archivo.text();
    if (!texto.trim()) return null;
    return JSON.parse(texto);
  }

  async function escribirArchivo() {
    var h = persistencia.handle;
    if (!h || !persistencia.archivoPermiso || persistencia.archivoPausado) return;
    try {
      var enDisco = null;
      try { enDisco = await leerArchivo(h); } catch (e) { enDisco = null; }
      if (enDisco && enDisco.sesion !== SESION && (enDisco.guardado || 0) > persistencia.baseArchivo) {
        persistencia.archivoPausado = true;
        pintarGuardado();
        alerta("atencion", "El archivo de trabajo fue modificado desde otra ventana o PC. Para no pisar esas respuestas, se pausó el guardado en el archivo.", "Revisar diferencias", function () {
          conflictoCon(enDisco, "el archivo de trabajo");
        });
        return;
      }
      var escritor = await h.createWritable();
      await escritor.write(JSON.stringify(estado));
      await escritor.close();
      persistencia.baseArchivo = estado.guardado;
      persistencia.archivoHora = new Date();
      persistencia.archivoError = "";
    } catch (e) {
      persistencia.archivoError = "No se pudo escribir el archivo (" + (e && e.name ? e.name : "error") + ").";
    }
    pintarGuardado();
  }

  function validarAjeno(obj) {
    if (!obj || typeof obj !== "object") return "El archivo no es una revisión válida.";
    var esEstado = typeof obj.formato === "string" && obj.formato.indexOf("revision-servicio-estado/") === 0;
    var esDevolucion = typeof obj.formato === "string" && obj.formato.indexOf("revision-servicio-devolucion/") === 0;
    if (!esEstado && !esDevolucion) return "El archivo no es una revisión de artículos por servicio.";
    if (obj.bodega !== DATOS.bodega) return "El archivo es de la bodega «" + obj.bodega + "», no de «" + DATOS.bodega + "». No se mezclan bodegas.";
    return "";
  }

  // Una devolución se puede volver a cargar: se pasa al formato de trabajo.
  function aEstado(obj) {
    if (obj.formato.indexOf("revision-servicio-devolucion/") !== 0) return obj;
    var e = estadoNuevo();
    e.versionDatos = obj.versionDatos; e.servicio = obj.servicio || ""; e.observaciones = obj.observaciones || "";
    e.nombre = (obj.responsable || {}).nombre || ""; e.apellido = (obj.responsable || {}).apellido || "";
    e.inicio = (obj.fechas || {}).inicio || null; e.modificado = (obj.fechas || {}).ultimaModificacion || null;
    e.guardado = obj.guardado || 0; e.sesion = "devolucion";
    (obj.respuestas || []).forEach(function (r) {
      if (r.resultado || r.observaciones) e.respuestas[r.codigo_interno] = { r: r.resultado || null, obs: r.observaciones || "", t: r.fecha || e.modificado, hist: r.historial || [] };
    });
    return e;
  }

  async function crearArchivo() {
    if (!hayApiArchivos) { alerta("atencion", "Este navegador no permite guardar en un archivo de la PC. Usá Chrome o Edge, o descargá copias de seguridad."); return; }
    try {
      var h = await window.showSaveFilePicker({
        suggestedName: "revision-" + SLUG + "-trabajo.json",
        types: [{ description: "Revisión de artículos (JSON)", accept: { "application/json": [".json"] } }]
      });
      persistencia.handle = h; persistencia.archivoPermiso = true; persistencia.archivoPausado = false;
      persistencia.baseArchivo = 0;
      try { await idbGuardar("archivos", CLAVE, h); } catch (e) { /* se puede reconectar a mano */ }
      registrar("archivo de trabajo creado", h.name);
      guardar(true);
      cola = cola.then(escribirArchivo);
    } catch (e) {
      if (e && e.name !== "AbortError") alerta("error", "No se pudo crear el archivo de trabajo.");
    }
  }

  async function abrirArchivo() {
    if (!hayApiArchivos) { alerta("atencion", "Este navegador no permite abrir un archivo de trabajo. Usá «Recuperar una copia»."); return; }
    try {
      var lista = await window.showOpenFilePicker({ types: [{ description: "Revisión de artículos (JSON)", accept: { "application/json": [".json"] } }] });
      await conectarArchivo(lista[0], true);
    } catch (e) {
      if (e && e.name !== "AbortError") alerta("error", "No se pudo abrir el archivo de trabajo.");
    }
  }

  async function conectarArchivo(h, esNuevo) {
    var contenido = null;
    try { contenido = await leerArchivo(h); } catch (e) { alerta("error", "El archivo elegido no se pudo leer como revisión."); return; }
    if (contenido) {
      var error = validarAjeno(contenido);
      if (error) { alerta("error", error); return; }
    }
    persistencia.handle = h; persistencia.archivoPermiso = true; persistencia.archivoPausado = false;
    persistencia.baseArchivo = contenido ? contenido.guardado || 0 : 0;
    if (esNuevo) { try { await idbGuardar("archivos", CLAVE, h); } catch (e) { /* nada */ } }
    registrar("archivo de trabajo conectado", h.name);
    if (contenido) combinar(aEstado(contenido), "el archivo de trabajo");
    else guardar(true);
    pintarGuardado();
  }

  async function reconectar() {
    var h = persistencia.handle;
    if (!h) return;
    try {
      var p = await h.requestPermission({ mode: "readwrite" });
      if (p === "granted") await conectarArchivo(h, false);
      else alerta("atencion", "Sin permiso no se puede seguir guardando en el archivo de trabajo.");
    } catch (e) { alerta("error", "No se pudo reconectar el archivo de trabajo."); }
  }

  // --------------------------------------------------- copias de seguridad --
  function descargar(nombre, texto) {
    var blob = new Blob([texto], { type: "application/json" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url; a.download = nombre;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
  }
  function sello() {
    var d = new Date(); function dos(n) { return String(n).padStart(2, "0"); }
    return d.getFullYear() + "-" + dos(d.getMonth() + 1) + "-" + dos(d.getDate()) + "_" + dos(d.getHours()) + dos(d.getMinutes());
  }

  function textoCopia() { return JSON.stringify(estado, null, 1); }

  function exportarCopia() {
    estado.ultimaCopia = ahora();
    estado.cambiosDesdeCopia = 0;
    registrar("copia de seguridad descargada", "guardado " + (estado.guardado + 1));
    guardar(true);
    // Se descarga el estado tal como queda después de este guardado.
    cola = cola.then(function () { descargar("revision-" + SLUG + "-copia-" + sello() + "-g" + estado.guardado + ".json", textoCopia()); });
  }

  function importarCopia(archivo) {
    var lector = new FileReader();
    lector.onload = function () {
      var obj;
      try { obj = JSON.parse(lector.result); } catch (e) { alerta("error", "El archivo no se pudo leer: no es un JSON válido."); return; }
      var error = validarAjeno(obj);
      if (error) { alerta("error", error); return; }
      registrar("copia importada", archivo.name);
      combinar(aEstado(obj), "la copia «" + archivo.name + "»");
    };
    lector.onerror = function () { alerta("error", "No se pudo leer el archivo."); };
    lector.readAsText(archivo);
  }

  // ------------------------------------------------- combinar y conflictos --
  function igual(a, b) { return (a.r || null) === (b.r || null) && (a.obs || "") === (b.obs || ""); }
  function vacia(a) { return !a || (!a.r && !(a.obs || "").trim()); }
  function fechaDe(a) { return a && a.t ? Date.parse(a.t) || 0 : 0; }

  function analizar(otro) {
    var ids = new Set(Object.keys(estado.respuestas).concat(Object.keys(otro.respuestas || {})));
    var res = { nuevas: [], iguales: 0, conflictos: [], huerfanas: [] };
    ids.forEach(function (id) {
      var mia = estado.respuestas[id], suya = (otro.respuestas || {})[id];
      if (!POR_ID.has(id)) { if (suya && !vacia(suya)) res.huerfanas.push(id); return; }
      if (vacia(suya)) return;
      if (vacia(mia)) { res.nuevas.push(id); return; }
      if (igual(mia, suya)) { res.iguales++; return; }
      res.conflictos.push(id);
    });
    return res;
  }

  function conHistorial(ganadora, perdedora, motivo) {
    var g = JSON.parse(JSON.stringify(ganadora));
    g.hist = (g.hist || []).slice();
    if (perdedora && !vacia(perdedora)) g.hist.push({ r: perdedora.r || null, obs: perdedora.obs || "", t: perdedora.t || null, motivo: motivo });
    if (g.hist.length > MAX_HISTORIAL) g.hist = g.hist.slice(-MAX_HISTORIAL);
    return g;
  }

  function aplicar(otro, analisis, modo, origen) {
    analisis.nuevas.forEach(function (id) { estado.respuestas[id] = JSON.parse(JSON.stringify(otro.respuestas[id])); });
    analisis.conflictos.forEach(function (id) {
      var mia = estado.respuestas[id], suya = otro.respuestas[id];
      var ganaSuya = modo === "suyas" || (modo === "recientes" && fechaDe(suya) > fechaDe(mia));
      estado.respuestas[id] = ganaSuya ? conHistorial(suya, mia, "reemplazada al combinar con " + origen) : conHistorial(mia, suya, "descartada al combinar con " + origen);
    });
    analisis.huerfanas.forEach(function (id) { estado.huerfanas[id] = otro.respuestas[id]; });
    Object.keys(otro.huerfanas || {}).forEach(function (id) { if (!estado.huerfanas[id]) estado.huerfanas[id] = otro.huerfanas[id]; });
    ["servicio", "nombre", "apellido", "observaciones"].forEach(function (campo) {
      if (!(estado[campo] || "").trim() && (otro[campo] || "").trim()) estado[campo] = otro[campo];
    });
    if (otro.inicio && (!estado.inicio || otro.inicio < estado.inicio)) estado.inicio = otro.inicio;
    if (otro.ultimaCopia && (!estado.ultimaCopia || otro.ultimaCopia > estado.ultimaCopia)) estado.ultimaCopia = otro.ultimaCopia;
    if (!estado.finalizado && otro.finalizado && !analisis.nuevas.length && !analisis.conflictos.length) estado.finalizado = otro.finalizado;
    (otro.registro || []).forEach(function (x) { if (x.sesion !== SESION) estado.registro.push(x); });
    estado.registro.sort(function (a, b) { return a.t < b.t ? -1 : 1; });
    if (estado.registro.length > MAX_REGISTRO) estado.registro.splice(0, estado.registro.length - MAX_REGISTRO);
    if (analisis.nuevas.length || analisis.conflictos.length) estado.modificado = ahora();
    registrar("combinación con " + origen, analisis.nuevas.length + " nuevas, " + analisis.iguales + " iguales, " + analisis.conflictos.length + " en conflicto (" + modo + "), " + analisis.huerfanas.length + " de artículos que ya no están");
    persistencia.baseLocal = Math.max(persistencia.baseLocal, otro.guardado || 0);
    estado.guardado = Math.max(estado.guardado || 0, otro.guardado || 0);
    if (origen === "el archivo de trabajo") { persistencia.baseArchivo = Math.max(persistencia.baseArchivo, otro.guardado || 0); persistencia.archivoPausado = false; }
    guardar(true);
    pintarTodo();
    var partes = [analisis.nuevas.length + " respuestas recuperadas", analisis.iguales + " ya estaban iguales"];
    if (analisis.conflictos.length) partes.push(analisis.conflictos.length + " diferencias resueltas");
    if (analisis.huerfanas.length) partes.push(analisis.huerfanas.length + " de artículos que ya no están en esta planilla (se conservan aparte)");
    alerta("ok", "Listo: se combinó con " + origen + ". " + partes.join(" · ") + ".");
  }

  function combinar(otro, origen) {
    var distintaVersion = otro.versionDatos && otro.versionDatos !== DATOS.versionDatos;
    var a = analizar(otro);
    if (!a.conflictos.length) { aplicar(otro, a, "recientes", origen); if (distintaVersion) avisoVersion(); return; }
    mostrarConflictos(otro, a, origen, distintaVersion);
  }

  function avisoVersion() {
    alerta("atencion", "La revisión recuperada se hizo con otra versión de la planilla. Las respuestas se unieron por código de artículo; las de artículos que ya no están se conservan aparte y van en la devolución.");
  }

  function conflictoCon(otro, origen) {
    var a = analizar(otro);
    if (!a.conflictos.length) { aplicar(otro, a, "recientes", origen); return; }
    mostrarConflictos(otro, a, origen, false);
  }

  function describir(r) {
    if (!r) return "—";
    var t = (r.r ? RESULTADOS[r.r] : "Sin resultado") + (r.obs ? " · «" + r.obs.slice(0, 80) + "»" : "");
    return t + (r.t ? " (" + new Date(r.t).toLocaleString() + ")" : "");
  }

  function mostrarConflictos(otro, a, origen, distintaVersion) {
    var cuerpo = document.createElement("div");
    var p = document.createElement("p");
    p.textContent = "Hay " + a.conflictos.length + " artículos con respuestas distintas entre esta planilla y " + origen + ". " +
      "También hay " + a.nuevas.length + " respuestas que solo están en " + origen + " (se agregan siempre). Elegí cómo resolver las diferencias:";
    cuerpo.appendChild(p);
    if (distintaVersion) { var pv = document.createElement("p"); pv.textContent = "Atención: " + origen + " es de otra versión de la planilla."; cuerpo.appendChild(pv); }
    var tabla = document.createElement("table"); tabla.className = "rs-tabla-conf";
    var cab = tabla.insertRow(); ["Artículo", "En esta planilla", "En " + origen].forEach(function (t) { var th = document.createElement("th"); th.textContent = t; cab.appendChild(th); });
    a.conflictos.slice(0, 40).forEach(function (id) {
      var fila = tabla.insertRow();
      fila.insertCell().textContent = id + " · " + (POR_ID.get(id) || { n: "" }).n;
      fila.insertCell().textContent = describir(estado.respuestas[id]);
      fila.insertCell().textContent = describir(otro.respuestas[id]);
    });
    cuerpo.appendChild(tabla);
    if (a.conflictos.length > 40) { var mas = document.createElement("p"); mas.textContent = "…y " + (a.conflictos.length - 40) + " más."; cuerpo.appendChild(mas); }
    var nota = document.createElement("p"); nota.className = "rs-nota";
    nota.textContent = "Nada se borra: la respuesta que no se elige queda en el historial del artículo.";
    cuerpo.appendChild(nota);
    abrirModal("Respuestas distintas", cuerpo, [
      { texto: "Quedarme con la más reciente de cada artículo", accion: function () { aplicar(otro, a, "recientes", origen); } },
      { texto: "Conservar las de esta planilla", claro: true, accion: function () { aplicar(otro, a, "mias", origen); } },
      { texto: "Usar las de " + origen, claro: true, accion: function () { aplicar(otro, a, "suyas", origen); } },
      { texto: "Cancelar", claro: true, accion: function () { alerta("atencion", "No se combinó nada. Ojo: mientras haya otra versión distinta, el guardado puede volver a avisar."); } }
    ]);
  }

  // --------------------------------------------------------- respuestas ---
  // `tipeando`: la observación se está escribiendo. Mientras siga siendo la
  // misma edición (mismo resultado, menos de un minuto) no se suma una
  // versión al historial por cada tecla.
  function responder(id, r, obs, tipeando) {
    var previa = estado.respuestas[id];
    var nueva = { r: r, obs: obs, t: ahora(), hist: previa ? (previa.hist || []).slice() : [] };
    var mismaEdicion = tipeando && previa && previa.r === r && Date.now() - fechaDe(previa) < 60000;
    if (previa && !vacia(previa) && !igual(previa, nueva) && !mismaEdicion) {
      nueva.hist.push({ r: previa.r || null, obs: previa.obs || "", t: previa.t || null });
      if (nueva.hist.length > MAX_HISTORIAL) nueva.hist = nueva.hist.slice(-MAX_HISTORIAL);
    }
    estado.respuestas[id] = nueva;
    if (!estado.inicio) { estado.inicio = nueva.t; registrar("revisión iniciada", ""); }
    estado.modificado = nueva.t;
    if (!mismaEdicion) estado.cambiosDesdeCopia = (estado.cambiosDesdeCopia || 0) + 1;
    if (estado.finalizado) {
      estado.finalizado = null;
      registrar("revisión reabierta", "cambio en " + id);
      alerta("atencion", "Cambiaste una respuesta después de finalizar: la revisión volvió a quedar abierta. Al terminar, finalizala de nuevo.");
    }
    if (estado.cambiosDesdeCopia > 0 && estado.cambiosDesdeCopia % AVISO_COPIA_CADA === 0) {
      alerta("atencion", "Llevás " + estado.cambiosDesdeCopia + " cambios desde la última copia de seguridad.", "Descargar copia ahora", exportarCopia);
    }
  }

  // -------------------------------------------------------------- vista ---
  var $ = function (id) { return document.getElementById(id); };

  function normal(t) { return (t || "").normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase(); }
  var INDICE = new Map(ITEMS.map(function (i) { return [i.id, normal([i.n, i.id, i.ca, i.cp, i.dn].join(" "))]; }));

  function filtrados() {
    var palabras = normal(ui.buscar).split(/\s+/).filter(Boolean);
    return ITEMS.filter(function (i) {
      if (i.s !== ui.seccion) return false;
      if (palabras.length) { var t = INDICE.get(i.id); if (!palabras.every(function (p) { return t.indexOf(p) !== -1; })) return false; }
      var r = respuesta(i.id), res = r && r.r;
      if (ui.filtro === "pendiente") return !res;
      if (ui.filtro === "revisado") return !!res;
      if (ui.filtro) return res === ui.filtro;
      return true;
    });
  }

  function elem(tag, clase, texto) { var e = document.createElement(tag); if (clase) e.className = clase; if (texto !== undefined) e.textContent = texto; return e; }

  function tarjeta(i) {
    var r = respuesta(i.id);
    var t = elem("article", "rs-tarjeta" + (r && r.r ? " r-" + r.r : ""));
    t.dataset.id = i.id;
    var cab = elem("div", "rs-tarjeta__cab");
    cab.appendChild(elem("span", "rs-tarjeta__nombre", i.n));
    var cods = elem("span", "rs-codigos");
    cods.appendChild(document.createTextNode("Código actual: "));
    cods.appendChild(elem("code", "", i.id));
    if (i.ca) { cods.appendChild(document.createTextNode(" · artículo ")); cods.appendChild(elem("code", "", i.ca)); }
    cods.appendChild(document.createTextNode(" · bodega " + DATOS.bodega));
    cab.appendChild(cods);
    t.appendChild(cab);

    var prop = elem("div", "rs-propuesto" + (i.cp ? "" : " rs-propuesto--vacio"));
    prop.appendChild(elem("p", "rs-propuesto__tit", "Nomenclador TIMBÓ (Catálogo WEB)"));
    if (i.cp) {
      var linea = elem("div");
      linea.appendChild(document.createTextNode("Código propuesto: "));
      linea.appendChild(elem("code", "", i.cp));
      var copiar = elem("button", "rs-copiar", "Copiar"); copiar.type = "button"; copiar.dataset.copiar = i.cp;
      linea.appendChild(copiar);
      prop.appendChild(linea);
      prop.appendChild(elem("div", "", i.dn));
    } else {
      prop.appendChild(elem("div", "", "Sin código propuesto: no se encontró un ítem que corresponda."));
    }
    t.appendChild(prop);

    var motivo = elem("p", "rs-motivo"); motivo.appendChild(elem("b", "", "Motivo: ")); motivo.appendChild(document.createTextNode(i.m));
    t.appendChild(motivo);
    if (i.nu) t.appendChild(elem("p", "rs-alerta-item", "⚠ El código propuesto figura en el catálogo como «NO UTILIZAR»."));
    if (i.nota || i.cd) {
      var det = elem("details", "rs-detalle"); det.appendChild(elem("summary", "", "Detalle técnico de la comparación"));
      if (i.nota) det.appendChild(elem("p", "", i.nota));
      if (i.cd) det.appendChild(elem("p", "", "Candidato descartado por la comparación automática: " + i.cd));
      t.appendChild(det);
    }

    var botones = elem("div", "rs-respuestas"); botones.setAttribute("role", "group"); botones.setAttribute("aria-label", "Resultado");
    Object.keys(RESULTADOS).forEach(function (k) {
      var b = elem("button", "rs-res"); b.type = "button"; b.dataset.r = k;
      b.setAttribute("aria-pressed", r && r.r === k ? "true" : "false");
      b.appendChild(document.createTextNode(RESULTADOS[k]));
      b.appendChild(elem("small", "", AYUDA[i.s][k]));
      botones.appendChild(b);
    });
    t.appendChild(botones);
    var obs = elem("textarea", "rs-obs"); obs.rows = 2; obs.maxLength = 2000; obs.placeholder = "Observaciones (opcional)"; obs.value = r ? r.obs || "" : "";
    obs.setAttribute("aria-label", "Observaciones de " + i.n);
    t.appendChild(obs);
    var pie = elem("div", "rs-tarjeta__pie");
    pie.appendChild(elem("span", "rs-guardado-item", r && r.t ? "Guardado " + new Date(r.t).toLocaleString() : "Sin revisar"));
    var borrar = elem("button", "rs-borrar", "Quitar resultado"); borrar.type = "button"; borrar.hidden = !(r && r.r);
    pie.appendChild(borrar);
    t.appendChild(pie);
    return t;
  }

  function actualizarTarjeta(t, id) {
    var r = respuesta(id);
    t.className = "rs-tarjeta" + (r && r.r ? " r-" + r.r : "");
    t.querySelectorAll(".rs-res").forEach(function (b) { b.setAttribute("aria-pressed", r && r.r === b.dataset.r ? "true" : "false"); });
    t.querySelector(".rs-guardado-item").textContent = r && r.t ? "Guardado " + new Date(r.t).toLocaleString() : "Sin revisar";
    t.querySelector(".rs-borrar").hidden = !(r && r.r);
  }

  function pintarLista() {
    var lista = filtrados();
    var paginas = Math.max(1, Math.ceil(lista.length / POR_PAGINA));
    if (ui.pagina >= paginas) ui.pagina = paginas - 1;
    if (ui.pagina < 0) ui.pagina = 0;
    var cont = $("rs-lista"); cont.textContent = "";
    var trozo = lista.slice(ui.pagina * POR_PAGINA, (ui.pagina + 1) * POR_PAGINA);
    if (!trozo.length) cont.appendChild(elem("div", "rs-vacio", "No hay artículos con este filtro en esta sección."));
    trozo.forEach(function (i) { cont.appendChild(tarjeta(i)); });
    $("rs-resultados").textContent = lista.length + " artículos" + (ui.buscar || ui.filtro ? " con este filtro" : " en esta sección");
    $("rs-pagina").textContent = "Página " + (ui.pagina + 1) + " de " + paginas;
    $("rs-ant").disabled = ui.pagina === 0;
    $("rs-sig").disabled = ui.pagina >= paginas - 1;
    guardarUi();
  }

  function contar() {
    var c = { total: ITEMS.length, revisados: 0, correcto: 0, no_corresponde: 0, no_necesario: 0, aclaracion: 0, porSeccion: { 1: [0, 0], 2: [0, 0], 3: [0, 0] } };
    ITEMS.forEach(function (i) {
      var r = respuesta(i.id); c.porSeccion[i.s][1]++;
      if (r && r.r) { c.revisados++; c[r.r]++; c.porSeccion[i.s][0]++; }
    });
    c.pendientes = c.total - c.revisados;
    return c;
  }

  function pintarAvance() {
    var c = contar();
    $("rs-revisados").textContent = c.revisados; $("rs-pendientes").textContent = c.pendientes;
    $("rs-avance-relleno").style.width = (c.total ? (100 * c.revisados / c.total) : 0).toFixed(1) + "%";
    document.querySelectorAll("[data-cuenta]").forEach(function (s) {
      var p = c.porSeccion[s.dataset.cuenta]; s.textContent = p[0] + " de " + p[1] + " revisados";
    });
    document.querySelectorAll(".rs-tab").forEach(function (b) { b.classList.toggle("activa", Number(b.dataset.seccion) === ui.seccion); });
    var res = $("rs-resumen"); res.textContent = "";
    [["Total", c.total], ["Correctos / corresponden", c.correcto], ["No corresponden", c.no_corresponde], ["No necesarios", c.no_necesario], ["Requieren aclaración", c.aclaracion], ["Pendientes", c.pendientes]].forEach(function (x) {
      var d = elem("div"); d.appendChild(elem("b", "", String(x[1]))); d.appendChild(elem("span", "", x[0])); res.appendChild(d);
    });
    function f(v) { return v ? new Date(v).toLocaleString() : "—"; }
    $("rs-f-inicio").textContent = f(estado.inicio); $("rs-f-mod").textContent = f(estado.modificado); $("rs-f-fin").textContent = f(estado.finalizado);
  }

  function pintarInstrucciones() {
    var ins = INSTRUCCIONES[ui.seccion], cont = $("rs-instrucciones"); cont.textContent = "";
    cont.appendChild(elem("h2", "", ins.titulo));
    cont.appendChild(elem("p", "", ins.texto));
    var ol = elem("ol"); ins.pasos.forEach(function (p) { ol.appendChild(elem("li", "", p)); }); cont.appendChild(ol);
  }

  function pintarIdentificacion() {
    [["rs-servicio", "servicio"], ["rs-nombre", "nombre"], ["rs-apellido", "apellido"], ["rs-obs-general", "observaciones"]].forEach(function (x) {
      var e = $(x[0]); if (document.activeElement !== e) e.value = estado[x[1]] || "";
    });
  }

  function capa(id, clase, texto) {
    var li = $(id); li.classList.remove("ok", "atencion", "error"); if (clase) li.classList.add(clase);
    li.querySelector(".rs-capa-estado").textContent = texto;
  }

  function pintarGuardado() {
    var p = persistencia;
    if (p.navegadorOk === null) capa("rs-capa-navegador", estado.guardado ? "ok" : "", estado.guardado ? "con datos de una sesión anterior (guardado n.º " + estado.guardado + ")" : "todavía sin respuestas");
    else if (p.navegadorOk) capa("rs-capa-navegador", "ok", "guardado a las " + p.navegadorHora.toLocaleTimeString() + " (n.º " + estado.guardado + ")" + (p.persistente === true ? " · almacenamiento persistente" : ""));
    else capa("rs-capa-navegador", "error", "¡no se pudo guardar en el navegador! Descargá una copia ya.");

    $("rs-archivo-reconectar").hidden = !(p.handle && !p.archivoPermiso);
    $("rs-archivo-nuevo").hidden = !!(p.handle && p.archivoPermiso);
    if (!hayApiArchivos) { capa("rs-capa-archivo", "", "este navegador no lo permite (usá Chrome o Edge)"); $("rs-archivo-nuevo").disabled = $("rs-archivo-abrir").disabled = true; }
    else if (!p.handle) capa("rs-capa-archivo", "", "sin elegir");
    else if (!p.archivoPermiso) capa("rs-capa-archivo", "atencion", "«" + p.handle.name + "»: tocá Reconectar para seguir guardando ahí");
    else if (p.archivoPausado) capa("rs-capa-archivo", "error", "«" + p.handle.name + "»: pausado por diferencias");
    else if (p.archivoError) capa("rs-capa-archivo", "error", p.archivoError);
    else capa("rs-capa-archivo", "ok", "«" + p.handle.name + "»" + (p.archivoHora ? " · guardado a las " + p.archivoHora.toLocaleTimeString() : ""));

    if (estado.ultimaCopia) capa("rs-capa-copia", estado.cambiosDesdeCopia >= AVISO_COPIA_CADA ? "atencion" : "ok", "última el " + new Date(estado.ultimaCopia).toLocaleString() + " · " + (estado.cambiosDesdeCopia || 0) + " cambios después");
    else capa("rs-capa-copia", estado.guardado ? "atencion" : "", "nunca descargada");

    var aviso = $("rs-aviso-guardado");
    aviso.classList.remove("ok");
    if (p.handle && p.archivoPermiso && !p.archivoPausado && !p.archivoError) {
      aviso.classList.add("ok");
      aviso.textContent = "Tus respuestas se guardan en este navegador y en el archivo «" + p.handle.name + "» de tu PC. Igual conviene descargar una copia de vez en cuando.";
    } else {
      aviso.textContent = "Tus respuestas se guardan solas en este navegador, pero ahí se pueden perder si se borran los datos de navegación. Para no depender de eso, creá un archivo de trabajo en la PC o descargá copias de seguridad.";
    }
  }

  function pintarTodo() { pintarIdentificacion(); pintarInstrucciones(); pintarAvance(); pintarLista(); pintarGuardado(); }

  function guardarUi() { lsGuardar("ui::" + CLAVE, JSON.stringify({ seccion: ui.seccion, pagina: ui.pagina })); }

  // ------------------------------------------------------------ alertas ---
  function alerta(tipo, texto, textoBoton, accion) {
    var cont = $("rs-alertas");
    var a = elem("div", "rs-alerta rs-alerta--" + tipo);
    a.appendChild(elem("span", "", texto));
    var acciones = elem("span");
    if (textoBoton) { var b = elem("button", "rs-btn rs-btn--chico", textoBoton); b.type = "button"; b.onclick = function () { a.remove(); accion(); }; acciones.appendChild(b); }
    var x = elem("button", "rs-btn rs-btn--chico rs-btn--claro", "Cerrar"); x.type = "button"; x.onclick = function () { a.remove(); }; acciones.appendChild(x);
    a.appendChild(acciones);
    cont.appendChild(a);
    while (cont.children.length > 4) cont.firstChild.remove();
  }

  function abrirModal(titulo, cuerpo, botones) {
    $("rs-modal-titulo").textContent = titulo;
    var c = $("rs-modal-cuerpo"); c.textContent = ""; c.appendChild(cuerpo);
    var acc = $("rs-modal-acciones"); acc.textContent = "";
    botones.forEach(function (b) {
      var e = elem("button", "rs-btn" + (b.claro ? " rs-btn--claro" : ""), b.texto); e.type = "button";
      e.onclick = function () { $("rs-modal").hidden = true; b.accion(); };
      acc.appendChild(e);
    });
    $("rs-modal").hidden = false;
    acc.firstChild && acc.firstChild.focus();
  }

  // ---------------------------------------------------------- finalizar ---
  function devolucion() {
    var c = contar();
    return {
      formato: FORMATO_DEVOLUCION,
      bodega: DATOS.bodega,
      servicio: estado.servicio,
      responsable: { nombre: estado.nombre, apellido: estado.apellido },
      fechas: { inicio: estado.inicio, ultimaModificacion: estado.modificado, finalizacion: estado.finalizado },
      versionDatos: DATOS.versionDatos,
      nomencladorActualizado: DATOS.nomencladorActualizado,
      planillaGenerada: DATOS.generado,
      guardado: estado.guardado,
      totales: {
        total: c.total, aprobados: c.correcto, rechazados: c.no_corresponde, noNecesarios: c.no_necesario,
        requierenAclaracion: c.aclaracion, pendientes: c.pendientes
      },
      porSeccion: { faltanCargar: c.porSeccion[1], necesitanConfirmacion: c.porSeccion[2], existenYVerificar: c.porSeccion[3] },
      observaciones: estado.observaciones,
      respuestas: ITEMS.map(function (i) {
        var r = respuesta(i.id) || {};
        return {
          codigo_interno: i.id, codigo_articulo: i.ca, descripcion: i.n, seccion: i.s,
          codigo_propuesto: i.cp, descripcion_nomenclador: i.dn, motivo: i.m,
          resultado: r.r || null, observaciones: r.obs || "", fecha: r.t || null, historial: r.hist || []
        };
      }),
      respuestasDeArticulosQueYaNoEstan: estado.huerfanas,
      registro: estado.registro
    };
  }

  function finalizar() {
    var faltan = [];
    ["rs-nombre", "rs-apellido"].forEach(function (id) { var e = $(id); var vacio = !e.value.trim(); e.classList.toggle("rs-falta", vacio); if (vacio) faltan.push(e); });
    if (faltan.length) { alerta("error", "Para finalizar hacen falta tu nombre y tu apellido."); faltan[0].focus(); faltan[0].scrollIntoView({ block: "center" }); return; }
    var c = contar();
    function hacer() {
      estado.finalizado = ahora();
      estado.modificado = estado.modificado || estado.finalizado;
      registrar("revisión finalizada", c.revisados + " revisados, " + c.pendientes + " pendientes");
      guardar(true);
      cola = cola.then(function () {
        descargar("revision-" + SLUG + "-DEVOLUCION-" + sello() + ".json", JSON.stringify(devolucion(), null, 1));
        pintarAvance();
        alerta("ok", "Revisión finalizada. Se descargó el archivo de devolución. Guardalo: cómo se entrega se va a definir más adelante.");
      });
    }
    if (c.pendientes) {
      var cuerpo = elem("p", "", "Quedan " + c.pendientes + " artículos sin resultado. Si finalizás ahora, van a figurar como pendientes en la devolución. Podés seguir revisando después y volver a finalizar.");
      abrirModal("¿Finalizar con pendientes?", cuerpo, [
        { texto: "Finalizar igual", accion: hacer },
        { texto: "Seguir revisando", claro: true, accion: function () {} }
      ]);
    } else hacer();
  }

  // ------------------------------------------------------------ eventos ---
  function irAlProximoPendiente() {
    var orden = [ui.seccion, 1, 2, 3].filter(function (v, i, a) { return a.indexOf(v) === i; });
    for (var k = 0; k < orden.length; k++) {
      var s = orden[k];
      var lista = ITEMS.filter(function (i) { return i.s === s; });
      var pos = lista.findIndex(function (i) { return !revisado(i.id); });
      if (pos !== -1) {
        ui.seccion = s; ui.buscar = ""; ui.filtro = ""; $("rs-buscar").value = ""; $("rs-estado").value = "";
        ui.pagina = Math.floor(pos / POR_PAGINA);
        pintarInstrucciones(); pintarAvance(); pintarLista();
        var t = document.querySelector('.rs-tarjeta[data-id="' + CSS.escape(lista[pos].id) + '"]');
        if (t) { t.scrollIntoView({ block: "center" }); t.querySelector(".rs-res").focus(); }
        return;
      }
    }
    alerta("ok", "¡No quedan artículos pendientes!");
  }

  function conectarEventos() {
    document.querySelectorAll(".rs-tab").forEach(function (b) {
      b.addEventListener("click", function () { ui.seccion = Number(b.dataset.seccion); ui.pagina = 0; pintarInstrucciones(); pintarAvance(); pintarLista(); });
    });
    var tBuscar = null;
    $("rs-buscar").addEventListener("input", function (e) { clearTimeout(tBuscar); tBuscar = setTimeout(function () { ui.buscar = e.target.value; ui.pagina = 0; pintarLista(); }, 200); });
    $("rs-estado").addEventListener("change", function (e) { ui.filtro = e.target.value; ui.pagina = 0; pintarLista(); });
    $("rs-ant").addEventListener("click", function () { ui.pagina--; pintarLista(); window.scrollTo({ top: $("rs-lista").offsetTop - 120 }); });
    $("rs-sig").addEventListener("click", function () { ui.pagina++; pintarLista(); window.scrollTo({ top: $("rs-lista").offsetTop - 120 }); });
    $("rs-ir-pendiente").addEventListener("click", irAlProximoPendiente);
    document.addEventListener("keydown", function (e) {
      if (!$("rs-modal").hidden || /^(INPUT|TEXTAREA|SELECT)$/.test((e.target || {}).tagName || "")) return;
      if (e.key === "ArrowLeft" && !$("rs-ant").disabled) $("rs-ant").click();
      if (e.key === "ArrowRight" && !$("rs-sig").disabled) $("rs-sig").click();
    });

    $("rs-lista").addEventListener("click", function (e) {
      var t = e.target.closest(".rs-tarjeta"); if (!t) return;
      var id = t.dataset.id;
      var boton = e.target.closest(".rs-res");
      if (boton) {
        var r = respuesta(id);
        if (r && r.r === boton.dataset.r) return;
        responder(id, boton.dataset.r, t.querySelector(".rs-obs").value);
        actualizarTarjeta(t, id); pintarAvance(); guardar(true);
        return;
      }
      if (e.target.closest(".rs-borrar")) {
        responder(id, null, t.querySelector(".rs-obs").value);
        actualizarTarjeta(t, id); pintarAvance(); guardar(true);
        return;
      }
      var copiar = e.target.closest(".rs-copiar");
      if (copiar && navigator.clipboard) navigator.clipboard.writeText(copiar.dataset.copiar).then(function () { copiar.textContent = "Copiado"; setTimeout(function () { copiar.textContent = "Copiar"; }, 1200); }, function () {});
    });
    $("rs-lista").addEventListener("input", function (e) {
      if (!e.target.classList.contains("rs-obs")) return;
      var t = e.target.closest(".rs-tarjeta"), id = t.dataset.id, r = respuesta(id);
      responder(id, r ? r.r : null, e.target.value, true);
      actualizarTarjeta(t, id); pintarAvance(); guardar(false);
    });

    [["rs-servicio", "servicio"], ["rs-nombre", "nombre"], ["rs-apellido", "apellido"], ["rs-obs-general", "observaciones"]].forEach(function (x) {
      $(x[0]).addEventListener("input", function (e) {
        estado[x[1]] = e.target.value; e.target.classList.remove("rs-falta");
        if (!estado.inicio) estado.inicio = ahora();
        estado.modificado = ahora(); pintarAvance(); guardar(false);
      });
    });

    $("rs-archivo-nuevo").addEventListener("click", crearArchivo);
    $("rs-archivo-abrir").addEventListener("click", abrirArchivo);
    $("rs-archivo-reconectar").addEventListener("click", reconectar);
    $("rs-exportar").addEventListener("click", exportarCopia);
    $("rs-importar").addEventListener("change", function (e) { var f = e.target.files[0]; if (f) importarCopia(f); e.target.value = ""; });
    $("rs-finalizar").addEventListener("click", finalizar);

    // Si se cierra con texto a medio guardar, la copia sincrónica en
    // localStorage lo conserva; IndexedDB se completa al reabrir.
    function alSalir() { if (hayCambiosSinGuardar) lsGuardar(CLAVE, JSON.stringify(estado)); }
    window.addEventListener("pagehide", alSalir);
    document.addEventListener("visibilitychange", function () { if (document.visibilityState === "hidden") { alSalir(); if (hayCambiosSinGuardar) guardar(true); } });
  }

  var canal = null;
  try {
    canal = new BroadcastChannel(PREFIJO_LS + CLAVE);
    var avisado = false;
    canal.onmessage = function (m) {
      if (m.data && m.data.sesion !== SESION && !avisado) {
        avisado = true;
        alerta("atencion", "Esta misma revisión está abierta en otra pestaña o ventana. Trabajá en una sola: si se cruzan respuestas, la planilla te va a preguntar cuál conservar.");
      }
    };
  } catch (e) { canal = null; }

  // -------------------------------------------------------------- inicio ---
  async function iniciar() {
    try { persistencia.db = await abrirDB(); } catch (e) { persistencia.db = null; }
    var previo = await leerGuardadoLocal(CLAVE);
    if (previo && previo.bodega === DATOS.bodega) {
      estado = Object.assign(estadoNuevo(), previo);
      persistencia.baseLocal = previo.guardado || 0;
    } else {
      // ¿Hay una revisión de esta misma bodega hecha con otra versión de la planilla?
      var claves = lsClaves();
      try { claves = claves.concat(await idbClaves("estados")); } catch (e) { /* nada */ }
      var otras = Array.from(new Set(claves)).filter(function (k) { return k.indexOf(DATOS.bodega + "::") === 0 && k !== CLAVE; });
      var mejor = null;
      for (var k = 0; k < otras.length; k++) mejor = masNuevo(mejor, await leerGuardadoLocal(otras[k]));
      if (mejor && Object.keys(mejor.respuestas || {}).length) {
        alerta("atencion", "En este navegador hay una revisión anterior de " + DATOS.bodega + " hecha con otra versión de la planilla (" + Object.keys(mejor.respuestas).length + " respuestas).", "Recuperarla", function () {
          combinar(mejor, "la revisión anterior de este navegador"); avisoVersion();
        });
      }
    }
    var uiGuardada = lsLeer("ui::" + CLAVE);
    if (uiGuardada) { ui.seccion = [1, 2, 3].indexOf(uiGuardada.seccion) !== -1 ? uiGuardada.seccion : 1; ui.pagina = uiGuardada.pagina || 0; }
    else { ui.seccion = [1, 2, 3].find(function (s) { return DATOS.secciones[s]; }) || 1; }

    if (hayApiArchivos && persistencia.db) {
      try {
        var h = await idbLeer("archivos", CLAVE);
        if (h) {
          persistencia.handle = h;
          var permiso = await h.queryPermission({ mode: "readwrite" });
          if (permiso === "granted") await conectarArchivo(h, false);
          else persistencia.archivoPermiso = false;
        }
      } catch (e) { persistencia.handle = null; }
    }
    conectarEventos();
    pintarTodo();
    if (previo && previo.guardado) alerta("ok", "Se recuperó tu revisión: " + contar().revisados + " artículos ya revisados.", "Ir al próximo pendiente", irAlProximoPendiente);
  }

  // Para las pruebas automáticas (no cambia nada por sí solo).
  window.RevisionServicio = {
    estado: function () { return JSON.parse(JSON.stringify(estado)); },
    devolucion: function () { return devolucion(); },
    copia: function () { return textoCopia(); },
    combinar: function (obj, origen) { var err = validarAjeno(obj); if (err) throw new Error(err); combinar(aEstado(obj), origen || "la copia"); },
    // El selector de archivos de Chrome no se puede manejar en una prueba
    // automática: esto conecta un archivo ya elegido por el mismo camino.
    usarArchivo: function (handle) { return conectarArchivo(handle, true); },
    esperar: function () { return cola; }
  };

  iniciar();
})();
