"""Deterministischer Teil OHNE LLM-Kosten: holt neue Jobs, filtert bereits
verschickte raus, legt sie zur Bewertung durch Claude Code bereit.

Wird von der Skill .claude/skills/job-radar-update/SKILL.md aufgerufen —
das ist die kostenlose Variante B (siehe README, "Zwei Varianten").
main.py bleibt Variante A mit eigenem Anthropic-API-Key.
"""

import json
from pathlib import Path

import yaml
from dotenv import load_dotenv

from .backlog import DEFAULT_BATCH_SIZE, load_backlog, take_batch
from .dedup import already_sent
from .matching.profile_builder import build_profile
from .sources import collect_jobs
from .sources import ba_jobsuche, stepstone_scraper

load_dotenv()

PENDING_DIR = Path("data/pending_scores")

# Ab dieser Zeichenlänge gilt eine Beschreibung als "zu knapp" und wird per
# Volltext-Nachladung ergänzt (siehe enrich_descriptions()).
MIN_DESCRIPTION_LENGTH = 200


def enrich_descriptions(batch: list[dict]) -> None:
    """Lädt für Jobs mit zu knapper Beschreibung den Volltext nach — nur für
    den tatsächlichen Bewertungs-Batch (nicht für alle Rohtreffer), sonst
    würden hunderte Extra-Requests pro Lauf anfallen.

    - ba_jobsuche liefert in der Suchantwort nur eine kurze Berufsbezeichnung
      ("hauptberuf") statt Volltext, daher hier per Zweit-Request nachgeladen.
    - stepstone liefert in der Suchantwort gar keine Beschreibung; die
      Volltext-Funktion existierte bereits (fetch_description()), wurde aber
      bisher nirgends aufgerufen.
    - indeed bewusst ausgelassen: ein Testabruf der Detailseite wurde sofort
      von Indeads Bot-Schutz geblockt ("Security Check"). Ein Fix dafür würde
      mehr Aufwand (Session-Warmup, ggf. Proxies) brauchen als für dieses
      Projekt sinnvoll ist — Beschreibung bleibt dort leer, Link zur Original-
      anzeige reicht als Fallback.
    """
    for job in batch:
        description = job.get("description") or ""
        if len(description) >= MIN_DESCRIPTION_LENGTH:
            continue
        if job["source"] == "ba_jobsuche":
            full_text = ba_jobsuche.fetch_full_description(job["id"])
        elif job["source"] == "stepstone":
            full_text = stepstone_scraper.fetch_description(job["url"])
        else:
            continue
        if full_text:
            job["description"] = full_text


def main() -> None:
    with open("config/people.yaml", encoding="utf-8") as f:
        people = yaml.safe_load(f)

    PENDING_DIR.mkdir(parents=True, exist_ok=True)

    for person_cfg in people:
        name = person_cfg["name"]
        profile = build_profile(person_cfg["cv_path"], person_cfg["survey_path"])
        batch_size = person_cfg.get("batch_size", DEFAULT_BATCH_SIZE)

        candidates = collect_jobs(person_cfg["search"])
        new_candidates = [j for j in candidates if not already_sent(name, j.id, j.source)]
        new_candidate_dicts = [
            {
                "id": j.id,
                "source": j.source,
                "title": j.title,
                "company": j.company,
                "location": j.location,
                "url": j.url,
                "description": j.description,
                "salary_min": j.salary_min,
                "salary_max": j.salary_max,
                "employment_type": j.employment_type,
                "posted_date": j.posted_date.isoformat() if j.posted_date else None,
            }
            for j in new_candidates
        ]

        # Backlog-Warteschlange: neue Treffer hinten anfügen, nur einen Batch
        # zur Bewertung entnehmen — bei einer großen Rohsuche (z.B. 1200
        # Treffer) wird so nicht alles auf einmal bewertet, sondern über
        # mehrere Läufe abgearbeitet (siehe src/backlog.py).
        batch = take_batch(name, new_candidate_dicts, batch_size)
        enrich_descriptions(batch)
        remaining_in_backlog = len(load_backlog(name))

        payload = {"person": name, "profile": profile, "jobs": batch}
        out_path = PENDING_DIR / f"{name}.json"
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(
            f"[{name}] {len(new_candidate_dicts)} neue Treffer gefunden, "
            f"{len(batch)} davon in diesem Lauf zur Bewertung bereit "
            f"({remaining_in_backlog} bleiben im Backlog für die nächsten Läufe)."
        )


if __name__ == "__main__":
    main()
