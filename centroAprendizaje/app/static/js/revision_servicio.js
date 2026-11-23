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
  // En línea (llave de servicio): las respuestas se guardan en el Centro y no
  // en el navegador. Sin `servidor`, es la planilla descargable de siempre.
  var SERVIDOR = DATOS.servidor || null;
  var ITEMS = DATOS.items;
  var POR_ID = new Map(ITEMS.map(function (i) { return [i.id, i]; }));
  // Artículos que comparten código propuesto (ver `_agrupar` en el servidor).
  var GRUPOS = new Map();
  ITEMS.forEach(function (i) { if (i.g) { if (!GRUPOS.has(i.g)) GRUPOS.set(i.g, []); GRUPOS.get(i.g).push(i); } });
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

  // De izquierda a derecha: de lo que se descarta a lo que se confirma.
  // «No se usa» va primero porque se decide sin mirar el código: el artículo
  // queda fuera y no hay que hacer nada más con él.
  var RESULTADOS = {
    no_necesario: "No se usa",
    otro_servicio: "No es de este servicio",
    no_corresponde: "No corresponde",
    aclaracion: "Requiere aclaración",
    correcto: "Correcto / corresponde"
  };
  var NO_SE_USA = "No se compra más: queda fuera, no hay que hacer nada";
  var TIPOS_NEC = {
    farmacia: "Medicamento o descartable de Farmacia",
    otro: "Otro bien o servicio",
    no_se: "No sé"
  };
  var CATALOGO_NEC = {
    no_busque: "Todavía no lo busqué",
    no_esta: "Lo busqué y no está",
    esta: "Lo busqué y sí está"
  };
  // Instrucciones de cada sección, en lenguaje simple. En todas, cada artículo
  // se resuelve con una sola pregunta (ver bloqueRespuesta).
  var INSTRUCCIONES = {
    1: {
      titulo: "1 · No están en el Catálogo WEB",
      texto: "Estos artículos todavía no están en TIMBÓ. Si el servicio los usa, se pide que los carguen.",
      pasos: [
        "Si lo usan, tocá «Sí, se usa» y listo: se pide que lo carguen.",
        "Si no lo usan, tocá «Ya no se usa». Si no es de tu servicio, «No es de nuestro servicio».",
        "Si querés aclarar algo, tocá «＋ Agregar una observación»."
      ]
    },
    2: {
      titulo: "2 · Hay que confirmar el código",
      texto: "TIMBÓ propone un artículo parecido. Fijate si es lo mismo que usa el servicio.",
      pasos: [
        "Si es lo mismo, tocá «✓ Sí, es este».",
        "Si el servicio lo usa pero TIMBÓ propone algo distinto, tocá «Es otra cosa»: se pide que lo carguen.",
        "Si en TIMBÓ es un artículo general (ejemplo: «Lámpara LED» para las de 12 W, 14 W…), también es «Sí, es este»: el detalle se aclara al hacer el pedido.",
        "Si ya no se usa o no es de tu servicio, tocá esa opción."
      ]
    },
    3: {
      titulo: "3 · Ya están en TIMBÓ",
      texto: "Estos artículos ya están cargados en TIMBÓ. No tenés que hacer nada: es solo para que los veas.",
      pasos: []
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
      respuestas: {}, huerfanas: {}, necesidades: {}, registro: []
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
  // La sección 3 (ya están en TIMBÓ) es solo para mirar: cuenta como hecha.
  function soloVer(i) { return !!i && i.s === 3; }
  // Lo que quedó sin decidir con pantallas anteriores («No sé», «no corresponde»
  // sin decir qué hacer, o una ✗ traída de Farmacia) vuelve al centro como
  // pendiente: se responde con la pregunta nueva. La respuesta guardada no se toca.
  function sinDecidirGuardado(r) { return !!r && (r.r === "aclaracion" || (r.r === "no_corresponde" && !r.dec)); }
  function revisado(id) { var r = respuesta(id); return (!!(r && r.r) && !sinDecidirGuardado(r)) || soloVer(POR_ID.get(id)); }

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
    if (SERVIDOR) { programarServidor(inmediato); return; }
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

  // ------------------------------------------------------- en el Centro ---
  // Cada respuesta cambiada se manda sola, en fila. Si falla, queda marcada
  // para reintentar y se avisa arriba.
  var sucios = new Set();
  var tServidor = null;
  var estadoEnvio = { enviando: 0, error: "" };

  function post(url, cuerpo) {
    return fetch(url, {
      method: "POST", credentials: "same-origin", keepalive: true,
      headers: { "Content-Type": "application/json", "X-CSRFToken": SERVIDOR.csrf },
      body: JSON.stringify(cuerpo)
    }).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (d) {
        if (r.status === 409 && d.enviado) { SERVIDOR.enviado = d.enviado; marcarEnviada(); }
        if (r.status === 403) return { ok: false, error: "Tu sesión terminó. Volvé a entrar con tu enlace (lo ya guardado no se pierde)." };
        return { ok: r.ok && d.ok !== false, error: d.error || (r.ok ? "" : "Error " + r.status), datos: d };
      });
    }, function () { return { ok: false, error: "Sin conexión con el Centro." }; });
  }

  function programarServidor(inmediato) {
    clearTimeout(tServidor);
    if (inmediato) enviarSucios(); else tServidor = setTimeout(enviarSucios, 800);
  }

  function enviarSucios() {
    var ids = Array.from(sucios); sucios.clear();
    ids.forEach(function (id) {
      estadoEnvio.enviando++; pintarEnvio();
      cola = cola.then(function () {
        var r = respuesta(id) || {};
        return post(SERVIDOR.urlRespuesta, { codigo: id, resultado: r.r || null, observacion: r.obs || "", decision: r.dec || null, codigo_correcto: r.cod || "", detalle_timbo: r.det || "" }).then(function (res) {
          estadoEnvio.enviando--;
          if (res.ok) { if (estadoEnvio.error && !sucios.size) estadoEnvio.error = ""; if (res.datos.finalizado === null) estado.finalizado = null; }
          else { sucios.add(id); estadoEnvio.error = res.error; }
          pintarEnvio();
        });
      });
    });
  }

  function pintarEnvio() {
    var e = $("rs-envio"); if (!e) return;
    e.classList.remove("ok", "error");
    if (estadoEnvio.error) { e.classList.add("error"); e.textContent = "⚠ " + estadoEnvio.error + " "; var b = elem("button", "rs-btn rs-btn--chico", "Reintentar"); b.type = "button"; b.onclick = function () { estadoEnvio.error = ""; enviarSucios(); }; e.appendChild(b); }
    else if (estadoEnvio.enviando || sucios.size) e.textContent = "Guardando…";
    else { e.classList.add("ok"); e.textContent = "✓ Todo guardado en el Centro"; }
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
      if (r.resultado || r.observaciones) e.respuestas[r.codigo_interno] = { r: r.resultado || null, obs: r.observaciones || "", dec: r.decision || null, cod: r.codigo_correcto || "", det: r.detalle_timbo || "", t: r.fecha || e.modificado, hist: r.historial || [] };
    });
    (obj.necesidades || []).forEach(function (n) {
      e.necesidades[n.id] = {
        id: n.id, d: n.descripcion || "", p: n.presentacion || "", u: n.uso || "", tipo: n.tipo || "",
        cat: n.catalogo || "no_busque", cod: n.codigo_catalogo || "", obs: n.observaciones || "",
        creado: n.creado || null, t: n.modificado || null, baja: !!n.quitada, hist: n.historial || []
      };
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
  function igual(a, b) {
    return (a.r || null) === (b.r || null) && (a.obs || "") === (b.obs || "") &&
      (a.dec || null) === (b.dec || null) && (a.cod || "") === (b.cod || "") && (a.det || "") === (b.det || "");
  }
  function vacia(a) { return !a || (!a.r && !(a.obs || "").trim()); }
  function fechaDe(a) { return a && a.t ? Date.parse(a.t) || 0 : 0; }

  function analizar(otro) {
    var ids = new Set(Object.keys(estado.respuestas).concat(Object.keys(otro.respuestas || {})));
    var res = { nuevas: [], iguales: 0, conflictos: [], huerfanas: [], necNuevas: [], necDistintas: [] };
    Object.keys(otro.necesidades || {}).forEach(function (id) {
      var mia = (estado.necesidades || {})[id], suya = otro.necesidades[id];
      if (!mia) res.necNuevas.push(id);
      else if (JSON.stringify(necComparable(mia)) !== JSON.stringify(necComparable(suya))) res.necDistintas.push(id);
    });
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
    // Necesidades: se unen por id. Si las dos versiones difieren, decide el
    // mismo criterio que para las respuestas; la otra queda en el historial.
    estado.necesidades = estado.necesidades || {};
    analisis.necNuevas.forEach(function (id) { estado.necesidades[id] = JSON.parse(JSON.stringify(otro.necesidades[id])); });
    analisis.necDistintas.forEach(function (id) {
      var mia = estado.necesidades[id], suya = otro.necesidades[id];
      var ganaSuya = modo === "suyas" || (modo === "recientes" && fechaDe(suya) > fechaDe(mia));
      estado.necesidades[id] = ganaSuya ? necConHistorial(suya, mia) : necConHistorial(mia, suya);
    });
    Object.keys(otro.huerfanas || {}).forEach(function (id) { if (!estado.huerfanas[id]) estado.huerfanas[id] = otro.huerfanas[id]; });
    ["servicio", "nombre", "apellido", "observaciones"].forEach(function (campo) {
      if (!(estado[campo] || "").trim() && (otro[campo] || "").trim()) estado[campo] = otro[campo];
    });
    if (otro.inicio && (!estado.inicio || otro.inicio < estado.inicio)) estado.inicio = otro.inicio;
    if (otro.ultimaCopia && (!estado.ultimaCopia || otro.ultimaCopia > estado.ultimaCopia)) estado.ultimaCopia = otro.ultimaCopia;
    if (!estado.finalizado && otro.finalizado && !analisis.nuevas.length && !analisis.conflictos.length && !analisis.necNuevas.length && !analisis.necDistintas.length) estado.finalizado = otro.finalizado;
    (otro.registro || []).forEach(function (x) { if (x.sesion !== SESION) estado.registro.push(x); });
    estado.registro.sort(function (a, b) { return a.t < b.t ? -1 : 1; });
    if (estado.registro.length > MAX_REGISTRO) estado.registro.splice(0, estado.registro.length - MAX_REGISTRO);
    var necCambios = analisis.necNuevas.length + analisis.necDistintas.length;
    if (analisis.nuevas.length || analisis.conflictos.length || necCambios) estado.modificado = ahora();
    registrar("combinación con " + origen, analisis.nuevas.length + " nuevas, " + analisis.iguales + " iguales, " + analisis.conflictos.length + " en conflicto (" + modo + "), " + analisis.huerfanas.length + " de artículos que ya no están, " + analisis.necNuevas.length + " necesidades nuevas, " + analisis.necDistintas.length + " necesidades distintas");
    persistencia.baseLocal = Math.max(persistencia.baseLocal, otro.guardado || 0);
    estado.guardado = Math.max(estado.guardado || 0, otro.guardado || 0);
    if (origen === "el archivo de trabajo") { persistencia.baseArchivo = Math.max(persistencia.baseArchivo, otro.guardado || 0); persistencia.archivoPausado = false; }
    guardar(true);
    pintarTodo();
    var partes = [analisis.nuevas.length + " respuestas recuperadas", analisis.iguales + " ya estaban iguales"];
    if (analisis.conflictos.length) partes.push(analisis.conflictos.length + " diferencias resueltas");
    if (analisis.huerfanas.length) partes.push(analisis.huerfanas.length + " de artículos que ya no están en esta planilla (se conservan aparte)");
    if (analisis.necNuevas.length) partes.push(analisis.necNuevas.length + " artículos necesarios recuperados");
    if (analisis.necDistintas.length) partes.push(analisis.necDistintas.length + " artículos necesarios con diferencias resueltas");
    alerta("ok", "Listo: se combinó con " + origen + ". " + partes.join(" · ") + ".");
  }

  function combinar(otro, origen) {
    var antes = JSON.stringify(estado);
    apilar("combinar con " + origen, function () { var g = estado.guardado; estado = JSON.parse(antes); estado.guardado = g; });
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
  // `dec` / `cod`: qué hacer con un «no corresponde» (agregar o código
  // correcto). Si no se pasan, se conservan mientras el resultado no cambie.
  // Decisiones válidas: «no corresponde» → agregar / código; «correcto» →
  // ítem general (código + `det`, el detalle para la observación en TIMBÓ).
  var DECISIONES_VALIDAS = { no_corresponde: ["agregar", "codigo"], correcto: ["general"] };
  // Una vez enviada la revisión no se puede cambiar nada (solo el
  // administrador la reabre).
  function enviada() { return !!(SERVIDOR && SERVIDOR.enviado); }
  function bloqueada() {
    if (!enviada()) return false;
    alerta("error", "La revisión ya se envió y no se puede cambiar. Si hace falta, pedí que la reabran.");
    return true;
  }

  function responder(id, r, obs, tipeando, dec, cod, det) {
    if (bloqueada()) return;
    var previa = estado.respuestas[id];
    if (dec === undefined) {
      var igualR = previa && previa.r === r;
      dec = igualR ? previa.dec || null : null; cod = igualR ? previa.cod || "" : ""; det = igualR ? previa.det || "" : "";
    }
    if ((DECISIONES_VALIDAS[r] || []).indexOf(dec) === -1) dec = null;
    if (dec !== "codigo" && dec !== "general") cod = "";
    if (dec !== "general") det = "";
    var nueva = { r: r, obs: obs, dec: dec || null, cod: cod || "", det: det || "", t: ahora(), hist: previa ? (previa.hist || []).slice() : [] };
    var mismaEdicion = tipeando && previa && previa.r === r && Date.now() - fechaDe(previa) < 60000;
    if (previa && !vacia(previa) && !igual(previa, nueva) && !mismaEdicion) {
      nueva.hist.push({ r: previa.r || null, obs: previa.obs || "", dec: previa.dec || null, cod: previa.cod || "", det: previa.det || "", t: previa.t || null });
      if (nueva.hist.length > MAX_HISTORIAL) nueva.hist = nueva.hist.slice(-MAX_HISTORIAL);
    }
    estado.respuestas[id] = nueva;
    sucios.add(id);
    marcarCambio(nueva.t, id, mismaEdicion);
  }

  // ----------------------------------------------------------- deshacer ---
  // Toda acción deja cómo volver atrás. Deshacer también queda en el
  // historial: nada se borra.
  var pilaDeshacer = [];
  function apilar(texto, volver) {
    pilaDeshacer.push({ texto: texto, volver: volver });
    if (pilaDeshacer.length > 50) pilaDeshacer.shift();
    pintarDeshacer();
  }
  function deshacerUltimo() {
    if (bloqueada()) return;
    var a = pilaDeshacer.pop(); if (!a) return;
    pintarDeshacer();
    Promise.resolve(a.volver()).then(function () {
      pintarLista(); pintarNecesidades(); pintarAvance(); guardar(true);
      if ($("rs-revfinal") && !$("rs-revfinal").hidden) pintarRevisionFinal();
      alerta("ok", "Se deshizo: " + a.texto + ".");
    }, function (err) { pilaDeshacer.push(a); pintarDeshacer(); alerta("error", "No se pudo deshacer: " + (err && err.message || err)); });
  }
  function pintarDeshacer() {
    var b = $("rs-deshacer"); if (!b) return;
    var u = pilaDeshacer[pilaDeshacer.length - 1];
    b.hidden = !u;
    if (u) { b.textContent = "↶ Deshacer lo último"; b.title = "Deshacer: " + u.texto + " (Ctrl+Z)"; }
  }
  var DECISIONES = { agregar: "hay que agregarlo", codigo: "código correcto" };
  function decidir(id, dec, cod) {
    var previa = respuesta(id) || {}, antes = { dec: previa.dec || null, cod: previa.cod || "" };
    responder(id, previa.r || null, previa.obs || "", false, dec, cod);
    var item = POR_ID.get(id);
    apilar((dec ? "«" + DECISIONES[dec] + "»" : "quitar la decisión") + " en " + (item ? item.n : id), function () {
      var r = respuesta(id) || {}; responder(id, r.r || null, r.obs || "", false, antes.dec, antes.cod);
    });
  }

  // Cambia la respuesta completa (resultado y, si corresponde, decisión) y
  // deja cómo deshacerlo.
  function cambiarResultado(id, r, obs, texto, dec, cod, det) {
    var p = respuesta(id) || {};
    var antes = { r: p.r || null, obs: p.obs || "", dec: p.dec || null, cod: p.cod || "", det: p.det || "" };
    responder(id, r, obs, false, dec === undefined ? null : dec, cod || "", det || "");
    var item = POR_ID.get(id);
    apilar(texto || ((r ? "«" + RESULTADOS[r] + "»" : "quitar el resultado") + " en " + (item ? item.n : id)), function () {
      responder(id, antes.r, antes.obs, false, antes.dec, antes.cod, antes.det);
    });
  }

  function marcarCambio(t, que, mismaEdicion) {
    if (!estado.inicio) { estado.inicio = t; registrar("revisión iniciada", ""); }
    estado.modificado = t;
    if (!mismaEdicion) estado.cambiosDesdeCopia = (estado.cambiosDesdeCopia || 0) + 1;
    if (estado.finalizado) {
      estado.finalizado = null;
      registrar("revisión reabierta", "cambio en " + que);
      alerta("atencion", "Hiciste un cambio después de finalizar: la revisión volvió a quedar abierta. Al terminar, finalizala de nuevo.");
    }
    if (!SERVIDOR && estado.cambiosDesdeCopia > 0 && estado.cambiosDesdeCopia % AVISO_COPIA_CADA === 0) {
      alerta("atencion", "Llevás " + estado.cambiosDesdeCopia + " cambios desde la última copia de seguridad.", "Descargar copia ahora", exportarCopia);
    }
  }

  // ---------------------------------------- artículos que no están (5) ---
  // Artículos que el servicio necesita y no figuran en la planilla. Al quitar
  // uno queda marcado como quitado (no se borra): así una copia vieja no lo
  // vuelve a traer al combinar.
  var necEditando = null;

  function necComparable(n) { return [n.d, n.p, n.u, n.tipo, n.cat, n.cod, n.obs, !!n.baja]; }
  function necConHistorial(ganadora, perdedora) {
    var g = JSON.parse(JSON.stringify(ganadora));
    g.hist = (g.hist || []).slice();
    if (perdedora) g.hist.push({ version: necComparable(perdedora), t: perdedora.t || null, motivo: "versión distinta al combinar" });
    if (g.hist.length > MAX_HISTORIAL) g.hist = g.hist.slice(-MAX_HISTORIAL);
    return g;
  }
  function necesidadesActivas() {
    return Object.keys(estado.necesidades || {}).map(function (k) { return estado.necesidades[k]; })
      .filter(function (n) { return !n.baja; })
      .sort(function (a, b) { return (a.creado || "") < (b.creado || "") ? -1 : 1; });
  }
  function idNecesidad() { return "n-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 7); }

  function leerFormNec() {
    var cat = $("rs-nec-cat").value;
    return {
      d: $("rs-nec-desc").value.trim(), p: $("rs-nec-pres").value.trim(), u: $("rs-nec-uso").value.trim(),
      tipo: $("rs-nec-tipo").value, cat: cat, cod: cat === "esta" ? $("rs-nec-cod").value.trim() : "",
      obs: $("rs-nec-obs").value.trim()
    };
  }
  function llenarFormNec(n) {
    $("rs-nec-desc").value = n ? n.d : ""; $("rs-nec-pres").value = n ? n.p : ""; $("rs-nec-uso").value = n ? n.u : "";
    $("rs-nec-tipo").value = n ? n.tipo : ""; $("rs-nec-cat").value = n ? n.cat || "no_busque" : "no_busque";
    $("rs-nec-cod").value = n ? n.cod : ""; $("rs-nec-obs").value = n ? n.obs : "";
    $("rs-nec-desc").classList.remove("rs-falta");
    pintarOrientacion();
  }

  function guardarNecesidad(datos) {
    var t = ahora();
    estado.necesidades = estado.necesidades || {};
    var previa = necEditando ? estado.necesidades[necEditando] : null;
    var n = Object.assign({ id: previa ? previa.id : idNecesidad(), creado: previa ? previa.creado : t, baja: false, hist: [] }, previa || {}, datos);
    if (previa) {
      if (JSON.stringify(necComparable(previa)) === JSON.stringify(necComparable(n))) return previa;
      n.hist = (previa.hist || []).concat([{ version: necComparable(previa), t: previa.t || null }]).slice(-MAX_HISTORIAL);
    }
    n.t = t;
    estado.necesidades[n.id] = n;
    registrar(previa ? "artículo necesario editado" : "artículo necesario agregado", n.d);
    marcarCambio(t, "artículo necesario «" + n.d + "»");
    return n;
  }

  function restaurarNecesidad(id) {
    var n = estado.necesidades[id]; if (!n || !n.baja) return;
    var t = ahora();
    n.hist = (n.hist || []).concat([{ version: necComparable(n), t: n.t || null }]).slice(-MAX_HISTORIAL);
    n.baja = false; n.t = t;
    registrar("artículo necesario vuelto a poner", n.d);
    marcarCambio(t, "artículo necesario «" + n.d + "»");
  }

  // Agregar / editar / quitar, en la planilla o en el Centro. Devuelven una
  // promesa (en el Centro esperan la respuesta para tener el id).
  function necGuardar(datos, id) {
    if (bloqueada()) return Promise.reject(new Error("La revisión ya se envió."));
    if (!SERVIDOR) { necEditando = id || null; var n = guardarNecesidad(datos); necEditando = null; guardar(true); return Promise.resolve(n.id); }
    return post(SERVIDOR.urlNecesidad, Object.assign({ id: id || null }, datos)).then(function (res) {
      if (!res.ok) throw new Error(res.error || "No se pudo guardar.");
      estado.necesidades = res.datos.necesidades; estado.finalizado = null;
      return res.datos.id;
    });
  }
  function necBaja(id, quitar) {
    if (bloqueada()) return Promise.reject(new Error("La revisión ya se envió."));
    if (!SERVIDOR) { if (quitar) quitarNecesidad(id); else restaurarNecesidad(id); guardar(true); return Promise.resolve(); }
    return post(SERVIDOR.urlNecesidadQuitar, { id: id, quitar: quitar }).then(function (res) {
      if (!res.ok) throw new Error(res.error || "No se pudo guardar.");
      estado.necesidades = res.datos.necesidades; estado.finalizado = null;
    });
  }
  function datosDe(n) { return { d: n.d, p: n.p, u: n.u, tipo: n.tipo, cat: n.cat, cod: n.cod, obs: n.obs }; }

  function quitarNecesidad(id) {
    var n = estado.necesidades[id]; if (!n || n.baja) return;
    var t = ahora();
    n.hist = (n.hist || []).concat([{ version: necComparable(n), t: n.t || null }]).slice(-MAX_HISTORIAL);
    n.baja = true; n.t = t;
    registrar("artículo necesario quitado", n.d);
    marcarCambio(t, "artículo necesario «" + n.d + "»");
  }

  function pintarOrientacion() {
    var tipo = $("rs-nec-tipo").value, cat = $("rs-nec-cat").value;
    var pedirAlta = cat !== "esta";
    var ver = {
      no_busque: cat === "no_busque", esta: cat === "esta",
      farmacia: pedirAlta && tipo === "farmacia", otro: pedirAlta && tipo === "otro", no_se: pedirAlta && tipo === "no_se"
    };
    ver.alta = ver.farmacia || ver.otro;
    document.querySelectorAll("[data-orienta]").forEach(function (p) { p.hidden = !ver[p.dataset.orienta]; });
    $("rs-nec-cod-campo").hidden = cat !== "esta";
  }

  function pintarNecesidades() {
    pintarColumnas();
    var lista = necesidadesActivas(), cont = $("rs-nec-lista"); cont.textContent = "";
    $("rs-nec-cuenta").textContent = lista.length ? lista.length + (lista.length === 1 ? " artículo cargado" : " artículos cargados") : "Todavía no cargaste ninguno.";
    lista.forEach(function (n) {
      var t = elem("article", "rs-tarjeta rs-nec-item"); t.dataset.nec = n.id;
      var cab = elem("div", "rs-tarjeta__cab");
      cab.appendChild(elem("span", "rs-tarjeta__nombre", n.d));
      if (n.p) cab.appendChild(elem("span", "rs-codigos", n.p));
      t.appendChild(cab);
      var partes = ["Tipo: " + (TIPOS_NEC[n.tipo] || "sin elegir"), "Catálogo WEB: " + (CATALOGO_NEC[n.cat] || "—") + (n.cod ? " (" + n.cod + ")" : "")];
      if (n.u) partes.unshift("Uso: " + n.u);
      t.appendChild(elem("p", "rs-motivo", partes.join(" · ")));
      if (n.obs) t.appendChild(elem("p", "", n.obs));
      var pie = elem("div", "rs-tarjeta__pie");
      pie.appendChild(elem("span", "rs-guardado-item", "Guardado " + new Date(n.t).toLocaleString()));
      var acc = elem("span");
      var ed = elem("button", "rs-borrar", "Editar"); ed.type = "button"; ed.dataset.accion = "editar"; acc.appendChild(ed);
      var qu = elem("button", "rs-borrar", "Quitar"); qu.type = "button"; qu.dataset.accion = "quitar"; acc.appendChild(qu);
      pie.appendChild(acc);
      t.appendChild(pie);
      cont.appendChild(t);
    });
  }

  function terminarEdicionNec() {
    necEditando = null;
    llenarFormNec(null);
    $("rs-nec-guardar").textContent = "Agregar a la lista";
    $("rs-nec-cancelar").hidden = true;
  }

  // -------------------------------------------------------------- vista ---
  var $ = function (id) { return document.getElementById(id); };

  function normal(t) { return (t || "").normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase(); }
  var INDICE = new Map(ITEMS.map(function (i) { return [i.id, normal([i.n, i.id, i.ca, i.cp, i.dn].join(" "))]; }));

  function coincide(i) {
    var palabras = normal(ui.buscar).split(/\s+/).filter(Boolean);
    if (!palabras.length) return true;
    var t = INDICE.get(i.id);
    return palabras.every(function (p) { return t.indexOf(p) !== -1; });
  }

  // Vista normal (filtro vacío): arriba solo lo pendiente; lo revisado va a
  // las columnas de abajo.
  function filtrados() {
    return ITEMS.filter(function (i) {
      if (i.s !== ui.seccion) return false;
      if (!coincide(i)) return false;
      if (soloVer(i)) return true;
      var r = respuesta(i.id), res = r && r.r;
      if (!ui.filtro || ui.filtro === "pendiente") return !revisado(i.id);
      if (ui.filtro === "todos") return true;
      if (ui.filtro === "revisado") return !!res;
      if (ui.filtro) return res === ui.filtro;
      return true;
    });
  }

  // Cada artículo en su propia card: juntar artículos distintos en una card
  // (por tener el mismo código propuesto) llevaba a responder por error
  // (23/11/2026). Los que comparten código se avisan dentro de la card.
  function unidades(lista) {
    return lista.map(function (i) { return { items: [i] }; });
  }

  function elem(tag, clase, texto) { var e = document.createElement(tag); if (clase) e.className = clase; if (texto !== undefined) e.textContent = texto; return e; }

  // Botones de respuesta (ver bloqueRespuesta).
  var abiertos = {};  // id → "si" | "no" | "codigo" | "general" (solo pantalla)
  function boton(padre, clase, texto, datos, apretado, ayuda) {
    var b = elem("button", clase, texto); b.type = "button";
    Object.keys(datos).forEach(function (k) { b.dataset[k] = datos[k]; });
    b.setAttribute("aria-pressed", apretado ? "true" : "false");
    if (ayuda) b.title = ayuda;
    padre.appendChild(b);
    return b;
  }
  // Primero SIEMPRE se pregunta por el artículo del hospital, nombrándolo
  // («¿En el servicio usan «PC MINI…»?»); recién si lo usan, si es lo mismo
  // que el de TIMBÓ. Así «Ya no lo usamos» nunca puede leerse como si fuera
  // del artículo de TIMBÓ (pasó con el PC MINI, 23/11/2026: quedó fuera
  // siendo muy usado).
  function pregunta(antes, nombre, despues) {
    var e = elem("span", "rs-paso__preg");
    e.appendChild(document.createTextNode(antes));
    e.appendChild(elem("b", "rs-paso__nombre", "«" + nombre + "»"));
    e.appendChild(document.createTextNode(despues));
    return e;
  }
  function bloqueRespuesta(i, r, chico) {
    r = r || {};
    var cont = elem("div", "rs-pasos" + (chico ? " rs-pasos--chicas" : ""));
    var conCodigo = r.dec === "codigo" || r.dec === "general";
    var decidido = r.r === "correcto" || (r.r === "no_corresponde" && !!r.dec);
    var usa = decidido || abiertos[i.id] === "si";
    var p = elem("div", "rs-paso");
    p.appendChild(pregunta("1. ¿En el servicio usan ", i.n, "?"));
    var b = elem("div", "rs-paso__botones");
    if (i.cp) boton(b, "rs-res rs-ok", "✓ Sí, lo usamos", { uso: "si" }, usa);
    else boton(b, "rs-res rs-ok", "✓ Sí, lo usamos", { r: "correcto" }, r.r === "correcto", "Se pide que lo carguen en TIMBÓ");
    boton(b, "rs-res rs-no", "Ya no lo usamos", { r: "no_necesario" }, r.r === "no_necesario", NO_SE_USA);
    boton(b, "rs-res rs-no", "No es de nuestro servicio", { r: "otro_servicio" }, r.r === "otro_servicio",
      "Está en la bodega por error: lo usa otro servicio");
    p.appendChild(b); cont.appendChild(p);
    if (i.cp && usa) {
      var p2 = elem("div", "rs-paso rs-paso--2" + (decidido ? "" : " rs-paso--falta"));
      p2.appendChild(pregunta("2. ¿Es lo mismo que ", nombreTimbo(i.dn), " de TIMBÓ?"));
      var b2 = elem("div", "rs-paso__botones");
      boton(b2, "rs-res rs-ok", "✓ Sí, es lo mismo", { r: "correcto" }, r.r === "correcto");
      boton(b2, "rs-res rs-mal", "No, es otra cosa", { r: "no_corresponde", dec: "agregar" }, r.r === "no_corresponde" && !!r.dec,
        "Lo usan, pero en TIMBÓ es otro artículo: se pide que lo carguen");
      p2.appendChild(b2); cont.appendChild(p2);
    }
    // Respuestas guardadas con la pantalla anterior: se muestran, no se pierden.
    if (r.r === "aclaracion") cont.appendChild(elem("p", "rs-nota rs-nota--antes", "Guardado antes como «No sé»: elegí una de las opciones."));
    if (r.r === "no_corresponde" && !r.dec) cont.appendChild(elem("p", "rs-nota rs-nota--antes",
      (r.persona && /Farmacia/.test(r.persona) ? "En la revisión de Farmacia se marcó ✗" : "Guardado antes como «no corresponde»") + ": elegí una de las opciones."));
    if (conCodigo) {
      var pc = elem("div", "rs-paso rs-paso--extra rs-campos-dato");
      pc.appendChild(elem("span", "", "Guardado antes: en TIMBÓ va como "));
      pc.appendChild(elem("code", "", r.cod || i.cp || ""));
      if (r.det) pc.appendChild(elem("span", "", " · al pedir, aclarar: «" + r.det + "»"));
      cont.appendChild(pc);
    }
    return cont;
  }

  function cajaObs(obs) {
    var d = elem("details", "rs-obs-caja"); d.open = !!obs.value;
    d.appendChild(elem("summary", "", "＋ Agregar una observación"));
    d.appendChild(obs);
    return d;
  }

  // «TECLADO — TECLADO EXPANDIDO ESPAÑOL» → «TECLADO EXPANDIDO ESPAÑOL».
  function nombreTimbo(dn) {
    var partes = String(dn || "").split(" — ");
    return partes[partes.length - 1];
  }

  function tarjetaVer(i) {
    var t = elem("article", "rs-tarjeta rs-tarjeta--ver"); t.dataset.id = i.id;
    t.appendChild(elem("p", "rs-origen", "Así figura hoy en el sistema de compras del hospital:"));
    var cab = elem("div", "rs-tarjeta__cab"); cab.appendChild(elem("span", "rs-tarjeta__nombre", i.n)); t.appendChild(cab);
    var prop = elem("div", "rs-propuesto");
    var linea = elem("div"); linea.appendChild(document.createTextNode("En TIMBÓ: ")); linea.appendChild(elem("code", "", i.cp || ""));
    prop.appendChild(linea); prop.appendChild(elem("div", "", i.dn || "")); t.appendChild(prop);
    t.appendChild(elem("p", "rs-ver-ok", "✓ Ya está en TIMBÓ. No tenés que hacer nada."));
    return t;
  }

  function tarjeta(i) {
    var r = respuesta(i.id);
    var t = elem("article", "rs-tarjeta" + (r && r.r ? " r-" + r.r : ""));
    t.dataset.id = i.id; t.dataset.base = "rs-tarjeta";
    t.appendChild(elem("p", "rs-origen", "Así figura hoy en el sistema de compras del hospital:"));
    var cab = elem("div", "rs-tarjeta__cab");
    cab.appendChild(elem("span", "rs-tarjeta__nombre", i.n));
    t.appendChild(cab);
    t.appendChild(elem("p", "rs-nousa-nota", "No se usa: queda fuera de la revisión. No hay que hacer nada más con este artículo."));
    t.appendChild(elem("p", "rs-otro-nota", "No es de este servicio: queda fuera de tu revisión. Compras lo va a reasignar."));

    var prop = elem("div", "rs-propuesto" + (i.cp ? "" : " rs-propuesto--vacio"));
    prop.appendChild(elem("p", "rs-propuesto__tit", "En TIMBÓ figura como"));
    if (i.cp) {
      prop.appendChild(elem("div", "rs-propuesto__nombre", nombreTimbo(i.dn)));
    } else {
      prop.appendChild(elem("div", "", "No se encontró en el catálogo."));
    }
    t.appendChild(prop);

    if (i.nu) t.appendChild(elem("p", "rs-alerta-item", "⚠ El código propuesto figura en el catálogo como «NO UTILIZAR»."));
    if (i.cc) t.appendChild(elem("p", "rs-alerta-item", "⚠ " + i.cc));
    var otrosMismo = i.g && GRUPOS.get(i.g) ? GRUPOS.get(i.g).length - 1 : 0;
    var det = elem("details", "rs-detalle"); det.appendChild(elem("summary", "", "＋ Más datos"));
    if (otrosMismo) det.appendChild(elem("p", "", "Hay " + otrosMismo + (otrosMismo === 1 ? " artículo más" : " artículos más") + " del hospital con este mismo artículo de TIMBÓ. Respondé cada uno por separado."));
    var cods = elem("p", "rs-codigos");
    cods.appendChild(document.createTextNode("Código actual: "));
    cods.appendChild(elem("code", "", i.id));
    if (i.ca) { cods.appendChild(document.createTextNode(" · artículo ")); cods.appendChild(elem("code", "", i.ca)); }
    cods.appendChild(document.createTextNode(" · bodega " + (i.b || [DATOS.bodega]).join(", ")));
    det.appendChild(cods);
    if (i.cp) det.appendChild(elem("p", "rs-codigos", "Código en TIMBÓ: " + i.cp + " · " + (i.dn || "")));
    if (i.ob) det.appendChild(elem("p", "rs-compartido", "También figura en: " + i.ob.join(", ")));
    det.appendChild(elem("p", "", i.m));
    if (i.nota) det.appendChild(elem("p", "", i.nota));
    if (i.cd) det.appendChild(elem("p", "", "Candidato descartado por la comparación automática: " + i.cd));
    t.appendChild(det);

    t.appendChild(bloqueRespuesta(i, r, false));
    var obs = elem("textarea", "rs-obs"); obs.rows = 2; obs.maxLength = 2000; obs.placeholder = "Observaciones (opcional)"; obs.value = r ? r.obs || "" : "";
    obs.setAttribute("aria-label", "Observaciones de " + i.n);
    t.appendChild(cajaObs(obs));
    var pie = elem("div", "rs-tarjeta__pie");
    pie.appendChild(elem("span", "rs-guardado-item", r && r.r && r.t ? "Guardado " + new Date(r.t).toLocaleString() : "Sin revisar"));
    var borrar = elem("button", "rs-borrar", "Quitar resultado"); borrar.type = "button"; borrar.hidden = !(r && r.r);
    pie.appendChild(borrar);
    t.appendChild(pie);
    return t;
  }

  function tarjetaGrupo(u) {
    var primero = u.items[0];
    var t = elem("article", "rs-tarjeta rs-grupo"); t.dataset.grupo = u.grupo;
    var prop = elem("div", "rs-propuesto");
    prop.appendChild(elem("p", "rs-propuesto__tit", "En TIMBÓ figura como"));
    prop.appendChild(elem("div", "rs-propuesto__nombre", nombreTimbo(primero.dn)));
    t.appendChild(prop);
    t.appendChild(elem("p", "rs-motivo", "Estos " + u.items.length + " artículos van al mismo artículo de TIMBÓ. Es normal: en TIMBÓ hay uno solo, general (como «Lámpara LED» para todas las lámparas LED), y el detalle se aclara al hacer el pedido."));
    if (primero.nu) t.appendChild(elem("p", "rs-alerta-item", "⚠ El código propuesto figura en el catálogo como «NO UTILIZAR»."));
    t.appendChild(elem("p", "rs-alerta-item rs-aviso-dup", ""));
    t.appendChild(elem("p", "rs-origen", "Así figuran hoy en el sistema de compras del hospital:"));
    u.items.forEach(function (i) {
      // Vista normal: lo ya respondido está al costado, no se repite en la card.
      if (!ui.filtro && revisado(i.id)) return;
      var r = respuesta(i.id);
      var f = elem("div", "rs-fila" + (r && r.r ? " r-" + r.r : "")); f.dataset.id = i.id; f.dataset.base = "rs-fila";
      var cab = elem("div", "rs-tarjeta__cab");
      cab.appendChild(elem("span", "rs-tarjeta__nombre", i.n));
      if (i.dup) cab.appendChild(elem("span", "rs-etiqueta-dup", "Mismo nombre que otro de esta card"));
      f.appendChild(cab);
      f.appendChild(elem("p", "rs-nousa-nota", "No se usa: queda fuera. No hay que hacer nada más."));
      f.appendChild(elem("p", "rs-otro-nota", "No es de este servicio: queda fuera de tu revisión."));
      var det = elem("details", "rs-detalle"); det.appendChild(elem("summary", "", "＋ Más datos"));
      var cods = elem("p", "rs-codigos");
      cods.appendChild(document.createTextNode("Código actual: ")); cods.appendChild(elem("code", "", i.id));
      if (i.ca) { cods.appendChild(document.createTextNode(" · artículo ")); cods.appendChild(elem("code", "", i.ca)); }
      if (i.b && i.b.length > 1) cods.appendChild(document.createTextNode(" · bodegas " + i.b.join(", ")));
      det.appendChild(cods);
      if (i.ob) det.appendChild(elem("p", "rs-compartido", "También figura en: " + i.ob.join(", ")));
      if (i.nota) det.appendChild(elem("p", "", i.nota));
      f.appendChild(det);
      f.appendChild(bloqueRespuesta(i, r, true));
      var obs = elem("textarea", "rs-obs"); obs.rows = 1; obs.maxLength = 2000; obs.placeholder = "Observaciones (opcional)"; obs.value = r ? r.obs || "" : "";
      obs.setAttribute("aria-label", "Observaciones de " + i.n);
      f.appendChild(cajaObs(obs));
      var pie = elem("div", "rs-tarjeta__pie");
      pie.appendChild(elem("span", "rs-guardado-item", r && r.r && r.t ? "Guardado " + new Date(r.t).toLocaleString() : "Sin revisar"));
      var borrar = elem("button", "rs-borrar", "Quitar resultado"); borrar.type = "button"; borrar.hidden = !(r && r.r);
      pie.appendChild(borrar);
      f.appendChild(pie);
      t.appendChild(f);
    });
    var acciones = elem("div", "rs-grupo__todos");
    var todos = elem("button", "rs-btn rs-todos", "✓ Sí, es este para todos");
    todos.type = "button"; todos.title = "Marca «Sí, es este» en los artículos de esta card que todavía no tienen respuesta.";
    acciones.appendChild(todos);
    var ninguno = elem("button", "rs-btn rs-btn--claro rs-ninguno", "Ninguno es este");
    ninguno.type = "button"; ninguno.title = "Marca «Es otra cosa» (se pide que los carguen) en los que todavía no tienen respuesta.";
    acciones.appendChild(ninguno);
    t.appendChild(acciones);
    avisoDuplicado(t);
    return t;
  }

  // Dos artículos con el mismo nombre marcados como correctos para el mismo
  // código: puede ser el mismo artículo cargado dos veces. Solo se avisa.
  function avisoDuplicado(t) {
    var aviso = t.querySelector(".rs-aviso-dup"); if (!aviso) return;
    var marcados = GRUPOS.get(t.dataset.grupo).filter(function (i) { var r = respuesta(i.id); return i.dup && r && r.r === "correcto"; });
    var porNombre = {};
    marcados.forEach(function (i) { var k = normal(i.n).replace(/\s+/g, " ").trim(); (porNombre[k] = porNombre[k] || []).push(i.id); });
    var dobles = Object.keys(porNombre).filter(function (k) { return porNombre[k].length > 1; });
    aviso.hidden = !dobles.length;
    aviso.textContent = dobles.length ? "⚠ Posible duplicado: los códigos internos " + dobles.map(function (k) { return porNombre[k].join(" y "); }).join("; ") + " tienen el mismo nombre y los marcaste como correctos. Anotá en observaciones si son el mismo artículo." : "";
  }

  function actualizarTarjeta(t, id) {
    var r = respuesta(id);
    t.className = t.dataset.base + (r && r.r ? " r-" + r.r : "");
    var bloque = t.querySelector(".rs-pasos");
    if (bloque) bloque.replaceWith(bloqueRespuesta(POR_ID.get(id), r, t.classList.contains("rs-fila")));
    t.querySelector(".rs-guardado-item").textContent = r && r.r && r.t ? "Guardado " + new Date(r.t).toLocaleString() : "Sin revisar";
    t.querySelector(".rs-borrar").hidden = !(r && r.r);
    var card = t.closest(".rs-grupo"); if (card) avisoDuplicado(card);
  }

  // Si en esta pestaña quedan pocos (o ninguno), avisa cuántos faltan en las
  // otras, con un botón para ir: el centro muestra solo la pestaña elegida.
  var NOMBRES_PESTANA = { 1: "No están en TIMBÓ", 2: "Confirmar el código" };
  function pintarOtrasPestanas(aca) {
    var cont = $("rs-otras"); if (!cont) return;
    cont.textContent = "";
    if (ui.filtro || ui.buscar) return;
    [1, 2].filter(function (s) { return s !== ui.seccion; }).forEach(function (s) {
      var n = ITEMS.filter(function (i) { return i.s === s && !revisado(i.id); }).length;
      if (!n) return;
      var b = elem("button", "rs-otras__ir", (aca ? "También te faltan " : "Te faltan ") + n + " en «" + NOMBRES_PESTANA[s] + "» →");
      b.type = "button"; b.dataset.irSeccion = s;
      cont.appendChild(b);
    });
  }

  // Cuando no queda nada en la pestaña: «¡Terminaste!» si no queda nada en
  // ninguna, o «Listo esta parte» si faltan en otra (el botón para ir lo pone
  // pintarOtrasPestanas).
  function cartelSinPendientes() {
    var quedan = ITEMS.filter(function (i) { return !revisado(i.id); }).length;
    var c = elem("div", "rs-terminaste" + (quedan ? " rs-terminaste--parte" : ""));
    if (quedan) {
      c.appendChild(elem("b", "", "Listo esta parte"));
      c.appendChild(elem("p", "", "No quedan artículos para revisar acá. Te faltan " + quedan + " en otra pestaña."));
      return c;
    }
    c.appendChild(elem("b", "", "¡Terminaste! No quedan más artículos para revisar."));
    if (enviada()) c.appendChild(elem("p", "", "Tu revisión ya fue enviada."));
    else if ($("rs-finalizar")) {
      c.appendChild(elem("p", "", "Último paso: mirá la revisión final y enviala."));
      var b = elem("button", "rs-btn rs-btn--grande", "Ver la revisión final"); b.type = "button";
      b.addEventListener("click", function () { $("rs-finalizar").click(); });
      c.appendChild(b);
    }
    return c;
  }

  function pintarLista() {
    var lista = filtrados(), us = unidades(lista);
    var paginas = Math.max(1, Math.ceil(us.length / POR_PAGINA));
    if (ui.pagina >= paginas) ui.pagina = paginas - 1;
    if (ui.pagina < 0) ui.pagina = 0;
    var cont = $("rs-lista"); cont.textContent = "";
    var trozo = us.slice(ui.pagina * POR_PAGINA, (ui.pagina + 1) * POR_PAGINA);
    if (!trozo.length) cont.appendChild(ui.filtro || ui.buscar ? elem("div", "rs-vacio", "No hay artículos con este filtro en esta sección.") : cartelSinPendientes());
    trozo.forEach(function (u) {
      if (soloVer(u.items[0])) u.items.forEach(function (i) { cont.appendChild(tarjetaVer(i)); });
      else cont.appendChild(u.grupo ? tarjetaGrupo(u) : tarjeta(u.items[0]));
    });
    var tit = document.querySelector(".rs-centro__tit");
    if (tit) { tit.querySelector("h2").firstChild.textContent = enviada() ? "🔒 Revisión enviada · sin revisar " : ui.seccion === 3 ? "✓ Ya están en TIMBÓ " : "⏳ Pendientes de revisión "; tit.classList.toggle("rs-centro__tit--ver", ui.seccion === 3); }
    if ($("rs-centro-cuenta")) $("rs-centro-cuenta").textContent = lista.length;
    if (ui.seccion === 3) { $("rs-resultados").textContent = lista.length + " artículos ya están en TIMBÓ"; }
    else $("rs-resultados").textContent = lista.length + (ui.filtro ? " artículos con este filtro" : " artículos pendientes en esta sección" + (ui.buscar ? " con esta búsqueda" : "")) ;
    pintarOtrasPestanas(lista.length);
    pintarColumnas();
    $("rs-pagina").textContent = "Página " + (ui.pagina + 1) + " de " + paginas;
    $("rs-ant").disabled = ui.pagina === 0;
    $("rs-sig").disabled = ui.pagina >= paginas - 1;
    guardarUi();
  }

  // Lo ya revisado va a un costado: a la izquierda (verde) lo que se va a poder
  // pedir en TIMBÓ (hay que cargarlo o ya está), a la derecha (rojo) lo que queda
  // fuera (no se usa / no es del servicio). Lo que tiene dudas queda debajo del centro. Muestra todas
  // las secciones: la columna izquierda es la planilla final.
  // Mismo criterio que `clasificar` en el servidor (services/llaves_servicio.py).
  function clasificar(i, r) {
    if (!r || !r.r) return soloVer(i) ? "estan" : "falta";
    if (r.r === "no_necesario" || r.r === "otro_servicio") return "fuera";
    if (r.r === "aclaracion") return "falta";
    if (r.r === "correcto") return r.dec === "general" ? "estan" : (i.s === 1 ? "cargar" : "estan");
    return r.dec === "agregar" ? "cargar" : r.dec === "codigo" ? "estan" : "falta";
  }
  function queHacer(i, r) {
    var c = clasificar(i, r); r = r || {};
    if (c === "fuera") return r.r === "otro_servicio" ? "No es de este servicio" : "Ya no se usa";
    if (c === "cargar") return "Pedir el alta" + (r.r === "correcto" ? ": no está en el catálogo" : ": el código propuesto es otro artículo");
    if (c === "estan") return r.dec === "general" ? "Va en el artículo general " + (r.cod || i.cp || "") + " · al pedir, aclarar: «" + (r.det || "") + "»"
      : r.dec === "codigo" ? "Ya está con el código " + (r.cod || "—") : "Ya está con el código " + (i.cp || "");
    if (r && r.r === "no_corresponde") return "No es este código: falta decidir";
    return r && r.r === "aclaracion" ? "Requiere aclaración" : "Sin revisar";
  }
  function ladoDe(i, r) {
    var c = clasificar(i, r);
    if (c === "falta") return "rs-col-aclaracion";   // «No sé» y «No es este» sin decidir
    return c === "fuera" ? "rs-col-ok" : "rs-col-pedir";
  }
  var verTodasColumnas = {};
  function pintarColumnas() {
    var cont = $("rs-columnas"); if (!cont) return;
    cont.classList.toggle("rs-sin-lados", !!ui.filtro);
    if (ui.filtro) return;
    var porLado = { "rs-col-pedir": [], "rs-col-ok": [], "rs-col-aclaracion": [] };
    // Los de la sección 3 sin respuesta se ven solo en su pestaña: no se repiten acá.
    var soloEnPestana = 0;
    ITEMS.forEach(function (i) {
      if (!revisado(i.id) || !coincide(i)) return;
      var r = respuesta(i.id);
      if (soloVer(i) && !(r && r.r)) { soloEnPestana++; return; }
      porLado[ladoDe(i, r || {})].push(i);
    });
    var nec = necesidadesActivas();
    Object.keys(porLado).forEach(function (idCol) {
      var lista = porLado[idCol], extra = idCol === "rs-col-pedir" ? nec : [];
      var col = $(idCol), cuerpo = col.querySelector(".rs-col__lista"); cuerpo.textContent = "";
      col.querySelector(".rs-col__cuenta").textContent = lista.length + extra.length + (idCol === "rs-col-pedir" ? soloEnPestana : 0);
      if (idCol === "rs-col-aclaracion") col.hidden = !lista.length;
      var max = verTodasColumnas[idCol] ? lista.length : 40;
      // Lo último que se respondió va arriba de todo. En la verde, primero lo
      // que hay que pedir que carguen y después lo que ya está.
      var yaEsta = idCol === "rs-col-pedir" ? function (i) { return clasificar(i, respuesta(i.id)) === "estan"; } : function () { return false; };
      lista.sort(function (a, b) { return (yaEsta(a) - yaEsta(b)) || (fechaDe(respuesta(b.id)) - fechaDe(respuesta(a.id))); });
      var titulo = "";
      lista.slice(0, max).forEach(function (i) {
        if (idCol === "rs-col-pedir") {
          var t = clasificar(i, respuesta(i.id)) === "estan" ? "Ya están en TIMBÓ" : "Hay que pedir que los carguen";
          if (t !== titulo) { titulo = t; cuerpo.appendChild(elem("h3", "rs-col__sub", t)); }
        }
        cuerpo.appendChild(filaCompacta(i));
      });
      if (lista.length > max) { var mas = elem("button", "rs-btn rs-btn--claro rs-btn--chico rs-col__mas", "Mostrar los " + lista.length); mas.type = "button"; mas.dataset.col = idCol; cuerpo.appendChild(mas); }
      extra.forEach(function (n) {
        var f = elem("div", "rs-compacta rs-compacta--nec");
        var a = elem("div", "rs-compacta__txt");
        a.appendChild(elem("b", "", n.d));
        a.appendChild(elem("span", "rs-chip-decision", "Cargado por el servicio"));
        if (n.p) a.appendChild(elem("span", "rs-codigos", " " + n.p));
        f.appendChild(a); cuerpo.appendChild(f);
      });
      if (idCol === "rs-col-pedir" && soloEnPestana) cuerpo.appendChild(elem("p", "rs-nota", "＋ " + soloEnPestana + " que ya están en TIMBÓ (pestaña 3)."));
      else if (!lista.length && !extra.length) cuerpo.appendChild(elem("p", "rs-vacio", "Todavía ninguno."));
    });
  }
  // Una línea por artículo: ícono, nombre y «↶» para deshacer. Al tocarla
  // se abre el detalle en palabras simples.
  var lineasAbiertas = new Set();
  function queDice(i, r, c) {
    if (c === "cargar") return "Se pide que lo carguen en TIMBÓ.";
    if (c === "estan") return r.dec === "general" ? "Va en un artículo general de TIMBÓ." : "Ya está en TIMBÓ: no hay que hacer nada.";
    if (c === "fuera") return r.r === "otro_servicio" ? "No es de este servicio: queda fuera." : "Ya no se usa: queda fuera y no se va a poder pedir.";
    return r.r === "aclaracion" ? "Quedó como «No sé»: falta responderlo." : "Falta responderlo.";
  }
  function filaCompacta(i) {
    var r = respuesta(i.id) || {};
    var c = clasificar(i, r);
    var abierta = lineasAbiertas.has(i.id);
    var f = elem("div", "rs-compacta rs-linea rs-linea--" + c + " r-" + (r.r || "ver") + (abierta ? " rs-linea--abierta" : "")); f.dataset.id = i.id;
    var cab = elem("button", "rs-linea__cab"); cab.type = "button"; cab.setAttribute("aria-expanded", abierta ? "true" : "false");
    cab.appendChild(elem("span", "rs-linea__icono", c === "fuera" ? "✗" : c === "falta" ? "?" : "✓"));
    cab.appendChild(elem("span", "rs-linea__nombre", i.n));
    cab.appendChild(elem("span", "rs-linea__flecha", abierta ? "▴" : "▾"));
    f.appendChild(cab);
    if (r.r) {
      var b = elem("button", "rs-borrar rs-volver rs-linea__deshacer", "↶"); b.type = "button";
      b.title = "Deshacer: vuelve a la lista para responderlo de nuevo"; b.setAttribute("aria-label", "Deshacer " + i.n);
      f.appendChild(b);
    }
    if (abierta) {
      var d = elem("div", "rs-linea__detalle");
      d.appendChild(elem("p", "rs-linea__que", queDice(i, r, c)));
      if (i.cp) d.appendChild(elem("p", "", r.r === "no_corresponde" ? "TIMBÓ proponía «" + nombreTimbo(i.dn) + "», pero es otra cosa."
        : "En TIMBÓ figura como: " + nombreTimbo(i.dn)));
      if (r.obs) d.appendChild(elem("p", "", "Observación: «" + r.obs + "»"));
      if (r.persona) d.appendChild(elem("p", "rs-nota", "Respondió " + r.persona + (r.t ? " · " + new Date(r.t).toLocaleString() : "")));
      if (r.r) { var bd = elem("button", "rs-btn rs-btn--claro rs-btn--chico rs-volver", "↶ Deshacer"); bd.type = "button"; d.appendChild(bd); }
      f.appendChild(d);
    }
    return f;
  }

  function contar() {
    var c = { total: ITEMS.length, revisados: 0, correcto: 0, no_corresponde: 0, no_necesario: 0, otro_servicio: 0, aclaracion: 0, porSeccion: { 1: [0, 0], 2: [0, 0], 3: [0, 0] } };
    ITEMS.forEach(function (i) {
      var r = respuesta(i.id); c.porSeccion[i.s][1]++;
      if (r && r.r && !sinDecidirGuardado(r)) { c.revisados++; c[r.r]++; c.porSeccion[i.s][0]++; }
      else if (soloVer(i)) { c.revisados++; c.porSeccion[i.s][0]++; }
    });
    c.pendientes = c.total - c.revisados;
    return c;
  }

  function pintarAvance() {
    var c = contar();
    $("rs-revisados").textContent = c.revisados; $("rs-pendientes").textContent = c.pendientes;
    $("rs-avance-relleno").style.width = (c.total ? (100 * c.revisados / c.total) : 0).toFixed(1) + "%";
    document.querySelectorAll("[data-cuenta]").forEach(function (s) {
      var p = c.porSeccion[s.dataset.cuenta];
      s.textContent = s.dataset.cuenta === "3" ? p[1] + " artículos · solo para mirar" : p[0] + " de " + p[1] + " revisados";
    });
    document.querySelectorAll(".rs-tab").forEach(function (b) { b.classList.toggle("activa", Number(b.dataset.seccion) === ui.seccion); });
    var res = $("rs-resumen"); res.textContent = "";
    [["Total", c.total], ["No se usan", c.no_necesario], ["No son de este servicio", c.otro_servicio], ["No corresponden", c.no_corresponde], ["Requieren aclaración", c.aclaracion], ["Correctos / corresponden", c.correcto], ["Pendientes", c.pendientes], ["Necesarios que no están", necesidadesActivas().length]].forEach(function (x) {
      var d = elem("div"); d.appendChild(elem("b", "", String(x[1]))); d.appendChild(elem("span", "", x[0])); res.appendChild(d);
    });
    function f(v) { return v ? new Date(v).toLocaleString() : "—"; }
    if ($("rs-f-inicio")) { $("rs-f-inicio").textContent = f(estado.inicio); $("rs-f-mod").textContent = f(estado.modificado); }
    $("rs-f-fin").textContent = f(estado.finalizado);
  }

  function pintarInstrucciones() {
    var ins = INSTRUCCIONES[ui.seccion], cont = $("rs-instrucciones"); cont.textContent = "";
    var d = elem("details"), sum = elem("summary");
    sum.appendChild(elem("span", "", ins.texto + " "));
    if (ins.pasos.length) sum.appendChild(elem("b", "rs-mas", "＋ Ver qué hacer"));
    d.appendChild(sum);
    var ol = elem("ol"); ins.pasos.forEach(function (p) { ol.appendChild(elem("li", "", p)); }); d.appendChild(ol);
    cont.appendChild(d);
  }

  function pintarIdentificacion() {
    [["rs-servicio", "servicio"], ["rs-nombre", "nombre"], ["rs-apellido", "apellido"], ["rs-obs-general", "observaciones"]].forEach(function (x) {
      var e = $(x[0]); if (e && document.activeElement !== e) e.value = estado[x[1]] || "";
    });
  }

  function capa(id, clase, texto) {
    var li = $(id); li.classList.remove("ok", "atencion", "error"); if (clase) li.classList.add(clase);
    li.querySelector(".rs-capa-estado").textContent = texto;
  }

  function pintarGuardado() {
    if (SERVIDOR) { pintarEnvio(); return; }
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

  function pintarTodo() { pintarIdentificacion(); pintarInstrucciones(); pintarAvance(); pintarLista(); pintarNecesidades(); pintarOrientacion(); pintarGuardado(); pintarDeshacer(); }

  function guardarUi() { if (SERVIDOR) return; lsGuardar("ui::" + CLAVE, JSON.stringify({ seccion: ui.seccion, pagina: ui.pagina })); }

  // ------------------------------------------------------------ alertas ---
  function alerta(tipo, texto, textoBoton, accion) {
    // Los «Listo…» saturan: lo hecho ya se ve en las columnas. Solo se
    // muestran los avisos (errores, atención) y los que traen un botón.
    if (tipo === "ok" && !textoBoton) return;
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
      var e = elem("button", "rs-btn" + (b.claro ? " rs-btn--claro" : "") + (b.rojo ? " rs-btn--rojo" : ""), b.texto); e.type = "button";
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
        requierenAclaracion: c.aclaracion, pendientes: c.pendientes,
        necesariosQueNoEstan: necesidadesActivas().length
      },
      porSeccion: { faltanCargar: c.porSeccion[1], necesitanConfirmacion: c.porSeccion[2], existenYVerificar: c.porSeccion[3] },
      observaciones: estado.observaciones,
      respuestas: ITEMS.map(function (i) {
        var r = respuesta(i.id) || {};
        return {
          codigo_interno: i.id, codigo_articulo: i.ca, descripcion: i.n, seccion: i.s,
          codigo_propuesto: i.cp, descripcion_nomenclador: i.dn, motivo: i.m,
          agrupado_con_mismo_codigo: !!i.g, mismo_nombre_en_el_grupo: !!i.dup,
          resultado: r.r || null, observaciones: r.obs || "", decision: r.dec || null, codigo_correcto: r.cod || "", detalle_timbo: r.det || "",
          fecha: r.t || null, historial: r.hist || []
        };
      }),
      // Incluye las quitadas (con `quitada: true`) para que, al volver a
      // cargar la devolución, no reaparezcan desde una copia vieja.
      necesidades: Object.keys(estado.necesidades || {}).map(function (k) { return estado.necesidades[k]; })
        .sort(function (a, b) { return (a.creado || "") < (b.creado || "") ? -1 : 1; })
        .map(function (n) {
          return {
            id: n.id, descripcion: n.d, presentacion: n.p, uso: n.u,
            tipo: n.tipo || "", tipo_texto: TIPOS_NEC[n.tipo] || "",
            catalogo: n.cat, catalogo_texto: CATALOGO_NEC[n.cat] || "", codigo_catalogo: n.cod,
            observaciones: n.obs, creado: n.creado, modificado: n.t, quitada: !!n.baja, historial: n.hist || []
          };
        }),
      planillaFinal: planillaFinal(),
      respuestasDeArticulosQueYaNoEstan: estado.huerfanas,
      registro: estado.registro
    };
  }

  function reabrir() {
    if (SERVIDOR) return post(SERVIDOR.urlFinalizar, { reabrir: true }).then(function (res) { if (!res.ok) throw new Error(res.error); estado.finalizado = null; });
    estado.finalizado = null; registrar("revisión reabierta", "deshacer finalizar"); guardar(true);
  }

  // ---------------------------------------------------- revisión final ---
  // Antes de terminar: todo agrupado por lo que hay que hacer con cada cosa.
  var GRUPOS_FINALES = [
    ["cargar", "Hay que cargar en TIMBÓ", "Se pide que los carguen."],
    ["estan", "Ya están en TIMBÓ", "No hay que hacer nada."],
    ["falta", "No se revisaron", "Sin respuesta o con dudas."],
    ["fuera", "Quedan fuera", "No se usan o no son del servicio: no se van a poder pedir."]
  ];
  function gruposFinales() {
    var g = { cargar: [], estan: [], fuera: [], falta: [] };
    ITEMS.forEach(function (i) { g[clasificar(i, respuesta(i.id))].push(i); });
    return g;
  }
  // Lo que va a la planilla final: lo que hay que cargar y lo que ya está.
  function planillaFinal() {
    var filas = [];
    ITEMS.forEach(function (i) {
      var r = respuesta(i.id), c = clasificar(i, r);
      if (c === "cargar" || c === "estan") filas.push({ grupo: c, accion: queHacer(i, r), id: i.id, n: i.n, cp: i.cp || "", cod: r.cod || (c === "estan" ? i.cp || "" : ""), det: r.det || "", obs: r.obs || "" });
    });
    necesidadesActivas().forEach(function (n) {
      filas.push({ grupo: "cargar", accion: "Pedir el alta: lo cargó el servicio", id: "", n: n.d + (n.p ? " — " + n.p : ""), cp: "", cod: n.cod || "", det: "", obs: n.obs || "", tipo: TIPOS_NEC[n.tipo] || "" });
    });
    return filas;
  }
  function sinDecidir() { return ITEMS.filter(function (i) { var r = respuesta(i.id); return r && r.r === "no_corresponde" && !r.dec; }); }

  function pintarPlanillaFinal() {
    var cont = $("rs-planilla-final"); if (!cont) return;
    cont.textContent = "";
    cont.hidden = !SERVIDOR;
    if (SERVIDOR) {
      var a = elem("a", "rs-btn rs-btn--claro rs-btn--chico", "⬇️ Bajar la planilla final (Excel)"); a.href = SERVIDOR.urlPlanillaFinal;
      cont.appendChild(a);
      cont.appendChild(elem("span", "rs-nota", " Tiene una hoja por cada bloque de abajo."));
    }
  }

  function filaFinal(i, grupo) {
    var r = respuesta(i.id) || {};
    var f = elem("div", "rs-compacta"); f.dataset.id = i.id;
    var a = elem("div", "rs-compacta__txt");
    a.appendChild(elem("b", "", i.n));
    a.appendChild(elem("span", "rs-codigos", " cód. " + i.id));
    a.appendChild(elem("span", "rs-rf-que", queHacer(i, r)));
    if (r.obs) a.appendChild(elem("span", "rs-compacta__obs", "«" + r.obs + "»"));
    if (grupo === "falta" && r.r === "no_corresponde") a.appendChild(controlesDecision(i, r));
    f.appendChild(a);
    if (r.r) { var b = elem("button", "rs-borrar rs-volver", "↶ Deshacer"); b.type = "button"; f.appendChild(b); }
    return f;
  }

  function pintarRevisionFinal() {
    pintarPlanillaFinal();
    var g = gruposFinales(), nec = necesidadesActivas();
    var res = $("rs-revfinal-resumen"); res.textContent = "";
    GRUPOS_FINALES.forEach(function (x) {
      var n = g[x[0]].length + (x[0] === "cargar" ? nec.length : 0);
      var d = elem("div", "rs-revfinal-tile rs-rf-" + x[0]); d.appendChild(elem("b", "", String(n))); d.appendChild(elem("span", "", x[1])); res.appendChild(d);
    });
    var cont = $("rs-revfinal-grupos"); cont.textContent = "";
    GRUPOS_FINALES.forEach(function (x) {
      var lista = g[x[0]], extra = x[0] === "cargar" ? nec : [];
      if (x[0] === "falta") {
        // Primero lo que necesita una decisión, después las dudas y al final lo sin revisar.
        var orden = function (i) { var r = respuesta(i.id); return r && r.r === "no_corresponde" ? 0 : r && r.r ? 1 : 2; };
        lista = lista.slice().sort(function (a, b) { return orden(a) - orden(b); });
      }
      var det = elem("details", "rs-rf-grupo rs-rf-" + x[0]); det.dataset.grupo = x[0];
      det.open = x[0] !== "fuera" && !(x[0] === "estan" && lista.length > 30);
      var sum = elem("summary"); sum.appendChild(elem("b", "", x[1] + " (" + (lista.length + extra.length) + ")")); sum.appendChild(elem("span", "rs-nota", " " + x[2]));
      if (x[0] === "falta") { var falta = sinDecidir().length; if (falta) sum.appendChild(elem("span", "rs-falta-decidir", " " + falta + " no coinciden y falta decidir.")); }
      det.appendChild(sum);
      if (!lista.length && !extra.length) det.appendChild(elem("p", "rs-vacio", "Ninguno."));
      var max = x[0] === "falta" ? 40 : lista.length;
      lista.slice(0, max).forEach(function (i) { det.appendChild(filaFinal(i, x[0])); });
      if (lista.length > max) det.appendChild(elem("p", "rs-nota", "…y " + (lista.length - max) + " más sin revisar."));
      extra.forEach(function (n) {
        var f = elem("div", "rs-compacta rs-compacta--nec");
        var a = elem("div", "rs-compacta__txt");
        a.appendChild(elem("b", "", n.d + (n.p ? " — " + n.p : "")));
        a.appendChild(elem("span", "rs-rf-que", "Pedir el alta: lo cargó el servicio" + (n.tipo ? " · " + TIPOS_NEC[n.tipo] : "")));
        if (n.obs) a.appendChild(elem("span", "rs-compacta__obs", "«" + n.obs + "»"));
        f.appendChild(a); det.appendChild(f);
      });
      cont.appendChild(det);
    });
  }
  function controlesDecision(i, r) {
    var c = elem("div", "rs-decision"); c.setAttribute("role", "group"); c.setAttribute("aria-label", "Qué hacer con " + i.n);
    c.appendChild(elem("span", "rs-decision__preg", "¿Qué hacemos?"));
    [["agregar", "Pedir que lo carguen en TIMBÓ"], ["nousa", "Ya no se usa"]].forEach(function (x) {
      var b = elem("button", "rs-res rs-dec", x[1]); b.type = "button"; b.dataset.dec = x[0];
      b.setAttribute("aria-pressed", r.dec === x[0] ? "true" : "false");
      c.appendChild(b);
    });
    // «Sé cuál es el código» solo abre el campo: se guarda con «Guardar».
    var cod = elem("input", "rs-dec-cod"); cod.type = "text"; cod.maxLength = 40; cod.placeholder = "Escribí el código, ej.: 19.1.283.4"; cod.value = r.cod || "";
    cod.hidden = true; cod.setAttribute("aria-label", "Código correcto de " + i.n);
    c.appendChild(cod);
    var g = elem("button", "rs-btn rs-btn--chico rs-dec-guardar", "Guardar"); g.type = "button"; g.hidden = true;
    c.appendChild(g);
    return c;
  }

  // Botones «agregar / código correcto / no se usa» de un «no corresponde»,
  // en la columna izquierda o en la revisión final.
  function manejarDecision(d) {
    var fila = d.closest("[data-id]"), idd = fila.dataset.id, rr = respuesta(idd) || {};
    if (d.dataset.dec === "codigo") {
      var campo = fila.querySelector(".rs-dec-cod"), g = fila.querySelector(".rs-dec-guardar");
      campo.hidden = g.hidden = false; campo.focus();
      return;
    }
    if (d.dataset.dec === "nousa") cambiarResultado(idd, "no_necesario", rr.obs || "");
    else decidir(idd, d.dataset.dec, "");
    pintarLista(); pintarAvance(); guardar(true);
    if ($("rs-revfinal") && !$("rs-revfinal").hidden) pintarRevisionFinal();
  }
  function guardarCodigoDecision(b) {
    var fila = b.closest("[data-id]"), idd = fila.dataset.id, cod = fila.querySelector(".rs-dec-cod").value.trim();
    if (!cod) { alerta("error", "Escribí el código del Catálogo WEB."); return; }
    decidir(idd, "codigo", cod);
    pintarLista(); pintarAvance(); guardar(true);
    if ($("rs-revfinal") && !$("rs-revfinal").hidden) pintarRevisionFinal();
  }

  function abrirRevisionFinal() {
    var p = $("rs-revfinal"); pintarRevisionFinal(); p.hidden = false;
    p.scrollIntoView({ block: "start" });
  }

  function finalizar() { abrirRevisionFinal(); }

  function finalizarConfirmado() {
    var faltan = [];
    if (!SERVIDOR) ["rs-nombre", "rs-apellido"].forEach(function (id) { var e = $(id); var vacio = !e.value.trim(); e.classList.toggle("rs-falta", vacio); if (vacio) faltan.push(e); });
    if (faltan.length) { alerta("error", "Para finalizar hacen falta tu nombre y tu apellido."); faltan[0].focus(); faltan[0].scrollIntoView({ block: "center" }); return; }
    var c = contar();
    function hacer() {
      if (SERVIDOR) {
        enviarSucios();
        cola = cola.then(function () { return post(SERVIDOR.urlFinalizar, { observaciones: estado.observaciones || "" }); }).then(function (res) {
          if (!res.ok) { alerta("error", res.error || "No se pudo finalizar."); return; }
          estado.finalizado = res.datos.finalizado;
          apilar("marcar «Terminé»", reabrir);
          pintarAvance();
          alerta("ok", "¡Listo! Quedó registrado que el servicio terminó la revisión. Si cambiás algo, se vuelve a abrir.");
        });
        return;
      }
      apilar("finalizar la revisión", reabrir);
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

  function marcarEnviada() {
    document.body.classList.add("rs-enviada");
    var a = $("rs-aviso-enviada");
    if (a) { a.hidden = false; a.querySelector("span").textContent = new Date(SERVIDOR.enviado).toLocaleString() + (SERVIDOR.enviadoPor ? " por " + SERVIDOR.enviadoPor : ""); }
    pilaDeshacer.length = 0; pintarDeshacer();
    pintarLista();
  }
  function enviarRevision() {
    if (bloqueada()) return;
    var c = contar(), falta = sinDecidir().length;
    var cuerpo = elem("div");
    cuerpo.appendChild(elem("p", "rs-envio-final", "⚠ Después de enviarla NO vas a poder cambiar, deshacer ni revisar nada."));
    if (c.pendientes || falta) cuerpo.appendChild(elem("p", "rs-alerta-item", "⚠ Todavía quedan " + c.pendientes + " artículos sin revisar" + (falta ? " y " + falta + " sin decidir" : "") + "."));
    abrirModal("¿Enviar la revisión?", cuerpo, [
      { texto: "Todavía no", claro: true, accion: function () {} },
      { texto: "Sí, enviar definitivamente", rojo: true, accion: function () {
        enviarSucios();
        cola = cola.then(function () { return post(SERVIDOR.urlEnviar, { confirmo: true }); }).then(function (res) {
          if (!res.ok) { alerta("error", res.error || "No se pudo enviar."); return; }
          SERVIDOR.enviado = res.datos.enviado; SERVIDOR.enviadoPor = res.datos.enviadoPor || ""; estado.finalizado = res.datos.finalizado;
          marcarEnviada(); pintarAvance();
          window.scrollTo(0, 0);
          alerta("ok", "¡Listo! La revisión se envió.");
        });
      } }
    ]);
  }

  // ------------------------------------------------------------ eventos ---
  function irAlProximoPendiente() {
    var orden = [ui.seccion, 1, 2, 3].filter(function (v, i, a) { return a.indexOf(v) === i; });
    for (var k = 0; k < orden.length; k++) {
      var s = orden[k];
      var us = unidades(ITEMS.filter(function (i) { return i.s === s && !revisado(i.id); }));
      var pos = us.findIndex(function (u) { return u.items.some(function (i) { return !revisado(i.id); }); });
      if (pos !== -1) {
        ui.seccion = s; ui.buscar = ""; ui.filtro = ""; $("rs-buscar").value = ""; $("rs-estado").value = "";
        ui.pagina = 0;
        pintarInstrucciones(); pintarAvance(); pintarLista();
        var pendiente = us[pos].items.find(function (i) { return !revisado(i.id); });
        var t = document.querySelector('[data-id="' + CSS.escape(pendiente.id) + '"]');
        if (t) { t.scrollIntoView({ block: "center" }); t.querySelector(".rs-res").focus(); }
        return;
      }
    }
    alerta("ok", "¡No quedan artículos pendientes!");
  }

  // Engancha un evento solo si el elemento existe (la pantalla en línea no
  // tiene los controles de guardado de la planilla descargable).
  function on(id, evento, fn) { var e = $(id); if (e) e.addEventListener(evento, fn); }

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
      if ((e.ctrlKey || e.metaKey) && (e.key === "z" || e.key === "Z")) { e.preventDefault(); deshacerUltimo(); return; }
      if (e.key === "ArrowLeft" && !$("rs-ant").disabled) $("rs-ant").click();
      if (e.key === "ArrowRight" && !$("rs-sig").disabled) $("rs-sig").click();
    });

    $("rs-lista").addEventListener("click", function (e) {
      var card = e.target.closest(".rs-grupo");
      if (card && (e.target.closest(".rs-ninguno") || e.target.closest(".rs-todos"))) {
        var todosSi = !!e.target.closest(".rs-todos");
        var cambiados = [];
        GRUPOS.get(card.dataset.grupo).forEach(function (i) {
          if (revisado(i.id)) return;
          var fila = card.querySelector('[data-id="' + CSS.escape(i.id) + '"]');
          var antes = respuesta(i.id);
          cambiados.push({ id: i.id, obs: antes ? antes.obs || "" : "" });
          var obsFila = fila ? (fila.querySelector(".rs-obs") || {}).value || "" : "";
          if (todosSi) responder(i.id, "correcto", obsFila, false, null);
          else responder(i.id, "no_corresponde", obsFila, false, "agregar");
        });
        var marcados = cambiados.length;
        if (marcados) {
          apilar((todosSi ? "«sí, es este» en " : "«ninguno es este» en ") + marcados + " artículos", function () { cambiados.forEach(function (x) { responder(x.id, null, x.obs); }); });
          pintarLista(); pintarAvance(); guardar(true);
        }
        alerta(marcados ? "ok" : "atencion", marcados ? "Listo: " + marcados + " artículos marcados. Si te equivocaste, tocá ↶ Deshacer." : "Todos los artículos de esta card ya tienen respuesta.");
        return;
      }
      var t = e.target.closest("[data-id]"); if (!t) return;
      var id = t.dataset.id, item = POR_ID.get(id);
      var obsActual = function () { var o = t.querySelector(".rs-obs"); return o ? o.value : ""; };
      var repintar = function () { if (ui.filtro) actualizarTarjeta(t, id); else pintarLista(); pintarAvance(); guardar(true); };
      var boton = e.target.closest(".rs-res, .rs-enlace-mas, [data-guardar]");
      if (boton) {
        var r = respuesta(id) || {};
        if (boton.dataset.uso === "si") {
          abiertos[id] = "si";
          if (r.r === "no_necesario" || r.r === "otro_servicio") cambiarResultado(id, null, obsActual(), "volver a «se usa» en " + item.n);
          actualizarTarjeta(t, id); pintarAvance(); guardar(true);
          return;
        }
        if (boton.dataset.abrir) {
          abiertos[id] = abiertos[id] === boton.dataset.abrir && !r.r ? "si" : boton.dataset.abrir;
          actualizarTarjeta(t, id);
          var campo = t.querySelector(".rs-in-cod");
          if (campo && boton.dataset.abrir !== "no") campo.focus();
          return;
        }
        if (boton.dataset.guardar) {
          var cod = (t.querySelector(".rs-in-cod") || {}).value || "";
          var det = (t.querySelector(".rs-in-det") || {}).value || "";
          cod = cod.trim(); det = det.trim();
          if (!cod) { alerta("error", "Escribí el código de TIMBÓ."); t.querySelector(".rs-in-cod").focus(); return; }
          if (det) cambiarResultado(id, "correcto", obsActual(), "ítem general en " + item.n, "general", cod, det);
          else cambiarResultado(id, "no_corresponde", obsActual(), "código " + cod + " en " + item.n, "codigo", cod);
          delete abiertos[id];
          repintar();
          return;
        }
        var nuevoR = boton.dataset.r, nuevaDec = boton.dataset.dec || null;
        if (r.r === nuevoR && (r.dec || null) === nuevaDec) return;
        cambiarResultado(id, nuevoR, obsActual(), null, nuevaDec);
        delete abiertos[id];
        repintar();
        return;
      }
      if (e.target.closest(".rs-borrar")) {
        delete abiertos[id];
        cambiarResultado(id, null, obsActual());
        if (ui.filtro) actualizarTarjeta(t, id); else pintarLista();
        pintarAvance(); guardar(true);
        return;
      }
      var copiar = e.target.closest(".rs-copiar");
      if (copiar && navigator.clipboard) navigator.clipboard.writeText(copiar.dataset.copiar).then(function () { copiar.textContent = "Copiado"; setTimeout(function () { copiar.textContent = "Copiar"; }, 1200); }, function () {});
    });
    $("rs-lista").addEventListener("keydown", function (e) {
      if (e.key !== "Enter" || !e.target.matches(".rs-in-cod, .rs-in-det")) return;
      e.preventDefault();
      var b = e.target.closest(".rs-paso").querySelector("[data-guardar]"); if (b) b.click();
    });
    $("rs-lista").addEventListener("input", function (e) {
      if (!e.target.classList.contains("rs-obs")) return;
      var t = e.target.closest("[data-id]"), id = t.dataset.id, r = respuesta(id);
      responder(id, r ? r.r : null, e.target.value, true);
      actualizarTarjeta(t, id); pintarAvance(); guardar(false);
    });

    on("rs-columnas", "click", function (e) {
      var d = e.target.closest(".rs-dec");
      if (d && !e.target.closest("#rs-lista")) { manejarDecision(d); return; }
      var gd = e.target.closest(".rs-dec-guardar");
      if (gd && !e.target.closest("#rs-lista")) { guardarCodigoDecision(gd); return; }
      var mas = e.target.closest(".rs-col__mas");
      if (mas) { verTodasColumnas[mas.dataset.col] = true; pintarColumnas(); return; }
      var lin = e.target.closest(".rs-linea__cab");
      if (lin) {
        var idl = lin.closest("[data-id]").dataset.id;
        if (lineasAbiertas.has(idl)) lineasAbiertas.delete(idl); else lineasAbiertas.add(idl);
        pintarColumnas();
        return;
      }
      var v = e.target.closest(".rs-volver"); if (!v) return;
      var id = v.closest("[data-id]").dataset.id, r = respuesta(id);
      cambiarResultado(id, null, r ? r.obs || "" : "", "volver a revisar " + (POR_ID.get(id) || { n: id }).n);
      pintarLista(); pintarAvance(); guardar(true);
    });
    on("rs-deshacer", "click", deshacerUltimo);

    [["rs-servicio", "servicio"], ["rs-nombre", "nombre"], ["rs-apellido", "apellido"], ["rs-obs-general", "observaciones"]].forEach(function (x) {
      on(x[0], "input", function (e) {
        estado[x[1]] = e.target.value; e.target.classList.remove("rs-falta");
        if (SERVIDOR) return;  // en línea, las observaciones generales van al finalizar
        if (!estado.inicio) estado.inicio = ahora();
        estado.modificado = ahora(); pintarAvance(); guardar(false);
      });
    });

    on("rs-archivo-nuevo", "click", crearArchivo);
    on("rs-archivo-abrir", "click", abrirArchivo);
    on("rs-archivo-reconectar", "click", reconectar);
    on("rs-exportar", "click", exportarCopia);
    on("rs-importar", "change", function (e) { var f = e.target.files[0]; if (f) importarCopia(f); e.target.value = ""; });
    on("rs-finalizar", "click", finalizar);
    on("rs-otras", "click", function (e) {
      var b = e.target.closest("[data-ir-seccion]"); if (!b) return;
      var tab = document.querySelector('.rs-tab[data-seccion="' + b.dataset.irSeccion + '"]');
      if (tab) { tab.click(); tab.scrollIntoView({ block: "start" }); }
    });
    document.querySelectorAll(".rs-enviar").forEach(function (b) { b.addEventListener("click", enviarRevision); });
    if (enviada()) marcarEnviada();
    on("rs-revfinal-confirmar", "click", function () {
      var falta = sinDecidir().length;
      if (!falta) { finalizarConfirmado(); return; }
      abrirModal("Faltan decidir " + falta, elem("p", "", "Hay " + falta + " artículos que no coinciden y todavía no dijiste si hay que agregarlos, cuál es el código correcto o si ya no se usan. Van a quedar fuera de la planilla final."), [
        { texto: "Decidir ahora", accion: function () { var g = document.querySelector('#rs-revfinal [data-grupo="no"]'); if (g) { g.open = true; g.scrollIntoView({ block: "start" }); } } },
        { texto: "Terminar igual", claro: true, accion: finalizarConfirmado }
      ]);
    });
    // Enter en el campo del código = Guardar.
    document.addEventListener("keydown", function (e) {
      if (e.key !== "Enter" || !e.target.classList.contains("rs-dec-cod")) return;
      e.preventDefault(); guardarCodigoDecision(e.target);
    });
    on("rs-revfinal-cerrar", "click", function () { $("rs-revfinal").hidden = true; });
    on("rs-revfinal-imprimir", "click", function () {
      document.body.classList.add("rs-imprimir-final");
      window.print();
      setTimeout(function () { document.body.classList.remove("rs-imprimir-final"); }, 500);
    });
    on("rs-revfinal", "click", function (e) {
      var d = e.target.closest(".rs-dec");
      if (d) { manejarDecision(d); return; }
      var gd = e.target.closest(".rs-dec-guardar");
      if (gd) { guardarCodigoDecision(gd); return; }
      var v = e.target.closest(".rs-volver"); if (!v) return;
      var id = v.closest("[data-id]").dataset.id, r = respuesta(id);
      cambiarResultado(id, null, r ? r.obs || "" : "", "volver a revisar " + (POR_ID.get(id) || { n: id }).n);
      pintarLista(); pintarAvance(); pintarRevisionFinal(); guardar(true);
    });

    $("rs-nec-tipo").addEventListener("change", pintarOrientacion);
    $("rs-nec-cat").addEventListener("change", pintarOrientacion);
    $("rs-nec-form").addEventListener("submit", function (e) {
      e.preventDefault();
      var datos = leerFormNec();
      if (!datos.d) { $("rs-nec-desc").classList.add("rs-falta"); $("rs-nec-desc").focus(); alerta("error", "Escribí la descripción del artículo."); return; }
      var idEditado = necEditando, previa = idEditado ? datosDe(estado.necesidades[idEditado]) : null;
      necGuardar(datos, idEditado).then(function (id) {
        if (previa) apilar("editar «" + datos.d + "»", function () { return necGuardar(previa, id); });
        else apilar("agregar «" + datos.d + "»", function () { return necBaja(id, true); });
        terminarEdicionNec();
        pintarNecesidades(); pintarAvance();
        alerta("ok", previa ? "Cambios guardados." : "Artículo agregado a la lista.");
      }, function (err) { alerta("error", err.message); });
    });
    $("rs-nec-cancelar").addEventListener("click", terminarEdicionNec);
    $("rs-nec-lista").addEventListener("click", function (e) {
      var b = e.target.closest("[data-accion]"); if (!b) return;
      var id = b.closest("[data-nec]").dataset.nec, n = estado.necesidades[id];
      if (b.dataset.accion === "editar") {
        necEditando = id; llenarFormNec(n);
        $("rs-nec-guardar").textContent = "Guardar cambios"; $("rs-nec-cancelar").hidden = false;
        $("rs-nec-desc").focus(); $("rs-nec-form").scrollIntoView({ block: "center" });
      } else {
        abrirModal("¿Quitar este artículo?", elem("p", "", "«" + n.d + "» deja de figurar en la lista. Se puede deshacer y queda en el historial."), [
          { texto: "Quitar", accion: function () {
            if (necEditando === id) terminarEdicionNec();
            necBaja(id, true).then(function () {
              apilar("quitar «" + n.d + "»", function () { return necBaja(id, false); });
              pintarNecesidades(); pintarAvance();
            }, function (err) { alerta("error", err.message); });
          } },
          { texto: "Cancelar", claro: true, accion: function () {} }
        ]);
      }
    });

    // Si se cierra con texto a medio guardar, la copia sincrónica en
    // localStorage lo conserva; IndexedDB se completa al reabrir.
    function alSalir() {
      if (SERVIDOR) { if (sucios.size) enviarSucios(); return; }
      if (hayCambiosSinGuardar) lsGuardar(CLAVE, JSON.stringify(estado));
    }
    window.addEventListener("pagehide", alSalir);
    document.addEventListener("visibilitychange", function () { if (document.visibilityState === "hidden") { alSalir(); if (hayCambiosSinGuardar) guardar(true); } });
  }

  var canal = null;
  try {
    if (SERVIDOR) throw new Error("en línea no hace falta");
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
    if (SERVIDOR) {
      estado = Object.assign(estadoNuevo(), DATOS.estado || {});
      ui.seccion = [1, 2, 3].find(function (s) { return DATOS.secciones[s]; }) || 1;
      conectarEventos();
      pintarTodo();
      return;
    }
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
    // Carga o quita un artículo necesario por el mismo camino que el formulario.
    agregarNecesidad: function (datos) {
      necEditando = null;
      var n = guardarNecesidad(Object.assign({ d: "", p: "", u: "", tipo: "", cat: "no_busque", cod: "", obs: "" }, datos));
      pintarNecesidades(); pintarAvance(); guardar(true);
      return n.id;
    },
    quitarNecesidad: function (id) { quitarNecesidad(id); pintarNecesidades(); pintarAvance(); guardar(true); },
    deshacer: function () { deshacerUltimo(); },
    planillaFinal: function () { return planillaFinal(); },
    decidir: function (id, dec, cod) { decidir(id, dec, cod); pintarLista(); pintarAvance(); guardar(true); },
    gruposFinales: function () { var g = gruposFinales(), r = {}; Object.keys(g).forEach(function (k) { r[k] = g[k].map(function (i) { return i.id; }); }); return r; },
    pila: function () { return pilaDeshacer.map(function (a) { return a.texto; }); },
    esperar: function () { return cola; }
  };

  iniciar();
})();
