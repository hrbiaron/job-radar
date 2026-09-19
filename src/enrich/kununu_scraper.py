"""Reichert eine Firma mit Kununu-Kennzahlen an: Gesamtnote,
Weiterempfehlungsrate, Anzahl Bewertungen, Kurzfazit letzter Kommentare.

Wichtig für Volumen-Kontrolle:
  - IMMER zuerst in data/company_cache.json nachsehen (siehe unten)
  - nur bei Cache-Miss oder abgelaufenem Cache (Standard: 90 Tage) wirklich
    einen Request an Kununu schicken
  - nur für Firmen aufrufen, deren Job es über den Score-Schwellenwert
    geschafft hat — nicht für jeden Treffer der Rohsuche
"""

import json
import time
from pathlib import Path
from urllib.parse import quote

from bs4 import BeautifulSoup

from ..sources.scraper_utils import polite_get

CACHE_PATH = Path("data/company_cache.json")
CACHE_TTL_SECONDS = 90 * 24 * 3600

SEARCH_URL = "https://www.kununu.com/de/search?q={query}"


def kununu_search_url(company_name: str) -> str:
    """Link zur Kununu-Suche für eine Firma — zum manuellen Nachschauen per Klick,
    kein automatischer Abruf (siehe get_company_info-Docstring, warum wir hier
    keine Daten scrapen)."""
    return SEARCH_URL.format(query=quote(company_name))


def _load_cache() -> dict:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return {}


def _save_cache(cache: dict) -> None:
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


EMPTY_INFO = {"rating": None, "recommend_pct": None, "review_count": None, "summary": None}


def get_company_info(company_name: str) -> dict:
    """Liefert {"rating": float, "recommend_pct": float, "review_count": int,
    "summary": str} — aus Cache falls vorhanden und frisch genug, sonst live.

    Kununu zeigt Scrapern aktuell eine "Human Verification"-Sperrseite (aktiver
    Bot-Schutz) — das gezielt zu umgehen (Stealth-Browser, Captcha-Lösung) ist
    bewusst nicht implementiert (siehe README, rechtlicher Hinweis). Schlägt
    der Abruf fehl, liefert diese Funktion EMPTY_INFO statt eine Exception zu
    werfen, damit ein einzelner blockierter Abruf nicht den ganzen Lauf killt.

    TODO:
      - Firmensuche -> korrektes Firmenprofil auswählen (Namensabgleich ist
        bei mehrdeutigen Firmennamen nicht trivial; im Zweifel ersten Treffer
        nehmen und im Log kennzeichnen, dass das ungeprüft ist)
      - `summary`: die letzten 3-5 Bewertungstitel/-kurztexte einsammeln und
        anschließend über die Claude-API paraphrasieren lassen (nicht 1:1
        übernehmen) — siehe src/matching/scorer.py für das Anthropic-Client-Setup
    """
    cache = _load_cache()
    entry = cache.get(company_name)
    if entry and (time.time() - entry["fetched_at"]) < CACHE_TTL_SECONDS:
        return entry["data"]

    try:
        response = polite_get(SEARCH_URL.format(query=quote(company_name)))
        soup = BeautifulSoup(response.text, "lxml")

        rating_el = soup.select_one("[data-testid='company-rating-value']")
        recommend_el = soup.select_one("[data-testid='company-recommend-pct']")
        count_el = soup.select_one("[data-testid='company-review-count']")

        data = {
            "rating": float(rating_el.get_text(strip=True).replace(",", ".")) if rating_el else None,
            "recommend_pct": float(recommend_el.get_text(strip=True).replace("%", "")) if recommend_el else None,
            "review_count": int(count_el.get_text(strip=True)) if count_el else None,
            "summary": None,  # TODO: siehe Docstring oben
        }
    except Exception as exc:  # noqa: BLE001 — ein blockierter Abruf darf den Lauf nie stoppen
        print(f"[kununu_scraper] WARNUNG: Abruf für '{company_name}' fehlgeschlagen: {exc}")
        data = dict(EMPTY_INFO)

    cache[company_name] = {"fetched_at": time.time(), "data": data}
    _save_cache(cache)
    return data
