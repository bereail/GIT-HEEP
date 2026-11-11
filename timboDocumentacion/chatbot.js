/*
 * Asistente TIMBÓ — chatbot de consulta sin conexión.
 * Busca la respuesta dentro del contenido de la propia guía (no usa internet
 * ni inteligencia artificial) y enlaza a la sección correspondiente.
 */
(function () {
  'use strict';

  var STOP = ('a al algo algun alguna como con cual cuales cuando de del donde el ella en entre es esa ese esta este esto hay la las le les lo los me mi mis muy necesito no o para pero por puedo que quiero se si sin sobre su sus te tengo tu un una uno unos y ya hago hacer hace debo tiene tienen puede pueden ser son esta estan').split(' ');

  // Sinónimos: cada grupo se reduce a su primera palabra.
  var SYN = [
    ['subir', 'subo', 'adjunto', 'adjuntar', 'cargar', 'agregar', 'anexar', 'archivo'],
    ['pase', 'envio', 'mando', 'enviar', 'mandar', 'remitir', 'derivar', 'girar'],
    ['subsanar', 'corrijo', 'corregir', 'rectificar', 'arreglar', 'error', 'equivoque', 'equivocado', 'equivocada', 'equivocacion', 'mal'],
    ['eliminar', 'borro', 'borrar', 'quitar', 'sacar'],
    ['contrasena', 'clave', 'password', 'pass'],
    ['ingresar', 'entro', 'ingreso', 'entrar', 'login', 'acceder', 'acceso', 'loguear', 'sesion'],
    ['caratula', 'caratulacion', 'caratular', 'abrir', 'iniciar', 'nuevo', 'crear'],
    ['expediente', 'ee', 'expedientes'],
    ['buscar', 'busco', 'consulto', 'encuentro', 'consultar', 'consulta', 'encontrar', 'localizar', 'ubicar'],
    ['firma', 'firmar', 'firmante', 'firmantes', 'firmo'],
    ['token', 'dispositivo', 'pendrive'],
    ['vista', 'visualizacion', 'visualizar', 'ver', 'mirar'],
    ['asignar', 'asigno', 'tomo', 'asignado', 'asignarme', 'tomar', 'todos'],
    ['guarda', 'espera', 'pausa', 'temporal'],
    ['resolucion', 'resoluciones', 'aar', 'acto', 'actos'],
    ['atencion', 'av', 'ciudadano', 'ciudadania', 'vecino'],
    ['documento', 'do', 'nota', 'documentos', 'ddoo'],
    ['comunicacion', 'comunicaciones', 'notificacion', 'mensaje'],
    ['oficina', 'oficinas', 'codigo', 'organigrama', 'destino'],
    ['menu', 'opciones', 'modulos', 'modulo', 'aparece', 'veo'],
    ['seguridad', 'phishing', 'virus', 'hacker', 'estafa'],
    ['soporte', 'ayuda', 'contacto', 'telefono', 'mail', 'correo', 'whatsapp'],
    ['incorporar', 'incorporado', 'incorporados'],
    ['providencia', 'comentario'],
    ['protocolizar', 'numerar', 'numero', 'numeracion']
  ];
  var SYNMAP = {};
  SYN.forEach(function (g) { g.forEach(function (w) { SYNMAP[w] = g[0]; }); });

  function norm(s) {
    return (s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9ñ\s]/g, ' ');
  }
  function stem(w) {
    if (SYNMAP[w]) return SYNMAP[w];
    var x = w.replace(/(aciones|acion|amiento|mente|ando|iendo|ados|adas|ido|ida|ar|er|ir|es|s)$/, '');
    if (x.length < 3) x = w;
    return SYNMAP[x] || x;
  }
  function tokens(s) {
    return norm(s).split(/\s+/).filter(function (w) { return w && w.length > 1 && STOP.indexOf(w) < 0; }).map(stem);
  }

  // ---------- Índice a partir del contenido de la página ----------
  var chunks = [];
  function slug(t) { return 'cb-' + norm(t).trim().replace(/\s+/g, '-').slice(0, 40); }

  function buildIndex() {
    var secs = document.querySelectorAll('main section, .wrap section');
    secs.forEach(function (sec) {
      var h2 = sec.querySelector('h2');
      var secTitle = h2 ? h2.textContent.replace(/\s+/g, ' ').replace(/\s*(CONFIRMADO|NO VERIFICADO|RECOMENDACIÓN)\s*/g, ' ').trim() : '';
      var cur = { id: sec.id, title: secTitle, text: '', parts: [] };
      var push = function () { if (cur.text.trim()) chunks.push(cur); };
      Array.prototype.forEach.call(sec.children, function (el) {
        if (el.tagName === 'H3') {
          push();
          if (!el.id) el.id = slug(el.textContent);
          cur = { id: el.id, title: secTitle.replace(/^\d+\.\s*/, '') + ' › ' + el.textContent.replace(/\s*(CONFIRMADO|NO VERIFICADO|RECOMENDACIÓN)\s*/g, ' ').trim(), text: '', parts: [] };
        } else if (el.tagName !== 'H2') {
          var t = el.innerText || el.textContent || '';
          cur.text += ' ' + t;
          t.split(/\n+/).forEach(function (p) { p = p.trim(); if (p.length > 3) cur.parts.push(p); });
        }
      });
      push();
    });
    // TF-IDF
    var df = {};
    chunks.forEach(function (c) {
      c.tf = {}; c.titleTok = tokens(c.title);
      var tk = tokens(c.text).concat(c.titleTok, c.titleTok);
      tk.forEach(function (w) { c.tf[w] = (c.tf[w] || 0) + 1; });
      c.len = tk.length || 1;
      Object.keys(c.tf).forEach(function (w) { df[w] = (df[w] || 0) + 1; });
    });
    var N = chunks.length;
    chunks.forEach(function (c) {
      c.idf = function (w) { return Math.log(1 + N / (df[w] || N)); };
    });
    buildIndex.df = df; buildIndex.N = N;
  }

  function score(c, q) {
    var s = 0, N = buildIndex.N, df = buildIndex.df;
    q.forEach(function (w) {
      var f = c.tf[w];
      if (!f) return;
      var idf = Math.log(1 + N / df[w]);
      s += idf * (f * 2.2) / (f + 1.2 * (0.25 + 0.75 * c.len / 120));
      if (c.titleTok.indexOf(w) >= 0) s += idf * 3;
    });
    return s;
  }

  function excerpt(c, q) {
    var ranked = c.parts.map(function (p, i) {
      var tk = tokens(p), hit = 0;
      q.forEach(function (w) { if (tk.indexOf(w) >= 0) hit++; });
      return { p: p, i: i, hit: hit };
    }).filter(function (x) { return x.hit > 0; })
      .sort(function (a, b) { return b.hit - a.hit || a.i - b.i; }).slice(0, 4)
      .sort(function (a, b) { return a.i - b.i; });
    if (!ranked.length) ranked = c.parts.slice(0, 3).map(function (p) { return { p: p }; });
    return ranked.map(function (x) { return x.p.length > 320 ? x.p.slice(0, 317) + '…' : x.p; });
  }

  function answer(qText) {
    var q = tokens(qText);
    if (!q.length) return null;
    var res = chunks.map(function (c) { return { c: c, s: score(c, q) }; })
      .filter(function (r) { return r.s > 0; })
      .sort(function (a, b) { return b.s - a.s; });
    if (!res.length || res[0].s < 1.2) return { none: true };
    return { best: res[0].c, q: q, more: res.slice(1, 4).map(function (r) { return r.c; }) };
  }

  // ---------- Interfaz ----------
  var css = '' +
    '#cb-btn{position:fixed;right:18px;bottom:18px;z-index:9999;border:none;border-radius:999px;padding:13px 18px;font:600 15px/1 "Segoe UI",system-ui,sans-serif;color:#fff;background:linear-gradient(90deg,#5b3f99,#d6245e 60%,#f07a2a);box-shadow:0 6px 20px rgba(91,63,153,.35);cursor:pointer;display:flex;gap:8px;align-items:center}' +
    '#cb-btn:hover{filter:brightness(1.06)}' +
    '#cb-panel{position:fixed;right:18px;bottom:78px;z-index:9999;width:380px;max-width:calc(100vw - 24px);height:560px;max-height:calc(100vh - 110px);background:#fff;border:1px solid #e3e5ec;border-radius:16px;box-shadow:0 18px 50px rgba(20,20,40,.22);display:none;flex-direction:column;overflow:hidden;font:15px/1.5 "Segoe UI",system-ui,sans-serif;color:#1f2330}' +
    '#cb-panel.open{display:flex}' +
    '#cb-head{padding:12px 16px;background:linear-gradient(90deg,#5b3f99,#d6245e 60%,#f07a2a);color:#fff;display:flex;justify-content:space-between;align-items:center}' +
    '#cb-head b{font-size:15px}#cb-head small{display:block;opacity:.9;font-size:11.5px}' +
    '#cb-x{background:rgba(255,255,255,.2);border:none;color:#fff;border-radius:8px;width:30px;height:30px;font-size:18px;cursor:pointer}' +
    '#cb-log{flex:1;overflow-y:auto;padding:14px;background:#f7f7fa}' +
    '.cb-m{margin:0 0 10px;max-width:92%;padding:9px 12px;border-radius:12px;word-wrap:break-word}' +
    '.cb-bot{background:#fff;border:1px solid #e3e5ec;border-top-left-radius:4px}' +
    '.cb-user{background:#5b3f99;color:#fff;margin-left:auto;border-top-right-radius:4px}' +
    '.cb-bot p{margin:4px 0}.cb-bot ul{margin:4px 0;padding-left:18px}.cb-bot li{margin:2px 0}' +
    '.cb-bot a{color:#d6245e;font-weight:600}' +
    '.cb-t{font-weight:700;color:#5b3f99;margin-bottom:4px}' +
    '.cb-more{font-size:13px;color:#5d6475;margin-top:6px}.cb-more a{font-weight:500}' +
    '.cb-sug{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0 4px}' +
    '.cb-sug button{border:1px solid #d9dbe6;background:#fff;border-radius:999px;padding:5px 10px;font:13px "Segoe UI",system-ui,sans-serif;cursor:pointer;color:#1f2330}' +
    '.cb-sug button:hover{border-color:#d6245e;color:#d6245e}' +
    '#cb-form{display:flex;gap:8px;padding:10px;border-top:1px solid #e3e5ec;background:#fff}' +
    '#cb-in{flex:1;border:1px solid #d9dbe6;border-radius:10px;padding:9px 12px;font:15px "Segoe UI",system-ui,sans-serif}' +
    '#cb-in:focus{outline:2px solid #d6245e33;border-color:#d6245e}' +
    '#cb-send{border:none;border-radius:10px;padding:0 14px;background:#d6245e;color:#fff;font-weight:600;cursor:pointer}' +
    '#cb-note{font-size:11px;color:#8a90a0;padding:0 12px 8px;background:#fff}' +
    '.cb-flash{animation:cbflash 1.6s ease}' +
    '@keyframes cbflash{0%,40%{box-shadow:0 0 0 4px #d6245e55}100%{box-shadow:none}}' +
    '@media (max-width:520px){#cb-panel{right:8px;left:8px;width:auto;bottom:70px;height:calc(100vh - 90px)}#cb-btn span{display:none}}' +
    '@media print{#cb-btn,#cb-panel{display:none!important}}';

  function el(tag, attrs, html) {
    var e = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    if (html != null) e.innerHTML = html;
    return e;
  }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }

  var log, input, cfg;

  function addMsg(html, who) {
    var m = el('div', { 'class': 'cb-m ' + (who === 'user' ? 'cb-user' : 'cb-bot') }, html);
    log.appendChild(m);
    log.scrollTop = log.scrollHeight;
    return m;
  }

  function suggestions(list) {
    var box = el('div', { 'class': 'cb-sug' });
    list.forEach(function (s) {
      var b = el('button', { type: 'button' }, esc(s));
      b.addEventListener('click', function () { ask(s); });
      box.appendChild(b);
    });
    return box;
  }

  function link(c, label) {
    return '<a href="#' + esc(c.id) + '" data-cb-go="' + esc(c.id) + '">' + esc(label || c.title) + '</a>';
  }

  function ask(text) {
    text = (text || '').trim();
    if (!text) return;
    addMsg(esc(text), 'user');
    var n = norm(text).trim();
    if (/^(hola|buen(os|as)? (dias|tardes|noches)|buenas)\b/.test(n) && n.split(/\s+/).length <= 3) {
      addMsg('<p>¡Hola! Escribí tu pregunta con tus palabras, por ejemplo: <em>“¿cómo envío un expediente a otra oficina?”</em></p>').appendChild(suggestions(cfg.suggestions));
      return;
    }
    if (/^(gracias|muchas gracias|genial|perfecto|listo)\b/.test(n)) {
      addMsg('<p>¡De nada! Si tenés otra duda, preguntame.</p>');
      return;
    }
    var r = answer(text);
    if (!r || r.none) {
      var m = addMsg('<p>No encontré eso en esta guía. 😕</p><p>Probá con otras palabras (por ejemplo “subir archivo”, “pase”, “firma”, “vista”) o consultá a tu referente. También podés ver ' +
        (document.getElementById(cfg.helpId) ? '<a href="#' + cfg.helpId + '" data-cb-go="' + cfg.helpId + '">los contactos de ayuda</a>' : 'los contactos de ayuda') + '.</p>');
      m.appendChild(suggestions(cfg.suggestions.slice(0, 4)));
      return;
    }
    var ex = excerpt(r.best, r.q);
    var html = '<div class="cb-t">' + esc(r.best.title.replace(/^\d+\.\s*/, '')) + '</div><ul>' +
      ex.map(function (p) { return '<li>' + esc(p) + '</li>'; }).join('') + '</ul>' +
      '<p>👉 ' + link(r.best, 'Ver la explicación completa') + '</p>';
    if (r.more.length) {
      html += '<div class="cb-more">También puede servirte: ' + r.more.map(function (c) { return link(c, c.title.replace(/^\d+\.\s*/, '')); }).join(' · ') + '</div>';
    }
    addMsg(html);
  }

  function go(id) {
    var t = document.getElementById(id);
    if (!t) return;
    t.scrollIntoView({ behavior: 'smooth', block: 'start' });
    t.classList.remove('cb-flash'); void t.offsetWidth; t.classList.add('cb-flash');
    if (window.innerWidth < 700) document.getElementById('cb-panel').classList.remove('open');
  }

  function init() {
    cfg = window.CHATBOT_CONFIG || {};
    cfg.suggestions = cfg.suggestions || ['¿Cómo entro a TIMBÓ?', '¿Cómo envío un expediente?', 'No veo el menú'];
    cfg.helpId = cfg.helpId || 'ayuda';
    buildIndex();

    var st = el('style', null, css); document.head.appendChild(st);
    var btn = el('button', { id: 'cb-btn', type: 'button', 'aria-label': 'Abrir asistente', 'aria-controls': 'cb-panel' }, '💬 <span>Preguntale al asistente</span>');
    var panel = el('div', { id: 'cb-panel', role: 'dialog', 'aria-label': 'Asistente TIMBÓ' });
    panel.innerHTML = '<div id="cb-head"><div><b>Asistente TIMBÓ</b><small>' + esc(cfg.subtitle || 'Respondo con el contenido de esta guía') + '</small></div><button id="cb-x" type="button" aria-label="Cerrar">×</button></div>' +
      '<div id="cb-log" aria-live="polite"></div>' +
      '<form id="cb-form" autocomplete="off"><input id="cb-in" type="text" placeholder="Escribí tu pregunta…" aria-label="Tu pregunta"><button id="cb-send" type="submit">Enviar</button></form>' +
      '<div id="cb-note">Funciona sin internet: busca en esta guía. No es inteligencia artificial y no inventa respuestas.</div>';
    document.body.appendChild(btn); document.body.appendChild(panel);
    log = panel.querySelector('#cb-log'); input = panel.querySelector('#cb-in');

    addMsg('<p>' + (cfg.welcome || '¡Hola! Soy el asistente de la guía. Preguntame cómo hacer algo en TIMBÓ y te llevo a la parte de la guía que lo explica.') + '</p>').appendChild(suggestions(cfg.suggestions));

    btn.addEventListener('click', function () {
      panel.classList.toggle('open');
      if (panel.classList.contains('open')) setTimeout(function () { input.focus(); }, 50);
    });
    panel.querySelector('#cb-x').addEventListener('click', function () { panel.classList.remove('open'); btn.focus(); });
    panel.querySelector('#cb-form').addEventListener('submit', function (e) { e.preventDefault(); var v = input.value; input.value = ''; ask(v); });
    log.addEventListener('click', function (e) {
      var a = e.target.closest('[data-cb-go]');
      if (a) { e.preventDefault(); go(a.getAttribute('data-cb-go')); }
    });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') panel.classList.remove('open'); });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
