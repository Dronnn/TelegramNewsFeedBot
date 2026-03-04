from __future__ import annotations

from typing import Any, Awaitable, Callable, Union

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from bot.db import queries
from bot.db.database import Database


class UserRegistrationMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Union[Message, CallbackQuery], dict[str, Any]], Awaitable[Any]],
        event: Union[Message, CallbackQuery],
        data: dict[str, Any],
    ) -> Any:
        if event.from_user:
            db: Database = data["db"]
            await queries.add_user(
                db,
                user_id=event.from_user.id,
                username=event.from_user.username,
                first_name=event.from_user.first_name,
            )
        return await handler(event, data)
