"""Persistente Warteschlange pro Person: Bei viel mehr neuen Treffern als pro
Lauf bewertet werden können (z.B. 1200 auf einmal), werden sie hier
zwischengespeichert. Jeder Lauf verarbeitet nur einen Batch (siehe
DEFAULT_BATCH_SIZE) und hängt gleichzeitig neu gefundene Jobs hinten an —
die Liste wird so mit der Zeit abgearbeitet, statt alles auf einmal bewerten
zu müssen.
"""

import json
from pathlib import Path

BACKLOG_DIR = Path("data/backlog")
DEFAULT_BATCH_SIZE = 200


def _path(person: str) -> Path:
    return BACKLOG_DIR / f"{person}.json"


def load_backlog(person: str) -> list[dict]:
    path = _path(person)
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def save_backlog(person: str, jobs: list[dict]) -> None:
    BACKLOG_DIR.mkdir(parents=True, exist_ok=True)
    _path(person).write_text(json.dumps(jobs, ensure_ascii=False, indent=2), encoding="utf-8")


def enqueue_new(person: str, candidate_dicts: list[dict]) -> list[dict]:
    """Fügt neue Jobs (die noch nicht im Backlog stehen) hinten an und gibt
    den aktualisierten, vollständigen Backlog zurück (noch nicht gespeichert)."""
    existing = load_backlog(person)
    existing_keys = {(j["source"], j["id"]) for j in existing}
    for job in candidate_dicts:
        key = (job["source"], job["id"])
        if key not in existing_keys:
            existing.append(job)
            existing_keys.add(key)
    return existing


def take_batch(person: str, candidate_dicts: list[dict], batch_size: int = DEFAULT_BATCH_SIZE) -> list[dict]:
    """Hängt neue Kandidaten an den Backlog an, entnimmt einen Batch zur
    Bewertung und speichert den Rest zurück.

    Reihenfolge: neuestes Veröffentlichungsdatum zuerst (posted_date), damit
    frische Anzeigen nicht erst nach hunderten älteren Backlog-Einträgen
    drankommen. Nur BA-Jobsuche liefert dieses Datum zuverlässig — Jobs ohne
    Datum (Adzuna/StepStone/Indeed) werden nicht bevorzugt, sonst kämen sie
    nie an die Reihe, sondern rutschen ans Ende, dort aber weiterhin FIFO
    (älteste zuerst entdeckt zuerst dran), damit sie trotzdem stetig
    abgearbeitet werden. Python sort() ist stabil, reverse=True erhält dabei
    die urspüngliche Reihenfolge innerhalb gleicher Schlüssel (hier: alle
    Jobs ohne Datum)."""
    full_queue = enqueue_new(person, candidate_dicts)
    full_queue.sort(key=lambda j: j.get("posted_date") or "", reverse=True)
    batch = full_queue[:batch_size]
    remaining = full_queue[batch_size:]
    save_backlog(person, remaining)
    return batch
