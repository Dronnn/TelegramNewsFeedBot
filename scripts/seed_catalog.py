"""Load channel catalog from JSON into the database."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

# Allow running from project root: `python -m scripts.seed_catalog`
# or directly: `python scripts/seed_catalog.py`
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from bot.db.database import Database
from bot.db.models import CatalogEntry
from bot.db.queries import seed_catalog

DEFAULT_CATALOG = PROJECT_ROOT / "data" / "channel_catalog.json"
DEFAULT_DB = PROJECT_ROOT / "data" / "bot.db"


def load_entries(catalog_path: Path) -> list[CatalogEntry]:
    """Read the JSON catalog and return a flat list of CatalogEntry objects."""
    with open(catalog_path, encoding="utf-8") as f:
        data = json.load(f)

    entries: list[CatalogEntry] = []
    for topic in data["topics"]:
        category = str(topic["id"])
        for ch in topic["channels"]:
            entries.append(
                CatalogEntry(
                    channel_username=ch["username"],
                    title=ch["title"],
                    category=category,
                    tags=ch.get("tags"),
                    language=ch.get("language", "ru"),
                )
            )
    return entries


async def main(
    catalog_path: Path = DEFAULT_CATALOG,
    db_path: Path = DEFAULT_DB,
) -> None:
    entries = load_entries(catalog_path)
    print(f"Loaded {len(entries)} catalog entries from {catalog_path}")

    db = Database(str(db_path))
    await db.connect()
    await db.init_schema()

    await seed_catalog(db, entries)
    print(f"Seeded {len(entries)} entries into {db_path}")

    await db.close()


if __name__ == "__main__":
    asyncio.run(main())
