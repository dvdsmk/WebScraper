"""News headline scraper (demo: Hacker News)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from scraper.base import BaseScraper, ScraperError, to_serializable


@dataclass
class NewsItem:
    rank: int
    title: str
    url: str
    points: str
    author: str
    comments: str


class HackerNewsScraper(BaseScraper):
    """Scrapes top stories from news.ycombinator.com."""

    BASE_URL = "https://news.ycombinator.com/"

    def __init__(self, limit: int = 30, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.limit = limit

    @property
    def name(self) -> str:
        return "news"

    def scrape(self) -> list[dict[str, Any]]:
        soup = self.get_soup(self.BASE_URL)
        items: list[NewsItem] = []

        rows = soup.select("tr.athing")[: self.limit]
        for row in rows:
            rank_el = row.select_one("span.rank")
            title_el = row.select_one("span.titleline a")
            if not title_el:
                continue

            rank = int(rank_el.get_text(strip=True).rstrip(".")) if rank_el else len(items) + 1
            story_id = row.get("id", "")

            meta_row = soup.select_one(f"tr#score_{story_id}") if story_id else None
            subtext_row = meta_row.find_parent("tr").find_next_sibling("tr") if meta_row else None
            subtext = subtext_row.select_one("td.subtext") if subtext_row else None

            points = "0"
            author = ""
            comments = "0"
            if subtext:
                score_el = subtext.select_one("span.score")
                if score_el:
                    points = score_el.get_text(strip=True).split()[0]

                user_el = subtext.select_one("a.hnuser")
                if user_el:
                    author = user_el.get_text(strip=True)

                for link in subtext.select("a"):
                    text = link.get_text(strip=True)
                    if "comment" in text.lower():
                        comments = text.split()[0]
                        break

            items.append(
                NewsItem(
                    rank=rank,
                    title=title_el.get_text(strip=True),
                    url=title_el.get("href", ""),
                    points=points,
                    author=author,
                    comments=comments,
                )
            )

        if not items:
            raise ScraperError("No news items found on Hacker News")

        return [to_serializable(item) for item in items]
