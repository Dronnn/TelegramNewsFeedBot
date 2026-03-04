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
from bot.db.models import CatalogEntry
from bot.db.queries import cleanup_old_forwarded, seed_catalog
from bot.forwarder.pipeline import ForwardingPipeline
from bot.forwarder.rate_limiter import TokenBucketRateLimiter
from bot.telegram_bot import load_topics
from bot.telegram_bot.handlers import register_all_handlers
from bot.telegram_bot.middlewares import UserRegistrationMiddleware
from bot.utils.logging import setup_logging

logger = logging.getLogger(__name__)


async def cleanup_task(db: Database) -> None:
    """Periodically remove old forwarded-message records (runs every hour)."""
    while True:
        await asyncio.sleep(3600)
        try:
            deleted = await cleanup_old_forwarded(db, days=7)
            logger.info("Cleaned up %d old forwarded-message records", deleted)
        except Exception:
            logger.exception("Error during forwarded-messages cleanup")


async def main() -> None:
    config = load_config()
    setup_logging(config.log_level)

    db = Database(config.db_path)
    await db.connect()
    await db.init_schema()

    catalog_data = load_topics(config.catalog_path)
    entries = []
    for topic in catalog_data:
        for ch in topic.get("channels", []):
            entries.append(CatalogEntry(
                channel_username=ch["username"],
                title=ch["title"],
                category=str(topic["id"]),
                tags=ch.get("tags"),
                language=ch.get("language", "ru"),
            ))
    await seed_catalog(db, entries)

    telethon_client = create_telethon_client(config)
    await start_telethon_client(telethon_client, config.telegram_phone)

    bot = Bot(token=config.bot_token)
    dp = Dispatcher()
    dp["db"] = db
    dp["config"] = config
    dp["topics"] = catalog_data

    dp.message.middleware(UserRegistrationMiddleware())
    dp.callback_query.middleware(UserRegistrationMiddleware())
    register_all_handlers(dp)

    channel_manager = ChannelManager(telethon_client, db, config)
    await channel_manager.load_joined_channels()
    dp["channel_manager"] = channel_manager

    rate_limiter = TokenBucketRateLimiter(rate=config.forward_rate_limit)
    pipeline = ForwardingPipeline(
        bot, db, rate_limiter, num_workers=config.forward_workers,
    )
    await pipeline.start()

    await setup_event_handler(telethon_client, channel_manager, pipeline, db)

    poller = ChannelPoller(telethon_client, db, pipeline, config, bot)
    poller_task = asyncio.create_task(poller.run())

    cleanup = asyncio.create_task(cleanup_task(db))

    try:
        await dp.start_polling(bot)
    finally:
        logger.info("Shutting down pipeline...")
        try:
            await pipeline.stop()
        except Exception:
            logger.exception("Error stopping pipeline")

        logger.info("Cancelling poller...")
        try:
            poller_task.cancel()
            await asyncio.gather(poller_task, return_exceptions=True)
        except Exception:
            logger.exception("Error cancelling poller")

        logger.info("Cancelling cleanup task...")
        try:
            cleanup.cancel()
            await asyncio.gather(cleanup, return_exceptions=True)
        except Exception:
            logger.exception("Error cancelling cleanup task")

        logger.info("Disconnecting Telethon...")
        try:
            await telethon_client.disconnect()
        except Exception:
            logger.exception("Error disconnecting Telethon")

        logger.info("Closing database...")
        try:
            await db.close()
        except Exception:
            logger.exception("Error closing database")

        logger.info("Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
