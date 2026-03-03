from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from telethon.tl.types import Channel

from bot.channel_monitor.client import (
    create_telethon_client,
    resolve_channel,
    start_telethon_client,
)
from bot.config import Config


def _make_config() -> Config:
    return Config(
        bot_token="tok",
        telegram_api_id=12345,
        telegram_api_hash="hash",
        telegram_phone="+1234567890",
    )


class TestCreateTelethonClient:
    def test_create_telethon_client(self):
        config = _make_config()

        with patch("bot.channel_monitor.client.TelegramClient") as mock_cls:
            result = create_telethon_client(config)

            mock_cls.assert_called_once_with(
                config.session_name,
                config.telegram_api_id,
                config.telegram_api_hash,
            )
            assert result is mock_cls.return_value


class TestStartTelethonClient:
    @pytest.mark.asyncio
    async def test_start_telethon_client(self):
        mock_client = AsyncMock()
        phone = "+1234567890"

        await start_telethon_client(mock_client, phone)

        mock_client.start.assert_called_once_with(phone=phone)


class TestResolveChannel:
    @staticmethod
    def _make_channel_mock(
        channel_id: int, username: str, title: str,
    ) -> Channel:
        mock = AsyncMock(spec=Channel)
        mock.id = channel_id
        mock.username = username
        mock.title = title
        return mock

    @pytest.mark.asyncio
    async def test_resolve_channel_at_username(self):
        channel = self._make_channel_mock(123, "testchan", "Test Channel")
        mock_client = AsyncMock()
        mock_client.get_entity = AsyncMock(return_value=channel)

        result = await resolve_channel(mock_client, "@testchan")

        mock_client.get_entity.assert_called_once_with("testchan")
        assert result == (123, "testchan", "Test Channel")

    @pytest.mark.asyncio
    async def test_resolve_channel_tme_link(self):
        channel = self._make_channel_mock(123, "testchan", "Test Channel")
        mock_client = AsyncMock()
        mock_client.get_entity = AsyncMock(return_value=channel)

        result = await resolve_channel(mock_client, "https://t.me/testchan")

        mock_client.get_entity.assert_called_once_with("testchan")
        assert result == (123, "testchan", "Test Channel")

    @pytest.mark.asyncio
    async def test_resolve_channel_plain(self):
        channel = self._make_channel_mock(123, "testchan", "Test Channel")
        mock_client = AsyncMock()
        mock_client.get_entity = AsyncMock(return_value=channel)

        result = await resolve_channel(mock_client, "testchan")

        mock_client.get_entity.assert_called_once_with("testchan")
        assert result == (123, "testchan", "Test Channel")
