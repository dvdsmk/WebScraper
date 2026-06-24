"""Base scraper utilities."""

from __future__ import annotations

import csv
import json
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup


class ScraperError(Exception):
    """Raised when scraping fails."""


class BaseScraper(ABC):
    """Abstract base class for all scrapers."""

    def __init__(
        self,
        *,
        timeout: int = 15,
        delay: float = 1.0,
        user_agent: str | None = None,
    ) -> None:
        self.timeout = timeout
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": user_agent
                or (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
            }
        )
        self._last_request_at: float | None = None

    def fetch_html(self, url: str) -> str:
        """Download page HTML with rate limiting."""
        self._respect_delay()
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ScraperError(f"Failed to fetch {url}: {exc}") from exc
        return response.text

    def parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML into BeautifulSoup object."""
        return BeautifulSoup(html, "lxml")

    def _respect_delay(self) -> None:
        if self._last_request_at is None:
            return
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)

    def _mark_request(self) -> None:
        self._last_request_at = time.monotonic()

    def get_soup(self, url: str) -> BeautifulSoup:
        """Fetch URL and return parsed soup."""
        self._respect_delay()
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ScraperError(f"Failed to fetch {url}: {exc}") from exc
        finally:
            self._mark_request()
        return BeautifulSoup(response.text, "lxml")

    @abstractmethod
    def scrape(self) -> list[dict[str, Any]]:
        """Collect data and return as list of dictionaries."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable scraper name."""


def to_serializable(item: Any) -> dict[str, Any]:
    """Convert dataclass or dict to plain dict."""
    if is_dataclass(item) and not isinstance(item, type):
        return asdict(item)
    if isinstance(item, dict):
        return item
    raise TypeError(f"Unsupported item type: {type(item)!r}")


def save_json(
    data: list[dict[str, Any]],
    path: Path,
    *,
    scraper_name: str,
    source_url: str,
) -> Path:
    """Save scraped data to JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "scraper": scraper_name,
        "source": source_url,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "count": len(data),
        "items": data,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def save_csv(data: list[dict[str, Any]], path: Path) -> Path:
    """Save scraped data to CSV file."""
    if not data:
        raise ScraperError("No data to save to CSV")

    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in data:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)

    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    return path
