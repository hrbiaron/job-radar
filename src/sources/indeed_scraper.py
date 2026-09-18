"""Scraper für die öffentlichen Indeed-Suchergebnisseiten.

Indeed blockt reine requests-Anfragen mit 403 (Bot-Schutz) — läuft daher über
einen echten Headless-Browser (polite_get_rendered(), Playwright) statt
polite_get(). Selektoren wurden am 2026-09-18 gegen das echte Markup geprüft.
"""

from bs4 import BeautifulSoup

from .base import JobPosting
from .scraper_utils import polite_get_rendered

SEARCH_URL = "https://de.indeed.com/jobs"


def search_jobs(was: str, wo: str, radius_km: int = 30) -> list[JobPosting]:
    """Sucht Jobs auf Indeed und liefert sie als JobPosting-Liste zurück.

    TODO:
      - Paginierung (Parameter `start`, in 10er-Schritten)
      - Indeed zeigt Beschreibungen oft erst auf der Detailseite -> ggf.
        gezielt nur für die besten Treffer nachladen
    """
    params = {"q": was, "l": wo, "radius": radius_km}
    html = polite_get_rendered(SEARCH_URL, params=params)
    soup = BeautifulSoup(html, "lxml")

    jobs: list[JobPosting] = []
    for card in soup.select("div.job_seen_beacon"):
        title_el = card.select_one("h3.jobTitle span")
        company_el = card.select_one("span[data-testid='company-name']")
        location_el = card.select_one("div[data-testid='text-location']")
        link_el = card.select_one("h3.jobTitle a")

        if not (title_el and link_el):
            continue

        job_id = link_el.get("data-jk") or link_el.get("href", "").split("jk=")[-1][:20]
        href = link_el.get("href", "")
        jobs.append(
            JobPosting(
                id=f"indeed-{job_id}",
                source="indeed",
                title=title_el.get_text(strip=True),
                company=company_el.get_text(strip=True) if company_el else "",
                location=location_el.get_text(strip=True) if location_el else "",
                url=href if href.startswith("http") else f"https://de.indeed.com{href}",
            )
        )
    return jobs
