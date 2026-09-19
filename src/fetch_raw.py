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

from .dedup import already_sent
from .matching.profile_builder import build_profile
from .sources import collect_jobs

load_dotenv()

PENDING_DIR = Path("data/pending_scores")


def main() -> None:
    with open("config/people.yaml", encoding="utf-8") as f:
        people = yaml.safe_load(f)

    PENDING_DIR.mkdir(parents=True, exist_ok=True)

    for person_cfg in people:
        name = person_cfg["name"]
        profile = build_profile(person_cfg["cv_path"], person_cfg["survey_path"])

        candidates = collect_jobs(person_cfg["search"])
        new_candidates = [j for j in candidates if not already_sent(name, j.id, j.source)]

        payload = {
            "person": name,
            "profile": profile,
            "jobs": [
                {
                    "id": j.id,
                    "source": j.source,
                    "title": j.title,
                    "company": j.company,
                    "location": j.location,
                    "url": j.url,
                    "description": j.description,
                }
                for j in new_candidates
            ],
        }
        out_path = PENDING_DIR / f"{name}.json"
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[{name}] {len(new_candidates)} neue Jobs bereit zur Bewertung in {out_path}")


if __name__ == "__main__":
    main()
