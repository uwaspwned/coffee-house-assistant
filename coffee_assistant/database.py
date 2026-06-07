from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import aiosqlite

MessageRole = Literal["user", "assistant"]


@dataclass(frozen=True)
class StoredMessage:
    role: MessageRole
    content: str


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._connection: aiosqlite.Connection | None = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = await aiosqlite.connect(self.path)
        self._connection.row_factory = aiosqlite.Row
        await self._connection.execute("PRAGMA foreign_keys = ON")
        await self._connection.execute("PRAGMA journal_mode = WAL")
        await self._connection.commit()

    async def init_schema(self) -> None:
        async with self._lock:
            await self.connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_user_id INTEGER NOT NULL,
                    telegram_chat_id INTEGER NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_sessions_lookup
                ON sessions (telegram_user_id, telegram_chat_id, is_active, id);

                CREATE UNIQUE INDEX IF NOT EXISTS idx_sessions_one_active
                ON sessions (telegram_user_id, telegram_chat_id)
                WHERE is_active = 1;

                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_messages_session_id
                ON messages (session_id, id);
                """
            )
            await self.connection.commit()

    @property
    def connection(self) -> aiosqlite.Connection:
        if self._connection is None:
            raise RuntimeError("Database is not connected")
        return self._connection

    async def get_or_create_session(self, telegram_user_id: int, telegram_chat_id: int) -> int:
        async with self._lock:
            session_id = await self._get_active_session_id(telegram_user_id, telegram_chat_id)
            if session_id is not None:
                return session_id

            now = _utc_now()
            cursor = await self.connection.execute(
                """
                INSERT INTO sessions (telegram_user_id, telegram_chat_id, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (telegram_user_id, telegram_chat_id, now, now),
            )
            await self.connection.commit()
            session_id = int(cursor.lastrowid)
            await cursor.close()
            return session_id

    async def add_message(self, session_id: int, role: MessageRole, content: str) -> None:
        async with self._lock:
            now = _utc_now()
            await self.connection.execute(
                """
                INSERT INTO messages (session_id, role, content, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, role, content, now),
            )
            await self.connection.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (now, session_id),
            )
            await self.connection.commit()

    async def get_recent_messages(self, session_id: int, limit: int) -> list[StoredMessage]:
        cursor = await self.connection.execute(
            """
            SELECT role, content
            FROM (
                SELECT id, role, content
                FROM messages
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
            )
            ORDER BY id ASC
            """,
            (session_id, limit),
        )
        rows = await cursor.fetchall()
        await cursor.close()

        return [StoredMessage(role=row["role"], content=row["content"]) for row in rows]

    async def reset_session(self, telegram_user_id: int, telegram_chat_id: int) -> int:
        async with self._lock:
            cursor = await self.connection.execute(
                """
                UPDATE sessions
                SET is_active = 0,
                    updated_at = ?
                WHERE telegram_user_id = ?
                  AND telegram_chat_id = ?
                  AND is_active = 1
                """,
                (_utc_now(), telegram_user_id, telegram_chat_id),
            )
            await self.connection.commit()
            rowcount = int(cursor.rowcount)
            await cursor.close()
            return rowcount

    async def close(self) -> None:
        if self._connection is not None:
            await self._connection.close()
            self._connection = None

    async def _get_active_session_id(
        self,
        telegram_user_id: int,
        telegram_chat_id: int,
    ) -> int | None:
        cursor = await self.connection.execute(
            """
            SELECT id
            FROM sessions
            WHERE telegram_user_id = ?
              AND telegram_chat_id = ?
              AND is_active = 1
            ORDER BY id DESC
            LIMIT 1
            """,
            (telegram_user_id, telegram_chat_id),
        )
        row = await cursor.fetchone()
        await cursor.close()
        if row is None:
            return None
        return int(row["id"])


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()
