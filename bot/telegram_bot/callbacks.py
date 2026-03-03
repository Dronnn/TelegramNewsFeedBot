from __future__ import annotations

import json

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.db import queries
from bot.db.database import Database
from bot.telegram_bot.keyboards import channel_list_keyboard, topics_keyboard

router = Router()


def _load_topics(catalog_path: str) -> list[dict]:
    with open(catalog_path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("topics", [])


def _find_topic_channels(all_topics: list[dict], topic_id: str) -> list[dict]:
    for t in all_topics:
        if str(t["id"]) == topic_id:
            return t.get("channels", [])
    return []


async def _resolve_channel(username: str) -> tuple[int, str, str]:
    """Stub: resolve channel by username. Will be replaced by Telethon later."""
    fake_id = abs(hash(username)) % (10**10)
    return fake_id, username, username


@router.callback_query(F.data.startswith("remove_channel:"))
async def cb_remove_channel(callback: CallbackQuery) -> None:
    db: Database = callback.bot["db"]  # type: ignore[index]
    channel_id = int(callback.data.split(":", 1)[1])
    user_id = callback.from_user.id

    await queries.unsubscribe(db, user_id, channel_id)

    subs = await queries.get_user_subscriptions(db, user_id)
    kb = channel_list_keyboard(subs)
    if subs:
        await callback.message.edit_text("Твои подписки:", reply_markup=kb)
    else:
        await callback.message.edit_text("Все подписки удалены.")
    await callback.answer("Канал удалён")


@router.callback_query(F.data.startswith("subscribe_topic:"))
async def cb_subscribe_topic(callback: CallbackQuery) -> None:
    db: Database = callback.bot["db"]  # type: ignore[index]
    topic_id = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id

    await queries.add_user_topic(db, user_id, topic_id)

    catalog_path = callback.bot["config"].catalog_path  # type: ignore[index]
    all_topics = _load_topics(catalog_path)

    # Subscribe user to all channels of this topic from the catalog
    channels = _find_topic_channels(all_topics, topic_id)
    for ch in channels:
        channel_id, ch_username, title = await _resolve_channel(ch["username"])
        await queries.add_channel(db, channel_id, ch_username, title)
        await queries.subscribe(db, user_id, channel_id)

    user_topics = await queries.get_user_topics(db, user_id)
    kb = topics_keyboard(all_topics, user_topics)
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer("Тема добавлена")


@router.callback_query(F.data.startswith("unsubscribe_topic:"))
async def cb_unsubscribe_topic(callback: CallbackQuery) -> None:
    db: Database = callback.bot["db"]  # type: ignore[index]
    topic_id = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id

    await queries.remove_user_topic(db, user_id, topic_id)

    catalog_path = callback.bot["config"].catalog_path  # type: ignore[index]
    all_topics = _load_topics(catalog_path)

    # Unsubscribe user from all channels of this topic from the catalog
    channels = _find_topic_channels(all_topics, topic_id)
    for ch in channels:
        channel_id, _username, _title = await _resolve_channel(ch["username"])
        await queries.unsubscribe(db, user_id, channel_id)

    user_topics = await queries.get_user_topics(db, user_id)
    kb = topics_keyboard(all_topics, user_topics)
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer("Тема убрана")
