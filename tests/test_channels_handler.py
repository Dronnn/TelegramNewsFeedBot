from __future__ import annotations

import pytest

from bot.db import queries
from bot.telegram_bot.handlers.channels import _parse_channel_ref


class TestParseChannelRef:
    def test_at_username(self):
        assert _parse_channel_ref("/add @durov") == "durov"

    def test_tme_link(self):
        assert _parse_channel_ref("/add t.me/durov") == "durov"

    def test_https_tme_link(self):
        assert _parse_channel_ref("/add https://t.me/durov") == "durov"

    def test_http_tme_link(self):
        assert _parse_channel_ref("/add http://t.me/durov") == "durov"

    def test_no_argument(self):
        assert _parse_channel_ref("/add") is None

    def test_invalid_argument(self):
        assert _parse_channel_ref("/add ???") is None

    def test_remove_at_username(self):
        assert _parse_channel_ref("/remove @news_channel") == "news_channel"


class TestChannelHandlersIntegration:
    @pytest.mark.asyncio
    async def test_add_and_list_subscription(self, db):
        user_id = 111
        channel_id = 9001
        username = "test_channel"

        await queries.add_user(db, user_id, "user1", "User")
        await queries.add_channel(db, channel_id, username, username)
        await queries.subscribe(db, user_id, channel_id)

        subs = await queries.get_user_subscriptions(db, user_id)
        assert len(subs) == 1
        assert subs[0].username == username

    @pytest.mark.asyncio
    async def test_remove_subscription(self, db):
        user_id = 222
        channel_id = 9002
        username = "remove_me"

        await queries.add_user(db, user_id, "user2", "User2")
        await queries.add_channel(db, channel_id, username, username)
        await queries.subscribe(db, user_id, channel_id)

        channel = await queries.get_channel_by_username(db, username)
        assert channel is not None

        await queries.unsubscribe(db, user_id, channel.channel_id)
        subs = await queries.get_user_subscriptions(db, user_id)
        assert len(subs) == 0

    @pytest.mark.asyncio
    async def test_remove_not_subscribed(self, db):
        user_id = 333
        channel_id = 9003
        username = "not_subbed"

        await queries.add_user(db, user_id, "user3", "User3")
        await queries.add_channel(db, channel_id, username, username)

        subs = await queries.get_user_subscriptions(db, user_id)
        assert not any(s.channel_id == channel_id for s in subs)

    @pytest.mark.asyncio
    async def test_list_empty(self, db):
        user_id = 444
        await queries.add_user(db, user_id, "user4", "User4")
        subs = await queries.get_user_subscriptions(db, user_id)
        assert subs == []
