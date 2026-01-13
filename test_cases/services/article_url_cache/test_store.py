import os
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from FCI_NewsAgents.services.article_url_cache.store import ArticleURLStore


def test_dedup_store_insert_different_days(tmp_path: Path):
    db_path = tmp_path / "test_article_cache__002.db"

    if db_path.exists():
        db_path.unlink()

    store = ArticleURLStore(db_path)
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    articles = [
        ("https://example.com/article1", yesterday),
        ("https://example.com/article2", yesterday),
        ("https://example.com/article1", today),  # Same URL, different day
        ("https://example.com/article3", today),
    ]

    # Initially, none of the URLs should exist
    for url, _ in articles:
        assert not store.exists(url), f"URL {url} should not exist initially."

    # Insert articles and check existence
    assert store.insert_if_new(articles[0][0], articles[0][1]), f"URL {articles[0][0]} of date {articles[0][1]} should be inserted."
    assert store.insert_if_new(articles[1][0], articles[1][1]), f"URL {articles[1][0]} of date {articles[1][1]} should be inserted."
    assert not store.insert_if_new(articles[2][0], articles[2][1]), f"URL {articles[2][0]} of date {articles[2][1]} should NOT be inserted again."
    assert store.insert_if_new(articles[3][0], articles[3][1]), f"URL {articles[3][0]} of date {articles[3][1]} should be inserted."

    # After all insertions, count should be 3 unique URLs
    assert store.count() == 3, "There should be exactly 3 unique URLs in the store."

    store.close()

def test_dedup_store_insert_same_days(tmp_path: Path):
    db_path = tmp_path / "test_article_cache__002.db"

    if db_path.exists():
        db_path.unlink()

    store = ArticleURLStore(db_path)

    today = date.today().isoformat()

    articles = [
        ("https://example.com/article1", today),
        ("https://example.com/article2", today),
        ("https://example.com/article1", today),  # Same URL, same day
    ]

    # Initially, none of the URLs should exist
    for url, _ in articles:
        assert not store.exists(url), f"URL {url} should not exist initially."

    # Insert articles and check existence
    assert store.insert_if_new(articles[0][0], articles[0][1]), f"URL {articles[0][0]} of date {articles[0][1]} should be inserted."
    assert store.insert_if_new(articles[1][0], articles[1][1]), f"URL {articles[1][0]} of date {articles[1][1]} should be inserted."
    assert store.insert_if_new(articles[2][0], articles[2][1]), f"URL {articles[2][0]} of date {articles[2][1]} should be considered new for the same day."

    # After all insertions, count should be 2 unique URLs
    assert store.count() == 2, "There should be exactly 2 unique URLs in the store."

    store.close()

def test_dedup_store_insert_many_dupe_against_db(tmp_path: Path):
    db_path = tmp_path / "test_article_cache__002.db"

    if db_path.exists():
        db_path.unlink()

    store = ArticleURLStore(db_path)
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    articles = [
        ("https://example.com/article1", yesterday),
        ("https://example.com/article2", today),
        ("https://example.com/article1", today),  # Same URL, different day
        ("https://example.com/article3", today),
    ]

    second_batch = [
        ("https://example.com/article4", today),
        ("https://example.com/article1", yesterday),  # Duplicate from first batch
    ]

    # Initially, none of the URLs should exist
    for url, _ in articles:
        assert not store.exists(url), f"URL {url} should not exist initially."

    # Insert articles and check existence
    results = store.insert_many_if_new(articles)
    assert results == [True, True, False, True], "Insert many results do not match expected."
    assert store.count() == 3, "There should be exactly 3 unique URLs in the store."

    # Insert second batch
    assert store.insert_many_if_new(second_batch) == [True, False], "Second batch insert results do not match expected."
    assert store.count() == 4, "There should be exactly 4 unique URLs in the store."

    store.close()

def test_dedup_store_insert_many_dupe_within_first_batch(tmp_path: Path):
    db_path = tmp_path / "test_article_cache__002.db"

    if db_path.exists():
        db_path.unlink()

    store = ArticleURLStore(db_path)
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    articles = [
        ("https://example.com/article2", today),
        ("https://example.com/article2", today), # Duplicate within batch
    ]

    second_batch = [
        ("https://example.com/article4", today),
        ("https://example.com/article1", yesterday),
    ]

    # Initially, none of the URLs should exist
    for url, _ in articles:
        assert not store.exists(url), f"URL {url} should not exist initially."

    # Insert articles and check existence
    results = store.insert_many_if_new(articles)
    assert results == [True, False], "Insert many results do not match expected."
    assert store.count() == 1, "There should be exactly 1 unique URL in the store."

    # Insert second batch
    assert store.insert_many_if_new(second_batch) == [True, True], "Second batch insert results do not match expected."
    assert store.count() == 3, "There should be exactly 3 unique URLs in the store."

    store.close()

def test_dedup_store_insert_many_dupe_within_second_batch(tmp_path: Path):
    db_path = tmp_path / "test_article_cache__002.db"

    if db_path.exists():
        db_path.unlink()

    store = ArticleURLStore(db_path)
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    first_batch = [
        ("https://example.com/article4", today),
        ("https://example.com/article1", yesterday),
    ]

    second_batch = [
        ("https://example.com/article2", today),
        ("https://example.com/article2", today), # Duplicate within batch
    ]



    # Initially, none of the URLs should exist
    for url, _ in first_batch:
        assert not store.exists(url), f"URL {url} should not exist initially."

    # Insert first batch and check existence
    results = store.insert_many_if_new(first_batch)
    assert results == [True, True], "Insert many results do not match expected."
    assert store.count() == 2, "There should be exactly 2 unique URLs in the store."

    # Insert second batch
    assert store.insert_many_if_new(second_batch) == [True, False], "Second batch insert results do not match expected."
    assert store.count() == 3, "There should be exactly 3 unique URLs in the store."

    store.close()
