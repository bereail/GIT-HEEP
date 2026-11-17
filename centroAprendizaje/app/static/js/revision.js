// revision.js — acceso con enlace privado y validación de equivalencias del nomenclador.
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

  // ------------------------------------------------- validar equivalencias
  // Lista con buscador, como el nomenclador público, de a 15 por página. En
  // cada tarjeta: ✓ Confirmar, ✎ Editar (escribir algo) o ✗ No coincide. Se
  // guarda al tocar; lo escrito, al salir del campo. Si solo escribe algo,
  // sin confirmar ni rechazar, queda "con dudas".
  const raiz = document.getElementById('val');
  if (!raiz) return;
  const datos = JSON.parse(document.getElementById('val-datos').textContent);
  const items = datos.items;
  const porClave = new Map(items.map((i) => [i.clave, i]));
  const $ = (id) => document.getElementById(id);
  const lista = $('val-lista');
  const POR_PAGINA = 15;
  let pagina = 0;
  let filtro = 'pendientes';
  let visibles = new Set(); // los que pasan el filtro; un ítem recién respondido no desaparece hasta cambiar el filtro

  const sinTildes = (t) => (t || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const esc = (t) => String(t == null ? '' : t).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  items.forEach((i) => { i.indice = sinTildes([i.nombre, i.timbo, i.codigo, i.codigo_hospital].join(' ')); });

  function contar() {
    const rev = items.filter((i) => i.validacion).length;
    $('val-n-rev').textContent = rev;
    $('val-n-pend').textContent = items.length - rev;
    $('val-barra').style.width = (items.length ? Math.round((100 * rev) / items.length) : 0) + '%';
  }

  const RESULTADO = { si: '✓ Confirmado', no: '✗ No coincide', duda: '✎ Con dudas' };
  const ACCIONES = [
    ['si', '✓', 'Confirmar', 'Son el mismo artículo: el código de TIMBÓ es correcto'],
    ['editar', '✎', 'Editar', 'Escribir una observación o una duda (si no confirmás ni rechazás, queda “con dudas”)'],
    ['no', '✗', 'No coincide', 'Son artículos diferentes: este código de TIMBÓ no corresponde'],
  ];

  function marca(i) {
    return i.validacion ? `<span class="val-marca val-marca--${i.validacion}">${RESULTADO[i.validacion]}${i.actualizado ? ' · ' + esc(i.actualizado) : ''}</span>` : '';
  }

  function tarjeta(i) {
    const opciones = ACCIONES.map(([v, icono, texto, ayuda]) => {
      const sel = v === 'editar' ? i.validacion === 'duda' || !!i.observacion : i.validacion === v;
      return `<button type="button" class="val-opcion val-opcion--${v}${sel ? ' is-selected' : ''}" data-accion="${v}" aria-pressed="${sel}" title="${esc(ayuda)}" data-ayuda="${esc(ayuda)}"><span class="val-opcion__icono" aria-hidden="true">${icono}</span> ${texto}</button>`;
    }).join('');
    return `
      <li class="val-item val-item--${i.validacion || 'pendiente'}" data-clave="${esc(i.clave)}">
        ${marca(i)}
        <div class="val-item__datos">
          <div>
            <div class="val-item__label">Como figura en el pedido</div>
            <div class="val-item__nombre">${esc(i.nombre)}</div>
            ${i.codigo_hospital ? `<span class="val-item__interno">Código interno del hospital: ${esc(i.codigo_hospital)}</span>` : ''}
          </div>
          <div>
            <div class="val-item__label">En TIMBÓ</div>
            <div class="val-item__timbo">${esc(i.timbo || '—')}</div>
            ${i.codigo ? `<span class="val-item__codigo">${esc(i.codigo)}</span><button type="button" class="val-copiar" data-codigo="${esc(i.codigo)}">Copiar</button>` : ''}
          </div>
          ${i.nota ? `<div class="val-item__nota">${esc(i.nota)}</div>` : ''}
        </div>
        <div class="val-item__resp">
          <div class="val-item__pregunta">¿Son realmente el mismo artículo?</div>
          <div class="val-opciones" role="group" aria-label="Respuesta">${opciones}</div>
          <div class="val-editor"${i.observacion ? '' : ' hidden'}>
            <textarea class="input val-obs" rows="2" maxlength="2000" aria-label="Observación" placeholder="Escribí la observación o la duda.">${esc(i.observacion)}</textarea>
            <button type="button" class="btn btn--primary btn--sm val-guardar" title="Guardar lo escrito">Guardar</button>
          </div>
          <div class="val-estado" role="status"></div>
        </div>
      </li>`;
  }

  function filtrar() {
    const palabras = sinTildes($('val-buscar').value).split(/\s+/).filter(Boolean);
    visibles = new Set(items.filter((i) =>
      (filtro === 'todos' || (filtro === 'revisados') === !!i.validacion) && palabras.every((p) => i.indice.includes(p))
    ).map((i) => i.clave));
    pagina = 0;
    pintar();
  }

  function pintar() {
    const ver = items.filter((i) => visibles.has(i.clave));
    const paginas = Math.max(1, Math.ceil(ver.length / POR_PAGINA));
    pagina = Math.min(pagina, paginas - 1);
    const desde = pagina * POR_PAGINA;
    lista.innerHTML = ver.slice(desde, desde + POR_PAGINA).map(tarjeta).join('');
    const texto = ver.length ? (desde + 1) + '–' + Math.min(desde + POR_PAGINA, ver.length) + ' de ' + ver.length : '';
    document.querySelectorAll('.val-paginas').forEach((nav) => {
      nav.hidden = ver.length <= POR_PAGINA;
      nav.querySelector('.val-paginas__texto').textContent = texto;
      nav.querySelector('[data-mover="-1"]').disabled = pagina === 0;
      nav.querySelector('[data-mover="1"]').disabled = pagina >= paginas - 1;
    });
    $('val-cuenta').textContent = ver.length ? 'Mostrando ' + texto + '.' : '';
    const vacio = $('val-vacio');
    vacio.hidden = ver.length > 0;
    vacio.textContent = $('val-buscar').value.trim() ? 'No hay artículos con esa búsqueda.'
      : filtro === 'pendientes' ? '🎉 No quedan artículos por revisar. Si querés cambiar algo, entrá a Revisados.'
      : 'Todavía no revisaste ningún artículo.';
  }

  function mover(delta) {
    pagina += delta;
    pintar();
    $('val-cuenta').scrollIntoView({ block: 'start', behavior: 'smooth' });
  }

  // De a un pedido por vez: si escribe y enseguida toca "Confirmar", primero
  // se guarda lo escrito y después la respuesta, en ese orden.
  let cola = Promise.resolve();
  function guardar(li, cambios) {
    cola = cola.then(() => guardarYa(li.dataset.clave, cambios));
    return cola;
  }

  const tarjetaDe = (clave) => lista.querySelector(`[data-clave="${CSS.escape(clave)}"]`);

  async function guardarYa(clave, cambios) {
    const item = porClave.get(clave);
    const estadoDe = () => { const li = tarjetaDe(clave); return li ? li.querySelector('.val-estado') : { classList: { add() {}, remove() {} } }; };
    estadoDe().textContent = 'Guardando…';
    estadoDe().classList.remove('is-error');
    try {
      const r = await fetch(raiz.dataset.urlGuardar, {
        method: 'POST',
        keepalive: true,
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': raiz.dataset.csrf },
        body: JSON.stringify(Object.assign({ clave: item.clave }, cambios)),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok || !d.ok) throw new Error(d.error || (r.status === 403 ? 'Tu acceso venció: abrí de nuevo el acceso directo.' : 'No se pudo guardar. Probá de nuevo.'));
      item.validacion = d.validacion;
      item.observacion = d.texto;
      item.actualizado = d.actualizado;
      contar();
      // Repinta la tarjeta (marca de revisado, botones) si sigue en pantalla,
      // sin perder lo que esté escribiendo.
      const li = tarjetaDe(clave);
      if (!li) return;
      const campo = li.querySelector('.val-obs');
      const escribiendo = document.activeElement === campo;
      const abierto = !li.querySelector('.val-editor').hidden;
      const borrador = campo.value;
      li.outerHTML = tarjeta(item);
      const nuevo = tarjetaDe(clave);
      const nuevoCampo = nuevo.querySelector('.val-obs');
      if (abierto) nuevo.querySelector('.val-editor').hidden = false;
      if (escribiendo) { nuevoCampo.value = borrador; nuevoCampo.focus(); }
      nuevo.querySelector('.val-estado').textContent = '✓ Guardado';
    } catch (e) {
      const li = tarjetaDe(clave);
      if (li) delete li.dataset.enviado; // que "Guardar" permita reintentar
      const estado = estadoDe();
      estado.textContent = '⚠️ ' + e.message;
      estado.classList.add('is-error');
    }
  }

  lista.addEventListener('click', (ev) => {
    const li = ev.target.closest('.val-item');
    if (!li) return;
    const opcion = ev.target.closest('.val-opcion');
    if (opcion && opcion.dataset.accion === 'editar') {
      li.querySelector('.val-editor').hidden = false;
      li.querySelector('.val-obs').focus();
      return;
    }
    if (ev.target.closest('.val-guardar')) {
      guardarObs(li);
      return;
    }
    if (opcion) {
      guardar(li, { validacion: opcion.dataset.accion, texto: li.querySelector('.val-obs').value });
      return;
    }
    const copiar = ev.target.closest('.val-copiar');
    if (copiar && navigator.clipboard) {
      navigator.clipboard.writeText(copiar.dataset.codigo).then(() => {
        copiar.textContent = '¡Copiado!';
        copiar.classList.add('is-ok');
        setTimeout(() => { copiar.textContent = 'Copiar'; copiar.classList.remove('is-ok'); }, 1500);
      });
    }
  });

  // La observación se guarda con el botón Guardar o al salir del campo, si
  // cambió (y una sola vez aunque pasen las dos cosas).
  function guardarObs(li) {
    const campo = li.querySelector('.val-obs');
    const item = porClave.get(li.dataset.clave);
    const texto = campo.value.trim();
    if (texto === (item.observacion || '') || texto === li.dataset.enviado) return;
    li.dataset.enviado = texto;
    // Escribió algo sin confirmar ni rechazar: queda "con dudas".
    const cambios = { texto: campo.value };
    if (!item.validacion && texto) cambios.validacion = 'duda';
    guardar(li, cambios);
  }
  lista.addEventListener('change', (ev) => {
    if (ev.target.classList.contains('val-obs')) guardarObs(ev.target.closest('.val-item'));
  });
  // Si cierra la pestaña con una observación a medio escribir, igual se guarda.
  document.addEventListener('visibilitychange', () => {
    const campo = document.activeElement;
    if (document.visibilityState === 'hidden' && campo && campo.classList && campo.classList.contains('val-obs')) {
      campo.dispatchEvent(new Event('change', { bubbles: true }));
    }
  });

  document.querySelectorAll('.val-tile').forEach((t) => t.addEventListener('click', () => {
    filtro = t.dataset.filtro;
    document.querySelectorAll('.val-tile').forEach((x) => {
      x.classList.toggle('is-active', x === t);
      x.setAttribute('aria-checked', x === t ? 'true' : 'false');
    });
    filtrar();
  }));
  $('val-buscar').addEventListener('input', filtrar);
  document.querySelectorAll('.val-paginas [data-mover]').forEach((b) => b.addEventListener('click', () => mover(Number(b.dataset.mover))));
  // Flechas del teclado para pasar de página (si no está escribiendo).
  document.addEventListener('keydown', (ev) => {
    if (/^(INPUT|TEXTAREA|SELECT)$/.test((document.activeElement || {}).tagName || '')) return;
    const nav = document.querySelector('.val-paginas');
    if (nav.hidden) return;
    if (ev.key === 'ArrowRight' && !nav.querySelector('[data-mover="1"]').disabled) mover(1);
    if (ev.key === 'ArrowLeft' && !nav.querySelector('[data-mover="-1"]').disabled) mover(-1);
  });

  contar();
  filtrar();
})();
