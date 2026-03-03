from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from bot.channel_monitor.poller import ChannelPoller
from bot.db.models import Channel


def _make_channel(
    channel_id: int = -1001,
    username: str = "testchan",
    last_message_id: int = 100,
) -> Channel:
    return Channel(
        channel_id=channel_id,
        username=username,
        title="Test Channel",
        is_joined=False,
        subscriber_count=2,
        last_message_id=last_message_id,
        poll_interval=120,
        last_polled_at=None,
        created_at=None,
    )


def _make_message(message_id: int) -> Mock:
    msg = Mock()
    msg.id = message_id
    return msg


def _make_poller(
    telethon_client: AsyncMock | None = None,
    db: AsyncMock | None = None,
    pipeline: AsyncMock | None = None,
    bot: AsyncMock | None = None,
) -> ChannelPoller:
    if telethon_client is None:
        telethon_client = AsyncMock()
    if db is None:
        db = AsyncMock()
    if pipeline is None:
        pipeline = AsyncMock()
    if bot is None:
        bot = AsyncMock()
    config = Mock()
    config.poll_interval_default = 120
    return ChannelPoller(
        telethon_client=telethon_client,
        db=db,
        pipeline=pipeline,
        config=config,
        bot=bot,
    )


@pytest.mark.asyncio
async def test_poll_once_new_messages():
    """poll_once fetches new messages and enqueues them for each subscriber."""
    channel = _make_channel(channel_id=-1001, last_message_id=100)
    messages = [_make_message(101), _make_message(102)]
    subscribers = [500, 600]

    telethon_client = AsyncMock()
    telethon_client.get_messages.return_value = messages

    pipeline = AsyncMock()

    poller = _make_poller(
        telethon_client=telethon_client,
        pipeline=pipeline,
    )

    with patch("bot.channel_monitor.poller.queries") as mock_queries:
        mock_queries.get_active_subscribers = AsyncMock(return_value=subscribers)
        mock_queries.update_channel_last_message = AsyncMock()
        mock_queries.update_channel_polled = AsyncMock()

        await poller.poll_once(channel)

    telethon_client.get_messages.assert_awaited_once_with(
        -1001, min_id=100, limit=100,
    )

    assert pipeline.enqueue.await_count == 4
    pipeline.enqueue.assert_any_await(-1001, 101, 500)
    pipeline.enqueue.assert_any_await(-1001, 101, 600)
    pipeline.enqueue.assert_any_await(-1001, 102, 500)
    pipeline.enqueue.assert_any_await(-1001, 102, 600)

    mock_queries.update_channel_last_message.assert_awaited_once_with(
        poller.db, -1001, 102,
    )
    mock_queries.update_channel_polled.assert_awaited_once_with(
        poller.db, -1001,
    )


@pytest.mark.asyncio
async def test_poll_once_no_new_messages():
    """poll_once with no new messages does not enqueue anything."""
    channel = _make_channel(channel_id=-1002, last_message_id=50)

    telethon_client = AsyncMock()
    telethon_client.get_messages.return_value = []

    pipeline = AsyncMock()

    poller = _make_poller(
        telethon_client=telethon_client,
        pipeline=pipeline,
    )

    with patch("bot.channel_monitor.poller.queries") as mock_queries:
        mock_queries.update_channel_polled = AsyncMock()

        await poller.poll_once(channel)

    pipeline.enqueue.assert_not_awaited()
    mock_queries.update_channel_polled.assert_awaited_once_with(
        poller.db, -1002,
    )


@pytest.mark.asyncio
async def test_poll_once_channel_private():
    """poll_once catches ChannelPrivateError, notifies subscribers via bot."""
    from telethon.errors import ChannelPrivateError

    channel = _make_channel(channel_id=-1003, username="testchan", last_message_id=10)
    subscribers = [700, 800]

    telethon_client = AsyncMock()
    telethon_client.get_messages.side_effect = ChannelPrivateError(
        request=Mock(),
    )

    pipeline = AsyncMock()
    bot = AsyncMock()

    poller = _make_poller(
        telethon_client=telethon_client,
        pipeline=pipeline,
        bot=bot,
    )

    with patch("bot.channel_monitor.poller.queries") as mock_queries:
        mock_queries.get_active_subscribers = AsyncMock(return_value=subscribers)
        mock_queries.update_channel_polled = AsyncMock()
        mock_queries.update_channel_last_message = AsyncMock()

        await poller.poll_once(channel)

    pipeline.enqueue.assert_not_awaited()
    mock_queries.get_active_subscribers.assert_awaited_once_with(
        poller.db, -1003,
    )
    assert bot.send_message.await_count == 2
    for uid in subscribers:
        bot.send_message.assert_any_await(
            uid,
            "Channel @testchan is no longer accessible "
            "(private or deleted). You may want to /remove it.",
        )
    mock_queries.update_channel_polled.assert_not_awaited()
    mock_queries.update_channel_last_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_polls_all_channels():
    """run() fetches channels to poll and calls poll_once for each."""
    channels = [
        _make_channel(channel_id=-2001, username="chan_a"),
        _make_channel(channel_id=-2002, username="chan_b"),
    ]

    poller = _make_poller()

    poll_call_count = 0

    async def _fake_get_channels_to_poll(db):
        nonlocal poll_call_count
        poll_call_count += 1
        if poll_call_count == 1:
            return channels
        return []

    sleep_call_count = 0

    async def _sleep_side_effect(*args):
        nonlocal sleep_call_count
        sleep_call_count += 1
        if sleep_call_count >= 3:
            raise asyncio.CancelledError

    with patch("bot.channel_monitor.poller.queries") as mock_queries, \
         patch.object(poller, "poll_once", new_callable=AsyncMock) as mock_poll, \
         patch("bot.channel_monitor.poller.asyncio.sleep", side_effect=_sleep_side_effect):

        mock_queries.get_channels_to_poll = AsyncMock(
            side_effect=_fake_get_channels_to_poll,
        )

        with pytest.raises(asyncio.CancelledError):
            await poller.run()

    assert mock_poll.await_count == 2
    mock_poll.assert_any_await(channels[0])
    mock_poll.assert_any_await(channels[1])
