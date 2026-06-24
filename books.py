"""Product price scraper (demo: books.toscrape.com)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin

from scraper.base import BaseScraper, ScraperError, to_serializable


@dataclass
class Product:
    title: str
    price: str
    availability: str
    rating: str
    url: str


class BooksScraper(BaseScraper):
    """Scrapes book titles and prices from books.toscrape.com."""

    BASE_URL = "https://books.toscrape.com/"

    def __init__(self, max_pages: int = 3, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.max_pages = max_pages

    @property
    def name(self) -> str:
        return "books"

    def scrape(self) -> list[dict[str, Any]]:
        products: list[Product] = []
        url: str | None = self.BASE_URL
        pages_scraped = 0

        while url and pages_scraped < self.max_pages:
            soup = self.get_soup(url)
            for article in soup.select("article.product_pod"):
                title_el = article.select_one("h3 a")
                price_el = article.select_one("p.price_color")
                availability_el = article.select_one("p.instock.availability")
                rating_el = article.select_one("p.star-rating")

                if not title_el or not price_el:
                    continue

                product_url = urljoin(url, title_el.get("href", ""))
                products.append(
                    Product(
                        title=title_el.get("title", title_el.get_text(strip=True)),
                        price=price_el.get_text(strip=True),
                        availability=(
                            availability_el.get_text(strip=True).replace("\n", " ")
                            if availability_el
                            else "Unknown"
                        ),
                        rating=(
                            " ".join(rating_el.get("class", [])[1:])
                            if rating_el and len(rating_el.get("class", [])) > 1
                            else "N/A"
                        ),
                        url=product_url,
                    )
                )

            next_link = soup.select_one("li.next a")
            url = urljoin(url, next_link["href"]) if next_link else None
            pages_scraped += 1

        if not products:
            raise ScraperError("No products found on books.toscrape.com")

        return [to_serializable(p) for p in products]
