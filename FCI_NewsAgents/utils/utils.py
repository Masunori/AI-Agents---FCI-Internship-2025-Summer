import json
from datetime import datetime, timezone
from typing import List
import os
from FCI_NewsAgents.models.document import Document
from FCI_NewsAgents.core.config import GuardrailsConfig


def get_time():
    current_datetime = datetime.now()
    return current_datetime


def convert_paper_to_document(paper_dict: dict) -> Document:
    """Convert paper dictionary to Document object"""
    # Parse published_date if it's a string
    if isinstance(paper_dict.get('published_date'), str):
        try:
            published_date = datetime.fromisoformat(paper_dict['published_date'].replace('Z', '+00:00'))
        except:
            published_date = datetime.now()
    else:
        published_date = datetime.now()
    
    return Document(
        url=paper_dict.get('url', ''),
        title=paper_dict.get('title', ''),
        summary=paper_dict.get('summary', ''),
        source=paper_dict.get('source', 'arXiv'),
        authors=paper_dict.get('authors', []),
        published_date=published_date,
        content_type="paper"
    )
def mark_used_paper(paper_storage_path, documents: list[Document]):
    try:
        with open(paper_storage_path, 'r', encoding= 'utf-8') as file:
            saved_papers = json.load(file)
        used_urls = set([doc.url for doc in documents])
        updated_counts = 0
        for paper in saved_papers:
            if paper['url'] in used_urls:
                paper['used'] = True
                updated_counts += 1
        with open(paper_storage_path, 'w', encoding='utf-8') as file:
            json.dump(saved_papers, file, indent = 4, ensure_ascii=False, default = str)
        print(f"Marked {updated_counts} papers as used.")
    except Exception as e:
        print(f"Error: {e}")
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

def convert_article_to_document(article_data: dict, source: str = "Article") -> Document:
    """Convert article data to RawDocument format"""
    try:
        if isinstance(article_data.get('published_date'), str):
            published_date = datetime.fromisoformat(article_data['published_date'].replace('Z', '+00:00'))
        else:
            published_date = datetime.now(timezone.utc)
    except Exception as e:
        print(f"Error parsing article date '{article_data.get('published_date')}': {e}")
        published_date = datetime.now(timezone.utc)
    
    # Convert single author string to list format
    authors = [article_data.get('authors', 'Unknown Author')]
    
    return Document(
        url=article_data.get('url', ''),
        title=article_data.get('title', 'Untitled Article'),
        summary=article_data.get('summary', ''),
        source=source,
        authors=authors,
        published_date=published_date,
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