import sqlite3
import os

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "friday_memory.db"))

class MemoryDatabase:
    """Embedded SQLite database for persistent conversation history & user preferences."""

    @staticmethod
    def get_connection():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def init_db(cls):
        """Initialize database schema if tables do not exist."""
        conn = cls.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                text TEXT NOT NULL,
                action TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    @classmethod
    def save_message(cls, sender: str, text: str, action: str = None) -> dict:
        """Save a new message entry to conversation database."""
        if not text:
            return {"success": False, "error": "Empty message"}
        try:
            conn = cls.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO conversations (sender, text, action) VALUES (?, ?, ?)",
                (sender, text, action)
            )
            conn.commit()
            msg_id = cursor.lastrowid
            conn.close()
            return {"success": True, "id": msg_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def get_recent_history(cls, limit: int = 50) -> list:
        """Fetch recent conversation history."""
        try:
            conn = cls.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, sender, text, action, timestamp FROM conversations ORDER BY id ASC LIMIT ?",
                (limit,)
            )
            rows = cursor.fetchall()
            conn.close()
            return [
                {
                    "id": str(row["id"]),
                    "sender": row["sender"],
                    "text": row["text"],
                    "action": row["action"] if row["action"] != "none" else None,
                    "timestamp": row["timestamp"]
                }
                for row in rows
            ]
        except Exception as e:
            print(f"[Memory DB] Fetch history error: {e}")
            return []

    @classmethod
    def clear_history(cls) -> dict:
        """Clear all stored conversation history."""
        try:
            conn = cls.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM conversations")
            conn.commit()
            conn.close()
            return {"success": True, "message": "Cleared conversation history"}
        except Exception as e:
            return {"success": False, "error": str(e)}

# Auto-initialize DB on import
MemoryDatabase.init_db()
