from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import DateWindow, ProcessedDocument, SourceResult


NO_NEWS_TEMPLATE = (
    "No se encontraron nuevas resoluciones, decisiones sobre derechos ARCO ni opiniones consultivas "
    "publicadas por la ANPD durante el periodo comprendido entre {start} y {end}."
)


def generate_reports(
    data_dir: Path,
    run_at: datetime,
    window: DateWindow,
    source_results: list[SourceResult],
) -> tuple[Path, Path]:
    reports_dir = data_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    stem = f"anpd_report_{run_at:%Y%m%d_%H%M%S}"
    json_path = reports_dir / f"{stem}.json"
    md_path = reports_dir / f"{stem}.md"
    dashboard_path = reports_dir / "dashboard.html"
    payload = build_payload(run_at, window, source_results)
    payload["data_dir_abs"] = str(data_dir.resolve())
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(build_markdown(payload), encoding="utf-8")
    dashboard_path.write_text(build_dashboard_html(payload), encoding="utf-8")
    return md_path, json_path


def build_payload(run_at: datetime, window: DateWindow, source_results: list[SourceResult]) -> dict[str, Any]:
    new_docs = [doc for result in source_results for doc in result.new_documents]
    existing = [doc for result in source_results for doc in result.existing_documents]
    manual = [doc for result in source_results for doc in result.manual_review]
    errors = [err for result in source_results for err in result.errors]
    return {
        "run_at": run_at.isoformat(),
        "period": {"start": window.start.isoformat(), "end": window.end.isoformat()},
        "sources": [
            {
                "key": result.source.key,
                "title": result.source.title,
                "url": result.source.url,
                "status": result.status,
                "candidates_seen": result.candidates_seen,
                "errors": result.errors,
            }
            for result in source_results
        ],
        "summary": {
            "new_documents": len(new_docs),
            "existing_documents": len(existing),
            "errors": len(errors),
            "manual_review": len(manual),
        },
        "new_documents": [_doc_payload(doc) for doc in new_docs],
        "existing_documents": [_doc_payload(doc) for doc in existing],
        "manual_review": [_doc_payload(doc) for doc in manual],
        "errors": errors,
        "no_news_message": NO_NEWS_TEMPLATE.format(
            start=window.start.isoformat(), end=window.end.isoformat()
        )
        if not new_docs
        else None,
    }


def build_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Reporte semanal ANPD",
        "",
        "## Resumen",
        "",
        f"- Fecha y hora de ejecucion: {payload['run_at']}",
        f"- Periodo revisado: {payload['period']['start']} a {payload['period']['end']}",
        f"- Total de documentos nuevos: {payload['summary']['new_documents']}",
        f"- Total de documentos ya registrados: {payload['summary']['existing_documents']}",
        f"- Total de errores: {payload['summary']['errors']}",
        f"- Total de documentos para revision manual: {payload['summary']['manual_review']}",
        "",
        "## Fuentes consultadas",
        "",
    ]
    for source in payload["sources"]:
        lines.append(f"- {source['title']} ({source['status']}): {source['url']}")
    if payload["no_news_message"]:
        lines.extend(["", "## Ausencia de novedades", "", payload["no_news_message"]])
    lines.extend(["", "## Resultados por categoria", ""])
    for doc in payload["new_documents"]:
        lines.extend(
            [
                f"### {doc['title']}",
                "",
                f"- Numero: {doc.get('number') or 'No identificado'}",
                f"- Fecha de publicacion: {doc.get('publication_date') or 'No verificable'}",
                f"- Fecha de emision: {doc.get('document_date') or 'No disponible'}",
                f"- Categoria: {doc['category']}",
                f"- Publicacion: {doc['publication_url']}",
                f"- PDF: {doc.get('file_url') or 'No disponible'}",
                f"- Archivo local: {doc.get('local_path') or 'No descargado'}",
                f"- SHA-256: {doc.get('sha256') or 'No calculado'}",
                "",
            ]
        )
    if payload["manual_review"]:
        lines.extend(["## Revision manual", ""])
        for doc in payload["manual_review"]:
            lines.append(f"- {doc['title']} - {doc['publication_url']}")
    if payload["errors"]:
        lines.extend(["", "## Errores", ""])
        for error in payload["errors"]:
            lines.append(f"- {error}")
    return "\n".join(lines) + "\n"


def build_dashboard_html(payload: dict[str, Any]) -> str:
    embedded = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    return _DASHBOARD_TEMPLATE.replace("__REPORT_JSON__", embedded)


_DASHBOARD_TEMPLATE = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>ANPD Monitor - Panel del ultimo run</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;900&display=swap" rel="stylesheet" />
<style>
  :root {
    --ink: #111111;
    --paper: #ffffff;
    --muted: #6f7072;
    --line: #d4d5d5;
    --ialaw-blue: #011ef4;
    --ialaw-blue-dark: #0118bf;
    --ialaw-yellow: #fbbb02;
    --ialaw-yellow-light: #ffe981;
    --ok: #2f7d5b;
    --warn: #b8791f;
    --err: #b23a3a;
    --shadow: 0 18px 44px rgba(1, 30, 244, 0.13);
  }
  * { box-sizing: border-box; }
  html { scroll-behavior: smooth; }
  body {
    margin: 0; color: var(--ink);
    background:
      linear-gradient(90deg, rgba(1, 30, 244, 0.055) 1px, transparent 1px) 0 0 / 34px 34px,
      linear-gradient(180deg, #ffffff, #f7f8ff);
    font-family: Poppins, Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
  }
  main { max-width: 1000px; margin: 0 auto; padding: 34px 24px 80px; }
  .hero {
    background: rgba(255, 255, 255, 0.72);
    border: 1px solid var(--line);
    border-top: 12px solid var(--ialaw-blue);
    border-radius: 18px;
    padding: 28px;
    margin-bottom: 24px;
  }
  .eyebrow {
    margin: 0 0 10px; color: var(--ialaw-blue);
    font-size: 0.78rem; text-transform: uppercase; font-weight: 900;
  }
  h1 { margin: 0 0 12px; font-size: clamp(1.7rem, 3vw, 2.4rem); color: var(--ialaw-blue); line-height: 1.05; }
  .hero p { margin: 4px 0; color: var(--muted); font-size: 0.98rem; }
  .grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px; }
  .kpi {
    background: var(--paper); border: 1px solid var(--ialaw-blue);
    border-radius: 18px; padding: 18px; box-shadow: var(--shadow);
  }
  .kpi .n { font-size: 2.2rem; font-weight: 900; line-height: 1; margin-bottom: 6px; color: var(--ialaw-blue); }
  .kpi .lbl { color: var(--muted); font-size: 0.72rem; text-transform: uppercase; font-weight: 800; letter-spacing: 0.06em; }
  .kpi.err .n { color: var(--err); }
  .kpi.warn .n { color: var(--warn); }
  .kpi.ok .n { color: var(--ok); }
  section {
    background: rgba(255, 255, 255, 0.72); border: 1px solid var(--line);
    border-radius: 18px; padding: 22px 24px; margin-bottom: 18px;
  }
  section h2 {
    margin: 0 0 14px; font-size: 0.85rem; text-transform: uppercase;
    letter-spacing: 0.06em; color: var(--ialaw-blue); font-weight: 900;
    border-bottom: 2px solid var(--ialaw-blue); padding-bottom: 8px;
  }
  ul.sources { list-style: none; padding: 0; margin: 0; }
  ul.sources li {
    display: flex; align-items: baseline; gap: 10px; padding: 10px 0;
    border-bottom: 1px dashed var(--line); font-size: 0.92rem;
  }
  ul.sources li:last-child { border-bottom: 0; }
  .badge {
    font-size: 0.7rem; padding: 3px 10px; border-radius: 999px; font-weight: 800;
    letter-spacing: 0.06em; text-transform: uppercase;
  }
  .badge.ok { background: #e6f2ec; color: var(--ok); }
  .badge.err { background: #f7e1e1; color: var(--err); }
  .source-title { flex: 1; }
  .source-title a { color: var(--ialaw-blue); font-weight: 700; text-decoration: none; }
  .source-title a:hover { text-decoration: underline; }
  .source-meta { color: var(--muted); font-size: 0.85rem; }
  .doc { border-bottom: 1px solid var(--line); padding: 14px 0; }
  .doc:last-child { border-bottom: 0; }
  .doc h3 { margin: 0 0 4px; font-size: 1rem; color: var(--ink); }
  .doc .meta { color: var(--muted); font-size: 0.85rem; margin-bottom: 6px; }
  .doc .links { font-size: 0.85rem; }
  .doc .links a { color: var(--ialaw-blue); text-decoration: underline; margin-right: 12px; font-weight: 700; }
  code.path { background: var(--ialaw-yellow-light); padding: 2px 8px; border-radius: 4px; font-size: 0.78rem; }
  .empty { color: var(--muted); font-style: italic; margin: 0; }
  .err-item { color: var(--err); font-size: 0.88rem; padding: 4px 0; }
  .folders { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; }
  .folder-card {
    background: white; border: 1px solid var(--ialaw-blue); border-radius: 14px;
    padding: 14px 16px; display: grid; gap: 8px;
  }
  .folder-card b { color: var(--ialaw-blue); font-weight: 800; }
  .folder-card code { font-size: 0.75rem; color: var(--muted); word-break: break-all; }
  .folder-card .actions { display: flex; gap: 8px; flex-wrap: wrap; }
  .btn {
    border: 1px solid var(--ink); background: white; color: var(--ink);
    padding: 8px 14px; border-radius: 999px; font-weight: 800; font-size: 0.8rem;
    cursor: pointer; text-decoration: none; display: inline-block;
  }
  .btn.primary { background: var(--ialaw-blue); color: white; border-color: var(--ialaw-blue); }
  .btn:hover, .btn:focus-visible { background: var(--ink); color: white; outline: none; }
  .btn.primary:hover, .btn.primary:focus-visible { background: var(--ialaw-blue-dark); border-color: var(--ialaw-blue-dark); }
  @media (max-width: 640px) { .grid { grid-template-columns: repeat(2, 1fr); } }
</style>
</head>
<body>
<main>
  <section class="hero">
    <p class="eyebrow">IALAW DIGITAL LAWYERS / ANPD Monitor</p>
    <h1>Panel del &uacute;ltimo run</h1>
    <p id="run-at"></p>
    <p id="period"></p>
  </section>

  <div class="grid">
    <div class="kpi ok"><div class="n" id="k-new">0</div><div class="lbl">Nuevos</div></div>
    <div class="kpi"><div class="n" id="k-existing">0</div><div class="lbl">Ya registrados</div></div>
    <div class="kpi warn"><div class="n" id="k-manual">0</div><div class="lbl">Revisi&oacute;n manual</div></div>
    <div class="kpi err"><div class="n" id="k-errors">0</div><div class="lbl">Errores</div></div>
  </div>

  <section>
    <h2>Fuentes consultadas</h2>
    <ul class="sources" id="sources"></ul>
  </section>

  <section id="folders-section" hidden>
    <h2>Carpetas de PDFs</h2>
    <div class="folders" id="folders"></div>
  </section>

  <section>
    <h2>Documentos nuevos</h2>
    <div id="new-docs"></div>
  </section>

  <section id="manual-section" hidden>
    <h2>Revisi&oacute;n manual</h2>
    <div id="manual-docs"></div>
  </section>

  <section id="errors-section" hidden>
    <h2>Errores</h2>
    <div id="errors"></div>
  </section>
</main>

<script id="report" type="application/json">__REPORT_JSON__</script>
<script>
  const data = JSON.parse(document.getElementById("report").textContent);
  const fmt = iso => {
    if (!iso) return "-";
    const d = new Date(iso);
    return isNaN(d) ? iso : d.toLocaleString("es-PE", { dateStyle: "long", timeStyle: "short" });
  };
  const fmtDate = iso => {
    if (!iso) return "-";
    const d = new Date(iso);
    return isNaN(d) ? iso : d.toLocaleDateString("es-PE", { dateStyle: "long" });
  };
  const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g,
    c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  // ponytail: URLs vienen del scraping (fuente externa); solo http/https en href, resto se descarta
  const safeUrl = u => /^https?:\/\//i.test(String(u || "")) ? esc(u) : "";

  document.getElementById("run-at").textContent = "Ejecutado: " + fmt(data.run_at);
  document.getElementById("period").textContent =
    "Periodo revisado: " + fmtDate(data.period.start) + " - " + fmtDate(data.period.end);
  document.getElementById("k-new").textContent = data.summary.new_documents;
  document.getElementById("k-existing").textContent = data.summary.existing_documents;
  document.getElementById("k-manual").textContent = data.summary.manual_review;
  document.getElementById("k-errors").textContent = data.summary.errors;

  document.getElementById("sources").innerHTML = data.sources.map(s => {
    const url = safeUrl(s.url);
    const title = url
      ? `<a href="${url}" target="_blank" rel="noopener">${esc(s.title)}</a>`
      : esc(s.title);
    return `
      <li>
        <span class="badge ${s.status === "ok" ? "ok" : "err"}">${esc(s.status)}</span>
        <span class="source-title">${title}</span>
        <span class="source-meta">${s.candidates_seen} candidatos</span>
      </li>`;
  }).join("");

  const renderDoc = d => {
    const pub = safeUrl(d.publication_url);
    const file = safeUrl(d.file_url);
    return `
    <div class="doc">
      <h3>${esc(d.title)}</h3>
      <div class="meta">
        ${esc(d.category)} &middot; publicado ${esc(fmtDate(d.publication_date))}
        ${d.number ? " &middot; N&deg; " + esc(d.number) : ""}
      </div>
      <div class="links">
        ${pub ? `<a href="${pub}" target="_blank" rel="noopener">Publicaci&oacute;n</a>` : ""}
        ${file ? `<a href="${file}" target="_blank" rel="noopener">PDF remoto</a>` : ""}
        ${d.local_path ? `<span>Local: <code class="path">${esc(d.local_path)}</code></span>` : ""}
      </div>
    </div>`;
  };

  const newDocs = document.getElementById("new-docs");
  if (data.new_documents.length) {
    newDocs.innerHTML = data.new_documents.map(renderDoc).join("");
  } else {
    newDocs.innerHTML = `<p class="empty">${esc(data.no_news_message || "Sin novedades en el periodo.")}</p>`;
  }

  if (data.manual_review.length) {
    document.getElementById("manual-section").hidden = false;
    document.getElementById("manual-docs").innerHTML = data.manual_review.map(renderDoc).join("");
  }

  if (data.errors.length) {
    document.getElementById("errors-section").hidden = false;
    document.getElementById("errors").innerHTML =
      data.errors.map(e => `<div class="err-item">${esc(e)}</div>`).join("");
  }

  // Bloque "Carpetas de PDFs": una tarjeta por categoria con al menos un doc nuevo o en manual review.
  // Local (file://) -> boton "Abrir carpeta" que lanza Explorer. Online -> "Copiar ruta".
  const catLabels = { sancionadores: "Procedimientos sancionadores", arco: "Derechos ARCO", opiniones: "Opiniones consultivas" };
  const cats = new Set([...data.new_documents, ...data.manual_review].map(d => d.category).filter(Boolean));
  if (cats.size && data.data_dir_abs) {
    const sep = data.data_dir_abs.includes("\\") ? "\\" : "/";
    const isLocal = location.protocol === "file:";
    const cards = [...cats].map(cat => {
      const abs = data.data_dir_abs + sep + cat;
      const fileHref = "file:///" + abs.replace(/\\/g, "/").replace(/ /g, "%20");
      const openBtn = isLocal
        ? `<a class="btn primary" href="${esc(fileHref)}" target="_blank" rel="noopener">Abrir carpeta</a>`
        : "";
      return `
        <div class="folder-card">
          <b>${esc(catLabels[cat] || cat)}</b>
          <code>${esc(abs)}</code>
          <div class="actions">
            ${openBtn}
            <button class="btn" type="button" data-copy-path="${esc(abs)}">Copiar ruta</button>
          </div>
        </div>`;
    });
    document.getElementById("folders").innerHTML = cards.join("");
    document.getElementById("folders-section").hidden = false;
    document.querySelectorAll("[data-copy-path]").forEach(btn => {
      btn.addEventListener("click", async () => {
        try { await navigator.clipboard.writeText(btn.dataset.copyPath); }
        catch { return; }
        const prev = btn.textContent;
        btn.textContent = "Copiado";
        setTimeout(() => { btn.textContent = prev; }, 1200);
      });
    });
  }
</script>
</body>
</html>
"""


def _doc_payload(doc: ProcessedDocument) -> dict[str, Any]:
    payload = asdict(doc)
    for key in ["publication_date", "document_date", "first_detected_at", "downloaded_at", "last_checked_at"]:
        if payload[key]:
            payload[key] = payload[key].isoformat()
    if payload["local_path"]:
        payload["local_path"] = str(payload["local_path"])
    payload["category"] = doc.category.value
    payload["status"] = doc.status.value
    return payload

