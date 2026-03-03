from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class Config:
    bot_token: str
    telegram_api_id: int
    telegram_api_hash: str
    telegram_phone: str
    session_name: str = "newsfeed_service"
    db_path: str = "data/bot.db"
    catalog_path: str = "data/channel_catalog.json"
    join_threshold: int = 3
    poll_interval_default: int = 120
    forward_rate_limit: int = 25
    forward_workers: int = 3
    log_level: str = "INFO"


def load_config() -> Config:
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN")
    telegram_api_id = os.getenv("TELEGRAM_API_ID")
    telegram_api_hash = os.getenv("TELEGRAM_API_HASH")
    telegram_phone = os.getenv("TELEGRAM_PHONE")

    missing = [
        name
        for name, val in (
            ("BOT_TOKEN", bot_token),
            ("TELEGRAM_API_ID", telegram_api_id),
            ("TELEGRAM_API_HASH", telegram_api_hash),
            ("TELEGRAM_PHONE", telegram_phone),
        )
        if not val
    ]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    forward_rate_limit = int(os.getenv("FORWARD_RATE_LIMIT", "25"))
    if forward_rate_limit <= 0:
        raise ValueError("FORWARD_RATE_LIMIT must be a positive integer")

    return Config(
        bot_token=bot_token,
        telegram_api_id=int(telegram_api_id),
        telegram_api_hash=telegram_api_hash,
        telegram_phone=telegram_phone,
        session_name=os.getenv("SESSION_NAME", "newsfeed_service"),
        db_path=os.getenv("DB_PATH", "data/bot.db"),
        catalog_path=os.getenv("CATALOG_PATH", "data/channel_catalog.json"),
        join_threshold=int(os.getenv("JOIN_THRESHOLD", "3")),
        poll_interval_default=int(os.getenv("POLL_INTERVAL_DEFAULT", "120")),
        forward_rate_limit=forward_rate_limit,
        forward_workers=int(os.getenv("FORWARD_WORKERS", "3")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
