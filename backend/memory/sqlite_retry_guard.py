"""
SQLite Lock Retries and Concurrency Guard
Prevents database busy/lock contention in multi-threaded background workers.
"""

import sqlite3
import time
import logging

logger = logging.getLogger(__name__)

def execute_with_retry(conn: sqlite3.Connection, query: str, params=(), max_retries=5, delay=0.1):
    for attempt in range(max_retries):
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower() and attempt < max_retries - 1:
                time.sleep(delay * (2 ** attempt))
                continue
            raise e
