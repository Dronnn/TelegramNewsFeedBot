from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import pytest

from bot.channel_monitor.event_handler import setup_event_handler


def _make_event(chat_id: int, message_id: int) -> Mock:
    event = Mock()
    event.chat_id = chat_id
    event.id = message_id
    return event


@pytest.mark.asyncio
async def test_handler_ignores_non_joined_channel():
    """Event from a channel NOT in joined_channels should be completely ignored."""
    telethon_client = Mock()
    channel_manager = Mock()
    channel_manager.joined_channels = {-1001}
    pipeline = AsyncMock()
    db = AsyncMock()

    await setup_event_handler(telethon_client, channel_manager, pipeline, db)
    handler = telethon_client.add_event_handler.call_args[0][0]

    event = _make_event(chat_id=-9999, message_id=1)
    await handler(event)

    db._conn.execute.assert_not_awaited()
    pipeline.enqueue.assert_not_awaited()


@pytest.mark.asyncio
async def test_handler_forwards_to_subscribers(db):
    """Event from a joined channel should update last_message_id and enqueue for each subscriber."""
    channel_id = -1001
    message_id = 42
    user_ids = [100, 200, 300]

    # Seed the DB with a channel and subscribed users
    await db._conn.execute(
        "INSERT INTO channels (channel_id, username, title, is_joined) VALUES (?, ?, ?, 1)",
        (channel_id, "testchan", "Test Channel"),
    )
    for uid in user_ids:
        await db._conn.execute(
            "INSERT INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
            (uid, f"user{uid}", f"User{uid}"),
        )
        await db._conn.execute(
            "INSERT INTO subscriptions (user_id, channel_id) VALUES (?, ?)",
            (uid, channel_id),
        )
    await db._conn.commit()

    telethon_client = Mock()
    channel_manager = Mock()
    channel_manager.joined_channels = {channel_id}
    pipeline = AsyncMock()

    await setup_event_handler(telethon_client, channel_manager, pipeline, db)
    handler = telethon_client.add_event_handler.call_args[0][0]

    event = _make_event(chat_id=channel_id, message_id=message_id)
    await handler(event)

    # last_message_id should be updated in the DB
    from bot.db import queries

    channel = await queries.get_channel(db, channel_id)
    assert channel is not None
    assert channel.last_message_id == message_id

    # enqueue called once per subscriber
    assert pipeline.enqueue.await_count == len(user_ids)
    for uid in user_ids:
        pipeline.enqueue.assert_any_await(channel_id, message_id, uid)


@pytest.mark.asyncio
async def test_handler_no_subscribers(db):
    """Event from a joined channel with no subscribers should update last_message_id but not enqueue."""
    channel_id = -1002
    message_id = 55

    await db._conn.execute(
        "INSERT INTO channels (channel_id, username, title, is_joined) VALUES (?, ?, ?, 1)",
        (channel_id, "emptychan", "Empty Channel"),
    )
    await db._conn.commit()

    telethon_client = Mock()
    channel_manager = Mock()
    channel_manager.joined_channels = {channel_id}
    pipeline = AsyncMock()

    await setup_event_handler(telethon_client, channel_manager, pipeline, db)
    handler = telethon_client.add_event_handler.call_args[0][0]

    event = _make_event(chat_id=channel_id, message_id=message_id)
    await handler(event)

    # last_message_id should still be updated
    from bot.db import queries

    channel = await queries.get_channel(db, channel_id)
    assert channel is not None
    assert channel.last_message_id == message_id

    # No enqueue calls since there are no subscribers
    pipeline.enqueue.assert_not_awaited()
