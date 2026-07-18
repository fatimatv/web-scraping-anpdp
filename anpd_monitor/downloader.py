from __future__ import annotations

import hashlib
import re
import unicodedata
from pathlib import Path

from .models import DocumentCandidate


class PdfValidationError(ValueError):
    pass


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def validate_pdf(content: bytes, min_bytes: int = 256) -> None:
    if len(content) < min_bytes:
        raise PdfValidationError(f"PDF demasiado pequeno: {len(content)} bytes")
    if not content.startswith(b"%PDF-"):
        raise PdfValidationError("El archivo no contiene firma PDF valida")
    head = content[:512].lower()
    if b"<html" in head or b"<!doctype html" in head:
        raise PdfValidationError("La descarga parece HTML, no PDF")


def safe_slug(value: str, max_length: int = 80) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", normalized).strip("_").lower()
    return normalized[:max_length].strip("_") or "documento"


def build_filename(candidate: DocumentCandidate, existing_hash: str | None = None) -> str:
    date_part = candidate.publication_date.date().isoformat() if candidate.publication_date else "sin_fecha"
    number = safe_slug(candidate.number or candidate.portal_id or "sin_numero", 45)
    title = safe_slug(candidate.title, 70)
    suffix = f"_{existing_hash[:8]}" if existing_hash else ""
    return f"{date_part}_{candidate.category.value}_{number}_{title}{suffix}.pdf"


def target_directory(base_dir: Path, candidate: DocumentCandidate) -> Path:
    if candidate.publication_date:
        return base_dir / candidate.category.value / f"{candidate.publication_date:%Y}" / f"{candidate.publication_date:%m}"
    return base_dir / candidate.category.value / "sin_fecha"


def write_pdf(base_dir: Path, candidate: DocumentCandidate, content: bytes, min_bytes: int) -> tuple[Path, str]:
    validate_pdf(content, min_bytes=min_bytes)
    digest = sha256_bytes(content)
    directory = target_directory(base_dir, candidate)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / build_filename(candidate)
    if path.exists():
        path = directory / build_filename(candidate, digest)
    path.write_bytes(content)
    return path, digest

