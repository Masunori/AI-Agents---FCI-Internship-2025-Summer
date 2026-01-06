import datetime as datetime_module
from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup

from FCI_NewsAgents.models.article import Article
from FCI_NewsAgents.services.scrapers.base_scraper import BaseScraper
from FCI_NewsAgents.services.scrapers.registry import register


@register("GoogleResearch")
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
            return {"published_date": "", "authors": "", "summary": ""}
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract blog details (date and authors)
        blog_details = soup.find("div", attrs={"class": "basic-hero--blog-detail__description"})
        if blog_details:
            blog_details_text = [p.get_text(strip=True) for p in blog_details.find_all("p")]
            if len(blog_details_text) == 2:
                published_date, authors = blog_details_text
            else:
                published_date, authors = "", ""
        else:
            published_date, authors = "", ""
        
        # Extract all paragraph text as summary
        p_tags = soup.find_all("p")
        summary = "\n".join(p.get_text(strip=True) for p in p_tags)
        
        # Convert date to ISO format if possible
        if published_date != "":
            try:
                dt = datetime_module.datetime.strptime(published_date, "%B %d, %Y")
                published_date = dt.isoformat()
            except ValueError:
                published_date = ""
        
        return {
            'published_date': published_date,
            'authors': authors,
            'summary': summary
        }
    
    def scrape(self) -> List[Article]:
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
        
        blog_posts: List[Article] = []
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

                published_date = content['published_date']

                if published_date:
                    # Filter articles older than 14 days
                    article_date = datetime_module.datetime.fromisoformat(published_date)
                    if article_date.date() < datetime_module.date.today() - datetime_module.timedelta(days=14):
                        print(f"Skipping article '{title}' as it is older than 14 days.")
                        continue

                article = Article(
                    title=title,
                    url=f"{self.base_url}{blog_path}",
                    summary=content['summary'],
                    published_date=published_date,
                    authors=content['authors'],
                )
                
                blog_posts.append(article)
                
            except Exception as e:
                print(f"Error processing article: {e}")
                continue
        
        return blog_posts
