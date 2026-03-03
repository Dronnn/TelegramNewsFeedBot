from __future__ import annotations

import re

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.db import queries
from bot.db.database import Database
from bot.telegram_bot.keyboards import channel_list_keyboard

router = Router()

_CHANNEL_RE = re.compile(
    r"(?:@|(?:https?://)?t\.me/)([A-Za-z][A-Za-z0-9_]{3,})"
)


def _parse_channel_ref(text: str) -> str | None:
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        return None
    m = _CHANNEL_RE.search(parts[1])
    return m.group(1) if m else None


async def _resolve_channel(username: str) -> tuple[int, str, str]:
    """Stub: resolve channel by username. Will be replaced by Telethon later."""
    fake_id = abs(hash(username)) % (10**10)
    return fake_id, username, username


@router.message(Command("add"))
async def cmd_add(message: Message) -> None:
    db: Database = message.bot["db"]  # type: ignore[index]
    username = _parse_channel_ref(message.text or "")
    if not username:
        await message.answer(
            "Укажи канал: /add @channel или /add t.me/channel"
        )
        return

    channel_id, ch_username, title = await _resolve_channel(username)
    await queries.add_channel(db, channel_id, ch_username, title)
    await queries.subscribe(db, message.from_user.id, channel_id)
    await message.answer(f"Подписка на @{ch_username} оформлена!")


@router.message(Command("remove"))
async def cmd_remove(message: Message) -> None:
    db: Database = message.bot["db"]  # type: ignore[index]
    username = _parse_channel_ref(message.text or "")
    if not username:
        await message.answer(
            "Укажи канал: /remove @channel"
        )
        return

    channel = await queries.get_channel_by_username(db, username)
    if channel is None:
        await message.answer("Канал не найден в подписках.")
        return

    subs = await queries.get_user_subscriptions(db, message.from_user.id)
    if not any(s.channel_id == channel.channel_id for s in subs):
        await message.answer("Ты не подписан на этот канал.")
        return

    await queries.unsubscribe(db, message.from_user.id, channel.channel_id)
    await message.answer(f"Отписка от @{username} выполнена.")


@router.message(Command("list"))
async def cmd_list(message: Message) -> None:
    db: Database = message.bot["db"]  # type: ignore[index]
    subs = await queries.get_user_subscriptions(db, message.from_user.id)
    if not subs:
        await message.answer("У тебя пока нет подписок. Используй /add @channel")
        return

    kb = channel_list_keyboard(subs)
    await message.answer("Твои подписки:", reply_markup=kb)
