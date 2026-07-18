from __future__ import annotations

import logging
from datetime import datetime

from .config import COLLECTIONS, Settings
from .dates import build_window, now_lima
from .downloader import PdfValidationError, sha256_bytes, validate_pdf, write_pdf
from .extractor import extract_collection, extract_detail, extract_next_page_url
from .http_client import HttpClient
from .models import ProcessingStatus, ProcessedDocument, SourceResult
from .repository import DocumentRepository
from .reporter import generate_reports

LOGGER = logging.getLogger(__name__)


def run_monitor(
    settings: Settings,
    *,
    days: int = 7,
    category: str | None = None,
    dry_run: bool = False,
    client: HttpClient | None = None,
    repository: DocumentRepository | None = None,
    run_at: datetime | None = None,
) -> tuple[str, str]:
    run_dt = run_at or now_lima()
    window = build_window(days, run_dt)
    selected = [COLLECTIONS[category]] if category else list(COLLECTIONS.values())
    http = client or HttpClient(
        settings.user_agent,
        timeout_seconds=settings.timeout_seconds,
        max_retries=settings.max_retries,
        rate_limit_seconds=settings.rate_limit_seconds,
    )
    repo = repository or DocumentRepository(settings.database_path)
    source_results: list[SourceResult] = []
    try:
        for source in selected:
            result = SourceResult(source=source, status="ok")
            source_results.append(result)
            try:
                page_url: str | None = source.url
                while page_url:
                    html = http.get_text(page_url)
                    candidates = extract_collection(html, source)
                    result.candidates_seen += len(candidates)
                    should_continue = _process_candidates(
                        candidates, http, repo, result, run_dt, window, settings, dry_run
                    )
                    if not should_continue:
                        break
                    page_url = extract_next_page_url(html, page_url)
            except (PdfValidationError, Exception) as exc:
                result.status = "error"
                message = f"{source.title}: {exc}"
                LOGGER.exception(message)
                result.errors.append(message)
        md_path, json_path = generate_reports(settings.data_dir, run_dt, window, source_results)
        return str(md_path), str(json_path)
    finally:
        if repository is None:
            repo.close()


def _process_candidates(
    candidates,
    http: HttpClient,
    repo: DocumentRepository,
    result: SourceResult,
    run_dt: datetime,
    window,
    settings: Settings,
    dry_run: bool,
) -> bool:
    continue_pages = True
    for candidate in candidates:
        processed = ProcessedDocument(**candidate.__dict__)
        if not processed.publication_date:
            processed.status = ProcessingStatus.MANUAL_REVIEW
            processed.error_message = "Fecha oficial de publicacion no verificable"
            result.manual_review.append(processed)
            repo.upsert(processed, run_dt)
            continue
        if processed.publication_date < window.start:
            continue_pages = False
            continue
        if not window.contains(processed.publication_date):
            continue
        processed = ProcessedDocument(**extract_detail(http.get_text(processed.publication_url), processed).__dict__)
        processed.first_detected_at = run_dt
        processed.last_checked_at = run_dt
        existing = repo.find_existing(processed)
        if existing:
            processed.status = ProcessingStatus.EXISTING
            result.existing_documents.append(processed)
            repo.upsert(processed, run_dt)
            continue
        if dry_run:
            processed.status = ProcessingStatus.DRY_RUN
            result.new_documents.append(processed)
            repo.upsert(processed, run_dt)
            continue
        if not processed.file_url:
            processed.status = ProcessingStatus.MANUAL_REVIEW
            processed.error_message = "No se encontro enlace PDF"
            result.manual_review.append(processed)
            repo.upsert(processed, run_dt)
            continue
        content = http.get_bytes(processed.file_url)
        validate_pdf(content, settings.min_pdf_bytes)
        processed.sha256 = sha256_bytes(content)
        hash_existing = repo.find_existing(processed)
        if hash_existing:
            processed.status = ProcessingStatus.EXISTING
            result.existing_documents.append(processed)
            repo.upsert(processed, run_dt)
            continue
        path, digest = write_pdf(settings.data_dir, processed, content, settings.min_pdf_bytes)
        processed.local_path = path
        processed.sha256 = digest
        processed.downloaded_at = run_dt
        processed.status = ProcessingStatus.DOWNLOADED
        result.new_documents.append(processed)
        repo.upsert(processed, run_dt)
    return continue_pages


def validate_sources(settings: Settings) -> list[SourceResult]:
    http = HttpClient(
        settings.user_agent,
        timeout_seconds=settings.timeout_seconds,
        max_retries=settings.max_retries,
        rate_limit_seconds=settings.rate_limit_seconds,
    )
    results = []
    for source in COLLECTIONS.values():
        result = SourceResult(source=source, status="ok")
        try:
            result.candidates_seen = len(extract_collection(http.get_text(source.url), source))
        except Exception as exc:
            result.status = "error"
            result.errors.append(str(exc))
        results.append(result)
    return results
