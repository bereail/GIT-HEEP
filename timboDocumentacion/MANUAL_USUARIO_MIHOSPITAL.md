# MANUAL DE USUARIO — MIHOSPITAL

**Sistema de Salud Hospitalario miHospital**
Gobierno de Santa Fe — Ministerio de Salud
Sectorial Informática — Ministerio de Salud

---

## 0. Portada

| | |
|---|---|
| Sistema | miHospital (Sistema de Salud Hospitalario) |
| Organismo | Gobierno de Santa Fe — Ministerio de Salud |
| Versión de sistema relevada | 26.5.6 |
| Instancia relevada | Ambiente de pruebas/staging (según confirmación del solicitante) — `192.168.4.24` |
| Establecimiento activo durante el relevamiento | HOSP EVA PERON |
| Usuario utilizado | `sa` — rol observado: **Administrador** |
| Fecha de relevamiento | 03/09/2026 |
| Autor | Relevamiento asistido — Claude Code |

---

## 1. Objetivo del manual

Este manual explica, paso a paso y sin dar por sabido nada, cómo usar el sistema **miHospital**. Está pensado para que una persona que **nunca usó el sistema** pueda:

- Entender qué hace cada módulo.
- Saber en qué menú encontrar cada función.
- Completar las tareas más comunes (buscar un paciente, ver una internación, gestionar turnos, cargar una cirugía, etc.).
- Reconocer los mensajes de error más frecuentes y saber qué hacer.

## 2. Alcance

El manual cubre los **5 módulos habilitados** en el efector relevado (HOSP EVA PERON):

- **Pacientes**
- **Consultorios**
- **Internaciones** (nombre interno del sistema: "Epicrisis")
- **Quirófano**
- **Administración** (configuración general del sistema para el efector)

También se documenta el enlace a **Red Salud** (Red Provincial de Salud), que es una integración externa.

No se cubren funcionalidades de otros efectores, ni módulos que pudieran habilitarse a futuro. Este manual describe **lo que se pudo observar y comprobar** durante el relevamiento; no incluye nada que no haya sido verificado en pantalla.

## 3. Recomendaciones de uso

- 🟡 El sistema maneja información de salud de pacientes reales. Varias pantallas (buscador de pacientes, listado de internaciones, listado de diagnósticos) muestran **nombre completo, DNI, fecha de nacimiento y diagnóstico** apenas se hace una búsqueda. Evitá dejar estas pantallas abiertas o visibles a personas sin autorización, y cerrá sesión cuando termines.
- 🟡 El usuario `sa` observado corresponde a un perfil de **Administrador**, con acceso a todos los módulos y a la configuración del sistema. En el uso diario, cada persona debería trabajar con su propio usuario y no con una cuenta administrativa compartida.
- 🔴 Hay botones y acciones que **modifican configuración crítica del sistema** (por ejemplo, desactivar un módulo, o crear el esquema de controles/permisos en la base de datos). Estas acciones están señaladas con 🔴 en este manual y **no deberían usarse sin saber exactamente qué hacen**.
- 🟢 La mayoría de las pantallas de búsqueda muestran una ayuda en letra chica: *"Si se obtuvieron muchos resultados, usar la combinación Ctrl+F y luego Enter, para buscar entre las coincidencias"*. Es el buscador del propio navegador, útil cuando una lista es muy larga.

## 4. Acceso al sistema

1. Abrir el navegador e ingresar a la dirección del sistema (en el efector relevado: `http://192.168.4.24/mihospital/home`; en cada efector la URL puede variar).
2. En la pantalla de inicio de sesión completar:
   - **Usuario** (campo con ícono de persona).
   - **Contraseña** (campo con ícono de candado).
3. Presionar **"Iniciar Sesión"**.
4. Si los datos son correctos, el sistema muestra la pantalla de **Inicio** con el nombre del establecimiento activo en la esquina superior derecha (por ejemplo, `[HOSP EVA PERON]`).

Al pie de la pantalla de login figura el contacto de soporte técnico ("Mesa de ayuda") y la versión del sistema.

**🟡 Importante:** por motivos de seguridad, este manual no debe usarse como referencia para compartir o escribir contraseñas de otras personas. Cada usuario debe ingresar su propia contraseña.

## 5. Conceptos básicos

| Término | Explicación |
|---|---|
| **Efector** | El establecimiento de salud (hospital, centro de salud) sobre el que se está trabajando. Aparece indicado arriba a la derecha entre corchetes, ej. `[HOSP EVA PERON]`. |
| **H.C.** | Historia Clínica. Es el número único que identifica a un paciente dentro del sistema. |
| **Ficha del Paciente** | Pantalla central de datos de un paciente, con pestañas para ver sus datos personales, internaciones, turnos, cirugías, laboratorios, farmacia y compras. |
| **Sala** | Unidad de internación del hospital (ej. Emergencias, Pediatría, Terapia Intensiva). Cada sala se divide en habitaciones y camas. |
| **CIE-10** | Clasificación Internacional de Enfermedades (10ª versión). Catálogo estándar de códigos de diagnóstico usado en toda la historia clínica. |
| **Nomenclador de Cirugías** | Catálogo estándar de procedimientos quirúrgicos con su código. |
| **RPS / Red Salud** | Red Provincial de Salud: integración con el sistema provincial que permite compartir información entre efectores. |

## 6. Interfaz general

La pantalla del sistema se organiza siempre igual:

- **Barra superior azul:** a la izquierda, el botón ☰ para desplegar/contraer el menú lateral y el logo de miHospital; a la derecha, tres íconos: 🔔 notificaciones, ✉️ mensajes, y 👤 el usuario conectado (con menú para **Cambiar Contraseña** y **Cerrar Sesión**).
- **Menú lateral (izquierda):** lista de módulos disponibles. Se puede mostrar expandido (con texto) o contraído (solo íconos) con el botón ☰.
- **Ruta de navegación ("migas de pan"):** arriba del contenido, muestra dónde estás parado dentro del sistema (ej. `miHospital > Módulo Pacientes > Buscador de Pacientes`).
- **Contenido central:** cambia según el módulo y la pantalla.
- **Pie de página:** datos de la Sectorial Informática del Ministerio de Salud y versión del sistema.

## 7. Mapa de navegación

```
MIHOSPITAL
│
├── Menú Principal (Inicio)
│    └── 4 accesos directos: Pacientes / Consultorios / Internaciones / Quirófano
│    └── Accesos Externos: Red Provincial de Salud
│
├── Pacientes
│    ├── Inicio (buscador rápido + altas del día)
│    ├── Pacientes (buscador/listado completo)
│    └── Altas del día
│
├── Consultorios
│    ├── Inicio
│    ├── Turnos
│    └── Conf. Edilicia
│         ├── Profesionales
│         └── Consultorios
│
├── Internaciones
│    ├── Inicio (tablero con indicadores)
│    ├── Salas
│    │    └── [Sala] → Habitaciones → Camas
│    ├── Internaciones (listado histórico)
│    ├── Diagnósticos (listado histórico)
│    └── Nomencladores
│         ├── CIE-10
│         └── Cirugías
│
├── Quirófano
│    ├── Inicio (alertas y accesos)
│    ├── Cirugías
│    │    ├── Lista de Espera
│    │    ├── Cirugías c/Turno
│    │    └── Nueva Cirugía
│    ├── Informes
│    │    ├── Parte Qx Diario
│    │    ├── Parte de Enfermería
│    │    ├── Cx c/Fecha Probable
│    │    └── Producción
│    └── Nomenclador (procedimientos)
│
├── Red Salud (enlace externo a la Red Provincial de Salud)
│
└── Administración
     ├── Módulos Habilitados
     ├── Compatibilidad Informes Diagnose / Acceso PACS
     ├── RPS (parámetros de conexión a Red Provincial de Salud)
     ├── Plantillas de Informes
     └── 🔴 Crear esquema de controles/permisos
```

Cada módulo, además del menú lateral, tiene en la pantalla de Inicio una **tarjeta con un desplegable "Secciones ▾"** que da acceso directo a sus pantallas principales.

### 7.1 Mapa técnico (URLs por pantalla)

Referencia técnica para quien administre o dé soporte al sistema (Sectorial Informática, o para armar accesos directos). Las URLs corresponden a la instancia relevada (`192.168.4.24`); en otro efector el dominio cambia pero la ruta (después de `/mihospital`) debería ser igual.

| Módulo | Pantalla | URL |
|---|---|---|
| General | Menú Principal | `/mihospital/home` |
| Pacientes | Inicio | `/mihospital/panel/pacientes/home` |
| Pacientes | Pacientes (buscador/listado) | `/mihospital/panel/pacientes/listado` |
| Pacientes | Altas del día | `/mihospital/panel/pacientes/altas-dia` |
| Consultorios | Inicio | `/mihospital/consultorio` |
| Consultorios | Turnos | `/mihospital/consultorio/turnosDetalle` |
| Consultorios | Profesionales | `/mihospital/consultorio/profesionales` |
| Consultorios | Consultorios | `/mihospital/consultorio/consultorios` |
| Internaciones | Inicio | `/mihospital/epicrisis` |
| Internaciones | Salas | `/mihospital/epicrisis/navSalas` |
| Internaciones | Internaciones | `/mihospital/epicrisis/navInternaciones` |
| Internaciones | Diagnósticos | `/mihospital/epicrisis/navDiagnosticos` |
| Internaciones | Nomenclador CIE-10 | `/mihospital/epicrisis/navCie10` |
| Internaciones | Nomenclador Cirugías | `/mihospital/epicrisis/navOperaciones` |
| Quirófano | Inicio | `/mihospital/quirofano` |
| Quirófano | Lista de Espera | `/mihospital/quirofano/cirugiasEspera` |
| Quirófano | Cirugías c/Turno | `/mihospital/quirofano/cirugias` |
| Quirófano | Nueva Cirugía | `/mihospital/quirofano/cirugiaCabeTrn/INS/0/-/noMsg/principal` |
| Quirófano | Parte Qx Diario (salida imprimible) | `/mihospital/quirofano/informeParte` |
| Quirófano | Producción | `/mihospital/quirofano/informe/cirugiasProduccion` |
| Quirófano | Nomenclador (procedimientos) | `/mihospital/quirofano/procedimientos` |
| Quirófano | Configuración | `/mihospital/quirofano/configuracion/configuraciones` |
| Administración | Pantalla principal | `/mihospital/home/configuracion/configuraciones` |
| Administración | Módulos Habilitados | `/mihospital/home/configuracion/configuracionModulos` |
| Administración | Compatibilidad Informes/PACS | `/mihospital/home/configuracion/configuracionInformes` |
| Administración | RPS | `/mihospital/home/configuracion/configuracionRPS` |
| Administración | Plantillas de Informes | `/mihospital/home/configuracion/configuracionPlantillas` |
| Administración | 🔴 Crear esquema de controles/permisos | `/mihospital/home/configuracion/sysConfiguracionFixture` |
| Red Salud | Buscador SICAP (externo) | `https://www.santafe.gov.ar/sicap56/cap/includes/seguimiento_paciente/seguimiento.php` |
| General | Perfil de usuario / Cambiar Contraseña | `/mihospital/home/configuracion/usuario/home` |
| General | Cerrar sesión | `/mihospital/home/logout` |
| General | Notificaciones | `/mihospital/home/novedades?tipo=Notificaciones` |
| General | Mensajes | `/mihospital/home/novedades?tipo=Mensajes` |

---

## 8. Módulos

### 8.1 Pacientes

#### ¿Para qué sirve?
Permite buscar pacientes ya registrados en el hospital y ver toda su información: datos personales, internaciones, turnos, cirugías, estudios de laboratorio, entregas de farmacia y compras asociadas.

#### ¿Quién debería utilizarlo?
Personal administrativo, de admisión, y profesionales de la salud que necesiten consultar la ficha de un paciente.

#### ¿Cómo acceder?
Menú lateral → **Pacientes**. Se despliegan tres opciones: Inicio, Pacientes, Altas del día.

#### Pantalla principal (Inicio del módulo)
Dos paneles:
- **Buscador de Pacientes**: campo de texto único para buscar.
- **Altas del día**: selector de fecha (por defecto hoy) para ver los pacientes dados de alta ese día.

#### Campos — Buscador de Pacientes

| Campo | Tipo | Obligatorio | ¿Para qué sirve? | Ejemplo |
|---|---|---|---|---|
| Buscar por Nombre/Apellido/Documento/H.C. | Texto libre | Sí (mínimo aprox. 3 caracteres) | Busca coincidencias parciales en nombre, apellido, número de documento o número de historia clínica | `Perez`, `30123456`, `1000001` |

Al ampliar filtros (ícono de embudo) se agregan campos de búsqueda más específicos: Apellido, Nombre, Nro. Documento, Nro. H.C., Sexo, Fecha de Nacimiento, Tipo de H.C. y Activo/Inactivo.

#### Botones

| Botón | Acción | Resultado |
|---|---|---|
| 🔍 (lupa) | Ejecuta la búsqueda | Muestra la tabla de resultados |
| Desplegar más filtros (embudo) | Abre búsqueda avanzada | Aparecen campos adicionales de filtro |

#### Resultado de la búsqueda
Tabla con columnas: **Nombre, Nro. Documento, Fecha Nac., Sexo, Nro. H.C., Obra Social**. Cada fila es un enlace que lleva a la Ficha del Paciente.

🟡 **Importante:** una búsqueda muy amplia (por ejemplo, 3 letras comunes) puede devolver **decenas de miles de resultados** y tardar varios segundos. Se recomienda buscar por apellido y nombre completos, o directamente por documento, para obtener resultados rápidos y precisos.

#### Procedimiento paso a paso — Buscar un paciente
1. Ir a **Pacientes → Pacientes** (o usar el buscador de la pantalla de Inicio).
2. Escribir un criterio de búsqueda específico (apellido completo, o número de documento).
3. Presionar Enter o el botón de lupa.
4. Esperar a que la tabla muestre los resultados (aparece un cartel "Procesando..." mientras busca).
5. Hacer clic en el nombre del paciente deseado para abrir su ficha.

#### Ficha del Paciente

Al abrir un paciente aparece la pantalla **"Ficha del Paciente"**, con:

- **Panel izquierdo fijo:** Nombre, N° de Historia Clínica (H.C.), DNI, Fecha de nacimiento (con edad calculada), Sexo, Obra Social, botón **"Pulsera Ident."** (para imprimir la pulsera identificatoria del paciente), y datos de Contacto (Domicilio, Teléfono, Celular, Centro de Salud de Referencia).
- **Pestañas** (panel derecho):

| Pestaña | Contenido |
|---|---|
| Datos Personales | Ficha completa: datos del paciente + datos de la madre/padre (tutor) |
| Internaciones | Historial de internaciones del paciente |
| Guardia | Atenciones de guardia |
| Turnos C.E. | Turnos de consultorio externo, con filtro por Especialidad y por rango de fechas (Desde/Hasta) |
| Cirugías | Cirugías realizadas o programadas |
| Laboratorios | Órdenes y resultados de laboratorio — 🔴 **ver Errores frecuentes, sección 12** |
| Farmacia | Entregas de medicación/insumos al paciente |
| Compras | Compras asociadas al paciente |

Cuando una pestaña no tiene información, el sistema muestra un mensaje como *"Sin Internaciones Registradas"*, *"Sin Cirugías Registradas"*, etc.

#### Mensajes y estados
- *"Por favor, ingresar un criterio de búsqueda."* → el buscador está vacío.
- *"Procesando..."* → la búsqueda está en curso.
- *"Sin [Internaciones/Cirugías/Compras/Entregas] Registradas"* → la pestaña no tiene datos para ese paciente.

#### Altas del día
Pantalla separada (**Pacientes → Altas del día**) que lista los pacientes dados de alta en una fecha determinada. Filtro: **Fecha** (por defecto, la fecha actual). Tabla: Nombre, Nro. Documento, Fecha Nac., Nro. H.C., Obra Social, Fecha/Hora Alta, Usuario Alta (qué usuario registró el alta).

---

### 8.2 Consultorios

#### ¿Para qué sirve?
Gestiona los turnos de consultorio externo, el listado de profesionales del efector y la agenda de consultorios (qué profesional atiende en qué consultorio, qué día y en qué horario).

#### ¿Quién debería utilizarlo?
Personal administrativo de turnos y de gestión de consultorios externos.

#### ¿Cómo acceder?
Menú lateral → **Consultorios**. Opciones: Inicio, Turnos, Conf. Edilicia (Profesionales, Consultorios).

#### Pantalla principal (Inicio)
Panel "Accesos" con cuatro bloques: **Turnos**, **Conf. Edilicia**, **Profesionales**, **Consultorios**.

#### Turnos — pantalla "Turnos del Efector"

**Campos y búsqueda:**

| Campo | Tipo | Obligatorio | ¿Para qué sirve? |
|---|---|---|---|
| Buscar por Nombre/Apellido/Documento | Texto libre | No | Filtra los turnos por el paciente |
| Filtro avanzado (ícono embudo) | — | No | Filtros adicionales |

**Botones:**

| Botón | Acción | Resultado |
|---|---|---|
| REFRESCAR | Activa/actualiza el refresco automático de la lista | La tabla se actualiza sin recargar la página |
| 🔍 | Ejecuta la búsqueda | Filtra la tabla |

**Tabla de resultados:** ID, Fecha, Hora, Paciente (H.C.), Documento, Presentismo, Especialidad, Estudio, Profesional, Tipo, Pedido.

Cuando no hay turnos: *"Sin Registros Encontrados"*.

#### Profesionales — pantalla "Profesionales del Efector"
Listado completo del personal profesional registrado (1.621 registros en el relevamiento). Es una grilla de tipo planilla, con herramientas de exportación:

| Botón | Acción |
|---|---|
| Copiar | Copia la tabla visible al portapapeles |
| CSV | Descarga la tabla en formato CSV |
| Excel | Descarga la tabla en formato Excel |
| PDF | Descarga la tabla en formato PDF |
| Imprimir | Abre el diálogo de impresión |
| Mostrar/Ocultar Columnas | Permite elegir qué columnas se ven |

**Tabla:** Nombre, Matrícula, Especialidad Ppal., Consultorios Habilitados. Con buscador simple y paginado (selector de cantidad de registros por página; en el relevamiento, 1.621 registros repartidos en 161 páginas con la paginación por defecto).

#### Consultorios — pantalla "Consultorios del Efector"
Muestra la agenda de consultorios por profesional. **Filtros:** Especialidad, Profesional, Día, C.E. (todos desplegables, combinables). **Tabla:** Especialidad, Profesional, Día, Horario, Tipo (ej. "Turnos Especiales", "Sin Consultorio").

#### Configuración del módulo
Menú lateral → engranaje ⚙ dentro de Consultorios → **Configuraciones**: por ahora solo incluye "Plantillas de Informes".

#### Caso de uso: Consultar la agenda de un profesional
**Objetivo:** saber qué días y horarios atiende un profesional determinado.
**Requisitos previos:** conocer el nombre del profesional (o su especialidad).
**Pasos:**
1. Ir a **Consultorios → Conf. Edilicia → Consultorios**.
2. Seleccionar el profesional en el filtro "Profesional" (o filtrar por Especialidad).
3. Revisar la tabla resultante: día, horario y tipo de atención.
**Resultado esperado:** la grilla muestra todas las franjas horarias asignadas a ese profesional.
**Problemas frecuentes:** si el profesional no tiene consultorio asignado, la columna "Tipo" muestra "Sin Consultorio".

---

### 8.3 Internaciones

*(en el sistema, internamente, este módulo se llama "Epicrisis")*

#### ¿Para qué sirve?
Es el módulo de gestión de camas y pacientes internados: muestra la ocupación de salas en tiempo real, el listado de internaciones activas e históricas, el registro de diagnósticos y los catálogos (nomencladores) de diagnóstico (CIE-10) y de cirugías.

#### ¿Quién debería utilizarlo?
Personal de enfermería, administración de camas, estadística/epidemiología y dirección médica.

#### ¿Cómo acceder?
Menú lateral → **Internaciones**.

#### Pantalla principal (Inicio) — Tablero
Al entrar se ve un **tablero (dashboard)** con:
- **Accesos:** Salas, Internaciones, Diagnósticos, Nomencladores (CIE-10, Cirugías).
- **Internaciones Pendientes:** gráfico de barras con la cantidad de internaciones sin cierre por sala/servicio (ej. Emergencia-Urgencias, Hospital de Día, Clínica Médica, Traumatología, etc.).
- **Ocupación total de Camas:** total de camas, camas disponibles, % de ocupación, y desglose en Ocupadas / Reservadas / En Reparación / Fuera de Servicio / Libres.
- **Ranking de Diagnósticos según estación del año:** cuatro columnas (Primavera, Verano, Otoño, Invierno) con los diagnósticos más frecuentes de cada temporada y su cantidad de casos.

Este tablero es útil para tener una foto rápida del estado del hospital sin tener que entrar a cada sala.

#### Salas — pantalla "Salas del Efector"
**Tabla:** Sala, Total/Disponibles, Ocupadas, Libres, Reservadas, En Reparación, Fuera de Servicio, Acciones. Fórmula indicada al pie: *Disponibles = Ocupadas + Libres + Reservadas*.

Salas observadas en el efector relevado (HOSP EVA PERON): Cuidados Intermedios, Emergencias, Hospital de Día, Hospital Modular, Internación Domiciliaria, Neonatología, Pediatría, Tocoginecología, Unidad de Cuidados Intensivos. 🟡 Esta lista es específica de este efector — cada hospital configura sus propias salas.

Botón **"Ingresar"** en cada fila lleva al detalle de esa sala.

##### Detalle de una Sala
Vistas disponibles: **Ver Listado**, **Ver Grilla**, **Reporte Diario (Pase de Sala)**. Filtro: **Sólo Disponibles / Mostrar todas**.
El contenido se agrupa por **Habitación**, y cada habitación tiene una tabla de camas: **Cama, Estado, Paciente, Sexo, Ingreso, Diag. presuntivo, Días estada, Acciones**.

🟡 **Importante:** esta pantalla puede mostrar el nombre y el diagnóstico presuntivo del paciente en cada cama ocupada. Es información clínica sensible — no debe quedar visible en pantallas compartidas o proyectores.

#### Internaciones (listado histórico)
Pantalla **"Internaciones"**, con buscador (Nombre/Apellido/Documento), filtro adicional, y un interruptor **"Vista Detallada / Totales"**.
**Tabla:** Ingreso, Sala, Habitación, N° Doc., Nombre, Diag. Presuntivo, Egreso, Diag. Principal, Acciones (**"Continuar"** = la internación sigue abierta).

#### Diagnósticos (listado histórico)
Pantalla **"Diagnósticos"**, mismo patrón de búsqueda/filtro/Vista Detallada-Totales.
**Tabla:** Diagnóstico, Tipo de Diagnóstico (Principal / Parcial N°1 / Parcial N°2...), Ingreso, Egreso, Sala, Nro. Doc., Nombre, Edad, Acciones.

#### Nomenclador CIE-10
Catálogo de diagnósticos estándar. Búsqueda por Código o Descripción (obligatoria para ver resultados). No contiene datos de pacientes — es información de referencia.

**Ejemplo de uso:** buscar "diabetes" devuelve todos los códigos relacionados (E10 a E14 con sus variantes, O24 —diabetes en el embarazo—, P70 —diabetes neonatal—, etc.), cada uno con su código y descripción oficial.

#### Nomenclador de Cirugías (provincial)
Mismo patrón que el CIE-10: búsqueda por Código/Descripción, catálogo institucional de procedimientos.

#### Caso de uso: Ver la ocupación de una sala específica
**Objetivo:** saber cuántas camas libres hay en una sala antes de decidir una internación.
**Requisitos previos:** ninguno.
**Pasos:**
1. Ir a **Internaciones → Salas**.
2. Ubicar la sala en la tabla y revisar la columna "Libres".
3. Si se necesita el detalle cama por cama, presionar "Ingresar" en esa fila.
**Resultado esperado:** se ve la cantidad exacta de camas libres, ocupadas, reservadas y fuera de servicio.
**Problemas frecuentes:** una sala puede tener camas "Fuera de Servicio" que reducen la disponibilidad real aunque figuren en el total.

---

### 8.4 Quirófano

#### ¿Para qué sirve?
Gestiona todo el circuito de cirugías: lista de espera, cirugías con turno asignado, carga de una nueva cirugía, informes (parte diario, parte de enfermería, producción) y el nomenclador de procedimientos quirúrgicos.

#### ¿Quién debería utilizarlo?
Personal de quirófano, cirujanos, anestesistas, enfermería quirúrgica y administración de quirófano.

#### ¿Cómo acceder?
Menú lateral → **Quirófano**.

#### Pantalla principal (Inicio)
- **Accesos:** Cirugías (Lista de Espera, Cirugías c/Turno, Nueva Cirugía), Informes (Parte Qx Diario, Cx c/Fecha Probable, Parte de Enfermería, Producción), Nomenclador.
- **Alertas para el usuario [usuario] - [Rol]:** tarjetas de alerta personal (ej. "Cirugías sin Cerrar", "Cirugías en espera sin turno", "Cirugías con Evaluación PreQx próxima a vencer", "Cirugías cercanas a su fecha de espera máx.", "Cirugías sin protocolo con turno en el pasado"), cada una con botón "Ver Detalle".
- **Alertas (generales del efector):** mismo tipo de tarjetas, pero a nivel de todo el efector, no solo del usuario logueado.

Cada tarjeta de alerta muestra un número: si es 0, no hay pendientes de ese tipo.

🟢 Esta pantalla de Inicio funciona como un **panel de control diario** para el equipo de quirófano: de un vistazo se ve qué cirugías requieren atención.

#### Cirugías — Lista de Espera / Cirugías c/Turno
Ambas pantallas comparten estructura: dos pestañas superiores, **"Quirófanos Centrales"** y **"Quirófanos Hosp Día"** (el sistema separa la gestión según el circuito quirúrgico), buscador por Nombre/Apellido/Documento y filtro adicional.
"Cirugías c/Turno" además ofrece dos vistas: **Lista** y **Calendario**.
Mensaje cuando no hay pendientes: *"Sin Cirugías Pendientes - Por favor ingrese un filtro de búsqueda o cargue una nueva."*

#### Nueva Cirugía — formulario completo

Pantalla **"Ficha de la Cirugía"** (aparece con la etiqueta "NUEVA CIRUGÍA" y el estado "ANULADA" hasta que se completa y confirma).

**Sección "Definir Cirugía":**

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| Inicio Proceso | Automático | — | Fecha/hora de creación del registro, la completa el sistema |
| Fecha Pedido | Fecha | **Sí** | Fecha en que se solicita la cirugía |
| Fecha Probable | Fecha | No | Fecha estimada de realización |
| Hora Probable | Hora | No | Hora estimada |
| Tipo de Cirugía | Combo (Programada / Urgencia) | **Sí** | Clasifica la urgencia de la cirugía |
| Oncológica | Combo (Sí / No) | **Sí** | Indica si es una cirugía oncológica |
| Tipo de PreQx | Combo (valor por defecto: Prequirúrgico) | No (trae valor por defecto) | Etapa del proceso prequirúrgico |
| Área Quirúrgica | Combo (Quirófanos Centrales / Quirófanos Hosp Día) | No* | Circuito donde se realizará |
| Paciente | Buscador | **Sí** | Selecciona el paciente (mismo buscador que el módulo Pacientes) |
| Celular / Tel. Fijo de Contacto | Texto (con código de área) | No | Datos de contacto |
| Procedencia - Sub-Sector | Combo (Ambulatorio, Guardia, Internación, Cama en UTI/UCO/UCBC/UCIM/RCV, Derivación) | **Sí** | De dónde proviene el paciente |
| Mail de Contacto | Texto | No | — |
| Cirujano | Combo | **Sí** | Profesional a cargo |
| Diagnóstico Presuntivo | Buscador (CIE-10) | **Sí** | — |
| Diagnóstico a imprimir | Texto libre | **Sí** | Texto que aparecerá impreso en la orden |
| Procedimiento Quirúrgico Presuntivo | Buscador (nomenclador) | **Sí** | — |
| Procedimiento a imprimir | Texto libre | **Sí** | — |
| Especialidad | Combo (Cirugía Cardíaca, Clínica Quirúrgica-Cirugía General, ORL, Gastroenterología, Neumonología, Neurocirugía, Tocoginecología, Traumatología, Urología Pediátrica, entre otras) | **Sí** | — |
| Observaciones | Texto libre | No | — |

\* Área Quirúrgica no mostró mensaje de validación al dejarla vacía — llamativo tratándose de un campo que define el circuito de quirófano; podría depender de otro campo o ser una omisión de la validación en esta versión.

**Sección "Datos Presuntivos":**

| Campo | Obligatorio |
|---|---|
| Tipo Anestesia (Bloqueo, General, Local, Raquídea, Regional, Sedación, Peridural, Plexual, Intubación Selectiva, Sin anestesia) | **Sí** |
| Destino post-quirúrgico (Ambulatorio, Internación, Cama en UTI/UCO/UCBC/UCIM/RCV, Morgue) | **Sí** |
| Requiere Diagnóstico por Imágenes (Sí/No) | **Sí** |
| Requiere Hemoterapia (Sí/No) | **Sí** |
| Requiere Torre de Laparoscopía (Sí/No) | **Sí** |
| Requiere Materiales Especiales (Sí/No) | **Sí** |
| Tiempo Estimado de Cirugía (de 1 a 8 horas) | **Sí** |
| Días de Post-Operatorio estimados (de 0 a "más de 28") | **Sí** |
| Ropa a Utilizar | No |
| Cajas a Utilizar | No |

**Sección "Asignación de Prioridades":** Score (puntaje de 0 a 10) y Fecha de Espera Máxima — ambos opcionales.

**Botones finales:** **Cancelar** / **Confirmar**.

🟢 **Campos obligatorios confirmados sin generar un registro real:** se presionó "Confirmar" con el formulario completamente vacío. El sistema no guardó nada — en cambio, mostró un mensaje de validación en letra naranja debajo de cada campo faltante (ej. "Seleccione un paciente", "Ingrese la Fecha de Pedido de Cirugía"). Se leyeron esos mensajes para completar la columna "Obligatorio" de arriba, sin cargar ni confirmar ningún dato. 19 de los ~28 campos del formulario resultaron obligatorios.

#### Caso de uso: Cargar una Nueva Cirugía
**Objetivo:** dejar registrada una cirugía en lista de espera con todos los datos obligatorios.
**Requisitos previos:** conocer el paciente (buscarlo por nombre/documento), el cirujano asignado, el diagnóstico presuntivo (código CIE-10) y el procedimiento quirúrgico presuntivo.
**Pasos:**
1. Ir a **Quirófano → Cirugías → Nueva Cirugía** (o el acceso directo "Nueva Cirugía" en la tarjeta de Inicio).
2. En "Definir Cirugía", completar como mínimo los campos obligatorios: Fecha Pedido, Tipo de Cirugía, Oncológica, Paciente, Procedencia-Sub-Sector, Cirujano, Diagnóstico Presuntivo, Diagnóstico a imprimir, Procedimiento Quirúrgico Presuntivo, Procedimiento a imprimir y Especialidad.
3. En "Datos Presuntivos", completar Tipo Anestesia, Destino, los cuatro campos Sí/No de requerimientos (Diag. por Imágenes, Hemoterapia, Torre Laparoscopia, Materiales Especiales), Tiempo Estimado de Cirugía y Días de Post-Operatorio.
4. Opcionalmente completar "Asignación de Prioridades" (Score, Fecha de Espera Máxima) si se conoce la urgencia relativa del caso.
5. Presionar **Confirmar**.
**Resultado esperado:** la cirugía pasa a figurar en **Lista de Espera** (o en **Cirugías c/Turno** si además se asignó fecha/turno), dejando de estar en estado "ANULADA".
**Problemas frecuentes:** si falta algún campo obligatorio, el sistema muestra un aviso naranja debajo de ese campo específico y no guarda nada — completar el campo señalado y volver a presionar Confirmar. 🟡 "Área Quirúrgica" no mostró aviso de obligatoriedad en las pruebas, pero conviene completarla igual porque define el circuito (Quirófanos Centrales / Hosp Día) de toda la cirugía.

#### Informes
Accesibles desde la pantalla de Inicio del módulo, sección "Informes":
- **Parte Qx Diario**: modal "Imprimir Parte Quirúrgico Diario". Campo **Fecha** (dd/mm/aaaa). Botones **Cancelar** / **Imprimir**.
- **Parte de Enfermería**: modal "Imprimir Parte de Enfermería". Misma estructura: campo **Fecha** + **Cancelar** / **Imprimir**.
- **Cx c/Fecha Probable**: modal "Imprimir Cirugías con Fecha Probable". Misma estructura: campo **Fecha** + **Cancelar** / **Imprimir**.
- **Producción**: pantalla propia (no modal). Búsqueda por Procedimiento/Diagnóstico principal. Tabla: Profesional, Total Prod., Total x Rol.

Los tres informes en modal comparten diseño: se elige una fecha y el botón **Imprimir** genera el documento para esa fecha puntual.

🟢 **Confirmado (con autorización explícita de Berenice):** "Imprimir" **no descarga ningún archivo**. Abre una **pestaña nueva** con una página HTML con formato de reporte (logo, título, fecha, tabla), pensada para imprimirse con el diálogo del propio navegador (Ctrl+P) — no genera un PDF en el servidor. Se probó con "Parte Qx Diario" y la fecha del día (no había cirugías cargadas en el efector, por lo que la tabla mostró "Sin Cirugías"; no se pudo ver el formato con datos reales). Se asume el mismo mecanismo para "Parte de Enfermería" y "Cx c/Fecha Probable", que comparten estructura idéntica de modal — no se probaron individualmente.

🟡 El pie de la página del informe expone un texto de depuración con el **hostname interno del servidor** — ver sección 12, Errores frecuentes.

#### Nomenclador (procedimientos)
**"Nomenclador Nacional de Cirugías"**: catálogo completo de procedimientos quirúrgicos con su código (ej. `08.05.24 - APENDICECTOMIA`), ordenado alfabéticamente por descripción. Se muestra completo sin necesidad de buscar, aunque también admite filtrar.

#### Configuración del módulo
Menú lateral → engranaje ⚙ dentro de Quirófano → **Configuraciones**, con los siguientes ítems:

| Ítem | Descripción |
|---|---|
| Alertas | Días de anticipación para cada tipo de alerta |
| Quirófanos | Salas de quirófano habilitadas en el efector |
| Roles/Profesionales | Profesionales que participan en cirugías y su rol |
| Plantillas de Informes | Plantillas de Consentimiento y Resumen Final |
| Días para Carga Diferida | Cuántos días hacia atrás se puede cargar un turno de cirugía ya pasado |
| Materiales/Insumos Habilitados | — |
| Especialidades Quirúrgicas habilitadas | — |
| Prefijos Habilitados (Nomenclador Nacional) | Qué códigos de cirugía están habilitados para el efector |
| Envío Automático de e-mails - Cambios de Estado | Notificaciones automáticas |
| Envío Automático de e-mails - Parte Quirúrgico Diario | Notificaciones automáticas |

#### Caso de uso: Consultar si un profesional tiene cirugías pendientes de cerrar
**Objetivo:** identificar cirugías realizadas que aún no fueron cerradas administrativamente.
**Requisitos previos:** haber iniciado sesión con un usuario que tenga cirugías asignadas.
**Pasos:**
1. Ir a **Quirófano** (pantalla de Inicio del módulo).
2. Revisar la tarjeta **"Cirugías sin Cerrar"** dentro de "Alertas para el usuario".
3. Si el número es mayor a 0, presionar **"Ver Detalle"**.
**Resultado esperado:** se abre el listado de esas cirugías pendientes.
**Problemas frecuentes:** si el número siempre da 0, verificar que el usuario tenga cirugías asignadas como cirujano.

---

### 8.5 Administración

#### ¿Para qué sirve?
Configuración general del sistema para el efector: qué módulos están activos, integración con PACS (imágenes médicas), conexión con la Red Provincial de Salud, plantillas de informes, y una herramienta técnica de inicialización de permisos.

#### ¿Quién debería utilizarlo?
Exclusivamente personal con **rol de Administrador** del sistema (en el relevamiento, el usuario `sa`).

#### ¿Cómo acceder?
Menú lateral → **Administración**.

#### Pantalla principal
Lista de accesos:

| Ítem | ¿Para qué sirve? |
|---|---|
| Módulos Habilitados | Ver y activar/desactivar los módulos del efector |
| Compatibilidad Informes Diagnose / Acceso PACS | Parámetros de conexión con el servidor PACS de imágenes y plantillas de informes de diagnóstico por imágenes |
| RPS | Parámetros de conexión a la Red Provincial de Salud |
| Plantillas de Informes | Plantillas generales de impresión (ej. pulsera del paciente internado) |
| 🔴 Crear esquema de controles/permisos | Herramienta técnica que crea tablas de permisos en la base de datos |

#### Módulos Habilitados
Tabla con los módulos activos del efector y, para cada uno, un botón **"Desactivar Módulo"**.

🔴 **CRÍTICO:** desactivar un módulo lo deja inaccesible para todos los usuarios del efector. **No debe usarse sin control**, ya que afecta la operación diaria del hospital. En este relevamiento **no se desactivó ningún módulo**. Los módulos observados activos fueron: Quirófano, Epicrisis (Internaciones), RPS, Paciente, Consultorio.

Botón **"+ Nuevo"**: permite habilitar un módulo adicional (no se probó, por prudencia).

#### Compatibilidad Informes Diagnose / Acceso PACS
Tabla de parámetros: **Url Prefijo Oviyam** (prefijo de URL para acceso al servidor PACS de imágenes). En el relevamiento figuraba **"Sin Definir"**. También incluye una sección de **Plantillas de Informes** de diagnóstico por imágenes.

#### RPS (Red Provincial de Salud)
Tabla de parámetros: **Código de Establecimiento**, **IP del Establecimiento** (dentro de la red del Ministerio), **URL de Logout** (a dónde redirigir al salir de la Red Provincial de Salud). En el relevamiento, los tres figuraban **"Sin Definir"**.

🟡 El sistema advierte en esta pantalla: *"El acceso a la Red Provincial de Salud debe ser gestionado por cada Efector, informando la IP del mismo dentro de la MAN a la [casilla de soporte]"*. Es decir, esta configuración la gestiona típicamente el área de sistemas de cada hospital junto con el Ministerio.

#### Plantillas de Informes (Administración)
Tabla con un ítem: **"Pulsera para el paciente internado"** — plantilla de impresión de la pulsera identificatoria. Figuraba **"Sin Definir"** en el relevamiento.

#### 🔴 Crear esquema de controles/permisos
Botón rojo que, según el texto en pantalla, *"Crea esquema de datos necesarios en esquema Compras - Tablas tProyectos, tForms y tControles. El proceso puede ejecutarse todas las veces que sea necesario sin afectar los permisos ya creados anteriormente"*.

**No se ejecutó esta acción durante el relevamiento**, ya que modifica el esquema de la base de datos y su alcance real no pudo verificarse sin ejecutarla — algo que este relevamiento evita por regla explícita de seguridad.

---

## 9. Red Salud (integración externa)

El acceso funcional es el botón **"RED PROVINCIAL DE SALUD"**, dentro de la tarjeta **"Accesos Externos"** de la pantalla de Inicio (`/mihospital/home`). El ítem "RED SALUD" del menú lateral colapsado solo muestra una etiqueta (tooltip) al pasar el mouse; no navega.

Al hacer clic se abre una **pestaña nueva** hacia `https://www.santafe.gov.ar/sicap56/cap/includes/seguimiento_paciente/seguimiento.php` — un buscador de pacientes de la Red Provincial de Salud (sistema SICAP), con tres bloques de búsqueda (Datos Personales, Datos Filiatorios, H.C./Legajo Familiar dentro del efector) y botones Buscar / Nueva Consulta / Cerrar.

🔴 **Hallazgo confirmado (con autorización explícita de Berenice para hacer clic):** el encabezado de esa pantalla externa muestra **"Usuario: .", "Nodo: -" y "Efector: -"**, todos vacíos. Esto confirma que, al no estar definidos los parámetros de RPS en este efector (ver punto 8.5), la integración con la Red Provincial **no logra identificar el usuario ni el efector**. La pantalla carga y el formulario de búsqueda funciona visualmente, pero no es posible saber si una búsqueda en estas condiciones queda correctamente asociada al efector o al usuario que la ejecuta. No se ejecutó ninguna búsqueda real allí, para no consultar la base de datos provincial en vivo sin necesidad.

**Conclusión:** el enlace no está roto, pero **no es funcionalmente confiable en este efector** hasta que se carguen los parámetros de RPS (Código de Establecimiento, IP del Establecimiento, URL de Logout).

## 10. Notificaciones y mensajes

En la barra superior:
- 🔔 **Notificaciones:** avisos internos del sistema. En el relevamiento no había notificaciones nuevas.
- ✉️ **Mensajes:** mensajería interna. En el relevamiento no había mensajes nuevos.

Ambos tienen un enlace "Ver todas/todos" que lleva a un listado completo.

## 11. Perfil de usuario

Desde el ícono 👤 (arriba a la derecha) se accede a:
- **Nombre del usuario logueado** y su usuario de acceso.
- **Cambiar Contraseña**: abre un formulario para cambiar la propia contraseña (no se completó durante el relevamiento, para no alterar las credenciales de la cuenta usada).
- **Cerrar Sesión**: cierra la sesión actual y vuelve a la pantalla de login.

---

## 12. Errores frecuentes

| Problema | Causa probable | Solución |
|---|---|---|
| La pestaña **Laboratorios** de la Ficha del Paciente muestra un error 500 ("An exception occurred...") | 🔴 Falla de base de datos: falta una columna (`stamp_usu_id`) en la tabla `labt_orden_analisis` (órdenes de laboratorio) de esta instancia. Comprobado con un paciente de prueba, por lo que afecta a **todos** los pacientes en este ambiente. | Reportar a Sectorial Informática (soporte técnico) indicando la pestaña y el mensaje de error completo. No es un error del usuario. |
| La misma página de error de Laboratorios expone, además del error, información técnica interna (consulta SQL completa, nombres de tablas/columnas, y una ruta de servidor tipo `/home/sectorial/git/mihospital/diagnose-web/code/...`) | 🔴 El sistema tiene el "modo debug" activo en esta instancia — un error de este tipo no debería mostrar detalle interno del servidor a un usuario final | Reportar a Sectorial Informática como hallazgo de seguridad aparte (además del bug en sí): la exposición de esa información es un riesgo independiente del error 500 |
| El buscador de Pacientes/Internaciones/Diagnósticos tarda varios segundos o no responde | La búsqueda es muy amplia (pocas letras, coincide con miles de registros) | Usar un criterio más específico: apellido y nombre completos, o número de documento/historia clínica |
| "Por favor, ingresar un criterio de búsqueda." | El campo de búsqueda está vacío y se intentó ver el listado sin filtrar | Escribir un criterio antes de buscar |
| "Sin Registros Encontrados" / "Sin Internaciones Registradas" / etc. | No hay datos que coincidan con la búsqueda, o el paciente/sala no tiene información cargada para esa pestaña | Verificar el criterio de búsqueda; si se esperaba encontrar algo, confirmar que esté bien escrito |
| La ficha de "Nueva Cirugía" se abre con la etiqueta "ANULADA" | Es el estado inicial del formulario hasta que se completa y se presiona "Confirmar" | Comportamiento normal; no indica ningún error |
| El informe "Parte Qx Diario" (y probablemente los otros 2 informes en modal) muestra al pie un texto tipo "Host: [nombre interno del servidor]" | El servidor no está removiendo información de depuración/hostname de la vista imprimible | Reportar a Sectorial Informática junto con el error 500 de Laboratorios — es información técnica que no debería figurar en un documento pensado para imprimir o compartir |
| Al entrar a **Red Salud** el encabezado de la pantalla externa muestra "Usuario: .", "Nodo: -" y "Efector: -" vacíos | Los parámetros de RPS (Código de Establecimiento, IP del Establecimiento, URL de Logout) no están cargados en Administración → RPS para este efector | La pantalla igual carga y deja buscar, pero no se puede confirmar que la búsqueda quede asociada al efector/usuario correcto. Solicitar a Sectorial Informática que complete los parámetros de RPS — ver sección 9 |

## 13. Problemas y soluciones (generales)

| Problema | Causa probable | Solución |
|---|---|---|
| No aparece un módulo en el menú lateral | El módulo no está habilitado para el efector, o el usuario no tiene permiso | Consultar con Administración (Módulos Habilitados) o con el administrador del sistema |
| La sesión se cierra sola / pide loguearse de nuevo | Vencimiento de sesión por inactividad (comportamiento típico de sistemas web, no confirmado el tiempo exacto en este relevamiento) | Volver a iniciar sesión |
| Un botón aparece deshabilitado o sin efecto | Puede requerir completar campos obligatorios antes, o el usuario no tiene el permiso correspondiente | Revisar campos obligatorios marcados en el formulario; si persiste, consultar con Administración |

## 14. Roles y permisos observados

Durante el relevamiento se usó exclusivamente el usuario **`sa`**, identificado internamente por el sistema como **"Administrador, Usuario"** (rol: **Administrador**). Con este usuario:

- Se pudo acceder a los 5 módulos habilitados (Pacientes, Consultorios, Internaciones, Quirófano, Administración).
- Se pudo ver la configuración completa del sistema.
- No se probaron otros roles ni usuarios, por lo que **no es posible documentar con certeza** qué ve o qué puede hacer un perfil no administrador (por ejemplo, un usuario de enfermería o de admisión). *No fue posible verificar esta información con el usuario disponible* — ver más abajo qué se intentó y por qué sigue pendiente.

### 14.1 Qué se intentó para conseguir un usuario no-administrador

- Se revisó el módulo **Administración** completo (Módulos Habilitados, Compatibilidad Informes/PACS, RPS, Plantillas de Informes, Crear esquema de controles/permisos) buscando una pantalla de gestión de usuarios o de asignación de roles. **No existe ninguna** en esta interfaz con el usuario `sa`.
- Se revisó **Perfil de usuario** (`/mihospital/home/configuracion/usuario/home`): solo muestra Nombre y Usuario en modo lectura, más el botón "Cambiar Contraseña". No hay selector de rol ni listado de permisos allí.
- 🟡 **Conclusión:** la gestión de cuentas de usuario y roles de MIHOSPITAL no tiene autoservicio dentro de la aplicación en este efector. Probablemente se administra del lado de **Sectorial Informática / Ministerio de Salud**, fuera de esta interfaz. Si en el futuro se necesita relevar un rol no-administrador, el camino es conseguir credenciales de un usuario existente de ese perfil, o solicitar la creación de uno a Sectorial Informática.

### 14.2 Indicios indirectos sobre el modelo de roles (sin haber iniciado sesión con otro usuario)

Aunque no se pudo verificar de forma directa, el relevamiento con `sa` dejó algunas señales de que el sistema **sí distingue roles internamente**, aunque no se pueda administrar desde la interfaz:

- 🟡 La pantalla de Inicio de Quirófano personaliza sus alertas con el texto **"Alertas para el usuario SA - Administrador, Usuario"** (ver sección 10) — el sistema conoce y muestra el rol de la persona logueada junto a su nombre, lo que sugiere que la interfaz está preparada para comportarse distinto según el rol, aunque con `sa` no se pudo comparar contra otro caso.
- 🟡 La sección de Preguntas Frecuentes / Errores (sección 13) ya advierte: *"Un módulo no aparece en el menú lateral → el módulo no está habilitado para el efector, **o el usuario no tiene permiso**"* y *"Un botón aparece deshabilitado o sin efecto → ... o el usuario no tiene el permiso correspondiente"*. Esto es una inferencia razonable a partir del diseño general del sistema (es el comportamiento típico de sistemas con permisos por módulo/acción), **no una observación directa**, ya que con `sa` todos los módulos y botones estuvieron siempre habilitados.
- 🟡 No confundir con **"Roles/Profesionales"** (Quirófano → Configuración): ese ítem no tiene que ver con permisos de acceso al sistema, sino con los **roles del equipo quirúrgico** dentro de una cirugía (ej. Cirujano, Anestesista, Instrumentador) — es un concepto clínico/operativo distinto, ya documentado en la sección 8.

### 14.3 Qué falta para completar esta sección

Para documentar con certeza las diferencias reales entre roles (qué módulos, pantallas y botones ve o no ve un usuario de enfermería, admisión, o un médico sin permisos administrativos) hace falta uno de estos dos caminos, ninguno resuelto todavía:

1. Que alguien facilite credenciales de un usuario no-administrador ya existente, para repetir el recorrido de este manual con ese usuario y comparar.
2. Que Sectorial Informática / Ministerio de Salud cree un usuario de prueba con un rol no-administrativo.

Hasta que uno de los dos ocurra, esta sección queda con lo observado (`sa`/Administrador) más las inferencias marcadas arriba, y **no debe leerse como confirmación de que otros roles ven exactamente eso** — solo como lo más probable dado el diseño del sistema.

## 15. Buenas prácticas

- No compartir el usuario `sa` (u otra cuenta de administrador) para el trabajo diario; cada persona debería tener su propio usuario con el rol que le corresponda.
- Cerrar sesión al alejarse del equipo, especialmente en pantallas con datos de pacientes.
- Usar criterios de búsqueda específicos para no exponer innecesariamente listados extensos con datos personales.
- No completar ni confirmar formularios (nueva cirugía, altas, etc.) a modo de prueba en el ambiente real de producción.
- Antes de desactivar un módulo o ejecutar la herramienta de "Crear esquema de controles/permisos", confirmar el impacto con Sectorial Informática.

---

## 16. Guía rápida

**¿Cómo busco un paciente?**
1. Menú lateral → Pacientes → Pacientes.
2. Escribir apellido y nombre (o documento) en el buscador.
3. Presionar Enter.
4. Hacer clic en el paciente deseado.

**¿Cómo veo si hay camas libres en una sala?**
1. Menú lateral → Internaciones → Salas.
2. Ver la columna "Libres" de la sala buscada.

**¿Cómo consulto los turnos de un profesional?**
1. Menú lateral → Consultorios → Conf. Edilicia → Consultorios.
2. Filtrar por "Profesional".

**¿Cómo veo el listado de profesionales del hospital?**
1. Menú lateral → Consultorios → Conf. Edilicia → Profesionales.
2. Usar el buscador o exportar la tabla (CSV/Excel/PDF).

**¿Cómo busco un código de diagnóstico (CIE-10)?**
1. Menú lateral → Internaciones → Nomencladores → CIE-10.
2. Escribir el nombre de la enfermedad o el código.

**¿Cómo veo las cirugías pendientes de un usuario?**
1. Menú lateral → Quirófano.
2. Revisar la sección "Alertas para el usuario [tu usuario]".

**¿Cómo cambio mi contraseña?**
1. Ícono 👤 (arriba a la derecha) → Cambiar Contraseña.

**¿Cómo vuelvo a la pantalla principal?**
1. Hacer clic en el logo "miHospital" (arriba) o en "Menú Principal" en el menú lateral.

**¿Cómo cierro sesión?**
1. Ícono 👤 (arriba a la derecha) → Cerrar Sesión.

---

## 17. Preguntas frecuentes

**¿Cómo busco un paciente si no sé el número de documento?**
Se puede buscar por nombre y apellido; si hay muchos resultados, agregar el nombre completo o usar el filtro avanzado (fecha de nacimiento, sexo, etc.).

**¿Qué hago si no encuentro al paciente?**
Verificar que el criterio de búsqueda esté bien escrito. Si el paciente nunca fue atendido en el efector, puede no estar registrado.

**¿Qué significa "Sin Registros Encontrados"?**
Que no hay datos que coincidan con la búsqueda o el filtro aplicado en ese momento.

**¿Qué campos son obligatorios en el formulario de Nueva Cirugía?**
Confirmado (sección 8.4): Fecha Pedido, Tipo de Cirugía, Oncológica, Paciente, Procedencia-Sub-Sector, Cirujano, Diagnóstico Presuntivo, Diagnóstico a imprimir, Procedimiento Quirúrgico Presuntivo, Procedimiento a imprimir, Especialidad, Tipo Anestesia, Destino, Req. Diag. por Imágenes, Req. Hemoterapia, Req. Torre Laparoscopia, Req. Materiales Especiales, Tiempo Estimado Cirugía y Días Post-Operatorio. El resto de los campos (Fecha Probable, Hora Probable, datos de contacto, Observaciones, Ropa/Cajas a Utilizar, Score, Fecha Espera Máx.) son opcionales. Área Quirúrgica no mostró aviso de obligatoriedad, lo cual llama la atención.

**¿Por qué la pestaña Laboratorios de un paciente da error?**
Es un problema conocido de esta instancia (ver sección 12, Errores frecuentes) y debe reportarse a Sectorial Informática; no es un error del usuario.

**¿Cómo exporto un listado a Excel o PDF?**
Solo **Consultorios → Profesionales** tiene botones Copiar / CSV / Excel / PDF / Imprimir. Se verificó que **no** están presentes en Turnos del Efector, listado de Pacientes, listado de Internaciones, Informe de Producción (Quirófano) ni Nomenclador de Cirugías — Profesionales parece ser un caso particular, no el estándar del sistema.

**¿Cómo vuelvo atrás?**
Usar la "miga de pan" (ruta de navegación) en la parte superior de cada pantalla, o el menú lateral.

**¿Qué hago si el sistema no guarda un cambio?**
No fue posible comprobar este escenario durante el relevamiento (no se guardaron cambios reales). Verificar que todos los campos obligatorios estén completos y, si el problema persiste, contactar a Sectorial Informática.

**¿Cómo cierro sesión?**
Ícono 👤 arriba a la derecha → Cerrar Sesión.

**¿Puedo confiar en los resultados que me da "Red Salud"?**
En este efector, no todavía: los parámetros de conexión (Administración → RPS) no están cargados, así que la pantalla externa abre pero muestra "Usuario", "Nodo" y "Efector" vacíos. Funciona visualmente pero no se pudo confirmar que identifique correctamente al efector — ver sección 9. Antes de usarla para una consulta real, confirmar con Sectorial Informática que los parámetros de RPS ya se cargaron.

**Vi datos técnicos del servidor (nombres de tablas, rutas de archivos) en un mensaje de error, ¿hice algo mal?**
No. Es un problema del sistema (modo de depuración activo en esta instancia), no algo que el usuario provocó ni algo que deba intentar solucionar. Cerrar la pantalla y reportarlo a Sectorial Informática tal como se indica en la sección 12.

---

## 18. Glosario

| Término | Significado |
|---|---|
| Efector | Establecimiento de salud (hospital, centro de salud) |
| H.C. | Historia Clínica (número identificador del paciente) |
| CIE-10 | Clasificación Internacional de Enfermedades, 10ª edición |
| PreQx / Prequirúrgico | Etapa previa a una cirugía |
| Diag. Presuntivo | Diagnóstico presunto, antes de confirmarse |
| Diag. Principal | Diagnóstico confirmado principal de una internación |
| RPS | Red Provincial de Salud |
| PACS | Sistema de almacenamiento y comunicación de imágenes médicas (radiografías, tomografías, etc.) |
| Sala / Habitación / Cama | Niveles de organización física de la internación: una Sala contiene Habitaciones, y cada Habitación contiene Camas |
| Presentismo | Estado de asistencia de un turno (si el paciente se presentó o no) |
| Score (Quirófano) | Puntaje de prioridad asignado a una cirugía en lista de espera |
| Paciente "VIRTUAL" | Registro de prueba del propio sistema, usado para pruebas internas (no es un paciente real) |
| "ANULADA" (estado) | Estado inicial de un formulario de Nueva Cirugía antes de completarse y confirmarse — no significa que algo haya salido mal |
| SICAP | Sistema provincial (Santa Fe) al que se accede a través del enlace "Red Provincial de Salud" — es la aplicación externa que aparece al hacer clic en ese acceso |
| Oviyam / PACS | Visor de imágenes médicas (radiografías, tomografías) al que se conecta miHospital mediante el parámetro "Url Prefijo Oviyam" en Administración → Compatibilidad Informes/PACS |
| Código de Establecimiento | Identificador del efector dentro de la Red Provincial de Salud, uno de los tres parámetros que deben cargarse en Administración → RPS para que Red Salud funcione |
| Sectorial Informática | Área de sistemas del Ministerio de Salud de Santa Fe que administra y da soporte técnico a miHospital — a quien se reportan los errores de esta sección |
| Migas de pan | Nombre común de la "ruta de navegación" que aparece arriba del contenido (ver sección 6), indica en qué pantalla se está parado dentro del sistema |

---

## 19. Inventario de funcionalidades

| N° | Módulo | Funcionalidad | Accesible | Documentada | Observaciones |
|---|---|---|---|---|---|
| 1 | General | Inicio de sesión | Sí | Sí | — |
| 2 | General | Menú lateral / navegación | Sí | Sí | — |
| 3 | General | Notificaciones | Sí | Sí | Sin novedades en la sesión |
| 4 | General | Mensajes | Sí | Sí | Sin novedades en la sesión |
| 5 | General | Cambiar Contraseña | Sí | Parcial | Formulario no abierto, por regla de seguridad |
| 6 | General | Cerrar sesión | Sí | Sí | — |
| 7 | Pacientes | Buscador de pacientes | Sí | Sí | — |
| 8 | Pacientes | Listado / búsqueda avanzada | Sí | Sí | — |
| 9 | Pacientes | Ficha del paciente - Datos Personales | Sí | Sí | — |
| 10 | Pacientes | Ficha del paciente - Internaciones | Sí | Sí | — |
| 11 | Pacientes | Ficha del paciente - Guardia | Sí | Sí | — |
| 12 | Pacientes | Ficha del paciente - Turnos C.E. | Sí | Sí | — |
| 13 | Pacientes | Ficha del paciente - Cirugías | Sí | Sí | — |
| 14 | Pacientes | Ficha del paciente - Laboratorios | Sí | Sí | 🔴 Error 500 (bug confirmado) |
| 15 | Pacientes | Ficha del paciente - Farmacia | Sí | Sí | — |
| 16 | Pacientes | Ficha del paciente - Compras | Sí | Sí | — |
| 17 | Pacientes | Altas del día | Sí | Sí | — |
| 18 | Pacientes | Impresión de pulsera identificatoria | Sí | Parcial | Botón identificado, no ejecutado |
| 19 | Consultorios | Turnos del efector | Sí | Sí | Sin exportación (confirmado) |
| 20 | Consultorios | Profesionales (listado + export) | Sí | Sí | Única grilla con exportación CSV/Excel/PDF (confirmado) |
| 21 | Consultorios | Consultorios / agenda | Sí | Sí | — |
| 22 | Consultorios | Configuración | Sí | Parcial | Solo un ítem observado |
| 23 | Internaciones | Tablero de inicio | Sí | Sí | — |
| 24 | Internaciones | Salas (ocupación) | Sí | Sí | — |
| 25 | Internaciones | Detalle de sala (habitaciones/camas) | Sí | Sí | — |
| 26 | Internaciones | Listado de internaciones | Sí | Sí | Datos sensibles, no citados |
| 27 | Internaciones | Listado de diagnósticos | Sí | Sí | Datos sensibles, no citados |
| 28 | Internaciones | Nomenclador CIE-10 | Sí | Sí | — |
| 29 | Internaciones | Nomenclador de Cirugías | Sí | Sí | — |
| 30 | Quirófano | Tablero de inicio / alertas | Sí | Sí | — |
| 31 | Quirófano | Lista de Espera | Sí | Sí | — |
| 32 | Quirófano | Cirugías c/Turno (Lista/Calendario) | Sí | Sí | — |
| 33 | Quirófano | Nueva Cirugía (formulario) | Sí | Sí | 🟢 Campos obligatorios confirmados por validación, no confirmada/guardada |
| 34 | Quirófano | Informe Parte Qx Diario | Sí | Sí | 🟢 Probado: abre HTML imprimible, no descarga archivo; 🟡 expone hostname interno |
| 35 | Quirófano | Informe Parte de Enfermería | Sí | Sí | Mismo modal que Parte Qx Diario, no probado individualmente |
| 36 | Quirófano | Informe Cx c/Fecha Probable | Sí | Sí | Mismo modal que Parte Qx Diario, no probado individualmente |
| 37 | Quirófano | Informe de Producción | Sí | Sí | — |
| 38 | Quirófano | Nomenclador de procedimientos | Sí | Sí | — |
| 39 | Quirófano | Configuración | Sí | Sí | Listado de ítems, no se entró a cada uno |
| 40 | Administración | Módulos Habilitados | Sí | Sí | 🔴 No se desactivó ningún módulo |
| 41 | Administración | Compatibilidad Informes/PACS | Sí | Sí | — |
| 42 | Administración | RPS (parámetros) | Sí | Sí | Sin configurar en este efector |
| 43 | Administración | Plantillas de Informes | Sí | Sí | Sin configurar |
| 44 | Administración | Crear esquema de controles/permisos | Sí | Parcial | 🔴 NO ejecutado |
| 45 | Red Salud | Enlace externo RPS | Sí | Sí | 🔴 Abre, pero Usuario/Nodo/Efector llegan vacíos (RPS sin configurar) |

## 20. Limitaciones de esta documentación

- El relevamiento se realizó íntegramente con el usuario **`sa`** (rol Administrador). No se pudo observar el sistema desde otros roles (por ejemplo, enfermería, admisión, médico sin permisos administrativos), por lo que **no se documentan diferencias de permisos entre roles** más allá de lo observado con este usuario.
- No se ejecutaron acciones potencialmente irreversibles: no se desactivó ningún módulo, no se ejecutó "Crear esquema de controles/permisos", no se confirmó ninguna cirugía nueva, no se generaron altas ni turnos reales, no se cambió la contraseña del usuario.
- Se hizo clic en el enlace a **Red Salud** (botón "Red Provincial de Salud", con autorización explícita de Berenice): abre correctamente una pestaña externa hacia el sistema SICAP, pero el encabezado llega sin Usuario/Nodo/Efector porque los parámetros de RPS no están definidos en este efector — ver sección 9 para el detalle. No se ejecutó ninguna búsqueda real en esa pantalla externa.
- Se probó "Imprimir" en el informe **Parte Qx Diario** (con autorización de Berenice): no descarga archivo, abre una página HTML imprimible en una pestaña nueva. Como el efector no tenía cirugías cargadas en la fecha probada, no se vio el formato con datos reales. No se probaron individualmente "Parte de Enfermería" ni "Cx c/Fecha Probable" (comparten el mismo modal y se asume el mismo mecanismo).
- Las pantallas de listados de Pacientes, Internaciones y Diagnósticos exhiben datos identificatorios reales (nombre, DNI, diagnóstico). Por la regla de privacidad de este relevamiento, **no se transcribió ningún dato real de pacientes** en este manual; el único paciente citado por su nombre es un registro de prueba del propio sistema, marcado como "VIRTUAL" (HC 1.000.001, "SOSA, MARTA").
- Los campos obligatorios del formulario "Nueva Cirugía" se confirmaron (sección 8.4) probando el botón Confirmar con el formulario vacío, sin guardar ningún registro. No se probó este mismo método en otros formularios del sistema (por ejemplo, Altas o Turnos), por lo que en esos casos la obligatoriedad de campos sigue sin confirmar.
- Este manual documenta el efector **HOSP EVA PERON**; otros efectores pueden tener módulos habilitados o configuraciones distintas.

## 21. Fecha de relevamiento / versión documentada

- **Fecha de relevamiento:** 03 de septiembre de 2026 (relevamiento inicial); continuado el 11 de septiembre de 2026 (informes modales de Quirófano) y el 14 de septiembre de 2026 (enlace Red Salud, manual visual con capturas, exportación en otras grillas, campos obligatorios de Nueva Cirugía, formato de salida del informe Parte Qx Diario).
- **Versión de sistema documentada:** 26.5.6.
- **Ambiente:** de pruebas/staging (según indicación del solicitante), instancia `192.168.4.24`.
