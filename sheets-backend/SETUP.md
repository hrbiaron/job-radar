# Setup: getrennte Google Sheets pro Person

Jede Person bekommt ihr eigenes Sheet, ihre eigene Apps-Script-Bereitstellung,
ihre eigene URL und ihr eigenes Secret. **Diese Schritte einmal pro Person
wiederholen:**

1. **Google Sheet erstellen** – neues, leeres Sheet, z.B. "Job-Radar-Sync
   <Name>" nennen. Kein Tabellenkopf nötig, das Skript legt ihn selbst an.
2. **Apps Script öffnen** – *Erweiterungen → Apps Script*, Inhalt von
   `Code.gs` (dieser Ordner) reinkopieren. `SECRET` durch ein eigenes,
   langes Zufalls-Passwort ersetzen (für jede Person ein anderes!).
3. **Als Web-App bereitstellen** – *Bereitstellen → Neue Bereitstellung* →
   Typ "Web-App" → "Ausführen als: Ich" → "Zugriff: Jeder" → bereitstellen,
   Berechtigungen bestätigen.
4. **Web-App-URL notieren** – die angezeigte URL (endet auf `/exec`) zusammen
   mit dem Secret festhalten.
5. In `config/people.yaml` beim jeweiligen Personen-Eintrag `sheets_sync_url`
   und `sheets_sync_token` eintragen (siehe `config/people.example.yaml` für
   die Struktur). Diese Werte werden bei jedem Lauf automatisch in die
   generierte `docs/<slug>/index.html` dieser Person eingebaut
   (`src/static_site.py`) — keine manuelle HTML-Bearbeitung nötig.
6. **Testen** – nach dem nächsten Lauf (`python -m src.finish_run` bzw. über
   die Skill) die Seite der Person öffnen, einen Job einen Status geben
   (z.B. "Interesse"), im zugehörigen Sheet prüfen, ob eine neue Zeile mit
   `status`/`comment` erscheint.

## Schema ändern (z.B. nach einem Update von `Code.gs`)

Wurde `Code.gs` in diesem Repo geändert (z.B. neue Spalten), muss **jede**
bereits bereitgestellte Person manuell aktualisiert werden — ein Push hier
aktualisiert die laufenden Google-Apps-Script-Bereitstellungen nicht
automatisch:

1. Google Sheet der Person öffnen → *Erweiterungen → Apps Script*
2. Alten Inhalt löschen, neuen `Code.gs`-Inhalt reinkopieren (`SECRET`
   unverändert lassen, sonst bricht die bestehende URL)
3. *Bereitstellen → Bereitstellungen verwalten* → Stift-Symbol bei der
   bestehenden Bereitstellung → Version: "Neue Version" → Bereitstellen

## Sicherheitshinweis

Die `SECRET`-Werte stehen im Klartext im HTML-Quelltext der öffentlichen
Seite — das schützt vor zufälligem Herumstöbern, ist aber keine echte
Absicherung gegen jemanden, der gezielt danach sucht. Für ein privates
Familientool vertretbar, aber: Link und Repo nicht öffentlich bewerben.

## Kosten & Limits

Kostenlos, für beide Sheets. Google Apps Script hat großzügige
Freikontingente für den persönlichen Gebrauch (u.a. 20.000 URL-Aufrufe/Tag
*pro* Google-Konto) — für zwei Personen mit gelegentlichem Markieren bei
Weitem ausreichend.
