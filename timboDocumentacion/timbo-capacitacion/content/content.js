// content.js — TODO el contenido pedagógico de la plataforma TIMBÓ.
// Este archivo es pura data (sin DOM, sin lógica de render) para que se pueda
// editar el contenido sin tocar el código de la aplicación.
// Fuente de verdad: MANUAL_USUARIO_MIHOSPITAL.md y notas_relevamiento.md
// (carpeta raíz del proyecto). No hay nada acá que no esté respaldado por esos
// documentos. Donde el manual no tiene una respuesta verificada, se marca
// explícitamente con el campo `verified: false` y una nota aclaratoria.

export const SYSTEM_INFO = {
  name: 'TIMBÓ',
  fullName: 'Sistema de Salud Hospitalario miHospital',
  org: 'Gobierno de Santa Fe — Ministerio de Salud',
  description:
    'TIMBÓ es el sistema que usa el hospital para buscar pacientes, gestionar camas e internaciones, coordinar turnos de consultorio, organizar el circuito de quirófano y administrar la configuración del efector.',
  scope:
    'Esta capacitación cubre los 5 módulos habilitados en el efector relevado (Pacientes, Consultorios, Internaciones, Quirófano y Administración) más el enlace a Red Salud. Todo el contenido está basado en un relevamiento real hecho con un usuario de perfil Administrador — donde algo no se pudo comprobar, se indica claramente.',
  recommendations: [
    'TIMBÓ maneja información de salud de pacientes reales. No dejes pantallas con datos de pacientes abiertas o visibles a personas sin autorización.',
    'Cada persona debería trabajar con su propio usuario, nunca con una cuenta administrativa compartida.',
    'Hay acciones que modifican configuración crítica del sistema (desactivar un módulo, crear el esquema de permisos). Estas acciones están marcadas con 🔴 en toda la capacitación — no se deben usar sin saber exactamente qué hacen.',
  ],
};

// ---------------------------------------------------------------------------
// GLOSARIO
// ---------------------------------------------------------------------------
export const GLOSSARY = [
  { term: 'Efector', definition: 'El establecimiento de salud (hospital, centro de salud) sobre el que se está trabajando. Aparece indicado arriba a la derecha entre corchetes.', module: 'General', usage: 'Aparece en la barra superior de toda pantalla del sistema.' },
  { term: 'H.C.', definition: 'Historia Clínica: el número único que identifica a un paciente dentro del sistema.', module: 'Pacientes', usage: 'Se usa para buscar pacientes y en casi todos los listados.' },
  { term: 'Ficha del Paciente', definition: 'La pantalla central de datos de un paciente, con pestañas para ver sus datos personales, internaciones, turnos, cirugías, laboratorios, farmacia y compras.', module: 'Pacientes', usage: 'Se abre al hacer clic en un paciente desde cualquier buscador.' },
  { term: 'Sala / Habitación / Cama', definition: 'Niveles de organización física de la internación: una Sala contiene Habitaciones, y cada Habitación contiene Camas.', module: 'Internaciones', usage: 'Se usa para ver la ocupación del hospital.' },
  { term: 'CIE-10', definition: 'Clasificación Internacional de Enfermedades (10ª versión). Catálogo estándar de códigos de diagnóstico usado en toda la historia clínica.', module: 'Internaciones', usage: 'Se busca por nombre de la enfermedad o por código.' },
  { term: 'Nomenclador de Cirugías', definition: 'Catálogo estándar de procedimientos quirúrgicos con su código.', module: 'Internaciones / Quirófano', usage: 'Se usa al cargar una cirugía o al consultar procedimientos.' },
  { term: 'RPS', definition: 'Red Provincial de Salud: integración con el sistema provincial que permite compartir información entre efectores.', module: 'Red Salud / Administración', usage: 'Sus parámetros de conexión se configuran en Administración → RPS.' },
  { term: 'PACS', definition: 'Sistema de almacenamiento y comunicación de imágenes médicas (radiografías, tomografías, etc.).', module: 'Administración', usage: 'Se conecta desde Administración → Compatibilidad Informes/PACS.' },
  { term: 'Presentismo', definition: 'Estado de asistencia de un turno: si el paciente se presentó o no.', module: 'Consultorios', usage: 'Es una columna en la tabla de Turnos del Efector.' },
  { term: 'Score (Quirófano)', definition: 'Puntaje de prioridad (0 a 10) asignado a una cirugía en lista de espera.', module: 'Quirófano', usage: 'Es un campo opcional al cargar una Nueva Cirugía.' },
  { term: 'Paciente "VIRTUAL"', definition: 'Registro de prueba del propio sistema, usado para pruebas internas. No es un paciente real.', module: 'Pacientes', usage: 'Se usa como ejemplo seguro en esta capacitación.' },
  { term: '"ANULADA" (estado)', definition: 'Estado inicial de un formulario de Nueva Cirugía antes de completarse y confirmarse. No significa que algo haya salido mal.', module: 'Quirófano', usage: 'Aparece como etiqueta al abrir el formulario de Nueva Cirugía.' },
  { term: 'SICAP', definition: 'Sistema provincial al que se accede a través del enlace "Red Provincial de Salud".', module: 'Red Salud', usage: 'Se abre en una pestaña nueva del navegador al hacer clic en "Red Provincial de Salud".' },
  { term: 'Oviyam', definition: 'Visor de imágenes médicas al que se conecta TIMBÓ mediante un parámetro de configuración.', module: 'Administración', usage: 'Se configura en Administración → Compatibilidad Informes/PACS.' },
  { term: 'Código de Establecimiento', definition: 'Identificador del efector dentro de la Red Provincial de Salud.', module: 'Administración', usage: 'Es uno de los parámetros que debe cargarse en Administración → RPS para que Red Salud funcione.' },
  { term: 'Sectorial Informática', definition: 'El área de sistemas del Ministerio de Salud de Santa Fe que administra y da soporte técnico a TIMBÓ.', module: 'General', usage: 'Es a quién se reportan los errores del sistema.' },
  { term: 'Migas de pan', definition: 'Nombre común de la "ruta de navegación" que aparece arriba del contenido, e indica en qué pantalla estás parado dentro del sistema.', module: 'General', usage: 'Aparece arriba del contenido en toda pantalla.' },
  { term: 'PreQx / Prequirúrgico', definition: 'Etapa previa a una cirugía, dentro del circuito de Quirófano.', module: 'Quirófano', usage: 'Es el valor por defecto del campo "Tipo de PreQx" al cargar una Nueva Cirugía.' },
  { term: 'Diag. Presuntivo', definition: 'Diagnóstico presunto de un paciente, antes de confirmarse.', module: 'Internaciones / Quirófano', usage: 'Aparece como columna en listados de internaciones y como campo obligatorio al cargar una cirugía.' },
  { term: 'Diag. Principal', definition: 'Diagnóstico confirmado principal de una internación.', module: 'Internaciones', usage: 'Es una columna en el listado de Diagnósticos de Internaciones.' },
];

// ---------------------------------------------------------------------------
// MÓDULOS Y LECCIONES
// ---------------------------------------------------------------------------

export const MODULES = [
  // ---------------------------------------------------------------- PRIMEROS PASOS
  {
    id: 'primeros-pasos',
    title: 'Primeros pasos',
    icon: '🧭',
    summary: 'Antes de entrar a un módulo: cómo ingresar al sistema, cómo está organizada la pantalla y los conceptos que vas a ver en todos lados.',
    audience: 'Cualquier persona que va a usar TIMBÓ por primera vez.',
    difficulty: 'basico',
    lessons: [
      {
        id: 'ingresar',
        title: 'Ingresar al sistema',
        minutes: 3,
        difficulty: 'basico',
        blocks: [
          { type: 'text', text: 'Para empezar a usar TIMBÓ necesitás un usuario y una contraseña propios, que te da el área de Sectorial Informática de tu hospital. Nunca compartas tu usuario con otra persona.' },
          { type: 'step', number: 1, image: 'login.jpg', alt: 'Pantalla de inicio de sesión de miHospital, con campos de usuario y contraseña', caption: 'Pantalla de inicio de sesión', explanation: 'Al entrar a la dirección del sistema, lo primero que ves es la pantalla de login.', lookFor: 'Dos campos: uno con ícono de persona (Usuario) y otro con ícono de candado (Contraseña). Al pie, el contacto de la Mesa de ayuda y la versión del sistema.', doThis: 'Completá tu Usuario y tu Contraseña, y presioná "Iniciar Sesión".' },
          { type: 'text', text: 'Si los datos son correctos, entrás directo a la pantalla de Inicio, con el nombre de tu establecimiento (efector) en la esquina superior derecha, por ejemplo "[HOSP EVA PERON]".' },
          { type: 'warning', text: 'Por seguridad, nunca escribas ni compartas la contraseña de otra persona. Cada usuario debe ingresar la suya.' },
          { type: 'practice', text: 'Abrí TIMBÓ en tu navegador e iniciá sesión con tu propio usuario. Fijate qué efector aparece arriba a la derecha.' },
        ],
        quiz: [
          { type: 'true-false', question: 'Es una buena práctica usar el usuario de un compañero si el propio no anda.', answer: false, explanation: 'Cada persona debe tener su propio usuario. Compartir credenciales no es una buena práctica de seguridad.' },
          { type: 'multiple-choice', question: '¿Qué información aparece en la esquina superior derecha después de iniciar sesión?', options: ['El nombre del establecimiento (efector)', 'La contraseña del usuario', 'El número de historia clínica del último paciente buscado'], correctIndex: 0, explanation: 'El efector activo aparece siempre arriba a la derecha, entre corchetes.' },
        ],
      },
      {
        id: 'interfaz',
        title: 'Conocer la pantalla principal',
        minutes: 4,
        difficulty: 'basico',
        blocks: [
          { type: 'text', text: 'La pantalla de Inicio es el punto de partida hacia cualquier módulo. Su organización se repite en todo el sistema, así que vale la pena conocerla bien.' },
          { type: 'step', number: 1, image: 'home.jpg', alt: 'Pantalla de Inicio de miHospital con las tarjetas de acceso a los módulos', caption: 'Pantalla de Inicio', explanation: 'Cuatro tarjetas de acceso directo (Pacientes, Consultorios, Internaciones, Quirófano) y un bloque de Accesos Externos con el enlace a la Red Provincial de Salud.', lookFor: 'La barra azul superior con el logo a la izquierda y tres íconos a la derecha (🔔 notificaciones, ✉️ mensajes, 👤 tu usuario). Debajo, el menú lateral con la lista de módulos.', doThis: 'Hacé clic en el botón ☰ para expandir o contraer el menú lateral, y probá los dos modos.' },
          { type: 'concepts', items: [
            { term: 'Menú lateral', def: 'Lista de módulos disponibles, a la izquierda. Se puede mostrar expandido (con texto) o contraído (solo íconos).' },
            { term: 'Ruta de navegación ("migas de pan")', def: 'Arriba del contenido, muestra dónde estás parado, por ejemplo "miHospital > Módulo Pacientes > Buscador de Pacientes".' },
            { term: '🔔 Notificaciones', def: 'Avisos internos del sistema. Tiene un enlace "Ver todas" que lleva a un listado completo.' },
            { term: '✉️ Mensajes', def: 'Mensajería interna entre usuarios del sistema. También tiene un enlace "Ver todos".' },
            { term: 'Ícono de usuario (👤)', def: 'Muestra tu nombre y tu usuario de acceso, y desde ahí llegás a dos acciones: "Cambiar Contraseña" (abre un formulario para definir una nueva) y "Cerrar Sesión" (te devuelve a la pantalla de login).' },
          ] },
          { type: 'tip', text: 'Cada módulo, además del menú lateral, tiene en su pantalla de Inicio un desplegable "Secciones ▾" con acceso directo a sus pantallas principales.' },
          { type: 'tip', text: 'Para volver a la pantalla principal desde cualquier lugar del sistema, hacé clic en el logo "miHospital" (arriba) o en "Menú Principal" dentro del menú lateral.' },
          { type: 'warning', text: 'Cambiar Contraseña y Cerrar Sesión son acciones sobre tu propia cuenta: no hace falta ni se debe pedirle ayuda a otra persona ni usar la sesión de un compañero para hacerlas.' },
          { type: 'practice', text: 'Dentro de TIMBÓ, recorré el menú lateral expandido y contraído, y fijate qué dice la ruta de navegación cuando entrás a un módulo cualquiera.' },
        ],
        quiz: [
          { type: 'multiple-choice', question: '¿Para qué sirve la "ruta de navegación" (migas de pan)?', options: ['Para saber en qué pantalla estás parado dentro del sistema', 'Para cambiar de efector', 'Para buscar un paciente'], correctIndex: 0, explanation: 'Muestra el camino desde el Inicio hasta la pantalla actual.' },
          { type: 'true-false', question: 'El menú lateral solo se puede ver expandido, no se puede contraer.', answer: false, explanation: 'Se puede expandir o contraer con el botón ☰.' },
          { type: 'multiple-choice', question: '¿Desde dónde cambiás tu contraseña o cerrás sesión?', options: ['Desde el ícono de usuario (👤), arriba a la derecha', 'Desde el menú lateral', 'Pidiéndoselo a un Administrador'], correctIndex: 0, explanation: 'El ícono de usuario tiene las dos opciones: Cambiar Contraseña y Cerrar Sesión.' },
        ],
      },
      {
        id: 'conceptos-basicos',
        title: 'Conceptos que vas a ver en todos lados',
        minutes: 4,
        difficulty: 'basico',
        blocks: [
          { type: 'text', text: 'Estos términos aparecen en casi todos los módulos. Conocerlos de entrada te va a ahorrar tiempo después. Podés volver a consultarlos cuando quieras en el Glosario.' },
          { type: 'concepts', items: [
            { term: 'Efector', def: 'El hospital o centro de salud sobre el que estás trabajando.' },
            { term: 'H.C.', def: 'Historia Clínica: el número que identifica a un paciente.' },
            { term: 'Ficha del Paciente', def: 'La pantalla con toda la información de un paciente, organizada en pestañas.' },
            { term: 'CIE-10', def: 'El catálogo estándar de códigos de diagnóstico.' },
            { term: 'RPS / Red Salud', def: 'La integración con el sistema provincial de salud.' },
          ] },
          { type: 'tip', text: 'La mayoría de las pantallas de búsqueda te recuerdan que podés usar Ctrl+F del navegador y luego Enter para buscar dentro de una lista de resultados larga.' },
        ],
        quiz: [
          { type: 'checklist', title: 'Antes de seguir, asegurate de poder explicar con tus palabras', items: [
            'Qué es un "efector"',
            'Qué es la "H.C." de un paciente',
            'Para qué sirve el CIE-10',
          ] },
        ],
      },
      {
        id: 'roles-y-permisos',
        title: 'Roles y permisos (lo que sabemos hasta ahora)',
        minutes: 3,
        difficulty: 'intermedio',
        blocks: [
          { type: 'text', text: 'Esta lección es distinta a las demás: en vez de enseñarte a usar una pantalla, te cuenta con honestidad qué se sabe (y qué no) sobre los distintos roles de usuario en TIMBÓ.' },
          { type: 'warning', text: 'Todo este relevamiento se hizo con un usuario de rol Administrador. No fue posible comprobar qué ve o qué puede hacer un usuario de otro perfil (por ejemplo, enfermería o admisión) — no hay, dentro de la aplicación, ninguna pantalla de autoservicio para crear o gestionar usuarios.' },
          { type: 'concepts', items: [
            { term: 'Lo que sí se sabe', def: 'El sistema identifica el rol de cada usuario internamente (por ejemplo, se ve el texto "Administrador, Usuario" en las alertas de Quirófano) — el diseño del sistema sugiere que hay diferencias de permisos por módulo o botón, aunque con el usuario Administrador todo estuvo siempre habilitado.' },
            { term: 'Lo que NO se sabe todavía', def: 'Qué módulos, pantallas o botones ve exactamente un usuario que no sea Administrador.' },
          ] },
          { type: 'tip', text: 'No confundas esto con "Roles/Profesionales" de la Configuración de Quirófano: ese es otro concepto, sobre los roles del equipo quirúrgico (Cirujano, Anestesista, Instrumentador) en una cirugía puntual, no sobre permisos de acceso al sistema.' },
        ],
        quiz: [],
      },
    ],
  },

  // ---------------------------------------------------------------- PACIENTES
  {
    id: 'pacientes',
    title: 'Pacientes',
    icon: '🧑‍⚕️',
    summary: 'Buscar pacientes ya registrados y ver toda su información: datos personales, internaciones, turnos, cirugías, laboratorios, farmacia y compras.',
    audience: 'Personal administrativo, de admisión, y profesionales de la salud que necesiten consultar la ficha de un paciente.',
    difficulty: 'basico',
    lessons: [
      {
        id: 'buscar-paciente',
        title: 'Buscar un paciente',
        minutes: 4,
        difficulty: 'basico',
        blocks: [
          { type: 'text', text: 'Buscar un paciente es probablemente la tarea que más vas a repetir en TIMBÓ. El buscador está pensado para encontrar a alguien con muy poca información.' },
          { type: 'prereq', items: ['Haber iniciado sesión en TIMBÓ.'] },
          { type: 'step', number: 1, image: 'pacientes-inicio.jpg', alt: 'Pantalla de inicio del módulo Pacientes con el buscador y las altas del día', caption: 'Inicio del módulo Pacientes', explanation: 'Al entrar a Pacientes → Inicio ves dos paneles: el Buscador de Pacientes y las Altas del Día.', lookFor: 'Un campo de texto único para buscar por Nombre, Apellido, Documento o H.C.', doThis: 'Escribí un criterio específico — por ejemplo apellido y nombre completos, o el número de documento — y presioná Enter o el botón de lupa.' },
          { type: 'warning', text: 'Una búsqueda muy amplia (por ejemplo, 3 letras comunes) puede devolver decenas de miles de resultados y tardar varios segundos. Cuanto más específico el criterio, más rápido y preciso el resultado.' },
          { type: 'step', number: 2, image: 'pacientes-resultado.jpg', alt: 'Tabla de resultados de la búsqueda de pacientes', caption: 'Resultado de la búsqueda', explanation: 'La tabla muestra Nombre, Nro. Documento, Fecha Nac., Sexo, Nro. H.C. y Obra Social.', lookFor: 'Un cartel "Procesando..." mientras la búsqueda está en curso.', doThis: 'Hacé clic en el nombre del paciente que buscás para abrir su ficha.' },
          { type: 'tip', text: 'Si necesitás filtros más específicos, desplegá el ícono de embudo: aparecen campos separados de Apellido, Nombre, Nro. Documento, Nro. H.C., Sexo, Fecha de Nacimiento, Tipo de H.C. y Activo/Inactivo.' },
          { type: 'practice', text: 'Buscá un paciente por apellido y nombre completos, y después repetí la búsqueda solo por documento. Compará qué tan rápido responde cada una.' },
        ],
        quiz: [
          { type: 'multiple-choice', question: '¿Cuál de estos criterios de búsqueda da un resultado más rápido y preciso?', options: ['3 letras comunes de un apellido', 'Apellido y nombre completos, o número de documento', 'Dejar el campo vacío y presionar buscar'], correctIndex: 1, explanation: 'Cuanto más específico el criterio, menos resultados y más rápida la búsqueda.' },
          { type: 'true-false', question: 'El buscador de pacientes solo permite buscar por nombre y apellido.', answer: false, explanation: 'También se puede buscar por Documento o por H.C. desde el mismo campo.' },
        ],
      },
      {
        id: 'ficha-paciente',
        title: 'La ficha del paciente',
        minutes: 5,
        difficulty: 'basico',
        blocks: [
          { type: 'text', text: 'Una vez que encontraste al paciente, la Ficha del Paciente es donde vas a pasar la mayor parte del tiempo: ahí está organizada toda su información.' },
          { type: 'step', number: 1, image: 'pacientes-ficha.jpg', alt: 'Ficha del paciente, con panel izquierdo de datos y pestañas a la derecha', caption: 'Ficha del Paciente', explanation: 'A la izquierda, un panel fijo con Nombre, H.C., DNI, Fecha de nacimiento (con edad calculada), Sexo, Obra Social, el botón "Pulsera Ident." y los datos de Contacto.', lookFor: 'A la derecha, un panel con pestañas: Datos Personales, Internaciones, Guardia, Turnos C.E., Cirugías, Laboratorios, Farmacia y Compras.', doThis: 'Recorré las pestañas para ver qué información tiene cada una. Si una pestaña no tiene datos, vas a ver un mensaje como "Sin Internaciones Registradas".' },
          { type: 'concepts', items: [
            { term: 'Datos Personales', def: 'Ficha completa del paciente, más los datos de la madre/padre o tutor.' },
            { term: 'Turnos C.E.', def: 'Turnos de consultorio externo, con filtro por Especialidad y por rango de fechas.' },
            { term: 'Laboratorios', def: 'Órdenes y resultados de laboratorio.' },
          ] },
          { type: 'warning', text: 'La pestaña Laboratorios tiene un error conocido en esta instancia del sistema (error 500 al abrirla) — no es algo que hiciste mal vos. Ver la sección "Tengo un problema" para más detalle.' },
        ],
        quiz: [
          { type: 'order-steps', instruction: 'Ordená los pasos para llegar a ver las internaciones previas de un paciente.', steps: [
            'Ir a Pacientes → Pacientes',
            'Buscar al paciente por apellido y nombre',
            'Hacer clic en el paciente para abrir su ficha',
            'Abrir la pestaña "Internaciones"',
          ] },
          { type: 'multiple-choice', question: '¿Qué pasa si una pestaña de la ficha no tiene datos para ese paciente?', options: ['El sistema no deja abrir la pestaña', 'Se muestra un mensaje como "Sin Internaciones Registradas"', 'Se cierra la sesión automáticamente'], correctIndex: 1, explanation: 'Es el comportamiento normal cuando no hay información cargada para esa pestaña.' },
        ],
      },
      {
        id: 'altas-del-dia',
        title: 'Ver las altas del día',
        minutes: 3,
        difficulty: 'basico',
        blocks: [
          { type: 'text', text: 'Si necesitás saber qué pacientes fueron dados de alta en una fecha puntual, no hace falta buscarlos uno por uno.' },
          { type: 'step', number: 1, image: null, alt: '', caption: '', explanation: 'Andá a Pacientes → Altas del día. Vas a ver un filtro de Fecha, con la fecha de hoy puesta por defecto.', lookFor: 'Una tabla con columnas: Nombre, Nro. Documento, Fecha Nac., Nro. H.C., Obra Social, Fecha/Hora Alta y Usuario Alta (quién registró el alta).', doThis: 'Cambiá la fecha si necesitás ver otro día, y presioná Buscar.', diagram: {
            variant: 'table',
            title: 'Altas del día — estructura de la tabla',
            columns: ['Nombre', 'Nro. Documento', 'Fecha Nac.', 'Nro. H.C.', 'Obra Social', 'Fecha/Hora Alta', 'Usuario Alta'],
            rows: [
              ['◼', '◼', '◼', '1.000.234', 'IAPOS', '26/10 09:14', 'mgomez'],
              ['◼', '◼', '◼', '1.000.871', 'Particular', '26/10 11:02', 'jperalta'],
            ],
            note: 'Los datos de pacientes se muestran tapados a propósito — no son reales. "Usuario Alta" es quien registró cada alta.',
          } },
          { type: 'practice', text: 'Entrá a Altas del día y revisá qué usuario aparece registrando cada alta.' },
        ],
        quiz: [
          { type: 'true-false', question: 'La pantalla de Altas del día muestra qué usuario registró cada alta.', answer: true, explanation: 'La columna "Usuario Alta" indica quién hizo el registro.' },
        ],
      },
    ],
  },

  // ---------------------------------------------------------------- CONSULTORIOS
  {
    id: 'consultorios',
    title: 'Consultorios',
    icon: '🗓️',
    summary: 'Gestioná los turnos de consultorio externo, el listado de profesionales y la agenda de consultorios.',
    audience: 'Personal administrativo de turnos y de gestión de consultorios externos.',
    difficulty: 'basico',
    lessons: [
      {
        id: 'turnos-efector',
        title: 'Ver los turnos del efector',
        minutes: 4,
        difficulty: 'basico',
        blocks: [
          { type: 'text', text: 'La pantalla "Turnos del Efector" te muestra todos los turnos de consultorio externo, con la posibilidad de filtrar por paciente.' },
          { type: 'step', number: 1, image: null, alt: '', caption: '', explanation: 'Andá a Consultorios → Turnos.', lookFor: 'Un buscador por Nombre/Apellido/Documento, un ícono de filtros adicionales, y un botón "REFRESCAR" para activar el auto-refresco de la lista.', doThis: 'Si buscás los turnos de un paciente puntual, escribilo en el buscador. Si no, revisá la tabla completa: ID, Fecha, Hora, Paciente (H.C.), Documento, Presentismo, Especialidad, Estudio, Profesional, Tipo, Pedido.', diagram: {
            variant: 'table',
            title: 'Turnos del Efector — estructura de la tabla',
            columns: ['Fecha', 'Hora', 'Paciente (H.C.)', 'Documento', 'Presentismo', 'Especialidad', 'Profesional'],
            rows: [
              ['26/10', '09:30', '◼', '◼', 'Presente', 'Cardiología', 'Dr. Méndez'],
              ['26/10', '10:00', '◼', '◼', 'Ausente', 'Pediatría', 'Dra. Ríos'],
            ],
            note: 'Los datos de pacientes se muestran tapados a propósito — no son reales. Esta grilla no tiene botones de exportación.',
          } },
          { type: 'tip', text: 'Esta grilla no tiene botones de exportación (CSV/Excel/PDF) — se comprobó que Profesionales es el único listado del sistema con esa función.' },
        ],
        quiz: [
          { type: 'multiple-choice', question: '¿Qué indica la columna "Presentismo" en Turnos del Efector?', options: ['El estado de asistencia del turno (si el paciente se presentó)', 'La especialidad del profesional', 'El número de documento del paciente'], correctIndex: 0, explanation: 'Presentismo es justamente ese dato: si el paciente se presentó o no al turno.' },
        ],
      },
      {
        id: 'profesionales-y-agenda',
        title: 'Consultar profesionales y su agenda',
        minutes: 4,
        difficulty: 'basico',
        blocks: [
          { type: 'text', text: 'TIMBÓ tiene un listado completo del personal profesional del efector, y una pantalla separada para ver en qué consultorio y horario atiende cada uno.' },
          { type: 'step', number: 1, image: null, alt: '', caption: '', explanation: 'Consultorios → Conf. Edilicia → Profesionales muestra el listado completo (1.621 registros en el relevamiento, repartidos en 161 páginas).', lookFor: 'Nombre, Matrícula, Especialidad Ppal. y Consultorios Habilitados. Arriba, botones Copiar / CSV / Excel / PDF / Imprimir / Mostrar-Ocultar Columnas.', doThis: 'Usá el buscador simple de la grilla, o exportá la tabla si necesitás trabajarla fuera del sistema.', diagram: {
            variant: 'list',
            title: 'Profesionales — botones disponibles arriba de la tabla',
            items: [
              { label: 'Copiar', hint: 'único caso', tone: 'verified' },
              { label: 'CSV', hint: 'único caso', tone: 'verified' },
              { label: 'Excel', hint: 'único caso', tone: 'verified' },
              { label: 'PDF', hint: 'único caso', tone: 'verified' },
              { label: 'Imprimir', hint: 'único caso', tone: 'verified' },
              { label: 'Mostrar/Ocultar Columnas', hint: '', tone: 'neutral' },
            ],
            note: 'Se confirmó que ninguna otra grilla del sistema (Turnos, Pacientes, Internaciones, Producción, Nomenclador de Cirugías) tiene estos botones de exportación.',
          } },
          { type: 'step', number: 2, image: null, alt: '', caption: '', explanation: 'Consultorios → Conf. Edilicia → Consultorios muestra la agenda: qué profesional atiende en qué consultorio, qué día y horario.', lookFor: 'Filtros combinables de Especialidad, Profesional, Día y C.E.', doThis: 'Filtrá por el nombre del profesional (o su especialidad) para ver sus franjas horarias.' },
          { type: 'warning', text: 'Si un profesional no tiene consultorio asignado, la columna "Tipo" muestra "Sin Consultorio".' },
          { type: 'text', text: 'El módulo Consultorios también tiene su propia Configuración (engranaje ⚙ dentro de Consultorios), aunque por ahora es muy breve: solo incluye "Plantillas de Informes".' },
        ],
        quiz: [
          { type: 'order-steps', instruction: 'Ordená los pasos para saber qué día y horario atiende un profesional determinado.', steps: [
            'Ir a Consultorios → Conf. Edilicia → Consultorios',
            'Filtrar por el nombre del profesional (o su especialidad)',
            'Revisar la columna Día y Horario en la tabla resultante',
          ] },
          { type: 'true-false', question: 'La pantalla de Profesionales es la única del sistema con botones de exportación (CSV/Excel/PDF).', answer: true, explanation: 'Se verificó que ninguna de las otras grillas (Turnos, Pacientes, Internaciones, Producción, Nomenclador de Cirugías) tiene esos botones.' },
          { type: 'true-false', question: 'La Configuración del módulo Consultorios tiene varios ítems para configurar.', answer: false, explanation: 'Por ahora solo tiene un ítem: "Plantillas de Informes".' },
        ],
      },
    ],
  },

  // ---------------------------------------------------------------- INTERNACIONES
  {
    id: 'internaciones',
    title: 'Internaciones',
    icon: '🛏️',
    summary: 'Gestión de camas y pacientes internados: ocupación de salas en tiempo real, listado de internaciones, diagnósticos y catálogos.',
    audience: 'Personal de enfermería, administración de camas, estadística/epidemiología y dirección médica.',
    difficulty: 'basico',
    lessons: [
      {
        id: 'tablero-inicio',
        title: 'El tablero de inicio',
        minutes: 3,
        difficulty: 'basico',
        blocks: [
          { type: 'text', text: 'Internaciones se llama "Epicrisis" internamente en el sistema, pero en el menú lateral vas a verlo como "Internaciones". Su pantalla de Inicio es un tablero pensado para tener una foto rápida del hospital.' },
          { type: 'step', number: 1, image: null, alt: '', caption: '', explanation: 'Al entrar a Internaciones ves un dashboard con Internaciones Pendientes por sala/servicio, la Ocupación total de Camas, y un Ranking de Diagnósticos según la estación del año.', lookFor: 'El desglose de ocupación: Ocupadas / Reservadas / En Reparación / Fuera de Servicio / Libres, y el porcentaje total.', doThis: 'Usá este tablero antes de entrar a cada sala, para tener una idea general del estado del hospital sin recorrer sala por sala.', diagram: {
            variant: 'cards',
            title: 'Ocupación de camas — ejemplo ilustrativo',
            items: [
              { label: 'Ocupadas', value: '62%' },
              { label: 'Libres', value: '24%' },
              { label: 'Reservadas', value: '8%' },
              { label: 'Fuera de Servicio', value: '4%' },
              { label: 'En Reparación', value: '2%' },
            ],
            note: 'Los porcentajes son un ejemplo para mostrar la estructura del tablero — no son datos reales de ningún efector.',
          } },
        ],
        quiz: [
          { type: 'true-false', question: 'El nombre interno del módulo Internaciones en el sistema es "Epicrisis".', answer: true, explanation: 'En el menú lateral figura como "Internaciones", pero internamente el sistema lo llama "Epicrisis".' },
        ],
      },
      {
        id: 'ocupacion-sala',
        title: 'Ver la ocupación de una sala',
        minutes: 4,
        difficulty: 'basico',
        blocks: [
          { type: 'text', text: 'Antes de decidir una internación, es útil saber cuántas camas libres hay en una sala.' },
          { type: 'step', number: 1, image: 'salas.jpg', alt: 'Tabla de Salas del Efector con el total, ocupadas, libres y reservadas por sala', caption: 'Salas del Efector', explanation: 'Internaciones → Salas muestra una tabla con: Sala, Total/Disponibles, Ocupadas, Libres, Reservadas, En Reparación, Fuera de Servicio.', lookFor: 'La fórmula indicada al pie: Disponibles = Ocupadas + Libres + Reservadas. Salas típicas en un efector: Cuidados Intermedios, Emergencias, Hospital de Día, Neonatología, Pediatría, Tocoginecología, Unidad de Cuidados Intensivos, entre otras (varía por hospital).', doThis: 'Ubicá la sala que te interesa y mirá la columna "Libres". Si necesitás el detalle cama por cama, presioná "Ingresar" en esa fila.' },
          { type: 'warning', text: 'El detalle de una sala puede mostrar el nombre y el diagnóstico presuntivo del paciente en cada cama ocupada. Es información clínica sensible — no la dejes visible en pantallas compartidas o proyectores.' },
          { type: 'tip', text: 'Una sala puede tener camas "Fuera de Servicio" que reducen la disponibilidad real aunque figuren en el total — no te quedes solo con el número de "Total".' },
        ],
        quiz: [
          { type: 'multiple-choice', question: 'Si necesitás saber el estado cama por cama de una sala, ¿qué botón usás?', options: ['"Ingresar" en la fila de esa sala', '"Exportar"', '"Nueva Sala"'], correctIndex: 0, explanation: 'El botón "Ingresar" abre el detalle de habitaciones y camas de esa sala.' },
          { type: 'checklist', title: 'Antes de proyectar o compartir esta pantalla, verificá', items: [
            'Que no haya personas sin autorización mirando la pantalla',
            'Que no necesites el detalle de nombre/diagnóstico visible (usar solo el resumen si es posible)',
          ] },
        ],
      },
      {
        id: 'listados-internaciones-diagnosticos',
        title: 'Listado de internaciones y diagnósticos',
        minutes: 4,
        difficulty: 'intermedio',
        blocks: [
          { type: 'text', text: 'Además del tablero y las salas, hay dos listados históricos: Internaciones y Diagnósticos, con toda la actividad del efector.' },
          { type: 'step', number: 1, image: null, alt: '', caption: '', explanation: 'Internaciones → Internaciones lista el historial completo: Ingreso, Sala, Habitación, N° Doc., Nombre, Diag. Presuntivo, Egreso, Diag. Principal.', lookFor: 'La acción "Continuar" en una fila indica que esa internación sigue abierta (todavía no tuvo egreso).', doThis: 'Usá el buscador (Nombre/Apellido/Documento) y el interruptor "Vista Detallada / Totales" según lo que necesites ver.', diagram: {
            variant: 'table',
            title: 'Listado de Internaciones — estructura de la tabla',
            columns: ['Ingreso', 'Sala', 'Habitación', 'N° Doc.', 'Nombre', 'Diag. Presuntivo', 'Egreso'],
            rows: [
              ['18/10', 'Pediatría', '204', '◼', '◼', '◼', '—'],
              ['12/10', 'UCI', '101', '◼', '◼', '◼', '20/10'],
            ],
            note: 'Los datos de pacientes se muestran tapados a propósito — no son reales. La fila sin Egreso ("—") sigue abierta.',
          } },
          { type: 'step', number: 2, image: null, alt: '', caption: '', explanation: 'Internaciones → Diagnósticos sigue el mismo patrón, pero organizado por diagnóstico: Tipo de Diagnóstico (Principal / Parcial N°1 / N°2...), Sala, Nombre, Edad.', lookFor: 'El mismo buscador y el mismo interruptor Vista Detallada / Totales.', doThis: 'Usalo cuando necesites analizar diagnósticos en vez de camas.' },
          { type: 'warning', text: 'Ambos listados exponen de inmediato nombre, documento y diagnóstico de pacientes reales apenas se hace una búsqueda. Extremá el cuidado de privacidad: no dejes estas pantallas abiertas o proyectadas.' },
        ],
        quiz: [
          { type: 'multiple-choice', question: '¿Qué significa la acción "Continuar" en la fila de una internación?', options: ['Que la internación sigue abierta, sin egreso', 'Que hay que confirmar el alta', 'Que el paciente pidió el alta voluntaria'], correctIndex: 0, explanation: 'Es la marca de que esa internación todavía no se cerró.' },
        ],
      },
      {
        id: 'nomencladores',
        title: 'Nomencladores: CIE-10 y Cirugías',
        minutes: 3,
        difficulty: 'basico',
        blocks: [
          { type: 'text', text: 'Los nomencladores son catálogos de referencia — no tienen datos de pacientes, así que se pueden consultar sin ningún cuidado especial de privacidad.' },
          { type: 'step', number: 1, image: null, alt: '', caption: '', explanation: 'Internaciones → Nomencladores → CIE-10 busca por Código o Descripción (la búsqueda es obligatoria para ver resultados).', lookFor: 'Ejemplo real: buscar "diabetes" devuelve todos los códigos relacionados (E10 a E14 y variantes, O24 —diabetes en el embarazo—, P70 —diabetes neonatal—, etc.).', doThis: 'Escribí el nombre de la enfermedad o el código que buscás.', diagram: {
            variant: 'table',
            title: 'CIE-10 — resultado real de buscar "diabetes"',
            columns: ['Código', 'Descripción'],
            rows: [
              ['E10–E14', 'Diabetes mellitus (y variantes)'],
              ['O24', 'Diabetes mellitus en el embarazo'],
              ['P70', 'Diabetes mellitus neonatal transitoria'],
            ],
            note: 'Este catálogo no tiene datos de pacientes, así que estos códigos sí son los resultados reales verificados en el relevamiento.',
          } },
          { type: 'step', number: 2, image: null, alt: '', caption: '', explanation: 'Internaciones → Nomencladores → Cirugías sigue el mismo patrón para procedimientos quirúrgicos.', lookFor: 'Mismo tipo de búsqueda por Código/Descripción.', doThis: 'Usalo para confirmar el código exacto de un procedimiento.' },
        ],
        quiz: [
          { type: 'true-false', question: 'El Nomenclador CIE-10 muestra datos de pacientes.', answer: false, explanation: 'Es un catálogo institucional de referencia, sin ningún dato de pacientes.' },
        ],
      },
    ],
  },

  // ---------------------------------------------------------------- QUIRÓFANO
  {
    id: 'quirofano',
    title: 'Quirófano',
    icon: '🏥',
    summary: 'Todo el circuito de cirugías: lista de espera, cirugías con turno, carga de una nueva cirugía, informes y nomenclador.',
    audience: 'Personal de quirófano, cirujanos, anestesistas, enfermería quirúrgica y administración de quirófano.',
    difficulty: 'intermedio',
    lessons: [
      {
        id: 'inicio-alertas',
        title: 'La pantalla de inicio y sus alertas',
        minutes: 4,
        difficulty: 'basico',
        blocks: [
          { type: 'text', text: 'La pantalla de Inicio de Quirófano funciona como un panel de control diario: de un vistazo se ve qué cirugías necesitan atención.' },
          { type: 'step', number: 1, image: 'quirofano-inicio.jpg', alt: 'Pantalla de inicio de Quirófano con tarjetas de alertas y accesos', caption: 'Inicio de Quirófano', explanation: 'Vas a ver accesos a Cirugías, Informes y Nomenclador, más dos bloques de alertas.', lookFor: '"Alertas para el usuario [tu usuario] - [tu rol]" (personales, como "Cirugías sin Cerrar" o "Cirugías en espera sin turno") y "Alertas (generales del efector)", con el mismo tipo de tarjetas pero para todo el hospital.', doThis: 'Si una tarjeta muestra un número mayor a 0, presioná "Ver Detalle" para ver esas cirugías puntuales.' },
        ],
        quiz: [
          { type: 'multiple-choice', question: 'Si la tarjeta "Cirugías sin Cerrar" siempre muestra 0, ¿qué conviene revisar?', options: ['Que el usuario tenga cirugías asignadas como cirujano', 'Que el navegador esté actualizado', 'Nada, es un error del sistema'], correctIndex: 0, explanation: 'Si el usuario no tiene cirugías asignadas, no va a tener alertas personales que mostrar.' },
        ],
      },
      {
        id: 'lista-espera-turno',
        title: 'Lista de espera y cirugías con turno',
        minutes: 4,
        difficulty: 'intermedio',
        blocks: [
          { type: 'text', text: 'TIMBÓ separa la gestión de cirugías en dos circuitos: Quirófanos Centrales y Quirófanos Hosp Día. Vas a ver esta división en varias pantallas del módulo.' },
          { type: 'step', number: 1, image: null, alt: '', caption: '', explanation: 'Quirófano → Cirugías → Lista de Espera y Cirugías c/Turno comparten la misma estructura: dos pestañas superiores (Centrales / Hosp Día), un buscador por Nombre/Apellido/Documento y un filtro adicional.', lookFor: '"Cirugías c/Turno" agrega además dos vistas: Lista y Calendario.', doThis: 'Elegí la pestaña del circuito que corresponda antes de buscar.', diagram: {
            variant: 'tabs',
            title: 'Pestañas superiores de Lista de Espera / Cirugías c/Turno',
            tabs: ['Quirófanos Centrales', 'Quirófanos Hosp Día'],
            active: 0,
            note: 'Son dos circuitos separados — elegí la pestaña antes de buscar, no se mezclan en una sola lista.',
          } },
          { type: 'tip', text: 'Cuando no hay cirugías pendientes, el sistema muestra: "Sin Cirugías Pendientes - Por favor ingrese un filtro de búsqueda o cargue una nueva."' },
        ],
        quiz: [
          { type: 'true-false', question: 'Quirófanos Centrales y Quirófanos Hosp Día son el mismo circuito.', answer: false, explanation: 'Son dos circuitos distintos que el sistema separa en pestañas.' },
        ],
      },
      {
        id: 'nueva-cirugia',
        title: 'Cargar una Nueva Cirugía',
        minutes: 6,
        difficulty: 'intermedio',
        blocks: [
          { type: 'text', text: 'Cargar una cirugía es uno de los formularios más largos del sistema, pero se completa por secciones y el sistema te avisa exactamente qué falta.' },
          { type: 'prereq', items: ['Conocer al paciente (para buscarlo)', 'Saber quién es el cirujano asignado', 'Tener el diagnóstico presuntivo (código CIE-10)', 'Tener el procedimiento quirúrgico presuntivo'] },
          { type: 'step', number: 1, image: 'nueva-cirugia.jpg', alt: 'Formulario de Nueva Cirugía, con las secciones Definir Cirugía y Datos Presuntivos', caption: 'Ficha de la Cirugía (formulario vacío)', explanation: 'Al abrir Quirófano → Cirugías → Nueva Cirugía aparece la "Ficha de la Cirugía", con el estado "ANULADA" hasta que se completa y confirma.', lookFor: 'Tres secciones: Definir Cirugía, Datos Presuntivos y Asignación de Prioridades.', doThis: 'En "Definir Cirugía", completá como mínimo: Fecha Pedido, Tipo de Cirugía, Oncológica, Paciente, Procedencia-Sub-Sector, Cirujano, Diagnóstico Presuntivo, Diagnóstico a imprimir, Procedimiento Quirúrgico Presuntivo, Procedimiento a imprimir y Especialidad.' },
          { type: 'step', number: 2, image: null, alt: '', caption: '', explanation: 'En "Datos Presuntivos" hay más campos obligatorios.', lookFor: 'Tipo Anestesia, Destino, y cuatro campos Sí/No (Requiere Diag. por Imágenes, Hemoterapia, Torre Laparoscopia, Materiales Especiales), más Tiempo Estimado de Cirugía y Días de Post-Operatorio.', doThis: 'Completá todos los que correspondan según el caso real.' },
          { type: 'step', number: 3, image: null, alt: '', caption: '', explanation: '"Asignación de Prioridades" (Score y Fecha de Espera Máxima) es opcional.', lookFor: 'Score va de 0 a 10.', doThis: 'Completalo solo si conocés la urgencia relativa del caso. Al terminar, presioná Confirmar.' },
          { type: 'warning', text: '"Área Quirúrgica" no muestra aviso de obligatoriedad al dejarla vacía, pero conviene completarla igual: define en qué circuito (Centrales / Hosp Día) queda la cirugía.' },
          { type: 'tip', text: 'Si falta un campo obligatorio, el sistema no guarda nada: muestra un aviso en letra naranja debajo de cada campo faltante. Podés corregir y volver a presionar Confirmar sin perder lo ya cargado.' },
          { type: 'practice', text: 'Sin llegar a confirmar (para no crear un registro real), abrí el formulario de Nueva Cirugía y recorré las tres secciones, identificando qué campos ya conocés de memoria y cuáles necesitás averiguar antes de cargar una cirugía real.' },
        ],
        quiz: [
          { type: 'order-steps', instruction: 'Ordená correctamente el procedimiento para cargar una Nueva Cirugía.', steps: [
            'Ir a Quirófano → Cirugías → Nueva Cirugía',
            'Completar los campos obligatorios de "Definir Cirugía"',
            'Completar los campos obligatorios de "Datos Presuntivos"',
            'Completar opcionalmente "Asignación de Prioridades"',
            'Presionar Confirmar',
          ] },
          { type: 'multiple-choice', question: '¿Qué pasa si presionás Confirmar y falta un campo obligatorio?', options: ['El sistema guarda igual con datos incompletos', 'Aparece un aviso naranja debajo del campo faltante y no se guarda nada', 'Se cierra el formulario sin avisar'], correctIndex: 1, explanation: 'El sistema valida campo por campo y no permite guardar hasta completarlos.' },
          { type: 'true-false', question: '"Área Quirúrgica" muestra siempre un aviso si se deja vacía.', answer: false, explanation: 'Es un caso llamativo: no mostró aviso de obligatoriedad en las pruebas, aunque conviene completarla igual.' },
        ],
      },
      {
        id: 'informes',
        title: 'Informes de Quirófano',
        minutes: 4,
        difficulty: 'basico',
        blocks: [
          { type: 'text', text: 'Desde la pantalla de Inicio del módulo, en la sección "Informes", hay tres documentos imprimibles y una pantalla de producción.' },
          { type: 'concepts', items: [
            { term: 'Parte Qx Diario', def: 'Modal con un campo Fecha. El botón Imprimir abre una pestaña nueva con una página HTML lista para imprimir (Ctrl+P) — no descarga ningún archivo ni genera un PDF en el servidor.' },
            { term: 'Parte de Enfermería', def: 'Mismo modal y mismo mecanismo que el Parte Qx Diario.' },
            { term: 'Cx c/Fecha Probable', def: 'Mismo modal y mismo mecanismo.' },
            { term: 'Producción', def: 'Es una pantalla propia (no modal): búsqueda por Procedimiento/Diagnóstico principal, con una tabla de Profesional, Total Prod. y Total x Rol.' },
          ] },
          { type: 'diagram', variant: 'list', title: 'Sección "Informes" — accesos desde Inicio de Quirófano', items: [
            { label: 'Parte Qx Diario', hint: 'modal → imprimible', tone: 'neutral' },
            { label: 'Parte de Enfermería', hint: 'modal → imprimible', tone: 'neutral' },
            { label: 'Cx c/Fecha Probable', hint: 'modal → imprimible', tone: 'neutral' },
            { label: 'Producción', hint: 'pantalla propia', tone: 'neutral' },
          ], note: 'Los tres primeros abren el mismo tipo de modal y terminan en una página lista para Ctrl+P. Producción no es un modal, es una pantalla de búsqueda aparte.' },
          { type: 'warning', text: 'El pie de la página del Parte Qx Diario expone un texto técnico con el nombre interno del servidor. No es algo que hiciste mal vos — es un dato que el sistema no debería mostrar, y está reportado como hallazgo a Sectorial Informática.' },
          { type: 'text', text: 'Además de los informes, Quirófano tiene su propio catálogo de procedimientos: el "Nomenclador Nacional de Cirugías" (Quirófano → Nomenclador). Es un catálogo institucional —sin datos de pacientes—, con cientos de filas ordenadas alfabéticamente (por ejemplo "08.05.24 - APENDICECTOMIA"), que se muestra completo sin necesidad de buscar aunque también admite filtrar.' },
        ],
        quiz: [
          { type: 'true-false', question: 'El botón "Imprimir" del Parte Qx Diario descarga un archivo PDF.', answer: false, explanation: 'Abre una pestaña con una página HTML pensada para el Ctrl+P del navegador, no descarga ningún archivo.' },
          { type: 'true-false', question: 'El Nomenclador de Quirófano muestra datos de pacientes.', answer: false, explanation: 'Es un catálogo institucional de procedimientos, igual que el CIE-10 de Internaciones: sin ningún dato de pacientes.' },
        ],
      },
      {
        id: 'configuracion-quirofano',
        title: 'Configuración del módulo (solo Administrador)',
        minutes: 3,
        difficulty: 'avanzado',
        blocks: [
          { type: 'warning', text: 'Esta pantalla es exclusivamente para personal con rol de Administrador. Si no administrás el circuito de Quirófano, probablemente no la necesites para tu trabajo diario.' },
          { type: 'text', text: 'Quirófano → Configuración agrupa los parámetros generales del circuito quirúrgico del efector: desde cuántos días de anticipación avisan las alertas, hasta qué especialidades y materiales están habilitados.' },
          { type: 'diagram', variant: 'table', title: 'Quirófano → Configuración — ítems observados', columns: ['Ítem', 'Descripción'], rows: [
            ['Alertas', 'Días de anticipación para cada tipo de alerta'],
            ['Quirófanos', 'Salas de quirófano habilitadas en el efector'],
            ['Roles/Profesionales', 'Profesionales que participan en cirugías y su rol'],
            ['Plantillas de Informes', 'Plantillas de Consentimiento y Resumen Final'],
            ['Días para Carga Diferida', 'Cuántos días hacia atrás se puede cargar un turno ya pasado'],
            ['Materiales/Insumos Habilitados', '—'],
            ['Especialidades Quirúrgicas habilitadas', '—'],
            ['Prefijos Habilitados (Nomenclador Nacional)', 'Qué códigos de cirugía están habilitados para el efector'],
            ['Envío automático de e-mails — Cambios de Estado', 'Notificaciones automáticas'],
            ['Envío automático de e-mails — Parte Quirúrgico Diario', 'Notificaciones automáticas'],
          ], note: 'Listado de ítems confirmado por observación directa del menú — no se entró a modificar cada uno, por tratarse de configuración que afecta a todo el efector.' },
          { type: 'tip', text: '"Roles/Profesionales" acá es un concepto distinto al de "Roles y permisos" de acceso al sistema (ver lección de Primeros pasos): este ítem define los roles del equipo quirúrgico en una cirugía puntual —Cirujano, Anestesista, Instrumentador—, no quién puede entrar a qué pantalla.' },
        ],
        quiz: [
          { type: 'true-false', question: '"Roles/Profesionales" dentro de Configuración de Quirófano define quién puede acceder a cada módulo del sistema.', answer: false, explanation: 'Es un concepto distinto: define los roles del equipo quirúrgico (Cirujano, Anestesista, Instrumentador) dentro de una cirugía, no permisos de acceso.' },
        ],
      },
    ],
  },

  // ---------------------------------------------------------------- ADMINISTRACIÓN
  {
    id: 'administracion',
    title: 'Administración',
    icon: '⚙️',
    summary: 'Configuración general del sistema para el efector: módulos activos, integración con PACS, Red Provincial de Salud y plantillas.',
    audience: 'Exclusivamente personal con rol de Administrador.',
    difficulty: 'avanzado',
    lessons: [
      {
        id: 'que-es-administracion',
        title: 'Qué es Administración y quién debería usarlo',
        minutes: 2,
        difficulty: 'avanzado',
        blocks: [
          { type: 'warning', text: 'Este módulo es exclusivamente para personal con rol de Administrador. Si no administrás el sistema, probablemente no lo necesites para tu trabajo diario — y varias de sus acciones son irreversibles o afectan a todo el hospital.' },
          { type: 'text', text: 'Administración → tiene 5 accesos: Módulos Habilitados, Compatibilidad Informes/PACS, RPS, Plantillas de Informes, y la herramienta técnica "Crear esquema de controles/permisos".' },
          { type: 'diagram', variant: 'list', title: 'Los 5 accesos del menú Administración', items: [
            { label: 'Módulos Habilitados', hint: '🔴 crítica', tone: 'avanzado' },
            { label: 'Compatibilidad Informes/PACS', hint: '', tone: 'neutral' },
            { label: 'RPS', hint: '', tone: 'neutral' },
            { label: 'Plantillas de Informes', hint: '', tone: 'neutral' },
            { label: 'Crear esquema de controles/permisos', hint: '🔴 irreversible', tone: 'avanzado' },
          ], note: 'Las dos marcadas en rojo son las que pueden afectar a todo el efector o modificar la base de datos — nunca se ejecutaron durante el relevamiento, por regla de seguridad.' },
        ],
        quiz: [],
      },
      {
        id: 'modulos-habilitados',
        title: 'Módulos Habilitados',
        minutes: 3,
        difficulty: 'avanzado',
        blocks: [
          { type: 'step', number: 1, image: 'modulos-habilitados.jpg', alt: 'Tabla de Módulos Habilitados con botón Desactivar Módulo por cada fila', caption: 'Módulos Habilitados', explanation: 'Muestra los módulos activos del efector, cada uno con un botón "Desactivar Módulo".', lookFor: 'El botón "+ Nuevo" para habilitar un módulo adicional.', doThis: 'Solo mirá esta pantalla si necesitás confirmar qué módulos están activos — no toques "Desactivar Módulo" sin estar seguro.' },
          { type: 'warning', text: 'Desactivar un módulo lo deja inaccesible para TODOS los usuarios del efector. No debe usarse sin control, porque afecta la operación diaria de todo el hospital.' },
        ],
        quiz: [
          { type: 'true-false', question: 'Desactivar un módulo solo afecta a la sesión del usuario que lo desactivó.', answer: false, explanation: 'Afecta a todos los usuarios del efector — es una acción crítica que debe usarse con control.' },
        ],
      },
      {
        id: 'rps-pacs-plantillas',
        title: 'RPS, PACS y Plantillas',
        minutes: 4,
        difficulty: 'avanzado',
        blocks: [
          { type: 'concepts', items: [
            { term: 'Compatibilidad Informes/PACS', def: 'Tabla con el parámetro "Url Prefijo Oviyam", para el acceso al servidor de imágenes médicas, más una sección propia de Plantillas de Informes de diagnóstico por imágenes.' },
            { term: 'RPS', def: 'Tabla con Código de Establecimiento, IP del Establecimiento y URL de Logout — los tres necesarios para que funcione la integración con Red Salud.' },
            { term: 'Plantillas de Informes', def: 'Plantillas generales de impresión. En el relevamiento tenía un solo ítem, "Pulsera para el paciente internado", que figuraba "Sin Definir".' },
          ] },
          { type: 'diagram', variant: 'list', title: 'Administración → RPS — estado observado en HOSP EVA PERON', items: [
            { label: 'Código de Establecimiento', hint: 'Sin Definir', tone: 'unverified' },
            { label: 'IP del Establecimiento', hint: 'Sin Definir', tone: 'unverified' },
            { label: 'URL de Logout', hint: 'Sin Definir', tone: 'unverified' },
          ], note: 'Esto es lo que se observó en el efector relevado — otro efector puede tener estos tres parámetros ya cargados. Si están "Sin Definir", Red Salud no identifica bien al usuario ni al efector.' },
          { type: 'warning', text: 'Los parámetros de RPS son gestionados típicamente por el área de sistemas de cada hospital junto con el Ministerio, no por un usuario cualquiera. Si "Red Salud" no funciona bien en tu efector, revisá primero si estos tres parámetros están cargados.' },
          { type: 'warning', text: '"Crear esquema de controles/permisos" es una herramienta técnica que modifica el esquema de la base de datos. No se debe ejecutar sin confirmar el impacto con Sectorial Informática.' },
        ],
        quiz: [
          { type: 'multiple-choice', question: 'Si el enlace a Red Salud no identifica bien el efector, ¿qué es lo primero que hay que revisar?', options: ['Si los tres parámetros de RPS están cargados en Administración', 'Si el usuario cambió de contraseña recientemente', 'Si el navegador está actualizado'], correctIndex: 0, explanation: 'Sin Código de Establecimiento, IP del Establecimiento y URL de Logout cargados, la integración no identifica al efector.' },
        ],
      },
    ],
  },

  // ---------------------------------------------------------------- RED SALUD
  {
    id: 'red-salud',
    title: 'Red Salud',
    icon: '🌐',
    summary: 'La integración con la Red Provincial de Salud (sistema SICAP), para buscar información de un paciente a nivel provincial.',
    audience: 'Cualquier usuario que necesite consultar datos de un paciente fuera del efector.',
    difficulty: 'intermedio',
    lessons: [
      {
        id: 'acceder-red-salud',
        title: 'Qué es y cómo acceder',
        minutes: 3,
        difficulty: 'intermedio',
        blocks: [
          { type: 'text', text: 'Red Salud te conecta con el sistema provincial (SICAP) para buscar información de un paciente más allá de tu efector.' },
          { type: 'step', number: 1, image: null, alt: '', caption: '', explanation: 'El acceso que realmente funciona es el botón "RED PROVINCIAL DE SALUD" dentro de la tarjeta "Accesos Externos" en la pantalla de Inicio.', lookFor: 'No es el ítem "Red Salud" del menú lateral colapsado — ese solo muestra un tooltip, no navega a ningún lado.', doThis: 'Hacé clic en "RED PROVINCIAL DE SALUD": se abre una pestaña nueva con un buscador de pacientes de la Red Provincial (Datos Personales, Datos Filiatorios, H.C./Legajo Familiar).', diagram: {
            variant: 'list',
            title: 'Encabezado real observado en la pantalla externa (SICAP)',
            items: [
              { label: 'Usuario:', hint: '"."  (vacío)', tone: 'avanzado' },
              { label: 'Nodo:', hint: '"-"  (vacío)', tone: 'avanzado' },
              { label: 'Efector:', hint: '"-"  (vacío)', tone: 'avanzado' },
            ],
            note: 'Esto es lo que se vio realmente en HOSP EVA PERON por no tener los parámetros de RPS cargados — la pantalla igual abre y deja buscar.',
          } },
          { type: 'warning', text: 'Si en tu efector los parámetros de RPS (Administración → RPS) no están cargados, el encabezado de esa pantalla externa va a mostrar "Usuario", "Nodo" y "Efector" vacíos. La pantalla igual carga y deja buscar, pero no queda garantizado que identifique correctamente tu efector — confirmá con Sectorial Informática antes de confiar en una búsqueda ahí si ves ese problema.' },
        ],
        quiz: [
          { type: 'true-false', question: 'El ítem "Red Salud" del menú lateral colapsado es el enlace que hay que usar para entrar a la Red Provincial.', answer: false, explanation: 'Ese ítem solo muestra un tooltip. El acceso real es el botón "RED PROVINCIAL DE SALUD" en la tarjeta "Accesos Externos" de Inicio.' },
        ],
      },
    ],
  },
];

// ---------------------------------------------------------------------------
// RUTA GUIADA "PRIMEROS 15 MINUTOS"
// ---------------------------------------------------------------------------
export const QUICKSTART = {
  title: 'Aprendé TIMBÓ en 15 minutos',
  intro: 'Una ruta corta para conocer lo básico del sistema. Al terminar, vas a poder buscar un paciente, revisar información y saber qué hacer si algo sale mal.',
  steps: [
    { step: 1, title: 'Conocer TIMBÓ', description: SYSTEM_INFO.description },
    { step: 2, title: 'Ingresar', moduleId: 'primeros-pasos', lessonId: 'ingresar' },
    { step: 3, title: 'Conocer la pantalla principal', moduleId: 'primeros-pasos', lessonId: 'interfaz' },
    { step: 4, title: 'Encontrar información (buscar un paciente)', moduleId: 'pacientes', lessonId: 'buscar-paciente' },
    { step: 5, title: 'Realizar una operación básica (ver ocupación de una sala)', moduleId: 'internaciones', lessonId: 'ocupacion-sala' },
    { step: 6, title: 'Verificar un resultado (la ficha del paciente)', moduleId: 'pacientes', lessonId: 'ficha-paciente' },
    { step: 7, title: 'Resolver un problema frecuente', situationId: 'error-laboratorios' },
  ],
  outro: 'Ya conocés lo básico de TIMBÓ. Para seguir, explorá los módulos completos o usá "Quiero hacer..." para resolver una tarea concreta.',
};

// ---------------------------------------------------------------------------
// "¿TENÉS UN PROBLEMA?"
// ---------------------------------------------------------------------------
export const SITUATIONS = [
  {
    id: 'no-encuentro-opcion',
    situation: 'No encuentro una opción o un módulo',
    description: 'Buscás un módulo o un botón en el menú y no aparece.',
    cause: 'El módulo no está habilitado para tu efector, o tu usuario no tiene permiso para verlo.',
    solution: 'Consultá con Administración → Módulos Habilitados (si tenés acceso), o con el administrador del sistema de tu hospital.',
    goesTo: { moduleId: 'administracion', lessonId: 'modulos-habilitados' },
    verified: true,
  },
  {
    id: 'no-deja-guardar',
    situation: 'El sistema no me deja guardar',
    description: 'Completás un formulario, presionás Confirmar o Guardar, y no pasa nada (o aparece un aviso).',
    cause: 'Casi siempre es un campo obligatorio sin completar. TIMBÓ marca en letra naranja, debajo de cada campo, cuál falta.',
    solution: 'Revisá si hay algún aviso naranja debajo de un campo. Completalo y volvé a intentar.',
    goesTo: { moduleId: 'quirofano', lessonId: 'nueva-cirugia' },
    verified: true,
  },
  {
    id: 'no-aparece-registro',
    situation: 'No aparece un registro que busco',
    description: 'Buscás un paciente, una internación o un turno y la tabla queda vacía.',
    cause: 'O el criterio de búsqueda está mal escrito, o el registro realmente no está cargado en el efector.',
    solution: 'Revisá que el criterio esté bien escrito (probá con menos datos, por ejemplo solo apellido). Si seguís sin encontrarlo, puede que el paciente nunca haya sido atendido en este efector.',
    goesTo: { moduleId: 'pacientes', lessonId: 'buscar-paciente' },
    verified: true,
  },
  {
    id: 'me-equivoque-cargando',
    situation: 'Me equivoqué cargando un dato / necesito modificar algo ya guardado',
    description: 'Ya guardaste un registro (por ejemplo una cirugía) y te diste cuenta de un error, o necesitás editarlo.',
    cause: 'No verificado.',
    solution: 'Este relevamiento no llegó a confirmar ningún registro real (por regla de seguridad, nunca se guardó una cirugía ni otro dato de prueba), así que no se pudo comprobar cómo se edita o corrige un registro ya guardado. Si te encontrás con esta situación, lo más seguro es consultar con Sectorial Informática o con un compañero con más experiencia en el sistema.',
    goesTo: null,
    verified: false,
  },
  {
    id: 'error-laboratorios',
    situation: 'La pestaña Laboratorios de un paciente da error',
    description: 'Al abrir la pestaña Laboratorios de la ficha de cualquier paciente, aparece un error 500.',
    cause: 'Es un bug conocido de esta instancia del sistema: falta una columna en la tabla de órdenes de laboratorio. Afecta a todos los pacientes, no es algo que hiciste vos.',
    solution: 'No es un error del usuario. Cerrá la pantalla y reportalo a Sectorial Informática si te lo piden — no hay nada que puedas hacer del lado del usuario para solucionarlo.',
    goesTo: { moduleId: 'pacientes', lessonId: 'ficha-paciente' },
    verified: true,
  },
  {
    id: 'datos-tecnicos-en-error',
    situation: 'Vi datos técnicos del servidor en un mensaje de error',
    description: 'Un mensaje de error muestra nombres de tablas, rutas de archivos, o el nombre interno del servidor.',
    cause: 'El sistema tiene información de depuración expuesta en esta instancia — es un problema de configuración del sistema, no algo que provocó el usuario.',
    solution: 'No intentes "solucionarlo" vos: cerrá la pantalla y, si es necesario, reportalo a Sectorial Informática.',
    goesTo: null,
    verified: true,
  },
  {
    id: 'red-salud-no-confiable',
    situation: 'Red Salud no identifica bien mi efector',
    description: 'Al entrar a la Red Provincial de Salud, el encabezado muestra "Usuario", "Nodo" y "Efector" vacíos.',
    cause: 'Los parámetros de RPS (Código de Establecimiento, IP del Establecimiento, URL de Logout) no están cargados en Administración → RPS para tu efector.',
    solution: 'La pantalla igual permite buscar, pero no hay garantía de que quede bien asociada a tu efector. Pedile a un Administrador que revise Administración → RPS, o consultá con Sectorial Informática.',
    goesTo: { moduleId: 'red-salud', lessonId: 'acceder-red-salud' },
    verified: true,
  },
  {
    id: 'sesion-se-cierra-sola',
    situation: 'La sesión se cierra sola / me pide loguearme de nuevo',
    description: 'Estás usando el sistema y, sin haber cerrado sesión vos, te encontrás de nuevo en la pantalla de login.',
    cause: 'Vencimiento de sesión por inactividad — es el comportamiento típico de este tipo de sistemas web. No se confirmó el tiempo exacto durante el relevamiento.',
    solution: 'Volvé a iniciar sesión con tu usuario y contraseña. No es un error ni significa que perdiste información ya guardada.',
    goesTo: { moduleId: 'primeros-pasos', lessonId: 'ingresar' },
    verified: true,
  },
  {
    id: 'boton-deshabilitado',
    situation: 'Un botón aparece deshabilitado o no hace nada al presionarlo',
    description: 'Un botón se ve "apagado", o lo presionás y no pasa nada visible.',
    cause: 'Casi siempre es porque falta completar algún campo obligatorio antes. Con menos frecuencia, puede ser que tu usuario no tenga el permiso correspondiente para esa acción.',
    solution: 'Revisá si hay campos obligatorios sin completar en el formulario. Si el botón sigue sin funcionar, consultá con Administración o con Sectorial Informática por tu nivel de permisos.',
    goesTo: null,
    verified: true,
  },
  {
    id: 'buscador-lento-no-responde',
    situation: 'El buscador tarda mucho o no responde',
    description: 'Hiciste una búsqueda (de pacientes, internaciones, diagnósticos) y la tabla tarda varios segundos en aparecer, o parece colgada.',
    cause: 'El criterio de búsqueda es muy amplio (por ejemplo, pocas letras de un apellido común) y el sistema tiene que revisar decenas de miles de registros.',
    solution: 'Esperá a que termine, o cancelá y repetí la búsqueda con un criterio más específico: apellido y nombre completos, o número de documento/H.C.',
    goesTo: { moduleId: 'pacientes', lessonId: 'buscar-paciente' },
    verified: true,
  },
];

// ---------------------------------------------------------------------------
// "QUIERO HACER..." — búsqueda orientada a tareas
// ---------------------------------------------------------------------------
export const TASKS = [
  { id: 'buscar-paciente', question: '¿Cómo busco un paciente?', keywords: ['buscar', 'paciente', 'encontrar', 'localizar'], moduleId: 'pacientes', lessonId: 'buscar-paciente', title: 'Buscar un paciente', level: 'basico', minutes: 4 },
  { id: 'ver-camas-libres', question: '¿Cómo veo si hay camas libres?', keywords: ['camas', 'libres', 'sala', 'ocupacion', 'internacion'], moduleId: 'internaciones', lessonId: 'ocupacion-sala', title: 'Ver la ocupación de una sala', level: 'basico', minutes: 4 },
  { id: 'consultar-turnos-profesional', question: '¿Cómo consulto los turnos de un profesional?', keywords: ['turnos', 'profesional', 'agenda', 'consultorio', 'horario'], moduleId: 'consultorios', lessonId: 'profesionales-y-agenda', title: 'Consultar profesionales y su agenda', level: 'basico', minutes: 4 },
  { id: 'ver-listado-profesionales', question: '¿Dónde encuentro el listado de profesionales del hospital?', keywords: ['profesionales', 'listado', 'medicos', 'matricula'], moduleId: 'consultorios', lessonId: 'profesionales-y-agenda', title: 'Consultar profesionales y su agenda', level: 'basico', minutes: 4 },
  { id: 'buscar-cie10', question: '¿Cómo busco un código de diagnóstico (CIE-10)?', keywords: ['cie-10', 'cie10', 'diagnostico', 'codigo'], moduleId: 'internaciones', lessonId: 'nomencladores', title: 'Nomencladores: CIE-10 y Cirugías', level: 'basico', minutes: 3 },
  { id: 'cirugias-pendientes', question: '¿Cómo veo las cirugías pendientes de un usuario?', keywords: ['cirugias', 'pendientes', 'alertas', 'quirofano'], moduleId: 'quirofano', lessonId: 'inicio-alertas', title: 'La pantalla de inicio y sus alertas', level: 'basico', minutes: 4 },
  { id: 'cambiar-contrasena', question: '¿Cómo cambio mi contraseña?', keywords: ['contraseña', 'clave', 'password', 'cambiar'], moduleId: 'primeros-pasos', lessonId: 'interfaz', title: 'Conocer la pantalla principal', level: 'basico', minutes: 4 },
  { id: 'cerrar-sesion', question: '¿Cómo cierro sesión?', keywords: ['cerrar', 'sesion', 'salir', 'logout'], moduleId: 'primeros-pasos', lessonId: 'interfaz', title: 'Conocer la pantalla principal', level: 'basico', minutes: 4 },
  { id: 'cargar-cirugia', question: '¿Cómo cargo una cirugía nueva?', keywords: ['cargar', 'cirugia', 'nueva', 'quirofano'], moduleId: 'quirofano', lessonId: 'nueva-cirugia', title: 'Cargar una Nueva Cirugía', level: 'intermedio', minutes: 6 },
  { id: 'exportar-listado', question: '¿Cómo exporto un listado a Excel o PDF?', keywords: ['exportar', 'excel', 'pdf', 'csv', 'imprimir'], moduleId: 'consultorios', lessonId: 'profesionales-y-agenda', title: 'Consultar profesionales y su agenda', level: 'basico', minutes: 4 },
  { id: 'imprimir-parte-diario', question: '¿Cómo imprimo el parte quirúrgico diario?', keywords: ['imprimir', 'parte', 'diario', 'quirurgico', 'informe'], moduleId: 'quirofano', lessonId: 'informes', title: 'Informes de Quirófano', level: 'basico', minutes: 4 },
  { id: 'ver-ocupacion-total', question: '¿Cómo veo la ocupación total del hospital?', keywords: ['ocupacion', 'total', 'tablero', 'camas', 'internaciones'], moduleId: 'internaciones', lessonId: 'tablero-inicio', title: 'El tablero de inicio', level: 'basico', minutes: 3 },
  { id: 'ver-ficha-paciente', question: '¿Cómo veo el historial completo de un paciente?', keywords: ['ficha', 'historial', 'paciente', 'internaciones', 'cirugias'], moduleId: 'pacientes', lessonId: 'ficha-paciente', title: 'La ficha del paciente', level: 'basico', minutes: 5 },
  { id: 'entrar-red-salud', question: '¿Cómo consulto un paciente en la Red Provincial de Salud?', keywords: ['red salud', 'sicap', 'provincial', 'externo'], moduleId: 'red-salud', lessonId: 'acceder-red-salud', title: 'Qué es y cómo acceder', level: 'intermedio', minutes: 3 },
  { id: 'ver-altas-del-dia', question: '¿Cómo veo las altas del día?', keywords: ['altas', 'dia', 'pacientes'], moduleId: 'pacientes', lessonId: 'altas-del-dia', title: 'Ver las altas del día', level: 'basico', minutes: 3 },
  { id: 'buscar-procedimiento-quirurgico', question: '¿Dónde busco el código de un procedimiento quirúrgico?', keywords: ['procedimiento', 'nomenclador', 'cirugia', 'codigo', 'quirofano'], moduleId: 'quirofano', lessonId: 'informes', title: 'Informes de Quirófano', level: 'basico', minutes: 4 },
  { id: 'ver-configuracion-quirofano', question: '¿Qué se configura en Quirófano → Configuración?', keywords: ['configuracion', 'quirofano', 'alertas', 'roles', 'materiales'], moduleId: 'quirofano', lessonId: 'configuracion-quirofano', title: 'Configuración del módulo (solo Administrador)', level: 'avanzado', minutes: 3 },
  { id: 'volver-pantalla-principal', question: '¿Cómo vuelvo a la pantalla principal?', keywords: ['volver', 'atras', 'inicio', 'menu principal', 'home'], moduleId: 'primeros-pasos', lessonId: 'interfaz', title: 'Conocer la pantalla principal', level: 'basico', minutes: 4 },
];
