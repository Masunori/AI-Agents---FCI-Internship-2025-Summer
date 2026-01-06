import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / os.environ["DEDUPLICATION_DB_PATH"]

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

def init_db(db_path: str | Path = DB_PATH) -> None:
    """
    Initialize the SQLite database with the required schema.

    Args:
        db_path (str | Path): Path to the SQLite database file.
    """
    print(f"Initializing database at: {db_path}")
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(DDL)
        conn.commit()
    finally:
        conn.close()
