import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List

# Add current directory to path for local imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from FCI_NewsAgents.services.scrapers.base_scraper import BaseScraper
from FCI_NewsAgents.services.scrapers.registry import SCRAPERS
from FCI_NewsAgents.services.scrapers.mit_news_scraper import MITNewsScraper


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


def scrape_articles(parallel: bool = True, max_workers: int = -1) -> List[Dict[str, Any]]:
    """
    Run all article scrapers and return results as a list.

    If `max_workers` is -1, use 1 worker per scraper, capped at 16 workers. `max_workers` is ignored if `parallel` is False.
    
    Args:
        parallel: If True, run scrapers in parallel. If False, run sequentially (default: True)
        max_workers: Maximum number of concurrent threads (default: -1)
        
    Returns:
        List of article dictionaries from all scrapers
    """
    print("Starting article scraping...")
    overall_start_time = time.time()

    # scrapers = [scraper_cls() for scraper_cls in SCRAPERS.values()]
    scrapers = [MITNewsScraper()]

    if max_workers == -1:
        max_workers = min(len(scrapers), 16)
    
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