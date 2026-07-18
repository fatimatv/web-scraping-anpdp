from __future__ import annotations

import re

from .models import Category


def classify_from_source_key(source_key: str) -> Category:
    mapping = {
        "sancionadores": Category.SANCIONADORES,
        "arco": Category.ARCO,
        "opiniones": Category.OPINIONES,
    }
    return mapping[source_key]


def extract_document_number(title: str, summary: str = "") -> str | None:
    text = f"{title} {summary}"
    patterns = [
        r"(OC\s*N[.°º]?\s*\d{1,3}-\d{4}[-/A-Z]*)",
        r"(Resoluci[oó]n\s+Directoral\s*N[.°º]?\s*[\d-]+[-/A-Z]*)",
        r"(EXP[-.\s]*\d{1,4}-\d{4}/?[A-Z]*)",
        r"(EXP\.\s*\d{1,4}-\d{4})",
        r"(PAS[:\s].*?\(EXP\.\s*\d{1,4}-\d{4}\))",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return " ".join(match.group(1).split()).strip(" .")
    return None

