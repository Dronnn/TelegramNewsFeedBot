from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest

from bot.channel_monitor.client import resolve_channel
from bot.db.queries import (
    add_channel,
    delete_channel,
    get_channel,
    get_channel_subscriber_count,
    get_joined_channel_ids,
    set_channel_joined,
)

if TYPE_CHECKING:
    from telethon import TelegramClient

    from bot.config import Config
    from bot.db.database import Database
    from bot.db.models import Channel

log = logging.getLogger(__name__)


class ChannelManager:
    def __init__(
        self, telethon_client: TelegramClient, db: Database, config: Config,
    ) -> None:
        self.client = telethon_client
        self.db = db
        self.config = config
        self.joined_channels: set[int] = set()

    async def load_joined_channels(self) -> None:
        ids = await get_joined_channel_ids(self.db)
        self.joined_channels = set(ids)
        log.info("Loaded %d joined channels", len(self.joined_channels))

    async def resolve_and_add_channel(self, channel_ref: str) -> Channel:
        channel_id, username, title = await resolve_channel(
            self.client, channel_ref,
        )
        await add_channel(self.db, channel_id, username, title)
        channel = await get_channel(self.db, channel_id)
        if channel is None:
            raise RuntimeError(
                f"Channel {channel_ref} (id={channel_id}) was added but not found in DB"
            )
        log.info("Resolved channel %s -> %d (%s)", channel_ref, channel_id, title)
        return channel

    async def on_subscription_change(self, channel_id: int) -> None:
        count = await get_channel_subscriber_count(self.db, channel_id)

        if count == 0:
            if channel_id in self.joined_channels:
                try:
                    await self.client(LeaveChannelRequest(channel_id))
                except Exception:
                    log.exception(
                        "Failed to leave channel %d, cleaning up anyway",
                        channel_id,
                    )
                self.joined_channels.discard(channel_id)
                await set_channel_joined(self.db, channel_id, False)
                log.info("Left channel %d (no subscribers)", channel_id)
            await delete_channel(self.db, channel_id)
            log.info("Deleted channel %d from DB", channel_id)
            return

        is_joined = channel_id in self.joined_channels

        if count >= self.config.join_threshold and not is_joined:
            try:
                await self.client(JoinChannelRequest(channel_id))
            except Exception:
                log.exception("Failed to join channel %d", channel_id)
                return
            await set_channel_joined(self.db, channel_id, True)
            self.joined_channels.add(channel_id)
            log.info("Joined channel %d (count=%d)", channel_id, count)

        elif count < self.config.join_threshold and is_joined:
            try:
                await self.client(LeaveChannelRequest(channel_id))
            except Exception:
                log.exception("Failed to leave channel %d", channel_id)
                return
            await set_channel_joined(self.db, channel_id, False)
            self.joined_channels.discard(channel_id)
            log.info("Left channel %d (count=%d)", channel_id, count)
