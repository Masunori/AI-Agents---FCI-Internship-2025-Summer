import sqlite3
from pathlib import Path
from datetime import date, datetime, timedelta

from .schema import init_db, connect_db


def purge_older_than(
    db_path: str | Path | None = None,
    days: int = 7,
) -> int:
    """
    Purge entries older than the specified number of days from the database.

    Args:
        db_path (str | Path | None): Path to the SQLite database file. If None, uses the default DEDUPLICATION_DB_PATH from environment (look at `schema.py`).
        days (int): Number of days to retain entries. Entries older than this will be deleted.

    Returns:
        int: Number of rows deleted.
    """
    init_db(db_path)

    cutoff_date = date.today() - timedelta(days=days)
    conn = connect_db(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM articles WHERE scrape_date < ?",
            (cutoff_date.strftime("%Y-%m-%d"),)
        )
        deleted_rows = cursor.rowcount
        conn.commit()
        return deleted_rows
    finally:
        conn.close()