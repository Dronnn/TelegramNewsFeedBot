from aiogram import Router

from bot.telegram_bot.handlers.start import router as start_router


def register_all_handlers(parent_router: Router) -> None:
    parent_router.include_router(start_router)
