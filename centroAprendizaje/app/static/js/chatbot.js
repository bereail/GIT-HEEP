// chatbot.js — asistente de preguntas, 100% local (sin IA externa, sin
// costo). Es la misma idea que timbo-capacitacion/assets/js/chatbot.js, pero
// ahora el índice vive en el servidor (una base de datos por tema) en vez de
// un archivo content.js fijo, así que la pregunta se manda por fetch en vez
// de buscarse en un índice ya cargado en el navegador.
//
// Para no saturar: cada respuesta es corta, y lo demás se ofrece como
// botones (sugerencias, "¿Te referís a...?", "También te puede servir") que
// se tocan en vez de tener que escribir.

function e(texto) {
  const div = document.createElement('div');
  div.textContent = texto == null ? '' : String(texto);
  return div.innerHTML;
}

export function initChatbot({ temaSlug, nombreTema }) {
  const SALUDO = `Hola 👋 Soy el asistente de ${nombreTema}. Escribí tu duda con tus palabras, o tocá una de estas:`;
  const SIN_RESULTADOS = 'No encontré una respuesta para eso. Probá con otras palabras, tocá una de estas opciones o dejanos la consulta.';
  const QUISO_DECIR = 'No estoy seguro de haber entendido. ¿Te referís a alguna de estas?';
  const urlProblemas = `/temas/${temaSlug}/problemas`;
  const urlConsulta = `/temas/${temaSlug}/consultas/nueva`;
  let ultimaPregunta = '';
  // La conversación se guarda por pestaña y por tema: si tocás un link a una
  // lección y volvés, sigue ahí. Si el navegador no deja guardar, no pasa nada.
  const CLAVE_HISTORIAL = `chatbot:${temaSlug}`;

  document.body.insertAdjacentHTML(
    'beforeend',
    `
    <button type="button" class="chatbot-fab" id="chatbot-fab" aria-haspopup="dialog" aria-expanded="false" aria-controls="chatbot-panel">
      <span class="chatbot-fab__icon" aria-hidden="true">💬</span>
      <span class="chatbot-fab__label">¿Tenés una duda?</span>
    </button>
    <section class="chatbot-panel" id="chatbot-panel" role="dialog" aria-label="Asistente de preguntas" aria-hidden="true">
      <header class="chatbot-panel__header">
        <span class="chatbot-panel__title">💬 Asistente ${e(nombreTema)}</span>
        <span class="chatbot-panel__acciones">
          <button type="button" class="chatbot-panel__reset" id="chatbot-reset" aria-label="Empezar de nuevo" title="Empezar de nuevo">↺</button>
          <button type="button" class="chatbot-panel__close" id="chatbot-close" aria-label="Cerrar asistente">×</button>
        </span>
      </header>
      <div class="chatbot-panel__messages" id="chatbot-messages" aria-live="polite"></div>
      <form class="chatbot-panel__form" id="chatbot-form">
        <input class="input" id="chatbot-input" type="text" placeholder="Escribí tu pregunta..." aria-label="Escribí tu pregunta" autocomplete="off" maxlength="300" enterkeyhint="send" />
        <button type="submit" class="chatbot-panel__send" aria-label="Enviar pregunta">➤</button>
      </form>
      <p class="chatbot-panel__pie">¿Preferís que te responda una persona? <a href="${urlConsulta}" id="chatbot-consulta">Dejá tu consulta</a></p>
    </section>
  `
  );

  const fab = document.getElementById('chatbot-fab');
  const panel = document.getElementById('chatbot-panel');
  const closeBtn = document.getElementById('chatbot-close');
  const resetBtn = document.getElementById('chatbot-reset');
  const mensajes = document.getElementById('chatbot-messages');
  const form = document.getElementById('chatbot-form');
  const input = document.getElementById('chatbot-input');

  let saludado = false;
  let sugerenciasIniciales = null;

  function bajar() {
    mensajes.scrollTop = mensajes.scrollHeight;
    guardar();
  }

  function guardar() {
    try {
      sessionStorage.setItem(CLAVE_HISTORIAL, JSON.stringify({ html: mensajes.innerHTML, ultimaPregunta }));
    } catch {
      /* sin almacenamiento: la conversación se pierde al cambiar de página */
    }
  }

  function restaurar() {
    try {
      const guardado = JSON.parse(sessionStorage.getItem(CLAVE_HISTORIAL) || 'null');
      if (!guardado || !guardado.html) return false;
      mensajes.innerHTML = guardado.html;
      // Si quedó a medio responder, se saca el "escribiendo".
      mensajes.querySelectorAll('.chatbot-escribiendo').forEach((el) => el.closest('.chatbot-msg').remove());
      ultimaPregunta = guardado.ultimaPregunta || '';
      return mensajes.children.length > 0;
    } catch {
      return false;
    }
  }

  function olvidar() {
    try {
      sessionStorage.removeItem(CLAVE_HISTORIAL);
    } catch {
      /* nada que borrar */
    }
  }

  function agregarMensaje({ quien, html }) {
    const burbuja = document.createElement('div');
    burbuja.className = `chatbot-msg chatbot-msg--${quien}`;
    burbuja.innerHTML = html;
    mensajes.appendChild(burbuja);
    bajar();
    return burbuja;
  }

  // Botones de pregunta: al tocarlos se manda ese texto tal cual. Los
  // anteriores se sacan para que la conversación no se llene de opciones.
  function agregarOpciones(preguntas, titulo) {
    if (!preguntas || !preguntas.length) return;
    mensajes.querySelectorAll('.chatbot-opciones').forEach((el) => el.remove());
    const caja = document.createElement('div');
    caja.className = 'chatbot-opciones';
    caja.innerHTML =
      (titulo ? `<div class="chatbot-opciones__titulo">${e(titulo)}</div>` : '') +
      preguntas
        .map((p) => `<button type="button" class="chatbot-chip" data-pregunta="${e(p)}">${e(p)}</button>`)
        .join('');
    mensajes.appendChild(caja);
    bajar();
  }

  function agregarFeedback() {
    const caja = document.createElement('div');
    caja.className = 'chatbot-feedback';
    caja.innerHTML = `
      <span>¿Te sirvió?</span>
      <button type="button" class="chatbot-feedback__btn" data-feedback="si">👍 Sí</button>
      <button type="button" class="chatbot-feedback__btn" data-feedback="no">👎 No</button>`;
    mensajes.appendChild(caja);
    bajar();
  }

  async function cargarSugerencias() {
    if (sugerenciasIniciales) return sugerenciasIniciales;
    try {
      const resp = await fetch(`/temas/${temaSlug}/chatbot/sugerencias`);
      sugerenciasIniciales = await resp.json();
    } catch {
      sugerenciasIniciales = [];
    }
    return sugerenciasIniciales;
  }

  async function ponerEjemplo() {
    const sugerencias = await cargarSugerencias();
    if (sugerencias.length) input.placeholder = `Ej.: ${sugerencias[0]}`;
  }

  async function saludar() {
    agregarMensaje({ quien: 'bot', html: e(SALUDO) });
    agregarOpciones(await cargarSugerencias());
    ponerEjemplo();
  }

  async function responder(consulta) {
    mensajes.querySelectorAll('.chatbot-opciones, .chatbot-feedback').forEach((el) => el.remove());
    const escribiendo = agregarMensaje({
      quien: 'bot',
      html: '<span class="chatbot-escribiendo" aria-label="Buscando respuesta"><i></i><i></i><i></i></span>',
    });

    let datos;
    try {
      const resp = await fetch(`/temas/${temaSlug}/chatbot`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mensaje: consulta }),
      });
      datos = await resp.json();
    } catch {
      escribiendo.remove();
      agregarMensaje({ quien: 'bot', html: 'No pude conectarme para responder. Probá de nuevo en un momento.' });
      return;
    }
    escribiendo.remove();

    if (!datos.encontrado) {
      if (datos.charla) {
        // "Hola", "gracias": respuesta corta y las opciones para seguir.
        agregarMensaje({ quien: 'bot', html: e(datos.charla) });
        agregarOpciones(datos.sugerencias);
        return;
      }
      if (datos.otro_tema) {
        // La pregunta es de otro sistema: mejor llevarlo ahí que decir "no sé".
        const o = datos.otro_tema;
        agregarMensaje({
          quien: 'bot',
          html: `Eso parece ser de <b>${e(o.tema)}</b>, no de ${e(nombreTema)}.<span class="chatbot-msg__otro-tema">${e(o.titulo)}</span><a class="chatbot-msg__link" href="${e(o.url)}">Ir a ${e(o.tema)} →</a>`,
        });
        return;
      }
      if (datos.quiso_decir && datos.quiso_decir.length) {
        agregarMensaje({ quien: 'bot', html: e(QUISO_DECIR) });
        agregarOpciones(datos.quiso_decir);
      } else {
        agregarMensaje({
          quien: 'bot',
          html: `${e(SIN_RESULTADOS)}<a class="chatbot-msg__link" href="${urlConsulta}?contexto=${encodeURIComponent(consulta)}">Dejar una consulta →</a>`,
        });
        agregarOpciones(datos.sugerencias || (await cargarSugerencias()));
      }
      return;
    }

    const respuesta = agregarMensaje({
      quien: 'bot',
      html: `${datos.html}<a class="chatbot-msg__link" href="${datos.url}">${e(datos.link_texto)}</a>`,
    });
    agregarFeedback();
    agregarOpciones(datos.relacionadas, 'También te puede servir:');
    // Si la respuesta es larga, que se lea desde el principio (con la
    // pregunta arriba) y no desde los botones del final.
    const pregunta = respuesta.previousElementSibling;
    mensajes.scrollTop = (pregunta || respuesta).offsetTop - mensajes.offsetTop - 8;
  }

  function preguntar(consulta) {
    ultimaPregunta = consulta;
    agregarMensaje({ quien: 'usuario', html: e(consulta) });
    responder(consulta);
  }

  function abrir() {
    panel.classList.add('is-open');
    panel.setAttribute('aria-hidden', 'false');
    fab.setAttribute('aria-expanded', 'true');
    if (!saludado) {
      if (restaurar()) ponerEjemplo();
      else saludar();
      saludado = true;
      bajar();
    }
    setTimeout(() => input.focus(), 60);
  }

  function cerrar() {
    panel.classList.remove('is-open');
    panel.setAttribute('aria-hidden', 'true');
    fab.setAttribute('aria-expanded', 'false');
  }

  fab.addEventListener('click', () => {
    if (panel.classList.contains('is-open')) cerrar();
    else abrir();
  });
  closeBtn.addEventListener('click', cerrar);
  resetBtn.addEventListener('click', () => {
    mensajes.innerHTML = '';
    ultimaPregunta = '';
    olvidar();
    saludar();
    input.focus();
  });
  document.addEventListener('keydown', (ev) => {
    if (ev.key === 'Escape' && panel.classList.contains('is-open')) cerrar();
  });

  form.addEventListener('submit', (ev) => {
    ev.preventDefault();
    const consulta = input.value.trim();
    if (!consulta) return;
    input.value = '';
    preguntar(consulta);
  });

  document.getElementById('chatbot-consulta').addEventListener('click', (ev) => {
    if (ultimaPregunta) ev.currentTarget.href = `${urlConsulta}?contexto=${encodeURIComponent(ultimaPregunta)}`;
  });

  mensajes.addEventListener('click', (ev) => {
    if (ev.target.closest('.chatbot-msg__link')) {
      cerrar();
      return;
    }
    const chip = ev.target.closest('.chatbot-chip');
    if (chip) {
      preguntar(chip.dataset.pregunta);
      return;
    }
    const fb = ev.target.closest('.chatbot-feedback__btn');
    if (fb) {
      fb.closest('.chatbot-feedback').remove();
      // Se avisa al servidor solo cuando no sirvió: así el admin ve qué falta.
      if (fb.dataset.feedback === 'no') {
        fetch(`/temas/${temaSlug}/chatbot/feedback`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ pregunta: ultimaPregunta, util: false }),
        }).catch(() => {});
      }
      if (fb.dataset.feedback === 'si') {
        agregarMensaje({ quien: 'bot', html: '¡Genial! Si tenés otra duda, escribila acá abajo.' });
      } else {
        agregarMensaje({
          quien: 'bot',
          html: `Perdón. Probá contarlo con otras palabras, o dejanos la consulta y te respondemos.<a class="chatbot-msg__link" href="${urlConsulta}?contexto=${encodeURIComponent(ultimaPregunta)}">Dejar una consulta →</a><a class="chatbot-msg__link" href="${urlProblemas}">Ver "Tengo un problema" →</a>`,
        });
      }
    }
  });
}
