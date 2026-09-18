"""Client für die (inoffizielle, aber seit Jahren stabile) Jobsuche-API der
Bundesagentur für Arbeit.

Dokumentation (community-gepflegt): https://github.com/bundesAPI/jobsuche-api
Keine Anmeldung nötig — Authentifizierung läuft über einen fixen, öffentlichen
Client-Key.

Ablauf:
  1. GET .../pc/v6/jobs mit Suchparametern -> Liste mit Referenznummern
  2. optional: GET .../pc/v4/jobdetails/{base64(refnr)} für Volltext-Beschreibung
"""

import requests

from .base import JobPosting

BASE_URL = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service"
HEADERS = {"X-API-Key": "jobboerse-jobsuche"}


def search_jobs(was: str, wo: str, umkreis_km: int = 25, size: int = 50) -> list[JobPosting]:
    """Sucht Jobs über die BA-API und liefert sie als JobPosting-Liste zurück.

    TODO:
      - Pagination beachten (Parameter `page`), falls mehr als `size` Treffer
      - Antwortstruktur (`stellenangebote`) gegen aktuelle API-Antwort prüfen,
        Feldnamen können sich leicht unterscheiden -> print(response.json())
        beim ersten Testlauf zur Kontrolle
      - Details je Treffer per /pc/v4/jobdetails/{base64(refnr)} nachladen,
        falls die Beschreibung aus der Suche zu knapp ist
    """
    params = {"was": was, "wo": wo, "umkreis": umkreis_km, "size": size}
    response = requests.get(f"{BASE_URL}/pc/v6/jobs", headers=HEADERS, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    jobs: list[JobPosting] = []
    for item in data.get("stellenangebote", []):
        jobs.append(
            JobPosting(
                id=item.get("refnr", ""),
                source="ba_jobsuche",
                title=item.get("titel", ""),
                company=item.get("arbeitgeber", ""),
                location=item.get("arbeitsort", {}).get("ort", ""),
                url=f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{item.get('refnr', '')}",
                description=item.get("beruf", ""),  # TODO: durch Volltext ersetzen
            )
        )
    return jobs
