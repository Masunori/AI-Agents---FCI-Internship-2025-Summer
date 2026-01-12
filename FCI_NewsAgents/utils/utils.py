import json
import os
from datetime import datetime, timezone
from enum import IntEnum
from typing import List, Callable, TypeVar, ParamSpec

import requests
from bs4 import BeautifulSoup
from w3lib.url import canonicalize_url

from FCI_NewsAgents.core.config import GuardrailsConfig
from FCI_NewsAgents.models.article import Article
from FCI_NewsAgents.models.document import Document
from FCI_NewsAgents.models.paper import Paper

EMBEDDING_ALIGNMENT_DOMAIN_QUERIES = [
    # Cloud & distributed systems (foundations first, products second)
    "Cloud and distributed systems research including scalability, fault tolerance, virtualization, serverless computing, edge computing, and cloud security.",

    # Systems, hardware, and infrastructure (explicitly research-oriented)
    "Computer systems and infrastructure research including GPUs, TPUs, AI accelerators, high-performance computing, networking, storage systems, and compute optimization.",

    # Core AI research (avoid product language)
    "Artificial intelligence research including deep learning, neural networks, representation learning, computer vision, natural language processing, reasoning, and learning algorithms.",

    # Generative models & LLMs (separate anchor)
    "Large-scale machine learning models including large language models, vision-language models, generative models, multimodal models, and AI agents.",

    # Data systems & data engineering
    "Data engineering and data systems research including data pipelines, distributed data processing, data storage, analytics systems, and real-time data platforms.",

    # Security applied to systems and AI
    "Security research related to cloud systems and artificial intelligence including system security, privacy, robustness, secure computation, and trustworthy machine learning.",

    # AI governance, safety, and regulation (explicitly non-technical allowed)
    "AI safety, governance, and policy topics including responsible AI, AI regulation, risk management, compliance, and societal impacts of AI systems.",
]


class DocumentDomain(IntEnum):
    CLOUD_COMPUTING = 0
    SYSTEMS_INFRASTRUCTURE = 1
    CORE_ARTIFICIAL_INTELLIGENCE = 2
    GENERATIVE_MODELS_LLMs = 3
    DATA_ENGINEERING_BIG_DATA = 4
    CYBERSECURITY = 5
    AI_SAFETY_GOVERNANCE_REGULATIONS = 6

def get_time():
    current_datetime = datetime.now()
    return current_datetime

def convert_paper_to_document(paper: Paper) -> Document:
    """Convert Paper to Document object"""
    
    return Document(
        url=paper.url,
        title=paper.title,
        summary=paper.summary,
        source=paper.source,
        authors=paper.authors,
        published_date=datetime.fromisoformat(paper.published_date),
        content_type="paper"
    )

def parse_twitter_date(date_string: str) -> datetime:
    """Parse Twitter date format: 'Sun Aug 17 16:03:02 +0000 2025'"""
    try:
        # Handle Twitter's date format
        if '+0000' in date_string:
            # Remove timezone info and parse
            clean_date = date_string.replace(' +0000', '')
            # Parse format like "Sun Aug 17 16:03:02 2025"
            parsed_date = datetime.strptime(clean_date, '%a %b %d %H:%M:%S %Y')
            # Set timezone to UTC
            return parsed_date.replace(tzinfo=timezone.utc)
        elif 'T' in date_string:
            # Handle ISO format if present
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        else:
            # Fallback to current time
            return datetime.now(timezone.utc)
    except Exception as e:
        print(f"Error parsing date '{date_string}': {e}")
        return datetime.now(timezone.utc)

def convert_tweet_to_document(tweet_data: dict, source: str = "Twitter") -> Document:
    """Convert tweet data to RawDocument format"""
    # Parse the Twitter date format properly
    created_at = parse_twitter_date(tweet_data.get('created_at', ''))
    
    return Document(
        url=f"https://twitter.com/user/status/{tweet_data['id']}",
        title=f"Tweet by @{tweet_data['user']}",
        summary=tweet_data['text'],
        source=source,
        authors=[tweet_data['user']],
        published_date=created_at,
        content_type="tweet"
    )

def convert_article_to_document(article_data: Article, source: str = "Article") -> Document:
    """Convert article data to RawDocument format"""
    
    return Document(
        url=article_data.url,
        title=article_data.title,
        summary=article_data.summary,
        source=source,
        authors=[article_data.authors] if isinstance(article_data.authors, str) else article_data.authors,
        published_date=datetime.fromisoformat(article_data.published_date),
        content_type="article"
    )


# def scrape_tweets_by_usernames(x_scraped_list_path: str, config: GuardrailsConfig) -> List[Document]:
#     """Scrape tweets from usernames listed in x_scrapelist.json"""
#     tweet_documents = []
    
#     if not os.path.exists(x_scraped_list_path):
#         print(f"Twitter username list file not found: {x_scraped_list_path}")
#         return tweet_documents
    
#     try:
#         with open(x_scraped_list_path, 'r', encoding='utf-8') as f:
#             scrape_data = json.load(f)
        
#         # Handle the array structure from x_scrapelist.json
#         if isinstance(scrape_data, list) and len(scrape_data) > 0:
#             # Get the first object in the array
#             data_obj = scrape_data[0]
#             usernames = data_obj.get('users_list', [])
#         else:
#             print("Invalid format in x_scrapelist.json")
#             return tweet_documents
        
#         print(f"Found {len(usernames)} usernames to scrape")
        
#         for username in usernames:
#             try:
#                 print(f"Scraping tweets from @{username}...")
#                 tweets_result = fetch_tweets_by_username(username, config.MAX_TWEETS_PER_USER)
                
#                 if tweets_result['success'] and tweets_result['tweets']:
#                     for tweet in tweets_result['tweets']:
#                         tweet_doc = convert_tweet_to_document(tweet, "Twitter_Username")
#                         tweet_documents.append(tweet_doc)
#                     print(f"Successfully scraped {len(tweets_result['tweets'])} tweets from @{username}")
#                 else:
#                     print(f"Failed to scrape tweets from @{username}: {tweets_result.get('error', 'Unknown error')}")
                    
#             except Exception as e:
#                 print(f"Error scraping tweets from @{username}: {e}")
                
#     except Exception as e:
#         print(f"Error reading username list: {e}")
    
#     return tweet_documents

# def scrape_tweets_by_urls(url_list: List[str]) -> List[Document]:
#     """Scrape tweets from URLs"""
#     tweet_documents = []
    
#     for url in url_list:
#         try:
#             print(f"Scraping tweet from URL: {url}")
#             tweet_result = extracting_tweet_info(url)
            
#             if tweet_result['success'] and tweet_result['tweets']:
#                 for tweet in tweet_result['tweets']:
#                     tweet_doc = convert_tweet_to_document(tweet, "Twitter_URL")
#                     tweet_documents.append(tweet_doc)
                
#                 # Handle quoted tweets if any
#                 if 'quoted_tweets' in tweet_result:
#                     for quoted_tweet in tweet_result['quoted_tweets']:
#                         quoted_doc = convert_tweet_to_document(quoted_tweet, "Twitter_Quoted")
#                         tweet_documents.append(quoted_doc)
                        
#                 print(f"Successfully scraped tweet from URL: {url}")
#             else:
#                 print(f"Failed to scrape tweet from URL {url}: {tweet_result.get('error', 'Unknown error')}")
                
#         except Exception as e:
#             print(f"Error scraping tweet from URL {url}: {e}")
    
#     return tweet_documents

# def get_tweet_urls(x_scraped_list_path: str) -> List[str]:
#     """Get tweet URLs from x_scrapelist.json"""
#     tweet_urls = []
    
#     if not os.path.exists(x_scraped_list_path):
#         print(f"Twitter config file not found: {x_scraped_list_path}")
#         return tweet_urls
    
#     try:
#         with open(x_scraped_list_path, 'r', encoding='utf-8') as f:
#             scrape_data = json.load(f)
        
#         # Handle the array structure from x_scrapelist.json
#         if isinstance(scrape_data, list) and len(scrape_data) > 0:
#             # Get the first object in the array
#             data_obj = scrape_data[0]
#             tweet_urls = data_obj.get('post_urls', [])
#         else:
#             print("Invalid format in x_scrapelist.json")
    
#     except Exception as e:
#         print(f"Error reading tweet URLs: {e}")
    
#     return tweet_urls

def save_report(report: str, output_path: str = "ai_news_report.md"):
    '''Save the final report to a markdown file'''
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

def clean_url(url: str) -> str:
    """
    Clean up the URL by removing unwanted characters.
    
    Args:
        url (str): The original URL.
        
    Returns:
        str: The cleaned URL.
    """
    url = url.strip() # Remove leading/trailing whitespace
    url = url.replace('\n', '') # Remove newlines
    url = url.replace('\r', '') # Remove carriage returns
    url = url.replace(' ', '') # Remove spaces
    url = url.replace('\t', '') # Remove tabs
    return url

def get_canonical_url(url: str) -> str:
    """
    Get the canonical URL.
    
    Args:
        url (str): The original URL.
        
    Returns:
        str: The canonical URL.
    """
    # Clean up the URL
    url = clean_url(url)

    try:
        print(f"Fetching canonical URL for: {url} ...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
        }

        # Final URL after redirects
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        final_url = response.url

        content_type = response.headers.get('Content-Type', '')
        if 'text/html' not in content_type:
            print(f"==> Non-HTML content type ({content_type}) for URL: {final_url}. Using final URL as canonical.")
            return canonicalize_url(final_url)

        # Parse HTML to find canonical link
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, 'html.parser')
        canonical_link = soup.find('link', rel='canonical')

        if canonical_link and canonical_link.get('href'):
            canonical_url = canonical_link['href']
        else:
            canonical_url = final_url

        # Normalize the canonical URL
        print(f"==> Canonical URL found: {canonical_url}")
        return canonicalize_url(canonical_url)

    except Exception as e:
        if isinstance(e, requests.RequestException):
            print(f"==> Error fetching canonical URL for {url}: {e}")
            return canonicalize_url(url)
        else:
            print(f"==> Unexpected error processing URL {url}: {e}")
            raise e

R = TypeVar("R")
P = ParamSpec("P")

def run_with_retry(
    fn: Callable[P, R], 
    max_retries: int = 3, 
    on_exception: Callable[[Exception, int], None] = lambda e, attempt: None,
    *args: P.args, 
    **kwargs: P.kwargs
) -> R:
    """
    Run a function with retries on exception.

    Args:
        fn (Callable[P, R]): The function to run.
        max_retries (int): Maximum number of retries. Defaults to 3.
        on_exception (Callable[[Exception, int], None]): Callback on exception with the exception and attempt number. Can be used for logging.
        *args: Positional arguments for the function.
        **kwargs: Keyword arguments for the function.

    Returns:
        R: The return value of the function if successful.

    Raises:
        Exception: The last exception raised if all retries fail.
    """
    attempt = 0
    while attempt < max_retries:
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            attempt += 1
            on_exception(e, attempt)
            if attempt == max_retries:
                print("Max retries reached. Raising exception.")
                raise e