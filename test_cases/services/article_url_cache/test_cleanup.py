import os
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from FCI_NewsAgents.services.article_url_cache.cleanup import purge_older_than
from FCI_NewsAgents.services.article_url_cache.store import ArticleURLStore


def test_purge_older_than(tmp_path: Path) -> None:
    db_path = tmp_path / "test_article_cache__003.db"
    store = ArticleURLStore(db_path)

    # Insert test data
    today = date.today()
    dates = [
        today - timedelta(days=1),
        today - timedelta(days=5),
        today - timedelta(days=10),
        today - timedelta(days=15),
    ]
    for i, scrape_date in enumerate(dates):
        store.insert_if_new(
            f"http://example.com/article{i}", scrape_date.strftime("%Y-%m-%d")
        )

    # Verify all entries are inserted
    assert store.count() == 4

    # Purge entries older than 7 days
    deleted_count = purge_older_than(db_path, days=7)
    assert deleted_count == 2  # Two entries should be deleted

    # Verify remaining entries
    for i in range(2):
        exists = store.exists(f"http://example.com/article{i}")
        assert exists is True

    # Verify deleted entries
    for i in range(2, 4):
        exists = store.exists(f"http://example.com/article{i}")
        assert exists is False

    store.close()
