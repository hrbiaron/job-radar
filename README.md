# Job-Radar

Ein kleines, quasi-kostenloses System, das automatisiert nach passenden Jobs sucht,
sie gegen Lebenslauf + Fragebogen bewertet, mit einer Firmenreputations-Einschätzung
(Kununu) anreichert und per E-Mail als Digest verschickt — ohne einen Job zweimal
vorzuschlagen.

Gebaut für zwei Personen gleichzeitig (z.B. Schwester + Frau), aber beliebig
erweiterbar über `config/people.yaml`.

## Wie es funktioniert (Ablauf pro Durchlauf)

1. **Suche** – BA-Jobsuche + Adzuna (APIs) sowie StepStone/Indeed (Scraper) werden
   pro Person mit deren Suchkriterien abgefragt.
2. **Dedup-Vorfilter** – Treffer werden gegen `data/sent_jobs.db` geprüft; bereits
   verschickte Jobs fliegen sofort raus.
3. **Matching** – für jeden neuen Job ruft `src/matching/scorer.py` die Claude-API
   auf: Kandidatenprofil (CV + Fragebogen) gegen Stellenanzeige → Score 0–100 +
   kurze Begründung.
4. **Schwellenwert** – nur Jobs über dem in `people.yaml` gesetzten `min_score`
   kommen weiter (optional inkl. "vielleicht"-Zone).
5. **Firmen-Check** – für die verbliebenen Top-Kandidaten wird `kununu_scraper.py`
   (Note, Weiterempfehlungsrate, Anzahl Bewertungen, Kurzfazit letzter Kommentare)
   abgefragt und in `data/company_cache.json` gecacht (Standard: 90 Tage).
6. **E-Mail** – `templates/email_digest.html` wird gerendert und per SMTP verschickt.
7. **Merken** – verschickte Jobs werden in `sent_jobs.db` eingetragen, damit sie nie
   wieder auftauchen.

## Zwei Varianten

| | Variante A: `main.py` + GitHub Actions | Variante B: `.claude/skills/job-radar-update` |
|---|---|---|
| Bewertung läuft über | eigener Anthropic-API-Key (`ANTHROPIC_API_KEY`) | deine Claude-Pro/Max-Session in Claude Code |
| Kosten | ein paar Euro/Monat (siehe "Kosten" unten) | keine zusätzlichen, zählt zu deinem Abo-Kontingent |
| Automatisierung | vollständig, täglich, unbeaufsichtigt | manuell — du tippst `/job-radar-update` in Claude Code |
| Wann sinnvoll | "läuft einfach, Kosten sind egal" | "will nichts extra zahlen, starte es gern selbst" |

**Wichtige Falle bei Variante B:** Ist auf deinem Rechner eine
`ANTHROPIC_API_KEY`-Umgebungsvariable gesetzt (z.B. weil du sie für ein
anderes Projekt brauchst), nutzt Claude Code automatisch diese und rechnet
über die API ab statt über dein Abo. Vor dem ersten Lauf prüfen:
`echo $ANTHROPIC_API_KEY` sollte leer sein, sonst mit `/login` in Claude
Code explizit auf den Abo-Modus wechseln.

Beide Varianten teilen sich Dedup-Datenbank, Kununu-Scraper, E-Mail-Versand
und die GitHub-Pages-Seite — man kann auch zwischen ihnen wechseln.

## Datenquellen

| Quelle | Art | Kosten | Hinweis |
|---|---|---|---|
| BA-Jobsuche | inoffizielle, aber stabile API | kostenlos | `clientId: jobboerse-jobsuche`, Header `X-API-Key` |
| Adzuna | offizielle API | kostenlos bis 250 Anfragen/Tag, 25/Min | Anmeldung: developer.adzuna.com |
| StepStone / Indeed | Scraper auf öffentliche Suchergebnisseiten | kostenlos | selektoren müssen ggf. nachgepflegt werden, Seiten ändern sich |
| Kununu | Scraper, kein offizielles API | kostenlos | stark cachen (90 Tage), nur für Top-Kandidaten aufrufen, Volumen niedrig halten |

## Setup

1. `python -m venv venv && source venv/bin/activate`
2. `pip install -r requirements.txt`
3. `playwright install chromium` (nur falls eine Scraper-Quelle JS-Rendering braucht)
4. `.env.example` nach `.env` kopieren und Zugangsdaten eintragen
5. `config/people.yaml` ausfüllen (CV-Pfad, Suchkriterien, E-Mail, Schwellenwert)
6. Fragebogen (`survey/fragebogen.md`) an Schwester & Frau schicken, Antworten
   in `data/profiles/<name>_survey.json` ablegen (Struktur siehe
   `src/matching/profile_builder.py`)

**Variante A (eigener API-Key, voll automatisch):**

7. `.env` mit `ANTHROPIC_API_KEY` befüllen
8. Testlauf: `python -m src.main --dry-run`, dann `python -m src.main`

**Variante B (Claude-Code-Skill, kostenlos über dein Abo):**

7. `ANTHROPIC_API_KEY` NICHT in der Umgebung setzen (siehe "Zwei Varianten")
8. Claude Code im Projektordner starten, `/job-radar-update` eingeben

## Live-Ansicht ohne Claude-Konto (GitHub Pages)

Statt (oder zusätzlich zur) E-Mail gibt es `docs/index.html` — eine kleine,
interaktive Seite (Suche, Sortierung, "als interessant markieren"/"ausblenden"
über den Browser-Speicher des jeweiligen Geräts), die `docs/jobs.json` anzeigt.
`src/static_site.py` schreibt diese Datei bei jedem Lauf automatisch mit.

Einmalig einrichten:
1. Repo zu GitHub pushen
2. Unter *Settings → Pages* als Quelle "Deploy from a branch", Branch `main`,
   Ordner `/docs` auswählen
3. GitHub zeigt danach den Link (z.B. `https://<user>.github.io/job-radar/`) —
   diesen an Schwester und Frau schicken, kein Login nötig

Wichtig: Ein "als interessant markiert"-Klick wird nur lokal im jeweiligen
Browser gespeichert, nicht geräteübergreifend synchronisiert — **außer** ihr
richtet den optionalen Google-Sheets-Sync ein, siehe nächster Abschnitt.

## Geräteübergreifende Synchronisation (Google Sheets als Datenbank)

`sheets-backend/` enthält ein kleines Google Apps Script, das ein Google
Sheet als kostenlose Mini-Datenbank nutzbar macht — **pro Person ein eigenes
Sheet und eine eigene Bereitstellung**, komplett getrennt. Setup-Anleitung
in `sheets-backend/SETUP.md`. Danach zeigen Markierungen ("interessant" /
"ausgeblendet") auf allen Geräten derselben Person denselben Stand, ganz
ohne eigenen Server.

## Automatisierung (Variante A)

`.github/workflows/daily-job-scan.yml` führt `main.py` täglich per GitHub Actions
aus (Freikontingent reicht locker). Zugangsdaten liegen dafür als GitHub Secrets,
nicht als `.env` im Repo.

## Kosten

**Variante B:** 0 € zusätzlich — zählt zu deinem bestehenden Claude-Abo.

**Variante A:** Kununu läuft über den Scraper (keine API, keine Kosten), der
einzige Kostenpunkt ist der Matching-Aufruf in `src/matching/scorer.py`
(Claude Haiku). Grobe Schätzung bei ~50 neuen Jobs/Person/Tag: ca. 4-5 €/Monat
für beide zusammen — unverifizierte Schätzung auf Basis angenommener
Job-Volumina, in der Praxis über die Anthropic-Console beobachten. Bei sehr
offenen Suchkriterien (z.B. leeres `was`-Feld) kann das deutlich höher
ausfallen; dagegen hilft ein Limit wie `MAX_JOBS_PER_RUN` in `main.py`.

## Rechtlicher Hinweis

StepStone/Indeed/Kununu-Scraping erfolgt gegen öffentlich zugängliche Seiten,
bewegt sich aber außerhalb der jeweiligen Nutzungsbedingungen. Deshalb bewusst:
niedrige Frequenz, echte Wartezeiten zwischen Requests, aggressives Caching bei
Kununu. Kein Umgehen von Logins oder Bezahlschranken.
