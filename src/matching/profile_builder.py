"""Baut aus CV + Fragebogen-Antworten ein strukturiertes Kandidatenprofil,
das scorer.py als Kontext für die Claude-API nutzt.
"""

import json
from pathlib import Path

import pdfplumber
from docx import Document


def _extract_pdf_text(path: Path) -> str:
    pages = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
    text = "\n".join(pages).strip()
    if not text:
        print(f"[profile_builder] WARNUNG: kein Text-Layer in {path} gefunden "
              f"(vermutlich gescanntes PDF ohne OCR) — Profil bleibt insoweit leer.")
    return text


def _extract_docx_text(path: Path) -> str:
    document = Document(path)
    return "\n".join(p.text for p in document.paragraphs if p.text.strip())


def extract_cv_text(cv_path: str) -> str:
    """Extrahiert reinen Text aus dem Lebenslauf (PDF oder Word)."""
    path = Path(cv_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return _extract_pdf_text(path)
    if suffix in (".docx", ".doc"):
        return _extract_docx_text(path)
    raise ValueError(f"Nicht unterstütztes CV-Format: {suffix} (erwartet .pdf oder .docx)")


def load_survey(survey_path: str) -> dict:
    """Lädt die strukturierten Fragebogen-Antworten (siehe survey/fragebogen.md
    für die Fragen; erwartete JSON-Struktur z.B.:

    {
      "kernkompetenzen": [...],
      "will_nicht_mehr": [...],
      "richtungswechsel_interessen": [...],
      "gehalt_min": 55000,
      "standort_flexibilitaet": "hybrid",
      "arbeitszeit": "vollzeit",
      "werte": [...],
      "tabu_branchen": [...]
    }
    """
    return json.loads(Path(survey_path).read_text(encoding="utf-8"))


def build_profile(cv_path: str, survey_path: str) -> dict:
    """Kombiniert CV-Text + Fragebogen zu einem Profil-Dict für scorer.py."""
    return {
        "cv_text": extract_cv_text(cv_path),
        "survey": load_survey(survey_path),
    }
