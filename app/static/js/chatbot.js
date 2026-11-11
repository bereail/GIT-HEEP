// chatbot.js — asistente de preguntas, 100% local (sin IA externa, sin
// costo). Es la misma idea que timbo-capacitacion/assets/js/chatbot.js, pero
// ahora el índice vive en el servidor (una base de datos por tema) en vez de
// un archivo content.js fijo, así que la pregunta se manda por fetch en vez
// de buscarse en un índice ya cargado en el navegador.

function e(texto) {
  const div = document.createElement('div');
  div.textContent = texto == null ? '' : String(texto);
  return div.innerHTML;
}

export function initChatbot({ temaSlug, nombreTema }) {
  const SALUDO = `Hola, soy el asistente de ${nombreTema}. Preguntame algo como "¿cómo busco un paciente?" y te muestro la respuesta.`;
  const SIN_RESULTADOS = 'No tengo una respuesta exacta para eso todavía. Probá con otras palabras, o mirá directamente "Quiero hacer..." o el Glosario. Si no encontrás lo que necesitás, dejanos tu consulta.';

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
        <button type="button" class="chatbot-panel__close" id="chatbot-close" aria-label="Cerrar asistente">×</button>
      </header>
      <div class="chatbot-panel__messages" id="chatbot-messages" aria-live="polite"></div>
      <form class="chatbot-panel__form" id="chatbot-form">
        <input class="input" id="chatbot-input" type="text" placeholder="Escribí tu pregunta..." aria-label="Escribí tu pregunta" autocomplete="off" />
        <button type="submit" class="chatbot-panel__send" aria-label="Enviar pregunta">➤</button>
      </form>
    </section>
  `
  );

  const fab = document.getElementById('chatbot-fab');
  const panel = document.getElementById('chatbot-panel');
  const closeBtn = document.getElementById('chatbot-close');
  const mensajes = document.getElementById('chatbot-messages');
  const form = document.getElementById('chatbot-form');
  const input = document.getElementById('chatbot-input');

  let saludado = false;

  function agregarMensaje({ quien, html }) {
    const burbuja = document.createElement('div');
    burbuja.className = `chatbot-msg chatbot-msg--${quien}`;
    burbuja.innerHTML = html;
    mensajes.appendChild(burbuja);
    mensajes.scrollTop = mensajes.scrollHeight;
  }

  async function responder(consulta) {
    let datos;
    try {
      const resp = await fetch(`/temas/${temaSlug}/chatbot`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mensaje: consulta }),
      });
      datos = await resp.json();
    } catch {
      agregarMensaje({ quien: 'bot', html: 'No pude conectarme para responder. Probá de nuevo en un momento.' });
      return;
    }
    if (!datos.encontrado) {
      agregarMensaje({ quien: 'bot', html: e(SIN_RESULTADOS) });
      return;
    }
    agregarMensaje({
      quien: 'bot',
      html: `${datos.html}<a class="chatbot-msg__link" href="${datos.url}">${e(datos.link_texto)}</a>`,
    });
  }

  function abrir() {
    panel.classList.add('is-open');
    panel.setAttribute('aria-hidden', 'false');
    fab.setAttribute('aria-expanded', 'true');
    if (!saludado) {
      agregarMensaje({ quien: 'bot', html: e(SALUDO) });
      saludado = true;
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
  document.addEventListener('keydown', (ev) => {
    if (ev.key === 'Escape' && panel.classList.contains('is-open')) cerrar();
  });

  form.addEventListener('submit', (ev) => {
    ev.preventDefault();
    const consulta = input.value.trim();
    if (!consulta) return;
    agregarMensaje({ quien: 'usuario', html: e(consulta) });
    input.value = '';
    responder(consulta);
  });

  mensajes.addEventListener('click', (ev) => {
    if (ev.target.closest('.chatbot-msg__link')) cerrar();
  });
}
