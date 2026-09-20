"""Bewertet eine Stellenanzeige gegen ein Kandidatenprofil per Claude-API.

Modell: claude-haiku-4-5 (günstig, für diese Klassifikations-/Bewertungsaufgabe
ausreichend). Bei Bedarf auf ein stärkeres Modell wechseln, falls die
Begründungen zu oberflächlich ausfallen.
"""

import json

import anthropic

client = anthropic.Anthropic()  # liest ANTHROPIC_API_KEY aus der Umgebung

SYSTEM_PROMPT = """\
Du bewertest, wie gut eine Stellenanzeige zu einem Kandidatenprofil passt.
Antworte AUSSCHLIESSLICH mit validem JSON, kein Fließtext davor oder danach:

{
  "score": <int 0-100>,
  "reason": "<2-3 Sätze, konkret, warum es passt oder nicht>",
  "direction_change_fit": <true/false — passt der Job zu einem angestrebten \
Richtungswechsel laut Fragebogen, falls einer gewünscht ist, sonst false>,
  "experience_gap": <string oder null — prüfe, ob die Anzeige Berufserfahrung \
in einem Bereich verlangt, den die Person laut CV/Fragebogen NICHT hat. Falls \
ja UND du den Job trotzdem empfiehlst (Score über der "vielleicht"-Grenze), \
beschreibe hier kurz und konkret, welche Erfahrung fehlt, und in "reason" \
zusätzlich, WARUM du den Job trotzdem für aussichtsreich hältst — wenn möglich \
mit einer Parallele zu anderer Erfahrung aus CV/Fragebogen, die übertragbar \
sein könnte. Sonst null.>
}
"""


def score_job(profile: dict, job_title: str, job_company: str, job_description: str) -> dict:
    """Ruft die Claude-API auf und gibt das geparste JSON-Ergebnis zurück.

    TODO:
      - Fehlerbehandlung, falls die Antwort mal kein valides JSON ist
        (z.B. Markdown-Codefences ```json entfernen, bevor json.loads)
      - Prompt ggf. um die Kununu-Kurzinfo erweitern, sobald die zum
        Bewertungszeitpunkt schon vorliegt
    """
    user_message = f"""\
KANDIDATENPROFIL:
Lebenslauf-Auszug: {profile['cv_text']}
Fragebogen: {json.dumps(profile['survey'], ensure_ascii=False)}

STELLENANZEIGE:
Titel: {job_title}
Firma: {job_company}
Beschreibung: {job_description}
"""

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=400,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    raw_text = response.content[0].text
    return json.loads(raw_text)
