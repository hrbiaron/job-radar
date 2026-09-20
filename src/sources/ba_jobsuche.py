"""Client für die (inoffizielle, aber seit Jahren stabile) Jobsuche-API der
Bundesagentur für Arbeit.

Dokumentation (community-gepflegt): https://github.com/bundesAPI/jobsuche-api
Keine Anmeldung nötig — Authentifizierung läuft über einen fixen, öffentlichen
Client-Key.

Ablauf:
  1. GET .../pc/v6/jobs mit Suchparametern -> Liste mit Referenznummern
  2. optional: GET .../pc/v4/jobdetails/{base64(refnr)} für Volltext-Beschreibung
"""

import base64
from datetime import date

import requests

from .base import JobPosting

BASE_URL = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service"
HEADERS = {"X-API-Key": "jobboerse-jobsuche"}


def fetch_full_description(refnr: str) -> str:
    """Lädt die Volltext-Beschreibung eines einzelnen Treffers nach.

    Die normale Suchantwort (search_jobs()) liefert in "hauptberuf" nur eine
    kurze Berufsbezeichnung, keinen Volltext — dafür extra dieser zweite
    Request auf /pc/v4/jobdetails/{base64(refnr)} (Feld "stellenangebotsBeschreibung").
    Bewusst NICHT Teil von search_jobs(): bei hunderten Rohtreffern pro Suche
    wäre das ein Extra-Request pro Treffer. Nur gezielt für die Jobs aufrufen,
    die tatsächlich in einen Bewertungs-Batch kommen (siehe fetch_raw.py).
    """
    encoded = base64.b64encode(refnr.encode()).decode()
    try:
        response = requests.get(
            f"{BASE_URL}/pc/v4/jobdetails/{encoded}", headers=HEADERS, timeout=15
        )
        response.raise_for_status()
        return response.json().get("stellenangebotsBeschreibung", "") or ""
    except requests.RequestException as exc:
        print(f"[ba_jobsuche] WARNUNG: Volltext für '{refnr}' nicht ladbar: {exc}")
        return ""


def _parse_salary(item: dict) -> tuple[int | None, int | None]:
    """Gehaltsangabe ist meist "KEINE_ANGABEN" (keine Werte), kommt aber manchmal
    als Festgehalt (ein Wert) oder Gehaltsspanne (von/bis) — beide Formen stehen
    schon in der normalen Suchantwort, kein Extra-Request nötig."""
    art = item.get("artDerVerguetung")
    if art == "FESTGEHALT" and item.get("festgehalt") is not None:
        value = int(item["festgehalt"])
        return value, value
    if art == "GEHALTSSPANNE":
        von = item.get("gehaltsspanneVon")
        bis = item.get("gehaltsspanneBis")
        return (int(von) if von is not None else None, int(bis) if bis is not None else None)
    return None, None


def _parse_employment_type(item: dict) -> str | None:
    """Steht ebenfalls schon in der Suchantwort, kein Extra-Request nötig."""
    vollzeit = bool(item.get("arbeitszeitVollzeit"))
    teilzeit = any(
        item.get(flag)
        for flag in (
            "arbeitszeitTeilzeitAbend",
            "arbeitszeitTeilzeitNachmittag",
            "arbeitszeitTeilzeitVormittag",
            "arbeitszeitTeilzeitFlexibel",
        )
    )
    if vollzeit and teilzeit:
        return "vollzeit_oder_teilzeit"
    if vollzeit:
        return "vollzeit"
    if teilzeit:
        return "teilzeit"
    return None


def search_jobs(was: str, wo: str, umkreis_km: int = 25, size: int = 50) -> list[JobPosting]:
    """Sucht Jobs über die BA-API und liefert sie als JobPosting-Liste zurück.

    TODO:
      - Pagination beachten (Parameter `page`), falls mehr als `size` Treffer
    """
    params = {"was": was, "wo": wo, "umkreis": umkreis_km, "size": size}
    response = requests.get(f"{BASE_URL}/pc/v6/jobs", headers=HEADERS, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    jobs: list[JobPosting] = []
    for item in data.get("ergebnisliste", []):
        locations = item.get("stellenlokationen") or [{}]
        posted_raw = item.get("datumErsteVeroeffentlichung")
        try:
            posted_date = date.fromisoformat(posted_raw) if posted_raw else None
        except ValueError:
            posted_date = None
        salary_min, salary_max = _parse_salary(item)

        jobs.append(
            JobPosting(
                id=item.get("referenznummer", ""),
                source="ba_jobsuche",
                title=item.get("stellenangebotsTitel", ""),
                company=item.get("firma", ""),
                location=locations[0].get("adresse", {}).get("ort", ""),
                url=f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{item.get('referenznummer', '')}",
                description=item.get("hauptberuf", ""),  # nur Kurzform — Volltext holt fetch_raw.py gezielt per fetch_full_description() nach
                posted_date=posted_date,
                salary_min=salary_min,
                salary_max=salary_max,
                employment_type=_parse_employment_type(item),
            )
        )
    return jobs
