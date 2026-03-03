from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Привет! Я — бот-агрегатор новостей.\n\n"
        "Подпишись на Telegram-каналы или выбери темы — "
        "и я буду пересылать тебе все новые посты в этот чат.\n\n"
        "Команды:\n"
        "/add @channel — подписаться на канал\n"
        "/list — мои подписки\n"
        "/topics — выбрать темы\n"
        "/help — полная справка"
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "Доступные команды:\n\n"
        "/add @channel — подписаться на канал\n"
        "/remove @channel — отписаться от канала\n"
        "/list — список подписок\n"
        "/topics — выбрать темы из каталога\n"
        "/mytopics — мои выбранные темы\n"
        "/pause — поставить ленту на паузу\n"
        "/resume — возобновить ленту\n"
        "/help — эта справка"
    )
