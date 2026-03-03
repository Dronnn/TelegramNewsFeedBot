from __future__ import annotations

import pytest

from bot.db import queries


class TestPauseResume:
    @pytest.mark.asyncio
    async def test_pause_sets_user_paused_true(self, db):
        user_id = 500
        await queries.add_user(db, user_id, "pauseuser", "Pause")

        await queries.set_user_paused(db, user_id, True)

        user = await queries.get_user(db, user_id)
        assert user is not None
        assert user.is_paused is True

    @pytest.mark.asyncio
    async def test_resume_sets_user_paused_false(self, db):
        user_id = 501
        await queries.add_user(db, user_id, "resumeuser", "Resume")

        await queries.set_user_paused(db, user_id, True)
        await queries.set_user_paused(db, user_id, False)

        user = await queries.get_user(db, user_id)
        assert user is not None
        assert user.is_paused is False

    @pytest.mark.asyncio
    async def test_pause_excludes_from_active_subscribers(self, db):
        user_id = 502
        channel_id = 8001

        await queries.add_user(db, user_id, "excl_user", "Excl")
        await queries.add_channel(db, channel_id, "excl_ch", "Excl Channel")
        await queries.subscribe(db, user_id, channel_id)

        active = await queries.get_active_subscribers(db, channel_id)
        assert user_id in active

        await queries.set_user_paused(db, user_id, True)

        active = await queries.get_active_subscribers(db, channel_id)
        assert user_id not in active

    @pytest.mark.asyncio
    async def test_resume_restores_active_subscriber(self, db):
        user_id = 503
        channel_id = 8002

        await queries.add_user(db, user_id, "rest_user", "Rest")
        await queries.add_channel(db, channel_id, "rest_ch", "Rest Channel")
        await queries.subscribe(db, user_id, channel_id)

        await queries.set_user_paused(db, user_id, True)
        await queries.set_user_paused(db, user_id, False)

        active = await queries.get_active_subscribers(db, channel_id)
        assert user_id in active

    @pytest.mark.asyncio
    async def test_default_user_is_not_paused(self, db):
        user_id = 504
        await queries.add_user(db, user_id, "default_user", "Default")

        user = await queries.get_user(db, user_id)
        assert user is not None
        assert user.is_paused is False
