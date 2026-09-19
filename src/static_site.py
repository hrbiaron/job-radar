"""Schreibt pro Person eine eigene, getrennte GitHub-Pages-Unterseite
(docs/<slug>/index.html + docs/<slug>/jobs.json) — jede Person bekommt einen
eigenen Link, sieht nur ihre eigenen Jobs, keine gemeinsame Auswahlseite.
"""

import json
import re
import unicodedata
from pathlib import Path

from jinja2 import Template

from .enrich.kununu_scraper import kununu_search_url
from .sources.base import JobPosting

DOCS_DIR = Path("docs")
PAGE_TEMPLATE_PATH = Path("templates/docs_person_page.html")


def slugify(person_name: str) -> str:
    """Wandelt einen Personennamen in einen URL-sicheren Ordnernamen um
    (z.B. "Frau Müller" -> "frau-mueller"). Muss stabil sein, damit der
    Link einer Person sich nicht bei jedem Lauf ändert."""
    normalized = unicodedata.normalize("NFKD", person_name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_name).strip("-").lower()
    return slug or "person"


def person_page_url(base_pages_url: str, person_name: str) -> str:
    base = base_pages_url if base_pages_url.endswith("/") else base_pages_url + "/"
    return f"{base}{slugify(person_name)}/"


def update_static_site(
    person_name: str,
    jobs: list[JobPosting],
    sync_api_url: str | None = None,
    sync_api_token: str | None = None,
) -> None:
    """Fügt neue Jobs zur bestehenden Liste dieser Person hinzu (kein
    Duplikat nach id) und schreibt/aktualisiert die zugehörige Unterseite.

    sync_api_url/sync_api_token: optionale, PRO PERSON eigene Google-Apps-Script-
    Bereitstellung für die geräteübergreifende Synchronisation (siehe
    sheets-backend/SETUP.md). Ohne diese Werte bleiben Markierungen nur im
    Browser der Person (localStorage).

    TODO: alte Einträge irgendwann aufräumen (z.B. > 90 Tage), damit die
    Seite nicht unbegrenzt wächst — sent_jobs.db (dedup.py) hat den
    vollständigen Verlauf, docs/<slug>/jobs.json muss den nicht für immer behalten.
    """
    person_dir = DOCS_DIR / slugify(person_name)
    person_dir.mkdir(parents=True, exist_ok=True)

    jobs_path = person_dir / "jobs.json"
    existing = json.loads(jobs_path.read_text(encoding="utf-8")) if jobs_path.exists() else []
    existing_ids = {j["id"] for j in existing}

    for job in jobs:
        if job.id in existing_ids:
            continue
        existing.append(
            {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "url": job.url,
                "score": job.match_score,
                "reason": job.match_reason,
                "kununu_rating": job.company_rating,
                "kununu_recommend_pct": job.company_recommend_pct,
                "kununu_review_count": job.company_review_count,
                "kununu_url": kununu_search_url(job.company),
                "description": job.description or None,
                "salary_min": job.salary_min,
                "salary_max": job.salary_max,
                "posted_date": job.posted_date.isoformat() if job.posted_date else None,
                "source": job.source,
                "direction_change_fit": job.direction_change_fit,
            }
        )

    jobs_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")

    template = Template(PAGE_TEMPLATE_PATH.read_text(encoding="utf-8"))
    html = template.render(
        person_name=person_name, sync_api_url=sync_api_url, sync_api_token=sync_api_token
    )
    (person_dir / "index.html").write_text(html, encoding="utf-8")
