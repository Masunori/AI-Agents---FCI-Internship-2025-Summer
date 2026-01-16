import os
import sys
import time
import argparse

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from FCI_NewsAgents.services.scrapers.csai_scraper import scrape_papers
from FCI_NewsAgents.services.scrapers.run_article_scrapers import scrape_articles
from FCI_NewsAgents.utils.utils import (
    convert_article_to_document,
    convert_paper_to_document,
)
from FCI_NewsAgents.workflows.workflow_builder import workflow_execution


parser = argparse.ArgumentParser(description="Run the FCI News Agents workflow.")
parser.add_argument("--md-path", type=str, required=False, default=r"FCI_NewsAgents\workflow_output\md", help="Path to save markdown output files.")
parser.add_argument("--pdf-path", type=str, required=False, default=r"FCI_NewsAgents\workflow_output\pdf", help="Path to save PDF output files.")
args = parser.parse_args()

if __name__ == "__main__":
    output_folder_md = args.md_path
    output_folder_pdf = args.pdf_path

    overall_start = time.time()

    # Scrape articles (now parallel internally)
    print("=" * 50)
    print("SCRAPING ARTICLES")
    print("=" * 50)
    article_dicts = scrape_articles(parallel=True)
    articles = [convert_article_to_document(a) for a in article_dicts]

    # Scrape papers
    print("\n" + "=" * 50)
    print("SCRAPING PAPERS")
    print("=" * 50)
    paper_dicts = scrape_papers(max_results=50)
    papers = [convert_paper_to_document(p) for p in paper_dicts]

    print(f"\nTotal articles scraped: {len(articles)}")
    print(f"Total papers scraped: {len(papers)}")

    # Run workflow
    print("\n" + "=" * 50)
    print("RUNNING WORKFLOW")
    print("=" * 50)
    workflow_execution(
        papers=papers, 
        articles=articles, 
        output_folder_md=output_folder_md,
        output_folder_pdf=output_folder_pdf
    )

    total_time = time.time() - overall_start
    print(f"\nTotal execution time of the workflow: {total_time:.2f}s")
