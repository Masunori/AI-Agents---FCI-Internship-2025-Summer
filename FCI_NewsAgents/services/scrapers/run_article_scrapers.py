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
from dateutil import parser as dateparser

#parallel 
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import threading
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
                }
                blog_posts.append(blog_post)
                
            except Exception as e:
                print(f"Error processing article: {e}")
                continue
        
        return blog_posts

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
    
    def scrape(self) -> List[Dict[str, Any]]:
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
                    published_date = None
                    if "published" in entry:
                        try:
                            published_date = dateparser.parse(entry.published)
                            published_date = published_date.isoformat()
                        except Exception:
                            published_date = datetime.now().isoformat()
                    else:
                        published_date = datetime.now().isoformat()
                    
                    # Extract authors
                    authors = []
                    if "author" in entry:
                        authors = [entry.author]
                    elif "authors" in entry:
                        authors = [a.get("name") or a.get("email") or str(a) for a in entry.authors]
                    authors_str = ", ".join(authors) if authors else "Unknown"
                    
                    # Extract content
                    content_html = ""
                    if "content" in entry and len(entry.content) > 0:
                        content_html = entry.content[0].value
                    else:
                        content_html = entry.get("summary", "")
                    
                    content_text = self.html_to_text(content_html)
                    
                    article = {
                        'title': title,
                        'url': url,
                        'summary': content_text,
                        'published_date': published_date,
                        'authors': authors_str,
                    }
                    articles.append(article)
                    
                except Exception as e:
                    print(f"Error processing MIT article: {e}")
                    continue
            
            print(f"Scraped {len(articles)} articles from MIT News")
            return articles
            
        except Exception as e:
            print(f"Error parsing MIT RSS feed: {e}")
            return []


# def scrape_articles() -> List[Dict[str, Any]]:
#     """
#     Run all article scrapers and return results as a list
#     """
#     print("Starting article scraping...")
    
#     # Create scrapers
#     scrapers = [
#         NeuronDailyScraper(),
#         TechRepublicScraper(),
#         GoogleResearchScraper(),
#         MITNewsScraper()
#     ]
    
#     # Run all scrapers and collect results
#     all_articles = []
#     for scraper in scrapers:
#         try:
#             if not scraper.is_enabled():
#                 print(f"Skipping {scraper.get_name()} (disabled)")
#                 continue
            
#             print(f"Running {scraper.get_name()} scraper...")
#             articles = scraper.scrape()
            
#             if articles:
#                 print(f"Successfully scraped {len(articles)} articles from {scraper.get_name()}")
#                 all_articles.extend(articles)
#             else:
#                 print(f"No articles found from {scraper.get_name()}")
                
#         except Exception as e:
#             print(f"Error in {scraper.get_name()} scraper: {e}")
#             continue
    
#     print(f"Total articles scraped: {len(all_articles)}")
#     return all_articles

def _run_scraper_safe(scraper: BaseScraper) -> tuple:
    """
    Safely execute a single scraper with error handling.
    
    Args:
        scraper: BaseScraper instance to run
        
    Returns:
        tuple: (scraper_name, articles_list, error_message, duration)
    """
    scraper_name = scraper.get_name()
    thread_name = threading.current_thread().name
    start_time = time.time()
    
    try:
        print(f"[{thread_name}] Starting {scraper_name} scraper...")
        
        if not scraper.is_enabled():
            print(f"[{thread_name}] {scraper_name} is disabled, skipping")
            return (scraper_name, [], "Scraper disabled", 0)
        
        articles = scraper.scrape()
        duration = time.time() - start_time
        
        if articles:
            print(f"[{thread_name}]{scraper_name} completed: {len(articles)} articles in {duration:.2f}s")
            return (scraper_name, articles, None, duration)
        else:
            print(f"[{thread_name}]{scraper_name} completed: 0 articles in {duration:.2f}s")
            return (scraper_name, [], "No articles found", duration)
            
    except Exception as e:
        duration = time.time() - start_time
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"[{thread_name}]  {scraper_name} failed after {duration:.2f}s: {error_msg}")
        return (scraper_name, [], error_msg, duration)


def scrape_articles(parallel: bool = True, max_workers: int = 4) -> List[Dict[str, Any]]:
    """
    Run all article scrapers and return results as a list.
    
    Args:
        parallel: If True, run scrapers in parallel. If False, run sequentially (default: True)
        max_workers: Maximum number of concurrent threads (default: 4)
        
    Returns:
        List of article dictionaries from all scrapers
    """
    print("Starting article scraping...")
    overall_start_time = time.time()
    
    # Create scrapers
    scrapers = [
        NeuronDailyScraper(),
        TechRepublicScraper(),
        GoogleResearchScraper(),
        MITNewsScraper()
    ]
    
    all_articles = []
    scraping_stats = {
        'total_articles': 0,
        'successful_scrapers': 0,
        'failed_scrapers': 0,
        'per_scraper': {}
    }
    
    if parallel:
        print(f"Running {len(scrapers)} scrapers in parallel with {max_workers} workers...")
        
        # Use ThreadPoolExecutor for parallel execution
        with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="Scraper") as executor:
            # Submit all scraper tasks
            future_to_scraper = {
                executor.submit(_run_scraper_safe, scraper): scraper.get_name() 
                for scraper in scrapers
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_scraper):
                scraper_name = future_to_scraper[future]
                
                try:
                    # Get the result (this will re-raise any exception from the thread)
                    name, articles, error, duration = future.result(timeout=300)  # 5 min timeout per scraper
                    
                    # Store statistics
                    scraping_stats['per_scraper'][name] = {
                        'article_count': len(articles),
                        'duration': duration,
                        'error': error,
                        'success': error is None
                    }
                    
                    if error is None:
                        all_articles.extend(articles)
                        scraping_stats['successful_scrapers'] += 1
                        scraping_stats['total_articles'] += len(articles)
                    else:
                        scraping_stats['failed_scrapers'] += 1
                        
                except Exception as e:
                    print(f"✗ Unexpected error retrieving result from {scraper_name}: {e}")
                    scraping_stats['failed_scrapers'] += 1
                    scraping_stats['per_scraper'][scraper_name] = {
                        'article_count': 0,
                        'duration': 0,
                        'error': str(e),
                        'success': False
                    }
    
    else:
        # Sequential execution (original behavior)
        print("Running scrapers sequentially...")
        
        for scraper in scrapers:
            name, articles, error, duration = _run_scraper_safe(scraper)
            
            scraping_stats['per_scraper'][name] = {
                'article_count': len(articles),
                'duration': duration,
                'error': error,
                'success': error is None
            }
            
            if error is None:
                all_articles.extend(articles)
                scraping_stats['successful_scrapers'] += 1
                scraping_stats['total_articles'] += len(articles)
            else:
                scraping_stats['failed_scrapers'] += 1
    
    # Print summary
    total_duration = time.time() - overall_start_time
    print("\n" + "="*60)
    print("SCRAPING SUMMARY")
    print("="*60)
    print(f"Total articles scraped: {scraping_stats['total_articles']}")
    print(f"Successful scrapers: {scraping_stats['successful_scrapers']}/{len(scrapers)}")
    print(f"Failed scrapers: {scraping_stats['failed_scrapers']}/{len(scrapers)}")
    print(f"Total time: {total_duration:.2f}s")
    print(f"Mode: {'PARALLEL' if parallel else 'SEQUENTIAL'}")
    print("="*60 + "\n")
    print("\nPer-scraper details:")
    
    for name, stats in scraping_stats['per_scraper'].items():
        print(f"{name}: {stats['article_count']} articles in {stats['duration']:.2f}s")
        if stats['error']:
            print(f"Error: {stats['error']}")
    
    print("="*60 + "\n")
    return all_articles




if __name__ == "__main__":
    pass