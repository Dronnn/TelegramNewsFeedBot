from __future__ import annotations

from typing import TYPE_CHECKING

import aiosqlite

if TYPE_CHECKING:
    from bot.db.database import Database

from bot.db.models import CatalogEntry, Channel, User


async def add_user(
    db: Database, user_id: int, username: str | None, first_name: str | None
) -> None:
    await db.conn.execute(
        "INSERT INTO users (user_id, username, first_name) VALUES (?, ?, ?) "
        "ON CONFLICT(user_id) DO UPDATE SET username=excluded.username, first_name=excluded.first_name",
        (user_id, username, first_name),
    )
    await db.conn.commit()


async def get_user(db: Database, user_id: int) -> User | None:
    cursor = await db.conn.execute(
        "SELECT * FROM users WHERE user_id = ?", (user_id,)
    )
    cursor.row_factory = aiosqlite.Row
    row = await cursor.fetchone()
    if row is None:
        return None
    return User(
        user_id=row["user_id"],
        username=row["username"],
        first_name=row["first_name"],
        is_paused=bool(row["is_paused"]),
        created_at=row["created_at"],
    )


async def set_user_paused(db: Database, user_id: int, is_paused: bool) -> None:
    await db.conn.execute(
        "UPDATE users SET is_paused = ? WHERE user_id = ?",
        (int(is_paused), user_id),
    )
    await db.conn.commit()


async def get_active_subscribers(db: Database, channel_id: int) -> list[int]:
    cursor = await db.conn.execute(
        "SELECT user_id FROM subscriptions JOIN users USING(user_id) "
        "WHERE channel_id = ? AND is_paused = 0",
        (channel_id,),
    )
    rows = await cursor.fetchall()
    return [row[0] for row in rows]


# ── Channel queries ───────────────────────────────────────────────


def _row_to_channel(row: aiosqlite.Row) -> Channel:
    return Channel(
        channel_id=row["channel_id"],
        username=row["username"],
        title=row["title"],
        is_joined=bool(row["is_joined"]),
        subscriber_count=row["subscriber_count"],
        last_message_id=row["last_message_id"],
        poll_interval=row["poll_interval"],
        last_polled_at=row["last_polled_at"],
        created_at=row["created_at"],
    )


async def add_channel(
    db: Database, channel_id: int, username: str | None, title: str | None
) -> None:
    await db.conn.execute(
        "INSERT INTO channels (channel_id, username, title) VALUES (?, ?, ?) "
        "ON CONFLICT(channel_id) DO UPDATE SET username=excluded.username, title=excluded.title",
        (channel_id, username, title),
    )
    await db.conn.commit()


async def get_channel(db: Database, channel_id: int) -> Channel | None:
    cursor = await db.conn.execute(
        "SELECT * FROM channels WHERE channel_id = ?", (channel_id,)
    )
    cursor.row_factory = aiosqlite.Row
    row = await cursor.fetchone()
    if row is None:
        return None
    return _row_to_channel(row)


async def get_channel_by_username(db: Database, username: str) -> Channel | None:
    cursor = await db.conn.execute(
        "SELECT * FROM channels WHERE username = ?", (username,)
    )
    cursor.row_factory = aiosqlite.Row
    row = await cursor.fetchone()
    if row is None:
        return None
    return _row_to_channel(row)


async def update_channel_last_message(
    db: Database, channel_id: int, message_id: int
) -> None:
    await db.conn.execute(
        "UPDATE channels SET last_message_id = ? "
        "WHERE channel_id = ? AND (last_message_id IS NULL OR last_message_id < ?)",
        (message_id, channel_id, message_id),
    )
    await db.conn.commit()


async def update_channel_polled(db: Database, channel_id: int) -> None:
    await db.conn.execute(
        "UPDATE channels SET last_polled_at = datetime('now') WHERE channel_id = ?",
        (channel_id,),
    )
    await db.conn.commit()


async def set_channel_joined(
    db: Database, channel_id: int, is_joined: bool
) -> None:
    await db.conn.execute(
        "UPDATE channels SET is_joined = ? WHERE channel_id = ?",
        (int(is_joined), channel_id),
    )
    await db.conn.commit()


async def get_channels_to_poll(db: Database) -> list[Channel]:
    cursor = await db.conn.execute(
        "SELECT * FROM channels WHERE is_joined = 0 AND subscriber_count > 0"
    )
    cursor.row_factory = aiosqlite.Row
    rows = await cursor.fetchall()
    return [_row_to_channel(row) for row in rows]


async def get_joined_channel_ids(db: Database) -> list[int]:
    cursor = await db.conn.execute(
        "SELECT channel_id FROM channels WHERE is_joined = 1"
    )
    rows = await cursor.fetchall()
    return [row[0] for row in rows]


async def delete_channel(db: Database, channel_id: int) -> None:
    """Delete a channel and its related data from the database."""
    await db.conn.execute(
        "DELETE FROM subscriptions WHERE channel_id = ?",
        (channel_id,),
    )
    await db.conn.execute(
        "DELETE FROM forwarded_messages WHERE channel_id = ?",
        (channel_id,),
    )
    await db.conn.execute(
        "DELETE FROM channels WHERE channel_id = ?",
        (channel_id,),
    )
    await db.conn.commit()


# ── Subscription queries ─────────────────────────────────────────


async def subscribe(db: Database, user_id: int, channel_id: int) -> None:
    cursor = await db.conn.execute(
        "INSERT OR IGNORE INTO subscriptions (user_id, channel_id) VALUES (?, ?)",
        (user_id, channel_id),
    )
    if cursor.rowcount > 0:
        await db.conn.execute(
            "UPDATE channels SET subscriber_count = subscriber_count + 1 "
            "WHERE channel_id = ?",
            (channel_id,),
        )
    await db.conn.commit()


async def unsubscribe(db: Database, user_id: int, channel_id: int) -> None:
    cursor = await db.conn.execute(
        "DELETE FROM subscriptions WHERE user_id = ? AND channel_id = ?",
        (user_id, channel_id),
    )
    if cursor.rowcount > 0:
        await db.conn.execute(
            "UPDATE channels SET subscriber_count = MAX(subscriber_count - 1, 0) "
            "WHERE channel_id = ?",
            (channel_id,),
        )
    await db.conn.commit()


async def get_user_subscriptions(db: Database, user_id: int) -> list[Channel]:
    cursor = await db.conn.execute(
        "SELECT channels.* FROM subscriptions JOIN channels USING(channel_id) "
        "WHERE user_id = ?",
        (user_id,),
    )
    cursor.row_factory = aiosqlite.Row
    rows = await cursor.fetchall()
    return [_row_to_channel(row) for row in rows]


async def get_channel_subscriber_count(db: Database, channel_id: int) -> int:
    cursor = await db.conn.execute(
        "SELECT subscriber_count FROM channels WHERE channel_id = ?",
        (channel_id,),
    )
    row = await cursor.fetchone()
    if row is None:
        return 0
    return row[0]


# ── User topic queries ───────────────────────────────────────────


async def add_user_topic(db: Database, user_id: int, topic_id: str) -> None:
    await db.conn.execute(
        "INSERT OR IGNORE INTO user_topics (user_id, topic_id) VALUES (?, ?)",
        (user_id, topic_id),
    )
    await db.conn.commit()


async def remove_user_topic(db: Database, user_id: int, topic_id: str) -> None:
    await db.conn.execute(
        "DELETE FROM user_topics WHERE user_id = ? AND topic_id = ?",
        (user_id, topic_id),
    )
    await db.conn.commit()


async def get_user_topics(db: Database, user_id: int) -> list[str]:
    cursor = await db.conn.execute(
        "SELECT topic_id FROM user_topics WHERE user_id = ?",
        (user_id,),
    )
    rows = await cursor.fetchall()
    return [row[0] for row in rows]


# ── Catalog queries ──────────────────────────────────────────────


async def search_catalog(db: Database, category: str) -> list[CatalogEntry]:
    cursor = await db.conn.execute(
        "SELECT * FROM catalog WHERE category = ?", (category,)
    )
    cursor.row_factory = aiosqlite.Row
    rows = await cursor.fetchall()
    return [
        CatalogEntry(
            channel_username=row["channel_username"],
            title=row["title"],
            category=row["category"],
            tags=row["tags"],
            language=row["language"],
        )
        for row in rows
    ]


async def get_catalog_categories(db: Database) -> list[str]:
    cursor = await db.conn.execute(
        "SELECT DISTINCT category FROM catalog ORDER BY category"
    )
    rows = await cursor.fetchall()
    return [row[0] for row in rows]


async def seed_catalog(db: Database, entries: list[CatalogEntry]) -> None:
    await db.conn.executemany(
        "INSERT INTO catalog "
        "(channel_username, title, category, tags, language) "
        "VALUES (?, ?, ?, ?, ?) "
        "ON CONFLICT(channel_username, category) DO UPDATE SET "
        "title=excluded.title, tags=excluded.tags, language=excluded.language",
        [
            (e.channel_username, e.title, e.category, e.tags, e.language)
            for e in entries
        ],
    )
    await db.conn.commit()


# ── Dedup queries ────────────────────────────────────────────────


async def is_forwarded(
    db: Database, channel_id: int, message_id: int, user_id: int
) -> bool:
    cursor = await db.conn.execute(
        "SELECT EXISTS("
        "SELECT 1 FROM forwarded_messages "
        "WHERE channel_id = ? AND message_id = ? AND user_id = ?"
        ")",
        (channel_id, message_id, user_id),
    )
    row = await cursor.fetchone()
    return bool(row[0])


async def mark_forwarded(
    db: Database, channel_id: int, message_id: int, user_id: int
) -> None:
    await db.conn.execute(
        "INSERT OR IGNORE INTO forwarded_messages "
        "(channel_id, message_id, user_id) VALUES (?, ?, ?)",
        (channel_id, message_id, user_id),
    )
    await db.conn.commit()


async def cleanup_old_forwarded(db: Database, days: int = 7) -> int:
    cursor = await db.conn.execute(
        "DELETE FROM forwarded_messages "
        "WHERE forwarded_at < datetime('now', ? || ' days')",
        (f"-{days}",),
    )
    await db.conn.commit()
    return cursor.rowcount
