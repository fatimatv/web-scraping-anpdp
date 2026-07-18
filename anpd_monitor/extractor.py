from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from .classifier import extract_document_number
from .dates import parse_spanish_publication_date
from .models import CollectionConfig, DocumentCandidate

BASE_URL = "https://www.gob.pe"


class ExtractionError(RuntimeError):
    pass


def extract_collection(html: str, source: CollectionConfig) -> list[DocumentCandidate]:
    soup = BeautifulSoup(html, "html.parser")
    container = soup.select_one(".js-official-documents-search-results") or soup
    cards = container.select(".shadow-campaign-card")
    candidates: list[DocumentCandidate] = []
    for card in cards:
        link = card.select_one("a[href*='/institucion/anpd/']")
        if not link:
            continue
        date_node = card.select_one(".border-b.font-medium, .border-b")
        publication_date = parse_spanish_publication_date(date_node.get_text(" ", strip=True)) if date_node else None
        title = link.get_text(" ", strip=True)
        publication_url = urljoin(BASE_URL, str(link.get("href")))
        portal_id = extract_portal_id(publication_url)
        summary = card.get_text(" ", strip=True).replace(title, "", 1)
        candidates.append(
            DocumentCandidate(
                category=source.category,
                title=title,
                publication_url=publication_url,
                portal_id=portal_id,
                publication_date=publication_date,
                summary=summary,
                number=extract_document_number(title, summary),
            )
        )
    if "resultados" in soup.get_text(" ", strip=True).lower() and not candidates:
        raise ExtractionError("La pagina reporta resultados, pero no se extrajeron tarjetas.")
    return candidates


def extract_next_page_url(html: str, current_url: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    link = soup.select_one("a[rel='next'][href], .next a[href]")
    if not link:
        return None
    return urljoin(current_url, str(link["href"]))


def extract_detail(html: str, candidate: DocumentCandidate) -> DocumentCandidate:
    soup = BeautifulSoup(html, "html.parser")
    header = soup.select_one(".institution-document__header")
    if header:
        title_node = header.select_one("h2")
        if title_node:
            candidate.title = title_node.get_text(" ", strip=True)
        paragraphs = [p.get_text(" ", strip=True) for p in header.select("p")]
        for value in paragraphs:
            parsed = parse_spanish_publication_date(value)
            if parsed:
                candidate.publication_date = parsed
                break
    body_text = soup.select_one(".rule-content")
    summary = body_text.get_text(" ", strip=True) if body_text else soup.get_text(" ", strip=True)
    candidate.summary = summary
    candidate.number = extract_document_number(candidate.title, summary) or candidate.number
    file_link = soup.select_one("a.download[href*='.pdf'], a[href*='.pdf']")
    if file_link and file_link.get("href"):
        candidate.file_url = urljoin(BASE_URL, str(file_link["href"]))
    return candidate


def extract_portal_id(url: str) -> str | None:
    path = urlparse(url).path
    match = re.search(r"/(?:normas-legales|informes-publicaciones)/(\d+)-", path)
    if match:
        return match.group(1)
    match = re.search(r"/(\d+)-", path)
    return match.group(1) if match else None
