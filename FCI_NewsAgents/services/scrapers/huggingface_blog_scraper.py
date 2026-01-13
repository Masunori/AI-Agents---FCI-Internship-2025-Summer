import datetime as datetime_module
from typing import Any, Dict, List, Tuple

import feedparser
import requests
from bs4 import BeautifulSoup

from FCI_NewsAgents.models.article import Article
from FCI_NewsAgents.services.parsers.web_article_parser import (
    extract_text_from_web_article,
)
from FCI_NewsAgents.services.scrapers.base_scraper import BaseScraper
from FCI_NewsAgents.services.scrapers.registry import register
from FCI_NewsAgents.utils.utils import run_with_retry


@register("HuggingfaceBlog")
class HuggingfaceBlogScraper(BaseScraper):
    """Scraper for Huggingface Blog articles"""

    def __init__(self, rss_url: str = "https://huggingface.co/blog/feed.xml"):
        self.rss_url = rss_url

    def get_name(self) -> str:
        return "HuggingfaceBlog"

    def _get_author_and_summary(self, url: str) -> Tuple[List[str], str]:
        """
        Extract author names and summary from a Huggingface Blog article URL
        """

        def get_html_content() -> str:
            request_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            }
            response = requests.get(url, headers=request_headers, timeout=10)
            response.raise_for_status()

            return response.text

        def on_exception(e: Exception, attempt: int):
            print(f"Attempt {attempt} failed for URL {url} with error: {e}")

        try:
            html_content = run_with_retry(
                fn=get_html_content, max_retries=3, on_exception=on_exception
            )

            soup = BeautifulSoup(html_content, "html.parser")

            author_spans = soup.select("span.fullname")
            authors = [
                span.get_text(strip=True)
                for span in author_spans
                if span.get_text(strip=True)
            ]

            summary = soup.get_text(strip=True)[:600]

            return authors, summary

        except Exception as e:
            print(f"Error extracting author and summary from {url}: {e}")
            return ["Huggingface Team"], ""

    def scrape(self) -> List[Article]:
        """
        Scrape articles from Huggingface Blog RSS feed
        """
        print(f"Scraping articles from {self.rss_url}...")

        try:
            request_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            }

            feed = feedparser.parse(self.rss_url, request_headers=request_headers)
            articles = []

            for entry in feed["entries"]:
                try:
                    published_date_str = entry.get("published", "")

                    if published_date_str:
                        # Example format: 'Wed, 14 Aug 2024 10:00:00 GMT'
                        published_date_str = published_date_str[5:16]
                        published_date = datetime_module.datetime.strptime(
                            published_date_str, "%d %b %Y"
                        ).date()

                        # Filter articles older than 14 days
                        if (
                            published_date
                            < datetime_module.date.today()
                            - datetime_module.timedelta(days=14)
                        ):
                            continue

                        published_date_str = published_date.isoformat()

                    authors, summary = self._get_author_and_summary(entry["link"])

                    article = Article(
                        url=entry["link"],
                        title=entry["title"],
                        summary=summary,
                        published_date=datetime_module.datetime(
                            *entry.published_parsed[:6]
                        ).isoformat(),
                        authors=authors,
                        source="Huggingface Blog",
                    )

                    articles.append(article)

                except Exception as e:
                    print(f"Error processing Huggingface Blog article: {e}")
                    continue

            print(f"Scraped {len(articles)} articles from Huggingface Blog")
            return articles

        except Exception as e:
            print(f"Error parsing Huggingface Blog RSS feed: {e}")
            return []
