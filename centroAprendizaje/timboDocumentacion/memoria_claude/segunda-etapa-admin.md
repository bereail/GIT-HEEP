---
name: segunda-etapa-admin
description: "Segunda etapa del Centro (formación privada en /admin): criterios de la usuaria, prefijo FP, estado por tandas"
metadata:
  node_type: memory
  type: project
  originSessionId: c30c3917-ed0d-4d2f-9384-67c8d4dd89fa
  modified: 2026-11-15T12:43:29.034Z
---

Desde el 2026-11-15 la usuaria pidió una "segunda etapa": recursos privados de formación en `/admin` (roles, glosario general, biblioteca documental, fichas, flujos interactivos, proveedores, soporte, lector PDF, examen profesional con casos de Compras, seguimiento).

Criterios que fijó:
- Todo lo nuevo solo en `/admin` hasta que lo revise y autorice; nada en producción sin su OK expreso.
- Por tandas: mostrar cada resultado en local antes de seguir con la siguiente.
- Marcar siempre ✅ confirmado (con fuente oficial), 📘 didáctico y ⏳ pendiente; no inventar roles, permisos, pasos ni funciones.
- Separar las etapas de TIMBÓ Compras, del expediente electrónico y de fuera del sistema.
- Fichas con prefijo **FP-01, FP-02…** (CD-01 ya es el formulario oficial de Compra Directa).
- Examen: priorizar casos prácticos reales de Compras.

**Why:** quiere formarse para trabajar con criterio profesional en Compras de un hospital público, y no confía en contenido sin fuente.

Aclaración del 2026-11-15: el sitio es para TODOS los empleados del hospital (herramienta institucional); `/admin` es el espacio privado de la usuaria para administrar. No mezclar públicos ni hacer depender lo público de `/admin`.

Condiciones de aceptación del proyecto (2026-11-15), obligatorias antes de publicar:
1. Auditoría de seguridad completa (público y `/admin`), con hallazgo, gravedad, evidencia, corrección y nueva prueba.
2. 100 % de los contenidos sobre TIMBÓ contrastados con fuentes oficiales, en una matriz de trazabilidad. Las discrepancias entre fuentes se documentan, no se eligen.
3. Inventario exhaustivo de documentos y videos oficiales (título, organismo, fecha, URL, leído o no, aporte, decisión, enlace vigente).
Informe final con porcentajes, descartes, pruebas y riesgos residuales.

**How to apply:**
- Tanda 1 (auditoría e investigación) hecha: `timboDocumentacion/INVESTIGACION_SEGUNDA_ETAPA.md` (commit `be93fc1`, solo local).
- Seguridad hecha en local: `AUDITORIA_SEGURIDAD.md`, `app/seguridad.py`, `tests/test_seguridad.py` (commits `2dfad08` a `73b0a0f`, nada deployado).
- 2026-11-15: hechos Recursos (también públicos en /recursos, con menú desplegable, a pedido de la usuaria) y el centro de capacitación privado con la primera clase (pptx, pdf y guía). Faltan el inventario, la matriz, el algoritmo de procedimientos y lo demás que pidió para capacitación (lista en el CLAUDE.md del repo, "Segunda etapa").
- La usuaria manda pedidos nuevos a mitad de turno: guardar seguido y dar un resumen "en limpio" de lo hecho y lo que falta.
- Para el deploy hace falta `pip install -r requirements.txt` (Flask 3.1.3).
- Ver [[faq-pendientes-timbo]].
