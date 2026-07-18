from __future__ import annotations

import argparse

from .config import COLLECTIONS, Settings
from .logging_config import configure_logging
from .runner import run_monitor, validate_sources


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m anpd_monitor")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run", help="Ejecuta el monitoreo ANPD")
    run.add_argument("--dry-run", action="store_true", help="No descarga archivos PDF")
    run.add_argument("--days", type=int, default=7, help="Dias calendario hacia atras")
    run.add_argument("--category", choices=sorted(COLLECTIONS), help="Fuente especifica")
    subparsers.add_parser("validate-sources", help="Valida que las fuentes sean extraibles")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = Settings.from_env()
    configure_logging(settings.data_dir, settings.log_level)
    if args.command == "run":
        md_path, json_path = run_monitor(
            settings, days=args.days, category=args.category, dry_run=args.dry_run
        )
        print(f"Reporte Markdown: {md_path}")
        print(f"Reporte JSON: {json_path}")
        return 0
    if args.command == "validate-sources":
        failed = False
        for result in validate_sources(settings):
            print(f"{result.source.key}: {result.status} ({result.candidates_seen} publicaciones)")
            if result.errors:
                failed = True
                for error in result.errors:
                    print(f"  - {error}")
        return 1 if failed else 0
    return 1

