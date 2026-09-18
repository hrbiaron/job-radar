"""Orchestriert den kompletten Ablauf für alle Personen aus config/people.yaml.

Aufruf:
    python src/main.py            # live, verschickt Mails
    python src/main.py --dry-run  # zeigt nur, was verschickt würde
"""

import argparse

import yaml
from dotenv import load_dotenv

from .dedup import already_sent, mark_sent
from .emailer import send_digest
from .enrich.kununu_scraper import get_company_info
from .matching.profile_builder import build_profile
from .matching.scorer import score_job
from .sources import adzuna, ba_jobsuche, indeed_scraper, stepstone_scraper
from .static_site import update_static_site

load_dotenv()


def collect_jobs(search_cfg: dict) -> list:
    """Fragt alle Quellen ab und gibt eine gemeinsame Liste zurück.

    TODO: Fehler einer einzelnen Quelle (z.B. Scraper down) dürfen die
    anderen Quellen nicht blockieren -> pro Quelle try/except mit Logging.
    """
    jobs = []
    jobs += ba_jobsuche.search_jobs(search_cfg["was"], search_cfg["wo"], search_cfg["umkreis_km"])
    jobs += adzuna.search_jobs(search_cfg["was"], search_cfg["wo"])
    jobs += stepstone_scraper.search_jobs(search_cfg["was"], search_cfg["wo"])
    jobs += indeed_scraper.search_jobs(search_cfg["was"], search_cfg["wo"])
    return jobs


def process_person(person_cfg: dict, dry_run: bool) -> None:
    name = person_cfg["name"]
    profile = build_profile(person_cfg["cv_path"], person_cfg["survey_path"])

    candidates = collect_jobs(person_cfg["search"])
    new_candidates = [j for j in candidates if not already_sent(name, j.id, j.source)]

    threshold = person_cfg["min_score"]
    maybe_zone = person_cfg.get("include_maybe_zone", False)
    lower_bound = 50 if maybe_zone else threshold

    to_send = []
    for job in new_candidates:
        result = score_job(profile, job.title, job.company, job.description)
        job.match_score = result["score"]
        job.match_reason = result["reason"]
        job.direction_change_fit = result["direction_change_fit"]

        if job.match_score >= lower_bound:
            info = get_company_info(job.company)
            job.company_rating = info["rating"]
            job.company_recommend_pct = info["recommend_pct"]
            job.company_review_count = info["review_count"]
            job.company_summary = info["summary"]
            to_send.append(job)

    if dry_run:
        print(f"[{name}] {len(to_send)} Jobs würden verschickt:")
        for job in to_send:
            print(f"  - {job.title} @ {job.company} (Score {job.match_score})")
        return

    send_digest(person_cfg["email"], name, to_send)
    update_static_site(
        name,
        to_send,
        sync_api_url=person_cfg.get("sheets_sync_url"),
        sync_api_token=person_cfg.get("sheets_sync_token"),
    )
    for job in to_send:
        mark_sent(name, job.id, job.source)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with open("config/people.yaml") as f:
        people = yaml.safe_load(f)

    for person_cfg in people:
        process_person(person_cfg, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
