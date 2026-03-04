from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from bot.db import queries
from bot.forwarder.pipeline import ForwardingPipeline
from bot.forwarder.rate_limiter import TokenBucketRateLimiter


def _make_forbidden_error() -> Exception:
    """Build a TelegramForbiddenError without depending on internal constructors."""
    from aiogram.exceptions import TelegramForbiddenError

    method = MagicMock()
    method.__class__.__name__ = "ForwardMessage"
    try:
        return TelegramForbiddenError(method=method, message="Forbidden: bot was blocked by the user")
    except TypeError:
        # Fallback: create via __new__ and set attrs manually
        exc = TelegramForbiddenError.__new__(TelegramForbiddenError)
        Exception.__init__(exc, "Forbidden: bot was blocked by the user")
        exc.method = method
        exc.message = "Forbidden: bot was blocked by the user"
        return exc


def _make_pipeline(bot: AsyncMock, db, *, num_workers: int = 1) -> ForwardingPipeline:
    rate_limiter = TokenBucketRateLimiter(rate=1000, burst=1000)
    telethon_client = AsyncMock()
    return ForwardingPipeline(
        bot=bot,
        db=db,
        rate_limiter=rate_limiter,
        telethon_client=telethon_client,
        num_workers=num_workers,
    )


async def _run_one_task(pipeline: ForwardingPipeline, timeout: float = 2.0) -> None:
    """Start the pipeline, wait until the queue is drained, then stop."""
    await pipeline.start()
    try:
        await asyncio.wait_for(pipeline._queue.join(), timeout=timeout)
    finally:
        await pipeline.stop()


@pytest.mark.asyncio
async def test_enqueue_and_forward(db):
    """Worker forwards the message and marks it as forwarded."""
    user_id, channel_id, message_id = 100, -1001, 42

    await queries.add_user(db, user_id, "testuser", "Test")

    bot = AsyncMock()
    pipeline = _make_pipeline(bot, db)

    await pipeline.enqueue(channel_id, message_id, user_id)
    await _run_one_task(pipeline)

    bot.forward_message.assert_awaited_once_with(
        chat_id=user_id,
        from_chat_id=channel_id,
        message_id=message_id,
    )
    assert await queries.is_forwarded(db, channel_id, message_id, user_id)


@pytest.mark.asyncio
async def test_dedup_skip(db):
    """Already-forwarded message is skipped; forward_message is not called."""
    user_id, channel_id, message_id = 101, -1002, 43

    await queries.add_user(db, user_id, "dupuser", "Dup")
    await queries.mark_forwarded(db, channel_id, message_id, user_id)

    bot = AsyncMock()
    pipeline = _make_pipeline(bot, db)

    await pipeline.enqueue(channel_id, message_id, user_id)
    await _run_one_task(pipeline)

    bot.forward_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_user_blocked(db):
    """TelegramForbiddenError pauses the user."""
    user_id, channel_id, message_id = 102, -1003, 44

    await queries.add_user(db, user_id, "blocked", "Blocked")

    bot = AsyncMock()
    bot.forward_message.side_effect = _make_forbidden_error()

    pipeline = _make_pipeline(bot, db)

    await pipeline.enqueue(channel_id, message_id, user_id)
    await _run_one_task(pipeline)

    user = await queries.get_user(db, user_id)
    assert user is not None
    assert user.is_paused is True


@pytest.mark.asyncio
async def test_retry_and_drop_after_max_retries(db):
    """Generic exception retries up to 3 times, then drops the message."""
    user_id, channel_id, message_id = 103, -1004, 45

    await queries.add_user(db, user_id, "retryuser", "Retry")

    bot = AsyncMock()
    bot.forward_message.side_effect = RuntimeError("transient failure")

    pipeline = _make_pipeline(bot, db)

    await pipeline.enqueue(channel_id, message_id, user_id)
    await _run_one_task(pipeline, timeout=5.0)

    assert bot.forward_message.await_count == 3
    assert not await queries.is_forwarded(db, channel_id, message_id, user_id)
