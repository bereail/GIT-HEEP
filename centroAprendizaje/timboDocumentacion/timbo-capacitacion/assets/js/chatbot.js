// chatbot.js — asistente de preguntas frecuentes, 100% local (sin IA externa,
// sin backend, sin conexión a internet). Reutiliza el mismo índice de
// búsqueda de search.js sobre el contenido de content.js (glosario, tareas
// de "Quiero hacer...", situaciones de "Tengo un problema", módulos y
// lecciones) para responder en formato de chat. Se sube junto con el resto
// del sitio estático — no requiere ningún paso de deploy aparte.

import { buscar } from './search.js';

function e(texto) {
  const div = document.createElement('div');
  div.textContent = texto == null ? '' : String(texto);
  return div.innerHTML;
}

const SALUDO = 'Hola, soy el asistente de TIMBÓ. Preguntame algo como "¿cómo busco un paciente?" o "qué es el CIE-10" y te muestro la respuesta.';
const SIN_RESULTADOS = 'No tengo una respuesta exacta para eso todavía. Probá con otras palabras, o mirá directamente "Quiero hacer..." o el Glosario.';

function primerBloqueDeTexto(leccion) {
  const bloque = (leccion.blocks || []).find((b) => b.type === 'text');
  return bloque ? bloque.text : '';
}

function armarRespuesta(entrada, { MODULES, SITUATIONS, TASKS }) {
  if (entrada.kind === 'Problema') {
    const situacion = SITUATIONS.find((s) => s.situation === entrada.title);
    if (situacion) {
      return {
        html: `<b>${e(situacion.situation)}</b><br>${e(situacion.solution)}`,
        hash: situacion.goesTo ? `#/modulo/${situacion.goesTo.moduleId}/leccion/${situacion.goesTo.lessonId}` : '#/problemas',
        linkTexto: situacion.goesTo ? 'Ver el procedimiento completo →' : 'Ver en "Tengo un problema" →',
      };
    }
  }
  if (entrada.kind === 'Glosario') {
    return {
      html: `<b>${e(entrada.title)}:</b> ${e(entrada.subtitle)}`,
      hash: entrada.hash,
      linkTexto: 'Ver en el Glosario →',
    };
  }
  if (entrada.kind === 'Tarea') {
    const tarea = TASKS.find((t) => t.question === entrada.title);
    return {
      html: `Para eso, mirá la lección <b>${e(entrada.subtitle)}</b>${tarea ? ` (${tarea.minutes} min).` : '.'}`,
      hash: entrada.hash,
      linkTexto: 'Ir a la lección →',
    };
  }
  if (entrada.kind === 'Lección') {
    const modulo = MODULES.find((m) => m.title === entrada.subtitle);
    const leccion = modulo && modulo.lessons.find((l) => l.title === entrada.title);
    const resumen = leccion ? primerBloqueDeTexto(leccion) : '';
    return {
      html: `<b>${e(entrada.title)}</b>${resumen ? `<br>${e(resumen)}` : ''}`,
      hash: entrada.hash,
      linkTexto: 'Ir a la lección →',
    };
  }
  // Módulo u otro tipo genérico
  return {
    html: `<b>${e(entrada.title)}</b>${entrada.subtitle ? `<br>${e(entrada.subtitle)}` : ''}`,
    hash: entrada.hash,
    linkTexto: 'Ir →',
  };
}

export function initChatbot({ indice, MODULES, SITUATIONS, TASKS }) {
  document.body.insertAdjacentHTML(
    'beforeend',
    `
    <button type="button" class="chatbot-fab" id="chatbot-fab" aria-haspopup="dialog" aria-expanded="false" aria-controls="chatbot-panel">
      <span class="chatbot-fab__icon" aria-hidden="true">💬</span>
      <span class="chatbot-fab__label">¿Tenés una duda?</span>
    </button>
    <section class="chatbot-panel" id="chatbot-panel" role="dialog" aria-label="Asistente de preguntas de TIMBÓ" aria-hidden="true">
      <header class="chatbot-panel__header">
        <span class="chatbot-panel__title">💬 Asistente TIMBÓ</span>
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

  function responder(consulta) {
    const resultados = buscar(indice, consulta, 1);
    if (!resultados.length) {
      agregarMensaje({ quien: 'bot', html: e(SIN_RESULTADOS) });
      return;
    }
    const respuesta = armarRespuesta(resultados[0], { MODULES, SITUATIONS, TASKS });
    agregarMensaje({
      quien: 'bot',
      html: `${respuesta.html}<a class="chatbot-msg__link" href="${respuesta.hash}">${e(respuesta.linkTexto)}</a>`,
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
    fab.focus();
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
