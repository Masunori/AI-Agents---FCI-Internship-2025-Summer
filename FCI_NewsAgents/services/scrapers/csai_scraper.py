import json
import os
import time
from typing import List, Literal

import feedparser
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from FCI_NewsAgents.models.paper import Paper
from FCI_NewsAgents.utils.utils import run_with_retry


def scrape_arxiv_cs_ai(max_results=10, sort_by: Literal["relevance", "lastUpdatedDate", "submittedDate"]="submittedDate", batch_size=10) -> List[Paper]:
    """
    Scrape arXiv papers from the cs.AI category.
    
    Parameters:
        max_results (int): Number of results to fetch.
        sort_by (Literal["relevance", "lastUpdatedDate", "submittedDate"]): The sorting criteria for the results.
        batch_size (int): Number of results to fetch per request. Defaults to 10.
    
    Returns:
        List[Paper]: List of Paper objects containing paper metadata.
    """
    base_url = "http://export.arxiv.org/api/query?"
    query = f"cat:cs.AI"

    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=1.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))

    headers = {
        "User-Agent": "FCI_NewsAgents/1.0 (ducdm67@fpt.com)"
    }

    papers: List[Paper] = []
    fetched = 0

    def fetch_and_parse_batch(start: int, max_results: int) -> List[Paper]:
        params = {
            "search_query": query,
            "start": start,
            "max_results": max_results,
            "sortBy": sort_by
        }

        response = requests.get(
            url=base_url, 
            headers=headers, 
            params=params, 
            timeout=(5, 30) # connect timeout, read timeout
        )

        feed = feedparser.parse(response.text)
        batch_papers: List[Paper] = []

        for entry in feed.entries:
            paper = Paper(
                url=next((link.href for link in entry.links if link.type == "application/pdf"), ""),
                title=entry.title,
                summary=entry.summary,
                source="arXiv cs.AI",
                authors=[author.name for author in entry.authors],
                published_date=entry.published,
            )

            batch_papers.append(paper)

        return batch_papers
    
    def on_exception(e: Exception, attempt: int):
        print(f"Exception on attempt {attempt} while fetching arXiv data: {e}")

    while fetched < max_results:
        current_batch = min(batch_size, max_results - fetched)

        try:
            batch_papers = run_with_retry(
                fn=lambda: fetch_and_parse_batch(start=fetched, max_results=current_batch),
                max_retries=3,
                on_exception=on_exception
            )
            papers.extend(batch_papers)
        except Exception as e:
            print(f"Failed to fetch batch starting at {fetched}: {e}")
            break

        fetched += len(batch_papers)
        time.sleep(3)  # Respect arXiv's rate limits

    return papers
 
def scrape_papers(max_results=50) -> List[Paper]:
    """
    Scrape arXiv papers.

    Parameters:
        max_results (int): Number of results to fetch.

    Returns:
        List[Paper]: List of Paper objects containing paper metadata.
    """
    print(f"Scraping {max_results} papers from arXiv cs.AI...")
    papers = scrape_arxiv_cs_ai(max_results=max_results, sort_by="submittedDate")
    print(f"Successfully scraped {len(papers)} papers")
    return papers
    



