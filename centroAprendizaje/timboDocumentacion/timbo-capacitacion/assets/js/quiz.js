// quiz.js — renderizado y corrección de los 4 tipos de pregunta:
// multiple-choice, true-false, order-steps y checklist.

function mezclar(array) {
  const copia = array.slice();
  for (let i = copia.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copia[i], copia[j]] = [copia[j], copia[i]];
  }
  return copia;
}

function crearElemento(tag, props = {}, hijos = []) {
  const el = document.createElement(tag);
  for (const [clave, valor] of Object.entries(props)) {
    if (clave === 'class') el.className = valor;
    else if (clave === 'html') el.innerHTML = valor;
    else if (clave.startsWith('on') && typeof valor === 'function') el.addEventListener(clave.slice(2), valor);
    else el.setAttribute(clave, valor);
  }
  for (const hijo of hijos) {
    if (hijo == null) continue;
    el.appendChild(typeof hijo === 'string' ? document.createTextNode(hijo) : hijo);
  }
  return el;
}

function renderMultipleChoice(pregunta, contenedor, onResuelta) {
  const feedback = crearElemento('div', { class: 'quiz-feedback', style: 'display:none' });
  const botones = [];

  const opciones = crearElemento(
    'div',
    { class: 'quiz-options' },
    pregunta.options.map((opcion, indice) => {
      const boton = crearElemento(
        'button',
        {
          class: 'quiz-option',
          type: 'button',
          onclick: () => {
            botones.forEach((b, i) => {
              b.disabled = true;
              if (i === pregunta.correctIndex) b.classList.add('is-correct');
            });
            const acerto = indice === pregunta.correctIndex;
            if (!acerto) boton.classList.add('is-incorrect');
            feedback.style.display = 'block';
            feedback.className = `quiz-feedback ${acerto ? 'quiz-feedback--correct' : 'quiz-feedback--incorrect'}`;
            feedback.textContent = acerto ? `✓ Correcto. ${pregunta.explanation || ''}` : `✗ No es así. ${pregunta.explanation || ''}`;
            onResuelta(acerto);
          },
        },
        [opcion]
      );
      botones.push(boton);
      return boton;
    })
  );

  contenedor.appendChild(opciones);
  contenedor.appendChild(feedback);
}

function renderTrueFalse(pregunta, contenedor, onResuelta) {
  renderMultipleChoice(
    {
      options: ['Verdadero', 'Falso'],
      correctIndex: pregunta.answer ? 0 : 1,
      explanation: pregunta.explanation,
    },
    contenedor,
    onResuelta
  );
}

function renderOrderSteps(pregunta, contenedor, onResuelta) {
  const orden = mezclar(pregunta.steps);
  let resuelto = false;

  const lista = crearElemento('ul', { class: 'quiz-order-list' });

  function render() {
    lista.innerHTML = '';
    orden.forEach((texto, indice) => {
      const item = crearElemento('li', { class: 'quiz-order-item' }, [
        crearElemento('span', {}, [`${indice + 1}. `]),
        crearElemento('span', {}, [texto]),
        crearElemento('span', { class: 'quiz-order-item__controls' }, [
          crearElemento(
            'button',
            {
              class: 'btn btn--ghost btn--icon btn--sm',
              type: 'button',
              'aria-label': 'Mover arriba',
              disabled: resuelto || indice === 0 ? 'disabled' : null,
              onclick: () => {
                [orden[indice - 1], orden[indice]] = [orden[indice], orden[indice - 1]];
                render();
              },
            },
            ['↑']
          ),
          crearElemento(
            'button',
            {
              class: 'btn btn--ghost btn--icon btn--sm',
              type: 'button',
              'aria-label': 'Mover abajo',
              disabled: resuelto || indice === orden.length - 1 ? 'disabled' : null,
              onclick: () => {
                [orden[indice], orden[indice + 1]] = [orden[indice + 1], orden[indice]];
                render();
              },
            },
            ['↓']
          ),
        ]),
      ]);
      lista.appendChild(item);
    });
  }
  render();

  const feedback = crearElemento('div', { class: 'quiz-feedback', style: 'display:none' });
  const botonComprobar = crearElemento(
    'button',
    {
      class: 'btn btn--primary btn--sm',
      type: 'button',
      onclick: () => {
        resuelto = true;
        const acerto = pregunta.steps.every((paso, i) => paso === orden[i]);
        Array.from(lista.children).forEach((li, i) => {
          li.classList.add(pregunta.steps[i] === orden[i] ? 'is-correct-pos' : 'is-wrong-pos');
          Array.from(li.querySelectorAll('button')).forEach((b) => (b.disabled = true));
        });
        feedback.style.display = 'block';
        feedback.className = `quiz-feedback ${acerto ? 'quiz-feedback--correct' : 'quiz-feedback--incorrect'}`;
        feedback.textContent = acerto ? '✓ ¡Orden correcto!' : '✗ El orden no es correcto — en verde ves las posiciones acertadas.';
        botonComprobar.disabled = true;
        onResuelta(acerto);
      },
    },
    ['Comprobar orden']
  );

  contenedor.appendChild(lista);
  contenedor.appendChild(botonComprobar);
  contenedor.appendChild(feedback);
}

function renderChecklist(pregunta, contenedor, onResuelta) {
  const lista = crearElemento(
    'div',
    { class: 'quiz-checklist' },
    pregunta.items.map((texto, indice) => {
      const id = `chk-${Math.random().toString(36).slice(2)}-${indice}`;
      return crearElemento('label', { for: id }, [
        crearElemento('input', { type: 'checkbox', id }),
        crearElemento('span', {}, [texto]),
      ]);
    })
  );
  contenedor.appendChild(crearElemento('p', { class: 'text-muted' }, ['Es una autoevaluación: marcá lo que ya podés explicar con tus palabras.']));
  contenedor.appendChild(lista);
  // El checklist no se "corrige": siempre cuenta como completado al verlo.
  onResuelta(true);
}

/**
 * Renderiza un quiz completo dentro de `contenedor`.
 * `onTerminado(correctas, total)` se llama una sola vez, cuando ya se resolvieron
 * todas las preguntas evaluables (checklist no cuenta para el puntaje).
 */
export function renderizarQuiz(contenedor, preguntas, onTerminado) {
  contenedor.innerHTML = '';
  if (!preguntas || !preguntas.length) {
    onTerminado(0, 0);
    return;
  }

  const evaluables = preguntas.filter((p) => p.type !== 'checklist');
  const resultados = new Array(evaluables.length).fill(null);
  let avisado = false;

  function revisarFin() {
    if (avisado) return;
    if (resultados.every((r) => r !== null)) {
      avisado = true;
      const correctas = resultados.filter(Boolean).length;
      onTerminado(correctas, evaluables.length);
    }
  }

  let indiceEvaluable = 0;
  preguntas.forEach((pregunta) => {
    const bloque = crearElemento('div', { class: 'quiz-question' }, [
      crearElemento('div', { class: 'quiz-question__text' }, [pregunta.question || pregunta.instruction || pregunta.title]),
    ]);
    contenedor.appendChild(bloque);

    if (pregunta.type === 'checklist') {
      renderChecklist(pregunta, bloque, () => {});
      return;
    }

    const miIndice = indiceEvaluable++;
    const marcar = (acerto) => {
      resultados[miIndice] = acerto;
      revisarFin();
    };

    if (pregunta.type === 'multiple-choice') renderMultipleChoice(pregunta, bloque, marcar);
    else if (pregunta.type === 'true-false') renderTrueFalse(pregunta, bloque, marcar);
    else if (pregunta.type === 'order-steps') renderOrderSteps(pregunta, bloque, marcar);
  });

  if (!evaluables.length) onTerminado(0, 0);
}
