from __future__ import annotations

import pytest

from bot.db import queries
from bot.telegram_bot.handlers.channels import _parse_channel_ref, _resolve_channel


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


class TestResolveChannelStub:
    @pytest.mark.asyncio
    async def test_returns_tuple(self):
        channel_id, username, title = await _resolve_channel("durov")
        assert isinstance(channel_id, int)
        assert username == "durov"
        assert title == "durov"

    @pytest.mark.asyncio
    async def test_deterministic(self):
        r1 = await _resolve_channel("test_ch")
        r2 = await _resolve_channel("test_ch")
        assert r1 == r2


class TestChannelHandlersIntegration:
    @pytest.mark.asyncio
    async def test_add_and_list_subscription(self, db):
        user_id = 111
        username = "test_channel"
        channel_id, _, title = await _resolve_channel(username)

        await queries.add_user(db, user_id, "user1", "User")
        await queries.add_channel(db, channel_id, username, title)
        await queries.subscribe(db, user_id, channel_id)

        subs = await queries.get_user_subscriptions(db, user_id)
        assert len(subs) == 1
        assert subs[0].username == username

    @pytest.mark.asyncio
    async def test_remove_subscription(self, db):
        user_id = 222
        username = "remove_me"
        channel_id, _, title = await _resolve_channel(username)

        await queries.add_user(db, user_id, "user2", "User2")
        await queries.add_channel(db, channel_id, username, title)
        await queries.subscribe(db, user_id, channel_id)

        channel = await queries.get_channel_by_username(db, username)
        assert channel is not None

        await queries.unsubscribe(db, user_id, channel.channel_id)
        subs = await queries.get_user_subscriptions(db, user_id)
        assert len(subs) == 0

    @pytest.mark.asyncio
    async def test_remove_not_subscribed(self, db):
        user_id = 333
        username = "not_subbed"
        channel_id, _, title = await _resolve_channel(username)

        await queries.add_user(db, user_id, "user3", "User3")
        await queries.add_channel(db, channel_id, username, title)

        subs = await queries.get_user_subscriptions(db, user_id)
        assert not any(s.channel_id == channel_id for s in subs)

    @pytest.mark.asyncio
    async def test_list_empty(self, db):
        user_id = 444
        await queries.add_user(db, user_id, "user4", "User4")
        subs = await queries.get_user_subscriptions(db, user_id)
        assert subs == []
