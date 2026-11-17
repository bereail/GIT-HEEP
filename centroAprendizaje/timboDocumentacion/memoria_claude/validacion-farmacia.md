---
name: validacion-farmacia
description: "Revisión del nomenclador por farmacia (17/11/2026) — lista con buscador, ✓/✎/✗, Excel por colores; preferencias de diseño que fijó la usuaria"
metadata:
  node_type: memory
  type: project
  originSessionId: 873a91b2-3522-426a-91d1-229181a718d4
  modified: 2026-11-17T09:22:41.559Z
---

El 17/11/2026 se mejoró la pantalla de farmacia (`/revision/`, entra con la llave) y el panel `/admin/nomenclador/revision`. Detalle técnico en la sección "Validación de equivalencias por farmacia" del CLAUDE.md del repo.

Lo que decidió la usuaria al verlo (respetarlo si se vuelve a tocar):
- **Lista con buscador como el nomenclador público, de a 15 con flechas**. Se probó "un artículo por vez" con Anterior/Siguiente y NO le gustó.
- Tres acciones por tarjeta: **✓ Confirmar** (verde), **✎ Editar** (escribe algo, con mini botón Guardar) y **✗ No coincide** (rojo), con ayuda al pasar el mouse. Lo revisado se ve distinto (teñido + marca con fecha).
- Mostrar la nota del ítem y el código interno del hospital, igual que el público.
- Excel separado por hojas y **filas pintadas por color** según la respuesta; también uno por persona desde el panel.
- En local la contraseña del admin es siempre `admin123` (fijada en `run.py`).

**Why:** quiere que farmacia valide rápido, sin capacitación, y obtener una base ordenada.
**How to apply:** para mostrarle cambios de pantalla, levantar un servidor de prueba en el puerto 5001 sobre una COPIA de la base con una usuaria de ejemplo (script en el scratchpad, rehacerlo) y abrirle el enlace; ella pide ver antes de commitear. Ver [[faq-pendientes-timbo]].
