"""SQLite-basierte Dedup-Liste.

Trotz der Namen already_sent()/mark_sent() bedeutet ein Eintrag hier "wurde
bereits BEWERTET", nicht nur "wurde verschickt" — finish_run.py/main.py rufen
mark_sent() für JEDEN bewerteten Job auf, auch die unter dem Schwellenwert.
Sonst würden Jobs, die es nicht über den Schwellenwert schaffen, bei jedem
Lauf erneut in der Rohsuche auftauchen und erneut bewertet werden (unnötige
Kosten in Variante A, unnötige Arbeit in Variante B) — v.a. relevant mit der
Backlog-Warteschlange (src/backlog.py), die pro Lauf nur einen Teil der
Treffer verarbeitet.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path("data/sent_jobs.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS sent_jobs (
    person   TEXT NOT NULL,
    job_id   TEXT NOT NULL,
    source   TEXT NOT NULL,
    sent_at  TEXT NOT NULL,
    PRIMARY KEY (person, job_id, source)
);
"""


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(SCHEMA)
    return conn


def already_sent(person: str, job_id: str, source: str) -> bool:
    with _connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM sent_jobs WHERE person=? AND job_id=? AND source=?",
            (person, job_id, source),
        ).fetchone()
        return row is not None


def mark_sent(person: str, job_id: str, source: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO sent_jobs (person, job_id, source, sent_at) "
            "VALUES (?, ?, ?, datetime('now'))",
            (person, job_id, source),
        )
        conn.commit()
