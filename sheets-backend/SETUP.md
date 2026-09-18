# Setup: getrennte Google Sheets für Schwester und Frau

Jede Person bekommt ihr eigenes Sheet, ihre eigene Apps-Script-Bereitstellung,
ihre eigene URL und ihr eigenes Secret. **Diese Schritte einmal pro Person
wiederholen** (also zweimal insgesamt):

1. **Google Sheet erstellen** – neues, leeres Sheet, z.B. "Job-Radar-Sync
   Schwester" bzw. "Job-Radar-Sync Frau" nennen. Kein Tabellenkopf nötig,
   das Skript legt ihn selbst an.
2. **Apps Script öffnen** – *Erweiterungen → Apps Script*, Inhalt von
   `Code.gs` (dieser Ordner) reinkopieren. `SECRET` durch ein eigenes,
   langes Zufalls-Passwort ersetzen (für jede Person ein anderes!).
3. **Als Web-App bereitstellen** – *Bereitstellen → Neue Bereitstellung* →
   Typ "Web-App" → "Ausführen als: Ich" → "Zugriff: Jeder" → bereitstellen,
   Berechtigungen bestätigen.
4. **Web-App-URL notieren** – die angezeigte URL (endet auf `/exec`) zusammen
   mit dem Secret irgendwo festhalten, bis beide Personen durch sind.
5. Nach beiden Durchläufen: in `docs/index.html` den `PERSON_CONFIG`-Block
   ausfüllen — pro Personenname (muss exakt zum Namen in
   `config/people.yaml` passen) die jeweilige URL + Secret eintragen.
6. **Testen** – Seite neu laden, Person auswählen, einen Job als
   "interessant" markieren, im zugehörigen Sheet prüfen, ob eine neue Zeile
   erscheint. Dann die andere Person testen — beide Sheets müssen unabhängig
   bleiben.
7. **Committen & pushen** – geänderte `docs/index.html` committen,
   GitHub Pages übernimmt automatisch.

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
