from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from telethon.errors import ChannelPrivateError

from bot.db import queries

if TYPE_CHECKING:
    from aiogram import Bot
    from telethon import TelegramClient

    from bot.config import Config
    from bot.db.database import Database
    from bot.db.models import Channel
    from bot.forwarder.pipeline import ForwardingPipeline

logger = logging.getLogger(__name__)


class ChannelPoller:
    """Periodically polls non-joined channels for new messages."""

    def __init__(
        self,
        telethon_client: TelegramClient,
        db: Database,
        pipeline: ForwardingPipeline,
        config: Config,
        bot: Bot,
    ) -> None:
        self.telethon_client = telethon_client
        self.db = db
        self.pipeline = pipeline
        self.config = config
        self.bot = bot

    async def poll_once(self, channel: Channel) -> None:
        """Poll a single channel for new messages since last_message_id."""
        try:
            messages = await self.telethon_client.get_messages(
                channel.channel_id,
                min_id=channel.last_message_id,
                limit=20,
            )
        except ChannelPrivateError:
            logger.warning(
                "Channel %d (%s) is now private, skipping poll",
                channel.channel_id,
                channel.username,
            )
            subscribers = await queries.get_active_subscribers(
                self.db, channel.channel_id,
            )
            for user_id in subscribers:
                try:
                    await self.bot.send_message(
                        user_id,
                        f"Channel @{channel.username} is no longer accessible "
                        f"(private or deleted). You may want to /remove it.",
                    )
                except Exception:
                    logger.warning(
                        "Failed to notify user %d about private channel %d",
                        user_id,
                        channel.channel_id,
                    )
            return

        if not messages:
            await queries.update_channel_polled(self.db, channel.channel_id)
            return

        subscribers = await queries.get_active_subscribers(
            self.db, channel.channel_id,
        )

        max_message_id = channel.last_message_id
        for message in reversed(messages):
            if message.id > max_message_id:
                max_message_id = message.id
            for user_id in subscribers:
                await self.pipeline.enqueue(
                    channel.channel_id, message.id, user_id,
                )

        if max_message_id > channel.last_message_id:
            await queries.update_channel_last_message(
                self.db, channel.channel_id, max_message_id,
            )

        await queries.update_channel_polled(self.db, channel.channel_id)

        logger.info(
            "Polled channel %d (%s): %d new messages for %d subscribers",
            channel.channel_id,
            channel.username,
            len(messages),
            len(subscribers),
        )

    async def run(self) -> None:
        """Infinite loop: poll all non-joined channels, sleep between cycles."""
        while True:
            channels = await queries.get_channels_to_poll(self.db)

            for channel in channels:
                await self.poll_once(channel)
                await asyncio.sleep(0.1)

            await asyncio.sleep(self.config.poll_interval_default)
