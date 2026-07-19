const flowSteps = [
  {
    title: "1. Solicita HTML o datos estructurados",
    body:
      "La IA programa una solicitud HTTP a la pagina oficial. Si la informacion ya viene en el HTML, usa requests. Si depende de JavaScript, evalua Playwright como ultima opcion.",
    bullets: ["Respeta timeouts", "Usa User-Agent identificable", "No evade autenticacion ni CAPTCHA"],
  },
  {
    title: "2. Extrae datos relevantes",
    body:
      "El codigo busca bloques repetidos: titulo, fecha oficial, URL de detalle, sumilla, categoria y enlace al documento. La IA intenta usar selectores estables, no clases fragiles.",
    bullets: ["Titulo", "Fecha oficial de publicacion", "URL canonica", "PDF"],
  },
  {
    title: "3. Normaliza fechas",
    body:
      "Convierte textos como '18 de julio de 2026' a una fecha comparable. La regla juridica es incluir solo documentos dentro del periodo definido.",
    bullets: ["Zona America/Lima", "Intervalo verificable", "Revision manual si falta fecha"],
  },
  {
    title: "4. Descarga y valida PDFs",
    body:
      "El sistema descarga solo archivos publicos y confirma que sean PDFs reales. Si recibe HTML, una pagina de error o un archivo demasiado pequeno, lo rechaza.",
    bullets: ["Firma %PDF-", "Tamano minimo", "Hash SHA-256"],
  },
  {
    title: "5. Evita duplicados",
    body:
      "Cada documento se compara contra registros anteriores usando URL, identificador del portal y hash. Si el contenido cambia, se conserva una nueva version.",
    bullets: ["SQLite", "URL canonica", "Id del portal", "SHA-256"],
  },
  {
    title: "6. Genera reporte y trazabilidad",
    body:
      "La salida debe explicar que se reviso, que se encontro, que fallo y que requiere revision manual. Si no hay novedades, el reporte tambien se genera.",
    bullets: ["Markdown", "JSON", "Logs", "Estado por fuente"],
  },
];

const promptTemplate = ({ entity, documents, frequency, urls }) => `Actua como arquitecto de software e ingeniero senior especializado en Python, web scraping responsable, monitoreo de fuentes publicas juridicas y procesamiento documental.

Objetivo:
Disena e implementa una aplicacion que revise de forma ${frequency} las publicaciones oficiales de ${entity} y detecte nuevos documentos de tipo: ${documents}.

Fuentes oficiales:
${urls}

Criterio temporal:
Usa como criterio principal la fecha oficial de publicacion mostrada por la pagina de la entidad. No confundas fecha de publicacion, fecha de emision del acto, fecha de actualizacion de la pagina ni fecha tecnica del PDF. Usa zona horaria America/Lima.

Requisitos tecnicos:
- Python 3.12 o estable equivalente.
- requests o httpx para HTTP.
- BeautifulSoup o lxml para HTML.
- Playwright solo si el contenido se carga por JavaScript.
- SQLite para trazabilidad local.
- pytest para pruebas.
- logging estructurado.
- .env.example para configuracion.

Modelo de datos minimo:
categoria, titulo, numero, fecha de publicacion, fecha del documento, URL de publicacion, URL del archivo, hash SHA-256, archivo local, primera deteccion, fecha de descarga, estado, error y ultima verificacion.

Controles:
- Evitar duplicados por URL, identificador del portal y hash.
- Validar que el archivo sea realmente PDF.
- Tolerar falla parcial de una fuente.
- Registrar revision manual cuando no haya fecha oficial verificable.
- Generar reporte Markdown y JSON aunque no haya novedades.

Comandos esperados:
python -m monitor run
python -m monitor run --dry-run
python -m monitor run --days 7
python -m monitor validate-sources

Antes de programar:
Inspecciona la estructura real de las paginas, identifica si el contenido esta en HTML, endpoints internos o JavaScript, y luego implementa por modulos con pruebas.`;

function byId(id) {
  return document.getElementById(id);
}

function setCode(id, text) {
  const target = byId(id);
  target.textContent = text;
}

function buildPrompt() {
  setCode(
    "promptOutput",
    promptTemplate({
      entity: byId("entity").value.trim() || "la entidad publica",
      documents: byId("documents").value.trim() || "jurisprudencia y documentos oficiales",
      frequency: byId("frequency").value,
      urls: byId("urls").value.trim() || "Incluye aqui las URLs oficiales.",
    }),
  );
}

function updateSourceScore() {
  const checks = [...document.querySelectorAll("#sourceChecklist input")];
  const done = checks.filter((item) => item.checked).length;
  byId("sourceScore").textContent = `${done} / ${checks.length}`;
  let advice = "Marca los puntos que puedas comprobar.";
  if (done >= 6) {
    advice = "La fuente esta lista para una prueba controlada de scraping.";
  } else if (done >= 4) {
    advice = "La fuente es prometedora, pero aun hay riesgos que documentar.";
  } else if (done > 0) {
    advice = "Todavia falta certeza para automatizar con confianza.";
  }
  byId("sourceAdvice").textContent = advice;
}

function renderFlow(index) {
  const item = flowSteps[index];
  byId("flowExplanation").innerHTML = `
    <h3>${item.title}</h3>
    <p>${item.body}</p>
    <ul>${item.bullets.map((bullet) => `<li>${bullet}</li>`).join("")}</ul>
  `;
  document
    .querySelectorAll(".flow-step")
    .forEach((step) => step.classList.toggle("active", step.dataset.flow === String(index)));
}

function buildBrief() {
  const fields = [...document.querySelectorAll(".adapter-form input, .adapter-form textarea")];
  const [entity, matter, url, documentType, rule] = fields.map((field) => field.value.trim() || "Pendiente");
  setCode(
    "briefOutput",
    `Brief tecnico-juridico

Entidad: ${entity}
Materia: ${matter}
Fuente oficial: ${url}
Documento esperado: ${documentType}
Regla de inclusion: ${rule}

Preguntas que debe resolver la IA:
1. La informacion esta en HTML estatico, endpoint interno o JavaScript?
2. Cual es la fecha oficial de publicacion?
3. Hay URL permanente por documento?
4. Como se identifica el PDF publico?
5. Que campos deben guardarse para trazabilidad?
6. Como se evitara duplicar documentos ya procesados?
7. Que pruebas automatizadas demostraran que el monitor funciona?`,
  );
}

async function copyBlock(id, button) {
  const text = byId(id).innerText;
  await navigator.clipboard.writeText(text);
  const previous = button.textContent;
  button.textContent = "Copiado";
  setTimeout(() => {
    button.textContent = previous;
  }, 1200);
}

document.querySelectorAll(".copy").forEach((button) => {
  button.addEventListener("click", () => copyBlock(button.dataset.copy, button));
});

document.querySelectorAll("#sourceChecklist input").forEach((input) => {
  input.addEventListener("change", updateSourceScore);
});

document.querySelectorAll(".flow-step").forEach((button) => {
  button.addEventListener("click", () => renderFlow(Number(button.dataset.flow)));
});

byId("buildPrompt").addEventListener("click", buildPrompt);
byId("buildBrief").addEventListener("click", buildBrief);

buildPrompt();
buildBrief();
updateSourceScore();
renderFlow(0);
