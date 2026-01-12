import os
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from typing import List

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from FCI_NewsAgents.models.document import Document
from FCI_NewsAgents.services.article_url_cache.cleanup import purge_older_than
from FCI_NewsAgents.services.article_url_cache.store import ArticleURLStore
from FCI_NewsAgents.utils.utils import get_canonical_url


def remove_duplicate_documents(
    documents: List[Document], 
    db_path: str | None = None,
    parallel: bool = True,
    max_workers: int = 16
) -> List[Document]:
    """
    Removes duplicate documents based on their URLs.

    Args:
        documents (List[Document]): List of Document objects to check for duplicates.
        db_path (str | None): Path to the database file for URL storage. If None, uses default.
        parallel (bool): Whether to use parallel processing to get canonical URLs.
        max_workers (int): Number of worker threads to use, if parallel is True. Defaults to 16.

    Returns:
        List[Document]: List of unique Document objects.
    """
    if len(documents) == 0:
        print("No documents provided for duplication check.")
        return documents
    
    today_str = date.today().isoformat()

    with ArticleURLStore(db_path) if db_path else ArticleURLStore() as article_store:
        if parallel:
            urls = [doc.url for doc in documents]
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                canonical_urls = list(executor.map(get_canonical_url, urls))

            to_insert = [(canonical_urls[idx], today_str) for idx in range(len(documents))]
        else:
            to_insert = [(get_canonical_url(doc.url), today_str) for doc in documents]

        insert_results = article_store.insert_many_if_new(to_insert)

    purge_older_than(days=7)

    for idx, doc in enumerate(documents):
        print(f"[{'KEEP' if insert_results[idx] else 'DUPLICATE'}] {doc.url}")
    return [d for idx, d in enumerate(documents) if insert_results[idx]]
