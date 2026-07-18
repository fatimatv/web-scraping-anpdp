from datetime import datetime

import pytest

from anpd_monitor.dates import LIMA_TZ
from anpd_monitor.downloader import PdfValidationError, build_filename, safe_slug, sha256_bytes, validate_pdf
from anpd_monitor.models import Category, DocumentCandidate


def test_safe_filename_is_ascii_and_stable():
    doc = DocumentCandidate(
        category=Category.OPINIONES,
        title="OC N° 001-2026 - Factura electronica / reserva tributaria",
        publication_url="https://www.gob.pe/x",
        portal_id="1",
        publication_date=datetime(2026, 7, 18, tzinfo=LIMA_TZ),
        number="OC N° 001-2026-JUS/DGTAIPD",
    )
    filename = build_filename(doc)
    assert filename.startswith("2026-07-18_opiniones_consultivas_oc_n_001_2026")
    assert filename.endswith(".pdf")


def test_validate_pdf_rejects_html_saved_as_pdf():
    with pytest.raises(PdfValidationError):
        validate_pdf(b"<!doctype html><html></html>" * 20, min_bytes=10)


def test_validate_pdf_accepts_signature_and_hashes():
    content = b"%PDF-1.7\n" + b"x" * 300
    validate_pdf(content, min_bytes=10)
    assert sha256_bytes(content) == sha256_bytes(content)
    assert safe_slug("Resolución N.° Á") == "resolucion_n_a"

