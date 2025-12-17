import os
import sqlite3
import sys
from pathlib import Path

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from FCI_NewsAgents.services.article_url_cache.schema import init_db


def test_init_db(tmp_path: Path):
    db_path = tmp_path / "test_article_cache__001.db"

    if db_path.exists():
        db_path.unlink()
    
    init_db(db_path)
    
    assert db_path.exists(), "Database file was not created."
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='articles';")
    table = cursor.fetchone()
    
    assert table is not None, "Articles table was not created."
    
    conn.close() # Close the connection