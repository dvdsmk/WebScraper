"""Schedule scraper (demo: worldtimeapi.org public timezone data)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from scraper.base import BaseScraper, ScraperError, to_serializable


@dataclass
class ScheduleEntry:
    timezone: str
    datetime: str
    day_of_week: str
    utc_offset: str
    is_dst: bool


class WorldTimeScraper(BaseScraper):
    """Scrapes current time/schedule info for major cities."""

    TIMEZONES = [
        ("Europe/Moscow", "Москва"),
        ("Europe/London", "Лондон"),
        ("America/New_York", "Нью-Йорк"),
        ("Asia/Tokyo", "Токио"),
        ("Australia/Sydney", "Сидней"),
        ("Europe/Berlin", "Берлин"),
    ]

    API_URL = "https://worldtimeapi.org/api/timezone/{timezone}"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @property
    def name(self) -> str:
        return "schedule"

    def scrape(self) -> list[dict[str, Any]]:
        entries: list[ScheduleEntry] = []

        for tz, _city in self.TIMEZONES:
            url = self.API_URL.format(timezone=tz)
            self._respect_delay()
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                data = response.json()
            except Exception as exc:
                raise ScraperError(f"Failed to fetch schedule for {tz}: {exc}") from exc
            finally:
                self._mark_request()

            entries.append(
                ScheduleEntry(
                    timezone=f"{tz} ({_city})",
                    datetime=data.get("datetime", ""),
                    day_of_week=data.get("day_of_week", ""),
                    utc_offset=data.get("utc_offset", ""),
                    is_dst=bool(data.get("dst", False)),
                )
            )

        return [to_serializable(entry) for entry in entries]
