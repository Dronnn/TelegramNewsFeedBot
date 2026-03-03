from aiogram import Router

from bot.telegram_bot.callbacks import router as callbacks_router
from bot.telegram_bot.handlers.channels import router as channels_router
from bot.telegram_bot.handlers.settings import router as settings_router
from bot.telegram_bot.handlers.start import router as start_router
from bot.telegram_bot.handlers.topics import router as topics_router


def register_all_handlers(parent_router: Router) -> None:
    parent_router.include_router(start_router)
    parent_router.include_router(channels_router)
    parent_router.include_router(topics_router)
    parent_router.include_router(settings_router)
    parent_router.include_router(callbacks_router)
