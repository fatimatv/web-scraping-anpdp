from __future__ import annotations

import logging
from pathlib import Path


def configure_logging(data_dir: Path, level: str) -> None:
    log_dir = data_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_dir / "anpd_monitor.log", encoding="utf-8"),
        ],
    )

