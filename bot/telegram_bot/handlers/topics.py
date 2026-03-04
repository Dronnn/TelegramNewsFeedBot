from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.db import queries
from bot.db.database import Database
from bot.telegram_bot.keyboards import my_topics_keyboard, topics_keyboard

router = Router()


async def _topics_from_catalog(db: Database, all_topics: list[dict]) -> list[dict]:
    """Build the topics list: categories from catalog DB, full data from JSON."""
    db_categories = await queries.get_catalog_categories(db)
    if not db_categories:
        return []

    db_cat_set = set(db_categories)
    return [t for t in all_topics if str(t["id"]) in db_cat_set]


@router.message(Command("topics"))
async def cmd_topics(message: Message, db: Database, topics: list[dict]) -> None:
    all_topics = await _topics_from_catalog(db, topics)
    if not all_topics:
        await message.answer("Каталог тем пуст.")
        return

    user_topics = await queries.get_user_topics(db, message.from_user.id)
    kb = topics_keyboard(all_topics, user_topics)
    await message.answer("Выбери темы — я подпишу тебя на все каналы:", reply_markup=kb)


@router.message(Command("mytopics"))
async def cmd_mytopics(message: Message, db: Database, topics: list[dict]) -> None:
    user_topic_ids = await queries.get_user_topics(db, message.from_user.id)
    if not user_topic_ids:
        await message.answer("У тебя пока нет выбранных тем. Используй /topics")
        return

    all_topics: list[dict] = topics
    selected = set(user_topic_ids)
    user_topics = [t for t in all_topics if str(t["id"]) in selected]

    if not user_topics:
        await message.answer("У тебя пока нет выбранных тем. Используй /topics")
        return

    kb = my_topics_keyboard(user_topics)
    await message.answer("Твои темы:", reply_markup=kb)
