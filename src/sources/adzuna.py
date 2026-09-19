"""Client für die offizielle Adzuna-API (Deutschland).

Anmeldung (kostenlos): https://developer.adzuna.com/signup
Freikontingent: 25 Anfragen/Minute, 250/Tag — für einen täglichen Lauf über
zwei Personen locker ausreichend.
"""

import os
from datetime import datetime

import requests

from .base import JobPosting

BASE_URL = "https://api.adzuna.com/v1/api/jobs/de/search"


def search_jobs(was: str, wo: str, page: int = 1, results_per_page: int = 50) -> list[JobPosting]:
    """Sucht Jobs über Adzuna und liefert sie als JobPosting-Liste zurück.

    TODO:
      - Mehrseitige Ergebnisse abholen (page erhöhen), falls nötig
      - Salary-Felder (salary_min/salary_max) sind bei Adzuna oft leer —
        entsprechend defensiv behandeln
    """
    app_id = os.environ["ADZUNA_APP_ID"]
    app_key = os.environ["ADZUNA_APP_KEY"]

    params = {
        "app_id": app_id,
        "app_key": app_key,
        "what": was,
        "where": wo,
        "results_per_page": results_per_page,
        "content-type": "application/json",
    }
    response = requests.get(f"{BASE_URL}/{page}", params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    jobs: list[JobPosting] = []
    for item in data.get("results", []):
        created_raw = item.get("created")
        try:
            posted_date = datetime.fromisoformat(created_raw.replace("Z", "+00:00")).date() if created_raw else None
        except ValueError:
            posted_date = None

        jobs.append(
            JobPosting(
                id=str(item.get("id", "")),
                source="adzuna",
                title=item.get("title", ""),
                company=item.get("company", {}).get("display_name", ""),
                location=item.get("location", {}).get("display_name", ""),
                url=item.get("redirect_url", ""),
                description=item.get("description", ""),
                salary_min=item.get("salary_min"),
                salary_max=item.get("salary_max"),
                posted_date=posted_date,
            )
        )
    return jobs
