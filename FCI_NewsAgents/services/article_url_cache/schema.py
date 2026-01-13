import sqlite3
from pathlib import Path

DDL = """
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_url TEXT NOT NULL UNIQUE,
    scrape_date TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_articles_canonical_url
    ON articles (canonical_url);

CREATE INDEX IF NOT EXISTS idx_articles_scrape_date
    ON articles (scrape_date);
"""

def init_db(db_path: str | Path | None = None) -> None:
    """
    Initialize the SQLite database with the required schema.
    If set to None, uses the default DEDUPLICATION_DB_PATH from environment.

    Args:
        db_path (str | Path | None): Path to the SQLite database file.
    """
    if db_path is None:
        import os
        from dotenv import load_dotenv

        load_dotenv()

        BASE_DIR = Path(__file__).resolve().parent
        db_path = BASE_DIR / os.environ["DEDUPLICATION_DB_PATH"]

    print(f"Initializing database at: {db_path}")
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(DDL)
        conn.commit()
    finally:
        conn.close()
