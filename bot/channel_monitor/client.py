from __future__ import annotations

from telethon import TelegramClient
from telethon.tl.types import Channel

from bot.config import Config


async def create_telethon_client(config: Config) -> TelegramClient:
    """Create a Telethon client instance without starting it."""
    return TelegramClient(
        config.session_name,
        config.telegram_api_id,
        config.telegram_api_hash,
    )


async def start_telethon_client(client: TelegramClient, phone: str) -> None:
    """Start the client and handle authentication."""
    await client.start(phone=phone)


async def resolve_channel(
    client: TelegramClient, channel_ref: str,
) -> tuple[int, str, str]:
    """Resolve a @username or t.me/ link to (id, username, title)."""
    ref = channel_ref.strip()
    if ref.startswith("@"):
        username = ref[1:]
    elif "t.me/" in ref:
        username = ref.split("t.me/")[-1].strip("/")
    else:
        username = ref

    entity = await client.get_entity(username)

    if isinstance(entity, Channel):
        return entity.id, entity.username or "", getattr(entity, "title", "")

    return entity.id, getattr(entity, "username", "") or "", getattr(entity, "title", "")
