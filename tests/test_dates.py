from datetime import datetime

from anpd_monitor.dates import LIMA_TZ, build_window, parse_spanish_publication_date


def test_parse_spanish_publication_date_accepts_setiembre():
    parsed = parse_spanish_publication_date("29 de setiembre de 2025")
    assert parsed == datetime(2025, 9, 29, tzinfo=LIMA_TZ)


def test_build_window_uses_previous_seven_days():
    end = datetime(2026, 7, 18, 16, 0, tzinfo=LIMA_TZ)
    window = build_window(7, end)
    assert window.start == datetime(2026, 7, 11, 16, 0, tzinfo=LIMA_TZ)
    assert window.contains(datetime(2026, 7, 18, 12, 0, tzinfo=LIMA_TZ))

