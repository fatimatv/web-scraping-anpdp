from anpd_monitor.config import COLLECTIONS
from anpd_monitor.dates import parse_spanish_publication_date
from anpd_monitor.extractor import ExtractionError, extract_collection, extract_detail, extract_next_page_url


COLLECTION_HTML = """
<div class="js-official-documents-search-count">2 resultados:</div>
<div class="js-official-documents-search-results">
  <div class="shadow-campaign-card">
    <div class="border-b border-gray-700 pb-2 font-medium mb-3">18 de julio de 2026</div>
    <a class="leading-6 font-bold" href="/institucion/anpd/informes-publicaciones/9001-oc-001-2026">
      OC N° 001-2026-JUS/DGTAIPD - Sobre prueba
    </a>
    Opinion Consultiva N° 001-2026-JUS/DGTAIPD.
    <div>Disponible en formato PDF</div>
  </div>
</div>
"""

DETAIL_HTML = """
<div class="institution-document__header black">
  <h2>OC N° 001-2026-JUS/DGTAIPD - Sobre prueba</h2>
  <p>Informe</p>
  <p>18 de julio de 2026</p>
</div>
<div class="description rule-content">
  <p>Opinion Consultiva N° 001-2026-JUS/DGTAIPD.</p>
  <a class="btn btn--secondary download" href="https://cdn.www.gob.pe/uploads/document/file/1/test.pdf?v=1">Descargar</a>
</div>
"""


def test_extract_collection_reads_cards_with_official_publication_date():
    docs = extract_collection(COLLECTION_HTML, COLLECTIONS["opiniones"])
    assert len(docs) == 1
    assert docs[0].publication_url == "https://www.gob.pe/institucion/anpd/informes-publicaciones/9001-oc-001-2026"
    assert docs[0].publication_date == parse_spanish_publication_date("18 de julio de 2026")
    assert docs[0].number == "OC N° 001-2026-JUS/DGTAIPD"


def test_extract_detail_reads_pdf_url_and_overrides_metadata():
    doc = extract_collection(COLLECTION_HTML, COLLECTIONS["opiniones"])[0]
    detailed = extract_detail(DETAIL_HTML, doc)
    assert detailed.file_url == "https://cdn.www.gob.pe/uploads/document/file/1/test.pdf?v=1"
    assert detailed.title == "OC N° 001-2026-JUS/DGTAIPD - Sobre prueba"


def test_extract_collection_detects_structure_change_when_results_exist():
    html = '<p class="js-official-documents-search-count">1 resultados:</p><div>No cards</div>'
    try:
        extract_collection(html, COLLECTIONS["arco"])
    except ExtractionError as exc:
        assert "no se extrajeron" in str(exc)
    else:
        raise AssertionError("Expected ExtractionError")


def test_extract_next_page_url_reads_gobpe_pagination():
    html = '<span class="next"><a rel="next" href="/institucion/anpd/colecciones/1?sheet=2">Siguiente</a></span>'
    assert (
        extract_next_page_url(html, "https://www.gob.pe/institucion/anpd/colecciones/1")
        == "https://www.gob.pe/institucion/anpd/colecciones/1?sheet=2"
    )
