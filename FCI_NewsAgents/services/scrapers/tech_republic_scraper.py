import datetime as datetime_module
from dataclasses import asdict
from typing import Any, Dict, List

import feedparser
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium_stealth import stealth

from FCI_NewsAgents.services.scrapers.base_scraper import BaseScraper
from FCI_NewsAgents.models.article import Article
from FCI_NewsAgents.services.scrapers.registry import register


@register("TechRepublic")
class TechRepublicScraper(BaseScraper):
    """Scraper for TechRepublic articles"""
    
    def __init__(self, rss_url: str = "https://www.techrepublic.com/rssfeeds/topic/artificial-intelligence/"):
        self.rss_url = rss_url
    
    def get_name(self) -> str:
        return "TechRepublic"
    
    def get_content(self, url: str) -> Dict[str, Any]:
        """Extract content from a TechRepublic article URL"""
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        driver = webdriver.Chrome(options=options)

        # Apply stealth
        stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )

        driver.get(url)

        try:
            # wait until article loads
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "article"))
            )

            soup = BeautifulSoup(driver.page_source, "html.parser")

            # === extract metadata ===
            authors = [span.get_text(strip=True) for span in soup.select('span[property="name"]')]
            published_date = soup.select_one('time[property="datePublished"]')
            published_date = published_date.get("datetime") if published_date else None

            # === extract article body in order ===
            article = soup.select_one("article, div.article-content, section.article-body")
            content_parts = []
            if article:
                for elem in article.find_all(["p", "h2", "div"], recursive=True):
                    if elem.name == "p" and elem.get_text(strip=True):
                        content_parts.append(elem.get_text(strip=True))
                    elif elem.name == "h2" and elem.get_text(strip=True):
                        content_parts.append(elem.get_text(strip=True))
                    elif elem.name == "div" and "article-summary" in elem.get("class", []):
                        content_parts.append(elem.get_text(strip=True))

            # Join all text content into paragraphs
            content_text = "\n\n".join(content_parts)

            # Convert authors list to string
            authors_str = ", ".join(authors) if authors else ""
            
            # Convert published_date to ISO format if available
            if published_date:
                try:
                    # Parse the datetime and convert to ISO format
                    dt = datetime_module.datetime.strptime(published_date, "%B %d, %Y")
                    published_date = dt.isoformat()
                except Exception as e:
                    print(f"Error parsing date {published_date}: {e}")
                    published_date = ""
            else:
                published_date = ""

            article_data = Article(
                url=url,
                authors=authors_str,
                published_date=published_date,
                summary=content_text,
            )

            return asdict(article_data)

        except Exception as e:
            print("Error extracting content:", e)
            return None
        finally:
            driver.quit()
    
    def scrape(self) -> List[Dict[str, Any]]:
        """Scrape articles from TechRepublic RSS feed"""
        print(f"Scraping articles from {self.rss_url}...")
        
        articles = []
        
        try:
            feed = feedparser.parse(self.rss_url)
            
            for entry in feed.entries:
                try:
                    print(f"Scraping article: {entry.title}")
                    article_data = self.get_content(entry.link)

                    if article_data:
                        published_date_str = article_data.get('published', '')

                        if published_date_str:
                            published_date = datetime_module.datetime.fromisoformat(published_date_str).date()
                            if published_date < datetime_module.date.today() - datetime_module.timedelta(days=14):
                                print(f"Skipping article '{entry.title}' as it is older than 14 days.")
                                continue

                        article_data["title"] = entry.title
                        articles.append(article_data)
                        print(f"Successfully scraped: {entry.title}")
                except Exception as e:
                    print(f"Error scraping article {entry.link}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error parsing RSS feed: {e}")
            return []
        
        print(f"Scraped {len(articles)} articles")
        return articles
