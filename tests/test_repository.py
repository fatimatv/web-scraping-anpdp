from datetime import datetime

from anpd_monitor.dates import LIMA_TZ
from anpd_monitor.models import Category, ProcessedDocument, ProcessingStatus
from anpd_monitor.repository import DocumentRepository


def test_repository_prevents_duplicate_by_url_portal_or_hash(tmp_path):
    repo = DocumentRepository(tmp_path / "db.sqlite3")
    checked_at = datetime(2026, 7, 18, tzinfo=LIMA_TZ)
    doc = ProcessedDocument(
        category=Category.ARCO,
        title="Resolucion",
        publication_url="https://www.gob.pe/institucion/anpd/normas-legales/1-test",
        portal_id="1",
        publication_date=checked_at,
        sha256="a" * 64,
        status=ProcessingStatus.DOWNLOADED,
    )
    repo.upsert(doc, checked_at)
    duplicate = ProcessedDocument(
        category=Category.ARCO,
        title="Resolucion duplicada",
        publication_url="https://www.gob.pe/otra",
        portal_id="1",
        publication_date=checked_at,
        status=ProcessingStatus.NEW,
    )
    assert repo.find_existing(duplicate)["title"] == "Resolucion"
    repo.close()

