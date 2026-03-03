from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from telethon import events

from bot.db import queries

if TYPE_CHECKING:
    from telethon import TelegramClient

    from bot.channel_monitor.manager import ChannelManager
    from bot.db.database import Database
    from bot.forwarder.pipeline import ForwardingPipeline

logger = logging.getLogger(__name__)


async def setup_event_handler(
    telethon_client: TelegramClient,
    channel_manager: ChannelManager,
    pipeline: ForwardingPipeline,
    db: Database,
) -> None:
    """Register a Telethon handler that forwards new channel messages to subscribers."""

    async def _on_new_message(event: events.NewMessage.Event) -> None:
        try:
            if event.chat_id not in channel_manager.joined_channels:
                return

            await queries.update_channel_last_message(db, event.chat_id, event.id)

            subscribers = await queries.get_active_subscribers(db, event.chat_id)

            for user_id in subscribers:
                await pipeline.enqueue(event.chat_id, event.id, user_id)

            logger.info(
                "Enqueued message %d from channel %d for %d subscribers",
                event.id,
                event.chat_id,
                len(subscribers),
            )
        except Exception:
            logger.exception(
                "Error handling new message from channel %d", event.chat_id,
            )

    telethon_client.add_event_handler(
        _on_new_message,
        events.NewMessage(incoming=True, func=lambda e: e.is_channel),
    )
    logger.info("Registered NewMessage event handler (channels only)")
