const stepContent = [
  {
    title: "1. Ubicar una fuente oficial",
    body: "No se empieza por el codigo. Se empieza por probar que la pagina pertenece a la entidad, que el listado es publico y que el enlace sera reconocible en el futuro.",
    bullets: ["Dominio oficial", "URL estable", "Paginacion o buscador verificable"],
  },
  {
    title: "2. Convertir el interes legal en una regla",
    body: "El scraper necesita una definicion juridica: que documentos entran, cuales quedan fuera y que categoria tendran en el reporte.",
    bullets: ["Materia", "Tipo de acto", "Periodo de revision"],
  },
  {
    title: "3. Usar la fecha correcta",
    body: "La fecha principal es la publicacion oficial de la pagina. La fecha de emision, actualizacion o creacion del PDF puede servir como contexto, pero no decide la novedad.",
    bullets: ["Publicacion oficial", "Zona horaria", "Revision manual si no hay fecha"],
  },
  {
    title: "4. Descargar con cuidado",
    body: "Solo se descargan documentos publicos. El sistema debe confirmar que el archivo es realmente PDF y no una pagina HTML de error.",
    bullets: ["Firma PDF", "Tamano minimo", "Sin CAPTCHA ni autenticacion"],
  },
  {
    title: "5. Dejar huella probatoria",
    body: "Cada ejecucion debe poder reconstruirse: URL, fecha, hash del archivo, estado y mensaje de error si algo fallo.",
    bullets: ["SHA-256", "SQLite o base local", "Logs y reporte"],
  },
  {
    title: "6. Reportar incluso si no hay novedades",
    body: "La ausencia de novedades tambien es un resultado. El abogado necesita saber que la fuente fue revisada y que no hubo publicaciones dentro del periodo.",
    bullets: ["Resumen", "Fuentes consultadas", "Errores o revision manual"],
  },
];

const navItems = document.querySelectorAll(".nav-item");
const panels = document.querySelectorAll(".view");
const progressText = document.querySelector("#progressText");
const progressBar = document.querySelector("#progressBar");
const visited = new Set();

function showPanel(name) {
  navItems.forEach((item) => item.classList.toggle("active", item.dataset.view === name));
  panels.forEach((panel) => panel.classList.toggle("active", panel.dataset.panel === name));
  visited.add(name);
  progressText.textContent = `${visited.size} de 6`;
  progressBar.style.width = `${(visited.size / 6) * 100}%`;
}

navItems.forEach((item) => item.addEventListener("click", () => showPanel(item.dataset.view)));

function renderStep(index) {
  const detail = document.querySelector("#stepDetail");
  const item = stepContent[index];
  detail.innerHTML = `
    <h3>${item.title}</h3>
    <p>${item.body}</p>
    <ul>${item.bullets.map((bullet) => `<li>${bullet}</li>`).join("")}</ul>
  `;
  document
    .querySelectorAll(".process-step")
    .forEach((step) => step.classList.toggle("selected", step.dataset.step === String(index)));
}

document.querySelectorAll(".process-step").forEach((button) => {
  button.addEventListener("click", () => renderStep(Number(button.dataset.step)));
});

document.querySelectorAll("[data-check]").forEach((check) => {
  check.addEventListener("change", () => {
    const total = document.querySelectorAll("[data-check]").length;
    const done = document.querySelectorAll("[data-check]:checked").length;
    const status = document.querySelector("#checkStatus");
    if (done === total) {
      status.textContent = "La fuente parece apta para una automatizacion responsable. Falta validar el HTML real y hacer una prueba controlada.";
    } else if (done >= 4) {
      status.textContent = "La fuente tiene buena base, pero aun hay puntos que conviene verificar antes de automatizar.";
    } else {
      status.textContent = "Todavia no hay suficiente certeza. Prioriza fecha oficial, enlace permanente y acceso publico.";
    }
  });
});

document.querySelector("#calculateWindow").addEventListener("click", () => {
  const runDate = document.querySelector("#runDate").value;
  const days = Number(document.querySelector("#daysBack").value || 7);
  const target = document.querySelector("#windowResult");
  if (!runDate) {
    target.textContent = "Elige una fecha de ejecucion.";
    return;
  }
  const end = new Date(`${runDate}T00:00:00-05:00`);
  const start = new Date(end);
  start.setDate(start.getDate() - days);
  target.innerHTML = `<strong>Periodo:</strong> desde ${start.toLocaleDateString("es-PE")} hasta ${end.toLocaleDateString("es-PE")} en zona America/Lima.`;
});

document.querySelector("#classifyButton").addEventListener("click", () => {
  const text = document.querySelector("#titleInput").value;
  const lower = text.toLowerCase();
  let category = "Revision manual";
  if (lower.includes("pas") || lower.includes("sancion")) category = "Procedimiento sancionador";
  if (lower.includes("arco")) category = "Derechos ARCO";
  if (lower.includes("opinion") || lower.includes("oc ")) category = "Opinion consultiva";
  const exp = text.match(/EXP[.\s-]*\d{1,4}-\d{4}/i)?.[0] || "No identificado";
  const number = text.match(/N[.°º]?\s*[\d-]+/i)?.[0] || "No identificado";
  document.querySelector("#metadataOutput").innerHTML = `
    <div><span>Categoria</span><strong>${category}</strong></div>
    <div><span>Numero</span><strong>${number}</strong></div>
    <div><span>Expediente</span><strong>${exp}</strong></div>
    <div><span>Decision</span><strong>${category === "Revision manual" ? "Revisar antes de descargar" : "Puede pasar a validacion de fecha"}</strong></div>
  `;
});

document.querySelector("#copyBrief").addEventListener("click", () => {
  const fields = [...document.querySelectorAll(".brief-form input, .brief-form textarea, .brief-form select")];
  const [entity, url, docs, rule, frequency] = fields.map((field) => field.value || "Pendiente");
  document.querySelector("#briefOutput").textContent = `Entidad: ${entity}
URL oficial: ${url}
Documentos: ${docs}
Criterio juridico: ${rule}
Frecuencia: ${frequency}
Controles minimos: fecha oficial verificable, descarga publica, deduplicacion por URL/id/hash, reporte con novedades y ausencia de novedades.`;
});

document.querySelector("#runDate").valueAsDate = new Date();
showPanel("mapa");
renderStep(0);
