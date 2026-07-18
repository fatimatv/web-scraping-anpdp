from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from .models import Category, CollectionConfig


COLLECTIONS: dict[str, CollectionConfig] = {
    "sancionadores": CollectionConfig(
        key="sancionadores",
        category=Category.SANCIONADORES,
        title="Resoluciones de los procedimientos sancionadores",
        url="https://www.gob.pe/institucion/anpd/colecciones/1801-resoluciones-de-los-procedimientos-sancionadores",
        kind="normas-legales",
    ),
    "arco": CollectionConfig(
        key="arco",
        category=Category.ARCO,
        title="Decisiones sobre derechos ARCO",
        url="https://www.gob.pe/institucion/anpd/colecciones/1749-decisiones-sobre-derechos-arco-2017",
        kind="normas-legales",
    ),
    "opiniones": CollectionConfig(
        key="opiniones",
        category=Category.OPINIONES,
        title="Opiniones consultivas emitidas por la ANPD",
        url="https://www.gob.pe/institucion/anpd/colecciones/1799-opiniones-consultivas-emitidas-por-la-anpd",
        kind="informes-publicaciones",
    ),
}


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    database_path: Path
    log_level: str
    user_agent: str
    timeout_seconds: float
    rate_limit_seconds: float
    max_retries: int
    min_pdf_bytes: int

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        data_dir = Path(os.getenv("ANPD_DATA_DIR", "data"))
        return cls(
            data_dir=data_dir,
            database_path=Path(os.getenv("ANPD_DATABASE_PATH", str(data_dir / "anpd_monitor.sqlite3"))),
            log_level=os.getenv("ANPD_LOG_LEVEL", "INFO"),
            user_agent=os.getenv("ANPD_USER_AGENT", "anpd-monitor/0.1 (+https://example.com)"),
            timeout_seconds=float(os.getenv("ANPD_TIMEOUT_SECONDS", "30")),
            rate_limit_seconds=float(os.getenv("ANPD_RATE_LIMIT_SECONDS", "1.0")),
            max_retries=int(os.getenv("ANPD_MAX_RETRIES", "3")),
            min_pdf_bytes=int(os.getenv("ANPD_MIN_PDF_BYTES", "256")),
        )

