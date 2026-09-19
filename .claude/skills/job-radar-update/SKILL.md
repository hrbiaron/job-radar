---
name: job-radar-update
description: Holt neue Jobs für Schwester und Frau, bewertet sie gegen ihr Profil (Score + Begründung), aktualisiert die GitHub-Pages-Seite und verschickt die Mail. Läuft komplett innerhalb dieser Claude-Code-Session — keine separaten Anthropic-API-Kosten, solange kein ANTHROPIC_API_KEY in der Umgebung gesetzt ist.
---

# Job-Radar Update

Führe diesen Ablauf Schritt für Schritt aus:

## 1. Neue Jobs holen (kostenlos, kein LLM)

Führe aus: `python -m src.fetch_raw`

Das schreibt für jede Person eine Datei `data/pending_scores/<Name>.json`
mit neuen, noch nicht bewerteten Jobs plus dem Kandidatenprofil
(CV-Text + Fragebogen-Antworten im Feld `profile`).

**Backlog-Warteschlange:** Findet die Rohsuche mehr neue Jobs, als in einem
Lauf sinnvoll bewertbar sind (Standard: 200, siehe `batch_size` in
`config/people.yaml`), landet der Rest in `data/backlog/<Name>.json` und
wird bei den nächsten Läufen nachgeholt (älteste zuerst) — zusammen mit
neu hinzugekommenen Treffern. Die Konsole zeigt an, wie viele Jobs noch im
Backlog übrig sind.

## 2. Jobs bewerten (das übernimmst DU, in dieser Session)

Für jede Datei in `data/pending_scores/`, die nicht leer ist:

- Lies die Datei.
- Bewerte JEDEN enthaltenen Job einzeln gegen das mitgelieferte
  `profile`-Feld. Vergib ehrlich und differenziert:
  - `score`: 0–100
  - `reason`: 2–3 Sätze auf Deutsch, konkret, warum es passt oder nicht
  - `direction_change_fit`: true/false — passt der Job zu einem
    gewünschten Richtungswechsel laut Fragebogen (nur relevant, falls im
    Fragebogen ein Richtungswechsel gewünscht ist, sonst immer false)
- Schreibe das Ergebnis nach `data/scored/<Name>.json` als JSON-Liste:
  jedes Element = das komplette Original-Job-Objekt (id, source, title,
  company, location, url, description, salary_min, salary_max,
  employment_type, posted_date — **alle unverändert durchreichen**, sonst
  fehlen Gehalt/Arbeitszeit/Datum später auf der Seite) plus die drei neuen
  Felder oben.
- Nicht pauschal hohe Scores vergeben — das Ziel ist eine ehrliche
  Einschätzung, keine Bestätigung.

## 3. Rest des Ablaufs (wieder kostenlos, kein LLM)

Führe aus: `python -m src.finish_run`

Das filtert nach dem in `config/people.yaml` gesetzten `min_score`,
verlinkt zu Kununu (kein automatischer Abruf, siehe Kununu-Hinweis im
Code), aktualisiert `docs/<person-slug>/jobs.json`, verschickt die
Benachrichtigungsmail und trägt ALLE bewerteten Jobs (nicht nur die
verschickten) in die Dedup-Datenbank ein, damit sie nie erneut bewertet
werden.

## 4. Committen & pushen

```
git add data/backlog docs
git commit -m "Job-Radar Update $(date +%Y-%m-%d)"
git push
```

(`config/people.yaml` bleibt bewusst außen vor, siehe `.gitignore` —
enthält echte Namen/E-Mails.)

GitHub Pages übernimmt die aktualisierte Seite automatisch — für diesen
Ablauf ist keine GitHub Action nötig.

## 5. Kurze Zusammenfassung

Am Ende: wie viele neue Jobs pro Person gefunden wurden und wie viele
davon über dem Schwellenwert lagen und verschickt wurden.

## Wichtig

- Wenn `data/pending_scores/<Name>.json` keine Jobs enthält, für diese
  Person Schritt 2 überspringen.
- Diese Skill ersetzt NICHT `src/main.py` — das ist Variante A mit
  eigenem Anthropic-API-Key für volle, unbeaufsichtigte
  GitHub-Actions-Automatisierung (kostet ein paar Euro/Monat, läuft aber
  auch ohne dass du etwas tust). Diese Skill hier ist Variante B: manuell
  angestoßen, dafür ohne Zusatzkosten zu deinem Abo. Siehe README,
  Abschnitt "Zwei Varianten".
