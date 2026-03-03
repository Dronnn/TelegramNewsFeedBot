from __future__ import annotations

from typing import TYPE_CHECKING

import aiosqlite

if TYPE_CHECKING:
    from bot.db.database import Database

from bot.db.models import User


async def add_user(
    db: Database, user_id: int, username: str | None, first_name: str | None
) -> None:
    await db._conn.execute(
        "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
        (user_id, username, first_name),
    )
    await db._conn.commit()


async def get_user(db: Database, user_id: int) -> User | None:
    cursor = await db._conn.execute(
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
    await db._conn.execute(
        "UPDATE users SET is_paused = ? WHERE user_id = ?",
        (int(is_paused), user_id),
    )
    await db._conn.commit()


async def get_active_subscribers(db: Database, channel_id: int) -> list[int]:
    cursor = await db._conn.execute(
        "SELECT user_id FROM subscriptions JOIN users USING(user_id) "
        "WHERE channel_id = ? AND is_paused = 0",
        (channel_id,),
    )
    rows = await cursor.fetchall()
    return [row[0] for row in rows]
