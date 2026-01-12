import sqlite3
from pathlib import Path
from typing import Iterable
from datetime import date
from typing import List, Tuple, Dict

from .schema import init_db, DB_PATH


class ArticleURLStore:
    """
    SQLite-based store for deduplicating article URLs.

    Intended usage:

    ```python
    with ArticleURLStore(DB_PATH) as store:
        if store.insert_if_new(url, date.today()):
            process(article)
    ```

    Because the code fetches daily articles but might be called more than once a day, the deduplication logic is as follows:
    - If URL A was scraped before today, and A was fetched again today, insertion does
        not happen and the article is deemed a duplicate.
    - If URL A was scraped today, and A is fetched again today, insertion does not
        happen, but the article is _**not**_ deemed a duplicate.
    - If URL A was scraped for the first time (today), insertion happens and the article 
        is _**not**_ deemed a duplicate.
    """
    __slots__ = ("_conn",)

    def __init__(self, db_path: str | Path = DB_PATH) -> None:
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
        URLs are only considered duplicates if they were scraped before today.

        Args:
            canonical_url (str): The canonical URL to check.
        Returns:
            bool: True if the URL exists and was scraped before today, False otherwise.
        """
        today_str = date.today().isoformat()

        cursor = self._conn.execute(
            "SELECT 1 FROM articles WHERE canonical_url = ? AND scrape_date < ? LIMIT 1;",
            (canonical_url, today_str),
        )
        return cursor.fetchone() is not None
    
    def insert_if_new(self, canonical_url: str, scrape_date: str) -> bool:
        """
        Insert the canonical URL into the store if it does not already exist.

        Deduplication logic is as follows:
        - (TL;DR) Return True if the URL is not a duplicate of any URL fetched BEFORE today.
        - If URL A was scraped before today, and A was fetched again today, insertion does not happen and this returns False (for existence).
        - If URL A was scraped today, and A is fetched again today, insertion does not happen, but this returns True (for non-existence).
        - If URL A was scraped for the first time (today), insertion happens and this returns True (for non-existence).

        Args:
            canonical_url (str): The canonical URL to insert.
            scrape_date (str): The date the article was scraped, should be in 'YYYY-MM-DD' format.
        Returns:
            bool: True if the URL was inserted, False if it already existed.
        """
        today_str = date.today().isoformat()
        
        cur = self._conn.execute(
            "SELECT scrape_date FROM articles WHERE canonical_url = ? LIMIT 1;",
            (canonical_url,)
        )
        row = cur.fetchone()

        if row:
            existing_scrape_date = row[0]
            return existing_scrape_date == today_str
        else:
            self._conn.execute(
                "INSERT INTO articles (canonical_url, scrape_date) VALUES (?, ?);",
                (canonical_url, scrape_date)
            )
            return True
    
    def insert_many_if_new(self, entries: Iterable[Tuple[str, str]]) -> List[bool]:
        """
        Insert multiple canonical URLs into the store if they do not already exist. This also handles within-batch deduplication.
        
        Deduplication logic is as follows:
        - **(TL;DR)** Return True if the URL is not a duplicate of any URL fetched BEFORE today.
        - If URL A was scraped before today, and A was fetched again today, insertion does not happen and this returns False (for existence).
        - If URL A was scraped today, and A is fetched again today, insertion does not happen, but this returns True (for non-existence, as if insertion is successful).
        - If URL A was scraped for the first time (today), insertion happens and this returns True (for non-existence).

        Args:
            entries (Iterable[tuple[str, str]]): An iterable of tuples containing
                (canonical_url, scrape_date). The scrape_date should be in 'YYYY-MM-DD' format.
        Returns:
            List[bool]: A list of booleans indicating for each entry whether it was "inserted" (True) or already "existed" (False).
        """
        if not entries:
            return []

        today_str = date.today().isoformat()
        urls = [canonical_url for canonical_url, _ in entries]
        
        placeholder = ",".join("?" for _ in urls)
        cur = self._conn.execute(
            f"SELECT canonical_url, scrape_date FROM articles WHERE canonical_url IN ({placeholder});",
            urls
        )
        existing_rows = {row[0]: row[1] for row in cur.fetchall()}

        results: List[bool] = []
        to_insert: List[Tuple[str, str, int]] = []

        # De-duplication against the database
        for idx, (url, scrape_date) in enumerate(entries):
            if url in existing_rows:
                existing_scrape_date = existing_rows[url]
                results.append(existing_scrape_date == today_str)
            else:
                to_insert.append((url, scrape_date, idx))
                results.append(True)

        # De-duplication within the batch
        seen: Dict[str, str] = {}
        final_to_insert: List[Tuple[str, str]] = []
        for url, scrape_date, idx in to_insert:
            if url not in seen:
                seen[url] = scrape_date
                final_to_insert.append((url, scrape_date))
            else:
                # results[idx] = seen[url] == today_str
                results[idx] = False  # since this is a duplicate within batch, it cannot be "new"
                # string comparison of YYYY-MM-DD works for date ordering
                # choose the earliest scrape_date
                seen[url] = min(seen[url], scrape_date)
        
        to_insert = final_to_insert
        
        # insertion
        if final_to_insert:
            self._conn.executemany(
                "INSERT INTO articles (canonical_url, scrape_date) VALUES (?, ?);",
                final_to_insert
            )

        return results
    
    def remove_all(self) -> None:
        """
        Remove all entries from the store.
        """
        self._conn.execute("DELETE FROM articles;")
    
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

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()