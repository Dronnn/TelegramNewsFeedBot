from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher

from bot.channel_monitor.client import create_telethon_client, start_telethon_client
from bot.channel_monitor.event_handler import setup_event_handler
from bot.channel_monitor.manager import ChannelManager
from bot.channel_monitor.poller import ChannelPoller
from bot.config import load_config
from bot.db.database import Database
from bot.db.queries import cleanup_old_forwarded
from bot.forwarder.pipeline import ForwardingPipeline
from bot.forwarder.rate_limiter import TokenBucketRateLimiter
from bot.telegram_bot.handlers import register_all_handlers
from bot.telegram_bot.middlewares import UserRegistrationMiddleware
from bot.utils.logging import setup_logging

logger = logging.getLogger(__name__)


async def main() -> None:
    config = load_config()
    setup_logging(config.log_level)

    db = Database(config.db_path)
    await db.connect()
    await db.init_schema()

    telethon_client = await create_telethon_client(config)
    await start_telethon_client(telethon_client, config.telegram_phone)

    bot = Bot(token=config.bot_token)
    dp = Dispatcher()
    bot["db"] = db

    dp.message.middleware(UserRegistrationMiddleware())
    register_all_handlers(dp)

    channel_manager = ChannelManager(telethon_client, db, config)
    await channel_manager.load_joined_channels()

    rate_limiter = TokenBucketRateLimiter(rate=config.forward_rate_limit)
    pipeline = ForwardingPipeline(
        bot, db, rate_limiter, num_workers=config.forward_workers,
    )
    await pipeline.start()

    await setup_event_handler(telethon_client, channel_manager, pipeline, db)

    poller = ChannelPoller(telethon_client, db, pipeline, config)
    poller_task = asyncio.create_task(poller.run())

    async def _cleanup_loop() -> None:
        while True:
            await asyncio.sleep(3600)
            deleted = await cleanup_old_forwarded(db, days=7)
            logger.info("Cleaned up %d old forwarded-message records", deleted)

    cleanup_task = asyncio.create_task(_cleanup_loop())

    try:
        await dp.start_polling(bot)
    finally:
        await pipeline.stop()
        poller_task.cancel()
        cleanup_task.cancel()
        await telethon_client.disconnect()
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
