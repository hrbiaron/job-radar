"""Scraper für die öffentlichen StepStone-Suchergebnisseiten.

WICHTIG: Die CSS-Selektoren unten sind Platzhalter/beste Schätzung — StepStone
ändert sein Markup gelegentlich. Vor dem ersten produktiven Lauf: Suchseite im
Browser öffnen, "Element untersuchen" auf ein Suchergebnis, Selektoren prüfen
und hier anpassen. Läuft der Scraper leer, ist das der erste Verdacht.
"""

from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

from .base import JobPosting
from .scraper_utils import polite_get

SEARCH_URL = "https://www.stepstone.de/jobs/{was}/in-{wo}"


def fetch_description(url: str) -> str:
    """Lädt die Volltext-Beschreibung von der Detailseite eines einzelnen Jobs.

    Bewusst NICHT Teil von search_jobs() — bei hunderten Treffern pro Suche wäre
    das ein Extra-Request + Pause pro Job. Nur für die engere Auswahl (z.B. beim
    Bewerten der Top-Kandidaten) gezielt aufrufen.

    Gibt "" zurück (statt eine Exception hochzureichen), wenn die Anzeige
    zwischenzeitlich offline ist (404/410 o.ä.) oder der Abruf sonst fehlschlägt
    — soll einen ganzen Batch nicht wegen einer einzelnen toten Anzeige abbrechen."""
    try:
        response = polite_get(url)
    except requests.RequestException as exc:
        print(f"[stepstone] WARNUNG: Volltext für '{url}' nicht ladbar: {exc}")
        return ""
    soup = BeautifulSoup(response.text, "lxml")
    content = soup.select_one("div[data-at='job-ad-content']")
    return content.get_text("\n", strip=True) if content else ""


def search_jobs(was: str, wo: str) -> list[JobPosting]:
    """Sucht Jobs auf StepStone und liefert sie als JobPosting-Liste zurück.

    TODO:
      - Paginierung (StepStone nutzt i.d.R. ?page=N)
      - Selektoren gegen aktuelles Markup verifizieren
    """
    url = SEARCH_URL.format(was=was.replace(" ", "-"), wo=wo.replace(" ", "-"))
    response = polite_get(url, params={"radius": 30})
    soup = BeautifulSoup(response.text, "lxml")

    jobs: list[JobPosting] = []
    # TODO: Selektor prüfen — Platzhalter-Annahme, dass jedes Suchergebnis
    # ein <article data-at="job-item"> ist
    for card in soup.select("article[data-at='job-item']"):
        title_el = card.select_one("[data-at='job-item-title']")
        company_el = card.select_one("[data-at='job-item-company-name']")
        location_el = card.select_one("[data-at='job-item-location']")
        link_el = card.select_one("a[data-at='job-item-title']")

        if not (title_el and link_el):
            continue

        url_full = link_el.get("href", "")
        jobs.append(
            JobPosting(
                id=f"stepstone-{url_full.split('/')[-1]}",
                source="stepstone",
                title=title_el.get_text(strip=True),
                company=company_el.get_text(strip=True) if company_el else "",
                location=location_el.get_text(strip=True) if location_el else "",
                url=url_full if url_full.startswith("http") else f"https://www.stepstone.de{url_full}",
            )
        )
    return jobs
