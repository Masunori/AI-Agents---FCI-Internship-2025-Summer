import sqlite3
from datetime import date
from pathlib import Path
from queue import Queue
from threading import Thread
from typing import Dict, Iterable, List, Tuple

from FCI_NewsAgents.utils.logger import file_writer

from .schema import init_db


class ArticleURLStore:
    """
    SQLite-based store for deduplicating article URLs.

    If this is initialised with no db_path, it uses the default DEDUPLICATION_DB_PATH from environment (look at `schema.py`).

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

    def __init__(self, db_path: str | Path | None = None) -> None:
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
            (canonical_url,),
        )
        row = cur.fetchone()

        if row:
            existing_scrape_date = row[0]
            return existing_scrape_date == today_str
        else:
            self._conn.execute(
                "INSERT INTO articles (canonical_url, scrape_date) VALUES (?, ?);",
                (canonical_url, scrape_date),
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
        - Within the same batch, if the same URL appears multiple times, only the first occurrence is considered for insertion;
        subsequent occurrences are treated as duplicates and return False, regardless of their scrape_date.

        Args:
            entries (Iterable[tuple[str, str]]): An iterable of tuples containing
                (canonical_url, scrape_date). The scrape_date should be in 'YYYY-MM-DD' format.
        Returns:
            List[bool]: A list of booleans indicating for each entry whether it was "inserted" (True) or already "existed" (False).
        """
        if not entries:
            return []

        info_queue: Queue[str] = Queue()
        log_thread = Thread(target=file_writer, args=("deduplication.log", info_queue))
        log_thread.start()

        today_str = date.today().isoformat()
        urls = [canonical_url for canonical_url, _ in entries]

        placeholder = ",".join("?" for _ in urls)
        cur = self._conn.execute(
            f"SELECT canonical_url, scrape_date FROM articles WHERE canonical_url IN ({placeholder});",
            urls,
        )
        existing_rows = {row[0]: row[1] for row in cur.fetchall()}

        results: List[bool] = []
        to_insert: List[Tuple[str, str]] = []
        seen_in_batch: Dict[str, bool] = {}  # Track URLs already seen in this batch

        info_queue.put(f"Checking {len(urls)} URLs against existing database entries.")

        # De-duplication against the database
        for url, scrape_date in entries:
            if url in seen_in_batch:
                # Duplicate within batch - always flag as duplicate
                results.append(False)
            elif url in existing_rows:
                existing_scrape_date = existing_rows[url]
                results.append(existing_scrape_date == today_str)
                seen_in_batch[url] = True
            else:
                info_queue.put(
                    f"New URL passes the DB dedup check: {url} (scrape_date: {scrape_date})"
                )
                to_insert.append((url, scrape_date))
                results.append(True)
                seen_in_batch[url] = True

        info_queue.put(
            f"{len(to_insert)} new URLs to insert after checking against database."
        )

        info_queue.put("Insertion complete.")
        info_queue.put(None)
        log_thread.join()

        # insertion
        if to_insert:
            self._conn.executemany(
                "INSERT INTO articles (canonical_url, scrape_date) VALUES (?, ?);",
                to_insert,
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
