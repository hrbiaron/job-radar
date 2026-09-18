"""Gemeinsame Abfrage aller Job-Quellen mit robuster Fehlerbehandlung:
Fällt eine Quelle aus (z.B. ein Scraper wird geblockt), dürfen die anderen
trotzdem Ergebnisse liefern.
"""

from . import adzuna, ba_jobsuche, indeed_scraper, stepstone_scraper
from .base import JobPosting

_SOURCES = {
    "ba_jobsuche": lambda was, wo, umkreis_km: ba_jobsuche.search_jobs(was, wo, umkreis_km),
    "adzuna": lambda was, wo, umkreis_km: adzuna.search_jobs(was, wo),
    "stepstone": lambda was, wo, umkreis_km: stepstone_scraper.search_jobs(was, wo),
    "indeed": lambda was, wo, umkreis_km: indeed_scraper.search_jobs(was, wo),
}


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
    """Fragt alle Quellen für alle konfigurierten Suchbegriffe ab und dedupliziert
    über (source, id). search_cfg["was"] darf ein einzelner String oder eine
    Liste von Suchbegriffen sein (die APIs unterstützen kein Boolean-OR in
    einem einzigen Request, daher mehrere Anfragen statt einer)."""
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
    return jobs
