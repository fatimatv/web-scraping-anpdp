from datetime import datetime

from anpd_monitor.config import COLLECTIONS
from anpd_monitor.dates import LIMA_TZ, build_window
from anpd_monitor.models import SourceResult
from anpd_monitor.reporter import generate_reports


def test_report_generated_with_exact_no_news_message(tmp_path):
    run_at = datetime(2026, 7, 18, 16, 0, tzinfo=LIMA_TZ)
    window = build_window(7, run_at)
    md_path, json_path = generate_reports(
        tmp_path,
        run_at,
        window,
        [SourceResult(source=source, status="ok") for source in COLLECTIONS.values()],
    )
    md = md_path.read_text(encoding="utf-8")
    assert json_path.exists()
    assert (
        "No se encontraron nuevas resoluciones, decisiones sobre derechos ARCO ni opiniones consultivas "
        "publicadas por la ANPD durante el periodo comprendido entre"
    ) in md

