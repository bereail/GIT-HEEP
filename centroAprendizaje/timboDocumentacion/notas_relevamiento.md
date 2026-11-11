# Notas de relevamiento — MIHOSPITAL (borrador de trabajo)

> Documento de trabajo interno. NO es el manual final. Acá se van registrando notas crudas de cada pantalla a medida que se explora el sistema. El manual final se redacta aparte a partir de esto.

- Sistema: Sistema de Salud Hospitalario miHospital — Gobierno de Santa Fe, Ministerio de Salud
- Instancia relevada: http://192.168.4.24/mihospital (confirmado por el usuario como ambiente de staging/pruebas)
- Establecimiento activo en la sesión: HOSP EVA PERON
- Usuario de relevamiento: sa (rol a determinar por observación)
- Versión de sistema: 26.5.6
- Fecha de relevamiento: 2026-09-03

## Mapa de navegación (menú lateral principal)

```
MIHOSPITAL
├── Menú principal (Home)
├── Pacientes ▸
│   ├── Inicio            → /mihospital/panel/pacientes/home
│   ├── Pacientes         → /mihospital/panel/pacientes/listado
│   └── Altas del día     → /mihospital/panel/pacientes/altas-dia
├── Consultorios ▸        → /mihospital/consultorio (pendiente de expandir submenú)
├── Internaciones ▸       → /mihospital/epicrisis (pendiente de expandir submenú)
├── Quirófano             → /mihospital/quirofano (sin flecha de submenú visible aún)
├── Red Salud             → (pendiente)
└── Administración ▸      → (pendiente)
```

Tarjetas de inicio (home): Pacientes, Consultorios, Internaciones, Quirófano — cada una con dropdown "Secciones".
Widget "Accesos Externos" → botón "RED PROVINCIAL DE SALUD" (enlace externo).

## Pantallas relevadas

### Home / Menú principal
- URL: /mihospital/home
- 4 tarjetas de acceso directo + Accesos Externos.

### Módulo Pacientes — Inicio
- URL: /mihospital/panel/pacientes/home
- Widgets:
  - "BUSCADOR DE PACIENTES": input "Buscar por Nombre/Apellido/Documento/H.C." + botón Buscar
  - "ALTAS DEL DÍA": input tipo fecha (default = hoy) + botón Buscar
- Widgets minimizables/cerrables (íconos − y × en cada uno)

## Mapa de navegación completo (confirmado vía DOM)

```
MIHOSPITAL
├── Menú Principal (Home)                       /mihospital/home
├── Pacientes ▸
│   ├── Inicio                                  /mihospital/panel/pacientes/home
│   ├── Pacientes (buscador/listado)             /mihospital/panel/pacientes/listado
│   └── Altas del día                            /mihospital/panel/pacientes/altas-dia
├── Consultorios ▸
│   ├── Inicio                                   /mihospital/consultorio
│   ├── Turnos                                   /mihospital/consultorio/turnosDetalle
│   └── Conf. Edilicia ▸
│       ├── Profesionales                        /mihospital/consultorio/profesionales
│       └── Consultorios                         /mihospital/consultorio/consultorios
├── Internaciones ▸ (Módulo "Epicrisis")
│   ├── Inicio                                   /mihospital/epicrisis
│   ├── Salas                                    /mihospital/epicrisis/navSalas
│   ├── Internaciones                            /mihospital/epicrisis/navInternaciones
│   ├── Diagnósticos                             /mihospital/epicrisis/navDiagnosticos
│   └── Nomencladores ▸
│       ├── CIE-10                               /mihospital/epicrisis/navCie10
│       └── Cirugías                             /mihospital/epicrisis/navOperaciones
├── Quirófano (accesos vía "Secciones" en home / módulo)
│   ├── Inicio                                   /mihospital/quirofano
│   ├── Cirugías: Lista de Espera                /mihospital/quirofano/cirugiasEspera
│   ├── Cirugías: Cirugías c/Turno                /mihospital/quirofano/cirugias
│   ├── Cirugías: Nueva Cirugía                   /mihospital/quirofano/cirugiaCabeTrn/INS/0/-/noMsg/principal
│   ├── Informes: Parte Qx Diario (modal)
│   ├── Informes: Parte de Enfermería (modal)
│   ├── Informes: Cx c/Fecha Probable (modal)
│   ├── Informes: Producción                      /mihospital/quirofano/informe/cirugiasProduccion
│   ├── Nomenclador (procedimientos)               /mihospital/quirofano/procedimientos
│   └── Configuración                              /mihospital/quirofano/configuracion/configuraciones
├── Red Salud                                    enlace externo (RPS - Red Provincial de Salud), requiere parámetros configurados
└── Administración                                /mihospital/home/configuracion/configuraciones
    ├── Módulos Habilitados                        /mihospital/home/configuracion/configuracionModulos
    ├── Compatibilidad Informes Diagnose/Acceso PACS /mihospital/home/configuracion/configuracionInformes
    ├── RPS (parámetros Red Provincial de Salud)    /mihospital/home/configuracion/configuracionRPS
    ├── Plantillas de Informes                      /mihospital/home/configuracion/configuracionPlantillas
    └── 🔴 Crear esquema de controles/permisos       /mihospital/home/configuracion/sysConfiguracionFixture
        (botón rojo, acción de esquema de BD — NO EJECUTADA, ver Limitaciones)

Barra superior:
├── 🔔 Notificaciones (sin novedades en la sesión relevada) → /mihospital/home/novedades?tipo=Notificaciones
├── ✉️ Mensajes (sin novedades) → /mihospital/home/novedades?tipo=Mensajes
└── 👤 Usuario (SA / "Administrador, Usuario")
    ├── Cambiar Contraseña → /mihospital/home/configuracion/usuario/home
    └── Cerrar Sesión → /mihospital/home/logout
```

## Rol observado
Usuario `sa` se identifica en el sistema como **"Administrador, Usuario"** (ver alerta del módulo Quirófano: "Alertas para el usuario SA - Administrador, Usuario"). Tiene acceso a los 5 módulos habilitados y a Administración. No se probó con otros roles (no se crearon ni modificaron usuarios).

## Módulos habilitados en este efector (HOSP EVA PERON)
Vía Administración > Módulos Habilitados: QUIROFANO, EPICRISIS, RPS, PACIENTE, CONSULTORIO. Cada uno tiene botón "Desactivar Módulo" (NO se tocó, es una acción crítica/reversible con impacto operativo).

## 🔴 Hallazgo importante — Error en pestaña "Laboratorios" de Ficha de Paciente
URL: /mihospital/panel/pacientes/pacienteLaboratorio/{id}
Al abrir la pestaña "Laboratorios" de CUALQUIER ficha de paciente, el sistema devuelve **Error 500 Internal Server Error** (Doctrine DBALException): `SQLSTATE[42S22]: Column not found: 1054 Unknown column 'l0_.stamp_usu_id' in 'field list'` en la tabla `labt_orden_analisis`.
- Parece un problema de esquema de base de datos desactualizado (falta la columna `stamp_usu_id`) en esta instancia.
- La página de error expone información sensible de infraestructura: consultas SQL completas, nombres de tablas y columnas internas, y una ruta de servidor (`/home/sectorial/git/mihospital/diagnose-web/code/...`). Esto es un problema de "modo debug" activo — no debería exponerse así ante un error. Recomendación: reportar a Sectorial Informática.
- Probado con paciente HC 1000001 (registro "VIRTUAL"/de prueba del propio sistema).

## Ficha del Paciente — estructura confirmada (paciente de prueba HC 1.000.001 "SOSA, MARTA", marcado VIRTUAL — NO es un paciente real, usado como ejemplo seguro)
Panel izquierdo fijo: Nombre, HC, DNI, F. Nacimiento (+edad calculada), Sexo, Obra Social, botón "PULSERA IDENT." (imprime pulsera identificatoria), bloque Contacto (Domicilio, Teléfono, Celular, C. Salud Ref.).
Pestañas (todas bajo /mihospital/panel/pacientes/paciente{Tab}/{id}):
- Datos Personales (pacienteDatos) — Datos Personales del Paciente + Datos Complementarios del Tutor (nombre/doc madre y padre)
- Internaciones (pacienteInternaciones) — listado de internaciones del paciente ("Sin Internaciones Registradas" si no tiene)
- Guardia (pacienteTurnos/{id}/S) — atenciones de guardia
- Turnos C.E. (pacienteTurnos/{id}/N) — turnos de consultorio externo. Filtros: Especialidad (combo), Desde/Hasta (fechas). Tabla: Fecha, Hora, Presentismo, Especialidad, Profesional, Pedido, Turno (acción "Continuar")
- Cirugías (pacienteCirugias)
- Laboratorios (pacienteLaboratorio) — 🔴 ROTO, ver hallazgo arriba
- Farmacia (pacienteStock) — entregas de farmacia al paciente
- Compras (pacienteCompras) — compras asociadas al paciente

## Buscador de Pacientes (listado)
URL: /mihospital/panel/pacientes/listado
- Campo de texto libre: "Buscar por Nombre/Apellido/Documento/H.C." — mínimo aparente 3 caracteres, dispara por Enter o botón lupa (envía por GET, parámetro `texto`)
- Botón "Desplegar más filtros" (ícono embudo) revela búsqueda avanzada con campos separados (confirmado por query string): Apellido, Nombre, Nro. Documento, Nro. H.C., Sexo, Fecha Nacimiento, Tipo H.C., Activo/Inactivo
- Resultado: tabla con columnas Nombre, Nro. Documento, Fecha Nac., Sexo, Nro. H.C., Obra Social. Cada fila es un link a la ficha del paciente.
- Búsquedas amplias (ej. 3 letras comunes) pueden devolver decenas de miles de resultados (se observó "Pacientes (49758)" con un criterio de 3 letras) — la búsqueda puede tardar varios segundos. Recomendar en el manual usar criterios específicos (apellido completo + nombre, o documento).
- ⚠️ IMPORTANTE PARA EL MANUAL: esta pantalla expone de inmediato datos identificatorios (nombre completo, DNI, fecha de nacimiento, obra social) apenas se ejecuta la búsqueda — remarcar en el manual buenas prácticas de privacidad al usarla (no dejar la pantalla abierta/visible, cerrar sesión al terminar).

## Altas del día
URL: /mihospital/panel/pacientes/altas-dia — Filtro Fecha (date picker). Tabla: Nombre, Nro. Documento, Fecha Nac., Nro. H.C., Obra Social, Fecha/Hora Alta, Usuario Alta. Vacío en la fecha relevada.

## Consultorios — Turnos (/mihospital/consultorio/turnosDetalle)
"Turnos del Efector" — búsqueda por Nombre/Apellido/Documento, ícono de filtros adicionales (embudo), botón "REFRESCAR" (auto-refresco de la lista, checkbox "Refrescar automáticamente"). Tabla: ID, Fecha, Hora, Paciente (H.C.), Documento, Presentismo, Especialidad, Estudio, Profesional, Tipo, Pedido. Sugerencia en pantalla: usar Ctrl+F del navegador para buscar dentro de resultados largos.

## Consultorios — Profesionales (/mihospital/consultorio/profesionales)
"Profesionales del Efector" — 1.621 registros. Barra de herramientas tipo planilla: Copiar, CSV, Excel, PDF, Imprimir, Mostrar/Ocultar Columnas, selector "Mostrar N registros/pág.", buscador simple. Tabla: Nombre, Matrícula, Especialidad Ppal., Consultorios Habilitados. Paginado numerado (161 páginas). Esta es la única grilla vista hasta ahora con exportación completa (CSV/Excel/PDF/Impresión).

## Consultorios — Consultorios / Conf. Edilicia (/mihospital/consultorio/consultorios)
"Consultorios del Efector" — filtros combinados: Especialidad, Profesional, Día, C.E. (combos) + búsqueda. Tabla: Especialidad, Profesional, Día, Horario, Tipo (valores vistos: "Turnos Especiales", "Sin Consultorio"). Muestra la grilla de agenda de consultorios por profesional/día/horario.

## Consultorios — Configuración (/mihospital/consultorio/configuraciones)
Solo un ítem: "Plantillas de Informes".

## Internaciones — Salas (/mihospital/epicrisis/navSalas)
"Salas del Efector" — tabla: Sala, Total/Disponibles(*), Ocupadas, Libres, Reservadas, En Reparación, Fuera de Servicio, Acciones ("Ingresar"). Nota al pie: "Disponibles = Ocupadas + Libres + Reservadas". Salas observadas: Cuidados Intermedios, Emergencias, Hospital de Día, Hospital Modular, Internación Domiciliaria, Neonatología, Pediatría, Tocoginecología, Unidad de Cuidados Intensivos.
Al "Ingresar" a una sala (ej. UCI, id 516): pantalla "Sala '{NOMBRE}'" con vistas Ver Listado / Ver Grilla / Reporte Diario (Pase de Sala), filtro Sólo Disponibles/Mostrar todas, agrupado por Habitación (ej. Uci-1..Uci-5), tabla por habitación: Cama, Estado, Paciente, Sexo, Ingreso, Diag. presuntivo, Días estada, Acciones. ⚠️ Esta vista puede exponer nombre y diagnóstico presuntivo del paciente internado en cada cama — pantalla sensible, cuidar quién puede verla.

## Internaciones — Internaciones (listado) (/mihospital/epicrisis/navInternaciones)
"Internaciones (135)" en la sesión relevada — búsqueda + filtro, toggle "Vista Detallada / Totales". Tabla: Ingreso, Sala, Habitación, N° Doc., Nombre, Diag. Presuntivo, Egreso, Diag. Principal, Acciones ("Continuar" = internación abierta). ⚠️ Expone de inmediato nombre, documento y diagnóstico de TODOS los pacientes internados — pantalla de uso clínico/administrativo, extremar cuidado de privacidad (no dejarla proyectada/visible).

## Internaciones — Diagnósticos (listado) (/mihospital/epicrisis/navDiagnosticos)
"Diagnósticos (1184)" — historial de diagnósticos por internación/egreso de todo el efector. Búsqueda + filtro, toggle Vista Detallada/Totales. Tabla: Diagnóstico, Tipo Diag. (Principal/Parcial #1/#2...), Ingreso, Egreso, Sala, Nro. Doc., Nombre, Edad, Acciones. Mismo nivel de sensibilidad que el listado de Internaciones.

## Internaciones — Nomenclador CIE-10 (/mihospital/epicrisis/navCie10)
Catálogo de diagnósticos CIE-10 (código + descripción), búsqueda por Código/Descripción. Catálogo institucional, sin datos de pacientes. Funciona bien (probado con "diabetes" → decenas de códigos E10-E14, O24, P70, etc.)

## Internaciones — Nomenclador Cirugías (provincial) (/mihospital/epicrisis/navOperaciones)
Mismo patrón: Código + Descripción, búsqueda obligatoria.

## Quirófano — Lista de Espera (/mihospital/quirofano/cirugiasEspera)
Tabs superiores "QUIROFANOS CENTRALES" / "QUIROFANOS HOSP DIA" (el módulo Quirófano distingue estos dos circuitos en varias pantallas). Búsqueda + filtro. Vacío en la sesión relevada.

## Quirófano — Cirugías Asignadas / c-Turno (/mihospital/quirofano/cirugias)
Mismos tabs Centrales/Hosp Día + toggle de vista Lista/Calendario. Vacío en la sesión relevada.

## Quirófano — Nueva Cirugía (/mihospital/quirofano/cirugiaCabeTrn/INS/0/-/noMsg/principal) — 🔴 NO SE CONFIRMÓ/GUARDÓ NADA
Formulario completo "Ficha de la Cirugía" (se abre en estado "ANULADA" hasta completarse y confirmarse):
Sección "Definir Cirugía": Inicio Proceso (auto), Fecha Pedido, Fecha Probable, Hora Probable, Tipo de Cirugía (Programada/Urgencia), Oncológica (Sí/No), Tipo de PreQx (default PREQUIRURGICO), Área Quirúrgica (Quirófanos Centrales/Hosp Día), Paciente (buscador), Celular de Contacto, Tel. Fijo de Contacto, Procedencia-Sub-Sector (Ambulatorio/Guardia/Internación/Cama UTI/UCO/UCBC/UCIM/RCV/Derivación), Mail de Contacto, Cirujano, Diagnóstico Presuntivo (buscador CIE10), Diagnóstico a imprimir (texto libre), Procedimiento Quirúrgico Presuntivo (buscador nomenclador), Procedimiento a imprimir, Especialidad (Cirugía Cardíaca, Clínica Quirúrgica-Cirugía General, ORL, Gastroenterología, Neumonología, Neurocirugía, Tocoginecología, Traumatología, Urología Pediátrica...), Observaciones.
Sección "Datos Presuntivos": Tipo Anestesia (Bloqueo/General/Local/Raquídea/Regional/Sedación/Peridural/Plexual/Intubación Selectiva/Sin anestesia), Destino (Ambulatorio/Internación/Cama UTI/UCO/UCBC/UCIM/RCV/Morgue), Req. Diag. por Imágenes (Sí/No), Req. Hemoterapia (Sí/No), Req. Torre Laparoscopia (Sí/No), Req. Materiales Especiales (Sí/No), Tiempo Estimado Cirugía (1 a 8 hs.), Días Post-Operatorio (0 a "más de 28"), Ropa a Utilizar, Cajas a Utilizar.
Sección "Asignación de Prioridades": Score (0-10), Fecha Espera Máx.
Botones finales: Cancelar / Confirmar. NO SE PRESIONÓ "Confirmar" — se documentó la estructura únicamente.

## Quirófano — Producción (/mihospital/quirofano/informe/cirugiasProduccion)
"Informe de Producción" — búsqueda por Procedimiento/Diagnóstico principal + filtro. Tabla: Profesional, Total Prod., Total x Rol. Vacío en la sesión relevada.

## Quirófano — Nomenclador (procedimientos) (/mihospital/quirofano/procedimientos)
"Nomenclador Nacional de Cirugías" — catálogo completo de códigos/procedimientos quirúrgicos (cientos de filas, cargado de entrada sin necesidad de buscar). Catálogo institucional, sin datos de pacientes.

## Quirófano — Configuración (/mihospital/quirofano/configuracion/configuraciones)
Ítems: Alertas (días de anticipación), Quirófanos (salas habilitadas), Roles/Profesionales, Plantillas de Informes (Consentimiento, Resumen Final), Días para Carga Diferida, Materiales/Insumos Habilitados, Especialidades Quirúrgicas habilitadas, Prefijos Habilitados (Nomenclador Nacional), Envío Automático de e-mails - Cambios de Estado, Envío Automático de e-mails - Parte Quirúrgico Diario.

## Perfil de usuario (/mihospital/home/configuracion/usuario/home)
"Datos del Usuario": Nombre = "Administrador, Usuario", Usuario = "sa" (solo lectura). Botón "Cambiar Contraseña" — NO SE PRESIONÓ (regla: no modificar credenciales).

## Red Salud
Enlace en menú lateral (href javascript, se abre externamente). Los parámetros de conexión (Cód. Establecimiento, IP del Establecimiento, Url Logout) están "Sin Definir" en Administración > RPS — el enlace probablemente no funcione correctamente en este efector hasta configurarse. NO SE HIZO CLIC para evitar una redirección externa impredecible con parámetros sin configurar.

## Notificaciones y Mensajes (barra superior)
Ambos widgets mostraron "No tienes notificaciones nuevas." / "No tienes mensajes nuevos." en la sesión relevada. Cada uno tiene un link "Ver todas las notificaciones" / "Ver todos los mensajes" → /mihospital/home/novedades?tipo=Notificaciones|Mensajes.

## Limitaciones de esta documentación
- No se ejecutó "Crear esquema de controles/permisos" (Administración) — acción irreversible sobre el esquema de base de datos.
- No se desactivó ningún módulo desde "Módulos Habilitados".
- No se confirmó ninguna "Nueva Cirugía" ni se generaron órdenes/turnos/altas reales.
- No se cambió la contraseña del usuario sa.
- No se hizo clic en "Red Salud" (parámetros sin configurar, enlace externo).
- No se probaron otros roles/usuarios — solo se documenta lo observable con el usuario "sa" (Administrador).
- Las pantallas de listados de Pacientes, Internaciones y Diagnósticos muestran datos identificatorios reales de personas; se documentó su estructura sin citar nombres/DNI/diagnósticos reales, salvo el paciente de prueba "SOSA, MARTA" (HC 1.000.001), marcado por el propio sistema como "VIRTUAL".
- Los modales de "Parte Qx Diario", "Parte de Enfermería" y "Cx c/Fecha Probable" del módulo Quirófano se abrieron y documentaron el 2026-09-11 (ver sección "Continuación 2026-09-11" más abajo). No se generó ningún informe real (botón "Imprimir") para evitar una descarga sin confirmación.

## Continuación 2026-09-11 — Informes modales de Quirófano

Acceso: módulo Quirófano → panel "Accesos" → columna "Informes" (también replicado en el menú lateral izquierdo bajo el mismo rótulo). Los 3 son botones que abren un modal (no navegan a una URL nueva — se queda en `/mihospital/quirofano`).

**1. Parte Qx Diario** → modal título "Imprimir Parte Quirúrgico Diario"
- Campo: **Fecha** (input tipo date, formato dd/mm/aaaa)
- Botones: **Cancelar** (ícono flecha, cierra el modal) / **Imprimir** (ícono impresora)

**2. Parte de Enfermería** → modal título "Imprimir Parte de Enfermería"
- Misma estructura exacta: campo **Fecha** + **Cancelar** / **Imprimir**

**3. Cx c/Fecha Probable** → modal título "Imprimir Cirugías con Fecha Probable"
- Misma estructura exacta: campo **Fecha** + **Cancelar** / **Imprimir**

Los 3 modales son visualmente y funcionalmente idénticos en su estructura (un único filtro por fecha puntual, sin rango). Se infiere que "Imprimir" genera un documento (PDF probable, a confirmar) para la fecha seleccionada — no se confirmó el formato de salida porque no se ejecutó la acción. Se cerró cada modal con "Cancelar" sin cargar fecha ni generar el documento.

Pendiente si se quiere completar al 100%: cargar una fecha con datos conocidos (ej. una fecha donde se sepa que hubo cirugías cargadas) y confirmar "Imprimir" para ver el formato real de salida — requiere autorización explícita de Berenice porque dispara una descarga de archivo.

## Continuación 2026-09-14 — Red Salud (clic real, con autorización de Berenice)

Berenice autorizó explícitamente hacer clic en el enlace, aceptando el riesgo de una redirección externa impredecible (documentado como pendiente desde el relevamiento inicial).

**Ubicación real del enlace funcional:** no es el ítem "RED SALUD" del menú lateral colapsado (ese solo muestra un tooltip al pasar el mouse, no navega) — el enlace que sí funciona es el botón **"RED PROVINCIAL DE SALUD"** dentro de la tarjeta **"Accesos Externos"** en la pantalla de Inicio (`/mihospital/home`), al lado de un ícono de RSS.

Al hacer clic, se abre una **pestaña nueva del navegador** (no una redirección en la misma pestaña) hacia:
`https://www.santafe.gov.ar/sicap56/cap/includes/seguimiento_paciente/seguimiento.php`

Esa pantalla externa ("Red Provincial", sistema SICAP) muestra un buscador de pacientes con tres bloques:
- **Buscar por Datos Personales:** Apellido*, Nombre*, Sexo*, Fecha de Nacimiento*, Tipo Doc, Número de Documento (los marcados * parecen obligatorios).
- **Buscar por Datos Filiatorios:** Tipo Relación, Número de Documento (para buscar por datos de Padre/Madre/Tutor).
- **Buscar por H.C. o L.F. dentro del efector:** Nro. Legajo Familiar, Nro. Historia Clínica Ambulatorio.
- Botones: Buscar / Nueva Consulta / Cerrar. Sección "Resultados de la búsqueda" debajo, vacía hasta buscar.

🔴 **Hallazgo:** el encabezado de esta pantalla externa muestra **"Usuario: .", "Nodo: -" y "Efector: -"** — los tres completamente vacíos/sin definir. Esto confirma lo que se sospechaba por la configuración de RPS ("Sin Definir" en Administración → RPS de este efector): la integración con la Red Provincial de Salud carga la pantalla y el formulario funcionan visualmente, pero **no logra identificar el usuario ni el efector** ante el sistema provincial. No se pudo determinar si una búsqueda ejecutada en estas condiciones queda igual asociada a algún efector "por defecto", si falla silenciosamente, o si el sistema la rechaza — no se ejecutó ninguna búsqueda real para evitar consultar la base de datos provincial en vivo sin necesidad. Se cerró la pestaña sin buscar.

**Conclusión para el manual:** el enlace a Red Salud no está roto (abre y carga), pero **no es funcionalmente confiable en este efector** hasta que Administración → RPS tenga cargados Código de Establecimiento, IP del Establecimiento y URL de Logout.

## Continuación 2026-09-14 (2) — Tres verificaciones adicionales (con autorización de Berenice)

### 1. Exportación CSV/Excel/PDF en otras grillas
Se revisaron 5 grillas más, además de Consultorios → Profesionales (que sí tiene exportación completa): Turnos del Efector, listado de Pacientes, listado de Internaciones, Informe de Producción (Quirófano) y Nomenclador Nacional de Cirugías (Quirófano). **Ninguna de las 5 tiene los botones Copiar/CSV/Excel/PDF/Imprimir/Columnas.** Confirmado: Profesionales es un caso particular (usa un componente de grilla distinto al resto del sistema), no el estándar.

### 2. Campos obligatorios del formulario "Nueva Cirugía"
Método: se presionó el botón **Confirmar** con el formulario completamente vacío. El sistema **no guardó ningún registro** — mostró, debajo de cada campo faltante, un globo de validación en letra naranja con un mensaje específico (ej. "Seleccione un paciente", "Ingrese la Fecha de Pedido de Cirugía"). Se extrajo el texto completo de la página (incluye esos mensajes de validación insertados en el DOM) para catalogar exactamente qué campos son obligatorios sin necesidad de cargar ni confirmar ningún dato real.

**Resultado — 19 campos obligatorios de ~28 totales:**
Fecha Pedido, Tipo de Cirugía, Oncológica, Paciente, Procedencia-Sub-Sector, Cirujano, Diagnóstico Presuntivo, Diagnóstico a imprimir, Procedimiento Quirúrgico Presuntivo, Procedimiento a imprimir, Especialidad, Tipo Anestesia, Destino, Req. Diag. por Imágenes, Req. Hemoterapia, Req. Torre Laparoscopia, Req. Materiales Especiales, Tiempo Estimado Cirugía, Días Post-Operatorio.

**Opcionales:** Fecha Probable, Hora Probable, Tipo de PreQx (trae valor por defecto), Celular/Tel. Fijo de Contacto, Mail de Contacto, Observaciones, Ropa a Utilizar, Cajas a Utilizar, Score, Fecha Espera Máx.

🟡 **Llamativo:** "Área Quirúrgica" (Quirófanos Centrales / Quirófanos Hosp Día) NO mostró mensaje de validación al dejarse vacía, pese a ser un campo que define el circuito completo de la cirugía. Podría ser una omisión real de la validación, o depender de otro campo no identificado.

Formulario cerrado sin cargar ni confirmar ningún dato — sigue en estado "ANULADA", sin registro creado.

### 3. Formato de salida real del informe "Parte Qx Diario"
Como no había ninguna cirugía cargada en el efector (Lista de Espera, Cirugías c/Turno e Informe de Producción mostraron 0 resultados en ambos circuitos), se probó igual con la fecha del día (14/09/2026) para confirmar el **formato de salida**, ya que el objetivo era documentar el mecanismo, no el contenido.

Resultado: el botón **Imprimir** del modal **no descarga ningún archivo**. Abre una **pestaña nueva** hacia `http://192.168.4.24/mihospital/quirofano/informeParte` — una página HTML con formato de reporte (logo, título "PARTE QUIRÚRGICO DIARIO", fecha, tabla de cirugías del día) pensada para imprimirse con el propio diálogo del navegador (Ctrl+P), no un PDF generado por el servidor. Con la fecha usada, la tabla mostró "Sin Cirugías" (0 registros ese día, consistente con lo observado en Lista de Espera/Cirugías c/Turno).

🟡 **Hallazgo menor:** el pie de la página del informe muestra un texto de depuración con el **hostname interno del servidor** ("Host: mihospitalheep ()" o similar) — información técnica que no debería quedar expuesta en un documento pensado para imprimirse/compartirse. Vale la pena reportarlo a Sectorial Informática junto con el hallazgo de Laboratorios (error 500 con stack trace).

No se probaron los otros dos modales (Parte de Enfermería, Cx c/Fecha Probable) porque comparten exactamente la misma estructura (campo Fecha + Cancelar/Imprimir) — se asume el mismo mecanismo de salida (página HTML imprimible, sin descarga).

## Continuación 2026-09-14 (3) — Profundización de "Roles y permisos" sin nuevo login

No se consiguió usuario no-administrador ni se intentó de nuevo buscar una pantalla de gestión de usuarios (ya descartada en la sesión anterior). En su lugar se ordenó y explicitó, en el manual (sección 14), todo lo que **ya estaba relevado pero disperso** sobre el modelo de roles del sistema, sin loguearse de nuevo:

- Perfil de usuario (`/mihospital/home/configuracion/usuario/home`) no tiene selector de rol, solo Nombre/Usuario de solo lectura + "Cambiar Contraseña" — confirma que la asignación de rol no es autogestionable desde ahí tampoco.
- El texto "Alertas para el usuario SA - Administrador, Usuario" (Quirófano → Inicio) es el único lugar del sistema donde se ve el rol de la persona logueada renderizado en pantalla.
- Se aclaró explícitamente en el manual que "Roles/Profesionales" (Quirófano → Configuración) es un concepto distinto (roles del equipo quirúrgico en una cirugía, ej. Cirujano/Anestesista/Instrumentador) y no debe confundirse con roles de acceso al sistema.
- Conclusión sin cambios respecto a la sesión anterior: sigue sin poder documentarse con certeza qué ve un usuario no-administrador; el manual ahora deja explícito qué haría falta para resolverlo (credenciales de un usuario existente, o gestión vía Sectorial Informática).

## Continuación 2026-09-14 (4) — Profundización de otras secciones del manual (sin nuevo login)

Berenice pidió seguir profundizando otras secciones. Se revisó todo lo ya relevado en este documento buscando detalle que no había llegado al manual final, y se agregó:

- **Mapa técnico (nueva sección 7.1):** tabla de URL por pantalla, tomada del "Mapa de navegación completo (confirmado vía DOM)" de más arriba en este documento — no estaba volcada al manual final.
- **Salas del Efector:** se agregó la lista real de salas del efector (Cuidados Intermedios, Emergencias, Hospital de Día, Hospital Modular, Internación Domiciliaria, Neonatología, Pediatría, Tocoginecología, UCI) — ya estaba en este documento, faltaba en el manual.
- **Consultorios → Profesionales:** se agregó el dato de paginación (161 páginas) que estaba en este documento pero no en el manual.
- **Caso de uso nuevo:** "Cargar una Nueva Cirugía" paso a paso en la sección de Quirófano, armado con los campos obligatorios ya confirmados (no se cargó ninguna cirugía real).
- **Errores frecuentes:** se separó como hallazgo aparte la exposición de la consulta SQL completa y la ruta de servidor (`/home/sectorial/git/mihospital/...`) en el error de Laboratorios — antes solo se mencionaba la columna faltante, no la exposición de información técnica. Se agregó también como fila el hallazgo de Red Salud (Usuario/Nodo/Efector vacíos), que ya estaba documentado en la sección 9 pero no en la tabla de errores.
- **Glosario:** se agregaron términos ya usados en el manual pero no definidos: "ANULADA" (estado), SICAP, Oviyam, Código de Establecimiento, Sectorial Informática, Migas de pan.
- **Preguntas frecuentes:** se agregaron dos preguntas nuevas (confiabilidad de Red Salud, exposición de datos técnicos en errores).
- 🔴 **Importante — se encontraron 2 respuestas del FAQ del Artifact desactualizadas:** "¿Qué campos son obligatorios en Nueva Cirugía?" y "¿Cómo exporto un listado a Excel o PDF?" seguían con el texto de ANTES de las verificaciones del 14/09 (decían "no se confirmó con certeza"), mientras que el manual `.md` ya tenía la respuesta verificada. Se corrigieron en el Artifact para que coincidan. **Lección:** al actualizar el manual `.md`, no asumir que el Artifact publicado está sincronizado — revisar también el FAQ y otras secciones "resumen" que puedan repetir contenido desactualizado.
- Nota técnica: el archivo HTML del Artifact en la carpeta `tool-results` del proyecto (cache de sesión) no se pudo editar directamente (bloqueado por el clasificador de permisos). Solución: copiarlo al scratchpad de la sesión, editarlo ahí, y publicar desde esa copia.

No se hizo ningún login nuevo ni se tocó nada en el sistema real — todo el trabajo fue de documentación a partir de lo ya relevado.
