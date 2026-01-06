import datetime as datetime_module
from typing import Any, Dict, List

import feedparser

from FCI_NewsAgents.models.article import Article
from FCI_NewsAgents.services.scrapers.base_scraper import BaseScraper
from FCI_NewsAgents.services.scrapers.registry import register


@register("OpenAINews")
class OpenAINewsScraper(BaseScraper):
    """Scraper for OpenAI News articles"""
    
    def __init__(self, rss_url: str = "https://openai.com/news/rss.xml"):
        self.rss_url = rss_url
    
    def get_name(self) -> str:
        return "OpenAINews"
    
    def scrape(self) -> List[Article]:
        """
        Scrape articles from OpenAI News RSS feed
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

            for entry in feed['entries']:
                try:
                    published_date_str = entry.get('published', '')

                    if published_date_str:
                        # Example format: 'Wed, 14 Aug 2024 10:00:00 GMT'
                        published_date_str = published_date_str[5:16]
                        published_date = datetime_module.datetime.strptime(published_date_str, '%d %b %Y').date()

                        # Filter articles older than 14 days
                        if published_date < datetime_module.date.today() - datetime_module.timedelta(days=14):
                            continue

                        published_date_str = published_date.isoformat()

                    article = Article(
                        url=entry['link'],
                        title=entry['title'],
                        summary=entry.get('summary', ''),
                        authors="OpenAI",
                        published_date=published_date_str,
                    )

                    articles.append(article)

                except Exception as e:
                    print(f"Error processing OpenAI article: {e}")
                    continue

            print(f"Scraped {len(articles)} articles from OpenAI News")
            return articles
        
        except Exception as e:
            print(f"Error parsing OpenAI RSS feed: {e}")
            return []
