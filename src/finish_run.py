"""Zweiter deterministischer Teil OHNE LLM-Kosten: nimmt die von Claude Code
bereits bewerteten Jobs (data/scored/<Name>.json), filtert nach
Schwellenwert, reichert mit Kununu an, aktualisiert die GitHub-Pages-Seite,
verschickt die Mail und trägt sie in die Dedup-Liste ein.

Erwartetes Format von data/scored/<Name>.json: Liste von Job-Objekten
(id, source, title, company, location, url, description) jeweils ergänzt
um score (int), reason (str), direction_change_fit (bool) — das hat
Claude Code beim Ausführen der Skill selbst hinzugefügt.
"""

import json
from pathlib import Path

import yaml
from dotenv import load_dotenv

from .dedup import mark_sent
from .emailer import send_digest
from .enrich.kununu_scraper import get_company_info
from .sources.base import JobPosting
from .static_site import update_static_site

load_dotenv()

SCORED_DIR = Path("data/scored")


def load_scored(person: str) -> list[JobPosting]:
    raw = json.loads((SCORED_DIR / f"{person}.json").read_text(encoding="utf-8"))
    jobs = []
    for item in raw:
        jobs.append(
            JobPosting(
                id=item["id"],
                source=item["source"],
                title=item["title"],
                company=item["company"],
                location=item["location"],
                url=item["url"],
                description=item.get("description", ""),
                match_score=item["score"],
                match_reason=item["reason"],
                direction_change_fit=item.get("direction_change_fit", False),
            )
        )
    return jobs


def process_person(person_cfg: dict) -> None:
    name = person_cfg["name"]
    scored_path = SCORED_DIR / f"{name}.json"
    if not scored_path.exists():
        print(f"[{name}] keine bewerteten Jobs gefunden, überspringe.")
        return

    jobs = load_scored(name)
    threshold = person_cfg["min_score"]
    maybe_zone = person_cfg.get("include_maybe_zone", False)
    lower_bound = 50 if maybe_zone else threshold

    to_send = [j for j in jobs if (j.match_score or 0) >= lower_bound]

    for job in to_send:
        info = get_company_info(job.company)
        job.company_rating = info["rating"]
        job.company_recommend_pct = info["recommend_pct"]
        job.company_review_count = info["review_count"]
        job.company_summary = info["summary"]

    send_digest(person_cfg["email"], name, to_send)
    update_static_site(
        name,
        to_send,
        sync_api_url=person_cfg.get("sheets_sync_url"),
        sync_api_token=person_cfg.get("sheets_sync_token"),
    )
    for job in to_send:
        mark_sent(name, job.id, job.source)

    print(f"[{name}] {len(to_send)} Jobs verschickt und in docs/jobs.json übernommen.")


def main() -> None:
    with open("config/people.yaml", encoding="utf-8") as f:
        people = yaml.safe_load(f)
    for person_cfg in people:
        process_person(person_cfg)


if __name__ == "__main__":
    main()
