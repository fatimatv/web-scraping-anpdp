# ANPD Monitor TDD Evidence

## Source Plan

Solicitud derivada del texto adjunto por el usuario: implementar un monitor semanal para tres colecciones ANPD en Gob.pe, con extraccion, deduplicacion, descarga, reportes, CLI, workflow y pruebas.

## User Journeys

- Como operador legal, quiero ejecutar `python -m anpd_monitor run`, para obtener documentos ANPD publicados en los ultimos dias.
- Como operador legal, quiero ejecutar `--dry-run`, para verificar novedades sin descargar PDFs.
- Como responsable de cumplimiento, quiero un reporte Markdown/JSON aunque no haya novedades, para conservar trazabilidad semanal.
- Como mantenedor, quiero pruebas con fixtures HTML locales, para detectar cambios de estructura sin depender siempre del portal vivo.

## Task Report

| # | What is guaranteed | Test file or command | Test type | Result | Evidence |
|---|--------------------|----------------------|-----------|--------|----------|
| 1 | Fechas oficiales en espanol se normalizan en America/Lima y el intervalo de 7 dias es verificable | `tests/test_dates.py` | Unit | PASS | `.venv\\Scripts\\python.exe -m pytest` |
| 2 | Los listados y detalles Gob.pe extraen fecha oficial, titulo, portal id, pagina siguiente y URL PDF | `tests/test_extractor.py` | Unit | PASS | `.venv\\Scripts\\python.exe -m pytest` |
| 3 | PDF se valida por firma, tamano minimo y rechazo de HTML; nombres son seguros | `tests/test_downloader.py` | Unit | PASS | `.venv\\Scripts\\python.exe -m pytest` |
| 4 | SQLite previene duplicados por URL, portal id y SHA-256 | `tests/test_repository.py` | Integration | PASS | `.venv\\Scripts\\python.exe -m pytest` |
| 5 | Runner tolera falla parcial, dry-run, revision manual, paginacion y descarga deduplicada | `tests/test_runner.py` | Integration | PASS | `.venv\\Scripts\\python.exe -m pytest` |
| 6 | CLI invoca los comandos requeridos y propaga errores de validacion | `tests/test_cli.py` | Unit | PASS | `.venv\\Scripts\\python.exe -m pytest` |
| 7 | Cliente HTTP aplica User-Agent, reintenta 429 y distingue errores HTTP | `tests/test_http_client.py` | Unit | PASS | `.venv\\Scripts\\python.exe -m pytest` |

## Validation

- `.venv\\Scripts\\python.exe -m pytest`: 25 passed, 91.86% coverage.
- `.venv\\Scripts\\python.exe -m ruff check .`: all checks passed.
- `.venv\\Scripts\\python.exe -m anpd_monitor validate-sources`: sancionadores, arco y opiniones `ok` con 25 publicaciones visibles en primera pagina.
- `.venv\\Scripts\\python.exe -m anpd_monitor run --dry-run --days 7`: genero `data\\reports\\anpd_report_20260718_171415.md` y `.json`, sin descargar PDFs.

## Known Gaps

- La alerta historica de "cero publicaciones cuando antes habia resultados" queda preparada por trazabilidad de conteo en reportes, pero no tiene una tabla dedicada de historial de fuentes todavia.
- El workflow de GitHub Actions incluye un cron documentado en UTC; cambiar el horario requiere editar el workflow o gestionar una plantilla externa, porque GitHub Actions no permite parametrizar dinamicamente `schedule.cron` con variables.
