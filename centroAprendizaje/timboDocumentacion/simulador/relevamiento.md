# Relevamiento de pantallas de TIMBÓ (Bandeja de trámites) para el simulador

Hecho en el Chrome de la usuaria, con su sesión, solo mirando (nada guardado, enviado ni firmado).
Fuente: https://tramites.santafe.gob.ar

## Tablero de Inicio (25/11/2026)
- Título «Tablero de Inicio», botón «Actualizar» (gris si no hay bandeja elegida, naranja con una elegida).
- Columna «Bandejas»: buscador «Buscar», píldoras «Con procesos en curso (0)» y «Todas (6)».
- «Todas» lista tarjetas (ícono en círculo naranja claro + nombre + «0 procesos en curso»):
  Expedientes - Solicitud de caratulación · Expedientes - Gestión · Expedientes - Gestión de visualización ·
  Documentos oficiales - Gestión · Internas (ícono flecha ↙) · Autorregistro.
- Al elegir una: título de la bandeja; pestaña «En curso / 0 procesos en curso» (barra degradé a la izquierda);
  recuadro naranja «Procesos en curso» con botón naranja «Todos (0) ▾» (opciones: Todos (0), 0 a 30 días (0),
  0 a 60 días (0), 0 a 90 días (0), 0 a 180 días (0), 0 a 365 días (0)); tabla con columnas «Nº de proceso»,
  «Fecha de arribo», «Estado», «Permanencia (en días)»; vacío: «No hay instancias disponibles en la bandeja»;
  pie «Items per page: 10 ▾», «0 of 0», botones |< < > >|.

## Expedientes (submenú, íconos: edit_document, bookmark_manager, search, preview, folder_supervised)
### Consulta (#/consulta_ee)
- Título «Consulta». «Tipo de búsqueda *» (select con filtro): Numero de Expediente · Expedientes Iniciados por Mi ·
  Expedientes Tramitados por Mi · Expedientes Caratulados por Mi · Expedientes Caratulados en mi Repartición ·
  Expedientes Caratulados en mi Jerarquía.
- Leyenda fija: «Los expedientes generados en formato papel se podrán consultar desde:
  https://www.santafe.gov.ar/expedientes-web/» (enlace naranja).
- «Numero de Expediente»: campo «Nro de Expediente *» + botón lupa (borde naranja). Al buscar, el campo queda gris
  con una ✕ (con «123» no mostró resultado ni mensaje).
- Las demás: «Desde *» (fecha, por defecto hace 15 días) con ✕, «Hasta *» (hoy) con ✕, «Trámite» (select),
  «Motivo» (texto), botón «Buscar» (borde naranja). Sin fechas: «Debe completar el rango de fechas donde encontrar
  los expedientes» (rojo). Resultado: tabla «Nro. de EE | Iniciador | Trámite | Motivo»; vacía: «Aún no has agregado
  ningún registro»; paginado «Anterior [1] Siguiente».
- Con el usuario de la usuaria (Informática) no apareció ningún expediente (repartición/jerarquía, 01/11 a 25/11).
### Visibilidad (#/admin_visibilidad_ee)
- Título «Visibilidad». «Buscar Expediente» + botón lupa.
### Gestión de visualización (#/solicitud_vista_expediente)
- Bandeja: pestañas «En Curso / Finalizadas / Vistas Compartidas»; filtros Buscar · Buscar Etiqueta · Estadío ·
  chip «Fecha de creación - Más reciente» · Desde · Hasta; Acciones › «Gestionar Etiquetas»; «+».
- «+» → pantalla «‹ Nuevo Trámite», buscador «Buscar», «2 trámites disponibles», filas con punto naranja y «Iniciar ›»:
  «Solicitud vista de expediente» y «Compartir Vista de Expediente».
- «Formulario Gestión de visualización de expedientes»: «Búsqueda de Expediente» › «Numero de Expediente *» + lupa.
- «Formulario Compartir Vista de Expediente»: Datos del Iniciador (Nombre, Apellido, Email, Oficina: grises, solo
  lectura) · Filtros de Búsqueda (Número de Expediente, Tema/Código de Trámite, Motivo, Solicitante, Fecha de
  Modificación (Desde)/(Hasta), Oficina Caratuladora Superior, Oficina Actual Superior) · «Buscar» · leyenda verde
  «El límite de expedientes por búsqueda es de 1000. El límite para seleccionar es de 500.» · sin filtros: «Debe
  indicar algún filtro para la búsqueda de EE»; sin resultados: «No se han encontrado expedientes.» · tablas
  «Expedientes» y «Expedientes Seleccionados» (Número de Expediente, Tema, Motivo, Solicitante, Oficina
  Caratuladora, Oficina Actual, Fecha de Modificación; la primera con casilla) · «Reiniciar Selección» ·
  «Agregar Destinatarios Desde: *» (Usuarios | Lista de Agentes | Oficina | Lista de Ciudadanos | Ciudadanos) ·
  «Fechas de Visualización»: Fecha de Inicio (hoy, con ✕) y Fecha de Fin * · «Guardar».
- La flecha ‹ de cualquier formulario SIEMPRE pregunta «¿Desea volver y descartar los cambios realizados?», aunque
  no se haya tocado nada.

## Documentos oficiales (submenú: Gestión [edit_document], Consulta [search], Visibilidad [preview])
### Consulta (#/consulta_do)
- «Tipo de búsqueda *»: Numero de Documento Oficial · Documentos Firmados por Mi · Documentos Firmados por Mi
  Repartición · Por referencia del Documento Oficial.
- Con rango: «Desde *», «Hasta *», «Filtrar por Tipo de Actuación» (multiselección, por defecto TODAS:
  AA, ACTA, ANT, AOF, CA, CC, CD, CE, CEI, CERESP, CERT, CF, CFImp, CIREL, CM, CON, CONE, CPR, CPU, DEC, DISIMP,
  DISPRE, DO, DOC, DOCADM, DOCFIN, DOCLEG, DOCPE, EE, EOF, FORM, FT, GCR, IER, IERC, IF, IMPOF, IMPPre, IPre, LA,
  LCA, LG, LPR, LPU, MP, MSJ, NORMA, NOTA, NP, OE, OF, OFI, OPE, PER, PLA, PLANO, PROY, PRV, PV, RECON, RES, RESIMP,
  RTCI, RTCL, SOLIC, SRyO, SUB), «Buscar». Tabla: Nro. de DO | Nro. de Proceso | Usuario Protocolizador |
  Referencia | Fecha | Firmantes | Responsables. (Sin resultados para Informática 10/11-25/11.)

## Comunicaciones Oficiales (submenú: Internas [call_received], Externas [outbox])
- Internas (#/communications_internas): pestañas «Recibidas (0) · Enviadas (0) · Eliminadas (0)»; «Buscar» con lupa,
  Desde, Hasta (calendario); botones «Todos (0)» y «No Leídos (0)». Sin botón para crear (no hay «+»).
- Externas (#/communications_externas): pestañas «Enviadas (0) · No Entregadas (0) · Archivadas (0)»; filtros
  «N° de Proceso» (lupa), «CUIL/CUIT destinatario» (lupa), «Tipo de remitente» (Usuario | Oficina) + «Remitente»
  (lupa), «Proceso» (Documentos Oficiales | Compras y Contrataciones), Desde, Hasta.

## Lista de destinatarios (submenú: Agentes, Ciudadanos [contact_page])
- #/users_distribution_list y #/citizens_distribution_list: «Filtrar listas» (lupa) y botón «+ Nueva lista».
- «Nueva lista» → «‹ Volver», «Creación de nueva lista», «Seleccionar tipo de creación *» (Nueva lista | Importar
  lista). Nueva lista: campo «Nombre de nueva lista» + botón «+ Nueva lista». Importar lista: «Examinar» + «+ Importar
  lista». (No se creó ninguna.)

## Biblioteca de Procedimientos Administrativos (#/bibloteca_de_procedimientos_administrativos)
- Filtros: «Tipo de Trámite» (Expediente Electrónico | Documentos Oficiales), «Palabras Clave» (multiselección con
  «Seleccionar todos» y «Cargar más»; entre otras ComprasYContrataciones, Contratos, GestiónDeBienes,
  GestionesAdministrativas, Farmacias…), «Buscar» (texto) y botón «Buscar».
- Tabla: Nombre | Descripción | Tipo Trámite | Palabras Clave Relacionadas (cantidad) | ⋮ (Previsualizar · Descargar).
  Paginado de a 10 (Anterior 1 2 Siguiente).
- Con ComprasYContrataciones: 20 procedimientos. Guía de cada uno (25/11/2026):
  | Procedimiento | Guía |
  |---|---|
  | Gestión Directa - Por Monto Menor al Tope | 9 págs, transcripta (guia_proceso_gd_monto_menor_tope.md) |
  | Gestión Directa - Por Reparación de Maquinaria | 11 págs (art. 116 inc. …) |
  | Gestión Directa - In Situ | 10 págs (art. 116 inc. c) ap. 8) |
  | Gestión Directa - Exclusividad | 10 págs (art. 116 inc. c) ap. 5) |
  | Gestión Directa - Por Especialización | 11 págs |
  | Gestión Directa - Entre Organismos Oficiales del Sector Público | 11 págs (art. 116 inc. c) ap. 6) |
  | Contratación por convenio marco | 4 págs |
  | Locación de inmuebles - Nuevo Alquiler | 11 págs |
  | Locación de inmuebles - Renovación de Alquileres | sin abrir |
  | Certificación de Pagos Múltiples - Gestión Única | 15 págs |
  | Certificación de Pagos Mensualizados/Periódicos - Gestión Única | 15 págs |
  | Certificación de Pagos | 1 pág genérica «Procedimiento Interno Jurisdiccional» |
  | Licitación/Concurso Privado | 1 pág genérica «Procedimiento Interno Jurisdiccional» (SIN paso a paso) |
  | Licitación/Concurso Público | 1 pág genérica «Procedimiento Interno Jurisdiccional» (SIN paso a paso) |
  | Contratos - Ampliaciones y Adicionales | 1 pág (texto no cargó; revisar) |
  | GD - Ley 14237 Emergencia Seguridad Pública | 1 pág (texto no cargó; revisar) |
  | GD - Ley 14241 Emergencia Social, Educativa y Sanitaria | 1 pág genérica «Procedimiento Administrativo Jurisdiccional» |
  | Redeterminación de precios | 1 pág genérica «Procedimiento Administrativo Jurisdiccional» |
  | Autorización de gastos por habilitación | 1 pág genérica «Procedimiento Administrativo Jurisdiccional» |
  | Reconocimiento y pago de intereses a proveedores | 1 pág genérica «Procedimiento Administrativo Jurisdiccional» |
- Texto de la guía genérica «Procedimiento Interno Jurisdiccional»: el procedimiento «reúne las características de
  interno y jurisdiccional… inicia y finaliza dentro de la administración pública provincial y no excede los límites
  de su jurisdicción…». Para pedir un paso a paso: escribir a procesosdigitales@santafe.gob.ar con Asunto «Nombre del
  Proceso Administrativo/Trámite» y en el cuerpo: a. Oficina TIMBÓ de inicio; b. Oficina TIMBÓ caratuladora; c. Breve
  descripción; d. Resumen del circuito; e. Otras oficinas involucradas; f. Documentos o formularios específicos;
  g. Procedimiento de rendición; h. Otros datos de relevancia.
- Corrección: «Contratos - Ampliaciones y Adicionales» = guía genérica «Procedimiento Administrativo Jurisdiccional».
  «GD - Ley 14237» quedó sin leer (1 pág).
- Texto de la guía genérica «Procedimiento Administrativo Jurisdiccional»: «El procedimiento administrativo que usted
  ha seleccionado es de carácter jurisdiccional. Esto significa que no excede los límites de su jurisdicción
  ministerial/organismo descentralizado/empresa del estado.» + el mismo pedido a procesosdigitales@santafe.gob.ar
  (Asunto y puntos a-h), «para ser incorporado en lugar de este documento».

## Oficinas y Usuarios (submenú: Oficinas [graph_2], Consulta de usuarios [group_search])
- Oficinas (#/organica): título «Oficinas», «Buscar», «Última modificacion 25/11/2026»; el organigrama no se dibujó
  (pestaña en segundo plano): no relevado.
- Consulta de usuarios (#/consulta_de_usuarios): «Usuario» (con ícono help), «Repartición de Nivel Superior» (select),
  «Buscar»; aviso «El campo de texto "Usuario" debe tener mínimamente 3 caracteres para realizar la búsqueda.»;
  «Listado de usuarios»: Nombre y Apellido | CUIL | Correo electrónico | Oficinas a las que pertenece.

## Autorregistro (#/autorregistro)
- Bandeja: pestañas «En Curso / Aprobadas / Rechazadas», «+» (add); filtros «Buscar usuario», «Buscar por Cargo»,
  «Modificado Desde», «Modificado Hasta», Desde, Hasta.
- «+» → «Nuevo Trámite»: «1 trámites disponibles» · «Autorregistro de usuarios · Iniciar».
- «Formulario Autorregistro de Usuario»: Datos del Usuario (CUIL *, Nombre *, Apellido *, Email *) · Seleccionar
  Oficina: «Oficina de Nivel Superior *» · leyenda «Deberá seleccionar una oficina de nivel inferior. Si no se
  encuentra, comuníquese con el área informática de su dependencia.» · «Observaciones» · «Se enviará este formulario
  al evaluador local de oficinas para confirmación.» · «Guardar».

## RLM (submenú: Entidades Digitales › Consulta de Apoderamientos [manage_search])
- #/entity_attorneys_lookup: «Tipo de busqueda *» (Búsqueda por entidad | Búsqueda por apoderado).

## Menú del usuario (botón con el nombre arriba a la derecha): «Cerrar sesión».

## Documento oficial ya enviado (tarjeta en «Iniciados por mi»)
- Menú ⋮: «Ver Flujo» (device_hub) · «Guía de proceso» (info) · «Previsualizar» (remove_red_eye) · «Historial»
  (history).
- «Historial» (panel a la derecha, de lo más nuevo a lo más viejo; cada entrada: usuario + fecha y hora):
  «Completó el formulario / Realizó la acción: Enviar a Producir» → «Realizó la acción: Enviar a Firmar» (con el
  texto "Enviar a Firmar ") → «Realizó la acción: Notificar firmante». Estadío que muestra la tarjeta: «Firmar
  Documento Oficial». Pie: número SDO, botón descargar y «Cerrar».
- **«Ver Flujo» (26/11, ya cargó: antes se quedaba en «CARGANDO»)**: diálogo «Flujo», pie «Versión: 2.0.2», diagrama
  BPMN de solo lectura (sin zoom táctil probado, control de línea de tiempo abajo a la derecha). Nodos, de izquierda
  a derecha: 🏠 inicio → «Iniciar Documento Oficial» (ícono documento) → «Producir Documento Oficial» (círculo) →
  gateway (rombo ▷) que abre dos ramas:
  - Rama de arriba (gris, NO transitada en este documento): vuelve a un ícono de sobre (✉) que conecta con «Revisar
    Documento Oficial» (círculo vacío); de ahí sale otro gateway hacia un sobre → ✕ (fin, rechazo) con un pin de
    ubicación (📍) verde debajo, sin tooltip visible.
  - Rama de abajo (verde, es la que siguió este expediente): gateway → sobre rosa (notificación) → «Firmar
    Documento Oficial» (con ✔ azul, recuadro verde: es el paso actual, pendiente) → gateway → «Evaluar Firma»
    (círculo) → gateway final: sobre → ✔ (fin, aprobado) arriba, o sobre → ✕ (fin, firma rechazada) abajo.
  - El color verde en las líneas marca el camino ya recorrido por este expediente puntual (se saltó «Revisar
    Documento Oficial»); el gris son ramas del proceso que no se usaron. No se probó con otro documento que sí
    pase por «Revisar».

## Solicitud de caratulación: variantes
- «Externo» agrega «* Persona física / Persona jurídica» (radios). Los campos siguientes no se pudieron ver.
- «¿Es Urgente?» en «Si» no agrega campos.

## Tipos de Documento Oficial
- 129 tipos (lista completa en app/recursos/simulador_timbo.json). Íconos: edit_document = se redacta en TIMBÓ
  («Libre»), upload_file = se sube un PDF («Importado»); grupo = firma conjunta; campana = aviso de firma;
  mail/contact_mail = comunicable; lock = reservado; star = especial; key = firma digital.

## Guías descargadas (25/11/2026, con permiso de la usuaria)
- Bajadas con «Descargar» de la Biblioteca a D:\Bere\Downloads (los PDF tienen marca de agua con nombre y CUIL: no
  van al repo). Texto sin marca de agua en `guias/*.txt` (PyMuPDF, se descartan las líneas en diagonal).
- «Certificación de Pagos Múltiples» y «Mensualizados/Periódicos» son el mismo PDF de 15 páginas con tres
  procedimientos: A. Pago Único (sobre el mismo expediente de la compra directa), B. Pagos Múltiples y
  C. Mensualizados/Periódicos (sobre un expediente nuevo vinculado al original).
- Renovación de alquileres: en el PDF oficial el paso 8 no tiene el corchete «[» del área (error del original).
