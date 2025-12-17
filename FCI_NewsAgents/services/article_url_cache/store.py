import sqlite3
from pathlib import Path
from typing import Iterable

from .schema import init_db


class DedupStore:
    """
    SQLite-based store for deduplicating article URLs.

    Intended usage:

    ```python
store = DedupStore(DB_PATH)
if store.insert_if_new(url, date.today()):
    process(article)
    ```
    """
    __slots__ = ("_conn",)

    def __init__(self, db_path: str | Path):
        init_db(db_path)
        self._conn = sqlite3.connect(
            db_path,
            isolation_level=None,  # autocommit mode
            check_same_thread=False,
        )
        self._conn.execute("PRAGMA foreign_keys=ON;")
        self._conn.execute("PRAGMA journal_mode=WAL;")

    def exists(self, canonical_url: str) -> bool:
        """
        Check if the given canonical URL exists in the store.

        Args:
            canonical_url (str): The canonical URL to check.
        Returns:
            bool: True if the URL exists, False otherwise.
        """
        cursor = self._conn.execute(
            "SELECT 1 FROM articles WHERE canonical_url = ? LIMIT 1;",
            (canonical_url,),
        )
        return cursor.fetchone() is not None
    
    def insert_if_new(self, canonical_url: str, scrape_date: str) -> bool:
        """
        Insert the canonical URL into the store if it does not already exist.

        Args:
            canonical_url (str): The canonical URL to insert.
            scrape_date (str): The date the article was scraped, should be in 'YYYY-MM-DD' format.
        Returns:
            bool: True if the URL was inserted, False if it already existed.
        """
        cur = self._conn.execute(
            """
            INSERT OR IGNORE INTO articles (canonical_url, scrape_date) 
            VALUES (?, ?);
            """,
            (canonical_url, scrape_date),
        )
        return cur.rowcount > 0
    
    def insert_many_if_new(self, entries: Iterable[tuple[str, str]]) -> int:
        """
        Insert multiple canonical URLs into the store if they do not already exist.

        Args:
            entries (Iterable[tuple[str, str]]): An iterable of tuples containing
                (canonical_url, scrape_date). The scrape_date should be in 'YYYY-MM-DD' format.
        Returns:
            int: The number of URLs that were inserted.
        """
        cur = self._conn.executemany(
            """
            INSERT OR IGNORE INTO articles (canonical_url, scrape_date) 
            VALUES (?, ?);
            """,
            entries,
        )
        return cur.rowcount
    
    def count(self) -> int:
        """
        Get the total number of unique canonical URLs stored.

        Returns:
            int: The count of unique canonical URLs.
        """
        cursor = self._conn.execute("SELECT COUNT(*) FROM articles;")
        result = cursor.fetchone()
        return result[0] if result else 0
    
    def close(self) -> None:
        """
        Close the database connection.
        """
        self._conn.close()