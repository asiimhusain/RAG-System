import sqlite3
import json
import contextlib
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class ChatHistoryManager:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(settings.DB_DIR / "chats.db")
        self._init_db()

    @contextlib.contextmanager
    def _connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._connection() as conn:
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        sources TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                    )
                """)

    def create_session(self, session_id: str, title: str) -> dict:
        with self._connection() as conn:
            with conn:
                conn.execute(
                    "INSERT OR IGNORE INTO sessions (id, title) VALUES (?, ?)",
                    (session_id, title)
                )
        return {"id": session_id, "title": title}

    def get_sessions(self) -> List[dict]:
        with self._connection() as conn:
            cursor = conn.execute("SELECT id, title, created_at FROM sessions ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def get_messages(self, session_id: str) -> List[dict]:
        with self._connection() as conn:
            cursor = conn.execute(
                "SELECT id, role, content, sources, created_at FROM messages WHERE session_id = ? ORDER BY created_at ASC",
                (session_id,)
            )
            rows = cursor.fetchall()
            messages = []
            for row in rows:
                msg = dict(row)
                if msg["sources"]:
                    try:
                        msg["sources"] = json.loads(msg["sources"])
                    except Exception:
                        msg["sources"] = []
                else:
                    msg["sources"] = []
                messages.append(msg)
            return messages

    def add_message(self, session_id: str, role: str, content: str, sources: Optional[List[dict]] = None) -> dict:
        sources_str = json.dumps(sources) if sources else None
        with self._connection() as conn:
            with conn:
                cursor = conn.execute(
                    "INSERT INTO messages (session_id, role, content, sources) VALUES (?, ?, ?, ?)",
                    (session_id, role, content, sources_str)
                )
                message_id = cursor.lastrowid
        return {
            "id": message_id,
            "session_id": session_id,
            "role": role,
            "content": content,
            "sources": sources or []
        }

    def delete_session(self, session_id: str):
        with self._connection() as conn:
            with conn:
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))

    def rename_session(self, session_id: str, title: str):
        with self._connection() as conn:
            with conn:
                conn.execute("UPDATE sessions SET title = ? WHERE id = ?", (title, session_id))
