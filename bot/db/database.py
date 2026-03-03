from __future__ import annotations

import aiosqlite


class Database:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self.conn = await aiosqlite.connect(self.db_path)
        await self.conn.execute("PRAGMA journal_mode=WAL")
        await self.conn.execute("PRAGMA foreign_keys=ON")

    async def close(self) -> None:
        if self.conn is not None:
            await self.conn.close()
            self.conn = None

    async def init_schema(self) -> None:
        assert self.conn is not None, "call connect() first"
        await self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id       INTEGER PRIMARY KEY,
                username      TEXT,
                first_name    TEXT,
                is_paused     INTEGER DEFAULT 0,
                created_at    TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS channels (
                channel_id       INTEGER PRIMARY KEY,
                username         TEXT,
                title            TEXT,
                is_joined        INTEGER DEFAULT 0,
                subscriber_count INTEGER DEFAULT 0,
                last_message_id  INTEGER DEFAULT 0,
                poll_interval    INTEGER DEFAULT 120,
                last_polled_at   TEXT,
                created_at       TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS subscriptions (
                user_id    INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                PRIMARY KEY (user_id, channel_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (channel_id) REFERENCES channels(channel_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS user_topics (
                user_id  INTEGER NOT NULL,
                topic_id TEXT NOT NULL,
                PRIMARY KEY (user_id, topic_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS catalog (
                channel_username TEXT NOT NULL,
                title            TEXT NOT NULL,
                category         TEXT NOT NULL,
                tags             TEXT,
                language         TEXT DEFAULT 'ru',
                PRIMARY KEY (channel_username, category)
            );

            CREATE TABLE IF NOT EXISTS forwarded_messages (
                channel_id   INTEGER NOT NULL,
                message_id   INTEGER NOT NULL,
                user_id      INTEGER NOT NULL,
                forwarded_at TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (channel_id, message_id, user_id)
            );

            CREATE INDEX IF NOT EXISTS idx_forwarded_messages_forwarded_at
                ON forwarded_messages(forwarded_at);
            """
        )
