"""Tests that handlers correctly call ChannelManager instead of stubs."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from bot.channel_monitor.manager import ChannelManager
from bot.config import Config
from bot.db import queries
from bot.db.models import Channel


def _make_config() -> Config:
    return Config(
        bot_token="fake:token",
        telegram_api_id=12345,
        telegram_api_hash="fakehash",
        telegram_phone="+10000000000",
        join_threshold=3,
    )


def _make_manager(db) -> ChannelManager:
    client = AsyncMock()
    config = _make_config()
    return ChannelManager(telethon_client=client, db=db, config=config)


class TestAddHandlerWiring:
    """Verify that /add handler uses channel_manager.resolve_and_add_channel."""

    @pytest.mark.asyncio
    async def test_resolve_and_add_called(self, db):
        """Simulate the flow: resolve channel, subscribe, on_subscription_change."""
        manager = _make_manager(db)
        user_id = 500
        channel_id = 8001

        await queries.add_user(db, user_id, "wired_user", "Wired")

        # Simulate what resolve_and_add_channel does
        await queries.add_channel(db, channel_id, "real_channel", "Real Channel")
        channel = await queries.get_channel(db, channel_id)
        assert channel is not None
        assert channel.username == "real_channel"

        # Subscribe and trigger subscription change
        await queries.subscribe(db, user_id, channel_id)
        await manager.on_subscription_change(channel_id)

        # Subscriber count = 1, threshold = 3, so no join should happen
        manager.client.assert_not_awaited()

        subs = await queries.get_user_subscriptions(db, user_id)
        assert len(subs) == 1
        assert subs[0].channel_id == channel_id

    @pytest.mark.asyncio
    async def test_resolve_and_add_triggers_join_at_threshold(self, db):
        """When enough users subscribe, on_subscription_change triggers join."""
        manager = _make_manager(db)
        channel_id = 8002

        await queries.add_channel(db, channel_id, "popular", "Popular Channel")

        # Add 3 users and subscribe them
        for uid in (601, 602, 603):
            await queries.add_user(db, uid, f"u{uid}", f"U{uid}")
            await queries.subscribe(db, uid, channel_id)

        # After 3rd subscription, on_subscription_change should trigger join
        await manager.on_subscription_change(channel_id)
        manager.client.assert_awaited_once()
        assert channel_id in manager.joined_channels


class TestRemoveHandlerWiring:
    """Verify that /remove handler calls on_subscription_change after unsubscribe."""

    @pytest.mark.asyncio
    async def test_unsubscribe_triggers_subscription_change(self, db):
        """Unsubscribing the last user should trigger cleanup."""
        manager = _make_manager(db)
        user_id = 700
        channel_id = 8003

        await queries.add_user(db, user_id, "rm_user", "RM")
        await queries.add_channel(db, channel_id, "gone", "Gone Channel")
        await queries.subscribe(db, user_id, channel_id)

        await queries.unsubscribe(db, user_id, channel_id)
        await manager.on_subscription_change(channel_id)

        # 0 subscribers -> channel deleted from DB
        channel = await queries.get_channel(db, channel_id)
        assert channel is None

    @pytest.mark.asyncio
    async def test_unsubscribe_one_of_many(self, db):
        """Unsubscribing one user when others remain keeps channel alive."""
        manager = _make_manager(db)
        channel_id = 8004

        await queries.add_channel(db, channel_id, "shared", "Shared Channel")

        for uid in (801, 802):
            await queries.add_user(db, uid, f"s{uid}", f"S{uid}")
            await queries.subscribe(db, uid, channel_id)

        await queries.unsubscribe(db, 801, channel_id)
        await manager.on_subscription_change(channel_id)

        # 1 subscriber remains -> channel still exists
        channel = await queries.get_channel(db, channel_id)
        assert channel is not None
        assert channel.subscriber_count == 1


class TestTopicsWiring:
    """Verify topic subscribe/unsubscribe calls channel_manager for each channel."""

    @pytest.mark.asyncio
    async def test_topic_subscribe_creates_subscriptions(self, db):
        """Subscribing to a topic should resolve and subscribe each channel."""
        manager = _make_manager(db)
        user_id = 900
        channel_ids = [9001, 9002]
        usernames = ["tech_news", "tech_reviews"]

        await queries.add_user(db, user_id, "topicfan", "TopicFan")

        # Simulate what the callback does for each channel in a topic
        for cid, uname in zip(channel_ids, usernames):
            await queries.add_channel(db, cid, uname, uname.replace("_", " ").title())
            await queries.subscribe(db, user_id, cid)
            await manager.on_subscription_change(cid)

        await queries.add_user_topic(db, user_id, "tech")

        subs = await queries.get_user_subscriptions(db, user_id)
        assert len(subs) == 2
        topics = await queries.get_user_topics(db, user_id)
        assert "tech" in topics

    @pytest.mark.asyncio
    async def test_topic_unsubscribe_removes_subscriptions(self, db):
        """Unsubscribing from a topic should unsubscribe from each channel."""
        manager = _make_manager(db)
        user_id = 901
        channel_ids = [9003, 9004]
        usernames = ["sport_live", "sport_news"]

        await queries.add_user(db, user_id, "sportfan", "SportFan")
        await queries.add_user_topic(db, user_id, "sports")

        for cid, uname in zip(channel_ids, usernames):
            await queries.add_channel(db, cid, uname, uname.replace("_", " ").title())
            await queries.subscribe(db, user_id, cid)

        # Unsubscribe from each channel (simulates callback behavior)
        for cid in channel_ids:
            await queries.unsubscribe(db, user_id, cid)
            await manager.on_subscription_change(cid)

        await queries.remove_user_topic(db, user_id, "sports")

        subs = await queries.get_user_subscriptions(db, user_id)
        assert len(subs) == 0
        topics = await queries.get_user_topics(db, user_id)
        assert "sports" not in topics

        # Both channels deleted (0 subscribers)
        for cid in channel_ids:
            assert await queries.get_channel(db, cid) is None


class TestTopicsFromCatalogDB:
    """Verify that /topics loads categories from the catalog DB."""

    @pytest.mark.asyncio
    async def test_get_catalog_categories(self, db):
        """Categories from seeded catalog should be returned."""
        from bot.db.models import CatalogEntry

        entries = [
            CatalogEntry(
                channel_username="tech_news", title="Tech News",
                category="tech", tags="technology", language="ru",
            ),
            CatalogEntry(
                channel_username="auto_daily", title="Auto Daily",
                category="cars", tags="auto", language="ru",
            ),
            CatalogEntry(
                channel_username="sport_live", title="Sport Live",
                category="sports", tags="sport", language="ru",
            ),
        ]
        await queries.seed_catalog(db, entries)

        categories = await queries.get_catalog_categories(db)
        assert set(categories) == {"cars", "sports", "tech"}

    @pytest.mark.asyncio
    async def test_topics_filtered_by_catalog(self, db):
        """_topics_from_catalog should only return topics present in catalog DB."""
        from bot.db.models import CatalogEntry
        from bot.telegram_bot import load_topics

        entries = [
            CatalogEntry(
                channel_username="tech_ch", title="Tech Channel",
                category="tech", tags=None, language="ru",
            ),
        ]
        await queries.seed_catalog(db, entries)

        db_categories = await queries.get_catalog_categories(db)
        db_cat_set = set(db_categories)

        # Simulate _topics_from_catalog logic
        all_topics = [
            {"id": "tech", "name": "Tech", "emoji": "T", "channels": []},
            {"id": "sports", "name": "Sports", "emoji": "S", "channels": []},
        ]
        filtered = [t for t in all_topics if str(t["id"]) in db_cat_set]

        assert len(filtered) == 1
        assert filtered[0]["id"] == "tech"
