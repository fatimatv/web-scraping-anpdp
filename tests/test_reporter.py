from datetime import datetime

from anpd_monitor.config import COLLECTIONS
from anpd_monitor.dates import LIMA_TZ, build_window
from anpd_monitor.models import SourceResult
from anpd_monitor.reporter import build_dashboard_html, generate_reports


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


def test_dashboard_html_generated_and_embeds_payload(tmp_path):
    run_at = datetime(2026, 7, 18, 16, 0, tzinfo=LIMA_TZ)
    window = build_window(7, run_at)
    generate_reports(
        tmp_path,
        run_at,
        window,
        [SourceResult(source=source, status="ok") for source in COLLECTIONS.values()],
    )
    dashboard = (tmp_path / "reports" / "dashboard.html").read_text(encoding="utf-8")
    assert "ANPD Monitor" in dashboard
    assert '<script id="report" type="application/json">' in dashboard
    assert '"summary"' in dashboard
    # XSS-safe: escaping helper y allowlist de esquemas presentes
    assert "safeUrl" in dashboard
    # No debe existir el marcador sin sustituir
    assert "__REPORT_JSON__" not in dashboard
    # Tokens del brandbook IALAW
    assert "--ialaw-blue: #011ef4" in dashboard
    assert "Poppins" in dashboard
    # data_dir_abs debe llegar al payload embebido (JSON escapa backslashes -> comparar via json.dumps)
    import json as _json
    assert '"data_dir_abs"' in dashboard
    assert _json.dumps(str(tmp_path.resolve()))[1:-1] in dashboard


def test_build_dashboard_html_escapes_script_in_payload():
    html = build_dashboard_html({"marker": "</script><script>alert(1)</script>"})
    # El cierre </script> del payload debe estar escapado, sin romper el <script> host
    assert "</script><script>alert(1)</script>" not in html
    assert "<\\/script>" in html

