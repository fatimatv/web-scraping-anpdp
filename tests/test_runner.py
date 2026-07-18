from datetime import datetime

from anpd_monitor.config import Settings
from anpd_monitor.dates import LIMA_TZ
from anpd_monitor.repository import DocumentRepository
from anpd_monitor.runner import run_monitor


class FakeClient:
    def __init__(self, pages: dict[str, str], files: dict[str, bytes] | None = None):
        self.pages = pages
        self.files = files or {}

    def get_text(self, url: str) -> str:
        if url not in self.pages:
            raise RuntimeError(f"missing page {url}")
        return self.pages[url]

    def get_bytes(self, url: str) -> bytes:
        return self.files[url]


def settings(tmp_path):
    return Settings(
        data_dir=tmp_path / "data",
        database_path=tmp_path / "data" / "db.sqlite3",
        log_level="INFO",
        user_agent="tests",
        timeout_seconds=1,
        rate_limit_seconds=0,
        max_retries=1,
        min_pdf_bytes=10,
    )


def test_runner_dry_run_generates_report_without_downloading(tmp_path):
    collection_url = "https://www.gob.pe/institucion/anpd/colecciones/1799-opiniones-consultivas-emitidas-por-la-anpd"
    detail_url = "https://www.gob.pe/institucion/anpd/informes-publicaciones/9001-test"
    pages = {
        collection_url: f"""
        <div class="js-official-documents-search-results">
          <div class="shadow-campaign-card">
            <div class="border-b font-medium">18 de julio de 2026</div>
            <a href="{detail_url}">OC N° 001-2026-JUS/DGTAIPD - Test</a>
            <div>Disponible en formato PDF</div>
          </div>
        </div>
        """,
        detail_url: """
        <div class="institution-document__header"><h2>OC N° 001-2026-JUS/DGTAIPD - Test</h2><p>18 de julio de 2026</p></div>
        <a class="download" href="https://cdn.www.gob.pe/test.pdf">Descargar</a>
        """,
    }
    repo = DocumentRepository(tmp_path / "db.sqlite3")
    md_path, json_path = run_monitor(
        settings(tmp_path),
        category="opiniones",
        dry_run=True,
        client=FakeClient(pages),
        repository=repo,
        run_at=datetime(2026, 7, 18, 16, 0, tzinfo=LIMA_TZ),
    )
    assert "anpd_report" in md_path
    assert "anpd_report" in json_path
    assert not list((tmp_path / "data" / "opiniones_consultivas").glob("**/*.pdf"))
    repo.close()


def test_runner_tolerates_partial_source_error(tmp_path):
    pages = {
        "https://www.gob.pe/institucion/anpd/colecciones/1801-resoluciones-de-los-procedimientos-sancionadores": "<p>sin resultados</p>",
        "https://www.gob.pe/institucion/anpd/colecciones/1749-decisiones-sobre-derechos-arco-2017": "<p>1 resultados:</p>",
        "https://www.gob.pe/institucion/anpd/colecciones/1799-opiniones-consultivas-emitidas-por-la-anpd": "<p>sin resultados</p>",
    }
    md_path, _ = run_monitor(
        settings(tmp_path),
        dry_run=True,
        client=FakeClient(pages),
        run_at=datetime(2026, 7, 18, 16, 0, tzinfo=LIMA_TZ),
    )
    assert "Errores" in open(md_path, encoding="utf-8").read()


def test_runner_follows_pagination_until_documents_are_older_than_window(tmp_path):
    collection_url = "https://www.gob.pe/institucion/anpd/colecciones/1799-opiniones-consultivas-emitidas-por-la-anpd"
    page_two = f"{collection_url}?sheet=2"
    detail_url = "https://www.gob.pe/institucion/anpd/informes-publicaciones/9002-test"
    pages = {
        collection_url: f"""
        <div class="js-official-documents-search-results"></div>
        <span class="next"><a rel="next" href="{page_two}">Siguiente</a></span>
        """,
        page_two: f"""
        <div class="js-official-documents-search-results">
          <div class="shadow-campaign-card">
            <div class="border-b font-medium">18 de julio de 2026</div>
            <a href="{detail_url}">OC N° 002-2026-JUS/DGTAIPD - Test</a>
          </div>
          <div class="shadow-campaign-card">
            <div class="border-b font-medium">1 de julio de 2026</div>
            <a href="https://www.gob.pe/institucion/anpd/informes-publicaciones/old-test">Viejo</a>
          </div>
        </div>
        """,
        detail_url: """
        <div class="institution-document__header"><h2>OC N° 002-2026-JUS/DGTAIPD - Test</h2><p>18 de julio de 2026</p></div>
        <a class="download" href="https://cdn.www.gob.pe/test.pdf">Descargar</a>
        """,
    }
    md_path, _ = run_monitor(
        settings(tmp_path),
        category="opiniones",
        dry_run=True,
        client=FakeClient(pages),
        run_at=datetime(2026, 7, 18, 16, 0, tzinfo=LIMA_TZ),
    )
    assert "Total de documentos nuevos: 1" in open(md_path, encoding="utf-8").read()


def test_runner_downloads_pdf_and_deduplicates_on_second_run(tmp_path):
    collection_url = "https://www.gob.pe/institucion/anpd/colecciones/1749-decisiones-sobre-derechos-arco-2017"
    detail_url = "https://www.gob.pe/institucion/anpd/normas-legales/777-test"
    pdf_url = "https://cdn.www.gob.pe/test.pdf"
    pages = {
        collection_url: f"""
        <div class="js-official-documents-search-results">
          <div class="shadow-campaign-card">
            <div class="border-b font-medium">18 de julio de 2026</div>
            <a href="{detail_url}">Resolucion Directoral N° 200-2026-JUS/DGTAIPD-DPDP</a>
            <div>Numero de expediente: 10-2026</div>
          </div>
        </div>
        """,
        detail_url: f"""
        <div class="institution-document__header"><h2>Resolucion Directoral N° 200-2026-JUS/DGTAIPD-DPDP</h2><p>18 de julio de 2026</p></div>
        <a class="download" href="{pdf_url}">Descargar</a>
        """,
    }
    client = FakeClient(pages, {pdf_url: b"%PDF-1.7\n" + b"x" * 300})
    repo = DocumentRepository(tmp_path / "db.sqlite3")
    run_at = datetime(2026, 7, 18, 16, 0, tzinfo=LIMA_TZ)
    run_monitor(settings(tmp_path), category="arco", client=client, repository=repo, run_at=run_at)
    pdfs = list((tmp_path / "data" / "derechos_arco").glob("**/*.pdf"))
    assert len(pdfs) == 1
    md_path, _ = run_monitor(settings(tmp_path), category="arco", client=client, repository=repo, run_at=run_at)
    assert "Total de documentos ya registrados: 1" in open(md_path, encoding="utf-8").read()
    repo.close()


def test_runner_sends_missing_date_to_manual_review(tmp_path):
    collection_url = "https://www.gob.pe/institucion/anpd/colecciones/1799-opiniones-consultivas-emitidas-por-la-anpd"
    pages = {
        collection_url: """
        <div class="js-official-documents-search-results">
          <div class="shadow-campaign-card">
            <a href="https://www.gob.pe/institucion/anpd/informes-publicaciones/42-test">Sin fecha verificable</a>
          </div>
        </div>
        """,
    }
    md_path, _ = run_monitor(
        settings(tmp_path),
        category="opiniones",
        dry_run=True,
        client=FakeClient(pages),
        run_at=datetime(2026, 7, 18, 16, 0, tzinfo=LIMA_TZ),
    )
    assert "Total de documentos para revision manual: 1" in open(md_path, encoding="utf-8").read()
