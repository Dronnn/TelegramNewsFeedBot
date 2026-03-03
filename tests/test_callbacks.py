from __future__ import annotations

import pytest

from bot.db import queries


class TestCallbackRemoveChannel:
    @pytest.mark.asyncio
    async def test_unsubscribe_removes_subscription(self, db):
        user_id = 100
        channel_id = 9001

        await queries.add_user(db, user_id, "cbuser", "CB")
        await queries.add_channel(db, channel_id, "testch", "Test Channel")
        await queries.subscribe(db, user_id, channel_id)

        subs = await queries.get_user_subscriptions(db, user_id)
        assert len(subs) == 1

        await queries.unsubscribe(db, user_id, channel_id)
        subs = await queries.get_user_subscriptions(db, user_id)
        assert len(subs) == 0

    @pytest.mark.asyncio
    async def test_unsubscribe_updates_count(self, db):
        user_id = 101
        channel_id = 9002

        await queries.add_user(db, user_id, "cbuser2", "CB2")
        await queries.add_channel(db, channel_id, "testch2", "Test Channel 2")
        await queries.subscribe(db, user_id, channel_id)

        count = await queries.get_channel_subscriber_count(db, channel_id)
        assert count == 1

        await queries.unsubscribe(db, user_id, channel_id)
        count = await queries.get_channel_subscriber_count(db, channel_id)
        assert count == 0


class TestCallbackTopics:
    @pytest.mark.asyncio
    async def test_subscribe_topic(self, db):
        user_id = 200
        await queries.add_user(db, user_id, "topicuser", "TU")
        await queries.add_user_topic(db, user_id, "tech")

        topics = await queries.get_user_topics(db, user_id)
        assert "tech" in topics

    @pytest.mark.asyncio
    async def test_unsubscribe_topic(self, db):
        user_id = 201
        await queries.add_user(db, user_id, "topicuser2", "TU2")
        await queries.add_user_topic(db, user_id, "sports")
        await queries.remove_user_topic(db, user_id, "sports")

        topics = await queries.get_user_topics(db, user_id)
        assert "sports" not in topics

    @pytest.mark.asyncio
    async def test_subscribe_topic_idempotent(self, db):
        user_id = 202
        await queries.add_user(db, user_id, "topicuser3", "TU3")
        await queries.add_user_topic(db, user_id, "music")
        await queries.add_user_topic(db, user_id, "music")

        topics = await queries.get_user_topics(db, user_id)
        assert topics.count("music") == 1
