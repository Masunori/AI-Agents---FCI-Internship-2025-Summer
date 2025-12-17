import os
import sys
from pathlib import Path

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from FCI_NewsAgents.services.article_url_cache.store import DedupStore


def test_dedup_store(tmp_path: Path):
    db_path = tmp_path / "test_article_cache__002.db"

    if db_path.exists():
        db_path.unlink()
    
    store = DedupStore(db_path)

    single_article = ("https://example.com/article0", "2024-06-01")

    articles = [
        ("https://example.com/article1", "2024-06-02"),
        ("https://example.com/article2", "2024-06-03"),
        ("https://example.com/article3", "2024-06-04"),
    ]

    half_dedup_articles = [
        ("https://example.com/article2", "2024-06-03"),  # duplicate
        ("https://example.com/article3", "2024-06-04"),  # duplicate
        ("https://example.com/article4", "2024-06-05"),  # new
    ]

    # Existence check before insertion
    for url, _ in articles:
        assert not store.exists(url), f"URL {url} should not exist before insertion."

    # Insert 1 article
    inserted = store.insert_if_new(single_article[0], single_article[1])
    assert inserted, "Insertion should succeed for a new URL."
    assert store.exists(single_article[0]), "URL should exist after insertion."

    # Insert multiple articles
    inserted_count = store.insert_many_if_new(articles)
    assert inserted_count == len(articles), "All new URLs should be inserted."
    for url, _ in articles:
        assert store.exists(url), f"URL {url} should exist after insertion."

    # Attempt to re-insert existing articles
    reinserted = store.insert_if_new(single_article[0], single_article[1])
    assert not reinserted, "Re-insertion should fail for existing URL."
    reinserted_count = store.insert_many_if_new(articles)
    assert reinserted_count == 0, "No URLs should be re-inserted."

    # Insert half deduplicated articles
    half_inserted_count = store.insert_many_if_new(half_dedup_articles)
    assert half_inserted_count == 1, "Only new URLs should be inserted."
    assert store.exists("https://example.com/article4"), "New URL should exist after insertion."

    store.close()