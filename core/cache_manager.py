import json
import sqlite3
import time
from pathlib import Path
from typing import Any


class CacheManager:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS api_cache (
                    key TEXT PRIMARY KEY,
                    response TEXT NOT NULL,
                    updated_at INTEGER NOT NULL
                )
                """
            )
            conn.commit()

    def get(self, key: str, ttl_seconds: int) -> Any | None:
        now = int(time.time())
        with self._connect() as conn:
            row = conn.execute(
                "SELECT response, updated_at FROM api_cache WHERE key = ?",
                (key,),
            ).fetchone()
        if not row:
            return None
        payload, updated_at = row
        if now - int(updated_at) > ttl_seconds:
            return None
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            return None

    def set(self, key: str, data: Any) -> None:
        payload = json.dumps(data)
        now = int(time.time())
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO api_cache (key, response, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    response = excluded.response,
                    updated_at = excluded.updated_at
                """,
                (key, payload, now),
            )
            conn.commit()

