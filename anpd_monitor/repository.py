from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from .models import ProcessedDocument


class DocumentRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self.init_schema()

    def init_schema(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              category TEXT NOT NULL,
              title TEXT NOT NULL,
              number TEXT,
              publication_date TEXT,
              document_date TEXT,
              publication_url TEXT NOT NULL,
              file_url TEXT,
              portal_id TEXT,
              sha256 TEXT,
              local_name TEXT,
              first_detected_at TEXT,
              downloaded_at TEXT,
              status TEXT NOT NULL,
              error_message TEXT,
              last_checked_at TEXT,
              UNIQUE(publication_url),
              UNIQUE(portal_id),
              UNIQUE(sha256)
            )
            """
        )
        self.connection.commit()

    def find_existing(self, doc: ProcessedDocument) -> sqlite3.Row | None:
        clauses = ["publication_url = ?"]
        params: list[str] = [doc.publication_url]
        if doc.portal_id:
            clauses.append("portal_id = ?")
            params.append(doc.portal_id)
        if doc.sha256:
            clauses.append("sha256 = ?")
            params.append(doc.sha256)
        query = f"SELECT * FROM documents WHERE {' OR '.join(clauses)} LIMIT 1"
        return self.connection.execute(query, params).fetchone()

    def upsert(self, doc: ProcessedDocument, checked_at: datetime) -> None:
        existing = self.find_existing(doc)
        if existing:
            self.connection.execute(
                """
                UPDATE documents
                SET title = ?, number = ?, publication_date = ?, document_date = ?,
                    file_url = ?, sha256 = COALESCE(?, sha256), local_name = COALESCE(?, local_name),
                    downloaded_at = COALESCE(?, downloaded_at), status = ?, error_message = ?,
                    last_checked_at = ?
                WHERE id = ?
                """,
                (
                    doc.title,
                    doc.number,
                    _dt(doc.publication_date),
                    _dt(doc.document_date),
                    doc.file_url,
                    doc.sha256,
                    str(doc.local_path) if doc.local_path else None,
                    _dt(doc.downloaded_at),
                    doc.status.value,
                    doc.error_message,
                    _dt(checked_at),
                    existing["id"],
                ),
            )
        else:
            self.connection.execute(
                """
                INSERT INTO documents (
                    category, title, number, publication_date, document_date,
                    publication_url, file_url, portal_id, sha256, local_name,
                    first_detected_at, downloaded_at, status, error_message, last_checked_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doc.category.value,
                    doc.title,
                    doc.number,
                    _dt(doc.publication_date),
                    _dt(doc.document_date),
                    doc.publication_url,
                    doc.file_url,
                    doc.portal_id,
                    doc.sha256,
                    str(doc.local_path) if doc.local_path else None,
                    _dt(doc.first_detected_at),
                    _dt(doc.downloaded_at),
                    doc.status.value,
                    doc.error_message,
                    _dt(checked_at),
                ),
            )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()


def _dt(value: datetime | None) -> str | None:
    return value.isoformat() if value else None
