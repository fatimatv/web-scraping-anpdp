from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path


class Category(StrEnum):
    SANCIONADORES = "procedimientos_sancionadores"
    ARCO = "derechos_arco"
    OPINIONES = "opiniones_consultivas"


class ProcessingStatus(StrEnum):
    NEW = "new"
    EXISTING = "existing"
    DOWNLOADED = "downloaded"
    DRY_RUN = "dry_run"
    MANUAL_REVIEW = "manual_review"
    ERROR = "error"


@dataclass(frozen=True)
class CollectionConfig:
    key: str
    category: Category
    title: str
    url: str
    kind: str


@dataclass
class DocumentCandidate:
    category: Category
    title: str
    publication_url: str
    portal_id: str | None
    publication_date: datetime | None
    summary: str = ""
    number: str | None = None
    document_date: datetime | None = None
    file_url: str | None = None


@dataclass
class ProcessedDocument(DocumentCandidate):
    sha256: str | None = None
    local_path: Path | None = None
    status: ProcessingStatus = ProcessingStatus.NEW
    error_message: str | None = None
    first_detected_at: datetime | None = None
    downloaded_at: datetime | None = None
    last_checked_at: datetime | None = None
    changed_hash: bool = False


@dataclass
class SourceResult:
    source: CollectionConfig
    status: str
    candidates_seen: int = 0
    new_documents: list[ProcessedDocument] = field(default_factory=list)
    existing_documents: list[ProcessedDocument] = field(default_factory=list)
    manual_review: list[ProcessedDocument] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DateWindow:
    start: datetime
    end: datetime

    def contains(self, value: datetime) -> bool:
        return self.start <= value <= self.end

