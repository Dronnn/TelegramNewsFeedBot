from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.db import queries
from bot.db.database import Database

router = Router()


@router.message(Command("pause"))
async def cmd_pause(message: Message) -> None:
    db: Database = message.bot["db"]  # type: ignore[index]
    await queries.set_user_paused(db, message.from_user.id, True)
    await message.answer("Лента поставлена на паузу. Используй /resume, чтобы возобновить.")


@router.message(Command("resume"))
async def cmd_resume(message: Message) -> None:
    db: Database = message.bot["db"]  # type: ignore[index]
    await queries.set_user_paused(db, message.from_user.id, False)
    await message.answer("Лента возобновлена!")
