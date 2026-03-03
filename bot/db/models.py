from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    is_paused: bool = False
    created_at: Optional[str] = None


@dataclass
class Channel:
    channel_id: int
    username: Optional[str] = None
    title: Optional[str] = None
    is_joined: bool = False
    subscriber_count: int = 0
    last_message_id: int = 0
    poll_interval: int = 120
    last_polled_at: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class CatalogEntry:
    channel_username: str
    title: str
    category: str
    tags: Optional[str] = None
    language: str = "ru"
