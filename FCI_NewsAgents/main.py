import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from FCI_NewsAgents.services.scrapers.csai_scraper import scrape_papers
from FCI_NewsAgents.services.scrapers.run_article_scrapers import scrape_articles
from FCI_NewsAgents.utils.utils import (
    convert_article_to_document,
    convert_paper_to_document,
)
from FCI_NewsAgents.services.parsers.cs_ai_parser import extract_text_from_paper
from FCI_NewsAgents.services.parsers.web_article_parser import (
    extract_text_from_web_article,
)
from FCI_NewsAgents.workflows.workflow_builder import workflow_execution
# from FCI_NewsAgents.services.llm.llm_interface import call_llm
from FCI_NewsAgents.services.article_url_cache.store import ArticleURLStore
from FCI_NewsAgents.utils.report_generator_utils import *
from FCI_NewsAgents.utils.doc_benchmark import RELEVANT_DOCS_AI 
from FCI_NewsAgents.prompts.get_prompts import (
    get_generation_prompt,
)

if __name__ == "__main__":
    # print(fn())

    output_folder = r"FCI_NewsAgents\workflow_output"
    
    overall_start = time.time()
    
    # Scrape articles (now parallel internally)
    print("="*50)
    print("SCRAPING ARTICLES")
    print("="*50)
    article_dicts = scrape_articles(parallel=True)
    articles = [convert_article_to_document(a) for a in article_dicts]
    
    # Scrape papers
    print("\n" + "="*50)
    print("SCRAPING PAPERS")
    print("="*50)
    paper_dicts = scrape_papers(max_results=50)
    papers = [convert_paper_to_document(p) for p in paper_dicts]

    print(f"\nTotal articles scraped: {len(articles)}")
    print(f"Total papers scraped: {len(papers)}")
    
    # Run workflow
    print("\n" + "="*50)
    print("RUNNING WORKFLOW")
    print("="*50)
    workflow_execution(papers=papers, articles=articles, output_folder=output_folder)
    
    total_time = time.time() - overall_start
    print(f"\nTotal execution time of the workflow: {total_time:.2f}s")
