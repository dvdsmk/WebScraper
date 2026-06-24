#!/usr/bin/env python3
"""CLI entry point for the web scraper."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scraper.base import BaseScraper, ScraperError, save_csv, save_json
from scraper.scrapers import BooksScraper, HackerNewsScraper, WorldTimeScraper

SCRAPERS: dict[str, type[BaseScraper]] = {
    "books": BooksScraper,
    "news": HackerNewsScraper,
    "schedule": WorldTimeScraper,
}

SOURCE_URLS = {
    "books": BooksScraper.BASE_URL,
    "news": HackerNewsScraper.BASE_URL,
    "schedule": "https://worldtimeapi.org/",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Web scraper — сбор данных с сайтов (цены, новости, расписание)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  python main.py books --format json
  python main.py news --limit 20 --format csv
  python main.py schedule --output data/timezones.json
  python main.py books --pages 5 --format both
        """,
    )
    parser.add_argument(
        "scraper",
        choices=list(SCRAPERS),
        help="Тип парсера: books (цены), news (новости), schedule (расписание/время)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "csv", "both"],
        default="json",
        help="Формат сохранения (по умолчанию: json)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Путь к выходному файлу (по умолчанию: output/<scraper>.<format>)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=30,
        help="Лимит записей для news (по умолчанию: 30)",
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=3,
        help="Количество страниц для books (по умолчанию: 3)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Задержка между запросами в секундах (по умолчанию: 1.0)",
    )
    return parser


def create_scraper(name: str, args: argparse.Namespace) -> BaseScraper:
    cls = SCRAPERS[name]
    kwargs = {"delay": args.delay}
    if name == "books":
        kwargs["max_pages"] = args.pages
    elif name == "news":
        kwargs["limit"] = args.limit
    return cls(**kwargs)


def default_output_path(scraper: str, fmt: str) -> Path:
    return Path("output") / f"{scraper}.{fmt}"


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    scraper = create_scraper(args.scraper, args)
    print(f"Запуск парсера: {scraper.name}...")

    try:
        data = scraper.scrape()
    except ScraperError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1

    print(f"Собрано записей: {len(data)}")

    formats = ["json", "csv"] if args.format == "both" else [args.format]
    source_url = SOURCE_URLS[args.scraper]

    for fmt in formats:
        if args.output and len(formats) == 1:
            out_path = args.output
        elif args.output and args.format == "both":
            out_path = args.output.with_suffix(f".{fmt}")
        else:
            out_path = default_output_path(args.scraper, fmt)

        if fmt == "json":
            saved = save_json(data, out_path, scraper_name=scraper.name, source_url=source_url)
        else:
            saved = save_csv(data, out_path)

        print(f"Сохранено: {saved.resolve()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
