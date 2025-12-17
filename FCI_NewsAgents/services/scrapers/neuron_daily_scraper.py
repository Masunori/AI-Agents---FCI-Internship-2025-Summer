import datetime as datetime_module
from typing import Any, Dict, List, Tuple
import requests

from bs4 import BeautifulSoup
from urllib.parse import urljoin
from dataclasses import asdict

from FCI_NewsAgents.services.scrapers.base_scraper import BaseScraper
from FCI_NewsAgents.services.scrapers.scraper_utils import Article
from FCI_NewsAgents.services.scrapers.registry import register


@register("NeuronDaily")
class NeuronDailyScraper(BaseScraper):
    """Scraper for NeuronDaily articles"""
    
    def __init__(self, base_url: str = "https://www.theneurondaily.com"):
        self.base_url = base_url
    
    def get_name(self) -> str:
        return "NeuronDaily"
    
    def get_datetime(self, date_string: str) -> str:
        """Converts a 'Month Day, Year' string to an ISO format string (JSON serializable)."""
        dt = datetime_module.datetime.strptime(date_string, "%B %d, %Y")
        return dt.isoformat()
    
    def get_article_text(self, url: str) -> Tuple[str, str, str]:
        """
        Fetches an article's webpage and extracts the text content from its <p> tags.

        Args:
            url (str): The URL of the article to scrape.
        Returns:
            Tuple[str, str, str]: A tuple containing the authors, published date, and full text content of the article.
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching article content from {url}: {e}")
            return "", "", ""

        soup = BeautifulSoup(response.text, "html.parser")

        try:
            postheader_body = soup.find("div", attrs={"class": "bh__byline_wrapper"})
            postheader_text = postheader_body.find_all("span")
            # this postheader has two span class, the first one is the author name, the second one is the datetime
            authors, date = [p.get_text(strip=True) for p in postheader_text]
            date = self.get_datetime(date)
        except Exception as e:
            print(f"Error extracting metadata from {url}: {e}")
            authors, date = "", ""
        
        article_body = soup.find("div", attrs={"id": "content-blocks"})

        if not article_body:
            print(f"Could not find the main article body using the selector 'div[id=\"content-blocks\"]' on {url}")
            return authors, date, ""

        paragraphs = article_body.find_all("p")
        
        full_text = "\n\n".join(p.get_text(strip=True) for p in paragraphs)

        print(f"Author: {authors}, Date: {date}, Content length: {len(full_text)} characters")
        return authors, date, full_text
    
    def scrape(self) -> List[Dict[str, Any]]:
        """Scrape articles from NeuronDaily"""
        print(f"Scraping articles from {self.base_url}...")
        
        # Standard headers to mimic a browser, avoid blocking from the web
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        try:
            response = requests.get(self.base_url, headers=headers, timeout=10)
            response.raise_for_status() 
        except requests.RequestException as e:
            print(f"Error fetching URL: {e}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        # Find all 'a' tags that act as containers for the articles.
        # The attribute 'data-discover' 
        article_links = soup.find_all("a", attrs={'data-discover': "true"})
        
        news_list = []
        for link_tag in article_links:
            # Find the h2 tag within the current 'a' tag
            title_tag = link_tag.find("h2")
            
            # Ensure both the title and href exist before processing
            if title_tag and link_tag.has_attr('href'):
                # Extract the text from the h2 tag
                title = title_tag.get_text(strip=True)
                
                # Extract the relative path from the 'href' attribute
                relative_href = link_tag['href']
                
                # Create a full, absolute URL
                full_url = urljoin(self.base_url, relative_href)
                
                try:
                    authors, date, content = self.get_article_text(full_url)

                    if date:
                        # Filter articles older than 14 days
                        article_date = datetime_module.datetime.fromisoformat(date)
                        if article_date.date() < datetime_module.date.today() - datetime_module.timedelta(days=14):
                            print(f"Skipping article '{title}' as it is older than 14 days.")
                            break # articles are in descending order, so we can stop here

                    article = Article(
                        url=full_url,
                        title=title,
                        summary=content,
                        published_date=date,
                        authors=authors,
                    )
                    news_list.append(asdict(article))

                    print(f"Successfully scraped: {title}")
                except Exception as e:
                    print(f"Error processing article {full_url}: {e}")
                    continue

        return news_list