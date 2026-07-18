from __future__ import annotations

import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from .models import DateWindow

LIMA_TZ = ZoneInfo("America/Lima")

MONTHS_ES = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "setiembre": 9,
    "septiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}


def now_lima() -> datetime:
    return datetime.now(LIMA_TZ)


def build_window(days: int, end: datetime | None = None) -> DateWindow:
    end_dt = end or now_lima()
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=LIMA_TZ)
    return DateWindow(start=end_dt - timedelta(days=days), end=end_dt)


def parse_spanish_publication_date(text: str) -> datetime | None:
    normalized = " ".join(text.strip().lower().split())
    match = re.search(r"(\d{1,2})\s+de\s+([a-záéíóúñ]+)\s+de\s+(\d{4})", normalized)
    if not match:
        return None
    day, month_name, year = match.groups()
    month = MONTHS_ES.get(month_name)
    if not month:
        return None
    return datetime(int(year), month, int(day), tzinfo=LIMA_TZ)

