from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter

from bot.db import queries
from bot.db.queries import get_channel

if TYPE_CHECKING:
    from aiogram import Bot

    from bot.db.database import Database
    from bot.forwarder.rate_limiter import TokenBucketRateLimiter

logger = logging.getLogger(__name__)


class ForwardingPipeline:
    def __init__(
        self,
        bot: Bot,
        db: Database,
        rate_limiter: TokenBucketRateLimiter,
        num_workers: int = 3,
    ) -> None:
        self.bot = bot
        self.db = db
        self.rate_limiter = rate_limiter
        self.num_workers = num_workers
        self._queue: asyncio.Queue[tuple[int, int, int]] = asyncio.Queue(maxsize=10000)
        self._workers: list[asyncio.Task[None]] = []
        self._retry_counts: dict[tuple[int, int, int], int] = {}
        self._in_progress: set[tuple[int, int, int]] = set()

    async def enqueue(
        self, channel_id: int, message_id: int, user_id: int
    ) -> None:
        await self._queue.put((channel_id, message_id, user_id))

    async def _worker(self) -> None:
        while True:
            channel_id, message_id, user_id = await self._queue.get()
            key = (channel_id, message_id, user_id)
            try:
                if key in self._in_progress:
                    continue
                self._in_progress.add(key)

                if await queries.is_forwarded(
                    self.db, channel_id, message_id, user_id
                ):
                    self._in_progress.discard(key)
                    continue

                await self.rate_limiter.acquire()

                # Use @username for from_chat_id so Bot API can access
                # public channels without being a member.
                channel = await get_channel(self.db, channel_id)
                from_chat: int | str = channel_id
                if channel and channel.username:
                    from_chat = f"@{channel.username}"

                await self.bot.forward_message(
                    chat_id=user_id,
                    from_chat_id=from_chat,
                    message_id=message_id,
                )

                await queries.mark_forwarded(
                    self.db, channel_id, message_id, user_id
                )

                self._in_progress.discard(key)
                self._retry_counts.pop(key, None)

            except TelegramForbiddenError:
                logger.warning(
                    "User %d blocked the bot, pausing delivery", user_id
                )
                await queries.set_user_paused(self.db, user_id, True)
                self._in_progress.discard(key)
                self._retry_counts.pop(key, None)

            except TelegramRetryAfter as exc:
                self._in_progress.discard(key)
                self._retry_counts[key] = self._retry_counts.get(key, 0) + 1
                if self._retry_counts[key] < 3:
                    logger.warning(
                        "Rate limited, retrying after %s seconds (attempt %d/3)",
                        exc.retry_after,
                        self._retry_counts[key],
                    )
                    await asyncio.sleep(exc.retry_after)
                    try:
                        self._queue.put_nowait(key)
                    except asyncio.QueueFull:
                        logger.warning(
                            "Queue full, dropping retry for message %d "
                            "from channel %d to user %d",
                            message_id, channel_id, user_id,
                        )
                        self._retry_counts.pop(key, None)
                else:
                    logger.warning(
                        "Dropping message %d from channel %d to user %d "
                        "after 3 rate-limit retries",
                        message_id,
                        channel_id,
                        user_id,
                    )
                    self._retry_counts.pop(key, None)

            except Exception:
                self._in_progress.discard(key)
                self._retry_counts[key] = self._retry_counts.get(key, 0) + 1
                if self._retry_counts[key] < 3:
                    logger.warning(
                        "Failed to forward message %d from channel %d to user %d "
                        "(attempt %d/3), re-queuing",
                        message_id,
                        channel_id,
                        user_id,
                        self._retry_counts[key],
                    )
                    await asyncio.sleep(1)
                    try:
                        self._queue.put_nowait(key)
                    except asyncio.QueueFull:
                        logger.warning(
                            "Queue full, dropping retry for message %d "
                            "from channel %d to user %d",
                            message_id, channel_id, user_id,
                        )
                        self._retry_counts.pop(key, None)
                else:
                    logger.exception(
                        "Dropping message %d from channel %d to user %d "
                        "after 3 retries",
                        message_id,
                        channel_id,
                        user_id,
                    )
                    self._retry_counts.pop(key, None)

            finally:
                self._queue.task_done()

    async def start(self) -> None:
        for i in range(self.num_workers):
            task = asyncio.create_task(self._worker(), name=f"fwd-worker-{i}")
            self._workers.append(task)
        logger.info("Started %d forwarding workers", self.num_workers)

    async def stop(self) -> None:
        for task in self._workers:
            task.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        logger.info("Stopped forwarding workers")
