"""Durable SQLite history for the single-user findings chat."""

from __future__ import annotations

import asyncio
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class FindingChatStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=5)
        try:
            if os.name != "nt":
                try:
                    os.chmod(self.path, 0o600)
                except OSError:
                    # Some host-mounted filesystems manage permissions outside POSIX.
                    pass
            connection.execute("PRAGMA busy_timeout = 5000")
            connection.execute("""
                CREATE TABLE IF NOT EXISTS finding_chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    finding_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_finding_chat_messages_finding_id_id
                ON finding_chat_messages (finding_id, id)
            """)
        except Exception:
            connection.close()
            raise
        return connection

    def _read(self, finding_id: str, limit: int | None = None) -> list[dict[str, str]]:
        connection = self._connect()
        try:
            if limit is None:
                rows = connection.execute(
                    "SELECT role, content FROM finding_chat_messages WHERE finding_id = ? ORDER BY id",
                    (finding_id,),
                ).fetchall()
            else:
                rows = connection.execute(
                    """SELECT role, content FROM finding_chat_messages
                       WHERE finding_id = ? ORDER BY id DESC LIMIT ?""",
                    (finding_id, limit),
                ).fetchall()[::-1]
            return [{"role": role, "content": content} for role, content in rows]
        finally:
            connection.close()

    async def list_messages(self, finding_id: str) -> list[dict[str, str]]:
        return await asyncio.to_thread(self._read, finding_id)

    async def recent_messages(self, finding_id: str, limit: int = 19) -> list[dict[str, str]]:
        return await asyncio.to_thread(self._read, finding_id, limit)

    def _append_exchange(self, finding_id: str, user: str, assistant: str) -> None:
        connection = self._connect()
        try:
            now = datetime.now(timezone.utc).isoformat()
            with connection:
                connection.executemany(
                    """INSERT INTO finding_chat_messages
                       (finding_id, role, content, created_at) VALUES (?, ?, ?, ?)""",
                    [(finding_id, "user", user, now), (finding_id, "assistant", assistant, now)],
                )
        finally:
            connection.close()

    async def append_exchange(self, finding_id: str, user: str, assistant: str) -> None:
        await asyncio.to_thread(self._append_exchange, finding_id, user, assistant)

    def _import_if_empty(self, finding_id: str, messages: list[dict[str, str]]) -> None:
        connection = self._connect()
        try:
            with connection:
                connection.execute("BEGIN IMMEDIATE")
                exists = connection.execute(
                    "SELECT 1 FROM finding_chat_messages WHERE finding_id = ? LIMIT 1",
                    (finding_id,),
                ).fetchone()
                if not exists:
                    now = datetime.now(timezone.utc).isoformat()
                    connection.executemany(
                        """INSERT INTO finding_chat_messages
                           (finding_id, role, content, created_at) VALUES (?, ?, ?, ?)""",
                        [(finding_id, item["role"], item["content"], now) for item in messages],
                    )
        finally:
            connection.close()

    async def import_if_empty(self, finding_id: str, messages: list[dict[str, str]]) -> list[dict[str, str]]:
        await asyncio.to_thread(self._import_if_empty, finding_id, messages)
        return await self.list_messages(finding_id)

    def _clear(self, finding_id: str) -> None:
        connection = self._connect()
        try:
            with connection:
                connection.execute(
                    "DELETE FROM finding_chat_messages WHERE finding_id = ?", (finding_id,)
                )
        finally:
            connection.close()

    async def clear(self, finding_id: str) -> None:
        await asyncio.to_thread(self._clear, finding_id)
