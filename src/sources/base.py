"""Gemeinsames Datenmodell für alle Job-Quellen (APIs + Scraper).

Jede Quelle (ba_jobsuche.py, adzuna.py, stepstone_scraper.py, indeed_scraper.py)
soll ihre Ergebnisse in dieses Format überführen, damit Matching, Dedup und
Mail-Versand quellenunabhängig funktionieren.
"""

from dataclasses import dataclass, field
from datetime import date


@dataclass
class JobPosting:
    # eindeutige ID zur Dedup — bei APIs meist die Referenznummer/Job-ID der
    # Quelle, bei Scrapern z.B. ein Hash aus (source, url) bilden
    id: str
    source: str                 # "ba_jobsuche" | "adzuna" | "stepstone" | "indeed"
    title: str
    company: str
    location: str
    url: str
    description: str = ""
    posted_date: date | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    # "vollzeit" | "teilzeit" | "vollzeit_oder_teilzeit" | None (Quelle macht keine Angabe)
    employment_type: str | None = None

    # wird erst im Matching-Schritt befüllt
    match_score: int | None = None
    match_reason: str | None = None
    direction_change_fit: bool | None = None
    # kurze Beschreibung der Berufserfahrung, die die Anzeige verlangt, die die
    # Person laut Fragebogen/CV NICHT hat, aber der Job trotzdem empfohlen wird
    # (z.B. weil eine Parallele zu anderer Erfahrung besteht) — None, wenn kein
    # relevanter Erfahrungs-Gap vorliegt. Wird explizit auf der Seite angezeigt,
    # damit die Empfehlung trotz fehlender Erfahrung nachvollziehbar bleibt.
    experience_gap: str | None = None
    # Freitext-Kategorie zum Filtern auf der GitHub-Pages-Seite, z.B. "Controlling",
    # "HR", "SAP/IT-Consulting", "Kundenbetreuung" — kein festes Set, die Seite
    # baut das Filter-Dropdown aus den tatsächlich vorkommenden Werten.
    category: str | None = None

    # wird erst im Enrichment-Schritt (Kununu) befüllt
    company_rating: float | None = None
    company_recommend_pct: float | None = None
    company_review_count: int | None = None
    company_summary: str | None = None
