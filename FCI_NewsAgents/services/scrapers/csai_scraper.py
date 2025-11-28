import requests
import feedparser
import json
import os
def scrape_arxiv_cs_ai(max_results=10, sort_by="submittedDate"):
    """
    Scrape arXiv papers from the cs.AI category.
    
    Parameters:
        max_results (int): Number of results to fetch.
        sort_by (str): One of ["relevance", "lastUpdatedDate", "submittedDate"].
                       Default = "submittedDate" (newest first).
    
    Returns:
        List of dictionaries containing paper metadata.
    """
    base_url = "http://export.arxiv.org/api/query?"
    query = f"cat:cs.AI"
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": sort_by
    }
    query_str = "&".join([f"{k}={v}" for k, v in params.items()])
    url = base_url + query_str

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    feed = feedparser.parse(response.text)
    papers = []

    for entry in feed.entries:
        paper = {
            "url": next((link.href for link in entry.links if link.type == "application/pdf"), None),
            "title": entry.title,
            "summary": entry.summary,
            "source": entry.id, #arxiv_url
            "authors": [author.name for author in entry.authors],
            "published_date": entry.published,
            'used': False
        }
        papers.append(paper)

    return papers
 
def scrape_papers(max_results=50) -> list:
    """
    Scrape arXiv papers and return them as a list
    (no saving to database)
    """
    print(f"Scraping {max_results} papers from arXiv cs.AI...")
    papers = scrape_arxiv_cs_ai(max_results=max_results, sort_by="submittedDate")
    print(f"Successfully scraped {len(papers)} papers")
    return papers

def add_scraped_paper(filepath : str, papers: list):
    if not filepath.endswith(".json"):
        raise Exception("The filepath should be a json file.")
    if not os.path.exists(filepath): #the local storage does not exist
        print(f"The path {filepath} does not exist.")
        with open(filepath, 'w', encoding= 'utf-8') as f:
            json.dump(papers, f, indent= 4, ensure_ascii=False)
            print(f"Sucessfully saved {len(papers)} papers to local file.")
    else:
        with open(filepath, 'r') as f:
            existed_papers = json.load(f)
        new_papers = []
        existed_paper_id = set([p['url'] for p in existed_papers])
        for paper in papers:
            if paper['url'] not in existed_paper_id:
                new_papers.append(paper)
        if len(new_papers) > 0:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(new_papers + existed_papers, f, indent=4, ensure_ascii=False)
            print(f"Succesfully added new {len(new_papers)} papers to the local storage.")
        else:
            print("No new papers scraped")

# Example usage
if __name__ == "__main__":
    results = scrape_arxiv_cs_ai(max_results=100)
    # for i, paper in enumerate(results, 1):
    #     print(f"\n{i}. {paper['title']}")
    #     print(f"   Authors: {', '.join(paper['authors'])}")
    #     print(f"   Published: {paper['published']}")
    #     print(f"   PDF: {paper['pdf_url']}")
    filepath = r"FCI_NewsAgents\database\papers.json"
    add_scraped_paper(filepath, results)
    



