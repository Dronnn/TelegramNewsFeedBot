from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.db.models import Channel


def channel_list_keyboard(channels: list[Channel]) -> InlineKeyboardMarkup | None:
    if not channels:
        return None
    rows = []
    for ch in channels:
        rows.append([
            InlineKeyboardButton(text=ch.title or ch.username or str(ch.channel_id), callback_data="noop"),
            InlineKeyboardButton(text="Удалить", callback_data=f"remove_channel:{ch.channel_id}"),
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def topics_keyboard(topics: list[dict], user_topics: list[str]) -> InlineKeyboardMarkup:
    selected = set(user_topics)
    buttons = []
    for t in topics:
        tid = str(t["id"])
        label = f"{t['emoji']} {t['name']}"
        if tid in selected:
            label = f"\u2705 {label}"
            cb = f"unsubscribe_topic:{tid}"
        else:
            cb = f"subscribe_topic:{tid}"
        buttons.append(InlineKeyboardButton(text=label, callback_data=cb))

    rows = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def my_topics_keyboard(user_topics: list[dict]) -> InlineKeyboardMarkup | None:
    if not user_topics:
        return None
    rows = []
    for t in user_topics:
        tid = str(t["id"])
        label = f"{t['emoji']} {t['name']}"
        rows.append([
            InlineKeyboardButton(text=label, callback_data="noop"),
            InlineKeyboardButton(text="Отписаться", callback_data=f"unsubscribe_topic:{tid}"),
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)
