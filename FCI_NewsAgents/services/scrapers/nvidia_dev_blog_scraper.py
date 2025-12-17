import datetime as datetime_module
from dataclasses import asdict
from typing import Any, Dict, List

import feedparser
from bs4 import BeautifulSoup

from FCI_NewsAgents.services.scrapers.base_scraper import BaseScraper
from FCI_NewsAgents.models.article import Article
from FCI_NewsAgents.services.scrapers.registry import register


@register("NVIDIADevBlog")
class NVIDIADevBlogScraper(BaseScraper):
    """Scraper for NVIDIA Developer Blog articles"""
    
    def __init__(self, rss_url: str = "https://developer.nvidia.com/blog/"):
        self.rss_url = rss_url
        
        self.rss_urls = [
            "https://developer.nvidia.com/blog/category/generative-ai/feed/",
            "https://developer.nvidia.com/blog/tag/inference-performance/feed/",
            "https://developer.nvidia.com/blog/tag/build-ai-agent/feed/",
            "https://developer.nvidia.com/blog/category/computer-vision/feed/",
            "https://developer.nvidia.com/blog/category/data-center-cloud/feed/",
            "https://developer.nvidia.com/blog/category/networking-communications/feed/",
        ]
    
    def get_name(self) -> str:
        return "NVIDIADevBlog"
    
    def scrape(self) -> List[Dict[str, Any]]:
        """Scrape articles from NVIDIA Developer Blog RSS feed"""
        print(f"Scraping articles from {self.rss_url}...")

        articles: List[Dict[str, Any]] = []
        
        for rss_url in self.rss_urls:
            try:
                feed = feedparser.parse(rss_url)
                
                for entry in feed["entries"]:
                    try:
                        published_date = entry.get("published", "")

                        if published_date:
                            published_datetime = datetime_module.datetime.fromisoformat(published_date)
                            if published_datetime.date() < datetime_module.date.today() - datetime_module.timedelta(days=14):
                                continue

                        soup = BeautifulSoup(entry["summary"], "lxml")
                        for img in soup.find_all("img"):
                            img.decompose()

                        article = Article(
                            title=entry["title"],
                            url=entry["link"],
                            summary=soup.get_text(separator=" ", strip=True),
                            published_date=published_date,
                            authors=entry.get("author", "")
                        )

                        articles.append(asdict(article))
                        
                    except Exception as e:
                        print(f"Error processing NVIDIA article: {e}")
                        continue
                
            except Exception as e:
                print(f"Error parsing NVIDIA RSS feed: {e}")
                
        print(f"Scraped {len(articles)} articles from NVIDIA Dev Blog")
        return articles
