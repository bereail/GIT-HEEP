// revision.js — acceso con enlace privado y observaciones del nomenclador.
(function () {
  // ---------------------------------------------------------------- acceso
  // El token viaja en el "#" del enlace: el navegador no lo manda al servidor
  // en la URL. Lo mandamos por POST y lo borramos de la barra de direcciones.
  const form = document.getElementById('rev-acceso-form');
  if (form) {
    const token = decodeURIComponent((location.hash || '').slice(1));
    history.replaceState(null, '', location.pathname);
    if (token) {
      document.getElementById('rev-token').value = token;
      form.submit();
    } else {
      document.getElementById('rev-acceso-titulo').textContent = 'Falta tu enlace de acceso';
      document.getElementById('rev-acceso-texto').textContent = 'Abrí la revisión desde el acceso directo que te dieron.';
    }
    return;
  }

  // ---------------------------------------------------------- observaciones
  const barra = document.querySelector('.rev-barra');
  if (!barra) return;
  const items = Array.from(document.querySelectorAll('.rev-item'));
  const buscar = document.getElementById('rev-buscar');
  let filtro = 'todos';
  const DE_A = 40; // de a pocos, como el nomenclador público
  let limite = DE_A;
  const mas = document.getElementById('rev-mas');

  function aplicar() {
    const q = buscar.value.trim().toLowerCase();
    let coinciden = 0;
    items.forEach((li) => {
      const conObs = li.classList.contains('tiene-obs');
      const ok = (!q || li.dataset.buscar.includes(q)) && (filtro === 'todos' || (filtro === 'con') === conObs);
      li.hidden = !ok || coinciden >= limite;
      if (ok) coinciden += 1;
    });
    document.getElementById('rev-vacio').hidden = coinciden > 0;
    const restan = coinciden - Math.min(coinciden, limite);
    mas.hidden = restan <= 0;
    mas.querySelector('span').textContent = 'Mostrando ' + Math.min(coinciden, limite) + ' de ' + coinciden + '.';
  }
  mas.querySelector('button').addEventListener('click', () => { limite += DE_A; aplicar(); });

  function contar() {
    const con = items.filter((li) => li.classList.contains('tiene-obs')).length;
    document.getElementById('rev-n-con').textContent = con;
    document.getElementById('rev-n-sin').textContent = items.length - con;
  }

  buscar.addEventListener('input', () => { limite = DE_A; aplicar(); });
  document.querySelectorAll('.rev-filtro').forEach((b) => b.addEventListener('click', () => {
    filtro = b.dataset.filtro;
    limite = DE_A;
    document.querySelectorAll('.rev-filtro').forEach((x) => {
      x.classList.toggle('is-active', x === b);
      x.setAttribute('aria-checked', x === b ? 'true' : 'false');
    });
    aplicar();
  }));

  aplicar();

  document.getElementById('rev-lista').addEventListener('click', async (ev) => {
    const li = ev.target.closest('.rev-item');
    if (!li) return;
    const editor = li.querySelector('.rev-obs__editor');
    const abrir = li.querySelector('.rev-obs__abrir');
    const campo = li.querySelector('.rev-obs__campo');
    const vista = li.querySelector('.rev-obs__vista');

    if (ev.target.closest('.rev-obs__abrir')) {
      editor.hidden = false;
      abrir.hidden = true;
      campo.focus();
      return;
    }
    if (ev.target.closest('.rev-obs__cancelar')) {
      campo.value = vista.querySelector('.rev-obs__texto').textContent;
      editor.hidden = true;
      abrir.hidden = false;
      return;
    }
    const guardar = ev.target.closest('.rev-obs__guardar');
    if (!guardar) return;
    const estado = li.querySelector('.rev-obs__estado');
    guardar.disabled = true;
    estado.textContent = 'Guardando…';
    try {
      const r = await fetch(barra.dataset.urlGuardar, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': barra.dataset.csrf },
        body: JSON.stringify({ clave: li.dataset.clave, texto: campo.value }),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok || !d.ok) throw new Error(d.error || (r.status === 403 ? 'Tu acceso venció: abrí de nuevo el acceso directo.' : 'No se pudo guardar.'));
      vista.querySelector('.rev-obs__texto').textContent = d.texto;
      vista.querySelector('.rev-obs__fecha').textContent = d.actualizado ? 'Guardada el ' + d.actualizado : '';
      vista.hidden = !d.texto;
      li.classList.toggle('tiene-obs', !!d.texto);
      abrir.textContent = d.texto ? 'Editar observación' : '+ Agregar observación';
      editor.hidden = true;
      abrir.hidden = false;
      estado.textContent = '';
      contar();
    } catch (e) {
      estado.textContent = '⚠️ ' + e.message;
    } finally {
      guardar.disabled = false;
    }
  });
})();
