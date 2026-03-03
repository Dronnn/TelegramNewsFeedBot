from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter

from bot.db import queries

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
        self._queue: asyncio.Queue[tuple[int, int, int]] = asyncio.Queue()
        self._workers: list[asyncio.Task[None]] = []

    async def enqueue(
        self, channel_id: int, message_id: int, user_id: int
    ) -> None:
        await self._queue.put((channel_id, message_id, user_id))

    async def _worker(self) -> None:
        while True:
            channel_id, message_id, user_id = await self._queue.get()
            try:
                if await queries.is_forwarded(
                    self.db, channel_id, message_id, user_id
                ):
                    continue

                await self.rate_limiter.acquire()

                await self.bot.forward_message(
                    chat_id=user_id,
                    from_chat_id=channel_id,
                    message_id=message_id,
                )

                await queries.mark_forwarded(
                    self.db, channel_id, message_id, user_id
                )

            except TelegramForbiddenError:
                logger.warning(
                    "User %d blocked the bot, pausing delivery", user_id
                )
                await queries.set_user_paused(self.db, user_id, True)

            except TelegramRetryAfter as exc:
                logger.warning(
                    "Rate limited, retrying after %s seconds",
                    exc.retry_after,
                )
                await self._queue.put((channel_id, message_id, user_id))
                await asyncio.sleep(exc.retry_after)

            except Exception:
                logger.exception(
                    "Failed to forward message %d from channel %d to user %d",
                    message_id,
                    channel_id,
                    user_id,
                )

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
