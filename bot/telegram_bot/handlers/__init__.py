from aiogram import Router

from bot.telegram_bot.handlers.channels import router as channels_router
from bot.telegram_bot.handlers.start import router as start_router


def register_all_handlers(parent_router: Router) -> None:
    parent_router.include_router(start_router)
    parent_router.include_router(channels_router)
