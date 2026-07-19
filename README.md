# ANPD Monitor

Aplicacion Python para revisar semanalmente las colecciones oficiales de la Autoridad Nacional de Proteccion de Datos Personales del Peru en Gob.pe, detectar publicaciones de los ultimos dias, descargar PDFs publicos y generar reportes Markdown/JSON.

## Instalacion

```bash
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
copy .env.example .env
```

## Uso

```bash
python -m anpd_monitor run
python -m anpd_monitor run --dry-run
python -m anpd_monitor run --days 7
python -m anpd_monitor run --category sancionadores
python -m anpd_monitor validate-sources
```

## Plataforma interactiva para abogados

El manual interactivo esta en `docs/platform/index.html` y desplegado en Vercel. Explica, paso a paso y para abogados no ingenieros, como pedirle a la IA un scraper juridico, que herramientas instalar, que hace tecnicamente el sistema y que controles legales aplicar al monitorear jurisprudencia o documentos oficiales de cualquier entidad publica.

La zona horaria operacional es `America/Lima`. El criterio temporal usa la fecha oficial de publicacion mostrada por Gob.pe, no la fecha de emision del documento ni la fecha tecnica del PDF.

## Fuentes

- Procedimientos sancionadores: https://www.gob.pe/institucion/anpd/colecciones/1801-resoluciones-de-los-procedimientos-sancionadores
- Derechos ARCO: https://www.gob.pe/institucion/anpd/colecciones/1749-decisiones-sobre-derechos-arco-2017
- Opiniones consultivas: https://www.gob.pe/institucion/anpd/colecciones/1799-opiniones-consultivas-emitidas-por-la-anpd

## Salidas

Los documentos se guardan bajo:

```text
data/
  procedimientos_sancionadores/YYYY/MM/
  derechos_arco/YYYY/MM/
  opiniones_consultivas/YYYY/MM/
  reports/
  logs/
```

Siempre se genera reporte Markdown y JSON, incluso cuando no hay novedades.

## Automatizacion

El workflow de GitHub Actions usa `ANPD_WEEKLY_CRON_UTC` como referencia documentada. Los cron de GitHub Actions se expresan en UTC; ajuste el horario segun la ventana deseada en Lima.

## Scraping responsable

La aplicacion usa un `User-Agent` identificable, timeouts, pausas, reintentos con backoff y no evade CAPTCHA, autenticacion ni controles de seguridad. Solo descarga documentos publicamente accesibles enlazados desde Gob.pe.
