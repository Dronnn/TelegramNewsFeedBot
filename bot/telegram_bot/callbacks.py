from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.channel_monitor.manager import ChannelManager
from bot.db import queries
from bot.db.database import Database
from bot.telegram_bot.keyboards import channel_list_keyboard, topics_keyboard

router = Router()
log = logging.getLogger(__name__)


def _find_topic_channels(all_topics: list[dict], topic_id: str) -> list[dict]:
    for t in all_topics:
        if str(t["id"]) == topic_id:
            return t.get("channels", [])
    return []


@router.callback_query(F.data.startswith("remove_channel:"))
async def cb_remove_channel(callback: CallbackQuery) -> None:
    db: Database = callback.bot["db"]  # type: ignore[index]
    channel_manager: ChannelManager = callback.bot["channel_manager"]  # type: ignore[index]
    try:
        channel_id = int(callback.data.split(":", 1)[1])
    except (ValueError, IndexError):
        log.warning("Malformed callback data: %s", callback.data)
        await callback.answer("Ошибка данных")
        return
    user_id = callback.from_user.id

    await queries.unsubscribe(db, user_id, channel_id)
    await channel_manager.on_subscription_change(channel_id)

    subs = await queries.get_user_subscriptions(db, user_id)
    kb = channel_list_keyboard(subs)
    if subs:
        await callback.message.edit_text("Твои подписки:", reply_markup=kb)
    else:
        await callback.message.edit_text("Все подписки удалены.")
    await callback.answer("Канал удалён")


@router.callback_query(F.data.startswith("subscribe_topic:"))
async def cb_subscribe_topic(callback: CallbackQuery) -> None:
    await callback.answer("Подписываю на каналы темы...")
    db: Database = callback.bot["db"]  # type: ignore[index]
    channel_manager: ChannelManager = callback.bot["channel_manager"]  # type: ignore[index]
    topic_id = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id

    await queries.add_user_topic(db, user_id, topic_id)

    all_topics = callback.bot["topics"]  # type: ignore[index]

    # Subscribe user to all channels of this topic from the catalog
    channels = _find_topic_channels(all_topics, topic_id)
    for ch in channels:
        try:
            channel = await channel_manager.resolve_and_add_channel(ch["username"])
        except Exception:
            log.exception(
                "Failed to resolve channel '%s' for topic '%s'",
                ch["username"], topic_id,
            )
            continue
        await queries.subscribe(db, user_id, channel.channel_id)
        await channel_manager.on_subscription_change(channel.channel_id)

    user_topics = await queries.get_user_topics(db, user_id)
    kb = topics_keyboard(all_topics, user_topics)
    await callback.message.edit_reply_markup(reply_markup=kb)


@router.callback_query(F.data.startswith("unsubscribe_topic:"))
async def cb_unsubscribe_topic(callback: CallbackQuery) -> None:
    await callback.answer("Отписываю от каналов темы...")
    db: Database = callback.bot["db"]  # type: ignore[index]
    channel_manager: ChannelManager = callback.bot["channel_manager"]  # type: ignore[index]
    topic_id = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id

    await queries.remove_user_topic(db, user_id, topic_id)

    all_topics = callback.bot["topics"]  # type: ignore[index]

    # Unsubscribe user from all channels of this topic
    channels = _find_topic_channels(all_topics, topic_id)
    for ch in channels:
        channel = await queries.get_channel_by_username(db, ch["username"])
        if channel is None:
            continue
        await queries.unsubscribe(db, user_id, channel.channel_id)
        await channel_manager.on_subscription_change(channel.channel_id)

    user_topics = await queries.get_user_topics(db, user_id)
    kb = topics_keyboard(all_topics, user_topics)
    await callback.message.edit_reply_markup(reply_markup=kb)


@router.callback_query(F.data == "noop")
async def cb_noop(callback: CallbackQuery) -> None:
    await callback.answer()
