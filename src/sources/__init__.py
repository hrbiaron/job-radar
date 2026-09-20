"""Gemeinsame Abfrage aller Job-Quellen mit robuster Fehlerbehandlung:
Fällt eine Quelle aus (z.B. ein Scraper wird geblockt), dürfen die anderen
trotzdem Ergebnisse liefern.
"""

import re

from . import adzuna, ba_jobsuche, indeed_scraper, stepstone_scraper
from .base import JobPosting

_SOURCES = {
    "ba_jobsuche": lambda was, wo, umkreis_km: ba_jobsuche.search_jobs(was, wo, umkreis_km),
    "adzuna": lambda was, wo, umkreis_km: adzuna.search_jobs(was, wo),
    "stepstone": lambda was, wo, umkreis_km: stepstone_scraper.search_jobs(was, wo),
    "indeed": lambda was, wo, umkreis_km: indeed_scraper.search_jobs(was, wo),
}

# Gleiche Stelle wird oft von der Firma parallel auf mehreren Portalen inseriert
# (z.B. direkt bei der Arbeitsagentur UND auf Indeed) — jede Quelle vergibt dafür
# eine eigene ID, daher greift die (source, id)-Dedup weiter unten nicht. Hier
# zusätzlich über normalisierte (Firma, Titel) dedupen und die Version mit den
# reichhaltigeren Daten behalten (APIs liefern i.d.R. Gehalt/Beschreibung,
# Scraper oft nicht) — daher diese Prioritätsreihenfolge.
_SOURCE_PRIORITY = {"ba_jobsuche": 0, "adzuna": 1, "stepstone": 2, "indeed": 3}

_GENDER_MARKER_RE = re.compile(r"\(?\s*[mwdfx]\s*/\s*[mwdfx]\s*(?:/\s*[mwdfx]\s*)?\)?", re.IGNORECASE)
_LEGAL_SUFFIX_RE = re.compile(
    r"\b(gmbh|co\s*kg|kg|ohg|mbh|ag|se|holding|gruppe|group)\b",
    re.IGNORECASE,
)
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def _normalize(text: str) -> str:
    text = text.lower()
    text = _GENDER_MARKER_RE.sub(" ", text)
    text = _LEGAL_SUFFIX_RE.sub(" ", text)
    text = _NON_ALNUM_RE.sub(" ", text)
    return " ".join(text.split())


def _cross_source_key(job: JobPosting) -> tuple[str, str]:
    return (_normalize(job.company), _normalize(job.title))


def _dedup_cross_source(jobs: list[JobPosting]) -> list[JobPosting]:
    best: dict[tuple[str, str], JobPosting] = {}
    for job in jobs:
        key = _cross_source_key(job)
        current = best.get(key)
        if current is None:
            best[key] = job
            continue
        if _SOURCE_PRIORITY.get(job.source, 99) < _SOURCE_PRIORITY.get(current.source, 99):
            print(
                f"[sources] Cross-Source-Duplikat: '{job.title}' bei '{job.company}' "
                f"kommt sowohl von '{current.source}' als auch von '{job.source}' — "
                f"behalte '{job.source}' (bessere Datenqualität)."
            )
            best[key] = job
        else:
            print(
                f"[sources] Cross-Source-Duplikat: '{job.title}' bei '{job.company}' "
                f"kommt sowohl von '{current.source}' als auch von '{job.source}' — "
                f"behalte '{current.source}'."
            )
    return list(best.values())


def search_all(was: str, wo: str, umkreis_km: int) -> list[JobPosting]:
    """Fragt alle Quellen für einen Suchbegriff ab. Eine fehlschlagende Quelle
    wird geloggt und übersprungen, blockiert aber nicht die anderen."""
    jobs: list[JobPosting] = []
    for name, fn in _SOURCES.items():
        try:
            jobs += fn(was, wo, umkreis_km)
        except Exception as exc:  # noqa: BLE001 — bewusst breit, einzelne Quelle darf nie den Lauf killen
            print(f"[sources] WARNUNG: Quelle '{name}' fehlgeschlagen für was={was!r}: {exc}")
    return jobs


def collect_jobs(search_cfg: dict) -> list[JobPosting]:
    """Fragt alle Quellen für alle konfigurierten Suchbegriffe ab, dedupliziert
    zunächst über (source, id) und danach quellenübergreifend über normalisierte
    (Firma, Titel) — dieselbe Stelle taucht sonst mehrfach auf, wenn sie parallel
    auf mehreren Portalen inseriert wurde (siehe _dedup_cross_source oben).
    search_cfg["was"] darf ein einzelner String oder eine Liste von Suchbegriffen
    sein (die APIs unterstützen kein Boolean-OR in einem einzigen Request, daher
    mehrere Anfragen statt einer)."""
    was_terms = search_cfg["was"]
    if isinstance(was_terms, str):
        was_terms = [was_terms]
    wo = search_cfg["wo"]
    umkreis_km = search_cfg["umkreis_km"]

    jobs: list[JobPosting] = []
    seen: set[tuple[str, str]] = set()
    for was in was_terms:
        for job in search_all(was, wo, umkreis_km):
            key = (job.source, job.id)
            if key in seen:
                continue
            seen.add(key)
            jobs.append(job)
    return _dedup_cross_source(jobs)
