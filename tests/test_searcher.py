from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from bot.channel_monitor.searcher import ChannelSearcher
from bot.db.models import CatalogEntry
from bot.db.queries import seed_catalog


def _make_catalog_entries(
    category: str, count: int,
) -> list[CatalogEntry]:
    """Generate *count* catalog entries for the given category."""
    return [
        CatalogEntry(
            channel_username=f"chan_{category}_{i}",
            title=f"Channel {category.title()} {i}",
            category=category,
            tags=category,
            language="ru",
        )
        for i in range(count)
    ]


# -- Tests -----------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_by_topic_from_catalog(db):
    """search_by_topic returns catalog entries matching the given topic_id."""
    client = AsyncMock()
    searcher = ChannelSearcher(telethon_client=client, db=db)

    entries = _make_catalog_entries("tech", 3)
    # Add an entry for a different category to confirm filtering works
    other = _make_catalog_entries("sports", 1)
    await seed_catalog(db, entries + other)

    results = await searcher.search_by_topic("tech")

    assert len(results) == 3
    usernames = {r.channel_username for r in results}
    assert usernames == {"chan_tech_0", "chan_tech_1", "chan_tech_2"}
    for r in results:
        assert r.category == "tech"


@pytest.mark.asyncio
async def test_search_combined_catalog_enough(db):
    """When catalog has >= 5 results, search_telegram is NOT called."""
    client = AsyncMock()
    searcher = ChannelSearcher(telethon_client=client, db=db)

    entries = _make_catalog_entries("news", 5)
    await seed_catalog(db, entries)

    result = await searcher.search_combined("news", "news channels")

    # Catalog results are returned
    assert len(result["catalog"]) == 5

    # Telegram search was skipped — client was never invoked
    assert result["telegram"] == []
    client.assert_not_awaited()
