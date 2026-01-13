import datetime as datetime_module
from typing import Any, Dict, List

import dateparser
import feedparser
from bs4 import BeautifulSoup

from FCI_NewsAgents.models.article import Article
from FCI_NewsAgents.services.scrapers.base_scraper import BaseScraper
from FCI_NewsAgents.services.scrapers.registry import register


@register("MITNews")
class MITNewsScraper(BaseScraper):
    """Scraper for MIT News AI articles"""
    
    def __init__(self, rss_url: str = "https://news.mit.edu/topic/mitartificial-intelligence2-rss.xml"):
        self.rss_url = rss_url
    
    def get_name(self) -> str:
        return "MITNews"
    
    def html_to_text(self, html: str) -> str:
        """Convert HTML content to plain text"""
        if not html:
            return ''
        return BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True)
    
    def scrape(self) -> List[Article]:
        """Scrape articles from MIT News RSS feed"""
        print(f"Scraping articles from {self.rss_url}...")
        
        try:
            feed = feedparser.parse(self.rss_url)
            articles = []
            
            for entry in feed.entries:
                try:
                    title = entry.get("title", "").strip()
                    url = entry.get("link") or entry.get("id")
                    
                    # Parse published date
                    published_date = ""
                    if "published" in entry:
                        try:
                            published_date = dateparser.parse(entry.published)
                            published_date = published_date.isoformat()

                            if published_date:
                                # Filter articles older than 14 days
                                pub_date_obj = datetime_module.datetime.fromisoformat(published_date)
                                if pub_date_obj.date() < datetime_module.date.today() - datetime_module.timedelta(days=14):
                                    print(f"Skipping article '{title}' as it is older than 14 days.")
                                    continue
                        except Exception:
                            published_date = ""
                    
                    # Extract authors
                    authors = []
                    if "author" in entry:
                        authors: str | List[str] = entry.author
                    elif "authors" in entry:
                        authors: str | List[str] = [a.get("name") or a.get("email") or str(a) for a in entry.authors]
                    
                    # Extract content
                    content_html = ""
                    if "content" in entry and len(entry.content) > 0:
                        content_html = entry.content[0].value
                    else:
                        content_html = entry.get("summary", "")
                    
                    content_text = self.html_to_text(content_html)

                    article = Article(
                        title=title,
                        url=url,
                        summary=content_text,
                        published_date=published_date,
                        authors=authors,
                        source="MIT News"
                    )

                    articles.append(article)
                    
                except Exception as e:
                    print(f"Error processing MIT article: {e}")
                    continue
            
            print(f"Scraped {len(articles)} articles from MIT News")
            return articles
            
        except Exception as e:
            print(f"Error parsing MIT RSS feed: {e}")
            return []
