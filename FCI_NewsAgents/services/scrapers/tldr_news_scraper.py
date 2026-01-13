import datetime as datetime_module
from typing import Any, Dict, List
import re

import feedparser
from bs4 import BeautifulSoup

from FCI_NewsAgents.models.article import Article
from FCI_NewsAgents.services.scrapers.base_scraper import BaseScraper
from FCI_NewsAgents.services.scrapers.registry import register


@register("TLDRNews")
class TLDRNewsScraper(BaseScraper):
    """Scraper for TLDR News articles"""
    
    def __init__(self, rss_url: str = "https://tldr.tech/"):
        self.rss_url = rss_url


        # Because of timezone, the latest available articles are "from 1-2 day(s) ago".
        self.__rss_urls_to_days_ago = {
            "https://tldr.tech/ai/": 1,
            "https://tldr.tech/data/": 2,
            # "https://tldr.tech/devops/": 2,
            # "https://tldr.tech/infosec/": 1,
            # "https://tldr.tech/dev/": 1,
        }
    
    def get_name(self) -> str:
        return "TLDRNews"
    
    def strip_read_time(self, title: str) -> str:
        """
        Strip 'X min read' from the given title

        Args:
            title (str): The article title of format "Some Title (xx min read)"
        Returns:
            str: The title without the read time.
        """
        return re.sub(r"\s*\(\d+\s+minutes?\s+read\)\s*$", "", title)
    
    def scrape(self) -> List[Article]:
        """Scrape articles from TLDR News RSS feed"""
        article_list: List[Article] = []

        for rss_url, days_ago in self.__rss_urls_to_days_ago.items():
            ytd_str = (datetime_module.date.today() - datetime_module.timedelta(days=days_ago)).strftime("%Y-%m-%d")
            url = f"{rss_url}{ytd_str}"

            print(f"Scraping articles from {url}...")

            try:
                feed = feedparser.parse(url)
                soup = BeautifulSoup(feed['feed']['summary'], 'html.parser')

                articles = soup.find_all('article')

                for article_div in articles:
                    try:
                        anchor = article_div.find('a')
                        title = anchor.get_text(strip=True)
                        url = anchor['href']
                        summary_div = article_div.select_one('div.newsletter-html')
                        summary = summary_div.get_text(separator="\n", strip=True) if summary_div else "No summary available."

                        article = Article(
                            title=self.strip_read_time(title),
                            url=url,
                            summary=summary,
                            published_date="",
                            authors="",
                            source="TLDR News"
                        )

                        article_list.append(article)
                    except Exception as e:
                        print(f"Error processing TLDR article: {e}")
                        continue

            except Exception as e:
                print(f"Error parsing TLDR RSS feed: {e}")
    
        print(f"Scraped {len(article_list)} articles from TLDR News")
        return article_list
