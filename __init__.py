"""Built-in scraper implementations."""

from scraper.scrapers.books import BooksScraper
from scraper.scrapers.news import HackerNewsScraper
from scraper.scrapers.schedule import WorldTimeScraper

__all__ = ["BooksScraper", "HackerNewsScraper", "WorldTimeScraper"]
