from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from bot.channel_monitor.manager import ChannelManager
from bot.config import Config
from bot.db import queries


def _make_config() -> Config:
    return Config(
        bot_token="fake:token",
        telegram_api_id=12345,
        telegram_api_hash="fakehash",
        telegram_phone="+10000000000",
        join_threshold=3,
    )


def _make_manager(telethon_client: AsyncMock, db, config: Config) -> ChannelManager:
    return ChannelManager(telethon_client=telethon_client, db=db, config=config)


async def _seed_channel(
    db, channel_id: int, subscriber_count: int, is_joined: bool = False,
) -> None:
    """Insert a channel row directly so on_subscription_change can read it."""
    await db._conn.execute(
        "INSERT INTO channels (channel_id, username, title, subscriber_count, is_joined) "
        "VALUES (?, ?, ?, ?, ?)",
        (channel_id, "testchan", "Test Channel", subscriber_count, int(is_joined)),
    )
    await db._conn.commit()


# -- Tests -----------------------------------------------------------------


@pytest.mark.asyncio
async def test_join_on_threshold(db):
    """When subscriber_count >= join_threshold, JoinChannelRequest is sent."""
    channel_id = -1001
    client = AsyncMock()
    config = _make_config()
    manager = _make_manager(client, db, config)

    await _seed_channel(db, channel_id, subscriber_count=3)

    await manager.on_subscription_change(channel_id)

    # Telethon client was called exactly once with a JoinChannelRequest
    client.assert_awaited_once()
    call_args = client.call_args
    request = call_args[0][0]

    from telethon.tl.functions.channels import JoinChannelRequest

    assert isinstance(request, JoinChannelRequest)

    # Manager tracks the channel as joined
    assert channel_id in manager.joined_channels

    # DB flag is set
    channel = await queries.get_channel(db, channel_id)
    assert channel is not None
    assert channel.is_joined is True


@pytest.mark.asyncio
async def test_leave_on_below_threshold(db):
    """When count < join_threshold and channel is joined, LeaveChannelRequest is sent."""
    channel_id = -1002
    client = AsyncMock()
    config = _make_config()
    manager = _make_manager(client, db, config)

    # Channel exists with 2 subscribers (below threshold=3) and is currently joined
    await _seed_channel(db, channel_id, subscriber_count=2, is_joined=True)
    # Pre-populate the in-memory joined set
    manager.joined_channels.add(channel_id)

    await manager.on_subscription_change(channel_id)

    # Telethon client was called exactly once with a LeaveChannelRequest
    client.assert_awaited_once()
    call_args = client.call_args
    request = call_args[0][0]

    from telethon.tl.functions.channels import LeaveChannelRequest

    assert isinstance(request, LeaveChannelRequest)

    # Manager no longer tracks channel as joined
    assert channel_id not in manager.joined_channels

    # DB flag is cleared
    channel = await queries.get_channel(db, channel_id)
    assert channel is not None
    assert channel.is_joined is False


@pytest.mark.asyncio
async def test_cleanup_on_zero(db):
    """When count == 0, channel is left (if joined) and deleted from DB."""
    channel_id = -1003
    client = AsyncMock()
    config = _make_config()
    manager = _make_manager(client, db, config)

    # Channel with 0 subscribers, currently joined
    await _seed_channel(db, channel_id, subscriber_count=0, is_joined=True)
    manager.joined_channels.add(channel_id)

    await manager.on_subscription_change(channel_id)

    # Telethon client was called with LeaveChannelRequest
    client.assert_awaited_once()
    call_args = client.call_args
    request = call_args[0][0]

    from telethon.tl.functions.channels import LeaveChannelRequest

    assert isinstance(request, LeaveChannelRequest)

    # Manager no longer tracks channel
    assert channel_id not in manager.joined_channels

    # Channel row is deleted from DB
    channel = await queries.get_channel(db, channel_id)
    assert channel is None


@pytest.mark.asyncio
async def test_cleanup_on_zero_not_joined(db):
    """When count == 0 and channel is NOT joined, no leave request but still deleted."""
    channel_id = -1004
    client = AsyncMock()
    config = _make_config()
    manager = _make_manager(client, db, config)

    # Channel with 0 subscribers, not joined
    await _seed_channel(db, channel_id, subscriber_count=0, is_joined=False)

    await manager.on_subscription_change(channel_id)

    # Telethon client should NOT have been called (no leave needed)
    client.assert_not_awaited()

    # Channel row is deleted from DB
    channel = await queries.get_channel(db, channel_id)
    assert channel is None


@pytest.mark.asyncio
async def test_no_action_below_threshold_not_joined(db):
    """When count < threshold and not joined, nothing happens."""
    channel_id = -1005
    client = AsyncMock()
    config = _make_config()
    manager = _make_manager(client, db, config)

    await _seed_channel(db, channel_id, subscriber_count=1)

    await manager.on_subscription_change(channel_id)

    # No Telethon call
    client.assert_not_awaited()

    # Channel still exists, still not joined
    channel = await queries.get_channel(db, channel_id)
    assert channel is not None
    assert channel.is_joined is False


@pytest.mark.asyncio
async def test_no_action_at_threshold_already_joined(db):
    """When count >= threshold and already joined, no duplicate join."""
    channel_id = -1006
    client = AsyncMock()
    config = _make_config()
    manager = _make_manager(client, db, config)

    await _seed_channel(db, channel_id, subscriber_count=5, is_joined=True)
    manager.joined_channels.add(channel_id)

    await manager.on_subscription_change(channel_id)

    # No Telethon call (already joined)
    client.assert_not_awaited()

    # Channel still joined
    assert channel_id in manager.joined_channels
