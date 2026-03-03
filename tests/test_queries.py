from __future__ import annotations

import pytest

from bot.db.database import Database
from bot.db.models import CatalogEntry
from bot.db.queries import (
    add_channel,
    add_user,
    add_user_topic,
    cleanup_old_forwarded,
    get_active_subscribers,
    get_channel,
    get_user,
    get_user_subscriptions,
    get_user_topics,
    is_forwarded,
    mark_forwarded,
    remove_user_topic,
    search_catalog,
    seed_catalog,
    set_user_paused,
    subscribe,
    unsubscribe,
)


# ── Step 060: test_add_and_get_user ──────────────────────────────


@pytest.mark.asyncio
async def test_add_and_get_user(db: Database) -> None:
    await add_user(db, user_id=1, username="alice", first_name="Alice")

    user = await get_user(db, user_id=1)

    assert user is not None
    assert user.user_id == 1
    assert user.username == "alice"
    assert user.first_name == "Alice"
    assert user.is_paused is False
    assert user.created_at is not None


# ── Step 061: test_add_user_duplicate ────────────────────────────


@pytest.mark.asyncio
async def test_add_user_duplicate(db: Database) -> None:
    await add_user(db, user_id=1, username="alice", first_name="Alice")
    await add_user(db, user_id=1, username="alice_v2", first_name="Alice V2")

    user = await get_user(db, user_id=1)

    assert user is not None
    # INSERT OR IGNORE keeps the first insert; the duplicate is silently ignored.
    assert user.username == "alice"
    assert user.first_name == "Alice"


# ── Step 062: test_set_user_paused ───────────────────────────────


@pytest.mark.asyncio
async def test_set_user_paused(db: Database) -> None:
    await add_user(db, user_id=1, username="alice", first_name="Alice")

    await set_user_paused(db, user_id=1, is_paused=True)
    user = await get_user(db, user_id=1)
    assert user is not None
    assert user.is_paused is True

    await set_user_paused(db, user_id=1, is_paused=False)
    user = await get_user(db, user_id=1)
    assert user is not None
    assert user.is_paused is False


# ── Step 063: test_add_channel_and_get ───────────────────────────


@pytest.mark.asyncio
async def test_add_channel_and_get(db: Database) -> None:
    await add_channel(db, channel_id=-1001, username="news_ch", title="News Channel")

    channel = await get_channel(db, channel_id=-1001)

    assert channel is not None
    assert channel.channel_id == -1001
    assert channel.username == "news_ch"
    assert channel.title == "News Channel"
    assert channel.is_joined is False
    assert channel.subscriber_count == 0
    assert channel.last_message_id == 0
    assert channel.poll_interval == 120
    assert channel.created_at is not None


# ── Step 064: test_subscribe_and_unsubscribe ─────────────────────


@pytest.mark.asyncio
async def test_subscribe_and_unsubscribe(db: Database) -> None:
    await add_user(db, user_id=1, username="alice", first_name="Alice")
    await add_channel(db, channel_id=-1001, username="news_ch", title="News")

    await subscribe(db, user_id=1, channel_id=-1001)
    channel = await get_channel(db, channel_id=-1001)
    assert channel is not None
    assert channel.subscriber_count == 1

    await unsubscribe(db, user_id=1, channel_id=-1001)
    channel = await get_channel(db, channel_id=-1001)
    assert channel is not None
    assert channel.subscriber_count == 0


# ── Step 065: test_get_user_subscriptions ────────────────────────


@pytest.mark.asyncio
async def test_get_user_subscriptions(db: Database) -> None:
    await add_user(db, user_id=1, username="alice", first_name="Alice")
    await add_channel(db, channel_id=-1001, username="ch_a", title="Channel A")
    await add_channel(db, channel_id=-1002, username="ch_b", title="Channel B")

    await subscribe(db, user_id=1, channel_id=-1001)
    await subscribe(db, user_id=1, channel_id=-1002)

    subs = await get_user_subscriptions(db, user_id=1)

    assert len(subs) == 2
    sub_ids = {ch.channel_id for ch in subs}
    assert sub_ids == {-1001, -1002}


# ── Step 066: test_get_active_subscribers ────────────────────────


@pytest.mark.asyncio
async def test_get_active_subscribers(db: Database) -> None:
    await add_user(db, user_id=1, username="alice", first_name="Alice")
    await add_user(db, user_id=2, username="bob", first_name="Bob")
    await add_user(db, user_id=3, username="carol", first_name="Carol")
    await add_channel(db, channel_id=-1001, username="news", title="News")

    await subscribe(db, user_id=1, channel_id=-1001)
    await subscribe(db, user_id=2, channel_id=-1001)
    await subscribe(db, user_id=3, channel_id=-1001)

    # Pause user 2
    await set_user_paused(db, user_id=2, is_paused=True)

    active = await get_active_subscribers(db, channel_id=-1001)

    assert sorted(active) == [1, 3]


# ── Step 067: test_is_forwarded_and_mark ─────────────────────────


@pytest.mark.asyncio
async def test_is_forwarded_and_mark(db: Database) -> None:
    await add_user(db, user_id=1, username="alice", first_name="Alice")
    await add_channel(db, channel_id=-1001, username="news", title="News")

    result = await is_forwarded(db, channel_id=-1001, message_id=42, user_id=1)
    assert result is False

    await mark_forwarded(db, channel_id=-1001, message_id=42, user_id=1)

    result = await is_forwarded(db, channel_id=-1001, message_id=42, user_id=1)
    assert result is True


# ── Step 068: test_cleanup_old_forwarded ─────────────────────────


@pytest.mark.asyncio
async def test_cleanup_old_forwarded(db: Database) -> None:
    await add_user(db, user_id=1, username="alice", first_name="Alice")
    await add_channel(db, channel_id=-1001, username="news", title="News")

    # Insert a forwarded record with a timestamp 30 days in the past.
    await db._conn.execute(
        "INSERT INTO forwarded_messages (channel_id, message_id, user_id, forwarded_at) "
        "VALUES (?, ?, ?, datetime('now', '-30 days'))",
        (-1001, 100, 1),
    )
    # Insert a recent forwarded record (should survive cleanup).
    await mark_forwarded(db, channel_id=-1001, message_id=200, user_id=1)
    await db._conn.commit()

    deleted = await cleanup_old_forwarded(db, days=7)

    assert deleted == 1
    # The old one is gone.
    assert await is_forwarded(db, channel_id=-1001, message_id=100, user_id=1) is False
    # The recent one is still there.
    assert await is_forwarded(db, channel_id=-1001, message_id=200, user_id=1) is True


# ── Step 069: test_seed_catalog ──────────────────────────────────


@pytest.mark.asyncio
async def test_seed_catalog(db: Database) -> None:
    entries = [
        CatalogEntry(channel_username="@tech", title="Tech News", category="tech"),
        CatalogEntry(
            channel_username="@sports",
            title="Sports Daily",
            category="sports",
            tags="football,basketball",
        ),
    ]

    await seed_catalog(db, entries)

    cursor = await db._conn.execute("SELECT COUNT(*) FROM catalog")
    row = await cursor.fetchone()
    assert row[0] == 2


# ── Step 070: test_search_catalog ────────────────────────────────


@pytest.mark.asyncio
async def test_search_catalog(db: Database) -> None:
    entries = [
        CatalogEntry(channel_username="@tech1", title="Tech One", category="tech"),
        CatalogEntry(channel_username="@tech2", title="Tech Two", category="tech"),
        CatalogEntry(
            channel_username="@sports",
            title="Sports Daily",
            category="sports",
        ),
    ]
    await seed_catalog(db, entries)

    results = await search_catalog(db, category="tech")

    assert len(results) == 2
    usernames = {e.channel_username for e in results}
    assert usernames == {"@tech1", "@tech2"}

    results = await search_catalog(db, category="sports")
    assert len(results) == 1
    assert results[0].channel_username == "@sports"

    results = await search_catalog(db, category="nonexistent")
    assert len(results) == 0


# ── Step 071: test_user_topics ───────────────────────────────────


@pytest.mark.asyncio
async def test_user_topics(db: Database) -> None:
    await add_user(db, user_id=1, username="alice", first_name="Alice")

    await add_user_topic(db, user_id=1, topic_id="python")
    await add_user_topic(db, user_id=1, topic_id="rust")
    await add_user_topic(db, user_id=1, topic_id="go")

    topics = await get_user_topics(db, user_id=1)
    assert sorted(topics) == ["go", "python", "rust"]

    await remove_user_topic(db, user_id=1, topic_id="rust")

    topics = await get_user_topics(db, user_id=1)
    assert sorted(topics) == ["go", "python"]
