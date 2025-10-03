import json
import os
import sys
from datetime import datetime
from pathlib import Path
from abc import ABC, abstractmethod
from typing import List, Dict, Any

# Additional imports for scrapers
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import feedparser
import time
from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Add current directory to path for local imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))



class BaseScraper(ABC):
    """Base class for all article scrapers"""
    
    @abstractmethod
    def get_name(self) -> str:
        """Return the name of this scraper"""
        pass
    
    @abstractmethod
    def scrape(self) -> List[Dict[str, Any]]:
        """Scrape articles and return them as a list of dictionaries"""
        pass
    
    def is_enabled(self) -> bool:
        """Check if this scraper is enabled (override in subclass if needed)"""
        return True

#If you want to add new scraper, just inherit the BaseScraper class, below are some examples:

class NeuronDailyScraper(BaseScraper):
    """Scraper for NeuronDaily articles"""
    
    def __init__(self, base_url: str = "https://www.theneurondaily.com"):
        self.base_url = base_url
    
    def get_name(self) -> str:
        return "NeuronDaily"
    
    def get_datetime(self, date_string: str) -> str:
        """Converts a 'Month Day, Year' string to an ISO format string (JSON serializable)."""
        dt = datetime.strptime(date_string, "%B %d, %Y")
        return dt.isoformat()
    
    def get_article_text(self, url: str) -> tuple:
        """
        Fetches an article's webpage and extracts the text content from its <p> tags.
        Returns (authors, date, full_text)
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
        except Exception as e:
            print(f"Error extracting metadata from {url}: {e}")
            authors, date = "Unknown", "January 1, 2024"
        
        article_body = soup.find("div", attrs={"id": "content-blocks"})

        if not article_body:
            print(f"Could not find the main article body using the selector 'div[id=\"content-blocks\"]' on {url}")
            return authors, date, ""

        paragraphs = article_body.find_all("p")
        
        full_text = "\n\n".join(p.get_text(strip=True) for p in paragraphs)
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
                    news_list.append({
                        'title': title,
                        'url': full_url,
                        'summary': content,
                        "published_date": self.get_datetime(date),
                        "authors": authors,
                        "used": False 
                    })
                except Exception as e:
                    print(f"Error processing article {full_url}: {e}")
                    continue

        return news_list


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
            authors_str = ", ".join(authors) if authors else "Unknown"
            
            # Convert published_date to ISO format if available
            if published_date:
                try:
                    # Parse the datetime and convert to ISO format
                    dt = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
                    published_date = dt.isoformat()
                except Exception as e:
                    print(f"Error parsing date {published_date}: {e}")
                    published_date = datetime.now().isoformat()
            else:
                published_date = datetime.now().isoformat()

            article_data = {
                "url": url,
                "authors": authors_str,
                "published_date": published_date,
                "summary": content_text,
                "used" : False
            }

            return article_data

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


class GoogleResearchScraper(BaseScraper):
    """Scraper for Google Research Blog articles"""
    
    def __init__(self, base_url: str = "https://research.google"):
        self.base_url = base_url
        self.blog_url = f"{base_url}/blog/"
    
    def get_name(self) -> str:
        return "GoogleResearch"
    
    def get_content(self, blog_path: str) -> Dict[str, Any]:
        """Extract content from a Google Research blog post"""
        full_url = self.base_url + blog_path
        
        try:
            response = requests.get(full_url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching article content from {full_url}: {e}")
            return {"published_date": "UNK", "authors": "UNK", "summary": ""}
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract blog details (date and authors)
        blog_details = soup.find("div", attrs={"class": "basic-hero--blog-detail__description"})
        if blog_details:
            blog_details_text = [p.get_text(strip=True) for p in blog_details.find_all("p")]
            if len(blog_details_text) == 2:
                published_date, authors = blog_details_text
            else:
                published_date, authors = "UNK", "UNK"
        else:
            published_date, authors = "UNK", "UNK"
        
        # Extract all paragraph text as summary
        p_tags = soup.find_all("p")
        summary = "\n".join(p.get_text(strip=True) for p in p_tags)
        
        # Convert date to ISO format if possible
        if published_date != "UNK":
            try:
                dt = datetime.strptime(published_date, "%B %d, %Y")
                published_date = dt.isoformat()
            except ValueError:
                # If date parsing fails, use current date
                published_date = datetime.now().isoformat()
        else:
            published_date = datetime.now().isoformat()
        
        return {
            'published_date': published_date,
            'authors': authors,
            'summary': summary
        }
    
    def scrape(self) -> List[Dict[str, Any]]:
        """Scrape articles from Google Research Blog"""
        print(f"Scraping articles from {self.blog_url}...")
        
        try:
            response = requests.get(self.blog_url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching URL: {e}")
            return []
        
        soup = BeautifulSoup(response.text, "html.parser")
        a_tags = soup.find_all("a", attrs={"class": "glue-card not-glue"})
        
        blog_posts = []
        for a_tag in a_tags:
            try:
                # Get the blog path from href (e.g., "/blog/article-name")
                blog_path = a_tag.get("href")
                if not blog_path:
                    continue
                
                # Get title
                title_element = a_tag.find("span", attrs={"class": "headline-5 js-gt-item-id"})
                if not title_element:
                    continue
                title = title_element.get_text(strip=True)
                
                # Get content details
                content = self.get_content(blog_path)
                
                blog_post = {
                    'title': title,
                    'url': f"{self.base_url}{blog_path}",
                    'summary': content['summary'],
                    'published_date': content['published_date'],
                    'authors': content['authors'],
                    'used': False
                }
                blog_posts.append(blog_post)
                
            except Exception as e:
                print(f"Error processing article: {e}")
                continue
        
        return blog_posts



def scrape_articles() -> List[Dict[str, Any]]:
    """
    Run all article scrapers and return results as a list
    """
    print("Starting article scraping...")
    
    # Create scrapers
    scrapers = [
        NeuronDailyScraper(),
        TechRepublicScraper(),
        GoogleResearchScraper()
    ]
    
    # Run all scrapers and collect results
    all_articles = []
    for scraper in scrapers:
        try:
            if not scraper.is_enabled():
                print(f"Skipping {scraper.get_name()} (disabled)")
                continue
            
            print(f"Running {scraper.get_name()} scraper...")
            articles = scraper.scrape()
            
            if articles:
                print(f"Successfully scraped {len(articles)} articles from {scraper.get_name()}")
                all_articles.extend(articles)
            else:
                print(f"No articles found from {scraper.get_name()}")
                
        except Exception as e:
            print(f"Error in {scraper.get_name()} scraper: {e}")
            continue
    
    print(f"Total articles scraped: {len(all_articles)}")
    return all_articles


if __name__ == "__main__":
    pass