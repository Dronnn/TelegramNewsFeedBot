from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.types import Channel

from bot.db.queries import search_catalog

if TYPE_CHECKING:
    from telethon import TelegramClient

    from bot.db.database import Database
    from bot.db.models import CatalogEntry

log = logging.getLogger(__name__)


class ChannelSearcher:
    """Search for channels in the local catalog and via Telegram API."""

    def __init__(self, telethon_client: TelegramClient, db: Database) -> None:
        self.client = telethon_client
        self.db = db

    async def search_by_topic(self, topic_id: str) -> list[CatalogEntry]:
        """Find channels in the catalog by category (topic_id)."""
        results = await search_catalog(self.db, topic_id)
        log.info(
            "Catalog search for topic '%s': %d result(s)", topic_id, len(results),
        )
        return results

    async def search_telegram(
        self, query: str, limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Search Telegram for public channels matching *query*.

        Returns a list of dicts with keys: channel_id, username, title.
        """
        try:
            result = await self.client(SearchRequest(q=query, limit=limit))
        except Exception:
            log.exception("Telegram search failed for query '%s'", query)
            return []

        channels: list[dict[str, Any]] = []
        for chat in result.chats:
            if not isinstance(chat, Channel):
                continue
            channels.append(
                {
                    "channel_id": chat.id,
                    "username": chat.username or "",
                    "title": getattr(chat, "title", ""),
                },
            )

        log.info(
            "Telegram search for '%s': %d channel(s) found", query, len(channels),
        )
        return channels

    async def search_combined(
        self, topic_id: str, query: str,
    ) -> dict[str, Any]:
        """Search catalog first; if fewer than 5 results, also search Telegram.

        Returns a dict with keys:
            catalog  -- list[CatalogEntry] from the local catalog
            telegram -- list[dict] from Telegram API (may be empty)
        """
        catalog_results = await self.search_by_topic(topic_id)

        telegram_results: list[dict[str, Any]] = []
        if len(catalog_results) < 5:
            log.info(
                "Only %d catalog result(s) for topic '%s'; "
                "supplementing with Telegram search for '%s'",
                len(catalog_results),
                topic_id,
                query,
            )
            telegram_results = await self.search_telegram(query)

        return {
            "catalog": catalog_results,
            "telegram": telegram_results,
        }
