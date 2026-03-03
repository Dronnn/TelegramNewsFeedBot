from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from bot.config import Config
from bot.db.database import Database
from bot.db.queries import add_channel, get_channel, set_channel_joined


def _make_config() -> Config:
    return Config(
        bot_token="tok",
        telegram_api_id=12345,
        telegram_api_hash="hash",
        telegram_phone="+1234567890",
        join_threshold=3,
    )


async def _seed_channel(
    db: Database,
    channel_id: int,
    *,
    subscriber_count: int = 0,
    is_joined: bool = False,
) -> None:
    await add_channel(db, channel_id=channel_id, username="test", title="Test Channel")
    if subscriber_count:
        await db._conn.execute(
            "UPDATE channels SET subscriber_count = ? WHERE channel_id = ?",
            (subscriber_count, channel_id),
        )
    if is_joined:
        await set_channel_joined(db, channel_id, True)
    await db._conn.commit()


class TestLoadJoinedChannels:
    @pytest.mark.asyncio
    async def test_load_joined_channels(self, db: Database) -> None:
        from bot.channel_monitor.manager import ChannelManager

        for cid in (1, 2, 3):
            await _seed_channel(db, cid, is_joined=True)
        await _seed_channel(db, 4, is_joined=False)

        mgr = ChannelManager(telethon_client=AsyncMock(), db=db, config=_make_config())
        await mgr.load_joined_channels()

        assert mgr.joined_channels == {1, 2, 3}


class TestResolveAndAddChannel:
    @pytest.mark.asyncio
    @patch("bot.channel_monitor.manager.resolve_channel", new_callable=AsyncMock)
    async def test_resolve_and_add_channel(
        self, mock_resolve: AsyncMock, db: Database
    ) -> None:
        from bot.channel_monitor.manager import ChannelManager

        mock_resolve.return_value = (123, "test", "Test Channel")

        mgr = ChannelManager(telethon_client=AsyncMock(), db=db, config=_make_config())
        result = await mgr.resolve_and_add_channel("@test")

        mock_resolve.assert_called_once()
        assert result is not None
        assert result.channel_id == 123
        assert result.username == "test"
        assert result.title == "Test Channel"

        stored = await get_channel(db, 123)
        assert stored is not None
        assert stored.channel_id == 123


class TestOnSubscriptionChange:
    @pytest.mark.asyncio
    async def test_join_on_threshold(self, db: Database) -> None:
        from bot.channel_monitor.manager import ChannelManager

        await _seed_channel(db, 100, subscriber_count=3, is_joined=False)

        client = AsyncMock()
        mgr = ChannelManager(telethon_client=client, db=db, config=_make_config())

        with patch("bot.channel_monitor.manager.JoinChannelRequest") as MockJoin:
            await mgr.on_subscription_change(100)

        MockJoin.assert_called_once_with(100)
        client.assert_called_once_with(MockJoin.return_value)

        channel = await get_channel(db, 100)
        assert channel is not None
        assert channel.is_joined is True
        assert 100 in mgr.joined_channels

    @pytest.mark.asyncio
    async def test_leave_on_below_threshold(self, db: Database) -> None:
        from bot.channel_monitor.manager import ChannelManager

        await _seed_channel(db, 200, subscriber_count=2, is_joined=True)

        client = AsyncMock()
        mgr = ChannelManager(telethon_client=client, db=db, config=_make_config())
        mgr.joined_channels.add(200)

        with patch("bot.channel_monitor.manager.LeaveChannelRequest") as MockLeave:
            await mgr.on_subscription_change(200)

        MockLeave.assert_called_once_with(200)
        client.assert_called_once_with(MockLeave.return_value)

        channel = await get_channel(db, 200)
        assert channel is not None
        assert channel.is_joined is False
        assert 200 not in mgr.joined_channels

    @pytest.mark.asyncio
    async def test_cleanup_on_zero(self, db: Database) -> None:
        from bot.channel_monitor.manager import ChannelManager

        await _seed_channel(db, 300, subscriber_count=0, is_joined=False)

        mgr = ChannelManager(telethon_client=AsyncMock(), db=db, config=_make_config())
        await mgr.on_subscription_change(300)

        channel = await get_channel(db, 300)
        assert channel is None

    @pytest.mark.asyncio
    async def test_no_change_below_threshold_not_joined(self, db: Database) -> None:
        from bot.channel_monitor.manager import ChannelManager

        await _seed_channel(db, 400, subscriber_count=1, is_joined=False)

        client = AsyncMock()
        mgr = ChannelManager(telethon_client=client, db=db, config=_make_config())

        with (
            patch("bot.channel_monitor.manager.JoinChannelRequest") as MockJoin,
            patch("bot.channel_monitor.manager.LeaveChannelRequest") as MockLeave,
        ):
            await mgr.on_subscription_change(400)

        MockJoin.assert_not_called()
        MockLeave.assert_not_called()
        client.assert_not_called()

        channel = await get_channel(db, 400)
        assert channel is not None
        assert channel.is_joined is False
