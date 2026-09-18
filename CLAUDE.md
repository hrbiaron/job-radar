# Kontext für Claude Code

Dieses Repo ist ein Gerüst (Skeleton), kein fertiges System. Alle Dateien unter
`src/` enthalten Funktions-Signaturen, Docstrings und TODO-Kommentare, aber keine
vollständige Implementierung. Deine Aufgabe: Schritt für Schritt ausimplementieren,
am besten in dieser Reihenfolge:

1. `src/sources/base.py` – Datenmodell fixieren (JobPosting)
2. `src/sources/ba_jobsuche.py` + `src/sources/adzuna.py` – die beiden API-Quellen,
   da stabil und ohne Scraping-Risiko am schnellsten lauffähig
3. `src/dedup.py` – SQLite-Schema + already_sent()/mark_sent()
4. `src/matching/profile_builder.py` – CV-Parsing (pdfplumber/python-docx) +
   Fragebogen-JSON zusammenführen
5. `src/matching/scorer.py` – Anthropic-API-Call (Modell: claude-haiku-4-5, günstig
   und für diese Klassifikationsaufgabe ausreichend), Prompt so bauen, dass die
   Antwort valides JSON ist ({"score": int, "reason": str, "direction_change_fit": bool})
6. `src/emailer.py` + `templates/email_digest.html` – Rendering + SMTP-Versand
7. `src/main.py` – alles verdrahten
8. Erst danach: `src/sources/stepstone_scraper.py`, `src/sources/indeed_scraper.py`,
   `src/enrich/kununu_scraper.py` — diese drei brauchen echtes HTML-Inspizieren
   (CSS-Selektoren sind Platzhalter und müssen gegen die aktuell live ausgelieferte
   Seite geprüft werden, die sich jederzeit ändern kann)

## Konventionen

- Python 3.11+, Typannotationen wo sinnvoll
- Ein gemeinsames `JobPosting`-Datenmodell für alle Quellen (siehe `base.py`),
  damit Matching/Dedup/Mail-Code quellenunabhängig bleiben
- Keine Secrets im Code — alles über `.env` (lokal) bzw. GitHub Secrets (Actions)
- Scraper: realistischer User-Agent, 3–8s zufällige Pause zwischen Requests,
  Retry mit Backoff, keine Parallelisierung gegen dieselbe Domain
- Kununu-Resultate immer über `data/company_cache.json` cachen (Default 90 Tage),
  nie live bei jedem Lauf neu abrufen
- Bei Unsicherheit bei einem CSS-Selektor: lieber mit `print()`/Logging sichtbar
  machen, was tatsächlich zurückkommt, statt stillschweigend falsche Daten zu liefern

## Fachlicher Kontext

- `README.md` — Gesamtüberblick, Ablauf, Datenquellen, Kosten, **Variante A
  vs. B** (eigener API-Key vs. kostenlos über Claude-Pro/Max-Abo)
- `.claude/skills/job-radar-update/SKILL.md` — Variante B: bei Aufruf
  bewertest DU (Claude Code, in dieser Session) die Jobs direkt, ohne
  `scorer.py`/Anthropic-API. `src/fetch_raw.py` und `src/finish_run.py`
  sind die deterministischen Teile davor/danach.
- `survey/fragebogen.md` — Fragebogen für die beiden Kandidatinnen; deren
  Antworten fließen als strukturiertes JSON in `profile_builder.py` ein
- `config/people.yaml` — pro Person: Name, E-Mail, CV-Pfad, Suchkriterien,
  Score-Schwellenwert
