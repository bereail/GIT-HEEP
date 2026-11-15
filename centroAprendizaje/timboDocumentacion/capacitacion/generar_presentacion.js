// Genera "Introducción a TIMBÓ Compras" (primera clase) en .pptx editable.
// node generar.js <salida.pptx>
const pptxgen = require("pptxgenjs");

const salida = process.argv[2] || "Introduccion_TIMBO_Compras.pptx";

const THEME = {
  name: "TIMBO Capacitacion",
  headFontFace: "Calibri",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1B2B34", lt1: "FFFFFF", dk2: "0E4D5C", lt2: "EEF5F4",
    accent1: "0E7C86", accent2: "3B6FE0", accent3: "22A06B", accent4: "8A909C", accent5: "E8A33D", accent6: "C2410C",
    hlink: "0E7C86", folHlink: "0E4D5C",
  },
};
// Colores fijos de la clase (en hex, para usar en cualquier opción).
const K = {
  tinta: "1B2B34", gris: "5B6770", grisClaro: "DDE5E8", fondo: "F4F8F8", blanco: "FFFFFF",
  marca: "0E7C86", marcaOsc: "0E4D5C", marcaSuave: "DDF0EF",
  exp: "3B6FE0", expSuave: "E6EEFF", com: "22A06B", comSuave: "E3F5EC", ext: "6B7280", extSuave: "EEF0F3",
  ambar: "E8A33D", ambarSuave: "FDF1DC", rojo: "C2410C", rojoSuave: "FBE7DE",
};

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625 in
pres.title = "Introducción a TIMBÓ Compras";
pres.subject = "Primera clase para el área de Compras del hospital";
pres.author = "Centro de Aprendizaje";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };

// ---------------------------------------------------------------- layouts
pres.defineSlideMaster({
  title: "PORTADA",
  background: { color: K.marcaOsc },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.7, y: 1.55, w: 8.6, h: 1.3, fontSize: 40, bold: true, color: K.blanco, valign: "bottom", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.7, y: 3.0, w: 8.6, h: 1.1, fontSize: 18, color: "CFE7E6", valign: "top", align: "left", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENIDO",
  background: { color: K.blanco },
  margin: [0.5, 0.5, 0.45, 0.5],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.28, w: 9.0, h: 0.7, fontSize: 30, bold: true, color: K.marcaOsc, valign: "middle", margin: 0 }, text: "" } },
    { text: { text: "TIMBÓ Compras · Primera clase", options: { x: 0.5, y: 5.27, w: 5, h: 0.25, fontSize: 10, color: K.gris, margin: 0 } } },
  ],
  slideNumber: { x: 9.0, y: 5.25, w: 0.5, h: 0.28, fontSize: 10, color: K.gris, align: "right" },
});

let n = 0;
function nueva(layout, seccion) {
  n += 1;
  return pres.addSlide({ masterName: layout, sectionTitle: seccion });
}
function titulo(s, texto) { s.addText(texto, { placeholder: "title" }); }
function fuente(s, texto) {
  s.addText("Fuente: " + texto, { x: 3.2, y: 5.27, w: 5.7, h: 0.25, fontSize: 10, color: K.gris, align: "right", margin: 0, isTextBox: true, objectName: "Fuente" });
}
function sombra() { return { type: "outer", color: "9AA7AD", opacity: 0.25, blur: 6, offset: 1.5, angle: 90 }; }
function tarjeta(s, x, y, w, h, fill, nombre) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: fill }, rectRadius: 0.12, shadow: sombra(), objectName: nombre || "Tarjeta" });
}
function circulo(s, x, y, d, fill, texto, tam) {
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill }, objectName: "Círculo" });
  s.addText(texto, { x, y, w: d, h: d, fontSize: tam || 16, bold: true, color: K.blanco, align: "center", valign: "middle", margin: 0, isTextBox: true });
}
function texto(s, t, o) { s.addText(t, Object.assign({ margin: 0, isTextBox: true, color: K.tinta, fontSize: 14, valign: "top" }, o)); }
function flecha(s, x, y, w, color) {
  s.addShape(pres.shapes.RIGHT_ARROW, { x, y, w, h: 0.28, fill: { color: color || K.grisClaro }, line: { color: color || K.grisClaro }, objectName: "Flecha" });
}
function chip(s, x, y, w, t, fill, color) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 0.3, fill: { color: fill }, line: { color: fill }, rectRadius: 0.15, objectName: "Etiqueta" });
  s.addText(t, { x, y, w, h: 0.3, fontSize: 11, bold: true, color, align: "center", valign: "middle", margin: 0, isTextBox: true });
}
function leyendaSistemas(s, y) {
  chip(s, 0.5, y, 2.0, "Expediente electrónico", K.expSuave, K.exp);
  chip(s, 2.65, y, 1.6, "TIMBÓ Compras", K.comSuave, K.com);
  chip(s, 4.4, y, 1.75, "Fuera del sistema", K.extSuave, K.ext);
}

// ===================================================================== 1
pres.addSection({ title: "Apertura" });
let s = nueva("PORTADA", "Apertura");
s.addText("Introducción a TIMBÓ Compras", { placeholder: "title" });
s.addText("Primera clase · Área de Compras del hospital\nQué es, quiénes intervienen y cómo es el circuito de una compra", { placeholder: "body" });
circulo(s, 0.7, 0.6, 0.75, K.marca, "🛒", 24);
texto(s, "Material con fuentes oficiales de la Provincia de Santa Fe · Noviembre 2026", { x: 0.7, y: 4.85, w: 8.6, h: 0.3, fontSize: 12, color: "9FCFCC" });
s.addNotes(`Bienvenida (10 min con la diapositiva 2).
- Presentate y contá el objetivo: hoy no vamos a aprender todos los botones, sino a entender cómo funciona una compra en TIMBÓ y quién hace cada cosa.
- Aclarar que todo lo que se dice sale de documentos oficiales (circulares, resoluciones y videos de la Provincia), y que lo que todavía no está confirmado se va a decir así.
- Preguntá al grupo: ¿quién ya entró alguna vez a TIMBÓ? ¿Quién participó de una licitación en papel?`);

// ===================================================================== 2
s = nueva("CONTENIDO", "Apertura");
titulo(s, "Qué nos llevamos hoy");
const objetivos = [
  ["1", "Entender qué es TIMBÓ y qué parte es TIMBÓ Compras"],
  ["2", "Reconocer los 5 roles y quién hace cada cosa"],
  ["3", "Saber qué es un pliego y qué contiene"],
  ["4", "Recorrer el circuito de una compra, del pedido a la preadjudicación"],
];
objetivos.forEach(([num, t], i) => {
  const x = 0.5 + (i % 2) * 4.55, y = 1.3 + Math.floor(i / 2) * 1.75;
  tarjeta(s, x, y, 4.35, 1.5, K.fondo);
  circulo(s, x + 0.3, y + 0.42, 0.66, K.marca, num, 20);
  texto(s, t, { x: x + 1.15, y: y + 0.25, w: 3.0, h: 1.0, fontSize: 17, bold: true, valign: "middle", color: K.marcaOsc });
});
s.addNotes(`Contá los 4 objetivos. Lo importante: que al final cada participante pueda explicar con sus palabras qué pasa en cada etapa de una compra y en qué sistema se hace.
Avisá que la práctica en pantalla (cargar un pliego, evaluar) queda para la segunda clase.`);

// ===================================================================== 3
pres.addSection({ title: "Qué es TIMBÓ" });
s = nueva("CONTENIDO", "Qué es TIMBÓ");
titulo(s, "¿Qué es TIMBÓ?");
tarjeta(s, 0.5, 1.2, 4.2, 3.7, K.marcaSuave);
texto(s, "La plataforma de la Provincia para hacer los trámites en digital.", { x: 0.8, y: 1.45, w: 3.6, h: 1.3, fontSize: 22, bold: true, color: K.marcaOsc });
texto(s, "Oficialmente: el Sistema de Gestión Documental Electrónica de la Provincia de Santa Fe. Comprende el expediente electrónico y los módulos que lo integran.", { x: 0.8, y: 2.85, w: 3.6, h: 1.6, fontSize: 14, color: K.tinta });
const piezas = [
  ["📁", "Expediente electrónico", "La carpeta digital del trámite", K.exp],
  ["📝", "Documentos oficiales", "Notas, informes y formularios con firma", K.exp],
  ["🛒", "TIMBÓ Compras", "Licitaciones y concursos", K.com],
  ["👤", "ID Ciudadana", "Tu usuario único para entrar", K.ext],
];
piezas.forEach(([ic, t, d, col], i) => {
  const y = 1.2 + i * 0.95;
  circulo(s, 5.05, y + 0.08, 0.62, col, ic, 18);
  texto(s, t, { x: 5.85, y: y + 0.02, w: 3.6, h: 0.38, fontSize: 16, bold: true, color: K.tinta });
  texto(s, d, { x: 5.85, y: y + 0.4, w: 3.6, h: 0.35, fontSize: 13, color: K.gris });
});
fuente(s, "Circular UG TIMBÓ 7/2026 (glosario)");
s.addNotes(`Explicación simple: "TIMBÓ es donde la Provincia hace sus trámites sin papel. Así como antes había una carpeta con fojas, ahora hay un expediente electrónico".
- TIMBÓ Compras es UNO de sus módulos: el que se usa para las licitaciones y concursos.
- Para entrar se usa la ID Ciudadana (CUIL y contraseña).
Error a evitar: decir que TIMBÓ Compras reemplaza al expediente. No lo reemplaza: trabajan juntos (lo vemos en la diapositiva 5).
Fuente: Circular UG TIMBÓ 7/2026, glosario (definición oficial de TIMBÓ, TIMBÓ Compras y expediente electrónico).`);

// ===================================================================== 4
s = nueva("CONTENIDO", "Qué es TIMBÓ");
titulo(s, "¿Para qué sirve?");
const beneficios = [
  ["🔎", "Trazabilidad", "Cada paso queda registrado: quién hizo qué y cuándo"],
  ["✍️", "Firma electrónica", "Los documentos se firman dentro del sistema, con validez legal"],
  ["📂", "Todo en un lugar", "Lo que genera TIMBÓ Compras se incorpora solo al expediente"],
];
beneficios.forEach(([ic, t, d], i) => {
  const x = 0.5 + i * 3.05;
  tarjeta(s, x, 1.2, 2.85, 2.25, K.fondo);
  circulo(s, x + 0.25, 1.42, 0.62, K.marca, ic, 18);
  texto(s, t, { x: x + 0.25, y: 2.15, w: 2.4, h: 0.4, fontSize: 17, bold: true, color: K.marcaOsc });
  texto(s, d, { x: x + 0.25, y: 2.58, w: 2.4, h: 0.8, fontSize: 13, color: K.tinta });
});
tarjeta(s, 0.5, 3.7, 9.0, 1.3, K.ambarSuave);
texto(s, "Es obligatorio", { x: 0.8, y: 3.85, w: 3, h: 0.35, fontSize: 16, bold: true, color: "8A5A10" });
texto(s, "Desde el 1/4/2026, el Ministerio de Salud usa TIMBÓ Compras para licitaciones y concursos de simple sobre. Y lo que empieza en digital sigue en digital: no se vuelve al papel.", { x: 0.8, y: 4.2, w: 8.4, h: 0.75, fontSize: 14, color: K.tinta });
fuente(s, "Circular UG TIMBÓ 3/2026 · Circular UG TIMBÓ 3/2025 · Circular UG TIMBÓ 7/2026");
s.addNotes(`Qué problema resuelve: la carpeta de papel se pierde, no se sabe dónde está, hay que trasladarla. En TIMBÓ el expediente se ve desde cualquier oficina y queda el historial.
- Firma electrónica: tiene la misma validez legal; la firma digital con token queda para decretos y resoluciones ministeriales (Circular UG 4/2025).
- Los documentos de cada etapa de TIMBÓ Compras se incorporan automáticamente al expediente (Circular UG 7/2026, punto 7).
- Obligatoriedad: Circular UG TIMBÓ 3/2026 (incluye al Ministerio de Salud desde el 1/4/2026). Lo que empezó en papel antes sigue en papel.
- Principio de "no regresión": lo que se inició en digital no puede seguir en papel (Circular UG 3/2025, art. 2).
Pregunta al grupo: ¿qué problemas tenían con el expediente en papel?`);

// ===================================================================== 5
s = nueva("CONTENIDO", "Qué es TIMBÓ");
titulo(s, "TIMBÓ Compras y expediente: qué va en cada uno");
tarjeta(s, 0.5, 1.15, 4.35, 2.6, K.expSuave);
texto(s, "📁  Expediente electrónico", { x: 0.75, y: 1.3, w: 3.9, h: 0.4, fontSize: 18, bold: true, color: K.exp });
texto(s, [
  { text: "El pedido y la autorización para iniciar", options: { bullet: true, breakLine: true } },
  { text: "Decisorios y actos administrativos", options: { bullet: true, breakLine: true } },
  { text: "La adjudicación", options: { bullet: true, breakLine: true } },
  { text: "El contrato, la recepción y el pago", options: { bullet: true } },
], { x: 0.75, y: 1.8, w: 3.9, h: 2.3, fontSize: 15, paraSpaceAfter: 8 });
tarjeta(s, 5.15, 1.15, 4.35, 2.6, K.comSuave);
texto(s, "🛒  TIMBÓ Compras", { x: 5.4, y: 1.3, w: 3.9, h: 0.4, fontSize: 18, bold: true, color: K.com });
texto(s, [
  { text: "El pliego particular (formularios)", options: { bullet: true, breakLine: true } },
  { text: "Consultas y circulares", options: { bullet: true, breakLine: true } },
  { text: "Ofertas, apertura y evaluación", options: { bullet: true, breakLine: true } },
  { text: "Subsanación, impugnaciones y preadjudicación", options: { bullet: true } },
], { x: 5.4, y: 1.8, w: 3.9, h: 2.3, fontSize: 15, paraSpaceAfter: 8 });
tarjeta(s, 0.5, 4.0, 9.0, 0.75, K.marcaSuave);
texto(s, "Para empezar en TIMBÓ Compras hace falta un número de expediente: los dos trabajan juntos.", { x: 0.75, y: 4.15, w: 8.5, h: 0.45, fontSize: 15, bold: true, color: K.marcaOsc, valign: "middle" });
fuente(s, "Circular UG TIMBÓ 7/2026, puntos 6, 7 y 11");
s.addNotes(`Es la diapositiva clave para no confundir sistemas.
- La Circular UG TIMBÓ 7/2026 (punto 6) lo dice textual: la etapa preparatoria se resuelve por expediente electrónico; del pliego al informe de preadjudicación, por TIMBÓ Compras; la adjudicación y la etapa contractual, por expediente.
- Punto 11: para iniciar un proceso hay que tener un número de expediente electrónico.
- Fuera de los dos sistemas quedan: la publicación en el Portal de Compras, la carga en el SIN y la vista al Tribunal de Cuentas (se hace con "Gestión de Visualización" del expediente).
Frase para recordar: "TIMBÓ Compras es la parte del medio; el principio y el final van por expediente".`);

// ===================================================================== 6
pres.addSection({ title: "Circuito" });
s = nueva("CONTENIDO", "Circuito");
titulo(s, "El recorrido de una compra pública");
const macro = [
  ["1", "Necesidad\ny pedido", K.exp],
  ["2", "Pliego y\naprobación", K.com],
  ["3", "Publicación", K.ext],
  ["4", "Ofertas, apertura\ny evaluación", K.com],
  ["5", "Adjudicación\ny contrato", K.exp],
];
macro.forEach(([num, t, col], i) => {
  const x = 0.5 + i * 1.86;
  tarjeta(s, x, 1.35, 1.56, 2.0, K.fondo);
  circulo(s, x + 0.48, 1.55, 0.6, col, num, 18);
  texto(s, t, { x: x + 0.08, y: 2.3, w: 1.4, h: 0.9, fontSize: 14, bold: true, align: "center", color: K.tinta });
  if (i < macro.length - 1) flecha(s, x + 1.6, 2.2, 0.24, K.grisClaro);
});
const notasMacro = [
  [0.5, "Área que necesita + Compras", K.exp], [2.36, "Gestor, Supervisor, comitente", K.com], [4.22, "Portal de Compras y aviso oficial", K.ext],
  [6.08, "Oferentes y Evaluadores", K.com], [7.94, "Autoridad competente", K.exp],
];
notasMacro.forEach(([x, t, col]) => texto(s, t, { x, y: 3.45, w: 1.56, h: 0.6, fontSize: 11, color: col, align: "center" }));
leyendaSistemas(s, 4.4);
texto(s, "TCP y SIN: también fuera del sistema", { x: 6.35, y: 4.4, w: 3.1, h: 0.3, fontSize: 11, color: K.gris, valign: "middle" });
fuente(s, "Circular UG TIMBÓ 7/2026 · Circular SCyGB 04/2026 · Circulares UG TIMBÓ 9 y 11/2026");
s.addNotes(`Mostrá el recorrido completo antes de entrar en detalle (15 min para esta parte, con las diapositivas 11 a 13).
1. Necesidad y pedido: el servicio pide; se abre el expediente (azul).
2. Pliego y aprobación: el Gestor arma el pliego en TIMBÓ Compras, la comitente lo revisa y el Supervisor lo aprueba; el acto que aprueba el pliego se firma en el expediente.
3. Publicación: Portal de Compras + aviso oficial por mail (Circular SCyGB 04/2026); TIMBÓ invita a la nómina.
4. Ofertas, apertura y evaluación: todo en TIMBÓ Compras, hasta la preadjudicación.
5. Adjudicación y contrato: por expediente.
También fuera del sistema: la vista al Tribunal de Cuentas y la carga en el SIN (Circulares UG 9 y 11/2026).
Pendiente: si los controles de la URC (Res. ME 73/2026) alcanzan al hospital. Si alguien pregunta, decir que está en consulta.`);

// ===================================================================== 7
pres.addSection({ title: "Roles" });
s = nueva("CONTENIDO", "Roles");
titulo(s, "Quiénes intervienen: los 5 roles");
const roles = [
  ["📝", "Gestor", "Prepara la contratación: arma el pliego y genera circulares", K.com],
  ["✅", "Supervisor", "Aprueba el pliego, arma cronograma y nómina, carga los actos", K.com],
  ["🔍", "Evaluador", "Analiza las ofertas y preadjudica (mínimo 3)", K.com],
  ["🏥", "Jurisdicción comitente", "Revisa los pliegos", K.marca],
  ["🏢", "Oferente / Proveedor", "Consulta, presenta ofertas e impugna", K.ext],
];
roles.forEach(([ic, t, d, col], i) => {
  const x = 0.5 + (i % 3) * 3.05, y = 1.15 + Math.floor(i / 3) * 1.85;
  tarjeta(s, x, y, 2.85, 1.65, K.fondo);
  circulo(s, x + 0.22, y + 0.22, 0.6, col, ic, 17);
  texto(s, t, { x: x + 0.95, y: y + 0.28, w: 1.8, h: 0.5, fontSize: 15, bold: true, color: K.tinta, valign: "middle" });
  texto(s, d, { x: x + 0.22, y: y + 0.9, w: 2.45, h: 0.7, fontSize: 12.5, color: K.gris });
});
tarjeta(s, 6.6, 3.0, 2.9, 1.65, K.ambarSuave);
texto(s, "¿Quién te da el rol?", { x: 6.8, y: 3.12, w: 2.5, h: 0.35, fontSize: 14, bold: true, color: "8A5A10" });
texto(s, "Se tramita ante el administrador local de tu jurisdicción.", { x: 6.8, y: 3.5, w: 2.5, h: 1.0, fontSize: 12.5, color: K.tinta });
fuente(s, "Circular UG TIMBÓ 7/2026, punto 10 · Circulares UG TIMBÓ 1 y 3/2026");
s.addNotes(`Mensaje central: cada usuario no hace lo mismo. Cada persona ve solo los procesos que corresponden a sus roles (Circular UG TIMBÓ 7/2026, punto 9).
- Gestor: genera la instancia, completa los formularios del pliego particular y genera circulares.
- Supervisor: aprueba o rechaza los formularios; arma el cronograma y la nómina; carga los actos (aprobación del pliego, sin efecto, adjudicación). Carga el acto, pero el acto lo firma la autoridad en el expediente.
- Evaluador: evalúa, pide subsanaciones o mejoras, preselecciona, preadjudica, carga el cronograma de impugnaciones y recibe las impugnaciones. Mínimo 3 evaluadores (punto 13).
- Jurisdicción comitente: revisa los pliegos.
- Oferente/Proveedor: accede a los procesos, oferta, consulta, recibe notificaciones en su domicilio digital e impugna.
Cómo se habilita: "tramitar el alta de perfiles y roles ante el administrador local" (Circulares UG 1 y 3/2026). Quién autoriza ese pedido NO está establecido en la normativa: si preguntan, decir que está pendiente de confirmar.
Error a evitar: decir que el Evaluador adjudica. El Evaluador PREadjudica (recomienda); la adjudicación es un acto de la autoridad, en el expediente.`);

// ===================================================================== 8
pres.addSection({ title: "Conceptos" });
s = nueva("CONTENIDO", "Conceptos");
titulo(s, "Conceptos fundamentales");
const conceptos = [
  ["Expediente", "La carpeta digital del trámite"],
  ["Proveedor", "Quien vende o presta el servicio; debe estar en el RUPC"],
  ["Renglón", "Cada cosa que se compra, con su cantidad"],
  ["Oferta", "La propuesta del proveedor, con precio y documentación"],
  ["Apertura", "TIMBÓ abre las ofertas solo, a la hora fijada"],
  ["Evaluación", "La comisión analiza cada oferta"],
  ["Preadjudicación", "La recomendación: a quién conviene adjudicar"],
  ["Adjudicación", "La decisión final, por acto en el expediente"],
];
conceptos.forEach(([t, d], i) => {
  const x = 0.5 + (i % 4) * 2.3, y = 1.15 + Math.floor(i / 4) * 1.95;
  const destacar = t === "Preadjudicación" || t === "Adjudicación";
  tarjeta(s, x, y, 2.1, 1.75, destacar ? K.ambarSuave : K.fondo);
  texto(s, t, { x: x + 0.18, y: y + 0.2, w: 1.8, h: 0.4, fontSize: 16, bold: true, color: destacar ? "8A5A10" : K.marcaOsc });
  texto(s, d, { x: x + 0.18, y: y + 0.65, w: 1.8, h: 1.0, fontSize: 13, color: K.tinta });
});
fuente(s, "Circular UG TIMBÓ 7/2026 · Dec. 287/2026 · Res. SCyGB 110/2026");
s.addNotes(`Repasá cada concepto con un ejemplo del hospital:
- Renglón: "Renglón 1: 500 cajas de guantes de látex talle M".
- Oferta: solo vale si quedó en estado "Oferta presentada" antes de la apertura (Circular UG 7/2026, punto 18).
- Apertura: es automática, a la fecha y hora del cronograma; genera el acta y el cuadro comparativo (punto 19).
- Evaluación: la comisión actúa según el pliego; su opinión no es vinculante (Dec. 287/2026, art. 123).
- Preadjudicación vs. adjudicación (marcadas en amarillo): la preadjudicación es una recomendación, en TIMBÓ Compras; la adjudicación es la decisión, en el expediente.
- Proveedor: tiene que estar inscripto en el RUPC para ofertar (Res. SCyGB 110/2026 y Circular UG 2/2026).
Pregunta al grupo: "Si el sistema dice Preadjudicado, ¿ya le podemos comprar al proveedor?" Respuesta: no, falta el acto de adjudicación.`);

// ===================================================================== 9
s = nueva("CONTENIDO", "Conceptos");
titulo(s, "¿Qué es un pliego?");
tarjeta(s, 0.5, 1.15, 9.0, 1.0, K.marcaSuave);
texto(s, "Las reglas de juego de una compra: qué se compra, cómo se oferta, cómo se evalúa y cómo se entrega.", { x: 0.8, y: 1.27, w: 8.4, h: 0.75, fontSize: 19, bold: true, color: K.marcaOsc, valign: "middle" });
tarjeta(s, 0.5, 2.4, 4.35, 2.6, K.fondo);
circulo(s, 0.75, 2.6, 0.6, K.marcaOsc, "G", 18);
texto(s, "Pliego general", { x: 1.5, y: 2.65, w: 3.2, h: 0.45, fontSize: 18, bold: true, color: K.tinta, valign: "middle" });
texto(s, "Pliego Único de Bases y Condiciones Generales. Vale para TODAS las licitaciones y concursos de bienes y servicios. Lo aprobó el Decreto 287/2026.", { x: 0.75, y: 3.3, w: 3.9, h: 1.6, fontSize: 14, color: K.tinta });
tarjeta(s, 5.15, 2.4, 4.35, 2.6, K.comSuave);
circulo(s, 5.4, 2.6, 0.6, K.com, "P", 18);
texto(s, "Pliego particular (PBCP)", { x: 6.15, y: 2.65, w: 3.2, h: 0.45, fontSize: 18, bold: true, color: K.tinta, valign: "middle" });
texto(s, "Las reglas de ESTA compra. Lo elabora y aprueba el organismo. En TIMBÓ Compras se arma completando formularios.", { x: 5.4, y: 3.3, w: 3.9, h: 1.6, fontSize: 14, color: K.tinta });
fuente(s, "Decreto 287/2026 (art. 1 y art. 131) · Circular UG TIMBÓ 7/2026, punto 12");
s.addNotes(`Concepto imprescindible (15 min con la diapositiva 10).
Metáfora: "Es como el reglamento de un campeonato. El general es el reglamento de la liga, igual para todos los partidos. El particular es lo de este partido: dónde, cuándo, quién juega".
- Pliego general: el Pliego Único de Bases y Condiciones Generales, aprobado por el Decreto 287/2026 (art. 1). Rige para todo el Sector Provincial No Financiero.
- Pliego particular (PBCP): lo elaboran y aprueban los órganos competentes de cada jurisdicción (Dec. 287/2026, art. 131.3). En TIMBÓ Compras se confecciona con formularios estandarizados (Circular UG 7/2026, punto 12).
- La Circular SCyGB 05/2026 trae textos modelo para completar los formularios.
Pregunta al grupo: "¿Qué tiene que decir sí o sí un pliego para que un proveedor pueda ofertar?" Dejá que respondan y pasá a la diapositiva siguiente.
Error a evitar: decir que el pliego lo hace el sistema. El sistema da los formularios; el contenido lo define el organismo.`);

// ===================================================================== 10
s = nueva("CONTENIDO", "Conceptos");
titulo(s, "Qué contiene el pliego particular");
const formularios = [
  ["Aspectos generales", "Objeto, moneda, forma de cotizar, criterio de evaluación"],
  ["Detalle de productos o servicios", "Los renglones: qué, cuánto, ficha técnica"],
  ["Requisitos de participación", "Qué documentación presenta el proveedor"],
  ["Garantías", "Porcentajes y tipos aceptados"],
  ["Condiciones del contrato", "Lugar, plazo y forma de entrega"],
  ["Facturación y pago", "Forma y plazo de pago, recepción"],
  ["Anexos", "Especificaciones, modelos, declaraciones juradas"],
  ["Evaluadores", "Al menos 3 integrantes"],
];
formularios.forEach(([t, d], i) => {
  const col = i % 2, fila = Math.floor(i / 2);
  const x = 0.5 + col * 4.55, y = 1.12 + fila * 0.98;
  tarjeta(s, x, y, 4.35, 0.84, K.fondo);
  circulo(s, x + 0.15, y + 0.15, 0.54, K.com, String(i + 1), 15);
  texto(s, t, { x: x + 0.85, y: y + 0.09, w: 3.35, h: 0.34, fontSize: 14, bold: true, color: K.tinta });
  texto(s, d, { x: x + 0.85, y: y + 0.43, w: 3.35, h: 0.34, fontSize: 12, color: K.gris });
});
fuente(s, "Video oficial APP-TimboCompras, Clase 02 · Circular SCyGB 05/2026");
s.addNotes(`Son los 8 formularios del pliego en TIMBÓ Compras (salen de la capacitación oficial "APP-TimboCompras", Clase 02). Recién con los 8 completos el Gestor puede avanzar.
Dos advertencias importantes:
- Lo que no esté en "Requisitos de participación" no se le puede exigir al proveedor.
- Si no se marca que se aceptan ofertas alternativas, el proveedor no puede cotizarlas.
- Evaluadores: mínimo 3 (Circular UG TIMBÓ 7/2026, punto 13); conviene sumar suplentes.
- Las especificaciones técnicas van por renglón (ficha técnica) y en los anexos.
- No pedirle al proveedor documentación que ya está en registros del Estado (RUPC, RPJEC): Circular UG TIMBÓ 7/2025.
El Decreto 287/2026 (art. 131) lista el contenido mínimo de todo PBCP: objeto, especificaciones técnicas, órganos de evaluación, criterios, garantías, plazos, moneda, entrega, recepción, facturación.`);

// ===================================================================== 11
pres.addSection({ title: "Procedimientos" });
s = nueva("CONTENIDO", "Procedimientos");
titulo(s, "Compra directa y licitación: diferencias");
const filas = [
  ["", "Compra directa por monto", "Licitación o concurso"],
  ["¿Cuándo?", "Montos chicos: hasta $5.850.000 (2026)", "Privado: hasta $58.500.000\nPúblico: más de $58.500.000"],
  ["¿Dónde se tramita?", "En el expediente electrónico", "En TIMBÓ Compras + expediente"],
  ["¿Con qué?", "Formularios CD-01 a CD-04 (documentos oficiales)", "Pliego particular con 8 formularios"],
  ["¿Competencia?", "Presupuestos de proveedores", "Publicación, ofertas y apertura electrónica"],
];
const filasTabla = filas.map((f, i) => f.map((c, j) => ({
  text: c,
  options: {
    bold: i === 0 || j === 0, fontSize: i === 0 ? 15 : 13,
    color: i === 0 ? K.blanco : (j === 0 ? K.marcaOsc : K.tinta),
    fill: { color: i === 0 ? (j === 1 ? K.exp : j === 2 ? K.com : K.marcaOsc) : (i % 2 ? K.fondo : K.blanco) },
    valign: "middle", margin: [4, 8, 4, 8],
  },
})));
s.addTable(filasTabla, { x: 0.5, y: 1.15, w: 9.0, colW: [1.9, 3.55, 3.55], rowH: [0.42, 0.62, 0.5, 0.62, 0.55], border: { type: "solid", pt: 0.75, color: K.grisClaro }, objectName: "Tabla comparativa" });
tarjeta(s, 0.5, 4.35, 9.0, 0.7, K.ambarSuave);
texto(s, "Ojo: las directas por urgencia o porque el proceso quedó desierto SÍ van por TIMBÓ Compras.", { x: 0.75, y: 4.45, w: 8.5, h: 0.5, fontSize: 14, bold: true, color: "8A5A10", valign: "middle" });
fuente(s, "Circular SCyGB 01/2026 (topes 2026) · Circular UG TIMBÓ 8/2026 · video oficial CD-01");
s.addNotes(`Diferencia central: dónde se tramita.
- Compra directa por monto menor al tope: se tramita en el expediente electrónico con documentos oficiales CD-01 (solicitud), CD-02 (pedido de presupuesto), CD-03 (evaluación y adjudicación) y CD-04 (orden de provisión). Marco: Ley 12.510, art. 116, inc. 1, y Dec. 1104/16. Trámite: "Compras y Contrataciones - Gestión Directa - por Monto Menor al Tope".
- Licitación o concurso de simple sobre: obligatorio por TIMBÓ Compras (Circular UG TIMBÓ 3/2026).
- Topes 2026 (Circular SCyGB 01/2026, según la Ley de Presupuesto): directa hasta $5.850.000; licitación o concurso privado hasta $58.500.000; público, más de $58.500.000. Se actualizan cada año.
- Excepción: las directas por urgencia o por proceso desierto van por TIMBÓ Compras, con al menos 3 proveedores invitados (Circular UG TIMBÓ 8/2026).
- Hay otros tipos de directa (especialización, exclusividad, entre organismos): no son tema de hoy.
Pregunta al grupo: "Hay que comprar 20 sillas por $3.000.000. ¿Qué procedimiento?" (Directa por monto, por expediente).`);

// ===================================================================== 12
s = nueva("CONTENIDO", "Procedimientos");
titulo(s, "Etapas de una licitación, paso a paso");
const etapas = [
  ["Pedido y expediente", K.exp], ["Pliego (Gestor)", K.com], ["Revisión y aprobación", K.com], ["Acto que aprueba el pliego", K.exp],
  ["Vista TCP y SIN", K.ext], ["Publicación", K.ext], ["Consultas y ofertas", K.com], ["Apertura automática", K.com],
  ["Evaluación", K.com], ["Preadjudicación", K.com], ["Impugnaciones", K.com], ["Adjudicación y contrato", K.exp],
];
etapas.forEach(([t, col], i) => {
  const fila = Math.floor(i / 4), colI = i % 4;
  const x = 0.5 + colI * 2.3, y = 1.15 + fila * 1.08;
  tarjeta(s, x, y, 2.05, 0.86, K.fondo);
  circulo(s, x + 0.12, y + 0.18, 0.5, col, String(i + 1), 14);
  texto(s, t, { x: x + 0.72, y: y + 0.1, w: 1.25, h: 0.66, fontSize: 12.5, bold: true, color: K.tinta, valign: "middle" });
});
leyendaSistemas(s, 4.5);
fuente(s, "Circular UG TIMBÓ 7/2026 · Circulares UG TIMBÓ 9 y 11/2026 · Circular SCyGB 04/2026");
s.addNotes(`Recorrido de izquierda a derecha y de arriba abajo. El color dice en qué sistema se hace.
1. Pedido y expediente (expediente).
2. El Gestor arma el pliego (TIMBÓ Compras).
3. La comitente lo revisa y el Supervisor lo aprueba: TIMBÓ asigna el número de proceso definitivo.
4. El acto que aprueba el pliego y autoriza el llamado se firma en el expediente y el Supervisor lo carga en TIMBÓ Compras.
5. Vista al Tribunal de Cuentas con "Gestión de Visualización" y carga en el SIN (Circulares UG 9 y 11/2026).
6. Publicación en el Portal de Compras con "generar enlace con TIMBO" y aviso oficial por mail, 3 días antes (Circular SCyGB 04/2026).
7 a 11. Todo en TIMBÓ Compras.
12. Adjudicación y contrato por expediente.
Pendiente de confirmar: si al hospital le corresponden los controles de la URC (pliego y preadjudicación, Res. ME 73/2026). No lo des como seguro.`);

// ===================================================================== 13
s = nueva("CONTENIDO", "Procedimientos");
titulo(s, "De la convocatoria a la preadjudicación");
const tramo = [
  ["📣", "Publicado", "Los proveedores ven el proceso y pueden consultar"],
  ["📨", "Ofertas", "Solo cuentan las que quedan en \"Oferta presentada\""],
  ["🔓", "Apertura", "Automática: acta y cuadro comparativo"],
  ["🔍", "Evaluación", "Se puede pedir subsanar, aclarar o mejorar precio"],
  ["📋", "Preadjudicación", "Informe firmado por los evaluadores, notificado"],
];
tramo.forEach(([ic, t, d], i) => {
  const x = 0.5 + i * 1.86;
  circulo(s, x + 0.45, 1.25, 0.66, K.com, ic, 20);
  if (i < tramo.length - 1) s.addShape(pres.shapes.LINE, { x: x + 1.17, y: 1.58, w: 1.2, h: 0, line: { color: K.com, width: 2, dashType: "dash" }, objectName: "Conector" });
  texto(s, t, { x, y: 2.05, w: 1.56, h: 0.4, fontSize: 15, bold: true, align: "center", color: K.tinta });
  texto(s, d, { x, y: 2.45, w: 1.56, h: 1.1, fontSize: 12, align: "center", color: K.gris });
});
tarjeta(s, 0.5, 3.75, 4.35, 1.3, K.comSuave);
texto(s, "Preadjudicar = recomendar", { x: 0.75, y: 3.88, w: 3.9, h: 0.35, fontSize: 16, bold: true, color: K.com });
texto(s, "Lo hacen los evaluadores, en TIMBÓ Compras. Los oferentes pueden impugnar.", { x: 0.75, y: 4.25, w: 3.9, h: 0.7, fontSize: 13, color: K.tinta });
tarjeta(s, 5.15, 3.75, 4.35, 1.3, K.expSuave);
texto(s, "Adjudicar = decidir", { x: 5.4, y: 3.88, w: 3.9, h: 0.35, fontSize: 16, bold: true, color: K.exp });
texto(s, "Es un acto de la autoridad, en el expediente. Recién ahí se contrata.", { x: 5.4, y: 4.25, w: 3.9, h: 0.7, fontSize: 13, color: K.tinta });
fuente(s, "Circular UG TIMBÓ 7/2026, puntos 16 a 22 · Pliego Único (Dec. 287/2026)");
s.addNotes(`El tramo que pasa entero dentro de TIMBÓ Compras.
- Publicado: los interesados con ID Ciudadana ven el proceso en "Participar de un proceso" (punto 16). Para consultar tienen que haber participado (punto 17). Las consultas no muestran el autor; se responden con circulares.
- Ofertas: hasta la fecha y hora de apertura; solo valen en estado "Oferta presentada" (punto 18). PDF de hasta 5 MB recomendado.
- Apertura automática: acta y cuadro comparativo (punto 19). Nadie tiene que "abrir" nada.
- Evaluación: subtrámites de subsanación, aclaración o mejora; si el proveedor no responde a tiempo pasa a "descartado" (punto 21).
- Preadjudicación: el informe lo firman los evaluadores en el orden del formulario "Ordenar evaluadores" y se notifica al domicilio digital (punto 22). Impugnación de la preadjudicación: 2 días (Pliego Único de Bases y Condiciones Generales).
Los plazos se rigen por la hora del servidor de TIMBÓ Compras (punto 4). El mail es "de cortesía": la notificación válida para el personal es el cambio de estado del sistema (punto 5).`);

// ===================================================================== 14
pres.addSection({ title: "Proveedores" });
s = nueva("CONTENIDO", "Proveedores");
titulo(s, "¿Qué hacen los proveedores?");
const pasosProv = [
  ["1", "Se inscriben en el RUPC", "En www.santafe.gov.ar/proveedores, con clave fiscal nivel 3"],
  ["2", "Tienen ID Ciudadana nivel 3", "Y domicilio digital, donde reciben las notificaciones"],
  ["3", "Participan del proceso", "Bandeja \"Participar de un proceso\""],
  ["4", "Consultan, ofertan, impugnan", "Desde \"Mis ofertas\", dentro de los plazos"],
];
pasosProv.forEach(([num, t, d], i) => {
  const y = 1.15 + i * 0.95;
  circulo(s, 0.5, y + 0.1, 0.6, K.ext, num, 17);
  texto(s, t, { x: 1.3, y: y + 0.05, w: 4.2, h: 0.38, fontSize: 16, bold: true, color: K.tinta });
  texto(s, d, { x: 1.3, y: y + 0.43, w: 4.2, h: 0.38, fontSize: 13, color: K.gris });
});
tarjeta(s, 5.85, 1.15, 3.65, 3.85, K.fondo);
texto(s, "Lo que verifica el hospital al evaluar", { x: 6.1, y: 1.3, w: 3.2, h: 0.65, fontSize: 15, bold: true, color: K.marcaOsc });
texto(s, [
  { text: "Que esté inscripto en el RUPC", options: { bullet: true, breakLine: true } },
  { text: "Que su actividad coincida con lo que se compra", options: { bullet: true, breakLine: true } },
  { text: "Habilitaciones y requisitos del pliego", options: { bullet: true } },
], { x: 6.1, y: 2.0, w: 3.2, h: 2.0, fontSize: 13.5, paraSpaceAfter: 8 });
texto(s, "La inscripción en el RUPC es un trámite aparte de TIMBÓ.", { x: 6.1, y: 4.15, w: 3.2, h: 0.7, fontSize: 12, color: K.gris });
fuente(s, "Res. SCyGB 110/2026 · Circular UG TIMBÓ 2/2026 · Circular UG TIMBÓ 7/2026");
s.addNotes(`Diferencia clave: el proveedor hace su parte desde su lado; el hospital no puede ofertar ni consultar por él.
- RUPC: inscripción en el Sistema de Gestión de Proveedores Web (www.santafe.gov.ar/proveedores), con clave fiscal nivel 3 y el servicio "ECON SANTA FE – Registro Único de Proveedores y Contratistas" (Res. SCyGB 110/2026). Es requisito indispensable para ofertar (Circular UG 2/2026).
- ID Ciudadana nivel 3 con domicilio digital vigente (Circular UG 2/2026).
- En TIMBÓ Compras: "Participar de un proceso" para ver y sumarse; "Mis ofertas" para consultar, completar la oferta e impugnar.
- Desde la Circular UG 2/2026, el RUPC solo administra la inscripción: los requisitos de participación los verifica la unidad de compras (el hospital) al evaluar.
Pendiente de confirmar (no afirmar): si la inscripción en el RUPC vence. Hay una discrepancia entre el Dec. 287/2026 y la Res. 110/2026.
Para la mesa de ayuda del proveedor: compras.santafe.gob.ar/tutoriales tiene los videos oficiales.`);

// ===================================================================== 15
pres.addSection({ title: "Buenas prácticas" });
s = nueva("CONTENIDO", "Buenas prácticas");
titulo(s, "Buenas prácticas y errores frecuentes");
const practicas = [
  ["⚠️", "Lo incorporado no se borra", "Si hay un error, se subsana con otro documento"],
  ["✍️", "Lo firmado no se edita", "Revisá número y fecha antes de mandar a firmar"],
  ["🕒", "Manda la hora del servidor", "Los plazos se cuentan con la hora de TIMBÓ"],
  ["📨", "El mail no es notificación", "Lo que vale es el cambio de estado"],
  ["🔗", "Enlace con TIMBÓ", "Sin marcarlo en el portal, no aparece \"Ofertar\""],
  ["🔒", "La clave es personal", "Lo hecho con tu clave se presume hecho por vos"],
];
practicas.forEach(([ic, t, d], i) => {
  const x = 0.5 + (i % 3) * 3.05, y = 1.15 + Math.floor(i / 3) * 1.95;
  tarjeta(s, x, y, 2.85, 1.75, K.fondo);
  circulo(s, x + 0.22, y + 0.22, 0.56, i < 2 ? K.rojo : K.marca, ic, 16);
  texto(s, t, { x: x + 0.9, y: y + 0.22, w: 1.85, h: 0.6, fontSize: 14, bold: true, color: K.tinta, valign: "middle" });
  texto(s, d, { x: x + 0.22, y: y + 0.95, w: 2.45, h: 0.7, fontSize: 12.5, color: K.gris });
});
fuente(s, "Circulares UG TIMBÓ 7/2026 y 3/2025 · Circular SCyGB 04/2026");
s.addNotes(`Errores documentados (salen de circulares, videos oficiales y consultas reales de soporte):
- Un documento incorporado al expediente no se puede eliminar: se corrige con "Subsanar documento" (curso oficial de expedientes).
- Un documento firmado no se edita (si no, se rompe la firma): revisar antes de mandar a firmar.
- Plazos: hora del servidor de TIMBÓ Compras (Circular UG 7/2026, punto 4).
- Correo de cortesía: no es notificación; la notificación válida es el evento del sistema (punto 5).
- En el portal hay que marcar "generar enlace con TIMBO" y el expediente principal; si no, al proveedor no le aparece OFERTAR (Circular SCyGB 04/2026).
- Credenciales personales e intransferibles (Circular UG 3/2025, art. 2.c).
Consulta frecuente de soporte: "el proveedor dice que ofertó y no aparece" → no la presentó (quedó en borrador).`);

// ===================================================================== 16
s = nueva("CONTENIDO", "Buenas prácticas");
titulo(s, "Ejemplo: comprar guantes para el hospital");
chip(s, 0.5, 1.12, 1.6, "Ejemplo ilustrativo", K.ambarSuave, "8A5A10");
const ejemplo = [
  ["El pedido", "Enfermería necesita 2.000 cajas de guantes. Monto estimado: $40.000.000", K.exp],
  ["El procedimiento", "Más de $5.850.000 y hasta $58.500.000: licitación privada, por TIMBÓ Compras", K.marca],
  ["El pliego", "Renglón 1: guantes de látex talle M · ficha técnica · 3 evaluadores", K.com],
  ["Las ofertas", "Tres proveedores inscriptos en el RUPC presentan oferta", K.com],
  ["El resultado", "Preadjudicación al de mejor oferta que cumple; luego, adjudicación por expediente", K.exp],
];
ejemplo.forEach(([t, d, col], i) => {
  const y = 1.6 + i * 0.7;
  circulo(s, 0.5, y + 0.05, 0.48, col, String(i + 1), 14);
  texto(s, t, { x: 1.15, y: y + 0.05, w: 2.0, h: 0.48, fontSize: 15, bold: true, color: K.tinta, valign: "middle" });
  texto(s, d, { x: 3.15, y: y + 0.05, w: 6.35, h: 0.48, fontSize: 13.5, color: K.tinta, valign: "middle" });
});
fuente(s, "Topes: Circular SCyGB 01/2026 · Circuito: Circular UG TIMBÓ 7/2026");
s.addNotes(`Es un ejemplo inventado para practicar (cantidades y montos ilustrativos). Lo normativo es real: los topes 2026 y el circuito.
Recorrelo con el grupo haciendo preguntas en cada paso:
1. ¿Dónde empieza? En el expediente, con el pedido de Enfermería.
2. ¿Qué procedimiento? $40.000.000 está entre $5.850.000 y $58.500.000: licitación o concurso privado (Circular SCyGB 01/2026). Por ser licitación de simple sobre, va por TIMBÓ Compras.
3. ¿Quién arma el pliego? El Gestor. ¿Cuántos evaluadores? Mínimo 3.
4. ¿Qué tienen que tener los proveedores? RUPC e ID Ciudadana nivel 3.
5. ¿El proveedor preadjudicado ya puede entregar? No: falta la adjudicación por acto, en el expediente.
Si alguien pregunta por el sellado o las garantías: el modelo de la Circular SCyGB 05/2026 pide garantía de mantenimiento de oferta del 1 %; es tema de la segunda clase.`);

// ===================================================================== 17
pres.addSection({ title: "Práctica" });
s = nueva("CONTENIDO", "Práctica");
titulo(s, "Actividad: ¿quién lo hace y dónde?");
const casos = [
  "Armar los formularios del pliego",
  "Aprobar el pliego y armar la nómina de proveedores",
  "Pedir a un oferente que subsane un documento",
  "Presentar una consulta sobre el pliego",
  "Firmar el acto de adjudicación",
];
casos.forEach((t, i) => {
  const y = 1.15 + i * 0.72;
  tarjeta(s, 0.5, y, 6.0, 0.58, K.fondo);
  circulo(s, 0.62, y + 0.07, 0.44, K.marca, String(i + 1), 13);
  texto(s, t, { x: 1.2, y: y + 0.08, w: 5.2, h: 0.42, fontSize: 15, color: K.tinta, valign: "middle" });
});
tarjeta(s, 6.8, 1.15, 2.7, 3.46, K.marcaSuave);
texto(s, "En grupos de 2 o 3", { x: 7.0, y: 1.3, w: 2.3, h: 0.4, fontSize: 15, bold: true, color: K.marcaOsc });
texto(s, "Para cada caso, respondan:\n\n¿Qué rol?\n¿En qué sistema?\n\n5 minutos", { x: 7.0, y: 1.75, w: 2.3, h: 2.7, fontSize: 14, color: K.tinta });
s.addNotes(`Actividad de 5 minutos + 5 de puesta en común.
Respuestas:
1. Armar los formularios del pliego → Gestor, en TIMBÓ Compras.
2. Aprobar el pliego y armar la nómina → Supervisor, en TIMBÓ Compras.
3. Pedir que subsane → Evaluador, en TIMBÓ Compras (subtrámite de subsanación).
4. Presentar una consulta → Oferente/Proveedor, en TIMBÓ Compras ("Mis ofertas"), si participó del proceso.
5. Firmar el acto de adjudicación → la autoridad competente, en el expediente electrónico. El Supervisor después lo carga en TIMBÓ Compras.
Fuente: Circular UG TIMBÓ 7/2026, puntos 6, 10 y 17.
Si sobra tiempo: "¿Una compra de $3.000.000 va por TIMBÓ Compras?" (No: compra directa por monto, por expediente).`);

// ===================================================================== 18
s = nueva("CONTENIDO", "Práctica");
titulo(s, "Preguntas frecuentes");
const faq = [
  ["¿Quién me da el rol de Gestor, Supervisor o Evaluador?", "Se tramita ante el administrador local de tu jurisdicción."],
  ["¿Y si TIMBÓ Compras no funciona?", "Avisar a la mesa de ayuda. Ante una falla comprobada, la UG TIMBÓ puede autorizar otra vía."],
  ["¿El preadjudicado ya puede entregar?", "No. Primero tiene que estar firmado el acto de adjudicación."],
  ["¿Dónde consulto dudas del proceso?", "Mesa de ayuda de TIMBÓ Compras: timbocompras@santafe.gob.ar · 0342-4506600 / 4506800 · de 8 a 13 h"],
];
faq.forEach(([q, a], i) => {
  const y = 1.12 + i * 0.98;
  tarjeta(s, 0.5, y, 9.0, 0.84, i % 2 ? K.blanco : K.fondo);
  texto(s, q, { x: 0.75, y: y + 0.08, w: 8.5, h: 0.34, fontSize: 15, bold: true, color: K.marcaOsc });
  texto(s, a, { x: 0.75, y: y + 0.43, w: 8.5, h: 0.36, fontSize: 13, color: K.tinta });
});
fuente(s, "Circulares UG TIMBÓ 1, 3 y 7/2026 · Circular SCyGB 03/2026 (mesa de ayuda)");
s.addNotes(`Preguntas y respuestas (15 min junto con la actividad).
Respuestas con su fuente:
- Rol: "tramitar el alta de perfiles y roles ante el administrador local" (Circulares UG 1 y 3/2026). Quién autoriza el pedido no está en la normativa: decir que está pendiente de confirmar.
- Falla del sistema: la UG TIMBÓ, como autoridad de aplicación, puede autorizar vías alternativas ante una imposibilidad técnica acreditada (Circular UG 1/2026, punto 7).
- Mesa de ayuda (Circular SCyGB 03/2026): timbocompras@santafe.gob.ar · 0342-4506600/4506800, internos 39479 y 39480 · WhatsApp +54 9 342 640-0792 · de 8 a 13 h.
Otras preguntas posibles:
- "¿La URC controla nuestros pliegos?" → Está pendiente de confirmar si nos alcanza (Res. ME 73/2026, dirigida a la Administración Pública Central).
- "¿Vence la inscripción en el RUPC?" → Hay una discrepancia entre normas; está en consulta.
- "¿Qué pasa si un artículo no está en el catálogo?" → Formulario CAByS (Res. SCyGB 292/2026); medicamentos y descartables, por el Servicio de Farmacia. Tema de la segunda clase.
- "¿Qué es el SIN?" → El Sistema de Información Normativa: ahí se cargan los actos y desde ahí van al Tribunal de Cuentas. Solo desde la red institucional.`);

// ===================================================================== 19
pres.addSection({ title: "Cierre" });
s = nueva("CONTENIDO", "Cierre");
titulo(s, "Repaso: 6 ideas para llevarse");
const ideas = [
  "TIMBÓ Compras es la parte del medio; el principio y el final van por expediente",
  "Hay 5 roles y cada uno hace algo distinto",
  "El pliego son las reglas de juego: general para todas, particular para esta compra",
  "La oferta vale solo si quedó \"presentada\"",
  "Preadjudicar es recomendar; adjudicar es decidir",
  "Para ofertar, el proveedor tiene que estar en el RUPC",
];
ideas.forEach((t, i) => {
  const x = 0.5 + (i % 2) * 4.55, y = 1.15 + Math.floor(i / 2) * 1.3;
  tarjeta(s, x, y, 4.35, 1.1, K.fondo);
  circulo(s, x + 0.2, y + 0.25, 0.6, K.marca, String(i + 1), 17);
  texto(s, t, { x: x + 1.0, y: y + 0.12, w: 3.2, h: 0.86, fontSize: 14, bold: true, color: K.tinta, valign: "middle" });
});
s.addNotes(`Pedí que alguien del grupo explique cada idea con sus palabras antes de mostrar la siguiente. Si alguna idea no queda clara, volvé a la diapositiva correspondiente:
1 → diapositiva 5 · 2 → 7 · 3 → 9 y 10 · 4 → 13 · 5 → 8 y 13 · 6 → 14.`);

// ===================================================================== 20
s = nueva("PORTADA", "Cierre");
s.addText("Próximos pasos", { placeholder: "title" });
s.addText("Segunda clase: práctica en pantalla. Armar un pliego, evaluar ofertas, catálogo de artículos (CAByS) y vista al Tribunal de Cuentas", { placeholder: "body" });
circulo(s, 0.7, 0.6, 0.75, K.marca, "✓", 26);
texto(s, "Mesa de ayuda de TIMBÓ Compras: timbocompras@santafe.gob.ar · 0342-4506600 / 4506800 · de 8 a 13 h", { x: 0.7, y: 4.55, w: 8.6, h: 0.5, fontSize: 13, color: "CFE7E6" });
s.addNotes(`Cierre (2 min).
- Agradecer y repartir el resumen de una página.
- Contar qué queda para la segunda clase: práctica en pantalla con los roles (Gestor, Supervisor, Evaluador), el formulario CAByS para artículos que no están en el catálogo, la vista al Tribunal de Cuentas y el SIN, y las directas por urgencia o desierto.
- Recordar el canal oficial: mesa de ayuda de TIMBÓ Compras (Circular SCyGB 03/2026).
- Invitar a dejar dudas en el Centro de Aprendizaje ("Dejar una consulta").`);

const { applyTheme } = require(process.env.SKILL_DIR + "/scripts/apply_theme.js");
(async () => {
  await pres.writeFile({ fileName: salida });
  await applyTheme(salida, THEME);
  console.log("ok", salida, n, "diapositivas");
})();
