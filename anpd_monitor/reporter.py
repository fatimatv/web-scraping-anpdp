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
    payload = build_payload(run_at, window, source_results)
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(build_markdown(payload), encoding="utf-8")
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

