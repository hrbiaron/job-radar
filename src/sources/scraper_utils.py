"""Gemeinsame Hilfsfunktionen für alle Scraper (StepStone, Indeed, Kununu).

Zweck: höfliches, robustes Scraping — realistischer User-Agent, zufällige
Pausen zwischen Requests, Retry mit Backoff. Von allen Scrapern importieren,
nicht duplizieren.
"""

import random
import time

import requests

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Language": "de-DE,de;q=0.9",
}


def polite_get(url: str, params: dict | None = None, max_retries: int = 3) -> requests.Response:
    """GET-Request mit Zufalls-Pause davor + Retry/Backoff bei Fehlern.

    TODO: bei Bedarf auf einen echten Browser (playwright) umstellen, falls
    eine Seite Inhalte per JavaScript nachlädt und requests nur ein leeres
    Gerüst zurückbekommt.
    """
    time.sleep(random.uniform(3, 8))  # nie im Sekundentakt anfragen

    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=DEFAULT_HEADERS, params=params, timeout=15)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:  # noqa: PERF203
            last_error = exc
            time.sleep(2**attempt)  # 1s, 2s, 4s ...
    raise last_error  # type: ignore[misc]
