// procesos-editor.js — editor de circuitos de /admin/procesos.
// Sin librerías externas (la CSP del sitio no las permite) y sin JS en línea.
// Los datos llegan en <script type="application/json" id="procesos-datos">.
// Todo lo que se valida acá se vuelve a validar en el servidor.
(() => {
  'use strict';
  const datosEl = document.getElementById('procesos-datos');
  if (!datosEl) return;
  const D = JSON.parse(datosEl.textContent);
  const CAT = D.catalogos;
  const SOLO = !!D.solo_lectura;
  const CLASE = D.circuito.clase;
  const raiz = document.getElementById('editor');
  const svg = document.getElementById('lienzo');
  const NS = 'http://www.w3.org/2000/svg';
  const csrf = raiz.dataset.csrf;

  // ---------------------------------------------------------------- colores
  const COLOR = {
    verde: ['#1b7a45', '#e7f5ec'], azul: ['#2456c7', '#eaf0fd'], amarillo: ['#8a6a00', '#fbf3d5'],
    naranja: ['#b85400', '#fdecdc'], rojo: ['#b42318', '#fdeceb'], violeta: ['#6d3fb5', '#f1eafd'],
    gris: ['#5b6472', '#eef0f3'],
  };
  const FLECHA = {
    normal: { c: '#475569', d: '' }, alternativa: { c: '#2456c7', d: '8 5' }, retorno: { c: '#6d3fb5', d: '8 5' },
    rechazo: { c: '#b42318', d: '' }, espera: { c: '#8a6a00', d: '2 5' }, incidencia: { c: '#b42318', d: '4 4' },
    digitalizacion: { c: '#0e7490', d: '10 4 2 4' },
  };
  const colorEstado = (e) => COLOR[(CAT.estados[e] || CAT.estados.pendiente_confirmacion).color];
  const W = 230;

  // ----------------------------------------------------------------- estado
  const clonar = (x) => JSON.parse(JSON.stringify(x));
  let modelo = clonar(D.contenido);
  let comentarios = D.comentarios || [];
  let revision = JSON.parse((document.getElementById('procesos-revision') || { textContent: '[]' }).textContent);
  let sel = null; // {tipo: 'nodo'|'flecha', id}
  let vista = raiz.classList.contains('pe-editor--informe') ? 'general' : leerPref('vista', 'general');
  let camara = { x: 40, y: 40, k: 1 };
  const pasado = [], futuro = [];
  let sucio = false, guardando = false, temporizador = null;

  function leerPref(k, def) { try { return localStorage.getItem('procesos:' + k) || def; } catch (e) { return def; } }
  function guardarPref(k, v) { try { localStorage.setItem('procesos:' + k, v); } catch (e) { /* sin almacenamiento */ } }

  const nodo = (id) => modelo.nodos.find((n) => n.id === id);
  const flecha = (id) => modelo.flechas.find((f) => f.id === id);
  const nuevoId = (p) => p + Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
  const comentariosDe = (id) => comentarios.filter((c) => c.elemento === id);
  const rango = (id) => D.rangos.find((r) => r.id === id);
  const doc = (id) => CAT.documentos.find((d) => d.id === id);
  const pesos = (v) => (v == null ? '' : '$' + Number(v).toLocaleString('es-AR', { maximumFractionDigits: 2 }));
  function textoRango(r) {
    if (!r) return '';
    if (r.minimo == null && r.maximo != null) return 'Hasta ' + pesos(r.maximo);
    if (r.minimo != null && r.maximo == null) return 'Más de ' + pesos(r.minimo);
    if (r.minimo != null && r.maximo != null) return pesos(r.minimo) + ' a ' + pesos(r.maximo);
    return '';
  }

  // --------------------------------------------------------------- historial
  function tomarFoto() {
    pasado.push(JSON.stringify(modelo));
    if (pasado.length > 150) pasado.shift();
    futuro.length = 0;
    actualizarBotones();
  }
  function deshacer() {
    if (!pasado.length || SOLO) return;
    futuro.push(JSON.stringify(modelo));
    modelo = JSON.parse(pasado.pop());
    if (sel && !(sel.tipo === 'nodo' ? nodo(sel.id) : flecha(sel.id))) sel = null;
    cambio(); dibujarPanel();
  }
  function rehacer() {
    if (!futuro.length || SOLO) return;
    pasado.push(JSON.stringify(modelo));
    modelo = JSON.parse(futuro.pop());
    if (sel && !(sel.tipo === 'nodo' ? nodo(sel.id) : flecha(sel.id))) sel = null;
    cambio(); dibujarPanel();
  }
  function editar(fn) { if (SOLO) return; tomarFoto(); fn(); cambio(); }

  // --------------------------------------------------------------- guardado
  function cambio() {
    dibujar();
    actualizarBotones();
    if (SOLO) return;
    sucio = true;
    estadoGuardado('pendiente');
    clearTimeout(temporizador);
    temporizador = setTimeout(guardarBorrador, 1200);
  }
  async function pedir(url, cuerpo) {
    const r = await fetch(url, {
      method: 'POST', credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
      body: JSON.stringify(cuerpo),
    });
    let j = null;
    try { j = await r.json(); } catch (e) { /* respuesta sin JSON */ }
    if (r.status === 401 || r.redirected) throw new Error('La sesión se cerró. Volvé a entrar al panel en otra pestaña.');
    if (!r.ok || !j || !j.ok) throw new Error((j && j.error) || 'No se pudo guardar.');
    return j;
  }
  function aplicarRespuesta(j) {
    if (j.contenido) { // el servidor ajustó algo: se toma su versión
      modelo = j.contenido;
      dibujar(); dibujarPanel();
    }
    (j.ajustes || []).forEach((a) => aviso(a.mensaje, 'error'));
    if (j.revision) { revision = j.revision; dibujarRevision(); }
  }
  async function guardarBorrador() {
    if (SOLO || guardando) return;
    guardando = true;
    estadoGuardado('guardando');
    const enviado = JSON.stringify(modelo);
    try {
      const j = await pedir(D.urls.borrador, { contenido: modelo });
      if (JSON.stringify(modelo) === enviado) sucio = false;
      aplicarRespuesta(j);
      estadoGuardado(sucio ? 'pendiente' : 'ok');
      if (sucio) { clearTimeout(temporizador); temporizador = setTimeout(guardarBorrador, 800); }
    } catch (e) {
      estadoGuardado('error', e.message);
      clearTimeout(temporizador);
      temporizador = setTimeout(guardarBorrador, 6000);
    } finally { guardando = false; }
  }
  function estadoGuardado(cual, msg) {
    const el = document.getElementById('estado-guardado');
    if (!el) return;
    const hora = new Date().toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' });
    el.dataset.estado = cual;
    el.textContent = { pendiente: 'Cambios sin guardar…', guardando: 'Guardando…', ok: 'Guardado ' + hora,
      error: (msg || 'No se pudo guardar') + ' · reintento en unos segundos' }[cual];
  }
  window.addEventListener('beforeunload', (ev) => {
    if (sucio || guardando) { ev.preventDefault(); ev.returnValue = ''; }
  });

  // ------------------------------------------------------------------ avisos
  function aviso(texto, tipo) {
    const caja = document.getElementById('avisos');
    if (!caja) return;
    const el = document.createElement('div');
    el.className = 'pe-aviso' + (tipo === 'error' ? ' pe-aviso--error' : '');
    el.setAttribute('role', 'status');
    el.textContent = texto;
    caja.appendChild(el);
    setTimeout(() => el.remove(), tipo === 'error' ? 9000 : 3500);
  }

  // ------------------------------------------------------------- geometría
  function lineas(texto, max, cuantas) {
    const palabras = String(texto || '').split(/\s+/).filter(Boolean);
    const out = [];
    let actual = '';
    for (const p of palabras) {
      if ((actual + ' ' + p).trim().length > max && actual) { out.push(actual); actual = p; } else actual = (actual + ' ' + p).trim();
    }
    if (actual) out.push(actual);
    if (out.length > cuantas) { out.length = cuantas; out[cuantas - 1] = out[cuantas - 1].replace(/.{0,2}$/, '') + '…'; }
    return out.length ? out : [''];
  }
  function responsableCorto(n) {
    const r = (n.responsables || [])[0];
    if (r) return (r.perfil_timbo ? 'Perfil TIMBÓ: ' : '') + r.quien;
    return n.sector || '';
  }
  function medidas(n) {
    const esDec = n.tipo === 'decision';
    const tit = lineas(n.titulo, esDec ? 22 : 28, vista === 'detallada' ? 3 : 2);
    let extra = [];
    if (vista === 'detallada') {
      const est = (CAT.estados[n.estado] || {}).nombre || '';
      extra.push(est);
      if (n.sistema && n.sistema !== 'sin_definir') extra.push(CAT.sistemas[n.sistema]);
      const resp = responsableCorto(n);
      if (resp) extra = extra.concat(lineas('👤 ' + resp, 34, 2));
      const nf = (n.fuentes || []).length;
      extra.push(nf ? '📎 ' + nf + (nf === 1 ? ' fuente' : ' fuentes') : '📎 Sin fuente');
    }
    let h = 24 + tit.length * 17 + extra.length * 15 + 18;
    if (esDec) h = Math.max(h + 34, 96);
    if (n.tipo === 'inicio' || n.tipo === 'fin') h = Math.max(h, 52);
    return { w: W, h: Math.max(h, 56), tit, extra };
  }
  const centro = (n) => { const m = medidas(n); return { x: n.x + m.w / 2, y: n.y + m.h / 2, m }; };

  function puertos(a, b) {
    const A = centro(a), B = centro(b);
    const dx = B.x - A.x, dy = B.y - A.y;
    if (Math.abs(dy) >= Math.abs(dx) * 0.55 && dy > 0) {
      return { p1: [A.x, a.y + A.m.h], d1: [0, 1], p2: [B.x, b.y], d2: [0, -1] };
    }
    if (Math.abs(dy) >= Math.abs(dx) * 0.55 && dy < 0) { // hacia arriba: rodea por el costado
      const lado = dx >= 0 ? 1 : -1;
      return { p1: [lado > 0 ? a.x + A.m.w : a.x, A.y], d1: [lado, 0], p2: [lado > 0 ? b.x + B.m.w : b.x, B.y], d2: [lado, 0], vuelta: true };
    }
    if (dx > 0) return { p1: [a.x + A.m.w, A.y], d1: [1, 0], p2: [b.x, B.y], d2: [-1, 0] };
    return { p1: [a.x, A.y], d1: [-1, 0], p2: [b.x + B.m.w, B.y], d2: [1, 0] };
  }

  // ----------------------------------------------------------------- dibujo
  const capa = { flechas: null, nodos: null, temp: null };
  function el(tag, attrs, padre) {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) if (attrs[k] != null) e.setAttribute(k, attrs[k]);
    if (padre) padre.appendChild(e);
    return e;
  }
  function texto(padre, x, y, s, attrs) {
    const t = el('text', Object.assign({ x, y, 'font-size': 13, fill: '#1c222b', 'font-family': 'Segoe UI, system-ui, sans-serif' }, attrs || {}), padre);
    t.textContent = s;
    return t;
  }
  function prepararLienzo() {
    svg.innerHTML = '';
    const defs = el('defs', {}, svg);
    for (const k in FLECHA) {
      const m = el('marker', { id: 'punta-' + k, viewBox: '0 0 10 10', refX: 8, refY: 5, markerWidth: 7, markerHeight: 7, orient: 'auto-start-reverse' }, defs);
      el('path', { d: 'M0,0 L10,5 L0,10 z', fill: FLECHA[k].c }, m);
    }
    const pat = el('pattern', { id: 'cuadricula', width: 20, height: 20, patternUnits: 'userSpaceOnUse' }, defs);
    el('circle', { cx: 1, cy: 1, r: 1, fill: '#d6dbe4' }, pat);
    capa.fondo = el('rect', { x: -50000, y: -50000, width: 100000, height: 100000, fill: 'url(#cuadricula)', 'data-fondo': '1' }, svg);
    capa.mundo = el('g', {}, svg);
    capa.carriles = el('g', {}, capa.mundo);
    capa.flechas = el('g', {}, capa.mundo);
    capa.nodos = el('g', {}, capa.mundo);
    capa.temp = el('g', {}, capa.mundo);
  }
  function aplicarCamara() {
    capa.mundo.setAttribute('transform', `translate(${camara.x},${camara.y}) scale(${camara.k})`);
    capa.fondo.setAttribute('transform', `translate(${camara.x},${camara.y}) scale(${camara.k})`);
    const z = document.getElementById('nivel-zoom');
    if (z) z.textContent = Math.round(camara.k * 100) + '%';
  }

  function formaNodo(g, n, m, col) {
    const w = m.w, h = m.h;
    const papel = n.soporte === 'papel';
    let fondo = papel ? '#fffaf0' : '#ffffff';
    if (n.tipo === 'error') fondo = '#fff5f4';
    if (n.tipo === 'observacion') fondo = '#fafafa';
    const borde = n.tipo === 'error' ? '#b42318' : col[0];
    const dash = ['pendiente', 'observacion', 'excepcion'].includes(n.tipo) ? '6 4' : null;
    const comun = { fill: fondo, stroke: borde, 'stroke-width': 2, 'stroke-dasharray': dash, class: 'pe-forma' };
    if (n.tipo === 'decision') {
      el('polygon', Object.assign({ points: `${w / 2},0 ${w},${h / 2} ${w / 2},${h} 0,${h / 2}` }, comun), g);
    } else if (n.tipo === 'inicio' || n.tipo === 'fin') {
      el('rect', Object.assign({ width: w, height: h, rx: h / 2 }, comun), g);
    } else if (n.tipo === 'documento') {
      el('path', Object.assign({ d: `M0,8 Q0,0 8,0 L${w - 8},0 Q${w},0 ${w},8 L${w},${h - 8} C${w * 0.75},${h - 22} ${w * 0.25},${h + 8} 0,${h - 8} Z` }, comun), g);
    } else if (n.tipo === 'observacion') {
      el('path', Object.assign({ d: `M0,0 L${w - 16},0 L${w},16 L${w},${h} L0,${h} Z` }, comun), g);
    } else {
      el('rect', Object.assign({ width: w, height: h, rx: 10 }, comun), g);
      el('rect', { x: 0, y: 0, width: 7, height: h, rx: 3, fill: col[0] }, g); // franja del estado
    }
  }

  function dibujarNodo(n) {
    const m = medidas(n);
    const col = colorEstado(n.estado);
    const g = el('g', { transform: `translate(${n.x},${n.y})`, 'data-nodo': n.id, class: 'pe-nodo' + (sel && sel.tipo === 'nodo' && sel.id === n.id ? ' es-sel' : ''), tabindex: 0, role: 'button', 'aria-label': (CAT.tipos[n.tipo] || {}).nombre + ': ' + n.titulo }, capa.nodos);
    if (sel && sel.tipo === 'nodo' && sel.id === n.id) {
      el('rect', { x: -6, y: -6, width: m.w + 12, height: m.h + 12, rx: 14, fill: 'none', stroke: '#2456c7', 'stroke-width': 3, opacity: 0.55 }, g);
    }
    formaNodo(g, n, m, col);
    const esDec = n.tipo === 'decision';
    const tipo = CAT.tipos[n.tipo] || { icono: '', nombre: '' };
    // ícono del tipo y punto de estado
    const yTipo = esDec ? Math.round(m.h / 2 - (m.tit.length * 17 + m.extra.length * 15) / 2 - 6) : 19;
    texto(g, esDec ? m.w / 2 : 16, yTipo, tipo.icono + ' ' + tipo.nombre.toUpperCase(), { 'font-size': 10, 'font-weight': 700, fill: col[0], 'letter-spacing': 0.5, 'text-anchor': esDec ? 'middle' : 'start' });
    el('circle', { cx: esDec ? m.w - 34 : m.w - 14, cy: esDec ? m.h / 2 : 14, r: 6, fill: col[0] }, g).appendChild(document.createElementNS(NS, 'title')).textContent = (CAT.estados[n.estado] || {}).nombre || '';
    let y = esDec ? yTipo + 19 : 38;
    m.tit.forEach((l) => { texto(g, m.w / 2, y, l, { 'text-anchor': 'middle', 'font-weight': 700, 'font-size': 13.5 }); y += 17; });
    m.extra.forEach((l, i) => { texto(g, m.w / 2, y + 2, l, { 'text-anchor': 'middle', 'font-size': 11.5, fill: i === 0 ? col[0] : '#5b6472', 'font-weight': i === 0 ? 700 : 400 }); y += 15; });
    // insignias abajo: soporte y comentarios
    const ins = [];
    if (n.soporte && n.soporte !== 'sin_definir') ins.push({ papel: '📄 Papel', digital: '💻 Digital', papel_y_digital: '📄+💻' }[n.soporte]);
    const nc = comentariosDe(n.id).filter((c) => !c.resuelto).length;
    if (nc) ins.push('💬 ' + nc);
    if (ins.length) texto(g, esDec ? m.w / 2 : m.w - 10, m.h - 7, ins.join('   '), { 'text-anchor': esDec ? 'middle' : 'end', 'font-size': 11, fill: '#5b6472' });
    if (!SOLO) {
      const asa = el('g', { class: 'pe-asa', 'data-asa': n.id, transform: `translate(${m.w / 2},${m.h + 2})` }, g);
      el('circle', { r: 10, fill: '#2456c7', stroke: '#fff', 'stroke-width': 2 }, asa);
      texto(asa, 0, 4.5, '+', { 'text-anchor': 'middle', fill: '#fff', 'font-weight': 700, 'font-size': 15 });
      el('title', {}, asa).textContent = 'Arrastrá hasta otro bloque para conectar';
    }
  }

  function rutaFlecha(f, idx, total) {
    const a = nodo(f.desde), b = nodo(f.hasta);
    if (!a || !b) return null;
    if (a === b) { const c = centro(a); return { d: `M${a.x + c.m.w},${c.y - 10} C${a.x + c.m.w + 70},${c.y - 60} ${a.x + c.m.w + 70},${c.y + 60} ${a.x + c.m.w},${c.y + 10}`, lx: a.x + c.m.w + 60, ly: c.y }; }
    const p = puertos(a, b);
    const off = (idx - (total - 1) / 2) * 16;
    const perp = p.d1[0] === 0 ? [1, 0] : [0, 1];
    const p1 = [p.p1[0] + perp[0] * off, p.p1[1] + perp[1] * off];
    const p2 = [p.p2[0] + perp[0] * off, p.p2[1] + perp[1] * off];
    const dist = Math.max(40, Math.min(160, Math.hypot(p2[0] - p1[0], p2[1] - p1[1]) / 2.2));
    const k = p.vuelta ? 90 + Math.abs(off) : dist;
    const c1 = [p1[0] + p.d1[0] * k, p1[1] + p.d1[1] * k];
    const c2 = [p2[0] + p.d2[0] * k, p2[1] + p.d2[1] * k];
    const fin = [p2[0] + p.d2[0] * 2, p2[1] + p.d2[1] * 2];
    const t = 0.5, u = 1 - t; // punto medio de la Bézier para la etiqueta
    const lx = u * u * u * p1[0] + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t * t * t * fin[0];
    const ly = u * u * u * p1[1] + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t * t * t * fin[1];
    return { d: `M${p1[0]},${p1[1]} C${c1[0]},${c1[1]} ${c2[0]},${c2[1]} ${fin[0]},${fin[1]}`, lx, ly };
  }

  function dibujarFlechas() {
    capa.flechas.innerHTML = '';
    const grupos = {};
    modelo.flechas.forEach((f) => { const k = [f.desde, f.hasta].sort().join('|'); (grupos[k] = grupos[k] || []).push(f); });
    modelo.flechas.forEach((f) => {
      const k = [f.desde, f.hasta].sort().join('|');
      const r = rutaFlecha(f, grupos[k].indexOf(f), grupos[k].length);
      if (!r) return;
      const est = FLECHA[f.tipo] || FLECHA.normal;
      const es = sel && sel.tipo === 'flecha' && sel.id === f.id;
      const g = el('g', { 'data-flecha': f.id, class: 'pe-flecha' }, capa.flechas);
      el('path', { d: r.d, fill: 'none', stroke: 'transparent', 'stroke-width': 16 }, g); // zona para hacer clic
      el('path', { d: r.d, fill: 'none', stroke: es ? '#2456c7' : est.c, 'stroke-width': es ? 3.5 : 2.2, 'stroke-dasharray': est.d || null, 'marker-end': `url(#punta-${f.tipo in FLECHA ? f.tipo : 'normal'})` }, g);
      const rg = f.rango != null ? rango(f.rango) : null;
      let etiqueta = f.etiqueta || '';
      if (rg) etiqueta = (etiqueta ? etiqueta + ' · ' : '') + textoRango(rg) + (rg.estado !== 'verificado' ? ' (sin validar)' : '');
      if (!etiqueta && f.tipo !== 'normal') etiqueta = CAT.tipos_flecha[f.tipo];
      if (etiqueta) {
        const ls = lineas(etiqueta, 30, 3);
        const ancho = Math.max(...ls.map((l) => l.length)) * 6.4 + 14;
        const alto = ls.length * 14 + 6;
        el('rect', { x: r.lx - ancho / 2, y: r.ly - alto / 2, width: ancho, height: alto, rx: 6, fill: '#ffffff', stroke: es ? '#2456c7' : '#d6dbe4' }, g);
        ls.forEach((l, i) => texto(g, r.lx, r.ly - alto / 2 + 14 + i * 14, l, { 'text-anchor': 'middle', 'font-size': 11, fill: est.c, 'font-weight': 600 }));
      }
    });
  }

  // Carriles: columnas de fondo con su título (solo visuales, no se editan acá).
  const COLOR_CARRIL = { naranja: ['#9a5b10', '#fdf1e2'], azul: ['#2456c7', '#eaf0fd'], verde: ['#1b7a45', '#e7f5ec'], violeta: ['#6d3fb5', '#f1eafd'], gris: ['#5b6472', '#eef0f3'] };
  function dibujarCarriles() {
    capa.carriles.innerHTML = '';
    const cs = modelo.carriles || [];
    if (!cs.length || !modelo.nodos.length) return;
    let y1 = Infinity, y2 = -Infinity;
    modelo.nodos.forEach((n) => { y1 = Math.min(y1, n.y); y2 = Math.max(y2, n.y + medidas(n).h); });
    cs.forEach((c) => {
      const col = COLOR_CARRIL[c.color] || COLOR_CARRIL.gris;
      el('rect', { x: c.x, y: y1 - 70, width: c.w, height: y2 - y1 + 110, rx: 16, fill: col[1], opacity: 0.55 }, capa.carriles);
      el('rect', { x: c.x, y: y1 - 70, width: c.w, height: 38, rx: 12, fill: col[0] }, capa.carriles);
      texto(capa.carriles, c.x + c.w / 2, y1 - 45, c.titulo, { 'text-anchor': 'middle', fill: '#ffffff', 'font-weight': 700, 'font-size': 13.5, 'letter-spacing': 0.6 });
    });
  }

  function dibujar() {
    dibujarCarriles();
    dibujarFlechas();
    capa.nodos.innerHTML = '';
    modelo.nodos.forEach(dibujarNodo);
    const vacio = document.getElementById('lienzo-vacio');
    if (vacio) vacio.hidden = modelo.nodos.length > 0;
    actualizarBotones();
  }

  // --------------------------------------------------------- interacción
  function aMundo(ev) {
    const r = svg.getBoundingClientRect();
    return { x: (ev.clientX - r.left - camara.x) / camara.k, y: (ev.clientY - r.top - camara.y) / camara.k };
  }
  let arrastre = null;
  svg.addEventListener('pointerdown', (ev) => {
    if (ev.button !== 0) return;
    const asa = ev.target.closest('[data-asa]');
    const gN = ev.target.closest('[data-nodo]');
    const gF = ev.target.closest('[data-flecha]');
    const p = aMundo(ev);
    if (asa && !SOLO) {
      arrastre = { modo: 'conectar', desde: asa.dataset.asa };
      svg.setPointerCapture(ev.pointerId);
      ev.preventDefault();
      return;
    }
    if (gN) {
      const n = nodo(gN.dataset.nodo);
      seleccionar({ tipo: 'nodo', id: n.id });
      if (!SOLO) {
        arrastre = { modo: 'mover', id: n.id, dx: p.x - n.x, dy: p.y - n.y, foto: JSON.stringify(modelo), movido: false };
        svg.setPointerCapture(ev.pointerId);
      }
      return;
    }
    if (gF) { seleccionar({ tipo: 'flecha', id: gF.dataset.flecha }); return; }
    seleccionar(null);
    arrastre = { modo: 'paneo', x: ev.clientX, y: ev.clientY, cx: camara.x, cy: camara.y };
    svg.setPointerCapture(ev.pointerId);
    svg.classList.add('pe-paneando');
  });
  svg.addEventListener('pointermove', (ev) => {
    if (!arrastre) return;
    const p = aMundo(ev);
    if (arrastre.modo === 'mover') {
      const n = nodo(arrastre.id);
      const nx = Math.round((p.x - arrastre.dx) / 10) * 10, ny = Math.round((p.y - arrastre.dy) / 10) * 10;
      if (nx !== n.x || ny !== n.y) { n.x = nx; n.y = ny; arrastre.movido = true; dibujar(); }
    } else if (arrastre.modo === 'paneo') {
      camara.x = arrastre.cx + ev.clientX - arrastre.x;
      camara.y = arrastre.cy + ev.clientY - arrastre.y;
      aplicarCamara();
    } else if (arrastre.modo === 'conectar') {
      const a = centro(nodo(arrastre.desde));
      capa.temp.innerHTML = '';
      el('path', { d: `M${a.x},${a.y + a.m.h / 2} L${p.x},${p.y}`, stroke: '#2456c7', 'stroke-width': 2.5, 'stroke-dasharray': '6 4', fill: 'none', 'marker-end': 'url(#punta-alternativa)' }, capa.temp);
    }
  });
  function terminarArrastre(ev) {
    if (!arrastre) return;
    const a = arrastre;
    arrastre = null;
    svg.classList.remove('pe-paneando');
    capa.temp.innerHTML = '';
    if (a.modo === 'mover' && a.movido) {
      pasado.push(a.foto); futuro.length = 0;
      cambio();
    }
    if (a.modo === 'conectar') {
      const objetivo = document.elementFromPoint(ev.clientX, ev.clientY);
      const g = objetivo && objetivo.closest('[data-nodo]');
      if (g && g.dataset.nodo !== a.desde) conectar(a.desde, g.dataset.nodo);
    }
  }
  svg.addEventListener('pointerup', terminarArrastre);
  svg.addEventListener('pointercancel', terminarArrastre);
  svg.addEventListener('wheel', (ev) => {
    ev.preventDefault();
    const r = svg.getBoundingClientRect();
    zoom(ev.deltaY < 0 ? 1.12 : 1 / 1.12, ev.clientX - r.left, ev.clientY - r.top);
  }, { passive: false });
  svg.addEventListener('dblclick', (ev) => {
    if (SOLO || ev.target.closest('[data-nodo]') || ev.target.closest('[data-flecha]')) return;
    const p = aMundo(ev);
    agregar('actividad', { x: p.x - W / 2, y: p.y - 30, sinConectar: true });
  });
  svg.addEventListener('keydown', (ev) => {
    const g = ev.target.closest && ev.target.closest('[data-nodo]');
    if (g && (ev.key === 'Enter' || ev.key === ' ')) { seleccionar({ tipo: 'nodo', id: g.dataset.nodo }); ev.preventDefault(); }
  });

  function zoom(f, cx, cy) {
    const r = svg.getBoundingClientRect();
    if (cx == null) { cx = r.width / 2; cy = r.height / 2; }
    const k = Math.min(2.5, Math.max(0.2, camara.k * f));
    camara.x = cx - (cx - camara.x) * (k / camara.k);
    camara.y = cy - (cy - camara.y) * (k / camara.k);
    camara.k = k;
    aplicarCamara();
  }
  function limites() {
    if (!modelo.nodos.length) return { x: 0, y: 0, w: 600, h: 400 };
    let x1 = Infinity, y1 = Infinity, x2 = -Infinity, y2 = -Infinity;
    modelo.nodos.forEach((n) => { const m = medidas(n); x1 = Math.min(x1, n.x); y1 = Math.min(y1, n.y); x2 = Math.max(x2, n.x + m.w); y2 = Math.max(y2, n.y + m.h); });
    // Con carriles: que entren completos (el +120/-120 de abajo es el margen general).
    (modelo.carriles || []).forEach((c) => { x1 = Math.min(x1, c.x + 110); x2 = Math.max(x2, c.x + c.w - 110); });
    if ((modelo.carriles || []).length) y1 -= 40;
    return { x: x1 - 120, y: y1 - 40, w: x2 - x1 + 240, h: y2 - y1 + 100 };
  }
  function ajustar() {
    const b = limites(), r = svg.getBoundingClientRect();
    camara.k = Math.min(1.2, Math.max(0.2, Math.min(r.width / b.w, r.height / b.h)));
    camara.x = (r.width - b.w * camara.k) / 2 - b.x * camara.k;
    camara.y = 20 - b.y * camara.k;
    aplicarCamara();
  }
  // Al abrir: ancho completo y desde arriba (un circuito largo se recorre bajando).
  function ajustarAncho() {
    const b = limites(), r = svg.getBoundingClientRect();
    camara.k = Math.min(1, Math.max(0.35, r.width / b.w));
    camara.x = (r.width - b.w * camara.k) / 2 - b.x * camara.k;
    camara.y = 20 - b.y * camara.k;
    aplicarCamara();
  }
  // El editor ocupa justo el alto que queda debajo de la barra del panel.
  function acomodarAlto() {
    if (raiz.classList.contains('pe-editor--informe') || document.fullscreenElement) return;
    if (window.innerWidth <= 800) { raiz.style.height = ''; return; }
    const arriba = raiz.getBoundingClientRect().top + window.scrollY;
    raiz.style.height = Math.max(560, window.innerHeight - arriba) + 'px';
  }
  function centrarEn(id) {
    const n = nodo(id);
    if (!n) return;
    const c = centro(n), r = svg.getBoundingClientRect();
    camara.x = r.width / 2 - c.x * camara.k;
    camara.y = r.height / 2 - c.y * camara.k;
    aplicarCamara();
  }

  // ------------------------------------------------------------- acciones
  function estadoInicial() { return CLASE === 'oficial' ? 'pendiente_documentacion' : 'pendiente_confirmacion'; }
  function agregar(tipo, opciones) {
    if (SOLO) return;
    opciones = opciones || {};
    const base = sel && sel.tipo === 'nodo' ? nodo(sel.id) : null;
    let x, y;
    if (opciones.x != null) { x = opciones.x; y = opciones.y; } else if (base) {
      const mb = medidas(base);
      if (tipo === 'error' || tipo === 'observacion' || tipo === 'responsable') { x = base.x + mb.w + 60; y = base.y; } else { x = base.x; y = base.y + mb.h + 70; }
    } else {
      const r = svg.getBoundingClientRect();
      x = (r.width / 2 - camara.x) / camara.k - W / 2;
      y = (r.height / 2 - camara.y) / camara.k - 30;
    }
    x = Math.round(x / 10) * 10; y = Math.round(y / 10) * 10;
    while (modelo.nodos.some((n) => Math.abs(n.x - x) < 40 && Math.abs(n.y - y) < 30)) { y += 40; }
    const n = { id: nuevoId('n'), tipo, titulo: CAT.tipos[tipo].nombre, descripcion: '', x, y, estado: estadoInicial(),
      soporte: 'sin_definir', sistema: 'sin_definir', sector: '', documentacion: '', resultado: '', condiciones: '',
      responsables: [], fuentes: [] };
    if (tipo === 'documento') n.documento = { origen: '', completa: '', recibe: '', revisa: '', autoriza: '', registra: '', archiva: '', continua: '' };
    if (tipo === 'error') n.error = { causa: '', detecta: '', interviene: '', resolucion: '', nueva_autorizacion: false, doc_adicional: false };
    if (CLASE === 'hospital') n.correspondencia = { circuito: '', nodo: '', relacion: '', nota: '' };
    editar(() => {
      modelo.nodos.push(n);
      if (base && !opciones.sinConectar && !['observacion', 'responsable', 'inicio'].includes(tipo)) {
        modelo.flechas.push({ id: nuevoId('f'), desde: base.id, hasta: n.id, etiqueta: '', tipo: tipo === 'error' ? 'incidencia' : 'normal', rango: null });
      }
    });
    seleccionar({ tipo: 'nodo', id: n.id }, true);
    mostrarSiHaceFalta(n.id);
  }
  function mostrarSiHaceFalta(id) {
    const n = nodo(id);
    if (!n) return;
    const m = medidas(n), r = svg.getBoundingClientRect();
    const x1 = n.x * camara.k + camara.x, y1 = n.y * camara.k + camara.y;
    const x2 = x1 + m.w * camara.k, y2 = y1 + m.h * camara.k;
    if (x1 < 20 || y1 < 20 || x2 > r.width - 20 || y2 > r.height - 120) centrarEn(id);
  }
  function conectar(desde, hasta) {
    const a = nodo(desde), b = nodo(hasta);
    const f = { id: nuevoId('f'), desde, hasta, etiqueta: '', tipo: b.tipo === 'error' ? 'incidencia' : 'normal', rango: null };
    editar(() => modelo.flechas.push(f));
    seleccionar({ tipo: 'flecha', id: f.id });
    if (a.tipo === 'decision') { const c = document.getElementById('campo-etiqueta'); if (c) c.focus(); }
  }
  function eliminarSeleccion() {
    if (!sel || SOLO) return;
    if (sel.tipo === 'nodo') {
      const n = nodo(sel.id);
      const conectadas = modelo.flechas.filter((f) => f.desde === n.id || f.hasta === n.id).length;
      editar(() => {
        modelo.nodos = modelo.nodos.filter((x) => x.id !== n.id);
        modelo.flechas = modelo.flechas.filter((f) => f.desde !== n.id && f.hasta !== n.id);
      });
      aviso(`Se borró «${n.titulo}»` + (conectadas ? ` y sus ${conectadas} flecha(s)` : '') + '. Ctrl+Z para deshacer.');
    } else {
      editar(() => { modelo.flechas = modelo.flechas.filter((f) => f.id !== sel.id); });
      aviso('Se borró la flecha (los bloques quedan). Ctrl+Z para deshacer.');
    }
    seleccionar(null);
  }
  function duplicar() {
    if (!sel || sel.tipo !== 'nodo' || SOLO) return;
    const n = clonar(nodo(sel.id));
    n.id = nuevoId('n'); n.x += 30; n.y += 30; n.titulo = n.titulo + ' (copia)';
    editar(() => modelo.nodos.push(n));
    seleccionar({ tipo: 'nodo', id: n.id });
    mostrarSiHaceFalta(n.id);
  }

  // Orden automático por capas (de arriba hacia abajo). Los retornos y
  // rechazos no cuentan, para que un circuito con vueltas se pueda ordenar.
  function ordenar() {
    if (SOLO || !modelo.nodos.length) return;
    editar(() => {
      const ids = modelo.nodos.map((n) => n.id);
      const sal = {}, ent = {};
      ids.forEach((i) => { sal[i] = []; ent[i] = []; });
      modelo.flechas.forEach((f) => {
        if (!sal[f.desde] || !ent[f.hasta] || ['retorno', 'rechazo'].includes(f.tipo) || f.desde === f.hasta) return;
        sal[f.desde].push(f.hasta); ent[f.hasta].push(f.desde);
      });
      // quitar ciclos con un recorrido en profundidad
      const estadoV = {}, aristas = [];
      const visitar = (u) => {
        estadoV[u] = 1;
        sal[u].forEach((v) => { if (estadoV[v] === 1) return; aristas.push([u, v]); if (!estadoV[v]) visitar(v); });
        estadoV[u] = 2;
      };
      const raices = ids.filter((i) => !ent[i].length).sort((a, b) => (nodo(a).tipo === 'inicio' ? -1 : 0) - (nodo(b).tipo === 'inicio' ? -1 : 0));
      raices.concat(ids).forEach((i) => { if (!estadoV[i]) visitar(i); });
      const capaDe = {};
      ids.forEach((i) => { capaDe[i] = 0; });
      for (let it = 0; it < ids.length; it++) {
        let cambio = false;
        aristas.forEach(([u, v]) => { if (capaDe[v] < capaDe[u] + 1) { capaDe[v] = capaDe[u] + 1; cambio = true; } });
        if (!cambio) break;
      }
      const sueltos = ids.filter((i) => !aristas.some(([u, v]) => u === i || v === i) && ['observacion', 'responsable'].includes(nodo(i).tipo));
      const capas = [];
      ids.filter((i) => !sueltos.includes(i)).forEach((i) => { (capas[capaDe[i]] = capas[capaDe[i]] || []).push(i); });
      const posX = {};
      let y = 0, anchoMax = 0;
      capas.forEach((fila, ci) => {
        if (!fila) return;
        if (ci > 0) fila.sort((a, b) => promedio(a) - promedio(b));
        let alto = 0;
        fila.forEach((id, j) => {
          const n = nodo(id);
          n.x = Math.round(((j - (fila.length - 1) / 2) * (W + 50)) / 10) * 10;
          n.y = y;
          posX[id] = n.x;
          alto = Math.max(alto, medidas(n).h);
        });
        anchoMax = Math.max(anchoMax, fila.length * (W + 50));
        y += alto + 70;
      });
      function promedio(id) { const ps = aristas.filter(([, v]) => v === id).map(([u]) => posX[u]).filter((v) => v != null); return ps.length ? ps.reduce((s, v) => s + v, 0) / ps.length : 0; }
      sueltos.forEach((id, j) => { const n = nodo(id); n.x = anchoMax / 2 + 80; n.y = j * 120; });
    });
    ajustar();
  }

  // ---------------------------------------------------------- selección
  function seleccionar(s, enfocarTitulo) {
    sel = s;
    dibujar();
    dibujarPanel();
    if (enfocarTitulo) { const t = document.getElementById('campo-titulo'); if (t) { t.focus(); t.select(); } }
  }

  // ------------------------------------------------------------- panel
  const panel = document.getElementById('panel');
  function h(tag, attrs, ...hijos) {
    const e = document.createElement(tag);
    for (const k in attrs || {}) {
      if (attrs[k] == null || attrs[k] === false) continue;
      if (k === 'class') e.className = attrs[k];
      else if (k === 'text') e.textContent = attrs[k];
      else if (k.startsWith('on')) e.addEventListener(k.slice(2), attrs[k]);
      else if (k === 'value') e.value = attrs[k];
      else e.setAttribute(k, attrs[k] === true ? '' : attrs[k]);
    }
    hijos.flat().forEach((c) => { if (c != null) e.appendChild(typeof c === 'string' ? document.createTextNode(c) : c); });
    return e;
  }
  // Campo de texto que edita el modelo en vivo y deja una sola foto para deshacer.
  function campoTexto(etiqueta, obtener, poner, opciones) {
    opciones = opciones || {};
    const id = opciones.id || 'c' + Math.random().toString(36).slice(2, 8);
    let fotoTomada = false;
    const tag = opciones.largo ? 'textarea' : 'input';
    const inp = h(tag, { id, class: 'input pe-input', value: obtener() || '', rows: opciones.largo ? (opciones.filas || 3) : null,
      placeholder: opciones.ayuda || '', readonly: SOLO || null, maxlength: opciones.largo ? 4000 : 300 });
    inp.addEventListener('focus', () => { fotoTomada = false; });
    inp.addEventListener('input', () => {
      if (SOLO) return;
      if (!fotoTomada) { tomarFoto(); fotoTomada = true; }
      poner(inp.value);
      cambio();
    });
    return h('div', { class: 'pe-campo' }, h('label', { for: id, text: etiqueta }), inp);
  }
  function campoOpciones(etiqueta, opciones, actual, poner, extra) {
    extra = extra || {};
    const id = 's' + Math.random().toString(36).slice(2, 8);
    const s = h('select', { id, class: 'input pe-input', disabled: SOLO || null });
    Object.entries(opciones).forEach(([k, v]) => {
      const o = h('option', { value: k, text: typeof v === 'string' ? v : v.nombre });
      if (extra.deshabilitar && extra.deshabilitar(k)) { o.disabled = true; o.textContent += ' — ' + extra.deshabilitar(k); }
      if (k === actual) o.selected = true;
      s.appendChild(o);
    });
    s.addEventListener('change', () => editar(() => poner(s.value)));
    return h('div', { class: 'pe-campo' }, h('label', { for: id, text: etiqueta }), s,
      extra.ayuda ? h('p', { class: 'pe-ayuda', text: extra.ayuda }) : null);
  }
  function seccion(titulo, ...hijos) {
    return h('details', { class: 'pe-seccion', open: true }, h('summary', { text: titulo }), ...hijos);
  }
  function chipEstado(estado) {
    const c = colorEstado(estado);
    const s = h('span', { class: 'pe-chip', text: (CAT.estados[estado] || {}).nombre || estado });
    s.style.background = c[1]; s.style.color = c[0]; s.style.borderColor = c[0];
    return s;
  }

  function dibujarPanel() {
    if (!panel) return;
    panel.innerHTML = '';
    if (!sel) { panel.appendChild(panelVacio()); return; }
    if (sel.tipo === 'nodo') panel.appendChild(panelNodo(nodo(sel.id)));
    else panel.appendChild(panelFlecha(flecha(sel.id)));
  }
  function panelVacio() {
    return h('div', { class: 'pe-panel-vacio' },
      h('p', { class: 'pe-panel-titulo', text: SOLO ? 'Tocá un bloque para ver su información' : 'Tocá un bloque o una flecha para editarlo' }),
      SOLO ? null : h('ul', { class: 'pe-ayuda-lista' },
        h('li', { text: 'Para agregar un paso, elegí un tipo en la columna de la izquierda. Si hay un bloque seleccionado, el paso nuevo va debajo y queda conectado.' }),
        h('li', { text: 'Para conectar dos bloques, arrastrá el círculo azul (+) de un bloque hasta el otro.' }),
        h('li', { text: 'Para moverte por el gráfico, arrastrá el fondo. Para acercar o alejar, usá la rueda del mouse.' }),
        h('li', { text: 'Atajos: Ctrl+Z deshace · Ctrl+Y rehace · Supr borra · Ctrl+D duplica · Ctrl+S guarda una versión.' })),
      comentariosPanel(''));
  }

  function bloqueFuentes(n) {
    const caja = h('div', { class: 'pe-fuentes', id: 'documentacion' });
    const verificadas = (n.fuentes || []).filter((f) => f.verificada);
    if (!n.fuentes || !n.fuentes.length) caja.appendChild(h('p', { class: 'pe-sin-respaldo', text: 'SIN RESPALDO DOCUMENTAL' }));
    else if (!verificadas.length) caja.appendChild(h('p', { class: 'pe-sin-verificar', text: 'PENDIENTE DE VERIFICACIÓN: hay fuentes, pero ninguna está verificada.' }));
    (n.fuentes || []).forEach((f, i) => {
      const d = f.doc ? doc(f.doc) : null;
      let url = d ? d.url : f.url;
      if (url && f.pagina && /\.pdf/i.test(url) && url.indexOf('#') < 0) url += '#page=' + f.pagina;
      caja.appendChild(h('div', { class: 'pe-fuente' + (f.verificada ? '' : ' pe-fuente--sin') },
        h('p', { class: 'pe-fuente__titulo', text: d ? d.titulo : (f.titulo || f.url) }),
        h('p', { class: 'pe-fuente__meta', text: [d ? d.emisor : f.emisor, d ? d.fecha : f.fecha].filter(Boolean).join(' · ') }),
        h('p', { class: 'pe-fuente__meta', text: [f.punto && ('Apartado: ' + f.punto), f.capitulo && ('Capítulo: ' + f.capitulo), f.pagina && ('Página ' + f.pagina)].filter(Boolean).join(' · ') }),
        f.fragmento ? h('blockquote', { class: 'pe-fuente__frag', text: f.fragmento }) : null,
        h('div', { class: 'pe-fuente__acciones' },
          url ? h('a', { href: url, target: '_blank', rel: 'noopener', class: 'btn btn--sm btn--ghost', text: 'Abrir documento ↗' }) : null,
          h('span', { class: 'pe-chip ' + (f.verificada ? 'pe-chip--ok' : 'pe-chip--pend'), text: f.verificada ? 'Verificada' : 'Sin verificar' }),
          SOLO ? null : h('button', { type: 'button', class: 'btn btn--sm btn--subtle', text: f.verificada ? 'Marcar sin verificar' : 'Marcar verificada', onclick: () => { editar(() => { f.verificada = !f.verificada; reglasEstado(n); }); dibujarPanel(); } }),
          SOLO ? null : h('button', { type: 'button', class: 'btn btn--sm btn--subtle', text: 'Quitar', onclick: () => { editar(() => { n.fuentes.splice(i, 1); reglasEstado(n); }); dibujarPanel(); } }))));
    });
    if (!SOLO) caja.appendChild(formFuente(n));
    return caja;
  }
  function reglasEstado(n) {
    if (n.estado === 'documentado' && !(n.fuentes || []).some((f) => f.verificada)) {
      n.estado = 'pendiente_documentacion';
      aviso('Sin una fuente verificada no puede quedar como «Documentado con fuente oficial». Quedó como pendiente de documentación.', 'error');
    }
  }
  function formFuente(n) {
    const filtro = h('input', { class: 'input pe-input', placeholder: 'Buscar en la biblioteca (circular, decreto, ley…)', type: 'search', 'aria-label': 'Buscar documento' });
    const lista = h('select', { class: 'input pe-input', size: 5, 'aria-label': 'Documento de la biblioteca' });
    const llenar = () => {
      const q = filtro.value.toLowerCase();
      lista.innerHTML = '';
      CAT.documentos.filter((d) => !q || (d.titulo + ' ' + d.emisor).toLowerCase().includes(q)).slice(0, 60)
        .forEach((d) => lista.appendChild(h('option', { value: d.id, text: d.titulo })));
    };
    filtro.addEventListener('input', llenar);
    llenar();
    const punto = h('input', { class: 'input pe-input', placeholder: 'Artículo, punto o apartado (ej.: Punto 10)' });
    const capitulo = h('input', { class: 'input pe-input', placeholder: 'Capítulo (si tiene)' });
    const pagina = h('input', { class: 'input pe-input', placeholder: 'Página del PDF', inputmode: 'numeric' });
    const frag = h('textarea', { class: 'input pe-input', rows: 3, placeholder: 'Fragmento textual que respalda este paso' });
    const url = h('input', { class: 'input pe-input', placeholder: 'O un enlace oficial (https://…) si no está en la biblioteca' });
    const titulo = h('input', { class: 'input pe-input', placeholder: 'Nombre del documento (si usás un enlace)' });
    const verif = h('input', { type: 'checkbox', id: 'fuente-verificada' });
    const agregarF = () => {
      const f = { doc: url.value.trim() ? '' : lista.value, url: url.value.trim(), titulo: titulo.value.trim(), emisor: '', fecha: '',
        punto: punto.value.trim(), capitulo: capitulo.value.trim(), pagina: pagina.value.replace(/\D/g, ''), fragmento: frag.value.trim(), verificada: verif.checked };
      if (!f.doc && !f.url) { aviso('Elegí un documento de la biblioteca o pegá un enlace oficial.', 'error'); return; }
      if (f.url && !/^https?:\/\//.test(f.url)) { aviso('El enlace tiene que empezar con https://', 'error'); return; }
      if (f.url && !f.titulo) { aviso('Poné el nombre del documento del enlace.', 'error'); return; }
      editar(() => { n.fuentes = n.fuentes || []; n.fuentes.push(f); });
      dibujarPanel();
    };
    return h('details', { class: 'pe-agregar-fuente' }, h('summary', { text: '+ Agregar una fuente' }),
      filtro, lista, punto, capitulo, pagina, frag, url, titulo,
      h('label', { class: 'pe-check', for: 'fuente-verificada' }, verif, ' Leí el documento y respalda este paso'),
      h('button', { type: 'button', class: 'btn btn--primary btn--sm', text: 'Agregar fuente', onclick: agregarF }));
  }

  function listaResponsables(n) {
    const caja = h('div', {});
    (n.responsables || []).forEach((r, i) => {
      caja.appendChild(h('div', { class: 'pe-resp' },
        h('span', { class: 'pe-chip', text: CAT.funciones[r.funcion] }),
        h('span', { text: r.quien }),
        r.perfil_timbo ? h('span', { class: 'pe-chip pe-chip--timbo', text: 'Perfil de TIMBÓ' }) : h('span', { class: 'pe-chip', text: 'Área o persona del hospital' }),
        SOLO ? null : h('button', { type: 'button', class: 'btn btn--sm btn--subtle', 'aria-label': 'Quitar responsable', text: '✕', onclick: () => { editar(() => n.responsables.splice(i, 1)); dibujarPanel(); } })));
    });
    if (!SOLO) {
      const funcion = h('select', { class: 'input pe-input', 'aria-label': 'Qué hace' });
      Object.entries(CAT.funciones).forEach(([k, v]) => funcion.appendChild(h('option', { value: k, text: v })));
      const quien = h('input', { class: 'input pe-input', placeholder: 'Área, persona o perfil (ej.: Farmacia, Gestor)', 'aria-label': 'Quién' });
      const perfil = h('input', { type: 'checkbox', id: 'resp-perfil' });
      caja.appendChild(h('div', { class: 'pe-fila' }, funcion, quien));
      caja.appendChild(h('label', { class: 'pe-check', for: 'resp-perfil' }, perfil, ' Es un perfil de TIMBÓ (Gestor, Supervisor, Evaluador…), no un área del hospital'));
      caja.appendChild(h('button', { type: 'button', class: 'btn btn--sm', text: '+ Agregar responsable', onclick: () => {
        if (!quien.value.trim()) { aviso('Escribí quién.', 'error'); return; }
        editar(() => { n.responsables = n.responsables || []; n.responsables.push({ funcion: funcion.value, quien: quien.value.trim(), perfil_timbo: perfil.checked }); });
        dibujarPanel();
      } }));
    }
    return caja;
  }

  function panelNodo(n) {
    const tipo = CAT.tipos[n.tipo];
    const cont = h('div', { class: 'pe-panel-nodo' });
    cont.appendChild(h('div', { class: 'pe-panel-cab' },
      h('span', { class: 'pe-panel-tipo', text: tipo.icono + ' ' + tipo.nombre }), chipEstado(n.estado)));
    cont.appendChild(h('button', { type: 'button', class: 'btn btn--primary pe-btn-doc', text: '📚 CONSULTAR DOCUMENTACIÓN', onclick: () => {
      const d = document.getElementById('documentacion');
      if (d) { d.closest('details').open = true; d.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
    } }));
    if (!SOLO) {
      cont.appendChild(h('div', { class: 'pe-fila pe-acciones' },
        h('button', { type: 'button', class: 'btn btn--sm', text: '⧉ Duplicar', onclick: duplicar }),
        h('button', { type: 'button', class: 'btn btn--sm btn--danger-ghost', text: '🗑 Borrar', onclick: eliminarSeleccion })));
    }
    const datos = [
      campoTexto('Título', () => n.titulo, (v) => { n.titulo = v; }, { id: 'campo-titulo' }),
      SOLO ? null : campoOpciones('Tipo de bloque', Object.fromEntries(Object.entries(CAT.tipos).map(([k, v]) => [k, v.icono + ' ' + v.nombre])), n.tipo, (v) => {
        n.tipo = v;
        if (v === 'documento' && !n.documento) n.documento = { origen: '', completa: '', recibe: '', revisa: '', autoriza: '', registra: '', archiva: '', continua: '' };
        if (v === 'error' && !n.error) n.error = { causa: '', detecta: '', interviene: '', resolucion: '', nueva_autorizacion: false, doc_adicional: false };
        setTimeout(dibujarPanel);
      }),
      campoOpciones('Estado de validación', CAT.estados, n.estado, (v) => { n.estado = v; setTimeout(dibujarPanel); }, {
        deshabilitar: (k) => {
          if (k === 'documentado' && !(n.fuentes || []).some((f) => f.verificada)) return 'necesita una fuente verificada';
          if (k === 'confirmado_equipo' && CLASE === 'oficial') return 'no se usa en el circuito oficial';
          return '';
        },
        ayuda: (CAT.estados[n.estado] || {}).ayuda,
      }),
      campoTexto('Descripción', () => n.descripcion, (v) => { n.descripcion = v; }, { largo: true, ayuda: 'Qué se hace en este paso, en palabras simples' }),
      h('div', { class: 'pe-fila' },
        campoOpciones('Soporte', CAT.soportes, n.soporte, (v) => { n.soporte = v; }),
        campoOpciones('Sistema', CAT.sistemas, n.sistema, (v) => { n.sistema = v; })),
    ];
    cont.appendChild(seccion('Datos', ...datos));
    cont.appendChild(seccion('Responsables',
      listaResponsables(n),
      campoTexto('Sector', () => n.sector, (v) => { n.sector = v; }, { ayuda: 'Sector que hace este paso' })));
    cont.appendChild(seccion('Documentación y referencias', bloqueFuentes(n)));
    const detalle = [
      campoTexto('Documentación necesaria', () => n.documentacion, (v) => { n.documentacion = v; }, { largo: true, filas: 2 }),
      campoTexto('Resultado esperado', () => n.resultado, (v) => { n.resultado = v; }, { largo: true, filas: 2 }),
      campoTexto('Condiciones para continuar', () => n.condiciones, (v) => { n.condiciones = v; }, { largo: true, filas: 2 }),
    ];
    if (n.tipo === 'documento' && n.documento) {
      const nombres = { origen: 'Dónde se origina', completa: 'Quién lo completa', recibe: 'Quién lo recibe', revisa: 'Quién lo revisa', autoriza: 'Quién lo autoriza', registra: 'Dónde se registra', archiva: 'Dónde se archiva', continua: 'Cómo sigue su recorrido' };
      cont.appendChild(seccion('Recorrido del documento',
        h('p', { class: 'pe-ayuda', text: 'Si existe en papel y también en el sistema, cargalos como dos bloques de documento y unilos con una flecha «Digitalización».' }),
        ...Object.keys(nombres).map((k) => campoTexto(nombres[k], () => n.documento[k], (v) => { n.documento[k] = v; }))));
    }
    if (n.tipo === 'error' && n.error) {
      const ent = modelo.flechas.filter((f) => f.hasta === n.id && f.tipo === 'incidencia').map((f) => nodo(f.desde)).filter(Boolean);
      cont.appendChild(seccion('Error o incidencia',
        h('p', { class: ent.length ? 'pe-ayuda' : 'pe-sin-respaldo', text: ent.length ? 'Ocurre en: ' + ent.map((x) => x.titulo).join(', ') : 'Falta indicar en qué paso ocurre: conectá ese paso con este bloque (flecha «Incidencia»).' }),
        campoTexto('Causa', () => n.error.causa, (v) => { n.error.causa = v; }, { largo: true, filas: 2 }),
        campoTexto('Quién lo detecta', () => n.error.detecta, (v) => { n.error.detecta = v; }),
        campoTexto('Quién tiene que intervenir', () => n.error.interviene, (v) => { n.error.interviene = v; }),
        campoTexto('Cómo se resuelve', () => n.error.resolucion, (v) => { n.error.resolucion = v; }, { largo: true, filas: 2 }),
        casilla('Genera una nueva autorización', () => n.error.nueva_autorizacion, (v) => { n.error.nueva_autorizacion = v; }),
        casilla('Requiere documentación adicional', () => n.error.doc_adicional, (v) => { n.error.doc_adicional = v; }),
        h('p', { class: 'pe-ayuda', text: 'Si devuelve el trámite a un paso anterior, conectá este bloque con ese paso y elegí el tipo «Vuelve a un paso anterior».' })));
    }
    cont.appendChild(seccion('Más detalle', ...detalle));
    if (CLASE === 'hospital' && n.correspondencia) cont.appendChild(seccion('Comparación con TIMBÓ', panelCorrespondencia(n)));
    cont.appendChild(seccion('Conexiones', panelConexiones(n)));
    cont.appendChild(seccion('Comentarios', comentariosPanel(n.id)));
    return cont;
  }
  function casilla(etiqueta, obtener, poner) {
    const id = 'k' + Math.random().toString(36).slice(2, 8);
    const c = h('input', { type: 'checkbox', id, disabled: SOLO || null });
    c.checked = !!obtener();
    c.addEventListener('change', () => editar(() => poner(c.checked)));
    return h('label', { class: 'pe-check', for: id }, c, ' ' + etiqueta);
  }
  function panelCorrespondencia(n) {
    const of = D.oficiales || {};
    const slugs = Object.keys(of);
    if (!slugs.length) return h('p', { class: 'pe-ayuda', text: 'Todavía no hay un circuito oficial para comparar.' });
    const c = n.correspondencia;
    if (!c.circuito) c.circuito = slugs[0];
    const pasos = { '': '— Elegí el paso oficial —' };
    ((of[c.circuito] || {}).nodos || []).forEach((x) => { pasos[x.id] = x.titulo; });
    return h('div', {},
      h('p', { class: 'pe-ayuda', text: 'Esto no juzga si está bien o mal: solo registra cómo se relaciona con lo documentado.' }),
      slugs.length > 1 ? campoOpciones('Circuito oficial', Object.fromEntries(slugs.map((s) => [s, of[s].nombre])), c.circuito, (v) => { c.circuito = v; c.nodo = ''; setTimeout(dibujarPanel); }) : null,
      campoOpciones('Paso oficial equivalente', pasos, c.nodo || '', (v) => { c.nodo = v; }),
      campoOpciones('Relación', Object.assign({ '': '— Sin indicar —' }, CAT.relaciones), c.relacion || '', (v) => { c.relacion = v; }),
      campoTexto('Nota (fundamento, implicancias)', () => c.nota, (v) => { c.nota = v; }, { largo: true, filas: 2 }));
  }
  function panelConexiones(n) {
    const sal = modelo.flechas.filter((f) => f.desde === n.id);
    const ent = modelo.flechas.filter((f) => f.hasta === n.id);
    const item = (f, otro, flechaTxt) => h('li', {}, h('button', { type: 'button', class: 'pe-link', text: flechaTxt + ' ' + (otro ? otro.titulo : '(sin bloque)') + (f.etiqueta ? ' — ' + f.etiqueta : ''), onclick: () => seleccionar({ tipo: 'flecha', id: f.id }) }));
    const caja = h('div', {},
      h('p', { class: 'pe-ayuda', text: 'Llegan desde:' }), h('ul', { class: 'pe-lista' }, ent.length ? ent.map((f) => item(f, nodo(f.desde), '←')) : h('li', { text: 'Ninguna' })),
      h('p', { class: 'pe-ayuda', text: 'Salen hacia:' }), h('ul', { class: 'pe-lista' }, sal.length ? sal.map((f) => item(f, nodo(f.hasta), '→')) : h('li', { text: 'Ninguna' })));
    if (!SOLO) {
      const destino = h('select', { class: 'input pe-input', 'aria-label': 'Conectar con' });
      destino.appendChild(h('option', { value: '', text: '— Conectar con… —' }));
      modelo.nodos.filter((x) => x.id !== n.id).forEach((x) => destino.appendChild(h('option', { value: x.id, text: x.titulo })));
      caja.appendChild(h('div', { class: 'pe-fila' }, destino, h('button', { type: 'button', class: 'btn btn--sm', text: 'Conectar', onclick: () => { if (destino.value) conectar(n.id, destino.value); } })));
    }
    return caja;
  }
  function panelFlecha(f) {
    const a = nodo(f.desde), b = nodo(f.hasta);
    const opcionesNodos = Object.fromEntries(modelo.nodos.map((x) => [x.id, x.titulo]));
    const rangos = { '': '— Sin rango de montos —' };
    D.rangos.forEach((r) => { rangos[r.id] = r.nombre + ' (' + textoRango(r) + ')' + (r.estado !== 'verificado' ? ' — sin validar' : ''); });
    const cont = h('div', { class: 'pe-panel-nodo' },
      h('div', { class: 'pe-panel-cab' }, h('span', { class: 'pe-panel-tipo', text: '➜ Flecha' })),
      h('p', { class: 'pe-panel-titulo', text: (a ? a.titulo : '?') + ' → ' + (b ? b.titulo : '?') }));
    if (!SOLO) {
      cont.appendChild(h('div', { class: 'pe-fila pe-acciones' },
        h('button', { type: 'button', class: 'btn btn--sm', text: '⇄ Invertir sentido', onclick: () => { editar(() => { const t = f.desde; f.desde = f.hasta; f.hasta = t; }); dibujarPanel(); } }),
        h('button', { type: 'button', class: 'btn btn--sm btn--danger-ghost', text: '🗑 Borrar flecha', onclick: eliminarSeleccion })));
    }
    const rg = f.rango != null ? rango(f.rango) : null;
    cont.appendChild(seccion('Datos de la flecha',
      campoTexto('Condición o etiqueta', () => f.etiqueta, (v) => { f.etiqueta = v; }, { id: 'campo-etiqueta', ayuda: 'Ej.: Sí · No · Falta documentación' }),
      campoOpciones('Tipo de camino', CAT.tipos_flecha, f.tipo, (v) => { f.tipo = v; }),
      campoOpciones('Rango de montos', rangos, f.rango == null ? '' : String(f.rango), (v) => { f.rango = v ? Number(v) : null; setTimeout(dibujarPanel); }),
      rg ? h('div', { class: 'pe-fuente' },
        h('p', { class: 'pe-fuente__titulo', text: rg.nombre }),
        h('p', { class: 'pe-fuente__meta', text: textoRango(rg) + ' · ' + rg.moneda + (rg.vigencia_desde ? ' · vigente desde ' + rg.vigencia_desde : '') }),
        rg.autorizacion ? h('p', { text: 'Autorización: ' + rg.autorizacion }) : null,
        h('p', { class: 'pe-fuente__meta', text: rg.fuente_doc ? ('Fuente: ' + ((doc(rg.fuente_doc) || {}).titulo || rg.fuente_doc) + (rg.fuente_punto ? ' · ' + rg.fuente_punto : '')) : 'SIN RESPALDO DOCUMENTAL' }),
        h('span', { class: 'pe-chip ' + (rg.estado === 'verificado' ? 'pe-chip--ok' : 'pe-chip--pend'), text: rg.estado === 'verificado' ? 'Verificado' : 'Pendiente de validación' })) : null,
      campoOpciones('Desde', opcionesNodos, f.desde, (v) => { f.desde = v; setTimeout(dibujarPanel); }),
      campoOpciones('Hasta', opcionesNodos, f.hasta, (v) => { f.hasta = v; setTimeout(dibujarPanel); })));
    cont.appendChild(seccion('Comentarios', comentariosPanel(f.id)));
    return cont;
  }

  function comentariosPanel(elemento) {
    const caja = h('div', { class: 'pe-comentarios' });
    const lista = comentariosDe(elemento);
    if (elemento === '') caja.appendChild(h('p', { class: 'pe-panel-titulo', text: 'Comentarios generales del circuito' }));
    if (!lista.length) caja.appendChild(h('p', { class: 'pe-ayuda', text: 'Sin comentarios.' }));
    lista.forEach((c) => {
      caja.appendChild(h('div', { class: 'pe-comentario' + (c.resuelto ? ' es-resuelto' : '') },
        h('span', { class: 'pe-chip', text: CAT.tipos_comentario[c.tipo] || c.tipo }),
        h('p', { text: c.texto }),
        h('div', { class: 'pe-fila' },
          h('small', { text: c.fecha ? new Date(c.fecha).toLocaleString('es-AR') : '' }),
          SOLO ? null : h('button', { type: 'button', class: 'btn btn--sm btn--subtle', text: c.resuelto ? 'Reabrir' : 'Marcar resuelto', onclick: async () => {
            try {
              const j = await pedir(D.urls.resolver.replace('/0/', '/' + c.id + '/'), {});
              c.resuelto = j.resuelto; dibujar(); dibujarPanel();
            } catch (e) { aviso(e.message, 'error'); }
          } }))));
    });
    if (!SOLO) {
      const tipo = h('select', { class: 'input pe-input', 'aria-label': 'Tipo de comentario' });
      Object.entries(CAT.tipos_comentario).forEach(([k, v]) => tipo.appendChild(h('option', { value: k, text: v })));
      const txt = h('textarea', { class: 'input pe-input', rows: 2, placeholder: 'Aclaración, duda, pregunta para Santa Fe…', 'aria-label': 'Comentario' });
      caja.appendChild(tipo); caja.appendChild(txt);
      caja.appendChild(h('button', { type: 'button', class: 'btn btn--sm', text: 'Agregar comentario', onclick: async () => {
        if (!txt.value.trim()) return;
        try {
          const j = await pedir(D.urls.comentario, { elemento, tipo: tipo.value, texto: txt.value });
          comentarios.push(j.comentario); dibujar(); dibujarPanel();
          aviso('Comentario guardado. No cambia el procedimiento.');
        } catch (e) { aviso(e.message, 'error'); }
      } }));
    }
    return caja;
  }

  // ------------------------------------------------------------- revisión
  function dibujarRevision() {
    const lista = document.getElementById('revision-lista');
    const cuenta = document.getElementById('revision-cuenta');
    if (!lista) return;
    const errores = revision.filter((o) => o.nivel === 'error').length;
    const avisos = revision.filter((o) => o.nivel === 'aviso').length;
    if (cuenta) { cuenta.textContent = errores + avisos ? `${errores} ✕ · ${avisos} !` : '0'; cuenta.dataset.hay = errores ? 'error' : (avisos ? 'aviso' : ''); }
    lista.innerHTML = '';
    if (!revision.length) {
      lista.appendChild(h('li', { class: 'pe-rev pe-rev--info', text: 'La revisión no encontró problemas. Eso no quiere decir que el circuito esté completo: solo que no hay huecos que se puedan detectar automáticamente.' }));
      return;
    }
    const nombres = { error: 'Problema', aviso: 'Revisar', info: 'Pendiente' };
    revision.forEach((o) => {
      lista.appendChild(h('li', { class: 'pe-rev pe-rev--' + o.nivel },
        h('button', { type: 'button', class: 'pe-link', onclick: () => {
          if (!o.elemento) return;
          if (nodo(o.elemento)) { seleccionar({ tipo: 'nodo', id: o.elemento }); centrarEn(o.elemento); } else if (flecha(o.elemento)) { seleccionar({ tipo: 'flecha', id: o.elemento }); centrarEn(flecha(o.elemento).desde); }
        } }, h('strong', { text: nombres[o.nivel] + ': ' }), o.mensaje)));
    });
  }

  // ------------------------------------------------------------- exportar
  function svgParaExportar() {
    const b = limites();
    const copia = svg.cloneNode(true);
    copia.querySelectorAll('.pe-asa').forEach((x) => x.remove());
    const fondo = copia.querySelector('[data-fondo]');
    if (fondo) { fondo.setAttribute('fill', '#ffffff'); fondo.removeAttribute('transform'); fondo.setAttribute('x', b.x); fondo.setAttribute('y', b.y - 60); fondo.setAttribute('width', b.w); fondo.setAttribute('height', b.h + 60); }
    const mundo = copia.querySelector(':scope > g');
    if (mundo) mundo.removeAttribute('transform');
    copia.setAttribute('xmlns', NS);
    copia.setAttribute('viewBox', `${b.x} ${b.y - 60} ${b.w} ${b.h + 60}`);
    copia.setAttribute('width', b.w);
    copia.setAttribute('height', b.h + 60);
    const t = el('text', { x: b.x + 20, y: b.y - 28, 'font-size': 20, 'font-weight': 700, fill: '#1c222b', 'font-family': 'Segoe UI, system-ui, sans-serif' }, copia);
    t.textContent = D.circuito.nombre + (D.version ? ` (versión ${D.version})` : '');
    return { texto: new XMLSerializer().serializeToString(copia), w: b.w, h: b.h + 60 };
  }
  function descargar(blob, nombre) {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = nombre;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1500);
  }
  function exportarSvg() { const s = svgParaExportar(); descargar(new Blob([s.texto], { type: 'image/svg+xml' }), D.circuito.slug + '.svg'); }
  function exportarPng() {
    const s = svgParaExportar();
    const img = new Image();
    img.onload = () => {
      const escala = Math.min(2, 8000 / Math.max(s.w, s.h));
      const c = document.createElement('canvas');
      c.width = Math.round(s.w * escala); c.height = Math.round(s.h * escala);
      const ctx = c.getContext('2d');
      ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, c.width, c.height);
      ctx.drawImage(img, 0, 0, c.width, c.height);
      c.toBlob((b) => b ? descargar(b, D.circuito.slug + '.png') : aviso('No se pudo generar la imagen.', 'error'), 'image/png');
    };
    img.onerror = () => aviso('No se pudo generar la imagen.', 'error');
    img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(s.texto);
  }

  // ------------------------------------------------------------- versiones
  const dialogo = document.getElementById('dialogo-version');
  function abrirVersion() {
    if (SOLO || !dialogo) return;
    dialogo.hidden = false;
    const m = document.getElementById('version-motivo');
    m.value = ''; m.focus();
  }
  async function confirmarVersion() {
    const motivo = document.getElementById('version-motivo').value;
    const importante = document.getElementById('version-importante').checked;
    clearTimeout(temporizador);
    try {
      estadoGuardado('guardando');
      const j = await pedir(D.urls.version, { contenido: modelo, motivo, importante });
      sucio = false;
      aplicarRespuesta(j);
      estadoGuardado('ok');
      dialogo.hidden = true;
      aviso(j.sin_cambios ? 'No había cambios desde la última versión.' : `Versión ${j.numero} guardada (${j.cambios} cambio${j.cambios === 1 ? '' : 's'}).`);
    } catch (e) { estadoGuardado('error', e.message); aviso(e.message, 'error'); }
  }

  // ------------------------------------------------------------- barra
  function actualizarBotones() {
    const d = document.querySelector('[data-accion="deshacer"]'), r = document.querySelector('[data-accion="rehacer"]');
    if (d) d.disabled = !pasado.length;
    if (r) r.disabled = !futuro.length;
    document.querySelectorAll('[data-accion="vista"]').forEach((b) => b.setAttribute('aria-pressed', b.dataset.valor === vista ? 'true' : 'false'));
  }
  raiz.addEventListener('click', (ev) => {
    const b = ev.target.closest('[data-accion]');
    if (!b) return;
    const a = b.dataset.accion;
    if (a === 'agregar') agregar(b.dataset.tipo);
    else if (a === 'deshacer') deshacer();
    else if (a === 'rehacer') rehacer();
    else if (a === 'zoom-mas') zoom(1.2);
    else if (a === 'zoom-menos') zoom(1 / 1.2);
    else if (a === 'ajustar') ajustar();
    else if (a === 'ordenar') ordenar();
    else if (a === 'vista') { vista = b.dataset.valor; guardarPref('vista', vista); dibujar(); }
    else if (a === 'pantalla') {
      if (document.fullscreenElement) document.exitFullscreen(); else if (raiz.requestFullscreen) raiz.requestFullscreen().catch(() => aviso('El navegador no permitió la pantalla completa.', 'error'));
    } else if (a === 'version') abrirVersion();
    else if (a === 'version-ok') confirmarVersion();
    else if (a === 'version-cancelar') dialogo.hidden = true;
    else if (a === 'svg') exportarSvg();
    else if (a === 'png') exportarPng();
    else if (a === 'revision') { const p = document.getElementById('revision'); p.hidden = !p.hidden; }
    else if (a === 'guardar-ya') { clearTimeout(temporizador); guardarBorrador(); }
  });
  document.addEventListener('fullscreenchange', () => setTimeout(() => { raiz.style.height = document.fullscreenElement ? '' : raiz.style.height; acomodarAlto(); aplicarCamara(); }, 50));
  document.addEventListener('keydown', (ev) => {
    const enCampo = ev.target.closest && ev.target.closest('input, textarea, select, [contenteditable]');
    const ctrl = ev.ctrlKey || ev.metaKey;
    if (ctrl && ev.key.toLowerCase() === 's') { ev.preventDefault(); abrirVersion(); return; }
    if (dialogo && !dialogo.hidden) {
      if (ev.key === 'Escape') dialogo.hidden = true;
      if (ev.key === 'Enter' && ctrl) confirmarVersion();
      return;
    }
    if (enCampo) return;
    if (ctrl && ev.key.toLowerCase() === 'z' && !ev.shiftKey) { ev.preventDefault(); deshacer(); return; }
    if (ctrl && (ev.key.toLowerCase() === 'y' || (ev.key.toLowerCase() === 'z' && ev.shiftKey))) { ev.preventDefault(); rehacer(); return; }
    if (ctrl && ev.key.toLowerCase() === 'd') { ev.preventDefault(); duplicar(); return; }
    if (ev.key === 'Delete' || ev.key === 'Backspace') { if (sel) { ev.preventDefault(); eliminarSeleccion(); } return; }
    if (ev.key === 'Escape') { seleccionar(null); return; }
    if (ev.key === '+' || ev.key === '=') { zoom(1.2); return; }
    if (ev.key === '-') { zoom(1 / 1.2); return; }
    if (ctrl || ev.altKey) return;
    const rapido = { a: 'actividad', d: 'decision', e: 'etapa', o: 'documento', x: 'error', p: 'pendiente', i: 'inicio', f: 'fin', u: 'autorizacion', v: 'verificacion', n: 'observacion', c: 'condicion', r: 'responsable', j: 'excepcion' }[ev.key.toLowerCase()];
    if (rapido && !SOLO) { ev.preventDefault(); agregar(rapido); }
  });

  // --------------------------------------------------------------- inicio
  const leyenda = document.querySelector('.pe-leyenda[data-recordar]');
  if (leyenda) {
    leyenda.open = leerPref('leyenda', 'cerrada') === 'abierta';
    leyenda.addEventListener('toggle', () => guardarPref('leyenda', leyenda.open ? 'abierta' : 'cerrada'));
  }
  prepararLienzo();
  dibujar();
  dibujarPanel();
  dibujarRevision();
  // En el informe el gráfico ocupa todo el ancho y crece hacia abajo (para imprimir).
  function modoInforme() {
    const b = limites();
    capa.mundo.removeAttribute('transform');
    capa.fondo.removeAttribute('transform');
    capa.fondo.setAttribute('fill', '#ffffff');
    svg.setAttribute('viewBox', `${b.x} ${b.y} ${b.w} ${b.h}`);
    svg.style.height = Math.round(svg.getBoundingClientRect().width * b.h / b.w) + 'px';
  }
  acomodarAlto();
  requestAnimationFrame(() => { if (raiz.classList.contains('pe-editor--informe')) modoInforme(); else ajustarAncho(); });
  window.addEventListener('resize', () => { if (raiz.classList.contains('pe-editor--informe')) { modoInforme(); return; } acomodarAlto(); aplicarCamara(); });
  if (!SOLO) estadoGuardado('ok');
})();
