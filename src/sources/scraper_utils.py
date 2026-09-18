"""Gemeinsame Hilfsfunktionen für alle Scraper (StepStone, Indeed, Kununu).

Zweck: höfliches, robustes Scraping — realistischer User-Agent, zufällige
Pausen zwischen Requests, Retry mit Backoff. Von allen Scrapern importieren,
nicht duplizieren.
"""

import random
import time
from urllib.parse import urlencode

import requests
from playwright.sync_api import sync_playwright

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

    Funktioniert nicht für Seiten mit Bot-Schutz (z.B. Indeed blockt reine
    requests-Anfragen mit 403) — dafür polite_get_rendered() verwenden.
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


def polite_get_rendered(url: str, params: dict | None = None, max_retries: int = 3) -> str:
    """Wie polite_get(), aber über einen echten (headless) Browser (Playwright)
    statt requests — nötig für Seiten mit Bot-Schutz gegen einfache HTTP-Clients
    (z.B. Indeed). Gibt das gerenderte HTML als String zurück.

    Braucht `playwright install chromium` einmalig lokal.
    """
    time.sleep(random.uniform(3, 8))  # nie im Sekundentakt anfragen
    full_url = f"{url}?{urlencode(params)}" if params else url

    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                try:
                    page = browser.new_page(
                        user_agent=USER_AGENT, extra_http_headers=DEFAULT_HEADERS
                    )
                    page.goto(full_url, timeout=20000, wait_until="domcontentloaded")
                    page.wait_for_timeout(2000)
                    return page.content()
                finally:
                    browser.close()
        except Exception as exc:  # noqa: BLE001 — Playwright wirft diverse Fehlertypen
            last_error = exc
            time.sleep(2**attempt)
    raise last_error  # type: ignore[misc]
