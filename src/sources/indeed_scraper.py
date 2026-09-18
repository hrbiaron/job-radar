"""Scraper für die öffentlichen Indeed-Suchergebnisseiten.

Gleicher Hinweis wie bei stepstone_scraper.py: Selektoren sind Platzhalter,
vor Produktivbetrieb gegen das aktuelle Markup prüfen. Indeed reagiert unter
Umständen empfindlicher auf hohe Frequenz als StepStone — polite_get()
(scraper_utils.py) unbedingt beibehalten, Frequenz eher senken als erhöhen.
"""

from bs4 import BeautifulSoup

from .base import JobPosting
from .scraper_utils import polite_get

SEARCH_URL = "https://de.indeed.com/jobs"


def search_jobs(was: str, wo: str, radius_km: int = 30) -> list[JobPosting]:
    """Sucht Jobs auf Indeed und liefert sie als JobPosting-Liste zurück.

    TODO:
      - Paginierung (Parameter `start`, in 10er-Schritten)
      - Selektoren gegen aktuelles Markup verifizieren
      - Indeed zeigt Beschreibungen oft erst auf der Detailseite -> ggf.
        gezielt nur für die besten Treffer nachladen
    """
    params = {"q": was, "l": wo, "radius": radius_km}
    response = polite_get(SEARCH_URL, params=params)
    soup = BeautifulSoup(response.text, "lxml")

    jobs: list[JobPosting] = []
    # TODO: Selektor prüfen — Platzhalter-Annahme
    for card in soup.select("div.job_seen_beacon"):
        title_el = card.select_one("h2.jobTitle span")
        company_el = card.select_one("span[data-testid='company-name']")
        location_el = card.select_one("div[data-testid='text-location']")
        link_el = card.select_one("h2.jobTitle a")

        if not (title_el and link_el):
            continue

        href = link_el.get("href", "")
        jobs.append(
            JobPosting(
                id=f"indeed-{href.split('jk=')[-1][:20]}",
                source="indeed",
                title=title_el.get_text(strip=True),
                company=company_el.get_text(strip=True) if company_el else "",
                location=location_el.get_text(strip=True) if location_el else "",
                url=href if href.startswith("http") else f"https://de.indeed.com{href}",
            )
        )
    return jobs
